"""
数据验证模块
提供数据字段验证和清洗功能
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class DataValidator:
    """数据验证器"""
    
    # 必填字段定义（放宽要求）
    REQUIRED_FIELDS = {
        'new_project': ['name', 'country', 'source', 'discovered_date'],  # city可选
        'sale': ['name', 'country', 'source', 'discovered_date'],
        'tender': ['name', 'country', 'source', 'published_date']
    }
    
    # 加拿大主要城市
    CANADA_MAJOR_CITIES = {
        'toronto', 'vancouver', 'montreal', 'calgary', 'edmonton', 
        'ottawa', 'winnipeg', 'quebec city', 'hamilton', 'kitchener',
        'london', 'victoria', 'halifax', 'oshawa', 'windsor',
        'saskatoon', 'regina', 'st. catharines', 'kelowna', 'barrie',
        'abbotsford', 'sherbrooke', 'kingston', 'trois-rivières', 'guelph',
        'moncton', 'brantford', 'thunder bay', 'saint john', 'peterborough'
    }
    
    # 澳大利亚主要城市
    AUSTRALIA_MAJOR_CITIES = {
        'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide',
        'gold coast', 'canberra', 'newcastle', 'sunshine coast', 'wollongong',
        'hobart', 'geelong', 'townsville', 'cairns', 'darwin',
        'toowoomba', 'ballarat', 'bendigo', 'launceston', 'mackay',
        'rockhampton', 'bunbury', 'bundaberg', 'hervey bay', 'wagga wagga'
    }
    
    # 加拿大省份代码
    CANADA_PROVINCES = {
        'on': 'Ontario', 'ontario': 'Ontario',
        'bc': 'British Columbia', 'british columbia': 'British Columbia',
        'ab': 'Alberta', 'alberta': 'Alberta',
        'qc': 'Quebec', 'quebec': 'Quebec',
        'mb': 'Manitoba', 'manitoba': 'Manitoba',
        'sk': 'Saskatchewan', 'saskatchewan': 'Saskatchewan',
        'ns': 'Nova Scotia', 'nova scotia': 'Nova Scotia',
        'nb': 'New Brunswick', 'new brunswick': 'New Brunswick',
        'nl': 'Newfoundland and Labrador', 'newfoundland': 'Newfoundland and Labrador',
        'pe': 'Prince Edward Island', 'pei': 'Prince Edward Island',
        'nt': 'Northwest Territories', 'northwest territories': 'Northwest Territories',
        'yt': 'Yukon', 'yukon': 'Yukon',
        'nu': 'Nunavut', 'nunavut': 'Nunavut'
    }
    
    # 澳大利亚州/领地代码
    AUSTRALIA_STATES = {
        'nsw': 'New South Wales', 'new south wales': 'New South Wales',
        'vic': 'Victoria', 'victoria': 'Victoria',
        'qld': 'Queensland', 'queensland': 'Queensland',
        'wa': 'Western Australia', 'western australia': 'Western Australia',
        'sa': 'South Australia', 'south australia': 'South Australia',
        'tas': 'Tasmania', 'tasmania': 'Tasmania',
        'act': 'Australian Capital Territory', 'australian capital territory': 'Australian Capital Territory',
        'nt': 'Northern Territory', 'northern territory': 'Northern Territory'
    }
    
    @classmethod
    def validate_record(cls, record: Dict, record_type: str = 'new_project') -> Tuple[bool, List[str]]:
        """
        验证一条记录
        
        Args:
            record: 记录字典
            record_type: 记录类型 (new_project/sale/tender)
            
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        required = cls.REQUIRED_FIELDS.get(record_type, cls.REQUIRED_FIELDS['new_project'])
        
        # 检查必填字段
        for field in required:
            value = record.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"缺少必填字段: {field}")
        
        # 验证容量
        capacity = record.get('capacity')
        if capacity is not None:
            if isinstance(capacity, str):
                try:
                    capacity = int(capacity)
                except ValueError:
                    errors.append(f"容量值无效: {capacity}")
            if isinstance(capacity, (int, float)) and capacity < 0:
                errors.append(f"容量不能为负数: {capacity}")
            if isinstance(capacity, (int, float)) and capacity > 500:
                errors.append(f"容量异常过大（>500）: {capacity}，请核实")
        
        # 验证日期格式
        for date_field in ['discovered_date', 'published_date', 'deadline_date']:
            date_value = record.get(date_field)
            if date_value:
                if not cls._validate_date(date_value):
                    errors.append(f"日期格式无效: {date_field}={date_value}")
        
        # 验证国家（支持emoji格式和标准格式）
        country = record.get('country', '').lower()
        valid_countries = ['canada', 'australia', 'ca', 'au', '🇨🇦', '🇦🇺', 
                          '🇨🇦 canada', '🇦🇺 australia']
        if country and not any(valid in country for valid in valid_countries):
            errors.append(f"不支持的国家: {country}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def _validate_date(cls, date_str: str) -> bool:
        """验证日期字符串格式"""
        formats = ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y']
        for fmt in formats:
            try:
                datetime.strptime(str(date_str), fmt)
                return True
            except ValueError:
                continue
        return False
    
    @classmethod
    def normalize_province(cls, province: str, country: str = 'Canada') -> str:
        """标准化省/州名称"""
        if not province:
            return ''
        
        province_lower = province.lower().strip()
        
        if country.lower() in ['canada', 'ca', '🇨🇦']:
            return cls.CANADA_PROVINCES.get(province_lower, province.title())
        elif country.lower() in ['australia', 'au', '🇦🇺']:
            return cls.AUSTRALIA_STATES.get(province_lower, province.title())
        
        return province.title()
    
    @classmethod
    def normalize_country(cls, country: str) -> str:
        """标准化国家名称（带emoji）"""
        if not country:
            return ''
        
        country_lower = country.lower().strip()
        
        if country_lower in ['canada', 'ca', 'can', '🇨🇦']:
            return '🇨🇦 Canada'
        elif country_lower in ['australia', 'au', 'aus', '🇦🇺']:
            return '🇦🇺 Australia'
        
        return country
    
    @classmethod
    def clean_phone(cls, phone: str) -> str:
        """清洗电话号码"""
        if not phone:
            return ''
        
        # 移除所有非数字字符（保留+号）
        cleaned = re.sub(r'[^\d+]', '', str(phone))
        
        # 格式化北美电话号码
        if len(cleaned) == 10:
            return f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
        elif len(cleaned) == 11 and cleaned[0] == '1':
            return f"+1 ({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:]}"
        
        return cleaned
    
    @classmethod
    def clean_email(cls, email: str) -> str:
        """清洗和验证邮箱"""
        if not email:
            return ''
        
        email = str(email).strip().lower()
        
        # 简单邮箱格式验证
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, email):
            return email
        
        return ''
    
    @classmethod
    def clean_capacity(cls, capacity) -> Optional[int]:
        """清洗容量值"""
        if capacity is None or capacity == '':
            return None
        
        if isinstance(capacity, (int, float)):
            return int(capacity)
        
        if isinstance(capacity, str):
            # 移除非数字字符
            numbers = re.findall(r'\d+', capacity)
            if numbers:
                return int(numbers[0])
        
        return None
    
    @classmethod
    def is_major_city(cls, city: str, country: str = None) -> bool:
        """判断是否为主要城市"""
        if not city:
            return False
        
        city_lower = city.lower().strip()
        
        if country and country.lower() in ['canada', 'ca', '🇨🇦']:
            return city_lower in cls.CANADA_MAJOR_CITIES
        elif country and country.lower() in ['australia', 'au', '🇦🇺']:
            return city_lower in cls.AUSTRALIA_MAJOR_CITIES
        
        # 如果未指定国家，检查所有城市
        return city_lower in cls.CANADA_MAJOR_CITIES or city_lower in cls.AUSTRALIA_MAJOR_CITIES
