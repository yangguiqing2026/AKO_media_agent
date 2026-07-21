"""行业知识图谱构建 - 实体+关系+推理"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Tuple

import jieba

from src.database import get_db

logger = logging.getLogger(__name__)


class IndustryKnowledgeGraph:
    """装配式建筑行业知识图谱"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.db = get_db()
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Tuple[str, str, str]] = []

        # 初始化核心节点
        self._init_core_nodes()
        logger.info("IndustryKnowledgeGraph 初始化完成")

    def _init_core_nodes(self):
        """初始化核心知识节点"""
        core = {
            "陶粒混凝土": {"type": "material", "props": ["轻质", "保温", "隔音", "耐火"]},
            "装配式建筑": {"type": "concept", "props": ["预制", "装配", "快速", "绿色"]},
            "模块化住宅": {"type": "concept", "props": ["工厂预制", "现场组装", "标准化"]},
            "T/CECS 10154": {"type": "standard", "props": ["抗压", "耐火", "隔声"]},
            "AKO": {"type": "brand", "props": ["贵州", "装配式", "陶粒", "品牌"]},
        }
        for name, data in core.items():
            self.nodes[name] = data

    def expand(self, text: str) -> Dict:
        """基于新内容扩展知识图谱"""
        words = list(jieba.cut(text))
        new_nodes = []
        new_edges = []

        # 提取实体
        for word in words:
            if len(word) >= 2 and word not in self.nodes:
                # 简单启发式：如果词频繁出现，可能是实体
                if any(k in word for k in ["建筑", "墙", "板", "钢", "项目", "工程"]):
                    self.nodes[word] = {"type": "concept", "props": []}
                    new_nodes.append(word)

        # 建立关系
        for i, w1 in enumerate(words):
            for w2 in words[i+1:i+5]:
                if w1 in self.nodes and w2 in self.nodes and w1 != w2:
                    edge = (w1, w2, "related")
                    if edge not in self.edges:
                        self.edges.append(edge)
                        new_edges.append(edge)

        result = {"new_nodes": len(new_nodes), "new_edges": len(new_edges)}
        logger.info(f"知识图谱扩展: +{len(new_nodes)}节点, +{len(new_edges)}关系")
        return result

    def get_graph_summary(self) -> Dict:
        """获取图谱摘要"""
        type_counts = {}
        for node in self.nodes.values():
            t = node.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "type_distribution": type_counts,
        }
