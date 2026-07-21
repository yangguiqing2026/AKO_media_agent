"""
策略调整器
自动+人工决策：降权/加权/时间微调
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.database import get_db

logger = logging.getLogger(__name__)


class StrategyAdjuster:
    """
    策略调整器

    功能:
    - 低表现内容类型自动降权
    - 高表现内容类型自动加权
    - 发布时间自动微调
    - 策略调整记录
    """

    def __init__(self, config: dict):
        self.config = config
        feedback_config = config.get("layers", {}).get("feedback", {})
        adjuster_config = feedback_config.get("strategy_adjuster", {})

        self.auto_adjust = adjuster_config.get("auto_adjust", True)
        self.adjust_dimensions = adjuster_config.get("adjust_dimensions", [
            "content_type_weight",
            "publish_timing",
            "keyword_priority",
        ])
        self.db = get_db()

        logger.info("StrategyAdjuster 初始化完成")

    def adjust_strategy(self):
        """执行策略调整"""
        logger.info("开始策略调整...")

        # 分析各内容类型表现
        type_performance = self._analyze_type_performance()

        # 生成调整建议
        adjustments = self._generate_adjustments(type_performance)

        # 执行自动调整
        if self.auto_adjust:
            for adj in adjustments:
                self._apply_adjustment(adj)

        return adjustments

    def _analyze_type_performance(self) -> Dict:
        """分析各内容类型表现"""
        sql = """
        SELECT c.column_name, 
               AVG(p.reads) as avg_reads,
               AVG(p.likes) as avg_likes,
               AVG(p.comments) as avg_comments,
               COUNT(*) as sample_count
        FROM content c
        JOIN performance_data p ON c.article_id = p.article_id
        WHERE c.published_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY c.column_name
        """
        results = self.db.fetch_all(sql)
        return {r["column_name"]: dict(r) for r in results}

    def _generate_adjustments(self, type_performance: Dict) -> List[Dict]:
        """生成调整建议"""
        adjustments = []

        if not type_performance:
            return adjustments

        # 计算平均表现
        avg_reads = sum(t.get("avg_reads", 0) for t in type_performance.values()) / len(type_performance)

        for col_name, perf in type_performance.items():
            if perf["avg_reads"] < avg_reads * 0.5:
                # 低表现，建议降权
                adjustments.append({
                    "type": "weight_down",
                    "dimension": "content_type_weight",
                    "target": col_name,
                    "reason": f"近30天平均阅读量({perf['avg_reads']:.0f})低于均值50%",
                    "auto": True,
                })
            elif perf["avg_reads"] > avg_reads * 1.5:
                # 高表现，建议加权
                adjustments.append({
                    "type": "weight_up",
                    "dimension": "content_type_weight",
                    "target": col_name,
                    "reason": f"近30天平均阅读量({perf['avg_reads']:.0f})高于均值50%",
                    "auto": True,
                })

        return adjustments

    def _apply_adjustment(self, adjustment: Dict):
        """应用调整"""
        sql = """
        INSERT INTO strategy_adjustments 
        (adjustment_type, dimension, old_value, new_value, reason, auto_adjusted)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
            adjustment["type"],
            adjustment["dimension"],
            "{}",  # old_value
            "{}",  # new_value
            adjustment["reason"],
            adjustment.get("auto", False),
        )
        self.db.execute(sql, params)
        logger.info(f"策略调整已记录: {adjustment['type']} -> {adjustment['target']}")

    def get_adjustment_history(self, days: int = 30) -> List[Dict]:
        """获取调整历史"""
        sql = """
        SELECT * FROM strategy_adjustments
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        ORDER BY created_at DESC
        """
        return self.db.fetch_all(sql, (days,))
