"""
Ontario Open Data 数据获取模块
获取安大略省持牌托儿设施数据
支持XLSX格式（2025年后Ontario不再提供CSV）
"""

from typing import Dict, List
from datetime import datetime
from io import BytesIO

import pandas as pd
import requests

from .base_fetcher import BaseFetcher
from config import config
from utils.helpers import get_today


class OntarioFetcher(BaseFetcher):
    """Ontario Open Data 数据获取器"""
    
    # 数据源页面
    DATASET_PAGE = "https://data.ontario.ca/dataset/licensed-child-care-facilities-in-ontario"
    
    # 最新XLSX下载URL（2025年11月版本）
    DATA_URL = "https://data.ontario.ca/dataset/7efd8b4b-cc63-4337-a551-c940a346605b/resource/2b81313c-9ada-4680-abba-4470ec386a2e/download/child_care_facilities_open_data_nov_2025.xlsx"
    
    # 备用URL列表
    BACKUP_URLS = [
        # 尝试不同文件名格式
        "https://data.ontario.ca/dataset/7efd8b4b-cc63-4337-a551-c940a346605b/resource/2b81313c-9ada-4680-abba-4470ec386a2e/download/child_care_facilities_open_data.xlsx",
        # API endpoint
        "https://data.ontario.ca/api/3/action/datastore_search?resource_id=2b81313c-9ada-4680-abba-4470ec386a2e&limit=10000",
    ]
    
    def __init__(self):
        super().__init__("Ontario Open Data")
        self.status['type'] = 'XLSX'
    
    def fetch(self) -> List[Dict]:
        """
        获取Ontario数据
        
        Returns:
            记录列表
        """
        self.logger.info(f"\n{'='*50}")
        self.logger.info(f"🇨🇦 开始获取 Ontario Licensed Child Care 数据")
        self.logger.info(f"{'='*50}")
        
        df = None
        
        # 尝试主URL (XLSX)
        df = self.fetch_xlsx(self.DATA_URL)
        
        # 如果主URL失败，尝试备用URL
        if df is None:
            for backup_url in self.BACKUP_URLS:
                self.logger.info(f"📡 尝试备用URL...")
                if 'api/3/action' in backup_url:
                    # API格式
                    df = self.fetch_api(backup_url)
                else:
                    df = self.fetch_xlsx(backup_url)
                if df is not None:
                    break
        
        if df is None:
            self.logger.error(f"❌ 无法获取Ontario数据")
            return []
        
        # 转换数据
        records = self.transform(df)
        
        self.status['count'] = len(records)
        self.logger.info(f"📊 Ontario数据处理完成: {len(records)} 条记录")
        
        return records
    
    def fetch_xlsx(self, url: str) -> pd.DataFrame:
        """
        下载并解析XLSX文件
        
        Args:
            url: XLSX文件URL
            
        Returns:
            DataFrame或None
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"📥 [{self.source_name}] 尝试下载XLSX (第{attempt + 1}次)...")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,*/*',
                }
                
                response = requests.get(url, timeout=self.timeout, headers=headers)
                response.raise_for_status()
                
                # 解析XLSX
                df = pd.read_excel(BytesIO(response.content), engine='openpyxl')
                
                self.logger.info(f"✅ [{self.source_name}] 下载成功: {len(df)} 行数据")
                self.status['status'] = '正常'
                self.status['last_fetch'] = datetime.now().isoformat()
                
                return df
                
            except Exception as e:
                self.logger.warning(f"⚠️ [{self.source_name}] 请求失败 (第{attempt + 1}次): {str(e)}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.info(f"   等待 {wait_time} 秒后重试...")
                    import time
                    time.sleep(wait_time)
        
        self.logger.error(f"❌ [{self.source_name}] 下载失败，已重试 {self.max_retries} 次")
        self.status['status'] = '异常'
        return None
    
    def fetch_api(self, url: str) -> pd.DataFrame:
        """
        通过CKAN API获取数据
        
        Args:
            url: API URL
            
        Returns:
            DataFrame或None
        """
        try:
            self.logger.info(f"📥 [{self.source_name}] 尝试通过API获取...")
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success') and data.get('result', {}).get('records'):
                records = data['result']['records']
                df = pd.DataFrame(records)
                self.logger.info(f"✅ [{self.source_name}] API获取成功: {len(df)} 行数据")
                return df
            
        except Exception as e:
            self.logger.warning(f"⚠️ [{self.source_name}] API请求失败: {str(e)}")
        
        return None
    
    def transform(self, df: pd.DataFrame) -> List[Dict]:
        """
        转换DataFrame为标准记录格式
        
        Args:
            df: 原始DataFrame
            
        Returns:
            标准格式的记录列表
        """
        records = []
        
        # 获取列名
        columns = df.columns.tolist()
        self.logger.debug(f"   数据列: {columns[:10]}...")
        
        # 列名映射（根据实际XLSX文件）
        column_mapping = {
            'name': self._find_column(columns, ['Child Care Site Name', 'Centre Name', 'center_name', 'Name']),
            'license_holder': self._find_column(columns, ['Licensee Name', 'Licence Holder', 'License Holder']),
            'license_number': self._find_column(columns, ['Licence Number', 'License Number']),
            'street_number': self._find_column(columns, ['Street Number']),
            'street_name': self._find_column(columns, ['Street Name']),
            'street_type': self._find_column(columns, ['Street Type']),
            'city': self._find_column(columns, ['City', 'city', 'Municipality']),
            'province': self._find_column(columns, ['Province']),
            'postal_code': self._find_column(columns, ['Postal Code', 'postal_code', 'PostalCode']),
            'issue_date': self._find_column(columns, ['Original Issue Date', 'Issue Date']),
            'license_status': self._find_column(columns, ['Licence Status', 'License Status']),
            'program_type': self._find_column(columns, ['Program Type Desc', 'Program Type']),
            'region': self._find_column(columns, ['Region Display Name', 'Region']),
        }
        
        for _, row in df.iterrows():
            try:
                # 获取中心名称
                name = self._safe_get(row, column_mapping['name'])
                if not name:
                    name = self._safe_get(row, column_mapping['license_holder'])
                
                if not name:
                    continue  # 跳过没有名称的记录
                
                # 构建完整地址
                street_num = self._safe_get(row, column_mapping['street_number']) or ''
                street_name = self._safe_get(row, column_mapping['street_name']) or ''
                street_type = self._safe_get(row, column_mapping['street_type']) or ''
                city = self._safe_get(row, column_mapping['city']) or ''
                postal_code = self._safe_get(row, column_mapping['postal_code']) or ''
                
                # 组合街道地址
                street_parts = [str(street_num), str(street_name), str(street_type)]
                street_address = ' '.join([p for p in street_parts if p and p.strip()])
                
                full_address = street_address
                if postal_code and postal_code not in str(street_address):
                    full_address = f"{street_address}, {postal_code}"
                
                record = {
                    'name': str(name).strip(),
                    'license_holder': self._safe_get(row, column_mapping['license_holder']),
                    'address': full_address,
                    'city': str(city).strip() if city else '',
                    'province': 'Ontario',
                    'country': 'Canada',
                    'license_number': self._safe_get(row, column_mapping['license_number']),
                    'capacity': None,  # 该数据集不包含容量信息
                    'phone': None,
                    'email': None,
                    'license_status': self._safe_get(row, column_mapping['license_status']) or '新发',
                    'program_type': self._safe_get(row, column_mapping['program_type']),
                    'region': self._safe_get(row, column_mapping['region']),
                    'discovered_date': get_today(),
                    'source': 'Ontario Open Data',
                    'source_url': self.DATASET_PAGE,
                    'type': '新建',
                }
                
                # 处理发放日期
                issue_date = self._safe_get(row, column_mapping['issue_date'])
                if issue_date:
                    record['issue_date'] = str(issue_date)[:10]  # 只取日期部分
                
                records.append(record)
                
            except Exception as e:
                self.logger.debug(f"   跳过一条记录: {str(e)}")
                continue
        
        return records
    
    def _find_column(self, columns: List[str], possible_names: List[str]) -> str:
        """查找匹配的列名"""
        for name in possible_names:
            if name in columns:
                return name
            # 不区分大小写匹配
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
    
    def fetch_new_licenses(self, existing_licenses: set = None) -> List[Dict]:
        """
        获取新发许可证（过滤掉已存在的）
        
        Args:
            existing_licenses: 已存在的许可证号集合
            
        Returns:
            新记录列表
        """
        all_records = self.fetch()
        
        if existing_licenses is None or len(existing_licenses) == 0:
            return all_records
        
        # 过滤掉已存在的许可证
        new_records = [
            r for r in all_records
            if r.get('license_number') and r['license_number'] not in existing_licenses
        ]
        
        self.logger.info(f"🔍 过滤后新记录: {len(new_records)} 条 (原 {len(all_records)} 条)")
        self.status['count'] = len(new_records)
        
        return new_records
