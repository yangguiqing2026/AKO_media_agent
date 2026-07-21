"""竞品策略模式学习 - 理解竞品为什么发，而不只是发了什么"""

import json
import logging
from datetime import datetime
from typing import Dict, List

from src.database import get_db

logger = logging.getLogger(__name__)


class CompetitorPatternLearning:
    """竞品策略模式学习器"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.db = get_db()

        self.competitor_strategies = {}
        self.industry_gaps = {}
        self.opportunities = {}

        logger.info("CompetitorPatternLearning 初始化完成")

    def learn(self, competitor_data: List[Dict]) -> Dict:
        """从竞品数据中提取策略模式"""
        if not competitor_data:
            return {"status": "no_data"}

        patterns = {
            "analyzed_at": datetime.now().isoformat(),
            "total_records": len(competitor_data),
            "content_strategies": {},
            "gaps": {"none_talk_about": [], "all_avoid": [], "overused": []},
            "opportunities": {"differentiation": [], "timing": []},
        }

        # 按竞品统计内容主题分布
        theme_counts = {}
        for item in competitor_data:
            name = item.get("competitor_name", "unknown")
            theme = item.get("content_theme", "unknown")
            if name not in theme_counts:
                theme_counts[name] = {}
            theme_counts[name][theme] = theme_counts[name].get(theme, 0) + 1

        # 识别策略路线
        for name, themes in theme_counts.items():
            dominant_theme = max(themes, key=themes.get) if themes else "unknown"
            patterns["content_strategies"][name] = {
                "dominant_theme": dominant_theme,
                "theme_distribution": themes,
                "total_content": sum(themes.values()),
            }

        # 识别行业空白
        all_themes = set()
        for themes in theme_counts.values():
            all_themes.update(themes.keys())

        # 大家都避开的主题 = 机会
        rare_themes = [t for t in all_themes if sum(1 for tc in theme_counts.values() if t in tc) <= 1]
        patterns["gaps"]["none_talk_about"] = rare_themes

        # 过度使用的主题
        common_themes = [t for t in all_themes if sum(1 for tc in theme_counts.values() if t in tc) >= 3]
        patterns["gaps"]["overused"] = common_themes

        # AKO的差异化机会
        patterns["opportunities"]["differentiation"] = [
            "人的在场、建造现场的真实",
            "具体造价透明化",
            "失败案例诚实分享",
        ]

        self._save_learning(patterns)
        logger.info(f"竞品策略学习完成，分析 {len(competitor_data)} 条数据")
        return patterns

    def _save_learning(self, patterns: Dict):
        if self.db.engine == "sqlite":
            placeholders = ", ".join(["?" for _ in range(2)])
        else:
            placeholders = ", ".join(["%s" for _ in range(2)])
        sql = f"INSERT INTO evolution_insights (insight_data, created_at) VALUES ({placeholders})"
        params = (json.dumps({"type": "competitor_learning", **patterns}, ensure_ascii=False),
                  datetime.now().isoformat())
        self.db.execute(sql, params)
