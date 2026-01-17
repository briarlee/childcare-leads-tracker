# 🏫 幼儿园商机自动追踪系统 - 双渠道通知版

[![Daily Fetch](https://github.com/YOUR_USERNAME/childcare-leads-tracker/actions/workflows/daily_fetch.yml/badge.svg)](https://github.com/YOUR_USERNAME/childcare-leads-tracker/actions/workflows/daily_fetch.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

企业级自动化系统，每日从加拿大和澳大利亚政府数据源获取幼儿园相关商机，使用AI进行智能分析、去重、评分后，自动写入Google Sheets进行追踪管理，并同时通过**PushPlus推送到微信群**和**钉钉群机器人推送到钉钉群**，实现团队协同。

## 📋 功能特性

### 🌐 多渠道数据获取
- **加拿大数据源**
  - ✅ Ontario Open Data - 持牌托儿设施
  - ✅ BC Child Care Map - BC省托儿地图
  - 🔜 Alberta Child Care
  - 🔜 CanadaBuys 招标信息

- **澳大利亚数据源**
  - ✅ ACECQA National Registers - 国家注册
  - 🔜 AusTender 政府招标

### 🤖 智能分析
- **AI评分系统** (Claude AI 或 规则引擎)
  - 容量规模评分 (30分)
  - 地理位置评分 (40分)
  - 项目阶段评分 (30分)
  - 特殊加分项

- **自动分级**
  - 🚨 Critical (紧急): ≥90分
  - 🔥 High (高优先级): 85-89分
  - 📌 Medium (中优先级): 70-84分
  - 📋 Low (低优先级): <70分

### 📊 智能去重
- 基于许可证号精确匹配
- 地址+名称组合匹配
- 模糊地址匹配 (相似度>90%)

### 📱 双渠道通知
- **PushPlus微信推送**
  - HTML富文本格式
  - 支持群组推送
  - 每日摘要推送

- **钉钉群机器人**
  - Markdown格式
  - 支持@所有人
  - 安全签名认证

### 📈 Google Sheets追踪
- 新建项目追踪
- 交易信息追踪
- 招标信息追踪
- 数据源监控
- 每日统计汇总

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/childcare-leads-tracker.git
cd childcare-leads-tracker
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件填入你的配置
```

### 5. 配置Google Sheets

详见下方[配置指南](#-配置指南)。

### 6. 运行测试

```bash
# 测试PushPlus
python scripts/test_pushplus.py

# 测试钉钉
python scripts/test_dingtalk.py

# 测试Google Sheets
python scripts/test_sheets.py
```

### 7. 运行系统

```bash
# 演习模式（不写入数据）
DRY_RUN=true python src/main.py

# 正式运行
python src/main.py
```

## ⚙️ 配置指南

### Google Sheets 配置

#### 1. 创建Google Cloud项目

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目 "Childcare-Leads-Tracker"
3. 启用以下API：
   - Google Sheets API
   - Google Drive API

#### 2. 创建服务账号

1. 进入 "IAM和管理" → "服务账号"
2. 点击 "创建服务账号"
3. 名称: `childcare-tracker`
4. 角色: "编辑者"
5. 创建密钥（JSON格式）
6. 下载并保存为 `credentials.json`

#### 3. 共享Google Sheets

1. 创建新的Google Sheets，命名为 "幼儿园商机追踪"
2. 点击右上角 "共享"
3. 添加服务账号邮箱（格式: `xxx@xxx.iam.gserviceaccount.com`）
4. 授予 "编辑者" 权限

### PushPlus 配置

1. 访问 [PushPlus官网](http://www.pushplus.plus/)
2. 微信扫码登录
3. 复制你的Token
4. （可选）创建群组用于团队推送

### 钉钉机器人配置

1. 打开钉钉群聊
2. 群设置 → 智能群助手 → 添加机器人
3. 选择 "自定义机器人"
4. 设置名称: "幼儿园商机助手"
5. 安全设置选择 "加签"
6. 复制Webhook和密钥

### Claude AI 配置（可选）

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 创建API Key
3. 填入 `.env` 文件

## 📁 项目结构

```
childcare-leads-tracker/
├── .github/
│   └── workflows/
│       └── daily_fetch.yml       # GitHub Actions配置
│
├── src/
│   ├── __init__.py
│   ├── main.py                   # 主入口
│   ├── config.py                 # 配置管理
│   │
│   ├── core/
│   │   ├── sheets_manager.py     # Google Sheets操作
│   │   └── data_processor.py     # 数据处理
│   │
│   ├── fetchers/
│   │   ├── base_fetcher.py       # 基类
│   │   ├── ontario_fetcher.py    # Ontario数据
│   │   ├── bc_fetcher.py         # BC数据
│   │   └── acecqa_fetcher.py     # ACECQA数据
│   │
│   ├── analyzers/
│   │   ├── deduplicator.py       # 去重逻辑
│   │   ├── scorer.py             # 规则评分
│   │   └── claude_analyzer.py    # AI评分
│   │
│   ├── notifiers/
│   │   ├── pushplus_notifier.py  # 微信推送
│   │   ├── dingtalk_notifier.py  # 钉钉推送
│   │   └── notification_manager.py
│   │
│   └── utils/
│       ├── logger.py             # 日志
│       ├── validators.py         # 验证
│       └── helpers.py            # 辅助函数
│
├── scripts/
│   ├── test_pushplus.py          # PushPlus测试
│   ├── test_dingtalk.py          # 钉钉测试
│   ├── test_sheets.py            # Sheets测试
│   └── manual_fetch.py           # 手动运行
│
├── logs/                          # 日志目录
├── credentials.json               # Google凭证（.gitignore）
├── .env                           # 环境变量（.gitignore）
├── .env.example                   # 环境变量示例
├── .gitignore
├── requirements.txt
└── README.md
```

## 🔄 GitHub Actions 部署

### 1. Fork仓库

Fork本仓库到你的GitHub账号。

### 2. 配置Secrets

在仓库 Settings → Secrets and variables → Actions 中添加：

| Secret名称 | 说明 |
|-----------|------|
| `GOOGLE_CREDENTIALS` | credentials.json的完整内容 |
| `GOOGLE_SHEET_NAME` | 电子表格名称 |
| `GOOGLE_SHEET_URL` | 电子表格URL |
| `PUSHPLUS_TOKEN` | PushPlus Token |
| `PUSHPLUS_TOPIC` | PushPlus群组代码（可选） |
| `DINGTALK_WEBHOOK` | 钉钉Webhook地址 |
| `DINGTALK_SECRET` | 钉钉加签密钥 |
| `ANTHROPIC_API_KEY` | Claude API Key（可选） |

### 3. 启用Actions

1. 进入仓库的 Actions 标签
2. 启用 workflows
3. 可以手动触发测试运行

### 4. 定时运行

系统默认每天北京时间上午9:00自动运行。

## 📊 Google Sheets 工作表说明

### 新建项目追踪
| 列 | 字段名 | 说明 |
|---|-------|------|
| A | 发现日期 | YYYY-MM-DD |
| B | 国家 | 🇨🇦 Canada / 🇦🇺 Australia |
| C | 省/州 | 省份或州名 |
| D | 城市 | 城市名 |
| E | 项目名称 | 托儿中心名称 |
| F | 完整地址 | 详细地址 |
| G | 容量 | 儿童数量 |
| H | 许可证号 | 唯一标识 |
| I | 许可状态 | 新发/变更/续期 |
| J | 联系电话 | 电话号码 |
| K | 联系邮箱 | 邮箱地址 |
| L | 数据来源 | Ontario/BC/ACECQA等 |
| M | 原始链接 | 数据源URL |
| N | 跟进状态 | 未联系/已联系/已报价/已成交/无效 |
| O | 优先级 | Critical/High/Medium/Low |
| P | AI评分 | 0-100分 |
| Q | 备注 | 自由备注 |
| R | 负责人 | 跟进人员 |
| S | 更新时间 | 最后更新时间 |

## 🛠️ 开发指南

### 添加新数据源

1. 在 `src/fetchers/` 创建新的fetcher类
2. 继承 `BaseFetcher`
3. 实现 `fetch()` 和 `transform()` 方法
4. 在 `src/fetchers/__init__.py` 中导出
5. 在 `src/main.py` 中添加调用逻辑

### 自定义评分规则

编辑 `src/analyzers/scorer.py` 中的评分逻辑：
- `_score_capacity()`: 容量评分
- `_score_location()`: 位置评分
- `_score_stage()`: 阶段评分
- `_calculate_bonus()`: 加分项

### 自定义通知模板

- PushPlus HTML模板: `src/notifiers/pushplus_notifier.py`
- 钉钉Markdown模板: `src/notifiers/dingtalk_notifier.py`

## 📝 日志说明

日志文件保存在 `logs/` 目录，按日期命名：
- `run_2026-01-17.log` - 2026年1月17日的运行日志

## ❓ 常见问题

### Q: Google Sheets连接失败？
A: 检查以下几点：
1. `credentials.json` 是否存在且格式正确
2. 服务账号是否有电子表格的编辑权限
3. Google Sheets API 是否已启用

### Q: PushPlus推送失败？
A: 检查以下几点：
1. Token是否正确
2. 是否超过推送频率限制
3. 网络是否能访问 pushplus.plus

### Q: 钉钉机器人发送失败？
A: 检查以下几点：
1. Webhook地址是否正确
2. 安全设置（关键词/加签/IP白名单）是否匹配
3. 机器人是否被禁用

### Q: 数据获取失败？
A: 检查以下几点：
1. 网络是否能访问数据源URL
2. 数据源是否已更改格式
3. 查看日志获取详细错误信息

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题，请通过 Issue 联系。

---

**Made with ❤️ for the childcare industry**
