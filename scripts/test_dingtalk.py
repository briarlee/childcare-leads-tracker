#!/usr/bin/env python3
"""
钉钉机器人 测试脚本
用于测试钉钉群机器人推送是否正常工作
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


def test_dingtalk():
    """测试钉钉推送"""
    
    print("=" * 50)
    print("🧪 钉钉机器人 推送测试")
    print("=" * 50)
    
    webhook = os.getenv('DINGTALK_WEBHOOK')
    secret = os.getenv('DINGTALK_SECRET')
    
    if not webhook:
        print("❌ 错误: DINGTALK_WEBHOOK 未配置")
        print("请在 .env 文件中设置 DINGTALK_WEBHOOK")
        return False
    
    print(f"✅ Webhook: {webhook[:50]}...")
    print(f"✅ Secret: {'已配置' if secret else '未配置（可能使用其他安全设置）'}")
    
    # 导入通知器
    from notifiers.dingtalk_notifier import DingTalkNotifier
    
    notifier = DingTalkNotifier()
    
    if not notifier.enabled:
        print("❌ 钉钉机器人 未启用")
        return False
    
    # 发送测试消息
    print("\n📤 发送测试消息...")
    
    # 测试简单文本消息
    print("\n1️⃣ 测试文本消息...")
    result1 = notifier.send_text(
        f"🧪 这是一条测试消息\n发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print(f"   结果: {'✅ 成功' if result1 else '❌ 失败'}")
    
    # 测试Markdown消息
    print("\n2️⃣ 测试Markdown消息...")
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
        'source_url': 'https://example.com',
        'capacity_score': 30,
        'location_score': 40,
        'stage_score': 22
    }
    
    result2 = notifier.send_critical_alert(test_lead, at_all=False)  # 测试时不@所有人
    print(f"   结果: {'✅ 成功' if result2 else '❌ 失败'}")
    
    # 测试每日摘要
    print("\n3️⃣ 测试每日摘要...")
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
    
    result3 = notifier.send_daily_summary(summary_data)
    print(f"   结果: {'✅ 成功' if result3 else '❌ 失败'}")
    
    # 总结
    print("\n" + "=" * 50)
    if result1 and result2 and result3:
        print("✅ 钉钉机器人 测试完成 - 全部通过")
        print("请检查钉钉群是否收到消息")
    else:
        print("⚠️ 钉钉机器人 测试完成 - 部分失败")
    print("=" * 50)
    
    return result1 and result2 and result3


if __name__ == '__main__':
    success = test_dingtalk()
    sys.exit(0 if success else 1)
