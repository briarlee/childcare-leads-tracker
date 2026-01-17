"""
配置管理模块
集中管理所有系统配置，从环境变量加载
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class Config:
    """系统配置类"""
    
    # ==================== Google Sheets ====================
    GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', '幼儿园商机追踪')
    GOOGLE_SHEET_URL = os.getenv('GOOGLE_SHEET_URL', '')
    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    
    # ==================== PushPlus ====================
    PUSHPLUS_TOKEN = os.getenv('PUSHPLUS_TOKEN', '')
    PUSHPLUS_TOPIC = os.getenv('PUSHPLUS_TOPIC', '')
    PUSHPLUS_WEBHOOK = os.getenv('PUSHPLUS_WEBHOOK', '')
    
    # ==================== 钉钉 ====================
    DINGTALK_WEBHOOK = os.getenv('DINGTALK_WEBHOOK', '')
    DINGTALK_SECRET = os.getenv('DINGTALK_SECRET', '')
    
    # ==================== Claude AI ====================
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')
    
    # ==================== 评分阈值 ====================
    CRITICAL_THRESHOLD = int(os.getenv('CRITICAL_THRESHOLD', '90'))
    HIGH_THRESHOLD = int(os.getenv('HIGH_THRESHOLD', '85'))
    MEDIUM_THRESHOLD = int(os.getenv('MEDIUM_THRESHOLD', '70'))
    LOW_THRESHOLD = int(os.getenv('LOW_THRESHOLD', '0'))
    
    # ==================== 通知开关 ====================
    ENABLE_PUSHPLUS = os.getenv('ENABLE_PUSHPLUS', 'true').lower() == 'true'
    ENABLE_DINGTALK = os.getenv('ENABLE_DINGTALK', 'true').lower() == 'true'
    ENABLE_INSTANT_ALERTS = os.getenv('ENABLE_INSTANT_ALERTS', 'true').lower() == 'true'
    ENABLE_SOUND_ALERTS = os.getenv('ENABLE_SOUND_ALERTS', 'true').lower() == 'true'
    ENABLE_CLAUDE_AI = os.getenv('ENABLE_CLAUDE_AI', 'true').lower() == 'true'
    
    # ==================== 推送控制 ====================
    BATCH_INTERVAL = int(os.getenv('BATCH_INTERVAL', '300'))
    MAX_INSTANT_ALERTS_PER_HOUR = int(os.getenv('MAX_INSTANT_ALERTS_PER_HOUR', '20'))
    DAILY_SUMMARY_TIME = os.getenv('DAILY_SUMMARY_TIME', '09:00')
    
    # ==================== 数据源 ====================
    ENABLED_SOURCES = os.getenv('ENABLED_SOURCES', 'ontario,acecqa').split(',')
    FETCH_TIMEOUT = int(os.getenv('FETCH_TIMEOUT', '30'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    
    # ==================== 运行模式 ====================
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # ==================== 其他 ====================
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Shanghai')
    MAX_RECORDS_PER_RUN = int(os.getenv('MAX_RECORDS_PER_RUN', '100'))
    
    # ==================== 数据源URL ====================
    # Ontario Open Data - Licensed Child Care Facilities
    ONTARIO_DATA_URL = "https://data.ontario.ca/dataset/868c8634-96e4-4878-abe7-e0c18c604a49/resource/8f7e7b09-0f09-4c40-a5bd-8e5a1e1a4916/download/lcc_facilities.csv"
    
    # BC Child Care Map Data
    BC_DATA_URL = "https://catalogue.data.gov.bc.ca/dataset/child-care-map-data/resource/9a9f14e1-03a0-4b7c-a8fc-ca8fcd1b8bb1/download/childcarebc.csv"
    
    # ACECQA National Registers (需要从网页获取最新链接)
    ACECQA_DATA_URL = "https://www.acecqa.gov.au/resources/national-registers"
    
    @classmethod
    def validate(cls) -> list:
        """验证必要配置是否已设置"""
        errors = []
        
        # Google Sheets必须配置
        if not cls.GOOGLE_SHEET_NAME:
            errors.append("GOOGLE_SHEET_NAME 未配置")
        
        # 至少启用一个通知渠道
        if not cls.ENABLE_PUSHPLUS and not cls.ENABLE_DINGTALK:
            errors.append("至少需要启用一个通知渠道 (PUSHPLUS 或 DINGTALK)")
        
        # 检查PushPlus配置
        if cls.ENABLE_PUSHPLUS and not cls.PUSHPLUS_TOKEN:
            errors.append("启用了PushPlus但未配置 PUSHPLUS_TOKEN")
        
        # 检查钉钉配置
        if cls.ENABLE_DINGTALK and not cls.DINGTALK_WEBHOOK:
            errors.append("启用了钉钉但未配置 DINGTALK_WEBHOOK")
        
        # 检查Claude AI配置
        if cls.ENABLE_CLAUDE_AI and not cls.ANTHROPIC_API_KEY:
            errors.append("启用了Claude AI但未配置 ANTHROPIC_API_KEY")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """打印当前配置（隐藏敏感信息）"""
        print("=" * 50)
        print("📋 系统配置")
        print("=" * 50)
        print(f"Google Sheet: {cls.GOOGLE_SHEET_NAME}")
        print(f"启用PushPlus: {cls.ENABLE_PUSHPLUS}")
        print(f"启用钉钉: {cls.ENABLE_DINGTALK}")
        print(f"启用Claude AI: {cls.ENABLE_CLAUDE_AI}")
        print(f"数据源: {', '.join(cls.ENABLED_SOURCES)}")
        print(f"调试模式: {cls.DEBUG_MODE}")
        print(f"演习模式: {cls.DRY_RUN}")
        print("=" * 50)


# 创建全局配置实例
config = Config()
