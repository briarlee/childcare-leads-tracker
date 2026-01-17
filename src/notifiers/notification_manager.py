"""
通知管理模块
统一管理多渠道通知的发送逻辑
"""

from typing import Dict, List
from datetime import datetime

from config import config
from utils.logger import get_logger
from .pushplus_notifier import PushPlusNotifier
from .dingtalk_notifier import DingTalkNotifier


class NotificationManager:
    """通知统一管理器"""
    
    def __init__(self):
        self.logger = get_logger()
        
        # 初始化通知器
        self.pushplus = None
        self.dingtalk = None
        
        if config.ENABLE_PUSHPLUS:
            self.pushplus = PushPlusNotifier()
        
        if config.ENABLE_DINGTALK:
            self.dingtalk = DingTalkNotifier()
        
        # 即时提醒计数器
        self.instant_alerts_count = 0
        self.max_instant_per_hour = config.MAX_INSTANT_ALERTS_PER_HOUR
        
        self.logger.info(f"📱 通知管理器初始化完成")
        self.logger.info(f"   - PushPlus: {'✅ 已启用' if self.pushplus and self.pushplus.enabled else '❌ 未启用'}")
        self.logger.info(f"   - 钉钉: {'✅ 已启用' if self.dingtalk and self.dingtalk.enabled else '❌ 未启用'}")
    
    def notify_critical_lead(self, lead: Dict) -> Dict[str, bool]:
        """
        发送紧急商机通知（双渠道+@所有人）
        
        Args:
            lead: 商机信息
            
        Returns:
            各渠道发送结果
        """
        if not config.ENABLE_INSTANT_ALERTS:
            self.logger.info("ℹ️ 即时提醒已禁用")
            return {'pushplus': False, 'dingtalk': False}
        
        if self.instant_alerts_count >= self.max_instant_per_hour:
            self.logger.warning(f"⚠️ 已达到每小时最大即时提醒次数限制 ({self.max_instant_per_hour})")
            return {'pushplus': False, 'dingtalk': False}
        
        results = {'pushplus': False, 'dingtalk': False}
        
        self.logger.info(f"\n🚨 发送紧急商机通知: {lead.get('name', 'Unknown')}")
        
        # 微信群推送
        if self.pushplus and self.pushplus.enabled:
            results['pushplus'] = self.pushplus.send_critical_alert(lead)
        
        # 钉钉群推送（@所有人）
        if self.dingtalk and self.dingtalk.enabled:
            results['dingtalk'] = self.dingtalk.send_critical_alert(lead, at_all=True)
        
        self.instant_alerts_count += 1
        
        return results
    
    def notify_high_priority_batch(self, leads: List[Dict]) -> Dict[str, bool]:
        """
        发送高优先级商机批量通知（双渠道，不@人）
        
        Args:
            leads: 商机列表
            
        Returns:
            各渠道发送结果
        """
        if not config.ENABLE_INSTANT_ALERTS or len(leads) == 0:
            return {'pushplus': False, 'dingtalk': False}
        
        results = {'pushplus': False, 'dingtalk': False}
        
        self.logger.info(f"\n🔥 发送高优先级批量通知: {len(leads)} 条")
        
        # 微信群推送
        if self.pushplus and self.pushplus.enabled:
            results['pushplus'] = self.pushplus.send_high_priority_batch(leads)
        
        # 钉钉群推送（不@人）
        if self.dingtalk and self.dingtalk.enabled:
            results['dingtalk'] = self.dingtalk.send_high_priority_batch(leads, at_all=False)
        
        return results
    
    def send_daily_summary(self, summary_data: Dict) -> Dict[str, bool]:
        """
        发送每日摘要（双渠道）
        
        Args:
            summary_data: 摘要数据
            
        Returns:
            各渠道发送结果
        """
        results = {'pushplus': False, 'dingtalk': False}
        
        self.logger.info(f"\n📊 发送每日摘要")
        
        # 微信群推送
        if self.pushplus and self.pushplus.enabled:
            results['pushplus'] = self.pushplus.send_daily_summary(summary_data)
        
        # 钉钉群推送
        if self.dingtalk and self.dingtalk.enabled:
            results['dingtalk'] = self.dingtalk.send_daily_summary(summary_data)
        
        return results
    
    def send_error_alert(self, error_msg: str, source: str) -> Dict[str, bool]:
        """
        发送错误警告（仅PushPlus个人，不打扰群组）
        
        Args:
            error_msg: 错误信息
            source: 错误来源
            
        Returns:
            发送结果
        """
        results = {'pushplus': False, 'dingtalk': False}
        
        self.logger.info(f"\n⚠️ 发送错误警告: {source}")
        
        # 只发送到PushPlus个人（不发群组）
        if self.pushplus and self.pushplus.enabled:
            results['pushplus'] = self.pushplus.send_error_alert(error_msg, source, to_group=False)
        
        return results
    
    def process_scored_leads(self, leads: List[Dict]) -> Dict:
        """
        处理评分后的商机，根据优先级发送通知
        
        Args:
            leads: 评分后的商机列表
            
        Returns:
            处理统计
        """
        stats = {
            'critical_notified': 0,
            'high_notified': 0,
            'total': len(leads)
        }
        
        # 分类商机
        critical_leads = [l for l in leads if l.get('priority') == 'Critical']
        high_leads = [l for l in leads if l.get('priority') == 'High']
        
        self.logger.info(f"\n📱 处理通知:")
        self.logger.info(f"   - Critical: {len(critical_leads)} 条")
        self.logger.info(f"   - High: {len(high_leads)} 条")
        
        # 发送Critical通知（逐条发送）
        for lead in critical_leads:
            result = self.notify_critical_lead(lead)
            if result.get('pushplus') or result.get('dingtalk'):
                stats['critical_notified'] += 1
        
        # 发送High优先级批量通知
        if high_leads:
            result = self.notify_high_priority_batch(high_leads)
            if result.get('pushplus') or result.get('dingtalk'):
                stats['high_notified'] = len(high_leads)
        
        return stats
    
    def reset_hourly_counter(self):
        """重置每小时计数器"""
        self.instant_alerts_count = 0
        self.logger.debug("🔄 即时提醒计数器已重置")
