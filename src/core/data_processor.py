"""
数据处理模块
负责数据清洗、标准化和转换
"""

from typing import Dict, List, Optional
from datetime import datetime

from ..utils.validators import DataValidator
from ..utils.helpers import clean_string, format_date, get_today
from ..utils.logger import get_logger


class DataProcessor:
    """数据处理器"""
    
    def __init__(self):
        self.logger = get_logger()
        self.validator = DataValidator()
    
    def process_records(self, records: List[Dict], record_type: str = 'new_project') -> List[Dict]:
        """
        处理记录列表
        
        Args:
            records: 原始记录列表
            record_type: 记录类型
            
        Returns:
            处理后的记录列表
        """
        processed = []
        errors = []
        
        for i, record in enumerate(records):
            try:
                # 标准化记录
                normalized = self.normalize_record(record)
                
                # 验证记录
                is_valid, validation_errors = DataValidator.validate_record(normalized, record_type)
                
                if is_valid:
                    processed.append(normalized)
                else:
                    errors.append({
                        'index': i,
                        'record': record.get('name', 'Unknown'),
                        'errors': validation_errors
                    })
            except Exception as e:
                errors.append({
                    'index': i,
                    'record': record.get('name', 'Unknown'),
                    'errors': [str(e)]
                })
        
        # 记录处理结果
        if errors:
            self.logger.warning(f"⚠️ {len(errors)} 条记录验证失败")
            for err in errors[:5]:  # 只显示前5条错误
                self.logger.debug(f"   - {err['record']}: {err['errors']}")
        
        self.logger.info(f"✅ 成功处理 {len(processed)}/{len(records)} 条记录")
        
        return processed
    
    def normalize_record(self, record: Dict) -> Dict:
        """
        标准化单条记录
        
        Args:
            record: 原始记录
            
        Returns:
            标准化后的记录
        """
        normalized = {}
        
        # 基础字段
        normalized['name'] = clean_string(record.get('name', ''))
        normalized['address'] = clean_string(record.get('address', ''))
        normalized['city'] = clean_string(record.get('city', '')).title()
        
        # 国家和省份标准化
        country = record.get('country', '')
        normalized['country'] = DataValidator.normalize_country(country)
        normalized['province'] = DataValidator.normalize_province(
            record.get('province', ''),
            country
        )
        
        # 容量
        normalized['capacity'] = DataValidator.clean_capacity(record.get('capacity'))
        
        # 联系方式
        normalized['phone'] = DataValidator.clean_phone(record.get('phone', ''))
        normalized['email'] = DataValidator.clean_email(record.get('email', ''))
        
        # 许可证信息
        normalized['license_number'] = clean_string(record.get('license_number', ''))
        normalized['license_status'] = record.get('license_status', '')
        
        # 日期
        normalized['discovered_date'] = format_date(
            record.get('discovered_date') or get_today()
        )
        
        # 来源信息
        normalized['source'] = record.get('source', '')
        normalized['source_url'] = record.get('source_url', '')
        
        # AI评分相关
        normalized['ai_score'] = record.get('ai_score', 50)
        normalized['priority'] = record.get('priority', 'Medium')
        normalized['ai_reasoning'] = record.get('ai_reasoning', '')
        normalized['ai_recommendation'] = record.get('ai_recommendation', '')
        
        # 其他字段
        normalized['notes'] = record.get('notes', '')
        normalized['type'] = record.get('type', '新建')
        
        # 交易相关字段
        if 'price' in record:
            normalized['price'] = record.get('price', '')
        if 'annual_revenue' in record:
            normalized['annual_revenue'] = record.get('annual_revenue', '')
        if 'cash_flow' in record:
            normalized['cash_flow'] = record.get('cash_flow', '')
        if 'lease_remaining' in record:
            normalized['lease_remaining'] = record.get('lease_remaining', '')
        if 'property_type' in record:
            normalized['property_type'] = record.get('property_type', '')
        
        # 招标相关字段
        if 'published_date' in record:
            normalized['published_date'] = format_date(record.get('published_date'))
        if 'deadline_date' in record:
            normalized['deadline_date'] = format_date(record.get('deadline_date'))
        if 'contract_value' in record:
            normalized['contract_value'] = record.get('contract_value', '')
        if 'tender_type' in record:
            normalized['tender_type'] = record.get('tender_type', '')
        if 'organization' in record:
            normalized['organization'] = record.get('organization', '')
        
        return normalized
    
    def classify_records(self, records: List[Dict]) -> Dict[str, List[Dict]]:
        """
        将记录按类型分类
        
        Args:
            records: 记录列表
            
        Returns:
            分类后的记录字典
        """
        classified = {
            'new_projects': [],
            'sales': [],
            'tenders': []
        }
        
        for record in records:
            record_type = record.get('type', '').lower()
            
            if record_type in ['新建', 'new', '新建项目', 'new_project']:
                classified['new_projects'].append(record)
            elif record_type in ['交易', 'sale', '买卖', '出售']:
                classified['sales'].append(record)
            elif record_type in ['招标', 'tender', 'rfp', 'rfq']:
                classified['tenders'].append(record)
            else:
                # 默认为新建项目
                classified['new_projects'].append(record)
        
        return classified
    
    def sort_by_score(self, records: List[Dict], descending: bool = True) -> List[Dict]:
        """
        按AI评分排序
        
        Args:
            records: 记录列表
            descending: 是否降序
            
        Returns:
            排序后的记录列表
        """
        return sorted(
            records,
            key=lambda x: x.get('ai_score', 0),
            reverse=descending
        )
    
    def filter_by_priority(self, records: List[Dict], priorities: List[str]) -> List[Dict]:
        """
        按优先级过滤
        
        Args:
            records: 记录列表
            priorities: 要保留的优先级列表
            
        Returns:
            过滤后的记录列表
        """
        priorities_lower = [p.lower() for p in priorities]
        return [
            r for r in records
            if r.get('priority', '').lower() in priorities_lower
        ]
    
    def get_statistics(self, records: List[Dict]) -> Dict:
        """
        计算记录统计信息
        
        Args:
            records: 记录列表
            
        Returns:
            统计字典
        """
        stats = {
            'total': len(records),
            'canada_new': 0,
            'canada_sales': 0,
            'canada_tenders': 0,
            'australia_new': 0,
            'australia_sales': 0,
            'australia_tenders': 0,
            'critical_count': 0,
            'high_count': 0,
            'medium_count': 0,
            'low_count': 0
        }
        
        for record in records:
            country = record.get('country', '').lower()
            record_type = record.get('type', '').lower()
            priority = record.get('priority', '').lower()
            
            # 按国家和类型统计
            if 'canada' in country or '🇨🇦' in country:
                if record_type in ['新建', 'new', 'new_project']:
                    stats['canada_new'] += 1
                elif record_type in ['交易', 'sale']:
                    stats['canada_sales'] += 1
                elif record_type in ['招标', 'tender']:
                    stats['canada_tenders'] += 1
            elif 'australia' in country or '🇦🇺' in country:
                if record_type in ['新建', 'new', 'new_project']:
                    stats['australia_new'] += 1
                elif record_type in ['交易', 'sale']:
                    stats['australia_sales'] += 1
                elif record_type in ['招标', 'tender']:
                    stats['australia_tenders'] += 1
            
            # 按优先级统计
            if priority == 'critical':
                stats['critical_count'] += 1
            elif priority == 'high':
                stats['high_count'] += 1
            elif priority == 'medium':
                stats['medium_count'] += 1
            else:
                stats['low_count'] += 1
        
        return stats
