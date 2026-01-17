"""
Claude AI 分析模块
使用Claude AI进行智能评分和分析
"""

import json
from typing import Dict, List, Optional

from config import config
from utils.logger import get_logger
from .scorer import Scorer


class ClaudeAnalyzer:
    """Claude AI 智能分析器"""
    
    def __init__(self):
        self.logger = get_logger()
        self.enabled = config.ENABLE_CLAUDE_AI and config.ANTHROPIC_API_KEY
        self.model = config.ANTHROPIC_MODEL
        self.client = None
        self.fallback_scorer = Scorer()
        
        if self.enabled:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
                self.logger.info(f"✅ Claude AI 已初始化 (模型: {self.model})")
            except ImportError:
                self.logger.warning("⚠️ anthropic库未安装，使用规则评分")
                self.enabled = False
            except Exception as e:
                self.logger.warning(f"⚠️ Claude AI 初始化失败: {str(e)}")
                self.enabled = False
        else:
            self.logger.info("ℹ️ Claude AI 未启用，使用规则评分")
    
    def score_project(self, project: Dict) -> Dict:
        """
        评分一个项目
        
        Args:
            project: 项目信息字典
            
        Returns:
            包含评分和分析的字典
        """
        if not self.enabled:
            return self.fallback_scorer.score_record(project)
        
        prompt = self._build_scoring_prompt(project)
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # 提取JSON响应
            response_text = message.content[0].text
            # 移除可能的markdown代码块标记
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(response_text)
            
            # 确保评分在0-100范围内
            result['score'] = max(0, min(100, result.get('score', 50)))
            
            # 自动确定优先级
            score = result['score']
            if score >= config.CRITICAL_THRESHOLD:
                result['priority'] = 'Critical'
            elif score >= config.HIGH_THRESHOLD:
                result['priority'] = 'High'
            elif score >= config.MEDIUM_THRESHOLD:
                result['priority'] = 'Medium'
            else:
                result['priority'] = 'Low'
            
            # 更新项目记录
            project['ai_score'] = result['score']
            project['priority'] = result['priority']
            project['ai_reasoning'] = result.get('reasoning', '')
            project['ai_recommendation'] = result.get('recommendation', '')
            project['scoring_method'] = 'claude_ai'
            
            return project
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"⚠️ Claude响应解析失败: {str(e)}")
            return self.fallback_scorer.score_record(project)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Claude评分失败: {str(e)}")
            return self.fallback_scorer.score_record(project)
    
    def _build_scoring_prompt(self, project: Dict) -> str:
        """构建评分提示词"""
        return f"""
你是一个专业的幼儿园商机评估专家。请根据以下信息评估这个项目的商业价值。

项目信息：
- 类型：{project.get('type', 'N/A')}
- 名称：{project.get('name', 'N/A')}
- 位置：{project.get('city', 'N/A')}, {project.get('province', 'N/A')}, {project.get('country', 'N/A')}
- 容量：{project.get('capacity', 'N/A')}名儿童
- 状态：{project.get('license_status', 'N/A')}
- 数据来源：{project.get('source', 'N/A')}

评分标准（总分100分）：

1. 容量规模（30分）
   - 80+儿童 = 30分
   - 60-79儿童 = 25分
   - 40-59儿童 = 20分
   - 20-39儿童 = 15分
   - <20儿童 = 10分
   - 未知 = 15分

2. 地理位置（40分）
   加拿大：Toronto/Vancouver/Montreal=40分，Calgary/Edmonton/Ottawa=35分，其他省会=30分
   澳大利亚：Sydney/Melbourne/Brisbane=40分，Perth/Adelaide/Canberra=35分，其他首府=30分

3. 项目阶段（30分）
   - 新建=30分
   - 扩建=25分
   - 许可变更=20分
   - 续期=15分

请返回JSON格式（只返回JSON，不要其他内容）：
{{
    "score": 数字(0-100),
    "capacity_score": 数字(0-30),
    "location_score": 数字(0-40),
    "stage_score": 数字(0-30),
    "priority": "Critical/High/Medium/Low",
    "reasoning": "简短评分理由（1-2句话）",
    "recommendation": "跟进建议（1句话）"
}}
"""
    
    def batch_score(self, projects: List[Dict]) -> List[Dict]:
        """
        批量评分多个项目
        
        Args:
            projects: 项目列表
            
        Returns:
            评分后的项目列表
        """
        if not projects:
            return []
        
        self.logger.info(f"\n🤖 开始{'AI' if self.enabled else '规则'}评分: {len(projects)} 条记录")
        
        results = []
        score_distribution = {
            'Critical': 0,
            'High': 0,
            'Medium': 0,
            'Low': 0
        }
        
        for i, project in enumerate(projects):
            if self.enabled:
                self.logger.debug(f"   [{i+1}/{len(projects)}] 评分: {project.get('name', 'Unknown')}")
            
            scored = self.score_project(project)
            results.append(scored)
            score_distribution[scored.get('priority', 'Low')] += 1
        
        # 输出评分分布
        method = "Claude AI" if self.enabled else "规则"
        self.logger.info(f"📈 {method}评分完成:")
        self.logger.info(f"   🚨 Critical: {score_distribution['Critical']} 条")
        self.logger.info(f"   🔥 High: {score_distribution['High']} 条")
        self.logger.info(f"   📌 Medium: {score_distribution['Medium']} 条")
        self.logger.info(f"   📋 Low: {score_distribution['Low']} 条")
        
        return results
    
    def analyze_opportunity(self, project: Dict) -> Optional[str]:
        """
        深度分析商机（生成详细报告）
        
        Args:
            project: 项目信息
            
        Returns:
            分析报告文本
        """
        if not self.enabled:
            return None
        
        prompt = f"""
请为以下幼儿园商机生成一份简短的分析报告。

项目信息：
- 名称：{project.get('name', 'N/A')}
- 位置：{project.get('city', 'N/A')}, {project.get('province', 'N/A')}, {project.get('country', 'N/A')}
- 容量：{project.get('capacity', 'N/A')}名儿童
- 类型：{project.get('type', 'N/A')}
- 当前评分：{project.get('ai_score', 'N/A')}分

请提供：
1. 项目亮点（2-3点）
2. 潜在风险（1-2点）
3. 建议跟进策略（1-2句话）

用中文回答，保持简洁专业。
"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text
            
        except Exception as e:
            self.logger.warning(f"⚠️ 商机分析失败: {str(e)}")
            return None
