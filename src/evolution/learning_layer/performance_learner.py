"""
表现数据深度学习
从表现数据中提取深层规律，理解"为什么表现好/差"
"""

import json
import logging
from datetime import datetime
from typing import Dict, List

from src.database import get_db

logger = logging.getLogger(__name__)


class PerformanceDeepLearning:
    """
    表现数据深度学习器

    不只是统计"这篇打开率高"
    而是理解"为什么这篇打开率高"
    并提炼可迁移的知识
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.db = get_db()
        self.learned_rules = []
        logger.info("PerformanceDeepLearning 初始化完成")

    def analyze(self, content_dna: Dict, performance: Dict) -> Dict:
        """
        深度分析表现背后的原因

        Args:
            content_dna: 内容DNA
            performance: 表现数据

        Returns:
            深层洞察
        """
        genes = content_dna.get("genes", {})
        structure = genes.get("structure", {})
        style = genes.get("style", {})
        thought = genes.get("thought", {})

        reads = performance.get("reads", 0)
        likes = performance.get("likes", 0)
        comments = performance.get("comments", 0)
        shares = performance.get("shares", 0)

        engagement_rate = (likes + comments + shares) / max(reads, 1)
        insights = {
            "analyzed_at": datetime.now().isoformat(),
            "engagement_rate": round(engagement_rate, 4),
            "surface_patterns": [],
            "deep_patterns": [],
            "causal_chains": [],
            "transferable_knowledge": [],
        }

        # 表层模式识别
        if structure.get("has_numbers") and engagement_rate > 0.05:
            insights["surface_patterns"].append("标题含数字的内容互动率高")
            insights["deep_patterns"].append("数字产生信任感，降低认知负担")
            insights["causal_chains"].append("具体数字 → 减少认知负担 → 快速建立信任 → 高互动")
            insights["transferable_knowledge"].append("在所有栏目中都适用：用数字代替形容词")

        if style.get("person_in_scene") and engagement_rate > 0.05:
            insights["surface_patterns"].append("有真实人物的内容互动率高")
            insights["deep_patterns"].append("人的在场产生共情和真实感")
            insights["causal_chains"].append("真实人物 → 读者产生共情 → 信任内容真实性 → 愿意分享")
            insights["transferable_knowledge"].append("技术内容也应加入操作者的视角")

        if thought.get("specificity_score", 0) > 60 and shares > 0:
            insights["surface_patterns"].append("高具体性内容转发率高")
            insights["deep_patterns"].append("具体数据让读者觉得'有价值，值得收藏'")
            insights["causal_chains"].append("具体数据 → 感知价值高 → 转发给需要的人")
            insights["transferable_knowledge"].append("造价说栏目的核心优势就是具体性")

        if style.get("forbidden_count", 0) > 3 and engagement_rate < 0.02:
            insights["surface_patterns"].append("空洞词汇多的内容互动率低")
            insights["deep_patterns"].append("抽象概念让读者产生距离感")
            insights["causal_chains"].append("空洞词汇 → 读者无法产生身体感知 → 快速划走")
            insights["transferable_knowledge"].append("每出现一个抽象词，必须配一个具体数字或场景")

        # 保存学习成果
        if insights["deep_patterns"]:
            self.learned_rules.extend(insights["deep_patterns"])
            self._save_insights(insights)

        return insights

    def get_learned_rules(self) -> List[str]:
        """获取已学习的规律"""
        return list(set(self.learned_rules))

    def _save_insights(self, insights: Dict):
        """保存洞察"""
        if self.db.engine == "sqlite":
            placeholders = ", ".join(["?" for _ in range(2)])
        else:
            placeholders = ", ".join(["%s" for _ in range(2)])

        sql = f"""
        INSERT INTO evolution_insights (insight_data, created_at)
        VALUES ({placeholders})
        """
        params = (json.dumps(insights, ensure_ascii=False), datetime.now().isoformat())
        self.db.execute(sql, params)
