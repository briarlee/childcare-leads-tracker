"""
ACECQA National Registers 数据获取模块
获取澳大利亚幼儿教育和护理服务注册数据
使用完整浏览器头模拟绕过403限制
"""

import re
import time
from typing import Dict, List, Optional
from datetime import datetime

import requests
import pandas as pd
from io import StringIO

from .base_fetcher import BaseFetcher
from utils.helpers import get_today


class ACECQAFetcher(BaseFetcher):
    """ACECQA National Registers 数据获取器"""
    
    # 主页URL
    PAGE_URL = "https://www.acecqa.gov.au/resources/national-registers"
    
    # 直接CSV下载URLs（用户提供的工作链接）
    DIRECT_CSV_URLS = [
        # 全澳大利亚服务列表（主URL）
        "https://www.acecqa.gov.au/sites/default/files/national-registers/services/Education-services-au-export.csv",
        # 带nocache参数
        "https://www.acecqa.gov.au/sites/default/files/national-registers/services/Education-services-au-export.csv?nocache=1",
    ]
    
    # 完整的浏览器头模拟
    BROWSER_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-AU,en;q=0.9,en-US;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    def __init__(self):
        super().__init__("ACECQA")
        self.status['type'] = 'CSV'
        self.session = requests.Session()
        self.session.headers.update(self.BROWSER_HEADERS)
    
    def fetch(self) -> List[Dict]:
        """获取ACECQA数据"""
        self.logger.info(f"\n{'='*50}")
        self.logger.info(f"🇦🇺 开始获取 ACECQA National Registers 数据")
        self.logger.info(f"{'='*50}")
        
        df = None
        
        # 方法1：尝试直接CSV URLs
        for csv_url in self.DIRECT_CSV_URLS:
            self.logger.info(f"📥 尝试直接下载CSV: {csv_url[:60]}...")
            df = self._fetch_csv_with_session(csv_url)
            if df is not None:
                break
            time.sleep(1)  # 避免请求过快
        
        # 方法2：从页面动态获取CSV链接
        if df is None:
            self.logger.info("📡 尝试从页面获取CSV链接...")
            csv_url = self._get_csv_download_url()
            if csv_url:
                df = self._fetch_csv_with_session(csv_url)
        
        # 方法3：使用data.gov.au的备用数据
        if df is None:
            self.logger.info("📡 尝试从 data.gov.au 获取...")
            df = self._fetch_from_data_gov_au()
        
        if df is not None:
            records = self.transform(df)
            self.status['count'] = len(records)
            self.status['status'] = '正常'
            self.logger.info(f"📊 ACECQA数据处理完成: {len(records)} 条记录")
            return records
        
        # 如果所有方法都失败，返回空列表
        self.logger.warning("⚠️ 无法获取ACECQA数据，返回空列表")
        self.status['status'] = '异常'
        self.status['error'] = '所有数据源都无法访问'
        return []
    
    def _fetch_csv_with_session(self, url: str) -> Optional[pd.DataFrame]:
        """使用session获取CSV"""
        try:
            # 首先访问主页获取cookies
            try:
                self.session.get(self.PAGE_URL, timeout=10)
            except:
                pass
            
            # 然后获取CSV
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 检查是否是CSV内容
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type and 'csv' not in content_type:
                self.logger.warning(f"   返回的是HTML而非CSV")
                return None
            
            # 解析CSV
            df = pd.read_csv(StringIO(response.text))
            self.logger.info(f"✅ 下载成功: {len(df)} 行数据")
            return df
            
        except Exception as e:
            self.logger.warning(f"   下载失败: {str(e)[:100]}")
            return None
    
    def _get_csv_download_url(self) -> Optional[str]:
        """从ACECQA页面获取CSV下载链接"""
        try:
            response = self.session.get(self.PAGE_URL, timeout=30)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找CSV下载链接
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().lower()
                
                if '.csv' in href.lower() and ('service' in text or 'australia' in text or 'export' in href.lower()):
                    if href.startswith('http'):
                        return href
                    else:
                        return f"https://www.acecqa.gov.au{href}"
            
            # 查找任何CSV链接
            for link in soup.find_all('a', href=True):
                if '.csv' in link['href'].lower():
                    href = link['href']
                    if href.startswith('http'):
                        return href
                    else:
                        return f"https://www.acecqa.gov.au{href}"
            
            return None
            
        except Exception as e:
            self.logger.warning(f"   获取页面失败: {str(e)[:100]}")
            return None
    
    def _fetch_from_data_gov_au(self) -> Optional[pd.DataFrame]:
        """从澳大利亚政府开放数据门户获取数据"""
        try:
            # data.gov.au 上的ACECQA数据
            api_url = "https://data.gov.au/data/api/3/action/datastore_search"
            params = {
                'resource_id': 'your-resource-id-here',  # 需要找到正确的resource_id
                'limit': 10000
            }
            
            response = requests.get(api_url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('result', {}).get('records'):
                    return pd.DataFrame(data['result']['records'])
            
            return None
            
        except Exception as e:
            self.logger.warning(f"   data.gov.au 获取失败: {str(e)[:100]}")
            return None
    
    def transform(self, df: pd.DataFrame) -> List[Dict]:
        """转换DataFrame为标准记录格式"""
        records = []
        columns = df.columns.tolist()
        
        self.logger.debug(f"   CSV列: {columns[:10]}...")
        
        # ACECQA列名映射（根据实际CSV）
        column_mapping = {
            'name': self._find_column(columns, ['ServiceName', 'Service Name']),
            'provider': self._find_column(columns, ['ProviderLegalName', 'Provider Name']),
            'address': self._find_column(columns, ['ServiceAddress', 'Address']),
            'suburb': self._find_column(columns, ['Suburb', 'City']),
            'state': self._find_column(columns, ['State', 'State/Territory']),
            'postcode': self._find_column(columns, ['Postcode', 'Post Code']),
            'phone': self._find_column(columns, ['Phone', 'Telephone']),
            'service_type': self._find_column(columns, ['ServiceType', 'Service Type']),
            'approval_number': self._find_column(columns, ['ServiceApprovalNumber', 'Approval Number']),
            'quality_rating': self._find_column(columns, ['OverallRating', 'Overall Rating']),
            'approved_places': self._find_column(columns, ['NumberOfApprovedPlaces', 'Approved Places']),
            'approval_date': self._find_column(columns, ['ServiceApprovalGrantedDate', 'Approval Date']),
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
                    'license_holder': self._safe_get(row, column_mapping['provider']),
                    'address': full_address,
                    'city': str(suburb).strip() if suburb else '',
                    'province': self._normalize_state(state),
                    'country': 'Australia',
                    'license_number': self._safe_get(row, column_mapping['approval_number']),
                    'capacity': capacity,
                    'phone': self._safe_get(row, column_mapping['phone']),
                    'email': None,  # ACECQA数据不包含邮箱
                    'service_type': self._safe_get(row, column_mapping['service_type']),
                    'quality_rating': self._safe_get(row, column_mapping['quality_rating']),
                    'license_status': '已批准',
                    'discovered_date': get_today(),
                    'source': 'ACECQA National Register',
                    'source_url': self.PAGE_URL,
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
            'nt': 'Northern Territory',
            'new south wales': 'New South Wales',
            'victoria': 'Victoria',
            'queensland': 'Queensland',
            'western australia': 'Western Australia',
            'south australia': 'South Australia',
            'tasmania': 'Tasmania',
            'australian capital territory': 'Australian Capital Territory',
            'northern territory': 'Northern Territory'
        }
        
        state_lower = state.lower().strip()
        return state_mapping.get(state_lower, state)
    
    def _find_column(self, columns: List[str], possible_names: List[str]) -> Optional[str]:
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
