"""
AI文案生成器
基于 AKO_media_post_template_v1.0 模板
结构：标题公式 + 价值重构句 + 短句正文 + 互动钩子 + 标签矩阵
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Copywriter:
    """
    AI文案生成器（基于 AKO 帖子模板 v1.0）

    功能:
    - 标题：数字锚定 + 身份标签 + 情绪钩子
    - 钩子句：不是[品类]，是让你从[旧状态]变成[新状态]
    - 正文：短句 + 换行 + 表情符号 + 四段式内容块
    - 互动钩子：负面体验邀请
    - 标签矩阵：6标签覆盖5维度
    """

    def __init__(self, config: dict):
        self.config = config
        execution_config = config.get("layers", {}).get("execution", {})
        writer_config = execution_config.get("copywriter", {})

        self.provider = writer_config.get("provider", "deepseek")
        self.style_control = writer_config.get("style_control", {})
        self.platforms_config = writer_config.get("platforms", {})

        # 加载帖子模板
        self.template = self._load_template()

        # 风格控制参数
        self.corpus_min_samples = self.style_control.get("corpus_min_samples", 100)
        self.consistency_threshold = self.style_control.get("consistency_threshold", 80)

        # 平台适配参数
        self.platform_specs = {
            "wechat": {"word_count": "800-2000", "style": "深度+故事"},
            "xiaohongshu": {"word_count": "300-600", "style": "口语+种草"},
            "douyin": {"duration": "15-60秒", "style": "短句+节奏"},
            "linkedin": {"word_count": "200-500词", "style": "专业+数据", "language": "en"},
            "blog": {"word_count": "1500-3000", "style": "SEO+深度"},
        }

        logger.info(f"Copywriter 初始化完成，提供商: {self.provider}，模板: {self.template.get('template_name', 'v1.0')}")

    def _load_template(self) -> dict:
        """加载帖子模板 JSON"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config", "AKO_media_post_template_v1.0.json"
        )
        if os.path.exists(template_path):
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                logger.info(f"加载帖子模板成功: {template_path}")
                return template
            except Exception as e:
                logger.error(f"加载帖子模板失败: {e}")
        return {}

    def generate_article(self, topic: str, column: str, platform: str,
                         data_insights: Dict = None) -> Dict:
        """
        生成文章

        Args:
            topic: 选题
            column: 栏目名称
            platform: 目标平台
            data_insights: 数据洞察

        Returns:
            生成的文章
        """
        # 构建提示词
        prompt = self._build_prompt(topic, column, platform, data_insights)

        # 调用大模型生成
        result = self._call_llm(prompt)

        article = {
            "article_id": f"AKO_media_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": result.get("title", f"{topic}"),
            "body": result.get("body", ""),
            "platform": platform,
            "column": column,
            "word_count": len(result.get("body", "")),
            "style_score": 0.0,
            "thought_depth_score": 0.0,
            "generated_at": datetime.now().isoformat(),
        }

        # 风格一致性检查
        article["style_score"] = self._check_style_consistency(article)

        # 思想厚度预评
        article["thought_depth_score"] = self._evaluate_thought_depth(article)

        return article

    def _call_llm(self, prompt: str) -> Dict:
        """调用 LLM API 生成内容"""
        api_key = os.environ.get("LLM_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
        base_url = os.environ.get("LLM_BASE_URL") or os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        model = os.environ.get("LLM_MODEL") or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

        if not api_key:
            logger.warning("未配置 LLM API Key，返回占位内容")
            return {"title": "[未配置API Key]", "body": "请先在 secrets.env 中配置 LLM_API_KEY 或 DEEPSEEK_API_KEY"}

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)

            # 构建基于模板的 system prompt
            system_content = self._build_system_prompt()

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7,
            )

            content = response.choices[0].message.content.strip()
            logger.info(f"LLM 生成内容成功，长度: {len(content)}")

            # 解析标题和正文
            lines = content.split("\n")
            title = ""
            body_lines = []
            for line in lines:
                if not title and line.startswith("#"):
                    title = line.lstrip("#").strip()
                elif not title and line.strip():
                    title = line.strip()[:50]
                else:
                    body_lines.append(line)

            return {
                "title": title or "AKO内容",
                "body": "\n".join(body_lines).strip(),
            }

        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return {"title": "[生成失败]", "body": f"LLM 调用异常: {str(e)}"}

    def _build_system_prompt(self) -> str:
        """基于帖子模板构建 system prompt"""
        t = self.template
        structure = t.get("structure", {})
        tone = t.get("tone_guide", {})
        checklist = t.get("quality_checklist", [])

        title_rule = structure.get("title", {})
        hook_rule = structure.get("hook_line", {})
        body_rule = structure.get("body", {})
        interaction_rule = structure.get("interaction_hook", {})
        tag_rule = structure.get("tag_matrix", {})

        prompt = f"""你是AKO（阿格建筑）的品牌内容创作者，严格按照以下模板创作：

## 标题规则
- 公式：{title_rule.get('formula', '数字锚定 + 身份标签 + 情绪钩子')}
- 约束：{'; '.join(title_rule.get('constraints', []))}
- 示例：{'; '.join(title_rule.get('examples', [])[:2])}

## 钩子句（价值重构）
- 公式：{hook_rule.get('formula', '不是[品类]，是让你从[旧状态]变成[新状态]')}
- 语气：{hook_rule.get('tone', '赋能感，拒绝说教，给读者尊严感')}

## 正文格式
- 每行不超过{body_rule.get('format', {}).get('max_line_length', 15)}字
- {body_rule.get('format', {}).get('line_break', '每1-2句换行')}
- {body_rule.get('format', {}).get('emoji_usage', '每3-4行一个表情符号')}
- 表情池：{' '.join(body_rule.get('format', {}).get('emoji_pool', []))}
- 内容块顺序：{' → '.join(b.get('block_name', '') for b in body_rule.get('content_blocks', []))}

## 互动钩子
- {interaction_rule.get('formula', '评论区聊聊：[场景] + [负面体验邀请]')}
- 心理：{interaction_rule.get('psychology', '吐槽 > 分享成功')}

## 标签矩阵
- {tag_rule.get('rule', '6个标签覆盖5个维度')}
- 维度：{', '.join(f'{k}={v}' for k, v in tag_rule.get('dimensions', {}).items())}

## 语气指南
- 要做：{'; '.join(tone.get('do', []))}
- 不要：{'; '.join(tone.get('dont', []))}

## 质量自检清单
{chr(10).join(f'- {item}' for item in checklist)}

请严格按模板结构输出，确保每条内容只有AKO能发。"""
        return prompt

    def _build_prompt(self, topic: str, column: str, platform: str,
                      data_insights: Dict = None) -> str:
        """构建生成提示词"""
        spec = self.platform_specs.get(platform, {})
        structure = self.template.get("structure", {})
        tag_dims = structure.get("tag_matrix", {}).get("dimensions", {})

        prompt = f"""
请为AKO（阿格建筑）创作{platform}平台内容。

## 栏目: {column}
## 选题: {topic}
## 字数: {spec.get('word_count', '300-800')}
## 风格: {spec.get('style', '深度+数据')}

## 输出格式要求
1. 标题（25字以内，数字锚定+身份标签+情绪钩子）
2. 钩子句（不是...是...的价值重构句）
3. 正文（短句换行，每行不超15字，加表情符号，包含：权威背书→场景痛点→解决方案→情绪升华）
4. 互动钩子（评论区聊聊：邀请负面体验）
5. 标签（6个，覆盖产品/品类/技术/场景/地域/品牌维度）

## 标签维度参考
- 产品: {tag_dims.get('product', 'AKObuild')}
- 品类: {tag_dims.get('category', '装配式建筑')}
- 技术: {tag_dims.get('tech', '陶粒发泡')}
- 场景: {tag_dims.get('scene', '住宅建筑')}
- 地域: {tag_dims.get('region', '贵州建筑')}
- 品牌: {tag_dims.get('brand', '#AKObuild')}

请严格按模板结构输出。"""
        return prompt

    def _check_style_consistency(self, article: Dict) -> float:
        """检查风格一致性"""
        # TODO: 与品牌语料库对比，计算一致性分数
        return 85.0  # 模拟分数

    def _evaluate_thought_depth(self, article: Dict) -> float:
        """
        评估思想厚度评分

        维度:
        - 不可替代性 (40%)
        - 具体性 (30%)
        - 时间诚实 (15%)
        - 人的在场 (15%)
        """
        # TODO: 实际评估逻辑
        return 70.0  # 模拟分数

    def adapt_for_platform(self, article: Dict, target_platform: str) -> Dict:
        """
        将文章适配到不同平台

        Args:
            article: 原始文章
            target_platform: 目标平台

        Returns:
            适配后的文章
        """
        adapted = article.copy()
        adapted["platform"] = target_platform

        spec = self.platform_specs.get(target_platform, {})

        # TODO: 根据平台特点调整内容
        # - 公众号: 深度展开
        # - 小红书: 口语化、加标签
        # - 抖音: 脚本化、短句
        # - LinkedIn: 专业化、英文
        # - 博客: SEO优化

        return adapted

    def generate_multi_platform(self, topic: str, column: str,
                                platforms: List[str]) -> List[Dict]:
        """
        为多平台生成内容变体

        Args:
            topic: 选题
            column: 栏目
            platforms: 目标平台列表

        Returns:
            各平台内容列表
        """
        results = []
        base_article = self.generate_article(topic, column, platforms[0])

        for platform in platforms:
            if platform == platforms[0]:
                results.append(base_article)
            else:
                adapted = self.adapt_for_platform(base_article, platform)
                results.append(adapted)

        return results
