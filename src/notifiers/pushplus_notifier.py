"""
PushPlus 微信推送模块
通过PushPlus API发送消息到微信群和个人
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime

from ..config import config
from ..utils.logger import get_logger
from ..utils.helpers import get_priority_emoji, get_priority_color


class PushPlusNotifier:
    """PushPlus 微信推送器"""
    
    API_URL = "http://www.pushplus.plus/send"
    
    def __init__(self):
        self.logger = get_logger()
        self.token = config.PUSHPLUS_TOKEN
        self.topic = config.PUSHPLUS_TOPIC
        self.enabled = bool(self.token)
        
        if not self.enabled:
            self.logger.warning("⚠️ PushPlus未配置Token，微信推送已禁用")
    
    def _send(self, title: str, content: str, template: str = 'html',
              topic: str = None, channel: str = 'wechat') -> bool:
        """
        发送消息
        
        Args:
            title: 消息标题
            content: 消息内容
            template: 模板类型 (html/txt/json/markdown)
            topic: 群组代码（不传则发送到个人）
            channel: 发送渠道
            
        Returns:
            是否发送成功
        """
        if not self.enabled:
            return False
        
        if config.DRY_RUN:
            self.logger.info(f"🔍 [DRY RUN] PushPlus发送: {title}")
            return True
        
        try:
            payload = {
                'token': self.token,
                'title': title,
                'content': content,
                'template': template,
                'channel': channel
            }
            
            # 如果指定topic，发送到群组
            if topic or self.topic:
                payload['topic'] = topic or self.topic
            
            response = requests.post(self.API_URL, json=payload, timeout=10)
            result = response.json()
            
            if result.get('code') == 200:
                self.logger.info(f"✅ PushPlus发送成功: {title}")
                return True
            else:
                self.logger.error(f"❌ PushPlus发送失败: {result.get('msg')}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ PushPlus发送异常: {str(e)}")
            return False
    
    def send_critical_alert(self, lead: Dict) -> bool:
        """发送紧急商机通知"""
        title = f"🚨 紧急商机发现 - 评分{lead.get('ai_score', 0)}分"
        
        content = self._render_critical_template(lead)
        
        # 发送到群组和个人
        result1 = self._send(title, content, template='html')
        
        return result1
    
    def send_high_priority_batch(self, leads: List[Dict]) -> bool:
        """发送高优先级商机批量通知"""
        if not leads:
            return True
        
        title = f"🔥 发现 {len(leads)} 个高优先级商机"
        content = self._render_batch_template(leads)
        
        return self._send(title, content, template='html')
    
    def send_daily_summary(self, summary_data: Dict) -> bool:
        """发送每日摘要"""
        date = summary_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        title = f"📊 幼儿园商机日报 - {date}"
        
        content = self._render_summary_template(summary_data)
        
        return self._send(title, content, template='html')
    
    def send_error_alert(self, error_msg: str, source: str, to_group: bool = False) -> bool:
        """发送错误警告"""
        title = f"⚠️ 系统警告 - {source}"
        
        content = f"""
        <div style="background: #fff3cd; padding: 20px; border-left: 5px solid #ffc107; border-radius: 5px;">
            <h3 style="color: #856404; margin: 0 0 10px 0;">⚠️ 系统警告</h3>
            <p><strong>来源:</strong> {source}</p>
            <p><strong>错误信息:</strong> {error_msg}</p>
            <p><strong>时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """
        
        # 错误警告通常只发给个人
        topic = self.topic if to_group else None
        return self._send(title, content, template='html', topic=topic)
    
    def _render_critical_template(self, lead: Dict) -> str:
        """渲染紧急商机HTML模板"""
        score = lead.get('ai_score', 0)
        priority_color = get_priority_color(lead.get('priority', 'Critical'))
        
        return f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 20px; border-radius: 10px; color: white; text-align: center;">
    <h1 style="margin: 0;">🚨 紧急商机发现</h1>
    <p style="font-size: 24px; margin: 10px 0;">评分：<strong>{score}</strong>分</p>
</div>

<div style="background: #fff3cd; padding: 20px; margin: 20px 0; 
            border-left: 5px solid {priority_color}; border-radius: 5px;">
    <h2 style="color: #856404; margin: 0 0 15px 0;">{lead.get('name', 'Unknown')}</h2>
    
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 8px 0; width: 120px;"><strong>📍 位置</strong></td>
            <td style="padding: 8px 0;">{lead.get('city', '')}, {lead.get('province', '')}, {lead.get('country', '')}</td>
        </tr>
        <tr>
            <td style="padding: 8px 0;"><strong>👥 容量</strong></td>
            <td style="padding: 8px 0;">{lead.get('capacity', 'N/A')}名儿童</td>
        </tr>
        <tr>
            <td style="padding: 8px 0;"><strong>🏷️ 类型</strong></td>
            <td style="padding: 8px 0;">{lead.get('type', '新建项目')}</td>
        </tr>
        <tr>
            <td style="padding: 8px 0;"><strong>📅 发现</strong></td>
            <td style="padding: 8px 0;">{lead.get('discovered_date', '')}</td>
        </tr>
        <tr>
            <td style="padding: 8px 0;"><strong>📞 联系</strong></td>
            <td style="padding: 8px 0;">{lead.get('phone', 'N/A')}</td>
        </tr>
    </table>
    
    <div style="margin-top: 20px; text-align: center;">
        <a href="{config.GOOGLE_SHEET_URL or '#'}" 
           style="background: #dc3545; color: white; 
                  padding: 12px 30px; text-decoration: none; border-radius: 5px;
                  display: inline-block; font-weight: bold;">
            🔥 立即查看详情
        </a>
    </div>
</div>

<p style="color: #888; font-size: 12px; text-align: center;">
    数据来源: {lead.get('source', 'N/A')} | 更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</p>
"""
    
    def _render_batch_template(self, leads: List[Dict]) -> str:
        """渲染批量通知HTML模板"""
        leads_html = ""
        for i, lead in enumerate(leads[:10], 1):  # 最多显示10条
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            leads_html += f"""
<div style="background: #f8f9fa; padding: 15px; margin: 10px 0; 
            border-radius: 5px; border-left: 3px solid {get_priority_color(lead.get('priority', 'High'))};">
    <strong>{emoji} {lead.get('name', 'Unknown')}</strong> - 评分 {lead.get('ai_score', 0)}分
    <p style="margin: 5px 0; color: #666;">
        📍 {lead.get('city', '')}, {lead.get('province', '')} | 
        👥 {lead.get('capacity', 'N/A')}名 | 
        🏷️ {lead.get('type', '新建')}
    </p>
</div>
"""
        
        return f"""
<div style="background: #ff5722; padding: 15px; border-radius: 10px; color: white; text-align: center;">
    <h2 style="margin: 0;">🔥 发现 {len(leads)} 个高优先级商机</h2>
</div>

<div style="margin: 20px 0;">
    {leads_html}
</div>

<div style="text-align: center; margin: 20px 0;">
    <a href="{config.GOOGLE_SHEET_URL or '#'}" 
       style="background: #28a745; color: white; 
              padding: 12px 30px; text-decoration: none; border-radius: 5px;
              display: inline-block; font-weight: bold;">
        📊 查看完整列表
    </a>
</div>

<p style="color: #888; font-size: 12px; text-align: center;">
    更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</p>
"""
    
    def _render_summary_template(self, data: Dict) -> str:
        """渲染每日摘要HTML模板"""
        canada = data.get('canada', {})
        australia = data.get('australia', {})
        high_priority = data.get('high_priority', [])
        sources = data.get('sources', [])
        
        # 高优先级商机列表
        priority_html = ""
        for i, lead in enumerate(high_priority[:5], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            priority_html += f"""
<details style="background: #f1f3f5; padding: 15px; margin: 10px 0; 
                border-radius: 5px; cursor: pointer;">
    <summary style="font-weight: bold; color: {get_priority_color(lead.get('priority', 'High'))};">
        {emoji} {lead.get('name', 'Unknown')} - 评分 {lead.get('ai_score', 0)}分
    </summary>
    <div style="padding: 10px 0;">
        <p>📍 {lead.get('city', '')}, {lead.get('province', '')}, {lead.get('country', '')}</p>
        <p>👥 容量: {lead.get('capacity', 'N/A')}名</p>
        <p>🏷️ {lead.get('type', '新建项目')}</p>
    </div>
</details>
"""
        
        # 数据源状态
        sources_html = ""
        for source in sources:
            status_icon = "✅" if source.get('status') == '正常' else "⚠️"
            sources_html += f"<li>{status_icon} {source.get('name', 'Unknown')}: {source.get('status', 'N/A')} (+{source.get('count', 0)})</li>"
        
        total = (canada.get('new_projects', 0) + canada.get('sales', 0) + canada.get('tenders', 0) +
                 australia.get('new_projects', 0) + australia.get('sales', 0) + australia.get('tenders', 0))
        
        return f"""
<h2 style="text-align: center;">📊 幼儿园商机日报 · {data.get('date', '')}</h2>

<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
    <h3>📈 今日数据概览</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="background: #e9ecef;">
            <th style="padding: 10px; text-align: left;">国家</th>
            <th style="padding: 10px; text-align: center;">新建</th>
            <th style="padding: 10px; text-align: center;">交易</th>
            <th style="padding: 10px; text-align: center;">招标</th>
        </tr>
        <tr>
            <td style="padding: 10px;">🇨🇦 加拿大</td>
            <td style="padding: 10px; text-align: center;"><strong>{canada.get('new_projects', 0)}</strong></td>
            <td style="padding: 10px; text-align: center;"><strong>{canada.get('sales', 0)}</strong></td>
            <td style="padding: 10px; text-align: center;"><strong>{canada.get('tenders', 0)}</strong></td>
        </tr>
        <tr style="background: #f8f9fa;">
            <td style="padding: 10px;">🇦🇺 澳大利亚</td>
            <td style="padding: 10px; text-align: center;"><strong>{australia.get('new_projects', 0)}</strong></td>
            <td style="padding: 10px; text-align: center;"><strong>{australia.get('sales', 0)}</strong></td>
            <td style="padding: 10px; text-align: center;"><strong>{australia.get('tenders', 0)}</strong></td>
        </tr>
    </table>
</div>

<hr style="border: none; border-top: 2px solid #dee2e6; margin: 30px 0;"/>

<h3>🔥 高优先级商机（Top 5）</h3>
{priority_html if priority_html else '<p style="color: #666;">今日暂无高优先级商机</p>'}

<hr style="border: none; border-top: 2px solid #dee2e6; margin: 30px 0;"/>

<h3>📊 数据源状态</h3>
<ul style="list-style: none; padding: 0;">
    {sources_html if sources_html else '<li>暂无数据源信息</li>'}
</ul>

<div style="text-align: center; margin: 30px 0;">
    <a href="{data.get('sheets_url') or config.GOOGLE_SHEET_URL or '#'}" 
       style="background: #28a745; color: white; padding: 15px 40px; 
              text-decoration: none; border-radius: 8px; display: inline-block;
              font-weight: bold;">
        📊 查看完整Google Sheets
    </a>
</div>

<p style="color: #6c757d; font-size: 12px; text-align: center; margin-top: 30px;">
    ⏰ 更新时间: {data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))} | 总计新增: {total}条记录
</p>
"""
