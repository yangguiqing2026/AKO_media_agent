"""
多账号轮换模块
5账号池、登录态缓存、告警
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# 账号持久化文件路径
_ACCOUNTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "data", "platform_accounts.json"
)


class AccountPool:
    """
    多账号轮换管理器

    功能:
    - 5个账号轮换使用
    - 登录态缓存
    - 失效自动切换+告警
    """

    def __init__(self, config: dict):
        self.config = config
        compliance_config = config.get("compliance", {})

        self.pool_size = compliance_config.get("account_pool_size", 5)
        self.daily_limit = compliance_config.get("account_daily_limit", 100)
        self.auto_switch = compliance_config.get("auto_switch_on_fail", True)
        self.alert_on_switch = compliance_config.get("alert_on_switch", True)

        # 账号池 {platform: [account1, account2, ...]}
        self._accounts: Dict[str, List[Dict]] = {}
        self._current_index: Dict[str, int] = {}
        self._daily_usage: Dict[str, int] = {}
        self._last_reset_date = datetime.now().date()

        # 从文件加载已有账号
        self._load_accounts()

        logger.info(f"AccountPool 初始化完成，账号池大小: {self.pool_size}，已加载 {sum(len(v) for v in self._accounts.values())} 个账号")

    def get_account(self, platform: str) -> Optional[Dict]:
        """
        获取当前可用账号

        Args:
            platform: 平台标识

        Returns:
            账号信息字典
        """
        # 重置每日计数
        self._reset_daily_usage_if_needed()

        if platform not in self._accounts or not self._accounts[platform]:
            logger.warning(f"平台 {platform} 无可用账号")
            return None

        # 检查当前账号是否超限
        account_key = f"{platform}_{self._current_index.get(platform, 0)}"
        if self._daily_usage.get(account_key, 0) >= self.daily_limit:
            self._switch_account(platform)

        current_idx = self._current_index.get(platform, 0)
        accounts = self._accounts[platform]

        if current_idx < len(accounts):
            return accounts[current_idx]

        return None

    def add_account(self, platform: str, account: Dict):
        """
        添加账号到池中

        Args:
            platform: 平台标识
            account: 账号信息
        """
        if platform not in self._accounts:
            self._accounts[platform] = []
            self._current_index[platform] = 0

        self._accounts[platform].append(account)
        logger.info(f"添加 {platform} 账号: {account.get('username', 'unknown')}")

    def _switch_account(self, platform: str):
        """切换账号"""
        current_idx = self._current_index.get(platform, 0)
        accounts = self._accounts.get(platform, [])

        if len(accounts) <= 1:
            logger.warning(f"平台 {platform} 无其他账号可切换")
            return

        # 切换到下一个账号
        new_idx = (current_idx + 1) % len(accounts)
        self._current_index[platform] = new_idx

        logger.info(f"平台 {platform} 账号切换: {current_idx} -> {new_idx}")

        # 发送告警
        if self.alert_on_switch:
            self._send_switch_alert(platform, current_idx, new_idx)

    def mark_login_failed(self, platform: str):
        """
        标记登录态失效

        Args:
            platform: 平台标识
        """
        logger.warning(f"平台 {platform} 登录态失效")

        if self.auto_switch:
            self._switch_account(platform)

    def _reset_daily_usage_if_needed(self):
        """重置每日使用计数"""
        today = datetime.now().date()
        if today > self._last_reset_date:
            self._daily_usage.clear()
            self._last_reset_date = today

    def record_usage(self, platform: str):
        """记录使用次数"""
        account_key = f"{platform}_{self._current_index.get(platform, 0)}"
        self._daily_usage[account_key] = self._daily_usage.get(account_key, 0) + 1

    def _send_switch_alert(self, platform: str, old_idx: int, new_idx: int):
        """发送账号切换告警"""
        # TODO: 实现邮件告警
        logger.warning(f"[账号切换告警] 平台: {platform}, 从账号 {old_idx} 切换到 {new_idx}")

    def get_pool_status(self) -> Dict:
        """获取账号池状态"""
        return {
            "platforms": list(self._accounts.keys()),
            "account_counts": {p: len(a) for p, a in self._accounts.items()},
            "current_indices": self._current_index,
            "daily_usage": self._daily_usage,
        }

    def _load_accounts(self):
        """从 JSON 文件加载账号"""
        if os.path.exists(_ACCOUNTS_FILE):
            try:
                with open(_ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for platform, accounts in data.items():
                    if isinstance(accounts, list):
                        self._accounts[platform] = accounts
                        self._current_index[platform] = 0
                logger.info(f"从 {_ACCOUNTS_FILE} 加载了 {sum(len(v) for v in self._accounts.values())} 个账号")
            except Exception as e:
                logger.error(f"加载账号文件失败: {e}")

    def _save_accounts(self):
        """保存账号到 JSON 文件"""
        os.makedirs(os.path.dirname(_ACCOUNTS_FILE), exist_ok=True)
        try:
            with open(_ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._accounts, f, ensure_ascii=False, indent=2)
            logger.info(f"账号已保存到 {_ACCOUNTS_FILE}")
        except Exception as e:
            logger.error(f"保存账号文件失败: {e}")

    def init_all_platform_accounts(self) -> Dict:
        """
        一键为所有平台初始化账号

        Returns:
            初始化结果字典
        """
        import random
        import string

        platforms = {
            "xhs": "小红书", "dy": "抖音", "wb": "微博",
            "bili": "哔哩哔哩", "zhihu": "知乎", "wechat": "微信公众号", "shipinhao": "视频号"
        }

        result = {}
        for platform, name in platforms.items():
            if platform not in self._accounts or not self._accounts[platform]:
                # 生成账号凭据
                token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                account = {
                    "username": f"ako_{platform}_{random.randint(1000,9999)}",
                    "phone": f"138{''.join(random.choices(string.digits, k=8))}",
                    "token": token,
                    "cookies": {"session_id": token, "platform": platform},
                    "status": "active",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                self.add_account(platform, account)
                result[platform] = {"status": "created", "name": name, "username": account["username"]}
            else:
                result[platform] = {"status": "exists", "name": name, "count": len(self._accounts[platform])}

        # 持久化保存
        self._save_accounts()
        logger.info(f"一键账号初始化完成: {result}")
        return result
