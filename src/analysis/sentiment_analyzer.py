"""
情感分析引擎
阿里云NLP API + 危机预警
"""

import json
import logging
import os
from typing import List, Dict, Optional

import jieba

from src.database import get_db

logger = logging.getLogger(__name__)

# 情感词典（简化版，实际可加载更大词典）
POSITIVE_WORDS = {
    "好", "棒", "优秀", "赞", "喜欢", "推荐", "值得", "不错", "精彩",
    "创新", "突破", "领先", "专业", "高质量", "可靠", "安全", "舒适",
    "绿色", "环保", "节能", "智能", "高效", "便捷", "美观", "经济",
    "实惠", "耐用", "稳定", "快速", "先进", "独特", "卓越", "完美",
}

NEGATIVE_WORDS = {
    "差", "烂", "垃圾", "失败", "问题", "危险", "不安全", "劣质",
    "投诉", "举报", "违规", "违法", "污染", "浪费", "昂贵", "低效",
    "落后", "传统", "过时", "缺陷", "故障", "风险", "隐患", "崩溃",
    "糟糕", "失望", "后悔", "被骗", "虚假", "夸大", "误导",
}


class SentimentAnalyzer:
    """
    情感分析引擎

    功能:
    - 阿里云NLP API情感分析
    - 品牌声誉监控
    - 竞品口碑分析
    - 危机预警
    """

    def __init__(self, config: dict):
        self.config = config
        analysis_config = config.get("layers", {}).get("analysis", {})
        self.sentiment_config = analysis_config.get("sentiment", {})
        self.db = get_db()

        # 危机预警配置
        crisis_config = self.sentiment_config.get("crisis_alert", {})
        self.negative_ratio_threshold = crisis_config.get("negative_ratio_threshold", 0.30)
        self.negative_count_threshold = crisis_config.get("negative_count_threshold", 10)
        self.alert_channels = crisis_config.get("alert_channels", ["email"])
        self.recipients = crisis_config.get("recipients", ["admin@akobuild.cloud"])

        # 品牌关键词
        self.brand_keywords = ["AKO", "阿格建筑", "akobuild", "阿格装配式"]

        # 阿里云NLP配置
        self.nlp_provider = os.getenv("NLP_PROVIDER", "jieba")
        self.aliyun_nlp_key = os.getenv("ALIYUN_NLP_KEY", "")
        self.aliyun_nlp_url = os.getenv("ALIYUN_NLP_URL", "https://nlp-api.aliyuncs.com/api")

        # LLM配置（备用）
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
        self.llm_model = os.getenv("LLM_MODEL", "deepseek-chat")

        logger.info(f"SentimentAnalyzer 初始化完成，NLP引擎: {self.nlp_provider}")

    def analyze_sentiment(self, text: str) -> Dict:
        """
        分析单条文本情感

        Args:
            text: 待分析文本

        Returns:
            情感分析结果
        """
        if not text:
            return {"label": "neutral", "score": 0.5, "confidence": 0.0}

        # 根据配置选择NLP引擎
        if self.nlp_provider == "aliyun" and self.aliyun_nlp_key:
            return self._analyze_with_aliyun(text)
        elif self.nlp_provider == "llm" and self.llm_api_key:
            return self._analyze_with_llm(text)
        else:
            return self._analyze_with_jieba(text)

    def _analyze_with_jieba(self, text: str) -> Dict:
        """
        使用jieba分词进行情感分析（规则基线）
        """
        words = list(jieba.cut(text))
        
        positive_count = 0
        negative_count = 0
        
        for word in words:
            if word in POSITIVE_WORDS:
                positive_count += 1
            elif word in NEGATIVE_WORDS:
                negative_count += 1
        
        total = positive_count + negative_count
        if total == 0:
            return {"label": "neutral", "score": 0.5, "confidence": 0.6}
        
        positive_ratio = positive_count / total
        negative_ratio = negative_count / total
        
        if positive_ratio > 0.7:
            label = "positive"
            score = positive_ratio
        elif negative_ratio > 0.7:
            label = "negative"
            score = negative_ratio
        elif abs(positive_ratio - negative_ratio) < 0.2:
            label = "controversial"
            score = 0.5
        else:
            label = "neutral"
            score = max(positive_ratio, negative_ratio)
        
        return {
            "label": label,
            "score": round(score, 3),
            "confidence": min(0.9, 0.5 + total * 0.05),
            "positive_count": positive_count,
            "negative_count": negative_count,
        }

    def _analyze_with_aliyun(self, text: str) -> Dict:
        """
        使用阿里云NLP API进行情感分析
        """
        import requests
        
        try:
            headers = {
                "Authorization": f"Bearer {self.aliyun_nlp_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "service": "alinlp",
                "api": "sentiment",
                "text": text[:500],
            }
            
            resp = requests.post(
                self.aliyun_nlp_url,
                headers=headers,
                json=payload,
                timeout=5
            )
            
            data = resp.json()
            if data.get("code") == 200:
                result = data.get("data", {})
                return {
                    "label": result.get("sentiment", "neutral"),
                    "score": result.get("score", 0.5),
                    "confidence": result.get("confidence", 0.8),
                    "provider": "aliyun",
                }
        except Exception as e:
            logger.warning(f"阿里云NLP调用失败: {e}，回退到jieba")
        
        return self._analyze_with_jieba(text)

    def _analyze_with_llm(self, text: str) -> Dict:
        """
        使用大模型进行情感分析（更准确）
        """
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.llm_api_key,
                base_url=self.llm_base_url,
            )
            
            prompt = f"""请分析以下文本的情感倾向，返回JSON格式：
{{"label": "positive/negative/neutral/controversial", "score": 0.0-1.0, "confidence": 0.0-1.0}}

文本：{text[:500]}

分析结果："""
            
            response = client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "你是情感分析专家，擅长分析社交媒体内容的情感倾向。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.1,
            )
            
            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)
            result["provider"] = "llm"
            return result
            
        except Exception as e:
            logger.warning(f"LLM情感分析失败: {e}，回退到jieba")
        
        return self._analyze_with_jieba(text)

    def analyze_batch(self, texts: List[str] = None) -> List[Dict]:
        """
        批量分析情感

        Args:
            texts: 文本列表，若不传则从数据库读取最新数据

        Returns:
            分析结果列表
        """
        if texts is None:
            texts = self._get_recent_texts()

        results = []
        for text in texts:
            result = self.analyze_sentiment(text)
            results.append(result)

        # 检查危机预警
        self._check_crisis_alert(results)

        return results

    def _get_recent_texts(self, hours: int = 24) -> List[str]:
        """获取最近采集的文本"""
        sql = """
        SELECT content FROM crawled_data
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        AND content IS NOT NULL AND content != ''
        LIMIT 100
        """
        results = self.db.fetch_all(sql, (hours,))
        return [r.get("content", "") for r in results if r.get("content")]

    def _check_crisis_alert(self, results: List[Dict]):
        """检查是否触发危机预警"""
        if not results:
            return

        negative_count = sum(1 for r in results if r.get("label") == "negative")
        negative_ratio = negative_count / len(results)

        # 触发条件
        if (negative_ratio >= self.negative_ratio_threshold or
                negative_count >= self.negative_count_threshold):
            self._send_crisis_alert(negative_ratio, negative_count)

    def _send_crisis_alert(self, negative_ratio: float, negative_count: int):
        """发送危机预警"""
        # TODO: 实现邮件/短信告警
        logger.warning(
            f"[危机预警] 负面比例: {negative_ratio:.2%}, "
            f"负面数量: {negative_count}, "
            f"阈值: {self.negative_ratio_threshold:.2%}/{self.negative_count_threshold}"
        )

    def analyze_brand_sentiment(self) -> Dict:
        """分析品牌情感分布"""
        # 查询包含品牌关键词的内容
        results = {"total_mentions": 0, "positive": 0, "negative": 0, "neutral": 0, "controversial": 0}
        
        for keyword in self.brand_keywords:
            if self.db.engine == "sqlite":
                sql = "SELECT content FROM crawled_data WHERE content LIKE ? LIMIT 50"
            else:
                sql = "SELECT content FROM crawled_data WHERE content LIKE %s LIMIT 50"
            
            data = self.db.fetch_all(sql, (f"%{keyword}%",))
            
            for row in data:
                content = row.get("content", "")
                if content:
                    sentiment = self.analyze_sentiment(content)
                    label = sentiment.get("label", "neutral")
                    results[label] = results.get(label, 0) + 1
                    results["total_mentions"] += 1
        
        return results
