"""
辅助函数模块
提供各种通用辅助功能
"""

import re
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional


def generate_record_id(record: Dict) -> str:
    """
    生成记录的唯一标识符
    
    Args:
        record: 记录字典
        
    Returns:
        MD5哈希字符串
    """
    # 使用关键字段生成唯一ID
    key_fields = [
        record.get('license_number', ''),
        record.get('name', ''),
        record.get('address', ''),
        record.get('city', ''),
        record.get('country', '')
    ]
    
    key_string = '|'.join(str(f).lower().strip() for f in key_fields)
    return hashlib.md5(key_string.encode()).hexdigest()[:16]


def format_date(date_input, output_format: str = '%Y-%m-%d') -> str:
    """
    格式化日期
    
    Args:
        date_input: 日期字符串或datetime对象
        output_format: 输出格式
        
    Returns:
        格式化后的日期字符串
    """
    if date_input is None:
        return ''
    
    if isinstance(date_input, datetime):
        return date_input.strftime(output_format)
    
    if isinstance(date_input, str):
        # 尝试多种输入格式
        input_formats = [
            '%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y',
            '%Y-%m-%d %H:%M:%S', '%Y%m%d'
        ]
        
        for fmt in input_formats:
            try:
                dt = datetime.strptime(date_input.strip(), fmt)
                return dt.strftime(output_format)
            except ValueError:
                continue
    
    return str(date_input)


def get_today() -> str:
    """获取今天的日期字符串 (YYYY-MM-DD)"""
    return datetime.now().strftime('%Y-%m-%d')


def get_now() -> str:
    """获取当前时间字符串 (YYYY-MM-DD HH:MM:SS)"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def truncate_string(s: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    截断字符串到指定长度
    
    Args:
        s: 输入字符串
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        截断后的字符串
    """
    if not s or len(s) <= max_length:
        return s or ''
    
    return s[:max_length - len(suffix)] + suffix


def clean_string(s: str) -> str:
    """
    清洗字符串：去除多余空白、特殊字符
    
    Args:
        s: 输入字符串
        
    Returns:
        清洗后的字符串
    """
    if not s:
        return ''
    
    # 转换为字符串
    s = str(s)
    
    # 替换多个空白字符为单个空格
    s = re.sub(r'\s+', ' ', s)
    
    # 去除首尾空白
    s = s.strip()
    
    return s


def extract_postal_code(address: str, country: str = 'Canada') -> Optional[str]:
    """
    从地址中提取邮政编码
    
    Args:
        address: 地址字符串
        country: 国家
        
    Returns:
        邮政编码或None
    """
    if not address:
        return None
    
    address = str(address).upper()
    
    if country.lower() in ['canada', 'ca', '🇨🇦']:
        # 加拿大邮编格式: A1A 1A1 或 A1A1A1
        pattern = r'[A-Z]\d[A-Z]\s?\d[A-Z]\d'
        match = re.search(pattern, address)
        if match:
            return match.group().replace(' ', '')
    
    elif country.lower() in ['australia', 'au', '🇦🇺']:
        # 澳大利亚邮编格式: 4位数字
        pattern = r'\b\d{4}\b'
        matches = re.findall(pattern, address)
        if matches:
            return matches[-1]  # 取最后一个匹配（通常邮编在地址末尾）
    
    return None


def format_currency(amount, currency: str = 'CAD') -> str:
    """
    格式化货币金额
    
    Args:
        amount: 金额
        currency: 货币代码
        
    Returns:
        格式化后的货币字符串
    """
    if amount is None:
        return ''
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return str(amount)
    
    currency_symbols = {
        'CAD': 'C$',
        'AUD': 'A$',
        'USD': '$'
    }
    
    symbol = currency_symbols.get(currency.upper(), '$')
    
    if amount >= 1000000:
        return f"{symbol}{amount/1000000:.1f}M"
    elif amount >= 1000:
        return f"{symbol}{amount/1000:.0f}K"
    else:
        return f"{symbol}{amount:,.0f}"


def get_priority_emoji(priority: str) -> str:
    """
    获取优先级对应的emoji
    
    Args:
        priority: 优先级 (Critical/High/Medium/Low)
        
    Returns:
        对应的emoji
    """
    priority_emojis = {
        'critical': '🚨',
        'high': '🔥',
        'medium': '📌',
        'low': '📋'
    }
    
    return priority_emojis.get(priority.lower(), '📋')


def get_priority_color(priority: str) -> str:
    """
    获取优先级对应的颜色代码
    
    Args:
        priority: 优先级 (Critical/High/Medium/Low)
        
    Returns:
        颜色代码
    """
    priority_colors = {
        'critical': '#FF0000',  # 红色
        'high': '#FF5722',      # 橙红色
        'medium': '#FF9800',    # 橙色
        'low': '#4CAF50'        # 绿色
    }
    
    return priority_colors.get(priority.lower(), '#9E9E9E')


def chunks(lst: list, chunk_size: int):
    """
    将列表分割成指定大小的块
    
    Args:
        lst: 输入列表
        chunk_size: 每块大小
        
    Yields:
        列表块
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def safe_get(d: Dict, *keys, default=None) -> Any:
    """
    安全地从嵌套字典中获取值
    
    Args:
        d: 字典
        *keys: 键路径
        default: 默认值
        
    Returns:
        获取到的值或默认值
    """
    result = d
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return default
        if result is None:
            return default
    return result
