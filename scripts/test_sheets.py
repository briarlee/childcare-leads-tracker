#!/usr/bin/env python3
"""
Google Sheets 测试脚本
用于测试Google Sheets连接和读写功能
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / '.env')


def test_sheets():
    """测试Google Sheets连接"""
    
    print("=" * 50)
    print("🧪 Google Sheets 连接测试")
    print("=" * 50)
    
    sheet_name = os.getenv('GOOGLE_SHEET_NAME')
    sheet_url = os.getenv('GOOGLE_SHEET_URL')
    credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    
    print(f"📋 Sheet名称: {sheet_name or '(未配置)'}")
    print(f"🔗 Sheet URL: {sheet_url[:50] + '...' if sheet_url and len(sheet_url) > 50 else sheet_url or '(未配置)'}")
    print(f"🔑 凭证文件: {credentials_path}")
    
    # 检查凭证文件
    creds_full_path = Path(__file__).parent.parent / credentials_path
    if not creds_full_path.exists():
        print(f"\n❌ 错误: 凭证文件不存在: {creds_full_path}")
        print("请按照 README.md 中的说明创建 credentials.json")
        return False
    
    print(f"✅ 凭证文件存在: {creds_full_path}")
    
    # 尝试连接
    print("\n📡 尝试连接Google Sheets...")
    
    try:
        from core.sheets_manager import SheetsManager
        
        sheets = SheetsManager()
        
        print("✅ 连接成功！")
        print(f"📊 电子表格URL: {sheets.get_sheet_url()}")
        
        # 列出工作表
        worksheets = sheets.spreadsheet.worksheets()
        print(f"\n📋 工作表列表 ({len(worksheets)} 个):")
        for ws in worksheets:
            print(f"   - {ws.title}")
        
        # 测试写入（可选）
        print("\n🔍 跳过写入测试（避免产生测试数据）")
        print("   如需测试写入，请设置 DRY_RUN=true 后运行主程序")
        
        # 测试读取
        print("\n📖 测试读取现有许可证号...")
        existing_licenses = sheets.get_existing_license_numbers()
        print(f"   已有许可证号: {len(existing_licenses)} 个")
        
        existing_addresses = sheets.get_existing_addresses()
        print(f"   已有地址: {len(existing_addresses)} 个")
        
        print("\n" + "=" * 50)
        print("✅ Google Sheets 测试完成 - 全部通过")
        print("=" * 50)
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n❌ 凭证文件错误: {str(e)}")
        return False
        
    except Exception as e:
        print(f"\n❌ 连接失败: {str(e)}")
        print("\n可能的原因:")
        print("1. credentials.json 格式不正确")
        print("2. 服务账号没有访问电子表格的权限")
        print("3. GOOGLE_SHEET_URL 配置不正确")
        print("4. Google Sheets API 未启用")
        return False


if __name__ == '__main__':
    success = test_sheets()
    sys.exit(0 if success else 1)
