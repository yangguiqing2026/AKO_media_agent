"""
代理IP池管理模块
住宅代理IP轮换、失败检测、自动切换
"""

import logging
import time
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class ProxyManager:
    """
    代理IP池管理器

    功能:
    - 代理IP轮换
    - 失败检测与自动切换
    - 地理分布
    """

    def __init__(self, config: dict):
        self.config = config
        compliance_config = config.get("compliance", {})

        self.rotation_interval = compliance_config.get("proxy_rotation_interval", 2)
        self.provider = compliance_config.get("proxy_provider", "bright_data")
        self.pool_size = compliance_config.get("proxy_pool_size", 10)
        self.geo_distribution = compliance_config.get("geo_distribution", True)

        # 代理池
        self._proxy_pool: List[Dict] = []
        self._current_index = 0
        self._last_rotation_time = 0
        self._failure_count: Dict[str, int] = {}

        logger.info(f"ProxyManager 初始化完成，提供商: {self.provider}")

    def get_proxy(self) -> Dict:
        """
        获取当前代理

        Returns:
            代理配置字典
        """
        current_time = time.time()

        # 检查是否需要轮换
        if current_time - self._last_rotation_time >= self.rotation_interval:
            self._rotate_proxy()

        if not self._proxy_pool:
            return self._get_default_proxy()

        proxy = self._proxy_pool[self._current_index % len(self._proxy_pool)]
        return proxy

    def _rotate_proxy(self):
        """轮换代理IP"""
        self._current_index = (self._current_index + 1) % max(len(self._proxy_pool), 1)
        self._last_rotation_time = time.time()
        logger.debug(f"代理轮换，当前索引: {self._current_index}")

    def _get_default_proxy(self) -> Dict:
        """获取默认代理配置"""
        return {
            "host": "",
            "port": 0,
            "username": "",
            "password": "",
            "protocol": "http",
        }

    def report_failure(self, proxy: Dict):
        """
        报告代理失败

        Args:
            proxy: 失败的代理配置
        """
        proxy_key = f"{proxy.get('host')}:{proxy.get('port')}"
        self._failure_count[proxy_key] = self._failure_count.get(proxy_key, 0) + 1

        # 连续失败3次自动切换
        if self._failure_count[proxy_key] >= 3:
            logger.warning(f"代理 {proxy_key} 连续失败3次，自动切换")
            self._remove_proxy(proxy)
            self._rotate_proxy()

    def _remove_proxy(self, proxy: Dict):
        """从池中移除代理"""
        proxy_key = f"{proxy.get('host')}:{proxy.get('port')}"
        self._proxy_pool = [
            p for p in self._proxy_pool
            if f"{p.get('host')}:{p.get('port')}" != proxy_key
        ]

    def add_proxy(self, proxy: Dict):
        """添加代理到池中"""
        self._proxy_pool.append(proxy)
        logger.info(f"添加代理: {proxy.get('host')}:{proxy.get('port')}")

    def get_pool_status(self) -> Dict:
        """获取代理池状态"""
        return {
            "pool_size": len(self._proxy_pool),
            "current_index": self._current_index,
            "failure_count": self._failure_count,
        }
