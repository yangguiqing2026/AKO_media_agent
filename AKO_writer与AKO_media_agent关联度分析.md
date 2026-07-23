# AKO_writer · AKO_media_agent · AKO工作流 三项目关联度分析

> 分析日期：2026-07-22 | 基于三者源代码、配置及文档的交叉对比

---

## 一、三项目定位总览

| 维度 | AKO_writer (WTR) | AKO_media_agent (MED) | AKO工作流 (WFL) |
|------|-------------------|------------------------|-------------------|
| 定位 | 技术文档自动化写作流水线 | 品牌媒体智能运营系统 | 多模型协作文档评定引擎 |
| 版本 | v0.1.0-phase1 | v1.2 | v1.0.2 |
| 核心产出 | 结构化大纲 → 章节正文 (Markdown) | 品牌内容 → 多平台发布 (社交媒体) | 技术评定报告 (Word .docx) |
| 输入 | 选题卡片 (TopicCard) | 采集数据 + 趋势 + 竞品 | 技术文档 (Word/PDF/PPT/Excel/txt/md) |
| 输出 | outline.md → 技术论文/方案/报告 | 社交媒体推文/文章/视频脚本 | 结构化评定报告 (技术+商业+法律+可行性) |
| 用户 | AKO 技术团队 Owner | AKO 品牌运营团队 | AKO 技术决策团队 |
| 生态角色 | AKO Hub Spoke | 独立 Agent (五层架构) | 独立评定引擎 |
| 核心问题 | "这篇文章该怎么写？" | "品牌内容怎么发？" | "这个方案/文章靠不靠谱？" |
| LLM 策略 | Kimi → DeepSeek 降级链 | DeepSeek 单引擎 | Kimi + DeepSeek + 阿里云通义千问 三模型并发 |

---

## 二、架构对比

### 2.1 AKO_writer 架构 (LangGraph StateGraph)

```
InputContract (选题卡片)
    ↓
N0: 选题节点 → 人工确认 → [批准/驳回]
    ↓
N1: 检索节点 (AKO_Hub KnowledgeHub + AKO_knowledge ChromaDB)
    ↓
N2: 大纲节点 (LLM: Kimi → DeepSeek 降级)
    ↓ 人工确认 → [批准/驳回]
N3: 撰写节点 (逐章 LLM 生成)
    ↓
Output: outline.md + 正文 .md 文件
```

### 2.2 AKO_media_agent 架构 (五层架构)

```
Layer 1: 数据采集 (7平台 + RSS + 竞品 + 趋势)
    ↓
Layer 2: 智能分析 (情感/聚类/关键词/互动预测/缺口)
    ↓
Layer 3: 决策引擎 (内容规划/标题优化/时间优化)
    ↓
Layer 4: 执行层 (AI文案/视觉/多平台发布/小程序)
    ↓
Layer 5: 反馈闭环 (表现追踪/策略调整/异常回退)
    +
进化模块 (记忆/学习/涌现)
```

### 2.3 AKO工作流 架构 (9节点 LangGraph StateGraph)

```
待检索文件 (Word/PDF/PPT/Excel/txt/md)
    ↓
Node 0: input_parser     → 文件解析 + 需求分类
    ↓
Node 1: retriever        → DuckDuckGo 外部知识检索
    ↓
Node 2: technical        → Kimi 技术方案生成 (验证失败自循环)
    ↓ (含商业需求时)
Node 3: business         → Kimi 商业方案生成
    ↓
Node 4: reverse_check    → 技术方案反向验证 (风险/成本/竞争/合规四维压力测试)
    ↓
Node 5: quality          → Kimi + DeepSeek + 通义千问 三模型并发投票 (质量评分 ≥0.8)
    ↓ (不达标回退 retriever，最多迭代3次)
Node 6: legal            → 通义千问 法律合规审查 (合同类型触发)
    ↓
Node 7: feasibility      → DeepSeek 可行性研究 (技术+经济+市场+环境四维)
    ↓
Node 8: output           → 生成 Word .docx 评定报告
    ↓
Output: docs/结论文件/{filename}_评定报告.docx
```

### 2.4 三项目架构共同点

| 共同特征 | WTR | MED | WFL |
|----------|-----|-----|-----|
| 编排方式 | LangGraph StateGraph | 自研 CLI + 流水线 | LangGraph StateGraph |
| 人工介入点 | N0/N2 两处 confirm | 五级审核 | 交互模式逐步确认 |
| 持久化 | checkpoint.json 文件 | MySQL/SQLite 数据库 | processed_files.json MD5追踪 |
| 重试/迭代 | LLM 重试2次 + 占位降级 | 无内置重试 | 技术验证自循环 + 质量不达标回退检索 (max 3次) |
| 最终产出 | .md 文件 | 数据库 + 多平台 API | .docx Word 报告 |
| 多模型 | Kimi + DeepSeek | DeepSeek | Kimi + DeepSeek + 通义千问 |

---

## 三、功能关联矩阵

### 3.1 高度关联区域 (直接互补/可集成)

| 关联领域 | AKO_writer 能力 | AKO_media_agent 能力 | 关联度 | 集成可能性 |
|----------|----------------|---------------------|--------|-----------|
| **AI 文案生成** | N3 节点逐章 LLM 生成技术论文正文 | Copywriter 生成品牌社交媒体文案 | ★★★★★ | **极高** - 可共享 LLM 调用逻辑、Prompt 模板体系 |
| **知识库检索** | N1 节点调用 AKO_Hub + AKO_knowledge ChromaDB | 无自有知识库检索 (仅采集外部公开数据) | ★★★★★ | **极高** - MED 可复用 WTR 的知识检索基础设施 |
| **内容审核** | N0/N2 人工确认节点 (approved/rejected+revisions) | 五级审核流程 (AI自审→初评→运营→终审→静默期) | ★★★★☆ | **高** - 审核机制可互相参考，WTR 可引入 MED 的思想厚度评分 |
| **LLM 调用** | Kimi/DeepSeek 降级链，OpenAI 兼容协议 | DeepSeek (deepseek-chat) 单一引擎 | ★★★★☆ | **高** - WTR/WFL 的降级链模式可被 MED 的 Copywriter 模块采纳 |
| **内容模板** | Prompt 模板 (CHAPTER_PROMPT/STRUCTURE_PROMPT) | 6大栏目模板 (templates/*.md) | ★★★★☆ | **高** - WTR 的技术写作模板可扩充 MED 的 "0154技术谈" 栏目 |

### 3.2 中度关联区域 (可协同/可参考)

| 关联领域 | AKO_writer 能力 | AKO_media_agent 能力 | 关联度 | 集成可能性 |
|----------|----------------|---------------------|--------|-----------|
| **内容规划** | TopicCard (topic/doc_type/target_length/audience) | ContentPlanner (5条规划规则: 热点/竞品/常青/事件/政策) | ★★★☆☆ | **中** - WTR 的 TopicCard 可作为 MED ContentPlanner 的一种触发源 |
| **标题优化** | 无专用模块 (N2 大纲天然含标题) | TitleOptimizer (6大公式 + 三引擎评分) | ★★★☆☆ | **中** - WTR 文章章节标题可借用 MED 的标题公式优化 |
| **Checkpoint 管理** | checkpoint.json 崩溃恢复机制 | 数据库持久化 (13张表) | ★★★☆☆ | **中** - 两套状态管理方案可互补，WTR 适合轻量场景，MED 适合大数据量 |
| **品牌知识** | terminology_profiles.yaml + facts_db.yaml | brand_corpus/ + content_dna | ★★★☆☆ | **中** - WTR 术语表和 MED 品牌语料库可合并为统一品牌知识体系 |

### 3.3 低度关联区域 (独立领域/互不重叠)

| 关联领域 | AKO_writer | AKO_media_agent | 关联度 | 说明 |
|----------|-----------|-----------------|--------|------|
| **数据采集** | 无 | Layer 1: 7平台抓取/RSS/竞品/趋势 | ☆☆☆☆☆ | 完全不重叠，WTR 无采集需求 |
| **情感分析** | 无 | Layer 2: 三级情感分析引擎 | ☆☆☆☆☆ | WTR 无此需求 |
| **多平台发布** | 无 | Layer 4: 公众号/博客/小红书/抖音/LinkedIn | ☆☆☆☆☆ | WTR 只需输出本地文件 |
| **视觉生成** | 无 | AKO-ART-Agent 配图 | ☆☆☆☆☆ | WTR 的技术文档通常不含配图需求 |
| **反馈闭环** | 无 | Layer 5: 表现追踪/策略调整/异常回退 | ☆☆☆☆☆ | WTR 是单次写作任务，无持续追踪需求 |
| **进化模块** | 无 | 记忆/学习/涌现三层进化 | ☆☆☆☆☆ | WTR 尚未进入自适应阶段 |
| **小程序** | 无 | 内容同步/推荐/SEO | ☆☆☆☆☆ | WTR 无此场景 |

---

## 四、内容执行层深度对比

### 4.1 内容生成流程对比

| 阶段 | AKO_writer (WTR) | AKO_media_agent (MED) |
|------|-------------------|------------------------|
| **选题/触发** | N0: TopicCard 人工/Agent 触发 | Layer 3: ContentPlanner 5规则自动触发 (热点/竞品/常青/事件/政策) |
| **知识检索** | N1: AKO_knowledge (ChromaDB+bge-m3) + AKO_Hub KnowledgeHub 多源向量检索 | Layer 2: 无内部知识库检索，依赖公开数据采集形成 insights |
| **大纲/结构** | N2: LLM (Kimi→DeepSeek降级链) 生成结构化 Outline (chapters + figure/table/formula_plan) | Layer 3: TitleOptimizer 6大公式生成候选标题，无章节级大纲 |
| **正文撰写** | N3: 逐章 LLM 生成 (每章独立 Prompt，含大纲上下文+知识引用)，合并为 Markdown | Copywriter: 单次 LLM 生成品牌短文案 (标题+钩子+正文+互动钩子+标签) |
| **内容产出** | 技术长文 (5000字级，含图表公式计划) | 社交媒体短内容 (300-2000字，按平台) |
| **人工审核** | N0/N2 两处 confirm 节点 (approved/rejected+revisions) | 五级审核 (AI自审→初评→运营→终审→24h静默) |
| **输出形式** | 本地 .md 文件 (outline.md + article.md) | 数据库存储 + 多平台 API 发布 |
| **迭代机制** | 驳回后 N0/N2 重跑 (带 revisions 上下文) | 反馈闭环自动调整策略 (表现数据驱动) |

### 4.2 模板/提示词体系对比

| 维度 | AKO_writer (WTR) | AKO_media_agent (MED) |
|------|-------------------|------------------------|
| **提示词架构** | 函数内嵌 Prompt 模板 (STRUCTURE_PROMPT_TEMPLATE / CHAPTER_PROMPT_TEMPLATE) | JSON 结构化帖子模板 (`AKO_media_post_template_v1.0.json`) + 6栏目 Markdown 模板 (`templates/*.md`) |
| **结构约束** | 学术论文体例 (引言/文献/方法/结果/讨论/结论)，强制 figure/table/formula_plan | 五段式：标题(数字+标签+钩子) → 钩子句(价值重构) → 正文(4内容块) → 互动钩子(负面体验邀请) → 标签矩阵(6标签5维度) |
| **风格控制** | 术语档位 (standard/client_friendly/academic) + LLM_TEMPERATURE=0.3 | 品牌色系 (奶油金/深棕黑/琥珀金) + 语气指南 (do/don't) + style_consistency 阈值 80% |
| **篇幅控制** | target_length 参数 (如5000字) → 自动均分每章字数 | 分平台字数控 (公众号800-2000/小红书300-600/LinkedIn 200-500) |
| **质量检查** | 大纲校验 (必需字段补缺，plan至少1项)，重试2次+占位降级 | 质量自检清单 (8项) + 风格一致性 score + 思想厚度 score (4维度) |
| **知识注入** | N1 检索结果 (ResearchPack) 作为 Prompt 上下文，含来源标注 [1][2] | data_insights 参数透传，未深度集成到 Prompt |

### 4.3 质量审核机制对比

| 维度 | AKO_writer | AKO_media_agent |
|------|-----------|-----------------|
| **审核节点数** | 2处 (N0选题后 + N2大纲后) | 5级 (AI自审 → AI初评 → 运营初审 → 思想厚度终审 → 24h静默) |
| **自动审核** | 无 (仅人工 confirm) | Level 1 (风格一致性80分) + Level 2 (不可替代性60分) |
| **人工审核** | 技术 Owner (批准/驳回+修改意见) | Level 3 (品牌调性/合规) + Level 4 (品牌主理人思想厚度终审75分) |
| **驳回反馈** | revisions 字符串透传至下一轮 Prompt | 无内置驳回后自动重跑机制 |
| **发布门禁** | N2 批准后自动输出文件 | 思想厚度≥75分 + 24h静默期 + 红线规则5条 |
| **崩溃恢复** | checkpoint.json 落盘，进程重启后断点继续 | 数据库持久化，无状态机概念 |

### 4.4 内容分发对比

| 维度 | AKO_writer | AKO_media_agent |
|------|-----------|-----------------|
| **分发目标** | 本地文件系统 (output/{task_id}/outline.md + article.md) | 多平台 (公众号/博客/小红书/抖音/LinkedIn) + 小程序 |
| **自动发布** | N/A | 公众号 (微信桥接API) + 博客 (akobuild.cloud) |
| **半自动发布** | N/A | 小红书/抖音/LinkedIn (生成后人工确认发布) |
| **版本管理** | 无 (每次覆盖前次 checkpoint) | 版本化草稿存储 (每次修改保存新版本) |
| **内容撤回** | N/A | Publisher.withdraw_content() 支持 |
| **定时发布** | N/A | scheduler 定时任务 (公众号12:00、小程序14:00) |

### 4.5 执行层关键差异总结

| 差异点 | WTR 优势 | MED 优势 | 互补空间 |
|--------|---------|----------|----------|
| **内容深度** | 5000字级技术长文，学术体例 | 300-2000字品牌短文案，社交媒体体例 | WTR 生成深度长文 → MED 拆解为多平台短内容 |
| **知识驱动** | ChromaDB 向量检索 + 知识引用标注 | 热点/竞品/趋势数据驱动的选题洞察 | WTR 的知识检索能力注入 MED 技术栏目 |
| **LLM 鲁棒性** | Kimi→DeepSeek 降级链 + 重试2次 + 占位降级 | 仅 DeepSeek 单引擎，无降级 | MED 采纳 WTR/WFL 的降级链模式 |
| **审核精细度** | 简洁高效 (2节点) | 五级审核 + 思想厚度评分 + 红线规则 | WTR 可引入思想厚度评分作为发布门禁 |
| **分发能力** | 本地文件输出 | 多平台 API 自动/半自动发布 | MED 承接 WTR 产出进行多渠道分发 |

---

## 五、技术栈交叉对比

| 技术层 | AKO_writer | AKO_media_agent | AKO工作流 | 重叠度 |
|--------|-----------|-----------------|-----------|--------|
| 语言 | Python 3.11 | Python 3.9+ | Python 3.10+ | ✅ 三者相同 |
| 编排框架 | LangGraph >= 0.2 | 自研 main.py (CLI + 流水线) | LangGraph (StateGraph) | ⚠️ WTR和WFL相同 |
| 数据契约 | Pydantic >= 2.0 (InputContract/TopicCard/Outline) | YAML + 数据库 (无严格 Schema) | TypedDict (WorkflowState) | ❌ 三者不同 |
| AI 引擎 | Kimi + DeepSeek | DeepSeek | Kimi + DeepSeek + 通义千问 | ⚠️ 三者共享DeepSeek |
| 向量数据库 | ChromaDB (via AKO_knowledge) | 无 | 无 | ❌ WTR 独有 |
| 外部检索 | AKO_Hub KnowledgeHub | 无 | DuckDuckGo 搜索引擎 | ❌ WTR与WFL各有独立检索 |
| 数据库 | checkpoint.json 文件 | MySQL/SQLite (双引擎) | processed_files.json MD5追踪 | ❌ 无重叠 |
| 代理爬虫 | 无 | Playwright + MediaCrawler | 无 | ❌ MED 独有 |
| NLP 分词 | 无 | jieba / 阿里云NLP | 无 | ❌ MED 独有 |
| 文档生成 | 无 | 无 | python-docx (Word .docx) | ❌ WFL 独有 |
| 文件解析 | 无 | 无 | 6格式 (docx/pdf/pptx/xlsx/txt/md) | ❌ WFL 独有 |
| 三模型并发投票 | 无 | 无 | Kimi+DeepSeek+通义千问 质量评分 | ❌ WFL 独有 |

---

## 六、数据流与集成路径分析

### 6.1 潜在集成路径一：MED 触发 WTR

```
AKO_media_agent ContentPlanner (每日内容策略)
    ↓ 检测到技术深度选题 (0154技术谈栏目)
    ↓ 构造 InputContract → TopicCard
    ↓ 调用 WriterSpoke.create_task()
AKO_writer N0→N1→N2→N3 (生成技术长文)
    ↓ 输出 outline.md + 正文 .md
    ↓ 回传 AKO_media_agent
AKO_media_agent Copywriter + Publisher (适配后发布)
```

**可行性**: ★★★★★ — WTR 已暴露 `SpokeAdapter` 协议，`run()` 方法可直接被 Hub 或其他 Agent 调用。

### 6.2 潜在集成路径二 ⭐ 核心路径：WTR 技术文章 → WFL 多维论证

```
AKO_writer N3 完成 (生成技术长文 article.md)
    ↓
    将 article.md 写入 D:\AKO工作流\docs\待检索文件\
    ↓
AKO工作流 batch_processor 自动扫描新文件
    ↓ (基于 MD5 增量追踪，仅处理新文章)
Node 0: input_parser     → 解析文章内容，识别技术主题与类型
Node 1: retriever        → DuckDuckGo 搜索外部资料交叉验证
Node 2: technical        → Kimi 生成技术评审方案 (验证文章的技术准确性)
Node 3: business  (可选) → Kimi 评估商业可行性 (对造价说/0154技术谈尤为重要)
Node 4: reverse_check    → 对文章论点进行四维压力测试 (风险/成本/竞争/合规)
Node 5: quality          → 三模型并发投票评分 (≥0.8 合格)
Node 6: legal     (可选) → 通义千问 法律合规审查 (含合同/标准引用准确性)
Node 7: feasibility      → DeepSeek 综合可行性评估 (技术+经济+市场+环境)
Node 8: output           → 生成 Word 评定报告
    ↓
输出: docs/结论文件/WR-YYYY-MMDD-NNN_评定报告.docx
    ↓ 评定通过 (quality_score ≥ 0.8，feasibility 结论="可行")
    ↓ 回传评分与建议到 AKO_media_agent
AKO_media_agent 决策: 发布 / 需修改 / 驳回重写
```

**可行性**: ★★★★★ — 此路径具有极高可行性，理由如下：

| 维度 | 分析 |
|------|------|
| **输入兼容** | WFL 支持 .md 格式输入，WTR 的 article.md 无需任何转换即可被 file_parser 解析 |
| **自动化触发** | WFL 的 batch_processor.py 已实现目录扫描 + MD5增量追踪 + 无人值守模式 |
| **多维验证** | WFL 的 9节点管道覆盖技术准确性、商业可行性、法律合规、综合可行性——正是技术文章发布前最需要的论证维度 |
| **量化评分** | WFL 产出质量分数 (0-1)、可行性结论 ("可行"/"不可行")，可为 MED 提供客观的发布决策依据 |
| **人工介入可配** | WFL 支持交互模式 (逐文件确认) 和批量模式 (无人值守)，可根据栏目重要性选择 |
| **三模型权威性** | Kimi(长文本)+DeepSeek(逻辑)+通义千问(法律) 三模型并发投票，论证权威性远超单模型自检 |

**推荐触发策略**:

| 栏目 | 是否需要 WFL 论证 | 建议模式 | 理由 |
|------|-------------------|----------|------|
| **0154技术谈** | ✅ 必须 | 交互模式 | 技术标准引用需要严格交叉验证，三模型投票确保准确性 |
| **造价说** | ✅ 必须 | 交互模式 | 成本数据需要商业可行性验证，避免因价格信息错误引发纠纷 |
| **AKO建造志** | ⚠️ 可选 | 批量模式 | 侧重现场纪实，技术参数较少，可在批次中统一论证 |
| **黄昏建筑** | ❌ 不需要 | — | 建筑美学思考，不涉及技术数据验证 |
| **工地24时** | ❌ 不需要 | — | 施工现场纪实，不涉及技术论证 |
| **AKO人物** | ❌ 不需要 | — | 人物故事，不涉及技术论证 |

### 6.3 潜在集成路径三：WTR 复用 MED 内容模板

```
AKO_writer N2 大纲生成
    ↓ 使用现有的 STRUCTURE_PROMPT_TEMPLATE
    ↓ 扩展支持 MED 6大栏目的写作体例
    ↓ 引用 AKO_media_agent 的 templates/*.md 风格约束
    ↓ 生成更贴合品牌调性的技术内容
```

**可行性**: ★★★★☆ — 需扩展 WTR Prompt 模板体系，引入 MED 的品牌风格约束参数。

### 6.4 潜在集成路径四：共享 LLM 降级链

```
当前: MED Copywriter → DeepSeek 单引擎
建议: MED Copywriter → Kimi (主) → DeepSeek (降级) 
      复用 WTR/WFL 的 call_llm_with_fallback() 机制
```

**可行性**: ★★★★★ — WTR 和 WFL 都已实现多模型降级链 (均基于 OpenAI 兼容协议)，MED 可零成本合并。WFL 额外提供三模型并发投票可借鉴。

### 6.5 潜在集成路径五：统一知识体系

```
当前: WTR - terminology_profiles.yaml + facts_db.yaml (技术术语/规范锚定)
      MED - brand_corpus/ + content_dna/ (品牌语料/内容基因)
      WFL - prompts/*.txt 九节点专业 Prompt (技术/商业/法律/可行性)
建议: 合并为 AKO 统一知识库
      → WTR 写作时调用品牌约束
      → MED 生成技术内容时调用术语表
      → WFL 评定时引用品牌知识校验一致性
```

**可行性**: ★★★★☆ — 需建立统一的知识结构 Schema，AKO_Hub KMS 是天然载体。

---

## 七、核心差异总结

### 7.1 AKO_writer 的独特价值 (其他项目不覆盖)

1. **技术长文写作**: 结构化大纲→逐章正文，面向期刊论文/申报书/技术报告
2. **向量知识检索**: ChromaDB 语义搜索 + AKO_Hub 知识库查询
3. **状态机编排**: LangGraph 驱动的 N0→N1→N2→N3 确定性流水线
4. **崩溃恢复**: checkpoint.json 轻量级断点续传
5. **LLM 降级链**: Kimi→DeepSeek 超时自动 fallback
6. **术语绑定**: terminology_profiles.yaml 档位化术语表

### 7.2 AKO_media_agent 的独特价值 (其他项目不覆盖)

1. **全链路自动化**: 采集→分析→决策→执行→反馈 五层闭环
2. **多平台分发**: 7大社交媒体平台自动/半自动发布
3. **数据采集**: Playwright 浏览器自动化 + NewsMonitor + TrendDetector + CompetitorTracker
4. **NLP 分析**: 情感分析/主题聚类/关键词提取/互动预测/竞品缺口
5. **视觉生成**: AKO-ART-Agent 品牌配色锁定配图
6. **反馈优化**: 表现追踪→策略调整→异常回退持续进化
7. **进化模块**: 记忆层(基因/认知/失败)→学习层(模式/表现/反馈)→涌现层(创造/跨界)
8. **小程序生态**: 内容同步/推荐/SEO/表单触达

### 7.3 AKO工作流 的独特价值 (其他项目不覆盖)

1. **多维技术评定**: 技术方案 + 商业方案 + 法律合规 + 可行性研究 四维分析
2. **反向验证**: 对产出的技术方案进行风险/成本/竞争/合规四维度压力测试
3. **三模型并发投票**: Kimi + DeepSeek + 通义千问 独立评分取加权结果，消除单模型偏见
4. **自适应迭代**: 质量不达标自动回退检索重生成 (最多3次)，技术验证失败自循环修正
5. **多格式文件解析**: .docx/.pdf/.pptx/.xlsx/.txt/.md 六种格式文本提取
6. **Word 报告生成**: python-docx 自动生成结构化评定报告
7. **增量批次追踪**: MD5 哈希增量处理，仅处理新增/变更文件，支持断点续传
8. **外部搜索引擎**: DuckDuckGo 实时搜索补充资料交叉验证

---

## 八、关联度结论

| 评估维度 | 关联度 | 说明 |
|----------|--------|------|
| **功能互补性** | ⭐⭐⭐⭐⭐ (极高) | WTR写→WFL验→MED发，三项目形成"写→验→发"完整闭环 |
| **技术可复用性** | ⭐⭐⭐⭐⭐ (极高) | LLM调用、LangGraph编排、知识检索三者高度共享 |
| **流程可集成性** | ⭐⭐⭐⭐⭐ (极高) | WTR输出.md→WFL输入.md→MED发布，数据格式天然兼容 |
| **数据互通性** | ⭐⭐⭐⭐☆ (高) | 三者通过 AKO_Hub 知识库可建立统一数据层 |
| **用户重叠度** | ⭐⭐⭐☆☆ (中) | WTR+WFL 面向技术团队，MED 面向运营团队 |

### 总体关联度评估: **极高 (★★★★★)**

三个项目构成 AKO 内容体系的"**写 → 验 → 发**"三大核心环节：

```
AKO_writer     ──写──▶  技术长文生成  (知识驱动、结构化大纲、逐章撰写)
       │                        │
       │              article.md (技术文章初稿)
       │                        │
       │                        ▼
AKO工作流      ──验──▶  多维技术论证  (三模型投票、反向验证、可行性评估)
       │                        │
       │         {filename}_评定报告.docx  (含质量分数、可行性结论、优化建议)
       │                        │
       │                        ▼  (评定通过: score≥0.8, 结论="可行")
       │                        
AKO_media_agent ──发──▶  多平台分发    (文案适配、视觉配图、定时发布)
                                         │
                                         ▼
                                   反馈闭环  (表现追踪、策略调整、持续进化)
```

### 回答核心问题：WTR 生成的技术文章是否需要推送 WFL 进行论证？

**答案：必须。理由如下：**

1. **WTR 缺乏自我验证能力**: WTR 的审核只有 N0/N2 两处人工 confirm，无自动技术验证。LLM 生成的 5000 字技术文章可能存在事实性错误、数据幻觉、逻辑矛盾——WTR 自身无法检测这些。

2. **WFL 专为此场景设计**: WFL 的 9 节点管道天然覆盖技术文章需要的所有验证维度——技术准确性 (Node 2+4)、数据合理性 (Node 5 三模型投票)、商业可行性 (Node 3)、法律合规 (Node 6)、综合可行性 (Node 7)。三模型并发投票的权威性远超单模型自检。

3. **数据格式零摩擦**: WTR 输出 `.md` 文件，WFL 原生支持 `.md` 输入解析，无需任何格式转换。

4. **量化发布决策依据**: WFL 产出质量分数 (0-1) 和可行性结论，MED 可据此自动决策——分数≥0.8且可行→准备发布；分数<0.8→回退WTR重写。

### 建议优先推动的集成方向

| 优先级 | 集成方向 | 涉及项目 | 难度 | 价值 |
|--------|----------|----------|------|------|
| **P0** | **WTR article.md → WFL 论证 → MED 发布** (写→验→发闭环) | 三者 | 低 | 极高 |
| P1 | 共享 LLM 降级链 (MED 采纳 Kimi→DeepSeek) | WTR+MED | 低 | 高 |
| P2 | MED ContentPlanner → WTR 选题触发 | MED+WTR | 中 | 高 |
| P3 | WTR/MED/WFL 统一品牌知识体系 (AKO_Hub) | 三者 | 高 | 极高 |