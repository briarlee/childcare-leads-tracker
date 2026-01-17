"""
Google Sheets 管理模块
负责所有与Google Sheets的交互操作
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from ..config import config
from ..utils.logger import get_logger


class SheetsManager:
    """Google Sheets 管理器"""
    
    # 工作表名称定义
    SHEET_NEW_PROJECTS = "新建项目追踪"
    SHEET_SALES = "交易信息追踪"
    SHEET_TENDERS = "招标信息追踪"
    SHEET_MONITORING = "数据源监控"
    SHEET_DAILY_STATS = "每日统计汇总"
    
    # 各工作表的列标题
    HEADERS = {
        SHEET_NEW_PROJECTS: [
            "发现日期", "国家", "省/州", "城市", "项目名称", "完整地址",
            "容量", "许可证号", "许可状态", "联系电话", "联系邮箱",
            "数据来源", "原始链接", "跟进状态", "优先级", "AI评分",
            "备注", "负责人", "更新时间"
        ],
        SHEET_SALES: [
            "发现日期", "国家", "省/州", "城市", "项目名称", "售价",
            "容量", "年营收", "净利润/现金流", "租约剩余年限", "物业类型",
            "卖家联系方式", "平台来源", "原始链接", "跟进状态", "评估分数",
            "ROI预估", "备注", "更新时间"
        ],
        SHEET_TENDERS: [
            "发布日期", "截止日期", "剩余天数", "国家", "省/州", "项目名称",
            "合同价值", "项目简述", "招标类型", "招标机构", "联系方式",
            "文件下载链接", "是否已投标", "中标概率评估", "备注", "更新时间"
        ],
        SHEET_MONITORING: [
            "数据源名称", "数据源类型", "最后成功时间", "最后尝试时间",
            "本次新增记录数", "累计记录数", "状态", "错误信息", "响应时间(ms)"
        ],
        SHEET_DAILY_STATS: [
            "日期", "🇨🇦新建项目数", "🇨🇦交易信息数", "🇨🇦招标信息数",
            "🇦🇺新建项目数", "🇦🇺交易信息数", "🇦🇺招标信息数",
            "Critical数量", "High数量", "总新增记录", "运行状态"
        ]
    }
    
    def __init__(self):
        """初始化Sheets管理器"""
        self.logger = get_logger()
        self.client = None
        self.spreadsheet = None
        self._connect()
    
    def _connect(self):
        """建立与Google Sheets的连接"""
        try:
            # 认证范围
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # 从环境变量或文件加载凭证
            credentials_json = os.getenv('GOOGLE_CREDENTIALS')
            credentials_path = config.GOOGLE_CREDENTIALS_PATH
            
            if credentials_json:
                # 从环境变量加载（用于GitHub Actions）
                credentials_dict = json.loads(credentials_json)
                credentials = Credentials.from_service_account_info(
                    credentials_dict,
                    scopes=scopes
                )
            elif os.path.exists(credentials_path):
                # 从文件加载
                credentials = Credentials.from_service_account_file(
                    credentials_path,
                    scopes=scopes
                )
            else:
                raise FileNotFoundError(f"未找到凭证文件: {credentials_path}")
            
            # 创建gspread客户端
            self.client = gspread.authorize(credentials)
            
            # 打开或创建电子表格
            self._open_or_create_spreadsheet()
            
            self.logger.info(f"✅ 已连接到Google Sheets: {config.GOOGLE_SHEET_NAME}")
            
        except Exception as e:
            self.logger.error(f"❌ 连接Google Sheets失败: {str(e)}")
            raise
    
    def _open_or_create_spreadsheet(self):
        """打开或创建电子表格"""
        sheet_name = config.GOOGLE_SHEET_NAME
        
        try:
            # 尝试通过URL打开
            if config.GOOGLE_SHEET_URL:
                sheet_id = config.GOOGLE_SHEET_URL.split('/d/')[1].split('/')[0]
                self.spreadsheet = self.client.open_by_key(sheet_id)
            else:
                # 尝试通过名称打开
                self.spreadsheet = self.client.open(sheet_name)
        except gspread.SpreadsheetNotFound:
            # 创建新的电子表格
            self.logger.info(f"📝 创建新电子表格: {sheet_name}")
            self.spreadsheet = self.client.create(sheet_name)
        
        # 确保所有工作表都存在
        self._ensure_worksheets_exist()
    
    def _ensure_worksheets_exist(self):
        """确保所有必需的工作表都存在"""
        existing_sheets = [ws.title for ws in self.spreadsheet.worksheets()]
        
        for sheet_name, headers in self.HEADERS.items():
            if sheet_name not in existing_sheets:
                self.logger.info(f"📋 创建工作表: {sheet_name}")
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=1000,
                    cols=len(headers)
                )
                # 添加标题行
                worksheet.update('A1', [headers])
                # 冻结标题行
                worksheet.freeze(rows=1)
            else:
                # 检查标题是否正确
                worksheet = self.spreadsheet.worksheet(sheet_name)
                current_headers = worksheet.row_values(1)
                if current_headers != headers:
                    self.logger.info(f"🔄 更新工作表标题: {sheet_name}")
                    worksheet.update('A1', [headers])
        
        # 删除默认的Sheet1（如果存在且为空）
        try:
            default_sheet = self.spreadsheet.worksheet('Sheet1')
            if default_sheet.row_count <= 1:
                self.spreadsheet.del_worksheet(default_sheet)
        except gspread.WorksheetNotFound:
            pass
    
    def append_new_projects(self, records: List[Dict]) -> int:
        """
        追加新建项目记录
        
        Args:
            records: 记录列表
            
        Returns:
            成功追加的记录数
        """
        if not records:
            return 0
        
        if config.DRY_RUN:
            self.logger.info(f"🔍 [DRY RUN] 将追加 {len(records)} 条新建项目记录")
            return len(records)
        
        worksheet = self.spreadsheet.worksheet(self.SHEET_NEW_PROJECTS)
        
        rows = []
        for record in records:
            row = [
                record.get('discovered_date', ''),
                record.get('country', ''),
                record.get('province', ''),
                record.get('city', ''),
                record.get('name', ''),
                record.get('address', ''),
                record.get('capacity', ''),
                record.get('license_number', ''),
                record.get('license_status', ''),
                record.get('phone', ''),
                record.get('email', ''),
                record.get('source', ''),
                record.get('source_url', ''),
                '未联系',  # 默认跟进状态
                record.get('priority', 'Medium'),
                record.get('ai_score', 50),
                record.get('notes', ''),
                '',  # 负责人
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            rows.append(row)
        
        # 批量追加
        worksheet.append_rows(rows, value_input_option='USER_ENTERED')
        
        self.logger.info(f"✅ 已追加 {len(rows)} 条新建项目记录")
        return len(rows)
    
    def append_sales(self, records: List[Dict]) -> int:
        """追加交易信息记录"""
        if not records:
            return 0
        
        if config.DRY_RUN:
            self.logger.info(f"🔍 [DRY RUN] 将追加 {len(records)} 条交易信息记录")
            return len(records)
        
        worksheet = self.spreadsheet.worksheet(self.SHEET_SALES)
        
        rows = []
        for record in records:
            row = [
                record.get('discovered_date', ''),
                record.get('country', ''),
                record.get('province', ''),
                record.get('city', ''),
                record.get('name', ''),
                record.get('price', ''),
                record.get('capacity', ''),
                record.get('annual_revenue', ''),
                record.get('cash_flow', ''),
                record.get('lease_remaining', ''),
                record.get('property_type', ''),
                record.get('seller_contact', ''),
                record.get('source', ''),
                record.get('source_url', ''),
                '未联系',
                record.get('ai_score', 50),
                record.get('roi_estimate', ''),
                record.get('notes', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            rows.append(row)
        
        worksheet.append_rows(rows, value_input_option='USER_ENTERED')
        
        self.logger.info(f"✅ 已追加 {len(rows)} 条交易信息记录")
        return len(rows)
    
    def append_tenders(self, records: List[Dict]) -> int:
        """追加招标信息记录"""
        if not records:
            return 0
        
        if config.DRY_RUN:
            self.logger.info(f"🔍 [DRY RUN] 将追加 {len(records)} 条招标信息记录")
            return len(records)
        
        worksheet = self.spreadsheet.worksheet(self.SHEET_TENDERS)
        
        rows = []
        for record in records:
            # 计算剩余天数
            deadline = record.get('deadline_date', '')
            days_remaining = ''
            if deadline:
                try:
                    deadline_dt = datetime.strptime(deadline, '%Y-%m-%d')
                    days_remaining = (deadline_dt - datetime.now()).days
                except ValueError:
                    pass
            
            row = [
                record.get('published_date', ''),
                deadline,
                days_remaining,
                record.get('country', ''),
                record.get('province', ''),
                record.get('name', ''),
                record.get('contract_value', ''),
                record.get('description', ''),
                record.get('tender_type', ''),
                record.get('organization', ''),
                record.get('contact', ''),
                record.get('document_url', ''),
                '否',  # 默认未投标
                record.get('win_probability', ''),
                record.get('notes', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            rows.append(row)
        
        worksheet.append_rows(rows, value_input_option='USER_ENTERED')
        
        self.logger.info(f"✅ 已追加 {len(rows)} 条招标信息记录")
        return len(rows)
    
    def update_source_monitoring(self, source_statuses: List[Dict]):
        """
        更新数据源监控信息
        
        Args:
            source_statuses: 数据源状态列表
        """
        if config.DRY_RUN:
            self.logger.info(f"🔍 [DRY RUN] 将更新 {len(source_statuses)} 个数据源状态")
            return
        
        worksheet = self.spreadsheet.worksheet(self.SHEET_MONITORING)
        
        # 获取现有数据源
        existing_data = worksheet.get_all_records()
        existing_sources = {row['数据源名称']: idx + 2 for idx, row in enumerate(existing_data)}
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for status in source_statuses:
            source_name = status.get('name', '')
            row_data = [
                source_name,
                status.get('type', 'CSV'),
                now if status.get('status') == '正常' else '',
                now,
                status.get('count', 0),
                status.get('total', 0),
                status.get('status', '正常'),
                status.get('error', ''),
                status.get('response_time', '')
            ]
            
            if source_name in existing_sources:
                # 更新现有行
                row_num = existing_sources[source_name]
                worksheet.update(f'A{row_num}', [row_data])
            else:
                # 追加新行
                worksheet.append_row(row_data, value_input_option='USER_ENTERED')
        
        self.logger.info(f"✅ 已更新 {len(source_statuses)} 个数据源监控状态")
    
    def update_daily_stats(self, stats: Dict):
        """
        更新每日统计汇总
        
        Args:
            stats: 统计数据字典
        """
        if config.DRY_RUN:
            self.logger.info(f"🔍 [DRY RUN] 将更新每日统计")
            return
        
        worksheet = self.spreadsheet.worksheet(self.SHEET_DAILY_STATS)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        row = [
            today,
            stats.get('canada_new', 0),
            stats.get('canada_sales', 0),
            stats.get('canada_tenders', 0),
            stats.get('australia_new', 0),
            stats.get('australia_sales', 0),
            stats.get('australia_tenders', 0),
            stats.get('critical_count', 0),
            stats.get('high_count', 0),
            stats.get('total', 0),
            stats.get('status', '正常')
        ]
        
        worksheet.append_row(row, value_input_option='USER_ENTERED')
        
        self.logger.info(f"✅ 已更新每日统计: {today}")
    
    def get_existing_license_numbers(self) -> set:
        """获取已存在的许可证号集合（用于去重）"""
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_NEW_PROJECTS)
            # 获取许可证号列（H列，索引7）
            license_column = worksheet.col_values(8)[1:]  # 跳过标题行
            return set(ln for ln in license_column if ln)
        except Exception as e:
            self.logger.warning(f"⚠️ 获取现有许可证号失败: {str(e)}")
            return set()
    
    def get_existing_addresses(self) -> set:
        """获取已存在的地址集合（用于去重）"""
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_NEW_PROJECTS)
            # 获取地址列（F列，索引5）
            address_column = worksheet.col_values(6)[1:]  # 跳过标题行
            return set(addr.lower().strip() for addr in address_column if addr)
        except Exception as e:
            self.logger.warning(f"⚠️ 获取现有地址失败: {str(e)}")
            return set()
    
    def get_sheet_url(self) -> str:
        """获取电子表格的URL"""
        return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet.id}"
