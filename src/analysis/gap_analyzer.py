"""
竞品缺口分析
对比矩阵 + 内容缺口识别
"""

import logging
from typing import List, Dict, Optional

from src.database import get_db

logger = logging.getLogger(__name__)


class GapAnalyzer:
    """
    竞品缺口分析器

    功能:
    - 竞品覆盖度 vs AKO覆盖度热力图
    - 机会点清单
    - 差异化建议
    """

    def __init__(self, config: dict):
        self.config = config
        self.db = get_db()

        # 内容主题维度
        self.topics = [
            "产品发布", "项目案例", "技术文章", "品牌故事",
            "行业活动", "用户反馈", "政策解读", "造价分析",
        ]

        logger.info("GapAnalyzer 初始化完成")

    def analyze_gaps(self) -> Dict:
        """
        分析竞品内容缺口

        Returns:
            缺口分析结果
        """
        # 获取竞品内容分布
        competitor_coverage = self._get_competitor_coverage()

        # 获取AKO内容分布
        ako_coverage = self._get_ako_coverage()

        # 识别缺口
        gaps = self._identify_gaps(competitor_coverage, ako_coverage)

        return {
            "competitor_coverage": competitor_coverage,
            "ako_coverage": ako_coverage,
            "gaps": gaps,
            "opportunities": self._generate_opportunities(gaps),
        }

    def _get_competitor_coverage(self) -> Dict:
        """获取竞品内容覆盖度"""
        if self.db.engine == "sqlite":
            sql = """
            SELECT content_theme, COUNT(*) as count
            FROM competitor_data
            WHERE publish_date >= datetime('now', '-90 days')
            GROUP BY content_theme
            """
        else:
            sql = """
            SELECT content_theme, COUNT(*) as count
            FROM competitor_data
            WHERE publish_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
            GROUP BY content_theme
            """
        results = self.db.fetch_all(sql)
        return {r.get("content_theme", "unknown"): r.get("count", 0) for r in results if r.get("content_theme")}

    def _get_ako_coverage(self) -> Dict:
        """获取AKO内容覆盖度"""
        if self.db.engine == "sqlite":
            sql = """
            SELECT column_name, COUNT(*) as count
            FROM content
            WHERE created_at >= datetime('now', '-90 days')
            AND status = 'published'
            GROUP BY column_name
            """
        else:
            sql = """
            SELECT column_name, COUNT(*) as count
            FROM content
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)
            AND status = 'published'
            GROUP BY column_name
            """
        results = self.db.fetch_all(sql)
        return {r.get("column_name", "unknown"): r.get("count", 0) for r in results if r.get("column_name")}

    def _identify_gaps(self, competitor_coverage: Dict, ako_coverage: Dict) -> List[Dict]:
        """识别内容缺口"""
        gaps = []

        # 竞品覆盖但AKO未覆盖的领域
        for topic, count in competitor_coverage.items():
            ako_count = ako_coverage.get(topic, 0)
            if ako_count < count * 0.5:  # AKO覆盖不足竞品50%
                gaps.append({
                    "topic": topic,
                    "competitor_count": count,
                    "ako_count": ako_count,
                    "gap_level": "high" if ako_count == 0 else "medium",
                })

        return sorted(gaps, key=lambda x: x["competitor_count"], reverse=True)

    def _generate_opportunities(self, gaps: List[Dict]) -> List[Dict]:
        """生成机会点建议"""
        opportunities = []

        for gap in gaps:
            if gap["gap_level"] == "high":
                opportunities.append({
                    "topic": gap["topic"],
                    "priority": "high",
                    "suggestion": f"竞品在'{gap['topic']}'领域有{gap['competitor_count']}篇内容，AKO尚未覆盖，建议优先布局",
                    "action": "立即规划相关内容",
                })
            elif gap["gap_level"] == "medium":
                opportunities.append({
                    "topic": gap["topic"],
                    "priority": "medium",
                    "suggestion": f"AKO在'{gap['topic']}'领域内容量不足竞品，建议加强",
                    "action": "纳入下月内容计划",
                })

        return opportunities

    def get_heatmap_data(self) -> Dict:
        """获取热力图数据"""
        analysis = self.analyze_gaps()
        return {
            "topics": self.topics,
            "competitor_data": analysis["competitor_coverage"],
            "ako_data": analysis["ako_coverage"],
        }
