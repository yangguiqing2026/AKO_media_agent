"""用户反馈语义学习 - 从评论中提取语义洞察"""

import json
import logging
from datetime import datetime
from typing import Dict, List

import jieba

from src.database import get_db

logger = logging.getLogger(__name__)


class FeedbackSemanticLearning:
    """
    用户反馈语义学习器

    不是统计评论数，是理解评论在说什么
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.db = get_db()

        # 语义分类关键词
        self.semantic_patterns = {
            "praise_technical": ["专业", "详细", "参数", "技术", "数据"],
            "praise_emotional": ["温度", "感动", "真实", "诚实", "不像广告"],
            "praise_personal": ["故事", "人物", "老周", "师傅", "人"],
            "confusion": ["什么意思", "不太懂", "怎么", "真的吗", "是全包"],
            "unmet_need": ["想看", "想知道", "能不能", "希望", "期待"],
            "trust_signal": ["相信", "靠谱", "放心", "推荐", "值得"],
        }

        logger.info("FeedbackSemanticLearning 初始化完成")

    def learn(self, comments: List[str]) -> Dict:
        """
        从评论列表中提取语义洞察

        Args:
            comments: 评论文本列表

        Returns:
            语义洞察结果
        """
        if not comments:
            return {"status": "no_comments"}

        results = {
            "analyzed_at": datetime.now().isoformat(),
            "total_comments": len(comments),
            "praise_types": {"technical": 0, "emotional": 0, "personal": 0},
            "confusion_points": [],
            "unmet_needs": [],
            "language_patterns": [],
            "trust_signals": 0,
        }

        for comment in comments:
            words = list(jieba.cut(comment))

            # 分类赞美类型
            if any(w in comment for w in self.semantic_patterns["praise_technical"]):
                results["praise_types"]["technical"] += 1
            if any(w in comment for w in self.semantic_patterns["praise_emotional"]):
                results["praise_types"]["emotional"] += 1
            if any(w in comment for w in self.semantic_patterns["praise_personal"]):
                results["praise_types"]["personal"] += 1

            # 提取困惑点
            if any(w in comment for w in self.semantic_patterns["confusion"]):
                results["confusion_points"].append(comment[:100])

            # 提取未满足需求
            if any(w in comment for w in self.semantic_patterns["unmet_need"]):
                results["unmet_needs"].append(comment[:100])

            # 统计信任信号
            if any(w in comment for w in self.semantic_patterns["trust_signal"]):
                results["trust_signals"] += 1

        # 保存学习成果
        self._save_learning(results)
        logger.info(f"语义学习完成，分析 {len(comments)} 条评论")
        return results

    def _save_learning(self, results: Dict):
        """保存学习成果"""
        if self.db.engine == "sqlite":
            placeholders = ", ".join(["?" for _ in range(2)])
        else:
            placeholders = ", ".join(["%s" for _ in range(2)])

        sql = f"""
        INSERT INTO evolution_insights (insight_data, created_at)
        VALUES ({placeholders})
        """
        params = (json.dumps({"type": "feedback_learning", **results}, ensure_ascii=False),
                  datetime.now().isoformat())
        self.db.execute(sql, params)
