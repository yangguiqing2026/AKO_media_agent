"""
验证码处理模块
验证码检测与自动暂停
"""

import logging
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class CaptchaHandler:
    """
    验证码处理器

    功能:
    - 验证码检测
    - 自动暂停采集
    - 人工介入告警
    """

    def __init__(self, config: dict):
        self.config = config
        compliance_config = config.get("compliance", {})

        self.auto_pause = compliance_config.get("auto_pause_on_captcha", True)
        self.alert_enabled = compliance_config.get("captcha_alert", True)

        # 验证码状态
        self._captcha_detected: Dict[str, bool] = {}
        self._last_captcha_time: Dict[str, datetime] = {}
        self._captcha_count: Dict[str, int] = {}

        logger.info(f"CaptchaHandler 初始化完成，自动暂停: {self.auto_pause}")

    def handle_captcha(self, platform: str) -> bool:
        """
        处理验证码

        Args:
            platform: 平台标识

        Returns:
            是否已暂停
        """
        logger.warning(f"[验证码] 平台 {platform} 检测到验证码")

        self._captcha_detected[platform] = True
        self._last_captcha_time[platform] = datetime.now()
        self._captcha_count[platform] = self._captcha_count.get(platform, 0) + 1

        # 自动暂停
        if self.auto_pause:
            logger.warning(f"[验证码] 平台 {platform} 已自动暂停采集")
            self._send_alert(platform)
            return True

        return False

    def is_paused(self, platform: str) -> bool:
        """
        检查平台是否因验证码暂停

        Args:
            platform: 平台标识

        Returns:
            是否已暂停
        """
        return self._captcha_detected.get(platform, False)

    def resume(self, platform: str):
        """
        恢复采集（人工确认）

        Args:
            platform: 平台标识
        """
        if self._captcha_detected.get(platform, False):
            self._captcha_detected[platform] = False
            logger.info(f"[验证码] 平台 {platform} 已恢复采集")

    def _send_alert(self, platform: str):
        """发送验证码告警"""
        if not self.alert_enabled:
            return

        # TODO: 实现邮件/短信告警
        count = self._captcha_count.get(platform, 0)
        logger.warning(
            f"[验证码告警] 平台: {platform}, "
            f"累计验证码次数: {count}, "
            f"请人工介入处理"
        )

    def get_status(self) -> Dict:
        """获取验证码处理状态"""
        return {
            "paused_platforms": [p for p, paused in self._captcha_detected.items() if paused],
            "captcha_counts": self._captcha_count,
            "last_captcha_times": {
                p: t.isoformat() for p, t in self._last_captcha_time.items()
            },
        }
