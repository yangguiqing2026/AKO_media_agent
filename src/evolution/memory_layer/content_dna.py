"""
内容DNA提取器
存储内容的"基因"而非内容本身，用于进化分析
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import jieba

from src.database import get_db

logger = logging.getLogger(__name__)


class ContentDNA:
    """
    内容DNA分析器
    
    从每条内容中提取四维基因：
    - 结构基因：开头类型、段落数、句长、对话比例
    - 风格基因：调性、感官词、禁用词、人在现场
    - 思想基因：不可替代性、具体性、时间诚实、人的在场
    - 表现基因：阅读率、点赞率、评论质量、转发率、收藏率
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.db = get_db()

        # 感官词库
        self.sensory_words = {
            "视觉": ["光线", "色彩", "阴影", "明亮", "昏暗", "金黄", "奶油色"],
            "听觉": ["声音", "碰撞", "风声", "金属", "回响", "安静", "嘈杂"],
            "触觉": ["温度", "粗糙", "光滑", "重量", "质感", "冰冷", "温暖"],
            "嗅觉": ["气味", "灰尘", "木头", "潮湿", "清新"],
        }

        # 禁用词（空洞词汇）
        self.forbidden_words = [
            "解决方案", "推动", "赋能", "打造", "引领", "生态",
            "闭环", "抓手", "颗粒度", "底层逻辑", "顶层设计",
        ]

        # 开头类型识别模式
        self.opening_patterns = {
            "slice": ["凌晨", "清晨", "下午", "傍晚", "黄昏", "早上", "上午"],
            "question": ["？", "吗", "怎么", "为什么", "如何", "是否"],
            "number": ["%", "元", "万", "吨", "平米", "MPa", "天"],
            "scene": ["工地", "车间", "现场", "项目", "厂房", "仓库"],
        }

        logger.info("ContentDNA 初始化完成")

    def extract_dna(self, content_id: str, title: str, body: str,
                    performance: Dict = None) -> Dict:
        """
        从内容中提取DNA

        Args:
            content_id: 内容ID
            title: 标题
            body: 正文
            performance: 表现数据（可选）

        Returns:
            内容DNA字典
        """
        dna = {
            "content_id": content_id,
            "extracted_at": datetime.now().isoformat(),
            "genes": {
                "structure": self._extract_structure_genes(title, body),
                "style": self._extract_style_genes(body),
                "thought": self._extract_thought_genes(title, body),
                "performance": performance or {},
            }
        }

        return dna

    def _extract_structure_genes(self, title: str, body: str) -> Dict:
        """提取结构基因"""
        paragraphs = [p.strip() for p in body.split("\n") if p.strip()]
        sentences = [s.strip() for s in body.replace("。", ".").split(".") if s.strip()]

        # 开头类型
        first_line = title + (body[:50] if body else "")
        opening_type = self._detect_opening_type(first_line)

        # 对话比例
        dialogue_markers = ['"', '"', '：', ':']
        dialogue_chars = sum(1 for c in body if c in dialogue_markers)
        dialogue_ratio = min(1.0, dialogue_chars / max(len(body), 1) * 10)

        return {
            "opening_type": opening_type,
            "paragraph_count": len(paragraphs),
            "sentence_count": len(sentences),
            "sentence_length_avg": round(len(body) / max(len(sentences), 1), 1),
            "dialogue_ratio": round(dialogue_ratio, 3),
            "has_numbers": any(c.isdigit() for c in title),
            "word_count": len(body),
        }

    def _extract_style_genes(self, body: str) -> Dict:
        """提取风格基因"""
        words = list(jieba.cut(body))

        # 感官词统计
        sensory_found = {}
        for category, word_list in self.sensory_words.items():
            found = [w for w in words if w in word_list]
            if found:
                sensory_found[category] = found

        # 禁用词检测
        forbidden_used = [w for w in words if w in self.forbidden_words]

        # 人在现场检测
        person_markers = ["我", "我们", "老周", "师傅", "工人", "他", "她"]
        person_in_scene = any(m in body for m in person_markers)

        return {
            "sensory_words": sensory_found,
            "sensory_richness": len(sensory_found),
            "forbidden_words_used": forbidden_used,
            "forbidden_count": len(forbidden_used),
            "person_in_scene": person_in_scene,
        }

    def _extract_thought_genes(self, title: str, body: str) -> Dict:
        """提取思想基因（思想厚度四维度）"""
        words = list(jieba.cut(body))

        # 不可替代性：是否包含AKO独有信息
        unique_markers = ["AKO", "阿格", "桐木岭", "陶粒", "T/CECS", "专利"]
        unique_score = min(100, sum(20 for m in unique_markers if m in body))

        # 具体性：数字和具体细节的密度
        numbers = [w for w in words if any(c.isdigit() for c in w)]
        specificity_score = min(100, len(numbers) * 10 + body.count("㎡") * 15 + body.count("元") * 15)

        # 时间诚实：是否体现长期积累
        time_markers = ["年", "月", " depuis", "以来", "持续", "坚持", "每天", "反复"]
        time_score = min(100, sum(15 for m in time_markers if m in body))

        # 人的在场：真实人物的出现
        person_names = ["老周", "师傅", "工友", "操作员", "设计师", "创始人"]
        presence_score = min(100, sum(20 for m in person_names if m in body))

        return {
            "irreplaceability_score": max(30, unique_score),
            "specificity_score": max(30, specificity_score),
            "time_honesty_score": max(20, time_score),
            "presence_score": max(20, presence_score),
            "thought_depth_total": round(
                unique_score * 0.4 + specificity_score * 0.3 +
                time_score * 0.15 + presence_score * 0.15, 1
            ),
        }

    def _detect_opening_type(self, text: str) -> str:
        """检测开头类型"""
        for opening_type, markers in self.opening_patterns.items():
            if any(m in text for m in markers):
                return opening_type
        return "narrative"

    def classify_genes(self, dna: Dict, performance: Dict) -> Dict:
        """
        根据表现数据对基因进行分类
        标记为"优势基因"或"劣势基因"

        Args:
            dna: 内容DNA
            performance: 表现数据

        Returns:
            基因分类结果
        """
        reads = performance.get("reads", 0)
        likes = performance.get("likes", 0)
        shares = performance.get("shares", 0)

        # 简单评估：高于平均为优势，低于平均为劣势
        engagement_rate = (likes + shares) / max(reads, 1)
        is_high_performing = engagement_rate > 0.05  # 5%互动率为阈值

        classification = {
            "content_id": dna["content_id"],
            "is_high_performing": is_high_performing,
            "gene_label": "优势基因" if is_high_performing else "劣势基因",
            "engagement_rate": round(engagement_rate, 4),
            "key_genes": {
                "structure": dna["genes"]["structure"],
                "style_highlights": dna["genes"]["style"].get("sensory_words", {}),
                "thought_total": dna["genes"]["thought"]["thought_depth_total"],
            }
        }

        return classification

    def get_dominant_genes(self, limit: int = 20) -> List[Dict]:
        """获取优势基因库（高表现内容的共性基因）"""
        if self.db.engine == "sqlite":
            sql = "SELECT dna_data FROM content_dna WHERE gene_label = ? ORDER BY extracted_at DESC LIMIT ?"
        else:
            sql = "SELECT dna_data FROM content_dna WHERE gene_label = %s ORDER BY extracted_at DESC LIMIT %s"

        rows = self.db.fetch_all(sql, ("优势基因", limit))
        return [json.loads(r["dna_data"]) for r in rows if r.get("dna_data")]

    def save_dna(self, dna: Dict, gene_label: str = "pending"):
        """保存DNA到数据库"""
        if self.db.engine == "sqlite":
            placeholders = ", ".join(["?" for _ in range(5)])
        else:
            placeholders = ", ".join(["%s" for _ in range(5)])

        sql = f"""
        INSERT INTO content_dna (content_id, dna_data, gene_label, extracted_at, updated_at)
        VALUES ({placeholders})
        """
        params = (
            dna["content_id"],
            json.dumps(dna, ensure_ascii=False),
            gene_label,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
        )
        self.db.execute(sql, params)
        logger.debug(f"DNA已保存: {dna['content_id']}")
