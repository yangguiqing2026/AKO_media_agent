"""
读者画像进化
动态理解读者，检测兴趣漂移，预测未来需求
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.database import get_db

logger = logging.getLogger(__name__)


class ReaderEvolution:
    """
    读者画像进化器

    功能:
    - 读者分群动态理解
    - 兴趣漂移检测
    - 内容偏好偏移追踪
    - 未来需求预测
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.db = get_db()

        # 初始读者分群
        self.segments = {
            "architect": {
                "name": "建筑师/设计师",
                "interests": ["技术参数", "建造现场", "建筑哲学", "材料创新"],
                "engagement_pattern": "收藏>点赞>评论",
                "content_preference": "深度技术内容+现场纪实",
            },
            "owner": {
                "name": "业主/投资方",
                "interests": ["造价分析", "项目案例", "品质信任", "政策解读"],
                "engagement_pattern": "点赞>分享>收藏",
                "content_preference": "真实案例+造价透明",
            },
            "industry": {
                "name": "行业从业者",
                "interests": ["行业动态", "技术标准", "市场趋势", "竞品分析"],
                "engagement_pattern": "评论>收藏>点赞",
                "content_preference": "行业洞察+技术干货",
            },
            "general": {
                "name": "普通关注者",
                "interests": ["建筑美学", "乡村建设", "绿色生活"],
                "engagement_pattern": "点赞>浏览",
                "content_preference": "故事性+视觉美感",
            },
        }

        logger.info("ReaderEvolution 初始化完成")

    def evolve(self, behavior_data: List[Dict]) -> Dict:
        """
        基于新行为数据进化读者理解

        Args:
            behavior_data: 行为数据列表 [{segment, action, content_type, timestamp}]

        Returns:
            进化结果
        """
        if not behavior_data:
            return {"status": "no_data"}

        # 统计各分群行为
        segment_stats = {}
        for data in behavior_data:
            seg = data.get("segment", "general")
            if seg not in segment_stats:
                segment_stats[seg] = {"actions": [], "content_types": []}
            segment_stats[seg]["actions"].append(data.get("action", ""))
            segment_stats[seg]["content_types"].append(data.get("content_type", ""))

        # 检测兴趣漂移
        shifts = self._detect_interest_shifts(segment_stats)

        # 更新偏好
        updates = self._update_preferences(segment_stats)

        result = {
            "evolved_at": datetime.now().isoformat(),
            "data_points": len(behavior_data),
            "segments_analyzed": list(segment_stats.keys()),
            "interest_shifts": shifts,
            "preference_updates": updates,
        }

        # 保存到数据库
        self._save_evolution(result)

        logger.info(f"读者画像进化完成，分析 {len(behavior_data)} 条行为数据")
        return result

    def _detect_interest_shifts(self, stats: Dict) -> List[Dict]:
        """检测兴趣漂移"""
        shifts = []
        for seg, data in stats.items():
            if seg not in self.segments:
                continue

            current_interests = self.segments[seg]["interests"]
            content_types = data.get("content_types", [])

            # 统计内容类型频率
            type_freq = {}
            for ct in content_types:
                type_freq[ct] = type_freq.get(ct, 0) + 1

            # 检测新兴兴趣（频率高但不在当前兴趣列表中）
            for ct, freq in type_freq.items():
                if freq >= 3 and ct not in current_interests:
                    shifts.append({
                        "segment": seg,
                        "shift_type": "emerging_interest",
                        "new_interest": ct,
                        "frequency": freq,
                        "suggestion": f"{self.segments[seg]['name']}群体对'{ct}'的关注增加",
                    })

        return shifts

    def _update_preferences(self, stats: Dict) -> Dict:
        """更新内容偏好"""
        updates = {}
        for seg, data in stats.items():
            if seg not in self.segments:
                continue

            actions = data.get("actions", [])
            action_freq = {}
            for a in actions:
                action_freq[a] = action_freq.get(a, 0) + 1

            if action_freq:
                dominant_action = max(action_freq, key=action_freq.get)
                updates[seg] = {
                    "dominant_action": dominant_action,
                    "action_distribution": action_freq,
                }

        return updates

    def predict_needs(self) -> List[Dict]:
        """预测读者未来内容需求"""
        predictions = []
        for seg_id, seg_data in self.segments.items():
            predictions.append({
                "segment": seg_id,
                "segment_name": seg_data["name"],
                "predicted_needs": [
                    f"更多{interest}相关内容" for interest in seg_data["interests"][:2]
                ],
                "content_suggestion": f"针对{seg_data['name']}，建议增加{seg_data['content_preference']}类型内容",
            })
        return predictions

    def _save_evolution(self, result: Dict):
        """保存进化结果"""
        if self.db.engine == "sqlite":
            placeholders = ", ".join(["?" for _ in range(2)])
        else:
            placeholders = ", ".join(["%s" for _ in range(2)])

        sql = f"""
        INSERT INTO reader_evolution (evolution_data, evolved_at)
        VALUES ({placeholders})
        """
        params = (
            json.dumps(result, ensure_ascii=False),
            datetime.now().isoformat(),
        )
        self.db.execute(sql, params)
