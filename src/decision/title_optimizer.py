"""
标题优化器
基于 AKO_media_post_template_v1.0：数字锚定 + 身份标签 + 情绪钩子
"""

import json
import logging
import os
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class TitleOptimizer:
    """
    标题优化器（基于帖子模板 v1.0）

    功能:
    - 模板标题公式：数字锚定 + 身份标签 + 情绪钩子
    - 6大补充公式库
    - 标题约束检查（25字以内、无空泛词）
    - 生成3个备选标题
    """

    def __init__(self, config: dict):
        self.config = config
        decision_config = config.get("layers", {}).get("decision", {})
        title_config = decision_config.get("title_optimizer", {})

        self.formulas = title_config.get("formulas", [
            "数字锚定", "身份标签", "情绪钩子",
            "时间切片", "技术真相", "失败档案",
        ])
        self.candidates_per_article = title_config.get("candidates_per_article", 3)

        # 加载帖子模板
        self.template = self._load_template()
        template_title = self.template.get("structure", {}).get("title", {})
        self.title_rule = template_title.get("rule", "数字锚定 + 身份标签 + 情绪钩子")
        self.title_formula = template_title.get("formula", "[数字权威] [产品定位] [身份锁定]")
        self.title_constraints = template_title.get("constraints", [])
        self.title_examples = template_title.get("examples", [])

        # 标题公式模板
        self.title_templates = {
            "数字锚定": {
                "pattern": "真实可验证数字 + 产品定位 + 身份锁定",
                "examples": self.title_examples or [
                    "46dB隔声实测，AKO墙板不是普通隔墙，建筑师必看",
                    "138kg/m²面密度，AKO模块化建筑重新定义住宅承重标准",
                ],
            },
            "身份标签": {
                "pattern": "目标人群 + 具体场景 + 价值承诺",
                "examples": [
                    "T/CECS 10154-2021认证，AKO陶粒墙板让开发商告别开裂焦虑",
                    "建筑师必看：AKO墙板的46dB隔声是怎么做到的",
                ],
            },
            "情绪钩子": {
                "pattern": "情绪触发 + 具体数字 + 行动邀请",
                "examples": [
                    "告别开裂焦虑，AKO墙板用数据说话",
                    "别再被空泛词骗了，这块墙板46dB实测",
                ],
            },
            "时间切片": {
                "pattern": "时间 + 地点 + 具体动作",
                "examples": [
                    "6:17，贵阳，吊车还没醒，但老周已经在了",
                    "下午三点，第12块墙板到位",
                ],
            },
            "技术真相": {
                "pattern": "标准号 + 行业不愿说的事",
                "examples": [
                    "T/CECS 10154：为什么很多墙板通不过",
                    "120mm墙板厚度背后的计算过程",
                ],
            },
            "失败档案": {
                "pattern": "时间 + 失败 + 学到的事",
                "examples": [
                    "2024年3月，那批墙板返工了",
                    "那次吊装，我们犯了个错误",
                ],
            },
        }

        logger.info(f"TitleOptimizer 初始化完成，模板规则: {self.title_rule}，公式库: {self.formulas}")

    def _load_template(self) -> dict:
        """加载帖子模板 JSON"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config", "AKO_media_post_template_v1.0.json"
        )
        if os.path.exists(template_path):
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载帖子模板失败: {e}")
        return {}

    def optimize_titles(self, content_plan: Dict) -> List[Dict]:
        """
        为内容计划优化标题

        Args:
            content_plan: 内容计划

        Returns:
            标题优化结果
        """
        tasks = content_plan.get("tasks", [])
        results = []

        for task in tasks:
            topic = task.get("topic", "")
            candidates = self.generate_candidates(topic)
            results.append({
                "task": task,
                "candidates": candidates,
                "recommended": candidates[0] if candidates else None,
            })

        return results

    def generate_candidates(self, topic: str) -> List[Dict]:
        """
        生成备选标题

        Args:
            topic: 主题/选题

        Returns:
            备选标题列表
        """
        candidates = []

        for formula in self.formulas[:self.candidates_per_article]:
            template = self.title_templates.get(formula, {})
            # TODO: 使用大模型基于模板生成标题
            candidate = {
                "formula": formula,
                "pattern": template.get("pattern", ""),
                "title": f"[待生成] {topic}",
                "score": 0.0,
            }
            candidates.append(candidate)

        # 评分排序
        candidates = self._score_candidates(candidates)

        return candidates

    def _score_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """
        对候选标题评分

        Args:
            candidates: 候选标题列表

        Returns:
            评分后的候选标题（按分数降序）
        """
        for c in candidates:
            score = 0.5  # 基础分

            # 长度评分（模板约束：25字以内）
            title_len = len(c.get("title", ""))
            if 10 <= title_len <= 25:
                score += 0.2

            # 模板公式加分（数字锚定/身份标签/情绪钩子优先）
            if c.get("formula") in ["数字锚定", "身份标签", "情绪钩子"]:
                score += 0.15

            # 约束检查加分
            if title_len <= 25:
                score += 0.05
            banned_words = ['重大突破', '行业领先', '遥遥领先', '颠覆行业', '众所周知']
            if not any(w in c.get("title", "") for w in banned_words):
                score += 0.05

            c["score"] = min(1.0, score)

        return sorted(candidates, key=lambda x: x["score"], reverse=True)

    def get_formula_examples(self, formula: str = None) -> Dict:
        """获取公式示例"""
        if formula:
            return {formula: self.title_templates.get(formula, {})}
        return self.title_templates
