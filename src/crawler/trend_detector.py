"""
趋势探测器模块
指数API + 热榜
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import List, Dict, Optional

import requests

from src.database import get_db

logger = logging.getLogger(__name__)


class TrendDetector:
    """
    趋势探测器

    功能:
    - 百度指数/微信指数/抖音热榜/小红书热搜
    - 关键词热度追踪
    - 关联词推荐
    """

    def __init__(self, config: dict):
        self.config = config
        self.crawler_config = config.get("layers", {}).get("crawler", {})
        self.trend_config = self.crawler_config.get("trend_detector", {})
        self.db = get_db()

        # 数据源
        self.sources = self.trend_config.get("sources", [
            "baidu_index", "wechat_index", "douyin_hot", "xhs_hot"
        ])

        # 关键词矩阵
        self.keyword_matrix = self.trend_config.get("keyword_matrix", {
            "tier1": ["装配式建筑", "模块化住宅"],
            "tier2": ["陶粒混凝土", "预制墙板", "快速建房"],
            "tier3": ["农村自建房", "轻钢别墅", "集装箱房"],
            "longtail": ["贵阳装配式建筑", "贵州模块化建筑", "三层别墅造价"],
        })

        logger.info(f"TrendDetector 初始化完成，数据源: {self.sources}")

        # API配置
        self.baidu_cookie = os.getenv("BAIDU_COOKIE", "")
        self.request_timeout = 10

    def detect_trends(self):
        """检测所有数据源的趋势"""
        logger.info("开始检测趋势...")

        for source in self.sources:
            try:
                self._detect_source_trend(source)
            except Exception as e:
                logger.error(f"趋势源 {source} 检测失败: {e}")

    def _detect_source_trend(self, source: str):
        """
        检测单个数据源趋势

        Args:
            source: 数据源标识
        """
        logger.debug(f"检测趋势源: {source}")

        # 遍历关键词矩阵
        for tier, keywords in self.keyword_matrix.items():
            for keyword in keywords:
                trend_data = self._fetch_trend_data(source, keyword, tier)
                if trend_data:
                    self._save_trend_data(source, keyword, tier, trend_data)

    def _fetch_trend_data(self, source: str, keyword: str, tier: str) -> Optional[Dict]:
        """
        获取趋势数据

        Args:
            source: 数据源
            keyword: 关键词
            tier: 词级

        Returns:
            趋势数据字典
        """
        try:
            if source == "baidu_index":
                return self._fetch_baidu_index(keyword, tier)
            elif source == "douyin_hot":
                return self._fetch_douyin_hot(keyword, tier)
            elif source == "xhs_hot":
                return self._fetch_xhs_hot(keyword, tier)
            elif source == "wechat_index":
                return self._fetch_wechat_index(keyword, tier)
            else:
                logger.warning(f"未知数据源: {source}")
                return None
        except Exception as e:
            logger.warning(f"获取趋势数据失败 ({source}/{keyword}): {e}")
            return None

    def _fetch_baidu_index(self, keyword: str, tier: str) -> Optional[Dict]:
        """
        获取百度指数
        需要登录态Cookie
        """
        if not self.baidu_cookie:
            logger.debug("百度指数需要Cookie，跳过")
            return None

        url = "https://index.baidu.com/api/SearchApi/index"
        params = {
            "area": 0,
            "word": json.dumps({"name": keyword, "wordType": 1}),
            "days": 7,
        }
        headers = {
            "Cookie": self.baidu_cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=self.request_timeout)
            data = resp.json().get("data", {})
            user_index = data.get("userIndexes", [])
            if user_index:
                index_data = user_index[0].get("index", [])
                return {
                    "heat_index": sum(index_data) / len(index_data) if index_data else 0,
                    "rank": 0,
                    "related_words": data.get("relatedWords", []),
                    "trend_curve": index_data,
                }
        except Exception as e:
            logger.debug(f"百度指数获取失败: {e}")
        return None

    def _fetch_douyin_hot(self, keyword: str, tier: str) -> Optional[Dict]:
        """
        获取抖音热榜
        通过抖音热榜API获取
        """
        url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.douyin.com/",
        }

        try:
            resp = requests.get(url, headers=headers, timeout=self.request_timeout)
            data = resp.json().get("data", {})
            word_list = data.get("word_list", [])

            # 检查关键词是否在热榜中
            for i, item in enumerate(word_list[:50]):
                word = item.get("word", "")
                if keyword in word or word in keyword:
                    return {
                        "heat_index": item.get("hot_value", 0),
                        "rank": i + 1,
                        "related_words": [w.get("word", "") for w in word_list[:10]],
                        "trend_curve": [],
                    }

            # 不在热榜则返回低热度
            return {
                "heat_index": 0,
                "rank": 0,
                "related_words": [w.get("word", "") for w in word_list[:10]],
                "trend_curve": [],
            }
        except Exception as e:
            logger.debug(f"抖音热榜获取失败: {e}")
        return None

    def _fetch_xhs_hot(self, keyword: str, tier: str) -> Optional[Dict]:
        """
        获取小红书热搜
        通过小红书热榜API获取
        """
        url = "https://edith.xiaohongshu.com/api/sns/v1/search/hot_list"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        try:
            resp = requests.get(url, headers=headers, timeout=self.request_timeout)
            data = resp.json().get("data", {})
            items = data.get("items", [])

            # 检查关键词是否在热搜中
            for i, item in enumerate(items[:30]):
                title = item.get("title", "")
                if keyword in title or title in keyword:
                    return {
                        "heat_index": item.get("hot_value", 0),
                        "rank": i + 1,
                        "related_words": [w.get("title", "") for w in items[:10]],
                        "trend_curve": [],
                    }

            return {
                "heat_index": 0,
                "rank": 0,
                "related_words": [w.get("title", "") for w in items[:10]],
                "trend_curve": [],
            }
        except Exception as e:
            logger.debug(f"小红书热搜获取失败: {e}")
        return None

    def _fetch_wechat_index(self, keyword: str, tier: str) -> Optional[Dict]:
        """
        获取微信指数
        通过搜狗微信搜索获取文章热度
        """
        url = "https://weixin.sogou.com/weixin"
        params = {
            "type": 2,
            "query": keyword,
            "ie": "utf8",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=self.request_timeout)
            # 简单解析搜索结果数量作为热度指标
            content = resp.text
            # 计算搜索结果数
            result_count = content.count('class="news-list')
            return {
                "heat_index": result_count * 100,  # 粗略估计
                "rank": 0,
                "related_words": [],
                "trend_curve": [],
            }
        except Exception as e:
            logger.debug(f"微信指数获取失败: {e}")
        return None

    def _save_trend_data(self, source: str, keyword: str, tier: str, data: Dict):
        """保存趋势数据"""
        if self.db.engine == "sqlite":
            placeholders = ", ".join(["?" for _ in range(7)])
        else:
            placeholders = ", ".join(["%s" for _ in range(7)])

        sql = f"""
        INSERT INTO trend_data 
        (source, keyword, tier, heat_index, rank, related_words, trend_data)
        VALUES ({placeholders})
        """
        params = (
            source, keyword, tier,
            data.get("heat_index", 0),
            data.get("rank", 0),
            json.dumps(data.get("related_words", []), ensure_ascii=False),
            json.dumps(data.get("trend_curve", []), ensure_ascii=False),
        )
        self.db.execute(sql, params)

    def get_hot_keywords(self, source: str = None, limit: int = 20) -> List[Dict]:
        """获取热门关键词"""
        sql = """
        SELECT keyword, tier, heat_index, rank, related_words
        FROM trend_data
        WHERE recorded_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        """
        params = []
        if source:
            sql += " AND source = %s"
            params.append(source)
        sql += " ORDER BY heat_index DESC LIMIT %s"
        params.append(limit)

        return self.db.fetch_all(sql, tuple(params))

    def get_keyword_trend(self, keyword: str, days: int = 30) -> List[Dict]:
        """获取关键词趋势曲线"""
        sql = """
        SELECT source, heat_index, rank, recorded_at
        FROM trend_data
        WHERE keyword = %s
        AND recorded_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        ORDER BY recorded_at ASC
        """
        return self.db.fetch_all(sql, (keyword, days))
