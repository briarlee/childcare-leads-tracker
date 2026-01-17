"""
钉钉群机器人推送模块
通过钉钉Webhook发送消息到钉钉群
"""

import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
from typing import Dict, List, Optional
from datetime import datetime

from ..config import config
from ..utils.logger import get_logger
from ..utils.helpers import get_priority_emoji


class DingTalkNotifier:
    """钉钉群机器人推送器"""
    
    def __init__(self):
        self.logger = get_logger()
        self.webhook = config.DINGTALK_WEBHOOK
        self.secret = config.DINGTALK_SECRET
        self.enabled = bool(self.webhook)
        
        if not self.enabled:
            self.logger.warning("⚠️ 钉钉Webhook未配置，钉钉推送已禁用")
    
    def _get_signed_url(self) -> str:
        """
        获取签名后的Webhook URL
        
        钉钉安全设置为"加签"时需要签名
        """
        if not self.secret:
            return self.webhook
        
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        return f"{self.webhook}&timestamp={timestamp}&sign={sign}"
    
    def _send(self, message: Dict) -> bool:
        """
        发送消息到钉钉
        
        Args:
            message: 消息体
            
        Returns:
            是否发送成功
        """
        if not self.enabled:
            return False
        
        if config.DRY_RUN:
            msg_type = message.get('msgtype', 'unknown')
            self.logger.info(f"🔍 [DRY RUN] 钉钉发送: {msg_type}")
            return True
        
        try:
            url = self._get_signed_url()
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(url, json=message, headers=headers, timeout=10)
            result = response.json()
            
            if result.get('errcode') == 0:
                self.logger.info(f"✅ 钉钉发送成功")
                return True
            else:
                self.logger.error(f"❌ 钉钉发送失败: {result.get('errmsg')}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 钉钉发送异常: {str(e)}")
            return False
    
    def send_text(self, content: str, at_all: bool = False, at_mobiles: List[str] = None) -> bool:
        """
        发送文本消息
        
        Args:
            content: 消息内容
            at_all: 是否@所有人
            at_mobiles: 要@的手机号列表
        """
        message = {
            "msgtype": "text",
            "text": {
                "content": content
            },
            "at": {
                "isAtAll": at_all,
                "atMobiles": at_mobiles or []
            }
        }
        
        return self._send(message)
    
    def send_markdown(self, title: str, content: str, 
                      at_all: bool = False, at_mobiles: List[str] = None) -> bool:
        """
        发送Markdown消息
        
        Args:
            title: 消息标题
            content: Markdown内容
            at_all: 是否@所有人
            at_mobiles: 要@的手机号列表
        """
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": content
            },
            "at": {
                "isAtAll": at_all,
                "atMobiles": at_mobiles or []
            }
        }
        
        return self._send(message)
    
    def send_critical_alert(self, lead: Dict, at_all: bool = True) -> bool:
        """
        发送紧急商机通知
        
        Args:
            lead: 商机信息
            at_all: 是否@所有人（默认True）
        """
        title = f"🚨 紧急商机发现！"
        content = self._render_critical_markdown(lead, at_all)
        
        return self.send_markdown(title, content, at_all=at_all)
    
    def send_high_priority_batch(self, leads: List[Dict], at_all: bool = False) -> bool:
        """发送高优先级商机批量通知"""
        if not leads:
            return True
        
        title = f"🔥 发现 {len(leads)} 个高优先级商机"
        content = self._render_batch_markdown(leads)
        
        return self.send_markdown(title, content, at_all=at_all)
    
    def send_daily_summary(self, summary_data: Dict) -> bool:
        """发送每日摘要"""
        title = "📊 幼儿园商机日报"
        content = self._render_summary_markdown(summary_data)
        
        return self.send_markdown(title, content)
    
    def send_error_alert(self, error_msg: str, source: str, at_mobiles: List[str] = None) -> bool:
        """发送错误警告"""
        title = f"⚠️ 系统警告"
        content = f"""### ⚠️ 系统警告

**来源：** {source}  
**错误信息：** {error_msg}  
**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

> 请及时检查系统状态
"""
        
        return self.send_markdown(title, content, at_mobiles=at_mobiles)
    
    def _render_critical_markdown(self, lead: Dict, at_all: bool = True) -> str:
        """渲染紧急商机Markdown"""
        score = lead.get('ai_score', 0)
        at_text = "\n\n@所有人 请立即关注！" if at_all else ""
        
        return f"""### 🚨 紧急商机发现！

---

**项目名称：** {lead.get('name', 'Unknown')}  
**AI评分：** <font color=#FF0000>{score}分</font>

#### 📋 项目详情

- **📍 位置：** {lead.get('city', '')}, {lead.get('province', '')}, {lead.get('country', '')}
- **👥 容量：** {lead.get('capacity', 'N/A')}名儿童
- **🏷️ 类型：** {lead.get('type', '新建项目')}
- **📅 发现时间：** {lead.get('discovered_date', '')}
- **📞 联系电话：** {lead.get('phone', 'N/A')}

#### 🎯 评分分析

- **容量规模：** {lead.get('capacity_score', 'N/A')}/30分
- **地理位置：** {lead.get('location_score', 'N/A')}/40分
- **项目阶段：** {lead.get('stage_score', 'N/A')}/30分

#### 🔗 快速操作

[查看Google Sheets]({config.GOOGLE_SHEET_URL or '#'}) | [数据来源]({lead.get('source_url', '#')})

---

> 📢 此商机已自动标记为【紧急】，建议立即跟进！  
> 💡 数据来源: {lead.get('source', 'N/A')}{at_text}
"""
    
    def _render_batch_markdown(self, leads: List[Dict]) -> str:
        """渲染批量通知Markdown"""
        leads_text = ""
        for i, lead in enumerate(leads[:5], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            leads_text += f"""
{emoji} **{lead.get('name', 'Unknown')}** - <font color=#FF5722>{lead.get('ai_score', 0)}分</font>  
> 📍 {lead.get('city', '')}, {lead.get('province', '')} | 👥 {lead.get('capacity', 'N/A')}名 | 🏷️ {lead.get('type', '新建')}

"""
        
        return f"""### 🔥 发现 {len(leads)} 个高优先级商机

---

{leads_text}

---

#### 🔗 快速链接

[📊 查看完整Google Sheets]({config.GOOGLE_SHEET_URL or '#'})

---

> ⏰ 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    def _render_summary_markdown(self, data: Dict) -> str:
        """渲染每日摘要Markdown"""
        canada = data.get('canada', {})
        australia = data.get('australia', {})
        high_priority = data.get('high_priority', [])
        sources = data.get('sources', [])
        
        # 计算总数
        canada_total = canada.get('new_projects', 0) + canada.get('sales', 0) + canada.get('tenders', 0)
        australia_total = australia.get('new_projects', 0) + australia.get('sales', 0) + australia.get('tenders', 0)
        total = canada_total + australia_total
        
        # 高优先级商机列表
        priority_text = ""
        for i, lead in enumerate(high_priority[:5], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            priority_text += f"""
{emoji} **{lead.get('name', 'Unknown')}** - <font color=#FF0000>{lead.get('ai_score', 0)}分</font>  
> 📍 {lead.get('city', '')}, {lead.get('province', '')} | 👥 {lead.get('capacity', 'N/A')}名 | 🏷️ {lead.get('type', '新建')}

"""
        
        if not priority_text:
            priority_text = "> 今日暂无高优先级商机"
        
        # 数据源状态
        sources_text = ""
        for source in sources:
            status_icon = "✅" if source.get('status') == '正常' else "⚠️"
            sources_text += f"- {status_icon} **{source.get('name', 'Unknown')}:** {source.get('status', 'N/A')} (+{source.get('count', 0)})\n"
        
        if not sources_text:
            sources_text = "- 暂无数据源信息"
        
        return f"""### 📊 幼儿园商机日报

**日期：** {data.get('date', '')}

---

#### 📈 今日数据概览

| 国家 | 新建项目 | 交易信息 | 招标信息 |
|-----|---------|---------|---------|
| 🇨🇦 加拿大 | **{canada.get('new_projects', 0)}** | **{canada.get('sales', 0)}** | **{canada.get('tenders', 0)}** |
| 🇦🇺 澳大利亚 | **{australia.get('new_projects', 0)}** | **{australia.get('sales', 0)}** | **{australia.get('tenders', 0)}** |
| 📊 **合计** | **{canada.get('new_projects', 0) + australia.get('new_projects', 0)}** | **{canada.get('sales', 0) + australia.get('sales', 0)}** | **{canada.get('tenders', 0) + australia.get('tenders', 0)}** |

---

#### 🔥 高优先级商机（评分85+）

{priority_text}

---

#### 📊 数据源状态

{sources_text}

---

#### 🔗 快速链接

[📊 查看完整Google Sheets]({data.get('sheets_url') or config.GOOGLE_SHEET_URL or '#'})

---

> ⏰ 更新时间: {data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}  
> 🤖 由AI自动生成并推送
"""
