"""
去重模块
负责检测和过滤重复记录
"""

from typing import Dict, List, Set
from fuzzywuzzy import fuzz

from utils.logger import get_logger
from utils.helpers import generate_record_id


class Deduplicator:
    """去重处理器"""
    
    # 地址相似度阈值（0-100）
    ADDRESS_SIMILARITY_THRESHOLD = 90
    
    def __init__(self, sheets_manager=None):
        """
        初始化去重器
        
        Args:
            sheets_manager: SheetsManager实例，用于获取历史数据
        """
        self.logger = get_logger()
        self.sheets_manager = sheets_manager
        
        # 缓存已存在的数据
        self._existing_licenses: Set[str] = set()
        self._existing_addresses: Set[str] = set()
        self._initialized = False
    
    def _load_existing_data(self):
        """从Google Sheets加载已存在的数据"""
        if self._initialized or self.sheets_manager is None:
            return
        
        try:
            self.logger.info("📂 加载历史数据用于去重...")
            
            # 获取已存在的许可证号
            self._existing_licenses = self.sheets_manager.get_existing_license_numbers()
            self.logger.info(f"   已加载 {len(self._existing_licenses)} 个许可证号")
            
            # 获取已存在的地址
            self._existing_addresses = self.sheets_manager.get_existing_addresses()
            self.logger.info(f"   已加载 {len(self._existing_addresses)} 个地址")
            
            self._initialized = True
            
        except Exception as e:
            self.logger.warning(f"⚠️ 加载历史数据失败: {str(e)}")
            self._initialized = True  # 避免重复尝试
    
    def remove_duplicates(self, records: List[Dict]) -> List[Dict]:
        """
        移除重复记录
        
        去重逻辑优先级：
        1. 许可证号完全匹配
        2. 地址+名称组合完全匹配
        3. 地址模糊匹配（相似度>90%）
        
        Args:
            records: 原始记录列表
            
        Returns:
            去重后的记录列表
        """
        if not records:
            return []
        
        # 加载历史数据
        self._load_existing_data()
        
        self.logger.info(f"\n🔍 开始去重处理: {len(records)} 条记录")
        
        unique_records = []
        seen_licenses = set(self._existing_licenses)
        seen_addresses = set(self._existing_addresses)
        seen_names_addresses = set()
        
        duplicates = {
            'license': 0,
            'name_address': 0,
            'fuzzy_address': 0
        }
        
        for record in records:
            license_number = record.get('license_number', '').strip()
            address = record.get('address', '').lower().strip()
            name = record.get('name', '').lower().strip()
            
            # 1. 许可证号去重
            if license_number:
                if license_number in seen_licenses:
                    duplicates['license'] += 1
                    continue
                seen_licenses.add(license_number)
            
            # 2. 名称+地址组合去重
            name_address_key = f"{name}|{address}"
            if name_address_key in seen_names_addresses:
                duplicates['name_address'] += 1
                continue
            seen_names_addresses.add(name_address_key)
            
            # 3. 地址模糊匹配去重
            if address and self._is_similar_address(address, seen_addresses):
                duplicates['fuzzy_address'] += 1
                continue
            
            if address:
                seen_addresses.add(address)
            
            # 通过所有去重检查
            unique_records.append(record)
        
        # 输出去重统计
        total_duplicates = sum(duplicates.values())
        self.logger.info(f"📊 去重结果:")
        self.logger.info(f"   - 原始记录: {len(records)} 条")
        self.logger.info(f"   - 重复记录: {total_duplicates} 条")
        self.logger.info(f"     └ 许可证重复: {duplicates['license']} 条")
        self.logger.info(f"     └ 名称+地址重复: {duplicates['name_address']} 条")
        self.logger.info(f"     └ 地址模糊重复: {duplicates['fuzzy_address']} 条")
        self.logger.info(f"   - 唯一记录: {len(unique_records)} 条")
        
        return unique_records
    
    def _is_similar_address(self, address: str, existing_addresses: Set[str]) -> bool:
        """
        检查地址是否与已存在的地址相似
        
        Args:
            address: 要检查的地址
            existing_addresses: 已存在的地址集合
            
        Returns:
            是否存在相似地址
        """
        if not address or not existing_addresses:
            return False
        
        # 对于大量地址，只抽样检查以提高性能
        addresses_to_check = existing_addresses
        if len(existing_addresses) > 1000:
            # 如果地址太多，先做精确匹配检查
            if address in existing_addresses:
                return True
            # 不做模糊匹配（太耗时）
            return False
        
        for existing in addresses_to_check:
            # 使用token_sort_ratio处理词序不同的情况
            similarity = fuzz.token_sort_ratio(address, existing)
            if similarity >= self.ADDRESS_SIMILARITY_THRESHOLD:
                return True
        
        return False
    
    def dedupe_within_batch(self, records: List[Dict]) -> List[Dict]:
        """
        在单个批次内去重（不与历史数据比较）
        
        Args:
            records: 记录列表
            
        Returns:
            去重后的记录列表
        """
        if not records:
            return []
        
        unique_records = []
        seen_ids = set()
        
        for record in records:
            # 生成唯一ID
            record_id = generate_record_id(record)
            
            if record_id not in seen_ids:
                seen_ids.add(record_id)
                unique_records.append(record)
        
        return unique_records
