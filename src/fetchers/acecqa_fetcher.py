"""
ACECQA National Registers 数据获取模块
获取澳大利亚幼儿教育和护理服务注册数据
"""

import re
from typing import Dict, List

import requests
import pandas as pd
from bs4 import BeautifulSoup

from .base_fetcher import BaseFetcher
from ..utils.helpers import get_today


class ACECQAFetcher(BaseFetcher):
    """ACECQA National Registers 数据获取器"""
    
    # 主页URL（需要从这里获取实际CSV下载链接）
    PAGE_URL = "https://www.acecqa.gov.au/resources/national-registers"
    
    # 直接CSV URL（如果可用）
    # 注意：ACECQA的CSV链接可能会变化，需要从页面动态获取
    DIRECT_CSV_URL = None
    
    def __init__(self):
        super().__init__("ACECQA")
        self.status['type'] = 'CSV'
    
    def fetch(self) -> List[Dict]:
        """获取ACECQA数据"""
        self.logger.info(f"\n{'='*50}")
        self.logger.info(f"🇦🇺 开始获取 ACECQA National Registers 数据")
        self.logger.info(f"{'='*50}")
        
        # 首先尝试获取CSV下载链接
        csv_url = self._get_csv_download_url()
        
        if csv_url:
            df = self.fetch_csv(csv_url)
            if df is not None:
                records = self.transform(df)
                self.status['count'] = len(records)
                self.logger.info(f"📊 ACECQA数据处理完成: {len(records)} 条记录")
                return records
        
        # 如果无法获取CSV，使用备用方案
        self.logger.warning("⚠️ 无法获取ACECQA CSV，使用模拟数据")
        return self._get_sample_data()
    
    def _get_csv_download_url(self) -> str:
        """从ACECQA页面获取CSV下载链接"""
        try:
            self.logger.info(f"📡 访问ACECQA页面获取CSV链接...")
            
            response = requests.get(
                self.PAGE_URL,
                timeout=self.timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找CSV下载链接
            # ACECQA页面通常有多个注册表的下载链接
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().lower()
                
                # 查找"已批准服务"或"approved services"的CSV
                if ('.csv' in href.lower() or 'csv' in text) and \
                   ('approved' in text or 'service' in text or 'register' in text):
                    
                    # 构建完整URL
                    if href.startswith('http'):
                        csv_url = href
                    else:
                        csv_url = f"https://www.acecqa.gov.au{href}"
                    
                    self.logger.info(f"   找到CSV链接: {csv_url[:80]}...")
                    return csv_url
            
            # 备用：查找任何CSV链接
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '.csv' in href.lower():
                    if href.startswith('http'):
                        csv_url = href
                    else:
                        csv_url = f"https://www.acecqa.gov.au{href}"
                    self.logger.info(f"   找到备用CSV链接: {csv_url[:80]}...")
                    return csv_url
            
            self.logger.warning("⚠️ 未在页面中找到CSV链接")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 获取CSV链接失败: {str(e)}")
            return None
    
    def transform(self, df: pd.DataFrame) -> List[Dict]:
        """转换DataFrame为标准记录格式"""
        records = []
        columns = df.columns.tolist()
        
        self.logger.debug(f"   CSV列: {columns[:10]}...")
        
        # ACECQA列名映射（根据实际CSV调整）
        column_mapping = {
            'name': self._find_column(columns, [
                'Service Name', 'SERVICE_NAME', 'Name', 'name',
                'Approved Provider', 'Provider Name'
            ]),
            'address': self._find_column(columns, [
                'Address', 'ADDRESS', 'Street Address', 'Service Address',
                'Physical Address'
            ]),
            'suburb': self._find_column(columns, [
                'Suburb', 'SUBURB', 'City', 'Locality'
            ]),
            'state': self._find_column(columns, [
                'State', 'STATE', 'State/Territory'
            ]),
            'postcode': self._find_column(columns, [
                'Postcode', 'POSTCODE', 'Post Code', 'Postal Code'
            ]),
            'phone': self._find_column(columns, [
                'Phone', 'PHONE', 'Contact Phone', 'Telephone'
            ]),
            'email': self._find_column(columns, [
                'Email', 'EMAIL', 'Contact Email'
            ]),
            'service_type': self._find_column(columns, [
                'Service Type', 'SERVICE_TYPE', 'Type', 'Care Type'
            ]),
            'approval_number': self._find_column(columns, [
                'Approval Number', 'APPROVAL_NUMBER', 'SE Number',
                'Service Approval Number', 'Approval No'
            ]),
            'quality_rating': self._find_column(columns, [
                'Overall Rating', 'Quality Rating', 'OVERALL_RATING',
                'Quality Area Rating'
            ]),
            'approved_places': self._find_column(columns, [
                'Approved Places', 'APPROVED_PLACES', 'Capacity',
                'Maximum Approved Places'
            ]),
        }
        
        for _, row in df.iterrows():
            try:
                name = self._safe_get(row, column_mapping['name'])
                if not name:
                    continue
                
                # 构建完整地址
                address = self._safe_get(row, column_mapping['address'])
                suburb = self._safe_get(row, column_mapping['suburb'])
                state = self._safe_get(row, column_mapping['state'])
                postcode = self._safe_get(row, column_mapping['postcode'])
                
                address_parts = [p for p in [address, suburb, state, postcode] if p]
                full_address = ', '.join(address_parts)
                
                # 解析容量
                capacity = self._safe_get(row, column_mapping['approved_places'])
                try:
                    capacity = int(float(str(capacity).replace(',', ''))) if capacity else None
                except (ValueError, TypeError):
                    capacity = None
                
                record = {
                    'name': str(name).strip(),
                    'address': full_address,
                    'city': str(suburb).strip() if suburb else '',
                    'province': self._normalize_state(state),
                    'country': 'Australia',
                    'license_number': self._safe_get(row, column_mapping['approval_number']),
                    'capacity': capacity,
                    'phone': self._safe_get(row, column_mapping['phone']),
                    'email': self._safe_get(row, column_mapping['email']),
                    'service_type': self._safe_get(row, column_mapping['service_type']),
                    'quality_rating': self._safe_get(row, column_mapping['quality_rating']),
                    'license_status': '已批准',
                    'discovered_date': get_today(),
                    'source': 'ACECQA National Register',
                    'source_url': 'https://www.acecqa.gov.au/resources/national-registers',
                    'type': '新建',
                }
                
                records.append(record)
                
            except Exception as e:
                self.logger.debug(f"   跳过一条记录: {str(e)}")
                continue
        
        return records
    
    def _normalize_state(self, state: str) -> str:
        """标准化澳大利亚州名"""
        if not state:
            return ''
        
        state_mapping = {
            'nsw': 'New South Wales',
            'vic': 'Victoria',
            'qld': 'Queensland',
            'wa': 'Western Australia',
            'sa': 'South Australia',
            'tas': 'Tasmania',
            'act': 'Australian Capital Territory',
            'nt': 'Northern Territory'
        }
        
        state_lower = state.lower().strip()
        return state_mapping.get(state_lower, state)
    
    def _find_column(self, columns: List[str], possible_names: List[str]) -> str:
        """查找匹配的列名"""
        for name in possible_names:
            if name in columns:
                return name
            for col in columns:
                if col.lower() == name.lower():
                    return col
        return None
    
    def _safe_get(self, row, column: str):
        """安全获取行中的值"""
        if column is None:
            return None
        try:
            value = row.get(column)
            if pd.isna(value):
                return None
            return str(value).strip() if value else None
        except:
            return None
    
    def _get_sample_data(self) -> List[Dict]:
        """
        获取示例数据（当无法访问真实数据时使用）
        在生产环境中这应替换为错误处理
        """
        self.logger.info("📋 生成ACECQA示例数据...")
        
        # 返回空列表或示例数据用于测试
        sample_records = [
            {
                'name': 'Sydney Learning Centre',
                'address': '123 George Street, Sydney, NSW 2000',
                'city': 'Sydney',
                'province': 'New South Wales',
                'country': 'Australia',
                'license_number': 'SE-00123456',
                'capacity': 75,
                'phone': '(02) 1234 5678',
                'email': 'info@sydneylearning.com.au',
                'service_type': 'Long Day Care',
                'quality_rating': 'Exceeding NQS',
                'license_status': '已批准',
                'discovered_date': get_today(),
                'source': 'ACECQA (Sample)',
                'source_url': 'https://www.acecqa.gov.au/resources/national-registers',
                'type': '新建',
            },
            {
                'name': 'Melbourne Kids Academy',
                'address': '456 Collins Street, Melbourne, VIC 3000',
                'city': 'Melbourne',
                'province': 'Victoria',
                'country': 'Australia',
                'license_number': 'SE-00789012',
                'capacity': 60,
                'phone': '(03) 9876 5432',
                'email': 'contact@melbournekids.com.au',
                'service_type': 'Long Day Care',
                'quality_rating': 'Meeting NQS',
                'license_status': '已批准',
                'discovered_date': get_today(),
                'source': 'ACECQA (Sample)',
                'source_url': 'https://www.acecqa.gov.au/resources/national-registers',
                'type': '新建',
            }
        ]
        
        self.status['count'] = len(sample_records)
        return sample_records
    
    def fetch_new_services(self, existing_approvals: set = None) -> List[Dict]:
        """获取新服务"""
        all_records = self.fetch()
        
        if existing_approvals is None or len(existing_approvals) == 0:
            return all_records
        
        new_records = [
            r for r in all_records
            if r.get('license_number') and r['license_number'] not in existing_approvals
        ]
        
        self.logger.info(f"🔍 过滤后新记录: {len(new_records)} 条")
        self.status['count'] = len(new_records)
        
        return new_records
