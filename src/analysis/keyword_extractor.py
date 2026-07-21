"""
关键词提取器
TF-IDF + TextRank
"""

import logging
from typing import List, Dict, Optional

import jieba
import jieba.analyse

from src.database import get_db

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """
    关键词提取器

    功能:
    - TF-IDF关键词提取
    - TextRank关键词提取
    - 高频词云生成
    - SEO优化建议
    """

    def __init__(self, config: dict):
        self.config = config
        analysis_config = config.get("layers", {}).get("analysis", {})
        keyword_config = analysis_config.get("keyword_extractor", {})

        self.methods = keyword_config.get("methods", ["tfidf", "textrank"])
        self.top_n = keyword_config.get("top_n", 50)
        self.db = get_db()

        logger.info(f"KeywordExtractor 初始化完成，方法: {self.methods}")

    def extract_keywords(self, text: str = None, method: str = "tfidf") -> List[Dict]:
        """
        提取关键词

        Args:
            text: 待提取文本
            method: 提取方法 (tfidf | textrank)

        Returns:
            关键词列表 [{"word": "xxx", "weight": 0.5}, ...]
        """
        if text is None:
            text = self._get_recent_content()

        if method == "tfidf":
            return self._extract_tfidf(text)
        elif method == "textrank":
            return self._extract_textrank(text)
        else:
            logger.warning(f"未知方法: {method}，使用tfidf")
            return self._extract_tfidf(text)

    def _extract_tfidf(self, text: str) -> List[Dict]:
        """TF-IDF关键词提取"""
        keywords = jieba.analyse.extract_tags(text, topK=self.top_n, withWeight=True)
        return [{"word": w, "weight": s} for w, s in keywords]

    def _extract_textrank(self, text: str) -> List[Dict]:
        """TextRank关键词提取"""
        keywords = jieba.analyse.textrank(text, topK=self.top_n, withWeight=True)
        return [{"word": w, "weight": s} for w, s in keywords]

    def _get_recent_content(self, hours: int = 24) -> str:
        """获取最近内容"""
        sql = """
        SELECT GROUP_CONCAT(content SEPARATOR ' ') as combined_content
        FROM crawled_data
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        """
        result = self.db.fetch_one(sql, (hours,))
        return result["combined_content"] if result and result["combined_content"] else ""

    def generate_word_cloud_data(self, days: int = 7) -> Dict:
        """
        生成词云数据

        Args:
            days: 统计天数

        Returns:
            词云数据
        """
        sql = """
        SELECT content FROM crawled_data
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        results = self.db.fetch_all(sql, (days,))

        all_text = " ".join([r["content"] for r in results if r["content"]])
        words = jieba.cut(all_text)

        # 统计词频
        word_freq = {}
        for word in words:
            if len(word) >= 2:  # 过滤单字
                word_freq[word] = word_freq.get(word, 0) + 1

        # 排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:100]
        return dict(sorted_words)

    def get_seo_suggestions(self, target_keyword: str) -> Dict:
        """
        获取SEO优化建议

        Args:
            target_keyword: 目标关键词

        Returns:
            SEO建议
        """
        # TODO: 分析关键词密度、长尾词等
        return {
            "keyword": target_keyword,
            "suggestions": [
                "建议在标题中包含关键词",
                "建议在首段前100字出现关键词",
                "建议添加相关长尾关键词",
            ],
            "related_words": [],
        }
