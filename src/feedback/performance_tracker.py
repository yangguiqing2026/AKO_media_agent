"""
表现追踪器
多维度指标 + 周报/月报生成
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import get_db

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    表现追踪器

    功能:
    - 多维度指标追踪（阅读/点赞/评论/转发/收藏/完读率/粉丝增长/转化率）
    - 周报生成
    - 月报生成
    """

    def __init__(self, config: dict):
        self.config = config
        feedback_config = config.get("layers", {}).get("feedback", {})
        tracker_config = feedback_config.get("performance_tracker", {})
        self.metrics = tracker_config.get("metrics", [
            "reads", "likes", "comments", "shares",
            "favorites", "completion_rate", "follower_growth",
            "conversion_rate", "mini_program_stats",
        ])
        self.db = get_db()
        logger.info("PerformanceTracker 初始化完成")

    def track_performance(self, article_id: str, platform: str, metrics: Dict):
        """
        记录表现数据

        Args:
            article_id: 文章ID
            platform: 平台
            metrics: 指标数据
        """
        sql = """
        INSERT INTO performance_data 
        (article_id, platform, reads, likes, comments, shares, 
         favorites, completion_rate, negative_ratio)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            article_id, platform,
            metrics.get("reads", 0),
            metrics.get("likes", 0),
            metrics.get("comments", 0),
            metrics.get("shares", 0),
            metrics.get("favorites", 0),
            metrics.get("completion_rate", 0.0),
            metrics.get("negative_ratio", 0.0),
        )
        self.db.execute(sql, params)

    def generate_weekly_report(self) -> Dict:
        """生成周报"""
        logger.info("生成周报...")

        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        # 汇总数据
        sql = """
        SELECT 
            platform,
            COUNT(DISTINCT article_id) as articles_count,
            SUM(reads) as total_reads,
            SUM(likes) as total_likes,
            SUM(comments) as total_comments,
            SUM(shares) as total_shares,
            AVG(completion_rate) as avg_completion_rate
        FROM performance_data
        WHERE recorded_at >= %s
        GROUP BY platform
        """
        results = self.db.fetch_all(sql, (week_ago,))

        report = {
            "type": "weekly",
            "period": f"{week_ago} ~ {datetime.now().strftime('%Y-%m-%d')}",
            "platforms": {},
            "generated_at": datetime.now().isoformat(),
        }

        for r in results:
            report["platforms"][r["platform"]] = {
                "articles": r["articles_count"],
                "reads": r["total_reads"],
                "likes": r["total_likes"],
                "comments": r["total_comments"],
                "shares": r["total_shares"],
                "avg_completion_rate": r["avg_completion_rate"],
            }

        logger.info(f"周报生成完成: {len(results)} 个平台")
        return report

    def generate_monthly_report(self) -> Dict:
        """生成月报"""
        logger.info("生成月报...")

        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        sql = """
        SELECT 
            platform,
            COUNT(DISTINCT article_id) as articles_count,
            SUM(reads) as total_reads,
            SUM(likes) as total_likes,
            SUM(comments) as total_comments,
            SUM(shares) as total_shares,
            AVG(completion_rate) as avg_completion_rate,
            AVG(negative_ratio) as avg_negative_ratio
        FROM performance_data
        WHERE recorded_at >= %s
        GROUP BY platform
        """
        results = self.db.fetch_all(sql, (month_ago,))

        report = {
            "type": "monthly",
            "period": f"{month_ago} ~ {datetime.now().strftime('%Y-%m-%d')}",
            "platforms": {},
            "generated_at": datetime.now().isoformat(),
        }

        for r in results:
            report["platforms"][r["platform"]] = {
                "articles": r["articles_count"],
                "reads": r["total_reads"],
                "likes": r["total_likes"],
                "comments": r["total_comments"],
                "shares": r["total_shares"],
                "avg_completion_rate": r["avg_completion_rate"],
                "avg_negative_ratio": r["avg_negative_ratio"],
            }

        logger.info(f"月报生成完成: {len(results)} 个平台")
        return report

    def get_top_contents(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """获取表现最好的内容"""
        sql = """
        SELECT article_id, platform, reads, likes, comments, shares
        FROM performance_data
        WHERE recorded_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        ORDER BY (reads + likes * 5 + comments * 10 + shares * 15) DESC
        LIMIT %s
        """
        return self.db.fetch_all(sql, (days, limit))
