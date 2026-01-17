#!/usr/bin/env python3
"""
PushPlus 测试脚本
用于测试PushPlus微信推送是否正常工作
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


def test_pushplus():
    """测试PushPlus推送"""
    
    print("=" * 50)
    print("🧪 PushPlus 推送测试")
    print("=" * 50)
    
    token = os.getenv('PUSHPLUS_TOKEN')
    topic = os.getenv('PUSHPLUS_TOPIC')
    
    if not token:
        print("❌ 错误: PUSHPLUS_TOKEN 未配置")
        print("请在 .env 文件中设置 PUSHPLUS_TOKEN")
        return False
    
    print(f"✅ Token: {token[:10]}...{token[-4:]}")
    print(f"✅ Topic: {topic or '(未配置，将发送到个人)'}")
    
    # 导入通知器
    from notifiers.pushplus_notifier import PushPlusNotifier
    
    notifier = PushPlusNotifier()
    
    if not notifier.enabled:
        print("❌ PushPlus 未启用")
        return False
    
    # 发送测试消息
    print("\n📤 发送测试消息...")
    
    test_lead = {
        'name': '测试商机 - Test Daycare',
        'city': 'Toronto',
        'province': 'Ontario',
        'country': '🇨🇦 Canada',
        'capacity': 80,
        'type': '新建项目',
        'ai_score': 92,
        'priority': 'Critical',
        'discovered_date': datetime.now().strftime('%Y-%m-%d'),
        'phone': '(416) 123-4567',
        'source': 'Test Script',
        'source_url': 'https://example.com'
    }
    
    # 测试紧急商机通知
    print("\n1️⃣ 测试紧急商机通知...")
    result1 = notifier.send_critical_alert(test_lead)
    print(f"   结果: {'✅ 成功' if result1 else '❌ 失败'}")
    
    # 测试每日摘要
    print("\n2️⃣ 测试每日摘要通知...")
    summary_data = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'canada': {'new_projects': 5, 'sales': 2, 'tenders': 1},
        'australia': {'new_projects': 3, 'sales': 1, 'tenders': 0},
        'high_priority': [test_lead],
        'sources': [
            {'name': 'Ontario Open Data', 'status': '正常', 'count': 5},
            {'name': 'ACECQA', 'status': '正常', 'count': 3}
        ],
        'sheets_url': 'https://docs.google.com/spreadsheets/',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    result2 = notifier.send_daily_summary(summary_data)
    print(f"   结果: {'✅ 成功' if result2 else '❌ 失败'}")
    
    # 总结
    print("\n" + "=" * 50)
    if result1 and result2:
        print("✅ PushPlus 测试完成 - 全部通过")
        print("请检查微信是否收到消息")
    else:
        print("⚠️ PushPlus 测试完成 - 部分失败")
    print("=" * 50)
    
    return result1 and result2


if __name__ == '__main__':
    success = test_pushplus()
    sys.exit(0 if success else 1)
