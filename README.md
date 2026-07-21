---
ako_doc_id: AKO_README_MED_001
ako_version: v0.1.0
ako_status: 草稿
ako_title: 媒体 Agent (MED)
ako_category: 媒体
ako_author: 杨越浩
ako_created: 2026-07-14
ako_source: AKO_DOC_001 v1.0.0
ako_project_root: D:\AKO_media_agent
---

# 媒体 Agent（MED）

## 1. 结论前置

AKO 媒体 Agent（MED）是 AKO 品牌体系的自主媒体数据智能体，基于五层架构（数据采集→智能分析→决策引擎→内容执行→反馈闭环）实现品牌内容的自动化生产与多平台分发。当前版本 v1.2，支持 7 大社交媒体平台数据采集、NLP 智能分析、AI 文案生成和多平台自动发布。核心理念：思想厚度 > 传播效率，品牌高度 > 流量规模。

## 2. 修订记录

| 版本 | 日期 | 修订人 | 修订内容 | 签发人 |
|------|------|--------|----------|--------|
| v0.1.0 | 2026-07-14 | 杨越浩 | 按 AKO_DOC_001 初始化 | （待签发） |

## 3. 项目概述

### 3.1 定位

AKO 品牌思想表达的放大器——不是"内容生产工具"，而是让 AKO 的每一句话都更不可替代的智能内容运营系统。

### 3.2 核心能力

- **自主数据采集**：7x24 小时无人值守抓取小红书、抖音、微博、B站、知乎、公众号、视频号 7 大平台内容，含 RSS 新闻监控、竞品追踪、趋势探测（百度/抖音/小红书/微信指数）
- **智能分析**：NLP 情感分析（jieba/阿里云 NLP/LLM 三级）、主题聚类（BERTopic/TF-IDF+KMeans）、关键词提取（TF-IDF+TextRank）、互动预测、竞品缺口分析
- **数据驱动决策**：自动生成内容策略与选题、标题优化（点击率/搜索/社交三引擎）、最佳发布时间推算
- **自动执行**：AI 文案生成（DeepSeek）、视觉配图、多平台发布（公众号/博客自动，小红书/抖音半自动），含小程序内容同步与 SEO 优化
- **反馈闭环**：表现追踪、策略自动调整、异常回退，分三阶段推进自动化率（Phase 1 100% 人工审核 → Phase 2 50% 抽检 → Phase 3 85%+ 自动化）

### 3.3 技术栈

- Python 3.9+（Playwright 数据采集、scikit-learn 分析、jieba 分词）
- DeepSeek API（文案生成）
- BERTopic / transformers（主题聚类，可选）
- MySQL / SQLite（双引擎数据库，自动回退）
- YAML + .env（配置管理）

## 4. 快速开始

### 4.1 环境要求

- Python 3.9+
- MySQL 5.7+（可选，默认使用 SQLite）
- Playwright 浏览器

### 4.2 安装

```bash
cd D:\AKO_media_agent
pip install -r requirements.txt
playwright install chromium
```

配置环境变量：
```bash
cp secrets.env.example secrets.env
# 编辑 secrets.env 填入 API 密钥和数据库连接信息
```

### 4.3 运行

```bash
# 初始化数据库
python src/main.py init-db

# 启动完整流水线
python src/main.py start

# 或分步执行
python src/main.py crawl      # 仅数据采集
python src/main.py analyze    # 仅智能分析
python src/main.py decide     # 仅决策引擎
python src/main.py publish    # 仅内容发布
python src/main.py feedback   # 仅反馈闭环
python src/main.py status     # 查看系统状态
```

## 5. 项目结构

```
D:\AKO_media_agent/
├── src/
│   ├── main.py                      # 主入口（CLI 命令）
│   ├── database.py                  # 数据库管理（MySQL/SQLite 双引擎）
│   ├── crawler/                     # Layer 1: 数据收集
│   │   ├── media_crawler.py         #   7 大平台采集（MediaCrawler 封装）
│   │   ├── news_monitor.py          #   RSS 新闻监控 + LLM 摘要
│   │   ├── competitor_tracker.py    #   竞品追踪
│   │   ├── trend_detector.py        #   趋势探测
│   │   └── compliance/              #   合规模块（代理IP/账号轮换/频率控制/验证码）
│   ├── analysis/                    # Layer 2: 智能分析
│   │   ├── sentiment_analyzer.py    #   情感分析（三级引擎）
│   │   ├── topic_cluster.py         #   主题聚类
│   │   ├── keyword_extractor.py     #   关键词提取
│   │   ├── engagement_predictor.py  #   互动预测
│   │   └── gap_analyzer.py          #   竞品缺口分析
│   ├── decision/                    # Layer 3: 决策引擎
│   │   ├── content_planner.py       #   内容规划
│   │   ├── title_optimizer.py       #   标题优化
│   │   └── timing_optimizer.py      #   发布时间优化
│   ├── execution/                   # Layer 4: 执行层
│   │   ├── copywriter.py            #   AI 文案生成
│   │   ├── visual_generator.py      #   视觉生成
│   │   ├── publisher.py             #   多平台发布
│   │   └── mini_program/            #   小程序模块（同步/推荐/SEO）
│   ├── feedback/                    # Layer 5: 反馈闭环
│   │   ├── performance_tracker.py   #   表现追踪
│   │   ├── strategy_adjuster.py     #   策略调整
│   │   └── rollback_manager.py      #   异常回退
│   └── evolution/                   # 进化模块（记忆/学习/涌现）
├── config/
│   ├── AKO_media_agent_config.yaml  # 全局配置
│   ├── crawler_config.py            # 采集合规配置
│   └── platform_settings.json       # 平台发布参数
├── templates/                       # 内容模板（6 大栏目）
│   ├── ako_building_log_v2.md       #   AKO 建造志
│   ├── cost_talk_v2.md              #   造价说
│   ├── twilight_architecture_v2.md  #   黄昏建筑
│   ├── tech_0154_v2.md              #   0154 技术谈
│   ├── site_24h_v2.md               #   工地 24 时
│   └── ako_people_v2.md             #   AKO 人物
├── prompts/                         # 提示词模板
│   ├── copywriting_prompts/         #   品牌文案生成提示词
│   ├── analysis_prompts/            #   分析提示词
│   └── brand_corpus/                #   品牌语料库
├── whitepaper/                      # 项目白皮书
├── docs/                            # 用户文档
├── compliance/                      # 合规文档（法务/数据/应急）
├── secrets.env.example              # 环境变量模板
├── requirements.txt                 # Python 依赖
└── pyproject.toml                   # 项目元数据
```

## 6. 相关文档

- 白皮书：`whitepaper/AKO_media_agent_whitepaper_v1.2.md`
- 学习模块设计：`whitepaper/AKO_media_agent_learning_module_v1.0.md`
- 用户手册：`docs/user_manual.md`
- 合规文档：`compliance/`（法务审查清单、数据使用政策、应急响应预案）

## 7. 术语

| 术语 | 定义 |
|------|------|
| 五层架构 | 数据采集（Layer 1）→ 智能分析（Layer 2）→ 决策引擎（Layer 3）→ 内容执行（Layer 4）→ 反馈闭环（Layer 5） |
| MediaCrawler | 开源社交媒体爬虫框架（MIT 协议），支持 7 大平台数据采集 |
| 思想厚度 | AKO 内容哲学核心指标：不可替代性 (40%) + 具体性 (30%) + 时间诚实 (15%) + 人的在场 (15%) |
| 精致静谧 | AKO 视觉情绪公式：暖金统治 + 白色软化 + 黑色沉稳 + 人的在场 + 时间的诚实 |
| 分阶段自动化 | Phase 1（100% 人工审核）→ Phase 2（50% 抽检）→ Phase 3（85%+ 自动化） |
