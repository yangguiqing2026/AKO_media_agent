# AKO Media Agent 用户手册

> 版本：v1.2 | 最后更新：2026年7月

---

## 目录

1. [系统概述](#1-系统概述)
2. [安装部署](#2-安装部署)
3. [环境配置](#3-环境配置)
4. [数据库管理](#4-数据库管理)
5. [日常操作](#5-日常操作)
6. [数据采集配置](#6-数据采集配置)
7. [分析引擎配置](#7-分析引擎配置)
8. [内容生成与发布](#8-内容生成与发布)
9. [反馈闭环](#9-反馈闭环)
10. [合规管理](#10-合规管理)
11. [故障排查](#11-故障排查)
12. [常见问题](#12-常见问题)

---

## 1. 系统概述

AKO Media Agent 是阿格建筑（AKO）的品牌媒体智能运营系统。系统通过五层架构实现从数据采集到内容发布的全链路自动化。

### 1.1 五层架构

| 层级 | 名称 | 职责 |
|------|------|------|
| Layer 1 | 数据收集 | 7大平台数据采集、RSS新闻监控、趋势探测、竞品追踪 |
| Layer 2 | 智能分析 | 情感分析、主题聚类、关键词提取、互动预测、缺口分析 |
| Layer 3 | 决策引擎 | 内容规划、标题优化、发布时间优化 |
| Layer 4 | 执行层 | AI文案生成、视觉生成、多平台发布、小程序同步 |
| Layer 5 | 反馈闭环 | 表现追踪、策略调整、异常回退 |

### 1.2 六大栏目

| 栏目 | 定位 | 发布频率 |
|------|------|----------|
| AKO建造志 | 项目案例展示 | 每周1-2篇 |
| 造价说 | 成本分析解读 | 每周1篇 |
| 黄昏建筑 | 建筑美学思考 | 每周1篇 |
| 0154技术谈 | 技术深度解析 | 每两周1篇 |
| 工地24时 | 施工现场纪实 | 每周1-2篇 |
| AKO人物 | 团队人物故事 | 每月2篇 |

### 1.3 思想厚度评分

所有内容发布前需通过思想厚度评分（满分100分，发布阈值≥75分）：

| 维度 | 权重 | 说明 |
|------|------|------|
| 不可替代性 | 40% | 是否只有AKO能写出这样的内容 |
| 具体性 | 30% | 是否有真实数据、具体案例、现场细节 |
| 时间诚实 | 15% | 是否体现长期积累而非速成 |
| 人的在场 | 15% | 是否有真实人物、真实感受、真实场景 |

---

## 2. 安装部署

### 2.1 环境要求

| 组件 | 最低版本 | 说明 |
|------|----------|------|
| Python | 3.10+ | 推荐3.12 |
| MySQL | 5.7+ | 可选，默认使用SQLite |
| 操作系统 | Windows 10/11, Linux, macOS | |

### 2.2 安装步骤

**第一步：安装Python依赖**

```bash
pip install -r requirements.txt
```

**第二步：安装Playwright浏览器**（数据采集必需）

```bash
pip install playwright
playwright install chromium
```

**第三步：配置环境变量**

```bash
cp secrets.env.example secrets.env
```

编辑 `secrets.env`，填入API密钥（详见第3节）。

**第四步：初始化数据库**

```bash
python src/main.py init-db
```

**第五步：验证安装**

```bash
python src/main.py status
```

如果看到五层架构全部 `[OK]`，则安装成功。

### 2.3 数据库选择

系统支持 MySQL 和 SQLite 两种数据库，默认使用 SQLite（零配置）。

**使用SQLite（默认）**：无需额外配置，数据存储在 `data/ako_media_agent.db`

**使用MySQL**：在 `secrets.env` 中设置：

```env
DB_ENGINE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ako_media_agent
DB_USER=root
DB_PASSWORD=your_password
```

---

## 3. 环境配置

### 3.1 secrets.env 配置项

#### 数据库配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_ENGINE` | 数据库引擎（`sqlite`/`mysql`） | `sqlite` |
| `DB_HOST` | MySQL主机 | `localhost` |
| `DB_PORT` | MySQL端口 | `3306` |
| `DB_NAME` | 数据库名 | `ako_media_agent` |
| `DB_USER` | 数据库用户 | `root` |
| `DB_PASSWORD` | 数据库密码 | - |

#### LLM配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | 大模型API密钥 | - |
| `LLM_BASE_URL` | API端点 | `https://api.deepseek.com/v1` |
| `LLM_MODEL` | 模型名称 | `deepseek-chat` |
| `DEEPSEEK_API_KEY` | DeepSeek专用密钥 | - |
| `NLP_PROVIDER` | 情感分析引擎（`jieba`/`aliyun`/`llm`） | `jieba` |

#### 阿里云NLP配置（可选）

| 变量 | 说明 |
|------|------|
| `ALIYUN_NLP_ACCESS_KEY_ID` | 阿里云AccessKey ID |
| `ALIYUN_NLP_ACCESS_KEY_SECRET` | 阿里云AccessKey Secret |
| `ALIYUN_NLP_ENDPOINT` | NLP服务地址 |

#### 代理服务配置

| 变量 | 说明 |
|------|------|
| `BRIGHT_DATA_API_KEY` | Bright Data代理API密钥 |
| `DATAIMPULSE_API_KEY` | DataImpulse代理API密钥（备选） |

### 3.2 全局配置文件

`config/AKO_media_agent_config.yaml` 包含系统所有运行参数：

```yaml
# 关键配置项
project:
  name: AKO Media Agent
  version: "1.2.0"
  environment: development  # development / staging / production

layers:
  crawler:
    enabled: true
    media_crawler:
      platforms: [xhs, dy, wb, bili, zhihu, wechat, shipinhao]
      keywords: ["装配式建筑", "模块化住宅", "贵州建筑"]
  
  analysis:
    enabled: true
    sentiment:
      crisis_alert:
        negative_ratio_threshold: 0.30
  
  decision:
    enabled: true
    content_planner:
      thought_depth_threshold: 75  # 思想厚度发布阈值
  
  executor:
    enabled: true
    copywriter:
      provider: deepseek
  
  feedback:
    enabled: true
```

---

## 4. 数据库管理

### 4.1 数据表说明

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `crawled_data` | 爬取数据 | platform, title, content, likes, comments |
| `competitor_data` | 竞品数据 | competitor_name, content_theme, is_viral |
| `trend_data` | 趋势数据 | source, keyword, heat_index, rank |
| `news_data` | 新闻数据 | source, title, summary, is_policy_change |
| `content` | 内容草稿 | article_id, column_name, status, thought_depth_score |
| `publish_record` | 发布记录 | article_id, platform, publish_url, status |
| `performance_data` | 表现数据 | article_id, reads, likes, negative_ratio |
| `strategy_adjustments` | 策略调整 | adjustment_type, old_value, new_value |

### 4.2 数据库操作

```bash
# 初始化建表
python src/main.py init-db

# 手动查询（SQLite）
sqlite3 data/ako_media_agent.db
> SELECT * FROM crawled_data LIMIT 10;
```

---

## 5. 日常操作

### 5.1 CLI命令

```bash
# 启动完整流水线
python src/main.py start

# 分步执行
python src/main.py crawl      # 数据采集
python src/main.py analyze    # 智能分析
python src/main.py decide     # 决策引擎
python src/main.py publish    # 内容发布
python src/main.py feedback   # 反馈闭环

# 查看状态
python src/main.py status
```

### 5.2 分阶段运营模式

#### Phase 1（前3个月）：100%人工审核

所有内容必须经过人工审核后才能发布。系统生成草稿 → 人工审核 → 手动发布。

#### Phase 2（3-6个月）：50%抽检

思想厚度≥85分的内容可自动发布，其余需人工审核。每周抽检50%已发布内容。

#### Phase 3（6-12个月）：85%+自动化

思想厚度≥75分的内容自动发布，仅低分内容需人工干预。

### 5.3 内容生命周期

```
采集数据 → 分析洞察 → 规划选题 → 生成草稿 → 审核 → 发布 → 追踪表现 → 策略调整
   draft  → review → scheduled → published → (withdrawn)
```

---

## 6. 数据采集配置

### 6.1 MediaCrawler采集

系统通过 Playwright 模拟浏览器访问7大平台，采集与关键词相关的内容。

**采集关键词**（在 `config/AKO_media_agent_config.yaml` 中配置）：

```yaml
layers:
  crawler:
    media_crawler:
      keywords:
        - "装配式建筑"
        - "模块化住宅"
        - "贵州建筑"
        - "AKO建筑"
```

### 6.2 RSS新闻监控

系统自动监控RSS源，获取行业最新资讯并生成AI摘要。

**默认RSS源**：
- 中国建筑新闻网
- 住建部官网

### 6.3 趋势探测

支持4个趋势数据源：
- 百度指数（需要Cookie）
- 微信指数（搜狗微信搜索）
- 抖音热榜
- 小红书热搜

### 6.4 合规参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 最小请求间隔 | 2秒 | 防止被封 |
| 随机抖动 | ±0.5秒 | 模拟人类行为 |
| 日请求上限 | 500条/平台 | 防止过度采集 |
| 活跃时段 | 09:00-23:00 | 非活跃时段暂停 |
| 账号池大小 | 5个/平台 | 轮换使用 |

---

## 7. 分析引擎配置

### 7.1 情感分析

支持三种引擎，通过 `NLP_PROVIDER` 环境变量切换：

| 引擎 | 说明 | 适用场景 |
|------|------|----------|
| `jieba`（默认） | 本地规则引擎，免费 | Phase 1 初期 |
| `aliyun` | 阿里云NLP API | 需要更高精度 |
| `llm` | DeepSeek大模型 | 最准确，消耗API额度 |

### 7.2 主题聚类

- **BERTopic**：安装 `pip install bertopic` 后自动启用，效果最佳
- **TF-IDF + KMeans**：默认回退方案，无需额外依赖

### 7.3 关键词提取

支持 TF-IDF 和 TextRank 两种方法，默认同时使用并合并结果。

### 7.4 互动预测

Phase 1 使用规则基线公式：

```
predicted_reads = followers × base_rate × title_score × hour_coefficient
```

随着数据积累，逐步切换到回归模型。

---

## 8. 内容生成与发布

### 8.1 AI文案生成

使用 DeepSeek `deepseek-chat` 模型生成文案，遵循品牌风格指南：

- **段落结构**：切片-展开-收束
- **品牌色系**：奶油金#EBDAB9、深棕黑#231E1C、琥珀金#A08C64
- **语言风格**：专业但不枯燥，有温度有深度

### 8.2 内容模板

6大栏目各有专属模板，位于 `templates/` 目录：

| 模板文件 | 栏目 |
|----------|------|
| `ako_building_log_v2.md` | AKO建造志 |
| `cost_talk_v2.md` | 造价说 |
| `twilight_architecture_v2.md` | 黄昏建筑 |
| `tech_0154_v2.md` | 0154技术谈 |
| `site_24h_v2.md` | 工地24时 |
| `ako_people_v2.md` | AKO人物 |

### 8.3 发布流程

| 平台 | 发布方式 | 说明 |
|------|----------|------|
| 公众号 | 自动 | 通过微信桥接API |
| 博客 | 自动 | 通过API发布 |
| 小红书 | 半自动 | 生成内容，人工确认发布 |
| 抖音 | 半自动 | 生成内容，人工确认发布 |
| LinkedIn | 半自动 | 生成内容，人工确认发布 |

### 8.4 版本管理

内容支持版本化管理，每次修改自动保存新版本，支持回退。

---

## 9. 反馈闭环

### 9.1 表现追踪

自动追踪已发布内容的表现数据：
- 阅读量、点赞、评论、转发、收藏
- 完读率、粉丝增长
- 负面评论比例

### 9.2 策略调整

根据表现数据自动建议策略调整：
- 内容方向调整
- 发布时间优化
- 平台权重调整

### 9.3 异常回退

自动检测异常情况并触发回退：
- 负面评论比例 > 50%
- 阅读量 < 预估的20%
- 触发自动撤回并通知

---

## 10. 合规管理

### 10.1 数据采集合规

- 仅采集公开可见内容
- 不采集用户隐私数据（手机号、地址等自动脱敏）
- 遵守各平台robots.txt
- 控制采集频率，不影响平台正常运行

### 10.2 内容发布合规

- 不抄袭、不洗稿
- 标注数据来源
- 遵守广告法相关规定
- 不做虚假宣传

### 10.3 合规文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 法务审查清单 | `compliance/legal_review.md` | 上线前法务审查 |
| 数据使用政策 | `compliance/data_usage_policy.md` | 数据采集和使用规范 |
| 应急响应预案 | `compliance/incident_response.md` | 异常情况处理流程 |

---

## 11. 故障排查

### 11.1 系统启动失败

```bash
# 检查Python版本
python --version  # 需要3.10+

# 检查依赖安装
pip list | grep -E "pyyaml|pymysql|feedparser|jieba|scikit-learn|openai"

# 检查配置文件
python -c "import yaml; yaml.safe_load(open('config/AKO_media_agent_config.yaml', encoding='utf-8')); print('YAML OK')"
```

### 11.2 数据库连接失败

```bash
# SQLite模式（默认）- 检查data目录权限
ls -la data/

# MySQL模式 - 检查连接
python -c "import pymysql; pymysql.connect(host='localhost', port=3306, user='root', password='xxx'); print('MySQL OK')"
```

### 11.3 数据采集失败

```bash
# 检查Playwright安装
playwright install chromium

# 检查代理配置
python -c "from src.crawler.compliance.proxy_manager import ProxyManager; pm = ProxyManager({}); print(pm.get_proxy())"
```

### 11.4 LLM调用失败

```bash
# 检查API密钥
python -c "from dotenv import load_dotenv; load_dotenv('secrets.env'); import os; print(os.getenv('LLM_API_KEY','')[:10]+'...')"

# 测试API连通
python -c "from openai import OpenAI; import os; from dotenv import load_dotenv; load_dotenv('secrets.env'); c = OpenAI(api_key=os.getenv('LLM_API_KEY'), base_url=os.getenv('LLM_BASE_URL')); r = c.chat.completions.create(model='deepseek-chat', messages=[{'role':'user','content':'hi'}], max_tokens=10); print(r.choices[0].message.content)"
```

### 11.5 常见错误码

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `ModuleNotFoundError` | 依赖未安装 | `pip install -r requirements.txt` |
| `UnicodeDecodeError` | Windows编码问题 | 代码已修复，确保使用UTF-8 |
| `Playwright Error` | 浏览器未安装 | `playwright install chromium` |
| `Connection Refused` | MySQL未启动 | 启动MySQL或切换SQLite模式 |
| `API 401` | API密钥无效 | 检查 `secrets.env` 中的密钥 |

---

## 12. 常见问题

### Q: 没有MySQL可以用吗？

可以。系统默认使用SQLite，无需安装任何数据库。数据存储在 `data/ako_media_agent.db` 文件中。

### Q: 没有API密钥能运行吗？

可以。没有LLM API密钥时，新闻摘要返回原文截断，情感分析使用本地jieba规则引擎，文案生成模块跳过。系统核心功能不受影响。

### Q: 如何切换到MySQL？

编辑 `secrets.env`：
```env
DB_ENGINE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ako_media_agent
DB_USER=root
DB_PASSWORD=your_password
```
然后运行 `python src/main.py init-db`。

### Q: 如何添加新的采集平台？

1. 在 `src/crawler/media_crawler.py` 的 `PLATFORM_URLS` 中添加平台配置
2. 在 `config/AKO_media_agent_config.yaml` 的 `platforms` 列表中添加平台标识

### Q: 如何修改思想厚度发布阈值？

编辑 `config/AKO_media_agent_config.yaml`：
```yaml
layers:
  decision:
    content_planner:
      thought_depth_threshold: 80  # 修改此值
```

### Q: 如何查看系统运行日志？

日志输出到控制台，同时保存在 `logs/` 目录（如已配置）。Windows下可通过重定向查看：

```bash
python src/main.py start 2>&1
```

---

*如有其他问题，请联系技术团队。*
