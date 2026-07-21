# AKO Media Agent v1.2

**阿格建筑品牌自主媒体数据智能体** — 基于五层架构的媒体内容自动化系统

## 项目简介

AKO Media Agent 是阿格建筑（AKO）的品牌媒体智能运营系统，通过数据采集→智能分析→决策引擎→内容执行→反馈闭环的五层架构，实现品牌内容的自动化生产与多平台分发。

### 核心理念

- **思想厚度 > 传播效率**：不可替代性(40%) + 具体性(30%) + 时间诚实(15%) + 人的在场(15%)
- **合规优先**：代理IP池、多账号轮换、频率控制、验证码自动暂停
- **分阶段自动化**：Phase 1 100%人工审核 → Phase 2 50%抽检 → Phase 3 85%+自动化

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│  Layer 5: 反馈闭环                                    │
│  表现追踪 → 策略调整 → 异常回退                         │
├─────────────────────────────────────────────────────┤
│  Layer 4: 执行层                                      │
│  AI文案生成 → 视觉生成 → 多平台发布 → 小程序同步         │
├─────────────────────────────────────────────────────┤
│  Layer 3: 决策引擎                                    │
│  内容规划 → 标题优化 → 发布时间优化                      │
├─────────────────────────────────────────────────────┤
│  Layer 2: 智能分析                                    │
│  情感分析 → 主题聚类 → 关键词提取 → 互动预测 → 缺口分析  │
├─────────────────────────────────────────────────────┤
│  Layer 1: 数据收集                                    │
│  MediaCrawler(7平台) → RSS新闻 → 趋势探测 → 竞品追踪   │
└─────────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.9+
- MySQL 5.7+（可选，默认使用SQLite）

### 安装

```bash
# 1. 克隆项目
git clone <repo_url>
cd AKO_media_agent

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp secrets.env.example secrets.env
# 编辑 secrets.env 填入API密钥

# 4. 初始化数据库
python src/main.py init-db

# 5. 启动系统
python src/main.py start
```

### 安装 Playwright（数据采集必需）

```bash
pip install playwright
playwright install chromium
```

## 项目结构

```
AKO_media_agent/
├── config/                          # 配置文件
│   ├── AKO_media_agent_config.yaml  # 全局配置（五层参数、审核流程、内容矩阵）
│   ├── crawler_config.py            # MediaCrawler合规配置
│   └── platform_settings.json       # 平台发布参数
├── src/
│   ├── main.py                      # 主入口（CLI命令）
│   ├── database.py                  # 数据库管理（MySQL/SQLite双引擎）
│   ├── crawler/                     # Layer 1: 数据收集
│   │   ├── media_crawler.py         #   MediaCrawler封装（7大平台）
│   │   ├── news_monitor.py          #   RSS新闻监控 + 大模型摘要
│   │   ├── competitor_tracker.py    #   竞品追踪
│   │   ├── trend_detector.py        #   趋势探测（百度/抖音/小红书/微信）
│   │   └── compliance/              #   合规模块
│   │       ├── proxy_manager.py     #     代理IP池
│   │       ├── account_pool.py      #     多账号轮换
│   │       ├── rate_limiter.py      #     频率控制
│   │       └── captcha_handler.py   #     验证码处理
│   ├── analysis/                    # Layer 2: 智能分析
│   │   ├── sentiment_analyzer.py    #   情感分析（jieba/阿里云NLP/LLM）
│   │   ├── topic_cluster.py         #   主题聚类（BERTopic/TF-IDF+KMeans）
│   │   ├── keyword_extractor.py     #   关键词提取（TF-IDF/TextRank）
│   │   ├── engagement_predictor.py  #   互动预测
│   │   └── gap_analyzer.py          #   竞品缺口分析
│   ├── decision/                    # Layer 3: 决策引擎
│   │   ├── content_planner.py       #   内容规划
│   │   ├── title_optimizer.py       #   标题优化
│   │   └── timing_optimizer.py      #   发布时间优化
│   ├── execution/                   # Layer 4: 执行层
│   │   ├── copywriter.py            #   AI文案生成（DeepSeek）
│   │   ├── visual_generator.py      #   视觉生成
│   │   ├── publisher.py             #   多平台发布
│   │   └── mini_program/            #   小程序模块
│   │       ├── content_sync.py      #     内容同步
│   │       ├── recommendation.py    #     数据驱动推荐
│   │       ├── form_trigger.py      #     表单触发
│   │       ├── monitor.py           #     小程序监控
│   │       └── seo_optimizer.py     #     SEO优化
│   └── feedback/                    # Layer 5: 反馈闭环
│       ├── performance_tracker.py   #   表现追踪
│       ├── strategy_adjuster.py     #   策略调整
│       └── rollback_manager.py      #   异常回退
├── templates/                       # 内容模板（6大栏目）
│   ├── ako_building_log_v2.md       #   AKO建造志
│   ├── cost_talk_v2.md              #   造价说
│   ├── twilight_architecture_v2.md  #   黄昏建筑
│   ├── tech_0154_v2.md              #   0154技术谈
│   ├── site_24h_v2.md               #   工地24时
│   └── ako_people_v2.md             #   AKO人物
├── prompts/                         # 提示词模板
│   ├── copywriting_prompts/         #   品牌文案生成提示词
│   ├── analysis_prompts/            #   分析提示词模板
│   └── brand_corpus/                #   品牌语料库
├── compliance/                      # 合规文档
│   ├── legal_review.md              #   法务审查清单
│   ├── data_usage_policy.md         #   数据使用政策
│   └── incident_response.md         #   应急响应预案
├── whitepaper/                      # 项目白皮书
├── data/                            # 数据存储（SQLite）
├── secrets.env                      # 环境变量（不入Git）
├── requirements.txt                 # Python依赖
└── pyproject.toml                   # 项目元数据
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `python src/main.py start` | 启动完整流水线（采集→分析→决策→发布→反馈） |
| `python src/main.py crawl` | 仅执行数据采集 |
| `python src/main.py analyze` | 仅执行智能分析 |
| `python src/main.py decide` | 仅执行决策引擎 |
| `python src/main.py publish` | 仅执行内容发布 |
| `python src/main.py feedback` | 仅执行反馈闭环 |
| `python src/main.py status` | 查看系统状态 |
| `python src/main.py init-db` | 初始化数据库（建表） |

## 技术栈

| 组件 | 技术选型 |
|------|----------|
| 数据采集 | Playwright + MediaCrawler (MIT) |
| 情感分析 | jieba规则引擎 / 阿里云NLP / DeepSeek LLM |
| 主题聚类 | BERTopic / TF-IDF + KMeans |
| 关键词提取 | TF-IDF + TextRank |
| 文案生成 | DeepSeek API (`deepseek-chat`) |
| 数据库 | MySQL / SQLite（自动回退） |
| 配置管理 | YAML + .env |

## 支持平台

| 平台 | 采集 | 发布 |
|------|------|------|
| 小红书 | ✅ | 半自动 |
| 抖音 | ✅ | 半自动 |
| 微博 | ✅ | - |
| B站 | ✅ | - |
| 知乎 | ✅ | - |
| 公众号 | ✅ | 自动 |
| 视频号 | ✅ | - |
| 博客 | - | 自动 |
| LinkedIn | - | 半自动 |

## 文档

- [用户手册](docs/user_manual.md) — 详细使用说明
- [白皮书](whitepaper/AKO_media_agent_whitepaper_v1.2.md) — 系统设计方案
- [合规文档](compliance/) — 法务审查、数据政策、应急预案

## 许可证

本项目为阿格建筑内部使用，未经授权不得外传。
