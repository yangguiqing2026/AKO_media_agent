"""
异常回退管理器
检测+告警+撤回+原因分析
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional

from src.database import get_db

logger = logging.getLogger(__name__)


class RollbackManager:
    """
    异常回退管理器

    功能:
    - 异常检测（负面评论>50%、阅读量<预估20%、平台下架、用户投诉）
    - 邮件告警
    - 一键撤回
    - 原因分析
    - 反馈至策略调整器
    """

    def __init__(self, config: dict):
        self.config = config
        feedback_config = config.get("layers", {}).get("feedback", {})
        rollback_config = feedback_config.get("rollback", {})

        self.triggers = rollback_config.get("triggers", {
            "negative_comment_ratio": 0.50,
            "read_below_prediction_ratio": 0.20,
            "platform_removal": True,
            "user_complaint": True,
        })
        self.alert_channels = rollback_config.get("alert_channels", ["email"])
        self.alert_recipients = rollback_config.get("alert_recipients", ["admin@akobuild.cloud"])
        self.db = get_db()

        logger.info("RollbackManager 初始化完成")

    def check_anomalies(self):
        """检查所有异常"""
        logger.info("开始异常检测...")

        anomalies = []

        # 检查负面评论比例
        negative_anomalies = self._check_negative_comments()
        anomalies.extend(negative_anomalies)

        # 检查阅读量异常
        read_anomalies = self._check_read_anomalies()
        anomalies.extend(read_anomalies)

        # 处理异常
        for anomaly in anomalies:
            self._handle_anomaly(anomaly)

        if anomalies:
            logger.warning(f"检测到 {len(anomalies)} 个异常")
        else:
            logger.info("未发现异常")

        return anomalies

    def _check_negative_comments(self) -> List[Dict]:
        """检查负面评论比例异常"""
        sql = """
        SELECT article_id, platform, negative_ratio
        FROM performance_data
        WHERE recorded_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        AND negative_ratio > %s
        """
        threshold = self.triggers.get("negative_comment_ratio", 0.50)
        results = self.db.fetch_all(sql, (threshold,))

        anomalies = []
        for r in results:
            anomalies.append({
                "type": "negative_comments",
                "article_id": r["article_id"],
                "platform": r["platform"],
                "value": r["negative_ratio"],
                "threshold": threshold,
                "severity": "high",
            })

        return anomalies

    def _check_read_anomalies(self) -> List[Dict]:
        """检查阅读量异常"""
        sql = """
        SELECT p.article_id, p.platform, p.reads,
               c.predicted_engagement
        FROM performance_data p
        JOIN content c ON p.article_id = c.article_id
        WHERE p.recorded_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        AND c.predicted_engagement IS NOT NULL
        """
        results = self.db.fetch_all(sql)

        anomalies = []
        for r in results:
            try:
                predicted = json.loads(r["predicted_engagement"]) if isinstance(r["predicted_engagement"], str) else r["predicted_engagement"]
                predicted_reads = predicted.get("reads", 0)
                if predicted_reads > 0 and r["reads"] < predicted_reads * 0.2:
                    anomalies.append({
                        "type": "low_reads",
                        "article_id": r["article_id"],
                        "platform": r["platform"],
                        "actual": r["reads"],
                        "predicted": predicted_reads,
                        "ratio": r["reads"] / predicted_reads,
                        "severity": "medium",
                    })
            except (json.JSONDecodeError, TypeError):
                pass

        return anomalies

    def _handle_anomaly(self, anomaly: Dict):
        """处理异常"""
        # 发送告警
        self._send_alert(anomaly)

        # 记录异常
        logger.warning(f"异常: {anomaly['type']} - {anomaly['article_id']}")

    def _send_alert(self, anomaly: Dict):
        """发送告警"""
        # TODO: 实现邮件/短信告警
        logger.warning(
            f"[异常告警] 类型: {anomaly['type']}, "
            f"文章: {anomaly['article_id']}, "
            f"严重度: {anomaly['severity']}"
        )

    def rollback_content(self, article_id: str, reason: str) -> Dict:
        """
        撤回内容

        Args:
            article_id: 文章ID
            reason: 撤回原因

        Returns:
            撤回结果
        """
        logger.warning(f"撤回内容: {article_id}, 原因: {reason}")

        # 更新内容状态
        sql = "UPDATE content SET status = 'withdrawn' WHERE article_id = %s"
        self.db.execute(sql, (article_id,))

        # 记录撤回
        sql = """
        INSERT INTO publish_record (article_id, platform, status, error_message)
        VALUES (%s, 'all', 'withdrawn', %s)
        """
        self.db.execute(sql, (article_id, reason))

        return {
            "success": True,
            "article_id": article_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        }

    def analyze_rollback_reason(self, article_id: str) -> Dict:
        """分析撤回原因"""
        # TODO: 分析撤回原因并反馈至策略调整器
        return {
            "article_id": article_id,
            "analysis": "待实现",
            "feedback": {},
        }
