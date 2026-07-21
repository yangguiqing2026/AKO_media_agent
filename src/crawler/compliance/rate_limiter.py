"""
频率控制模块
请求间隔、随机抖动、日限额
"""

import logging
import random
import time
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    请求频率限制器

    功能:
    - 最小间隔控制 (2秒)
    - 随机抖动 (±0.5秒)
    - 日总量上限 (单平台500条)
    - 活跃时段控制 (09:00-23:00)
    """

    def __init__(self, config: dict):
        self.config = config
        compliance_config = config.get("compliance", {})

        self.min_interval = compliance_config.get("min_request_interval", 2.0)
        self.jitter = compliance_config.get("request_jitter", 0.5)
        self.daily_limit = compliance_config.get("daily_request_limit", 500)
        self.active_hours = compliance_config.get("active_hours", [9, 23])

        # 各平台请求计数
        self._request_count: Dict[str, int] = {}
        self._last_request_time: Dict[str, float] = {}
        self._last_reset_date = datetime.now().date()

        logger.info(f"RateLimiter 初始化完成，间隔: {self.min_interval}s±{self.jitter}s，日限额: {self.daily_limit}")

    def can_request(self, platform: str) -> bool:
        """
        检查是否可以发起请求

        Args:
            platform: 平台标识

        Returns:
            是否可以请求
        """
        self._reset_daily_count_if_needed()

        # 检查活跃时段
        if not self._is_active_time():
            logger.debug(f"当前非活跃时段 ({self.active_hours[0]}:00-{self.active_hours[1]}:00)")
            return False

        # 检查日限额
        if self._request_count.get(platform, 0) >= self.daily_limit:
            logger.warning(f"平台 {platform} 已达日限额 {self.daily_limit}")
            return False

        # 检查最小间隔
        last_time = self._last_request_time.get(platform, 0)
        elapsed = time.time() - last_time
        required_interval = self.min_interval + random.uniform(-self.jitter, self.jitter)

        if elapsed < required_interval:
            wait_time = required_interval - elapsed
            logger.debug(f"等待 {wait_time:.2f}s 后请求")
            time.sleep(wait_time)

        return True

    def record_request(self, platform: str):
        """
        记录请求

        Args:
            platform: 平台标识
        """
        self._request_count[platform] = self._request_count.get(platform, 0) + 1
        self._last_request_time[platform] = time.time()

    def _is_active_time(self) -> bool:
        """检查是否在活跃时段"""
        current_hour = datetime.now().hour
        return self.active_hours[0] <= current_hour < self.active_hours[1]

    def _reset_daily_count_if_needed(self):
        """重置每日计数"""
        today = datetime.now().date()
        if today > self._last_reset_date:
            self._request_count.clear()
            self._last_reset_date = today

    def get_remaining_quota(self, platform: str) -> int:
        """获取剩余配额"""
        self._reset_daily_count_if_needed()
        used = self._request_count.get(platform, 0)
        return max(0, self.daily_limit - used)

    def get_status(self) -> Dict:
        """获取频率限制器状态"""
        return {
            "request_counts": self._request_count,
            "daily_limit": self.daily_limit,
            "active_hours": self.active_hours,
            "is_active_time": self._is_active_time(),
        }
