"""
竞品追踪器模块
人工标注 + 定时录入
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Optional

from src.database import get_db

logger = logging.getLogger(__name__)


class CompetitorTracker:
    """
    竞品追踪器

    功能:
    - 竞品数据录入接口
    - 爆款内容识别
    - 竞品动态汇总
    """

    def __init__(self, config: dict):
        self.config = config
        self.crawler_config = config.get("layers", {}).get("crawler", {})
        self.tracker_config = self.crawler_config.get("competitor_tracker", {})
        self.db = get_db()

        # 追踪对象
        self.competitors = self.tracker_config.get("competitors", [
            {"name": "远大住工", "platforms": ["wechat", "website"]},
            {"name": "中民筑友", "platforms": ["wechat", "douyin"]},
            {"name": "美好置业", "platforms": ["wechat", "xiaohongshu"]},
            {"name": "三一筑工", "platforms": ["wechat", "website"]},
        ])

        logger.info(f"CompetitorTracker 初始化完成，追踪 {len(self.competitors)} 个竞品")

    def record_competitor_content(self, competitor_name: str, platform: str,
                                   content_title: str, content_url: str,
                                   publish_date: date, content_theme: str,
                                   likes: int = 0, comments: int = 0,
                                   shares: int = 0, notes: str = ""):
        """
        录入竞品内容数据

        Args:
            competitor_name: 竞品名称
            platform: 平台
            content_title: 内容标题
            content_url: 内容链接
            publish_date: 发布日期
            content_theme: 内容主题
            likes: 点赞数
            comments: 评论数
            shares: 转发数
            notes: 备注
        """
        # 计算平均互动量，判断是否爆款
        avg_engagement = self._get_avg_engagement(competitor_name, platform)
        total_engagement = likes + comments + shares
        is_viral = total_engagement > avg_engagement * 3

        sql = """
        INSERT INTO competitor_data 
        (competitor_name, platform, content_title, content_url, publish_date,
         content_theme, likes, comments, shares, is_viral, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            competitor_name, platform, content_title, content_url,
            publish_date, content_theme, likes, comments, shares,
            is_viral, notes
        )
        self.db.execute(sql, params)

        if is_viral:
            logger.warning(f"[竞品爆款] {competitor_name}: {content_title}")

    def _get_avg_engagement(self, competitor_name: str, platform: str) -> float:
        """获取平均互动量"""
        sql = """
        SELECT AVG(likes + comments + shares) as avg_engagement
        FROM competitor_data
        WHERE competitor_name = %s AND platform = %s
        AND publish_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
        """
        result = self.db.fetch_one(sql, (competitor_name, platform))
        return result["avg_engagement"] if result and result["avg_engagement"] else 100

    def get_viral_contents(self, days: int = 7) -> List[Dict]:
        """获取近期竞品爆款"""
        sql = """
        SELECT * FROM competitor_data
        WHERE is_viral = TRUE
        AND recorded_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        ORDER BY (likes + comments + shares) DESC
        """
        return self.db.fetch_all(sql, (days,))

    def get_competitor_summary(self, competitor_name: str) -> Dict:
        """获取竞品汇总数据"""
        sql = """
        SELECT 
            COUNT(*) as total_contents,
            AVG(likes) as avg_likes,
            AVG(comments) as avg_comments,
            AVG(shares) as avg_shares,
            SUM(CASE WHEN is_viral THEN 1 ELSE 0 END) as viral_count
        FROM competitor_data
        WHERE competitor_name = %s
        AND publish_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """
        return self.db.fetch_one(sql, (competitor_name,))

    def remind_entry(self):
        """发送录入提醒"""
        logger.info("竞品数据录入提醒：请在本周五下午完成本周竞品数据录入")
        # TODO: 发送邮件提醒
