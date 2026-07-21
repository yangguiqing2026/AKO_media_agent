"""
表单数据触发模块
用户询价后推送匹配案例
"""

import logging
from typing import Dict, List, Optional

from src.database import get_db

logger = logging.getLogger(__name__)


class FormTrigger:
    """
    表单数据触发器

    功能:
    - 用户询价触发
    - 案例匹配推送
    - 跟进提醒
    """

    def __init__(self, config: dict):
        self.config = config
        self.db = get_db()
        logger.info("FormTrigger 初始化完成")

    def handle_form_submission(self, form_data: Dict) -> Dict:
        """
        处理表单提交

        Args:
            form_data: 表单数据

        Returns:
            处理结果
        """
        # 解析用户需求
        user_need = self._parse_user_need(form_data)

        # 匹配案例
        matched_cases = self._match_cases(user_need)

        return {
            "user_need": user_need,
            "matched_cases": matched_cases,
            "action": "push_recommendation",
        }

    def _parse_user_need(self, form_data: Dict) -> Dict:
        """解析用户需求"""
        return {
            "location": form_data.get("location", ""),
            "budget": form_data.get("budget", ""),
            "house_type": form_data.get("house_type", ""),
            "area": form_data.get("area", ""),
        }

    def _match_cases(self, user_need: Dict) -> List[Dict]:
        """匹配案例"""
        # TODO: 基于用户需求匹配案例
        return []
