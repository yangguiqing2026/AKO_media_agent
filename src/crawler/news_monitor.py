"""
行业新闻监控模块
RSS订阅 + 大模型摘要
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional

import feedparser

from src.database import get_db

logger = logging.getLogger(__name__)


class NewsMonitor:
    """
    行业新闻监控器

    功能:
    - RSS订阅源监控
    - 大模型摘要生成
    - 政策变动检测
    - 自动告警
    """

    def __init__(self, config: dict):
        self.config = config
        self.crawler_config = config.get("layers", {}).get("crawler", {})
        self.news_config = self.crawler_config.get("news_monitor", {})
        self.db = get_db()

        # RSS订阅源
        self.rss_feeds = self.news_config.get("rss_feeds", [
            "https://www.chinajsb.cn/rss",
            "https://www.mohurd.gov.cn/rss",
        ])

        # 监控关键词
        self.keywords = self.news_config.get("keywords", [
            "装配式建筑", "陶粒混凝土", "预制构件", "T/CECS 10154",
            "模块化建筑", "钢结构住宅", "绿色建材", "碳中和建筑",
            "装配式政策", "建筑工业化", "智能建造",
        ])

        # 扫描间隔
        self.scan_interval_hours = self.news_config.get("scan_interval_hours", 1)

        # 大模型配置
        self.llm_provider = os.getenv("LLM_PROVIDER", "deepseek")
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
        self.llm_model = os.getenv("LLM_MODEL", "deepseek-chat")

        logger.info(f"NewsMonitor 初始化完成，监控 {len(self.rss_feeds)} 个RSS源")

    def scan_news(self):
        """扫描所有RSS源"""
        logger.info("开始扫描新闻...")

        for feed_url in self.rss_feeds:
            try:
                self._scan_feed(feed_url)
            except Exception as e:
                logger.error(f"RSS源 {feed_url} 扫描失败: {e}")

    def _scan_feed(self, feed_url: str):
        """
        扫描单个RSS源

        Args:
            feed_url: RSS源URL
        """
        logger.debug(f"扫描RSS源: {feed_url}")

        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:20]:  # 每次最多处理20条
            # 检查是否已存在
            if self._news_exists(entry.link):
                continue

            # 提取内容
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            content = title + " " + summary

            # 关键词匹配
            matched_keywords = self._match_keywords(content)
            if not matched_keywords:
                continue

            # 生成摘要 (TODO: 接入大模型)
            ai_summary = self._generate_summary(content)

            # 检测是否为政策变动
            is_policy_change = self._detect_policy_change(content)

            # 入库
            self._save_news(
                source=feed.feed.get("title", feed_url),
                title=title,
                summary=ai_summary,
                original_content=summary,
                url=entry.link,
                publish_time=self._parse_time(entry),
                keywords=matched_keywords,
                is_policy_change=is_policy_change,
            )

            # 政策变动告警
            if is_policy_change:
                self._send_policy_alert(title, entry.link)

    def _match_keywords(self, content: str) -> List[str]:
        """匹配关键词"""
        matched = []
        for kw in self.keywords:
            if kw.lower() in content.lower():
                matched.append(kw)
        return matched

    def _generate_summary(self, content: str) -> str:
        """
        生成AI摘要（支持DeepSeek/OpenAI/通义千问）

        Args:
            content: 原文内容

        Returns:
            摘要文本
        """
        if not self.llm_api_key:
            # 无API Key时返回截断原文
            if len(content) > 200:
                return content[:200] + "..."
            return content

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.llm_api_key,
                base_url=self.llm_base_url,
            )

            prompt = f"""请对以下建筑行业相关新闻进行摘要，要求：
1. 提取核心信息，控制在150字以内
2. 标注对装配式建筑行业的潜在影响
3. 如涉及政策变动，明确标注

原文：
{content[:2000]}

摘要："""

            response = client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "你是建筑行业资深分析师，擅长政策解读和市场分析。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3,
            )

            summary = response.choices[0].message.content.strip()
            logger.debug(f"AI摘要生成成功: {summary[:50]}...")
            return summary

        except Exception as e:
            logger.warning(f"AI摘要生成失败: {e}，使用原文截断")
            if len(content) > 200:
                return content[:200] + "..."
            return content

    def _detect_policy_change(self, content: str) -> bool:
        """
        检测是否为政策变动

        Args:
            content: 内容文本

        Returns:
            是否为政策变动
        """
        policy_keywords = [
            "政策", "通知", "规定", "办法", "标准",
            "住建部", "省住建厅", "新标准", "修订",
            "实施", "发布", "征求", "意见",
        ]
        content_lower = content.lower()
        match_count = sum(1 for kw in policy_keywords if kw in content_lower)
        return match_count >= 2

    def _parse_time(self, entry) -> Optional[datetime]:
        """解析发布时间"""
        try:
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
        except Exception:
            pass
        return None

    def _news_exists(self, url: str) -> bool:
        """检查新闻是否已存在"""
        if self.db.engine == "sqlite":
            sql = "SELECT id FROM news_data WHERE url = ? LIMIT 1"
        else:
            sql = "SELECT id FROM news_data WHERE url = %s LIMIT 1"
        result = self.db.fetch_one(sql, (url,))
        return result is not None

    def _save_news(self, source: str, title: str, summary: str,
                   original_content: str, url: str, publish_time: datetime,
                   keywords: List[str], is_policy_change: bool):
        """保存新闻到数据库"""
        if self.db.engine == "sqlite":
            placeholders = ", ".join(["?" for _ in range(8)])
        else:
            placeholders = ", ".join(["%s" for _ in range(8)])

        sql = f"""
        INSERT INTO news_data 
        (source, title, summary, original_content, url, publish_time, 
         keywords, is_policy_change)
        VALUES ({placeholders})
        """
        params = (
            source, title, summary, original_content, url, publish_time,
            json.dumps(keywords, ensure_ascii=False), is_policy_change
        )
        self.db.execute(sql, params)
        logger.info(f"保存新闻: {title[:50]}...")

    def _send_policy_alert(self, title: str, url: str):
        """发送政策变动告警"""
        # TODO: 实现邮件/短信告警
        logger.warning(f"[政策变动告警] {title}\n链接: {url}")

    def get_recent_news(self, hours: int = 24) -> List[Dict]:
        """获取最近新闻"""
        sql = """
        SELECT * FROM news_data 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        ORDER BY created_at DESC
        """
        return self.db.fetch_all(sql, (hours,))
