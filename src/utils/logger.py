"""
日志记录模块
提供统一的日志配置和记录功能
"""

import os
import logging
from datetime import datetime
from pathlib import Path

# 全局日志实例
_logger = None


def setup_logger(name: str = "childcare_leads", log_dir: str = None) -> logging.Logger:
    """
    设置并返回日志记录器
    
    Args:
        name: 日志记录器名称
        log_dir: 日志目录路径，默认为项目根目录下的logs/
        
    Returns:
        配置好的Logger实例
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    
    # 从环境变量获取日志级别
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # 创建日志格式
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / 'logs'
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 按日期命名的日志文件
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = log_dir / f'run_{today}.log'
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """获取全局日志记录器"""
    global _logger
    if _logger is None:
        return setup_logger()
    return _logger


class LoggerMixin:
    """日志混入类，可被其他类继承使用"""
    
    @property
    def logger(self) -> logging.Logger:
        return get_logger()
