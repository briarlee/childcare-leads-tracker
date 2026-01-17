"""
评分模块
基于规则的商机评分算法（不依赖Claude AI）
"""

from typing import Dict, List
from ..utils.logger import get_logger
from ..config import config


class Scorer:
    """商机评分器"""
    
    # 加拿大主要城市评分
    CANADA_CITY_SCORES = {
        # 一线城市 (40分)
        'toronto': 40, 'vancouver': 40, 'montreal': 40,
        # 二线城市 (35分)
        'calgary': 35, 'edmonton': 35, 'ottawa': 35, 'winnipeg': 35,
        # 三线城市 (30分)
        'quebec city': 30, 'hamilton': 30, 'kitchener': 30, 'london': 30,
        'victoria': 30, 'halifax': 30,
        # 其他城市 (25分)
        'oshawa': 25, 'windsor': 25, 'saskatoon': 25, 'regina': 25,
        'st. catharines': 25, 'kelowna': 25, 'barrie': 25,
    }
    
    # 澳大利亚主要城市评分
    AUSTRALIA_CITY_SCORES = {
        # 一线城市 (40分)
        'sydney': 40, 'melbourne': 40, 'brisbane': 40,
        # 二线城市 (35分)
        'perth': 35, 'adelaide': 35, 'canberra': 35,
        # 三线城市 (30分)
        'gold coast': 30, 'newcastle': 30, 'sunshine coast': 30,
        'wollongong': 30, 'hobart': 30, 'geelong': 30,
        # 其他城市 (25分)
        'townsville': 25, 'cairns': 25, 'darwin': 25,
        'toowoomba': 25, 'ballarat': 25, 'bendigo': 25,
    }
    
    def __init__(self):
        self.logger = get_logger()
    
    def score_record(self, record: Dict) -> Dict:
        """
        评分单条记录
        
        评分标准（总分100分）：
        1. 容量规模（30分）
        2. 地理位置（40分）
        3. 项目阶段（30分）
        
        Args:
            record: 记录字典
            
        Returns:
            包含评分的记录字典
        """
        # 1. 容量评分 (30分)
        capacity_score = self._score_capacity(record.get('capacity'))
        
        # 2. 地理位置评分 (40分)
        location_score = self._score_location(
            record.get('city', ''),
            record.get('country', '')
        )
        
        # 3. 项目阶段评分 (30分)
        stage_score = self._score_stage(
            record.get('type', ''),
            record.get('license_status', '')
        )
        
        # 总分
        total_score = capacity_score + location_score + stage_score
        
        # 特殊加分项
        bonus = self._calculate_bonus(record)
        total_score = min(100, total_score + bonus)
        
        # 确定优先级
        priority = self._determine_priority(total_score)
        
        # 更新记录
        record['ai_score'] = total_score
        record['capacity_score'] = capacity_score
        record['location_score'] = location_score
        record['stage_score'] = stage_score
        record['priority'] = priority
        record['scoring_method'] = 'rule_based'
        
        return record
    
    def _score_capacity(self, capacity) -> int:
        """
        容量评分
        
        - 80+儿童 = 30分
        - 60-79儿童 = 25分
        - 40-59儿童 = 20分
        - 20-39儿童 = 15分
        - <20儿童 = 10分
        """
        if capacity is None:
            return 15  # 未知容量给中等分
        
        try:
            capacity = int(capacity)
        except (ValueError, TypeError):
            return 15
        
        if capacity >= 80:
            return 30
        elif capacity >= 60:
            return 25
        elif capacity >= 40:
            return 20
        elif capacity >= 20:
            return 15
        else:
            return 10
    
    def _score_location(self, city: str, country: str) -> int:
        """
        地理位置评分
        
        根据城市规模评分（40分满分）
        """
        if not city:
            return 20  # 未知城市给中等分
        
        city_lower = city.lower().strip()
        country_lower = country.lower() if country else ''
        
        # 根据国家选择评分表
        if 'canada' in country_lower or '🇨🇦' in country_lower:
            score = self.CANADA_CITY_SCORES.get(city_lower)
            if score:
                return score
            # 未知加拿大城市
            return 20
        
        elif 'australia' in country_lower or '🇦🇺' in country_lower:
            score = self.AUSTRALIA_CITY_SCORES.get(city_lower)
            if score:
                return score
            # 未知澳大利亚城市
            return 20
        
        # 其他国家
        return 20
    
    def _score_stage(self, project_type: str, license_status: str) -> int:
        """
        项目阶段评分
        
        - 新建项目 = 30分
        - 扩建项目 = 25分
        - 许可变更 = 20分
        - 续期 = 15分
        """
        project_type_lower = project_type.lower() if project_type else ''
        status_lower = license_status.lower() if license_status else ''
        
        # 新建项目
        if any(k in project_type_lower for k in ['新建', 'new', '新发']):
            return 30
        if any(k in status_lower for k in ['新发', 'new', 'issued']):
            return 30
        
        # 扩建项目
        if any(k in project_type_lower for k in ['扩建', 'expansion', 'expand']):
            return 25
        if any(k in status_lower for k in ['扩容', 'expansion']):
            return 25
        
        # 许可变更
        if any(k in status_lower for k in ['变更', 'change', 'amendment']):
            return 20
        
        # 续期
        if any(k in status_lower for k in ['续期', 'renewal', 'renew']):
            return 15
        
        # 交易/招标类型
        if any(k in project_type_lower for k in ['交易', 'sale', '出售']):
            return 25
        if any(k in project_type_lower for k in ['招标', 'tender', 'rfp']):
            return 25
        
        # 默认
        return 20
    
    def _calculate_bonus(self, record: Dict) -> int:
        """
        计算特殊加分项
        
        + 政府资助项目 = +5分
        + 新开发区域 = +5分
        """
        bonus = 0
        
        notes = str(record.get('notes', '')).lower()
        name = str(record.get('name', '')).lower()
        
        # 政府相关
        if any(k in name or k in notes for k in ['government', 'public', 'municipal', '政府']):
            bonus += 5
        
        # 学校/社区中心附近
        if any(k in name or k in notes for k in ['school', 'community', '学校', '社区']):
            bonus += 5
        
        return bonus
    
    def _determine_priority(self, score: int) -> str:
        """
        根据评分确定优先级
        
        - Critical（紧急）: ≥90分
        - High（高优先级）: 85-89分
        - Medium（中优先级）: 70-84分
        - Low（低优先级）: <70分
        """
        if score >= config.CRITICAL_THRESHOLD:
            return 'Critical'
        elif score >= config.HIGH_THRESHOLD:
            return 'High'
        elif score >= config.MEDIUM_THRESHOLD:
            return 'Medium'
        else:
            return 'Low'
    
    def batch_score(self, records: List[Dict]) -> List[Dict]:
        """
        批量评分
        
        Args:
            records: 记录列表
            
        Returns:
            评分后的记录列表
        """
        if not records:
            return []
        
        self.logger.info(f"\n📊 开始评分: {len(records)} 条记录")
        
        scored_records = []
        score_distribution = {
            'Critical': 0,
            'High': 0,
            'Medium': 0,
            'Low': 0
        }
        
        for record in records:
            scored = self.score_record(record)
            scored_records.append(scored)
            score_distribution[scored['priority']] += 1
        
        # 输出评分分布
        self.logger.info(f"📈 评分分布:")
        self.logger.info(f"   🚨 Critical: {score_distribution['Critical']} 条")
        self.logger.info(f"   🔥 High: {score_distribution['High']} 条")
        self.logger.info(f"   📌 Medium: {score_distribution['Medium']} 条")
        self.logger.info(f"   📋 Low: {score_distribution['Low']} 条")
        
        return scored_records
