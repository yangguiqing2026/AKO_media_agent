"""
AKO认知图谱
AKO品牌认知的持续构建与更新
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.database import get_db

logger = logging.getLogger(__name__)


class AKOCognitionGraph:
    """
    AKO品牌认知图谱

    功能:
    - 追踪AKO知道什么、不知道什么
    - 记录"以为知道但错了"的认知纠正
    - 积累新兴洞察
    - 生成AKO认知报告
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.db = get_db()

        # 初始认知状态
        self.cognition = {
            "what_we_know": [
                "陶粒墙板技术", "T/CECS 10154标准", "装配式建筑施工流程",
                "贵州建筑政策环境", "AKO产品线", "核心项目案例",
            ],
            "what_we_dont_know": [
                "用户真实价格敏感度", "竞品最新技术突破",
                "读者最关心的内容类型", "行业未满足需求",
            ],
            "what_we_thought_we_knew_but_wrong": [],
            "emerging_insights": [],
        }

        # 知识节点
        self.nodes = {}
        # 知识关系
        self.edges = []

        logger.info("AKOCognitionGraph 初始化完成")

    def update(self, new_content: str = "", feedback: List[Dict] = None) -> Dict:
        """
        基于新内容和反馈更新认知

        Args:
            new_content: 新内容文本
            feedback: 反馈数据列表

        Returns:
            认知更新结果
        """
        updates = {
            "updated_at": datetime.now().isoformat(),
            "new_knowledge": [],
            "corrected_knowledge": [],
            "new_insights": [],
        }

        # 从新内容中提取知识
        if new_content:
            new_entities = self._extract_entities(new_content)
            for entity in new_entities:
                if entity not in self.nodes:
                    self.nodes[entity] = {"type": "concept", "first_seen": datetime.now().isoformat()}
                    updates["new_knowledge"].append(entity)

        # 从反馈中检测认知纠正
        if feedback:
            corrections = self._detect_corrections(feedback)
            updates["corrected_knowledge"] = corrections

        # 保存更新
        self._save_cognition(updates)

        logger.info(f"认知图谱更新: +{len(updates['new_knowledge'])}新知识, "
                     f"{len(updates['corrected_knowledge'])}纠正")
        return updates

    def _extract_entities(self, text: str) -> List[str]:
        """从文本中提取知识实体"""
        import jieba
        words = list(jieba.cut(text))

        # 识别专业术语和专有名词
        entity_patterns = {
            "material": ["混凝土", "墙板", "钢材", "陶粒", "螺栓", "水泥"],
            "standard": ["T/CECS", "GB", "标准", "规范"],
            "project": ["项目", "工程", "桐木岭"],
            "technique": ["装配", "预制", "模块化", "吊装", "焊接"],
        }

        entities = []
        for word in words:
            for category, keywords in entity_patterns.items():
                if any(k in word for k in keywords) and len(word) >= 2:
                    entities.append(word)
                    break

        return list(set(entities))

    def _detect_corrections(self, feedback: List[Dict]) -> List[Dict]:
        """从反馈中检测认知纠正"""
        corrections = []
        for fb in feedback:
            if fb.get("type") == "correction":
                correction = {
                    "original_belief": fb.get("original", ""),
                    "corrected_to": fb.get("corrected", ""),
                    "source": fb.get("source", "user_feedback"),
                    "detected_at": datetime.now().isoformat(),
                }
                corrections.append(correction)
                self.cognition["what_we_thought_we_knew_but_wrong"].append(
                    f"{correction['original_belief']} → {correction['corrected_to']}"
                )
        return corrections

    def generate_report(self) -> Dict:
        """生成AKO认知报告"""
        return {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "known_items": len(self.cognition["what_we_know"]),
                "unknown_items": len(self.cognition["what_we_dont_know"]),
                "corrected_items": len(self.cognition["what_we_thought_we_knew_but_wrong"]),
                "emerging_insights": len(self.cognition["emerging_insights"]),
            },
            "what_we_know": self.cognition["what_we_know"],
            "what_we_dont_know": self.cognition["what_we_dont_know"],
            "corrections": self.cognition["what_we_thought_we_knew_but_wrong"],
            "emerging": self.cognition["emerging_insights"],
            "knowledge_nodes": len(self.nodes),
            "knowledge_edges": len(self.edges),
        }

    def _save_cognition(self, updates: Dict):
        """保存认知更新"""
        if self.db.engine == "sqlite":
            placeholders = ", ".join(["?" for _ in range(2)])
        else:
            placeholders = ", ".join(["%s" for _ in range(2)])

        sql = f"""
        INSERT INTO cognition_updates (update_data, updated_at)
        VALUES ({placeholders})
        """
        params = (
            json.dumps(updates, ensure_ascii=False),
            datetime.now().isoformat(),
        )
        self.db.execute(sql, params)
