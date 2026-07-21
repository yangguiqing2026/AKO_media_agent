"""
互动预测模型
规则基线 (Phase 1) -> 轻量ML (Phase 2) -> 时序模型 (Phase 3)
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class EngagementPredictor:
    """
    互动预测模型

    功能:
    - Phase 1: 规则基线预测
    - Phase 2: 轻量ML (线性回归/随机森林)
    - Phase 3: 时序模型 (ARIMA/LSTM)

    注意: 预测结果仅内部参考，不对外宣称
    """

    def __init__(self, config: dict):
        self.config = config
        analysis_config = config.get("layers", {}).get("analysis", {})
        predictor_config = analysis_config.get("engagement_predictor", {})

        self.phase = predictor_config.get("phase", 1)
        self.base_rates = predictor_config.get("base_rates", {
            "wechat": 0.05,
            "xiaohongshu": 0.10,
            "douyin": 0.15,
            "linkedin": 0.08,
            "blog": 0.03,
        })

        # 时段系数
        self.hour_coefficients = {
            8: 0.6, 9: 0.7, 10: 0.8, 11: 0.9, 12: 1.2,
            13: 1.1, 14: 1.0, 15: 0.9, 16: 0.8, 17: 0.9,
            18: 1.3, 19: 1.5, 20: 1.4, 21: 1.2, 22: 1.0,
        }

        logger.info(f"EngagementPredictor 初始化完成，Phase: {self.phase}")

    def predict(self, followers: int, title_score: float,
                publish_hour: int, platform: str) -> Dict:
        """
        预测互动数据

        Args:
            followers: 粉丝数
            title_score: 标题质量分 (0-1)
            publish_hour: 发布时间 (0-23)
            platform: 平台标识

        Returns:
            预测结果 {"reads": int, "likes": int, "comments": int}
        """
        if self.phase == 1:
            return self._predict_rule_based(followers, title_score, publish_hour, platform)
        elif self.phase == 2:
            # TODO: 实现轻量ML预测
            return self._predict_rule_based(followers, title_score, publish_hour, platform)
        elif self.phase == 3:
            # TODO: 实现时序模型预测
            return self._predict_rule_based(followers, title_score, publish_hour, platform)
        else:
            return self._predict_rule_based(followers, title_score, publish_hour, platform)

    def _predict_rule_based(self, followers: int, title_score: float,
                            publish_hour: int, platform: str) -> Dict:
        """
        规则基线预测 (Phase 1)

        公式: predicted_reads = followers * base_rate * title_score * hour_coefficient
        """
        base_rate = self.base_rates.get(platform, 0.05)
        hour_coeff = self.hour_coefficients.get(publish_hour, 1.0)

        predicted_reads = int(followers * base_rate * title_score * hour_coeff)
        predicted_likes = int(predicted_reads * 0.08)      # 点赞率约8%
        predicted_comments = int(predicted_reads * 0.015)  # 评论率约1.5%

        return {
            "reads": predicted_reads,
            "likes": predicted_likes,
            "comments": predicted_comments,
            "phase": self.phase,
            "confidence": 0.6 if self.phase == 1 else 0.7 if self.phase == 2 else 0.75,
        }

    def calculate_title_score(self, title: str) -> float:
        """
        计算标题质量分

        Args:
            title: 标题文本

        Returns:
            标题质量分 (0-1)
        """
        score = 0.5  # 基础分

        # 长度评分
        length = len(title)
        if 15 <= length <= 30:
            score += 0.2
        elif 10 <= length <= 40:
            score += 0.1

        # 数字加分
        if any(c.isdigit() for c in title):
            score += 0.1

        # 情感词加分
        emotional_words = ["为什么", "如何", "揭秘", "真相", "秘密", "惊人"]
        if any(w in title for w in emotional_words):
            score += 0.1

        return min(1.0, score)
