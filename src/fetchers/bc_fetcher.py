"""
BC Child Care Map 数据获取模块
获取BC省托儿设施数据
"""

from typing import Dict, List

import pandas as pd

from .base_fetcher import BaseFetcher
from utils.helpers import get_today


class BCFetcher(BaseFetcher):
    """BC Child Care Map 数据获取器"""
    
    # 数据源URL
    DATA_URL = "https://catalogue.data.gov.bc.ca/dataset/child-care-map-data/resource/9a9f14e1-03a0-4b7c-a8fc-ca8fcd1b8bb1/download/childcarebc.csv"
    
    def __init__(self):
        super().__init__("BC Child Care")
        self.status['type'] = 'CSV'
    
    def fetch(self) -> List[Dict]:
        """获取BC数据"""
        self.logger.info(f"\n{'='*50}")
        self.logger.info(f"🇨🇦 开始获取 BC Child Care Map 数据")
        self.logger.info(f"{'='*50}")
        
        df = self.fetch_csv(self.DATA_URL)
        
        if df is None:
            self.logger.error(f"❌ 无法获取BC数据")
            return []
        
        records = self.transform(df)
        self.status['count'] = len(records)
        
        self.logger.info(f"📊 BC数据处理完成: {len(records)} 条记录")
        return records
    
    def transform(self, df: pd.DataFrame) -> List[Dict]:
        """转换DataFrame为标准记录格式"""
        records = []
        columns = df.columns.tolist()
        
        self.logger.debug(f"   CSV列: {columns[:10]}...")
        
        # 列名映射
        column_mapping = {
            'name': self._find_column(columns, ['NAME', 'name', 'Facility Name', 'FACILITY_NAME']),
            'address': self._find_column(columns, ['ADDRESS', 'address', 'Street Address', 'STREET_ADDRESS']),
            'city': self._find_column(columns, ['CITY', 'city', 'City', 'MUNICIPALITY']),
            'postal_code': self._find_column(columns, ['POSTAL_CODE', 'postal_code', 'PostalCode']),
            'phone': self._find_column(columns, ['PHONE', 'phone', 'Phone', 'TELEPHONE']),
            'email': self._find_column(columns, ['EMAIL', 'email', 'Email']),
            'capacity': self._find_column(columns, ['CAPACITY', 'capacity', 'Total Capacity', 'TOTAL_CAPACITY']),
            'service_type': self._find_column(columns, ['SERVICE_TYPE', 'service_type', 'Type', 'FACILITY_TYPE']),
            'license_number': self._find_column(columns, ['LICENSE_NUMBER', 'license_number', 'Licence Number']),
        }
        
        for _, row in df.iterrows():
            try:
                name = self._safe_get(row, column_mapping['name'])
                if not name:
                    continue
                
                address = self._safe_get(row, column_mapping['address'])
                city = self._safe_get(row, column_mapping['city'])
                postal_code = self._safe_get(row, column_mapping['postal_code'])
                
                full_address = address
                if postal_code and address and postal_code not in str(address):
                    full_address = f"{address}, {postal_code}"
                
                capacity = self._safe_get(row, column_mapping['capacity'])
                try:
                    capacity = int(float(str(capacity).replace(',', ''))) if capacity else None
                except (ValueError, TypeError):
                    capacity = None
                
                record = {
                    'name': str(name).strip(),
                    'address': full_address,
                    'city': str(city).strip() if city else '',
                    'province': 'British Columbia',
                    'country': 'Canada',
                    'license_number': self._safe_get(row, column_mapping['license_number']),
                    'capacity': capacity,
                    'phone': self._safe_get(row, column_mapping['phone']),
                    'email': self._safe_get(row, column_mapping['email']),
                    'service_type': self._safe_get(row, column_mapping['service_type']),
                    'license_status': '新发',
                    'discovered_date': get_today(),
                    'source': 'BC Child Care Map',
                    'source_url': 'https://catalogue.data.gov.bc.ca/dataset/child-care-map-data',
                    'type': '新建',
                }
                
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
    
    def fetch_new_facilities(self, existing_licenses: set = None) -> List[Dict]:
        """获取新设施"""
        all_records = self.fetch()
        
        if existing_licenses is None or len(existing_licenses) == 0:
            return all_records
        
        new_records = [
            r for r in all_records
            if r.get('license_number') and r['license_number'] not in existing_licenses
        ]
        
        self.logger.info(f"🔍 过滤后新记录: {len(new_records)} 条")
        self.status['count'] = len(new_records)
        
        return new_records
