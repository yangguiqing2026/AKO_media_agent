"""
主题聚类器
BERTopic + LDA 主题模型
"""

import logging
from collections import Counter
from typing import List, Dict, Optional, Tuple

import jieba
import numpy as np

from src.database import get_db

logger = logging.getLogger(__name__)

# 停用词表
STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
    "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
    "自己", "这", "他", "她", "它", "们", "那", "些", "什么", "怎么", "如何", "为什么",
    "吗", "呢", "吧", "啊", "呀", "哦", "嗯", "哈", "嘿", "嗨", "喂", "噢",
}


class TopicCluster:
    """
    主题聚类器

    功能:
    - 自动聚类热门话题
    - 话题关联度图谱
    - 内容缺口发现
    """

    def __init__(self, config: dict):
        self.config = config
        analysis_config = config.get("layers", {}).get("analysis", {})
        topic_config = analysis_config.get("topic_cluster", {})
        self.db = get_db()

        self.method = topic_config.get("method", "tfidf_kmeans")
        self.min_topics = topic_config.get("min_topics", 5)
        self.max_topics = topic_config.get("max_topics", 30)

        # 尝试导入BERTopic
        self._bertopic_available = False
        try:
            from bertopic import BERTopic
            self._bertopic_available = True
            logger.info("BERTopic可用，使用BERTopic聚类")
        except ImportError:
            logger.info("BERTopic未安装，使用TF-IDF+KMeans聚类")

        logger.info(f"TopicCluster 初始化完成，方法: {self.method}")

    def cluster_topics(self, texts: List[str] = None) -> List[Dict]:
        """
        对文本进行主题聚类

        Args:
            texts: 文本列表

        Returns:
            聚类结果
        """
        if texts is None:
            texts = self._get_recent_texts()

        if not texts or len(texts) < 3:
            logger.warning("文本数量不足，无法聚类")
            return []

        # 分词处理
        tokenized_texts = [self._tokenize(text) for text in texts]
        
        # 过滤太短的文本
        valid_indices = [i for i, t in enumerate(tokenized_texts) if len(t) >= 5]
        if len(valid_indices) < 3:
            logger.warning("有效文本数量不足")
            return []
        
        valid_texts = [tokenized_texts[i] for i in valid_indices]
        valid_originals = [texts[i] for i in valid_indices]

        # 选择聚类方法
        if self._bertopic_available:
            return self._cluster_with_bertopic(valid_originals)
        else:
            return self._cluster_with_tfidf_kmeans(valid_texts, valid_originals)

    def _tokenize(self, text: str) -> str:
        """分词并去除停用词"""
        words = jieba.cut(text)
        return " ".join(w for w in words if w not in STOP_WORDS and len(w) > 1)

    def _get_recent_texts(self, limit: int = 200) -> List[str]:
        """从数据库获取最近采集的文本"""
        if self.db.engine == "sqlite":
            sql = """
            SELECT title, content FROM crawled_data
            WHERE content IS NOT NULL AND content != ''
            ORDER BY created_at DESC LIMIT ?
            """
        else:
            sql = """
            SELECT title, content FROM crawled_data
            WHERE content IS NOT NULL AND content != ''
            ORDER BY created_at DESC LIMIT %s
            """
        
        results = self.db.fetch_all(sql, (limit,))
        texts = []
        for row in results:
            title = row.get("title", "")
            content = row.get("content", "")
            texts.append(f"{title} {content}"[:500])
        return texts

    def _cluster_with_bertopic(self, texts: List[str]) -> List[Dict]:
        """使用BERTopic进行聚类"""
        try:
            from bertopic import BERTopic
            
            topic_model = BERTopic(
                language="chinese (simplified)",
                min_topic_size=3,
                nr_topics="auto",
            )
            
            topics, probs = topic_model.fit_transform(texts)
            
            # 整理结果
            topic_info = topic_model.get_topic_info()
            results = []
            
            for _, row in topic_info.iterrows():
                topic_id = row["Topic"]
                if topic_id == -1:  # 异常主题
                    continue
                    
                topic_words = topic_model.get_topic(topic_id)
                results.append({
                    "topic_id": topic_id,
                    "name": row.get("Name", f"topic_{topic_id}"),
                    "keywords": [w[0] for w in topic_words[:10]],
                    "count": int((np.array(topics) == topic_id).sum()),
                    "representative_docs": [
                        texts[i] for i, t in enumerate(topics) 
                        if t == topic_id
                    ][:3],
                })
            
            logger.info(f"BERTopic聚类完成，发现 {len(results)} 个主题")
            return results
            
        except Exception as e:
            logger.error(f"BERTopic聚类失败: {e}，回退到TF-IDF+KMeans")
            tokenized = [self._tokenize(t) for t in texts]
            return self._cluster_with_tfidf_kmeans(tokenized, texts)

    def _cluster_with_tfidf_kmeans(self, tokenized_texts: List[str], 
                                     original_texts: List[str]) -> List[Dict]:
        """使用TF-IDF + KMeans进行聚类"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.cluster import KMeans
            
            # TF-IDF向量化
            vectorizer = TfidfVectorizer(
                max_features=1000,
                max_df=0.95,
                min_df=2,
            )
            
            tfidf_matrix = vectorizer.fit_transform(tokenized_texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # 确定聚类数
            n_samples = len(tokenized_texts)
            n_clusters = min(self.max_topics, max(self.min_topics, n_samples // 10))
            n_clusters = min(n_clusters, n_samples - 1)  # 不能超过样本数
            
            if n_clusters < 2:
                logger.warning("样本数量不足，无法聚类")
                return []
            
            # KMeans聚类
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            kmeans.fit(tfidf_matrix)
            
            # 整理结果
            results = []
            for topic_id in range(n_clusters):
                # 获取该主题的关键词（按TF-IDF权重排序）
                center = kmeans.cluster_centers_[topic_id]
                top_indices = center.argsort()[-10:][::-1]
                keywords = [feature_names[i] for i in top_indices]
                
                # 获取该主题的文档
                doc_indices = [i for i, label in enumerate(kmeans.labels_) if label == topic_id]
                
                results.append({
                    "topic_id": topic_id,
                    "name": f"topic_{topic_id}",
                    "keywords": keywords,
                    "count": len(doc_indices),
                    "representative_docs": [original_texts[i] for i in doc_indices[:3]],
                })
            
            # 按文档数排序
            results.sort(key=lambda x: x["count"], reverse=True)
            
            logger.info(f"TF-IDF+KMeans聚类完成，发现 {len(results)} 个主题")
            return results
            
        except Exception as e:
            logger.error(f"TF-IDF+KMeans聚类失败: {e}")
            return []

    def get_topic_distribution(self) -> Dict:
        """获取主题分布"""
        # 从数据库查询并分析
        if self.db.engine == "sqlite":
            sql = """
            SELECT content_type, COUNT(*) as count
            FROM crawled_data
            GROUP BY content_type
            """
        else:
            sql = """
            SELECT content_type, COUNT(*) as count
            FROM crawled_data
            GROUP BY content_type
            """
        
        results = self.db.fetch_all(sql)
        return {row.get("content_type", "unknown"): row.get("count", 0) for row in results}

    def find_content_gaps(self) -> List[Dict]:
        """
        发现内容缺口

        Returns:
            内容缺口列表（热度高但AKO未覆盖的话题）
        """
        # 获取热门话题
        hot_topics = self.cluster_topics()
        
        # 获取AKO已发布内容
        if self.db.engine == "sqlite":
            sql = """
            SELECT content FROM crawled_data
            WHERE author LIKE '%AKO%' OR author LIKE '%阿格%'
            LIMIT 100
            """
        else:
            sql = """
            SELECT content FROM crawled_data
            WHERE author LIKE '%AKO%' OR author LIKE '%阿格%'
            LIMIT 100
            """
        
        ako_content = self.db.fetch_all(sql)
        ako_texts = " ".join(row.get("content", "") for row in ako_content)
        
        # 对比发现缺口
        gaps = []
        for topic in hot_topics:
            keywords = topic.get("keywords", [])
            # 检查AKO内容是否包含这些关键词
            coverage = sum(1 for kw in keywords if kw in ako_texts)
            coverage_ratio = coverage / len(keywords) if keywords else 0
            
            if coverage_ratio < 0.3 and topic.get("count", 0) >= 5:
                gaps.append({
                    "topic": topic.get("name"),
                    "keywords": keywords,
                    "hot_count": topic.get("count"),
                    "coverage": coverage_ratio,
                    "suggestion": f"建议创作关于 {', '.join(keywords[:3])} 的内容",
                })
        
        # 按热度排序
        gaps.sort(key=lambda x: x["hot_count"], reverse=True)
        
        logger.info(f"发现 {len(gaps)} 个内容缺口")
        return gaps
