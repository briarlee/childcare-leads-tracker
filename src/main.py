"""
幼儿园商机自动追踪系统 - 主程序入口
每日从加拿大和澳大利亚政府数据源获取幼儿园商机，
进行智能分析后写入Google Sheets，并通过双渠道推送通知。
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / '.env')

from config import config
from core.sheets_manager import SheetsManager
from core.data_processor import DataProcessor
from fetchers.ontario_fetcher import OntarioFetcher
from fetchers.bc_fetcher import BCFetcher
from fetchers.acecqa_fetcher import ACECQAFetcher
from analyzers.deduplicator import Deduplicator
from analyzers.claude_analyzer import ClaudeAnalyzer
from analyzers.scorer import Scorer
from notifiers.notification_manager import NotificationManager
from utils.logger import setup_logger


def main():
    """主程序入口"""
    
    # 初始化日志
    logger = setup_logger()
    
    logger.info("=" * 60)
    logger.info("🚀 幼儿园商机自动追踪系统启动")
    logger.info(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # 打印配置信息
    if config.DEBUG_MODE:
        config.print_config()
    
    # 验证配置
    errors = config.validate()
    if errors:
        for error in errors:
            logger.error(f"❌ 配置错误: {error}")
        if not config.DRY_RUN:
            sys.exit(1)
    
    try:
        # 1. 初始化各模块
        logger.info("\n📦 初始化模块...")
        
        sheets = None
        if not config.DRY_RUN:
            try:
                sheets = SheetsManager()
            except Exception as e:
                logger.error(f"❌ Google Sheets初始化失败: {str(e)}")
                logger.info("ℹ️ 继续运行但不会写入Sheets")
        
        processor = DataProcessor()
        deduplicator = Deduplicator(sheets)
        
        # 根据配置选择评分器
        if config.ENABLE_CLAUDE_AI:
            analyzer = ClaudeAnalyzer()
        else:
            analyzer = Scorer()
        
        notifier = NotificationManager()
        
        # 2. 获取启用的数据源
        enabled_sources = [s.strip().lower() for s in config.ENABLED_SOURCES]
        logger.info(f"\n📡 启用的数据源: {', '.join(enabled_sources)}")
        
        all_records = []
        source_status = []
        
        # 3. 从各数据源获取数据
        logger.info("\n📥 开始获取数据...")
        
        # Ontario数据源
        if 'ontario' in enabled_sources:
            try:
                logger.info("\n🇨🇦 获取Ontario数据...")
                ontario = OntarioFetcher()
                ontario_data = ontario.fetch()
                logger.info(f"   ✅ Ontario: 获取 {len(ontario_data)} 条记录")
                all_records.extend(ontario_data)
                source_status.append(ontario.get_status())
            except Exception as e:
                logger.error(f"   ❌ Ontario获取失败: {str(e)}")
                source_status.append({
                    'name': 'Ontario Open Data',
                    'status': '异常',
                    'error': str(e),
                    'count': 0
                })
        
        # BC数据源
        if 'bc' in enabled_sources:
            try:
                logger.info("\n🇨🇦 获取BC数据...")
                bc = BCFetcher()
                bc_data = bc.fetch()
                logger.info(f"   ✅ BC: 获取 {len(bc_data)} 条记录")
                all_records.extend(bc_data)
                source_status.append(bc.get_status())
            except Exception as e:
                logger.error(f"   ❌ BC获取失败: {str(e)}")
                source_status.append({
                    'name': 'BC Child Care',
                    'status': '异常',
                    'error': str(e),
                    'count': 0
                })
        
        # ACECQA数据源
        if 'acecqa' in enabled_sources:
            try:
                logger.info("\n🇦🇺 获取ACECQA数据...")
                acecqa = ACECQAFetcher()
                acecqa_data = acecqa.fetch()
                logger.info(f"   ✅ ACECQA: 获取 {len(acecqa_data)} 条记录")
                all_records.extend(acecqa_data)
                source_status.append(acecqa.get_status())
            except Exception as e:
                logger.error(f"   ❌ ACECQA获取失败: {str(e)}")
                source_status.append({
                    'name': 'ACECQA',
                    'status': '异常',
                    'error': str(e),
                    'count': 0
                })
        
        logger.info(f"\n📊 总计获取: {len(all_records)} 条原始记录")
        
        # 4. 检查是否有数据
        if len(all_records) == 0:
            logger.info("\nℹ️ 今日暂无新增记录")
            
            # 发送空摘要通知
            summary_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'canada': {'new_projects': 0, 'sales': 0, 'tenders': 0},
                'australia': {'new_projects': 0, 'sales': 0, 'tenders': 0},
                'high_priority': [],
                'sources': source_status,
                'sheets_url': sheets.get_sheet_url() if sheets else config.GOOGLE_SHEET_URL,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            notifier.send_daily_summary(summary_data)
            
            logger.info("\n✅ 系统运行完成（无新数据）")
            return
        
        # 5. 数据处理
        logger.info("\n🔧 处理数据...")
        processed_records = processor.process_records(all_records)
        
        # 6. 去重
        logger.info("\n🔍 执行去重检测...")
        unique_records = deduplicator.remove_duplicates(processed_records)
        
        if len(unique_records) == 0:
            logger.info("\nℹ️ 去重后无新增记录")
            
            summary_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'canada': {'new_projects': 0, 'sales': 0, 'tenders': 0},
                'australia': {'new_projects': 0, 'sales': 0, 'tenders': 0},
                'high_priority': [],
                'sources': source_status,
                'sheets_url': sheets.get_sheet_url() if sheets else config.GOOGLE_SHEET_URL,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            notifier.send_daily_summary(summary_data)
            
            logger.info("\n✅ 系统运行完成（无新数据）")
            return
        
        # 7. 限制记录数
        if len(unique_records) > config.MAX_RECORDS_PER_RUN:
            logger.warning(f"⚠️ 记录数超过限制({config.MAX_RECORDS_PER_RUN})，将截断")
            unique_records = unique_records[:config.MAX_RECORDS_PER_RUN]
        
        # 8. 评分
        logger.info("\n🤖 开始智能评分...")
        scored_records = analyzer.batch_score(unique_records)
        
        # 9. 按优先级分类
        critical_leads = [l for l in scored_records if l.get('priority') == 'Critical']
        high_leads = [l for l in scored_records if l.get('priority') == 'High']
        medium_leads = [l for l in scored_records if l.get('priority') == 'Medium']
        low_leads = [l for l in scored_records if l.get('priority') == 'Low']
        
        logger.info(f"\n📈 优先级分布:")
        logger.info(f"   🚨 Critical: {len(critical_leads)} 条")
        logger.info(f"   🔥 High: {len(high_leads)} 条")
        logger.info(f"   📌 Medium: {len(medium_leads)} 条")
        logger.info(f"   📋 Low: {len(low_leads)} 条")
        
        # 10. 写入Google Sheets
        if sheets:
            logger.info("\n💾 写入Google Sheets...")
            
            # 分类记录
            classified = processor.classify_records(scored_records)
            
            # 写入各工作表
            sheets.append_new_projects(classified['new_projects'])
            sheets.append_sales(classified['sales'])
            sheets.append_tenders(classified['tenders'])
            
            # 更新数据源监控
            sheets.update_source_monitoring(source_status)
            
            # 更新每日统计
            stats = processor.get_statistics(scored_records)
            stats['status'] = '正常'
            sheets.update_daily_stats(stats)
            
            logger.info(f"   ✅ 数据已保存到Google Sheets")
        
        # 11. 发送即时通知（Critical和High）
        logger.info("\n📱 发送即时通知...")
        notification_stats = notifier.process_scored_leads(scored_records)
        
        logger.info(f"   🚨 已发送紧急通知: {notification_stats['critical_notified']} 条")
        logger.info(f"   🔥 已发送高优先级通知: {notification_stats['high_notified']} 条")
        
        # 12. 生成并发送每日摘要
        logger.info("\n📊 生成每日摘要...")
        
        stats = processor.get_statistics(scored_records)
        
        summary_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'canada': {
                'new_projects': stats['canada_new'],
                'sales': stats['canada_sales'],
                'tenders': stats['canada_tenders']
            },
            'australia': {
                'new_projects': stats['australia_new'],
                'sales': stats['australia_sales'],
                'tenders': stats['australia_tenders']
            },
            'high_priority': sorted(
                critical_leads + high_leads,
                key=lambda x: x.get('ai_score', 0),
                reverse=True
            )[:5],
            'sources': source_status,
            'sheets_url': sheets.get_sheet_url() if sheets else config.GOOGLE_SHEET_URL,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        notifier.send_daily_summary(summary_data)
        logger.info("   ✅ 每日摘要已发送")
        
        # 13. 完成
        logger.info("\n" + "=" * 60)
        logger.info("✅ 系统运行完成！")
        logger.info(f"📊 总结:")
        logger.info(f"   - 获取记录: {len(all_records)} 条")
        logger.info(f"   - 去重后: {len(unique_records)} 条")
        logger.info(f"   - 高价值商机: {len(critical_leads) + len(high_leads)} 条")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ 系统运行出错: {str(e)}")
        logger.exception(e)
        
        # 发送错误通知
        try:
            notifier = NotificationManager()
            notifier.send_error_alert(str(e), "系统主程序")
        except:
            pass
        
        sys.exit(1)


if __name__ == '__main__':
    main()
