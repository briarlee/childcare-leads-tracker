"""
Ontario Open Data 数据获取模块
获取安大略省持牌托儿设施数据
"""

from typing import Dict, List
from datetime import datetime

import pandas as pd

from .base_fetcher import BaseFetcher
from ..config import config
from ..utils.helpers import get_today


class OntarioFetcher(BaseFetcher):
    """Ontario Open Data 数据获取器"""
    
    # 数据源URL (Licensed Child Care Facilities in Ontario)
    DATA_URL = "https://data.ontario.ca/dataset/868c8634-96e4-4878-abe7-e0c18c604a49/resource/8f7e7b09-0f09-4c40-a5bd-8e5a1e1a4916/download/lcc_facilities.csv"
    
    # 备用URL列表
    BACKUP_URLS = [
        "https://data.ontario.ca/en/dataset/licensed-child-care-facilities-in-ontario/resource/8f7e7b09-0f09-4c40-a5bd-8e5a1e1a4916/download/lcc_facilities.csv"
    ]
    
    def __init__(self):
        super().__init__("Ontario Open Data")
        self.status['type'] = 'CSV'
    
    def fetch(self) -> List[Dict]:
        """
        获取Ontario数据
        
        Returns:
            记录列表
        """
        self.logger.info(f"\n{'='*50}")
        self.logger.info(f"🇨🇦 开始获取 Ontario Licensed Child Care 数据")
        self.logger.info(f"{'='*50}")
        
        # 尝试主URL
        df = self.fetch_csv(self.DATA_URL)
        
        # 如果主URL失败，尝试备用URL
        if df is None:
            for backup_url in self.BACKUP_URLS:
                self.logger.info(f"📡 尝试备用URL...")
                df = self.fetch_csv(backup_url)
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
    
    def transform(self, df: pd.DataFrame) -> List[Dict]:
        """
        转换DataFrame为标准记录格式
        
        Ontario CSV字段说明:
        - Licence Holder: 许可证持有人
        - Centre Name: 中心名称
        - Address: 地址
        - City: 城市
        - Licence Number: 许可证号
        - Total Capacity: 总容量
        - Phone: 电话
        - Email: 邮箱
        - Issue Date: 发放日期
        ...
        
        Args:
            df: 原始DataFrame
            
        Returns:
            标准格式的记录列表
        """
        records = []
        
        # 获取列名（可能有变化）
        columns = df.columns.tolist()
        self.logger.debug(f"   CSV列: {columns[:10]}...")
        
        # 列名映射（处理可能的不同命名）
        column_mapping = {
            'name': self._find_column(columns, ['Centre Name', 'center_name', 'Name', 'name']),
            'license_holder': self._find_column(columns, ['Licence Holder', 'License Holder', 'licence_holder']),
            'address': self._find_column(columns, ['Address', 'address', 'Street Address']),
            'city': self._find_column(columns, ['City', 'city', 'Municipality']),
            'license_number': self._find_column(columns, ['Licence Number', 'License Number', 'licence_number']),
            'capacity': self._find_column(columns, ['Total Capacity', 'Capacity', 'capacity', 'total_capacity']),
            'phone': self._find_column(columns, ['Phone', 'phone', 'Telephone']),
            'email': self._find_column(columns, ['Email', 'email', 'E-mail']),
            'issue_date': self._find_column(columns, ['Issue Date', 'issue_date', 'Licence Issue Date']),
            'postal_code': self._find_column(columns, ['Postal Code', 'postal_code', 'PostalCode']),
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
                address = self._safe_get(row, column_mapping['address'])
                city = self._safe_get(row, column_mapping['city'])
                postal_code = self._safe_get(row, column_mapping['postal_code'])
                
                full_address = address
                if postal_code and postal_code not in str(address):
                    full_address = f"{address}, {postal_code}"
                
                # 解析容量
                capacity = self._safe_get(row, column_mapping['capacity'])
                try:
                    capacity = int(float(str(capacity).replace(',', ''))) if capacity else None
                except (ValueError, TypeError):
                    capacity = None
                
                record = {
                    'name': str(name).strip(),
                    'license_holder': self._safe_get(row, column_mapping['license_holder']),
                    'address': full_address,
                    'city': str(city).strip() if city else '',
                    'province': 'Ontario',
                    'country': 'Canada',
                    'license_number': self._safe_get(row, column_mapping['license_number']),
                    'capacity': capacity,
                    'phone': self._safe_get(row, column_mapping['phone']),
                    'email': self._safe_get(row, column_mapping['email']),
                    'license_status': '新发',  # 默认状态
                    'discovered_date': get_today(),
                    'source': 'Ontario Open Data',
                    'source_url': 'https://data.ontario.ca/dataset/licensed-child-care-facilities-in-ontario',
                    'type': '新建',
                }
                
                # 处理发放日期
                issue_date = self._safe_get(row, column_mapping['issue_date'])
                if issue_date:
                    record['issue_date'] = str(issue_date)
                
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
