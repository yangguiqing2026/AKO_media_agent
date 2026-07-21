"""
多平台发布器
公众号自动发布 + 其他平台半自动 + 版本化草稿
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional

from src.database import get_db

logger = logging.getLogger(__name__)


class Publisher:
    """
    多平台发布器

    功能:
    - 公众号/官网自动发布
    - 小红书/抖音/LinkedIn半自动（人工审核后一键发布）
    - 版本化草稿存储
    - 异常回退支持
    """

    def __init__(self, config: dict):
        self.config = config
        execution_config = config.get("layers", {}).get("execution", {})
        publisher_config = execution_config.get("publisher", {})
        self.platforms_config = publisher_config.get("platforms", {})
        self.db = get_db()

        logger.info("Publisher 初始化完成")

    def publish_pending(self, platform: str = None, stage: str = "review"):
        """
        发布待发布内容

        Args:
            platform: 目标平台（None表示所有平台）
            stage: 发布阶段 (draft|review|publish)
        """
        # 查询待发布内容
        contents = self._get_pending_contents(platform, stage)

        for content in contents:
            try:
                self._publish_content(content)
            except Exception as e:
                logger.error(f"发布失败 [{content['article_id']}]: {e}")

    def _get_pending_contents(self, platform: str = None, stage: str = "review") -> List[Dict]:
        """获取待发布内容"""
        sql = """
        SELECT * FROM content
        WHERE status = %s
        AND review_status = 'approved'
        """
        params = [stage]

        if platform:
            sql += " AND platform = %s"
            params.append(platform)

        sql += " AND scheduled_at <= NOW()"
        sql += " ORDER BY scheduled_at ASC"

        return self.db.fetch_all(sql, tuple(params))

    def _publish_content(self, content: Dict):
        """
        发布单条内容

        Args:
            content: 内容数据
        """
        article_id = content["article_id"]
        platform = content["platform"]

        logger.info(f"开始发布: {article_id} -> {platform}")

        # 保存草稿版本
        self._save_draft_version(content)

        # 根据平台选择发布方式
        platform_config = self.platforms_config.get(platform, {})

        if platform == "wechat":
            result = self._publish_to_wechat(content)
        elif platform == "blog":
            result = self._publish_to_blog(content)
        elif platform in ["xiaohongshu", "douyin", "linkedin"]:
            result = self._publish_to_manual(content)
        else:
            result = {"success": False, "error": f"不支持的平台: {platform}"}

        # 记录发布结果
        self._record_publish_result(article_id, platform, result)

        if result.get("success"):
            logger.info(f"发布成功: {article_id} -> {platform}")
        else:
            logger.error(f"发布失败: {article_id} -> {platform}, 错误: {result.get('error')}")

    def _publish_to_wechat(self, content: Dict) -> Dict:
        """发布到公众号（通过AKO_ext_wechat_bridge）"""
        # TODO: 实际调用微信桥接API
        return {
            "success": True,
            "publish_url": f"https://mp.weixin.qq.com/s/{content['article_id']}",
            "publish_time": datetime.now().isoformat(),
        }

    def _publish_to_blog(self, content: Dict) -> Dict:
        """发布到官网博客"""
        # TODO: 实际写入akobuild.cloud数据库
        return {
            "success": True,
            "publish_url": f"https://akobuild.cloud/blog/{content['article_id']}",
            "publish_time": datetime.now().isoformat(),
        }

    def _publish_to_manual(self, content: Dict) -> Dict:
        """半自动发布（需要人工操作）"""
        # 生成发布提示
        return {
            "success": True,
            "manual_required": True,
            "message": f"内容已准备就绪，请手动发布到{content['platform']}",
            "content_preview": content.get("body", "")[:200],
        }

    def _save_draft_version(self, content: Dict):
        """保存草稿版本（用于回退）"""
        draft_path = f"./data/published/{content['article_id']}_v{content.get('version', 1)}.json"
        try:
            with open(draft_path, "w", encoding="utf-8") as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存草稿版本失败: {e}")

    def _record_publish_result(self, article_id: str, platform: str, result: Dict):
        """记录发布结果"""
        sql = """
        INSERT INTO publish_record 
        (article_id, platform, publish_url, publish_time, status, error_message)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
            article_id,
            platform,
            result.get("publish_url", ""),
            result.get("publish_time", datetime.now().isoformat()),
            "success" if result.get("success") else "failed",
            result.get("error", ""),
        )
        self.db.execute(sql, params)

        # 更新内容状态
        if result.get("success"):
            sql = "UPDATE content SET status = 'published', published_at = NOW() WHERE article_id = %s"
            self.db.execute(sql, (article_id,))

    def withdraw_content(self, article_id: str, reason: str = ""):
        """
        撤回已发布内容

        Args:
            article_id: 文章ID
            reason: 撤回原因
        """
        logger.warning(f"撤回内容: {article_id}, 原因: {reason}")

        # 更新状态
        sql = "UPDATE content SET status = 'withdrawn' WHERE article_id = %s"
        self.db.execute(sql, (article_id,))

        # 记录撤回
        sql = """
        INSERT INTO publish_record (article_id, platform, status, error_message)
        VALUES (%s, 'all', 'withdrawn', %s)
        """
        self.db.execute(sql, (article_id, reason))
