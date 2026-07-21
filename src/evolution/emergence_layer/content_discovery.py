"""新内容形态发现 - 自主发现新的内容形态"""

import json
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class ContentFormDiscovery:
    """
    新内容形态发现器

    不是按模板生成，是创造新模板
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.discovered_forms = []
        logger.info("ContentFormDiscovery 初始化完成")

    def discover(self, performance_data: List[Dict] = None,
                 user_feedback: List[str] = None) -> List[Dict]:
        """发现潜在的新内容形态"""
        new_forms = []

        # 从表现数据中发现
        if performance_data:
            high_performers = [p for p in performance_data
                               if p.get("engagement_rate", 0) > 0.08]
            if high_performers:
                common_traits = self._find_common_traits(high_performers)
                if common_traits.get("emerging_pattern"):
                    new_forms.append({
                        "name": f"新形态-{common_traits['emerging_pattern']}",
                        "description": f"基于高表现内容的共性特征发现",
                        "inspiration": "数据驱动的内容创新",
                        "traits": common_traits,
                        "test_method": "生成3篇测试，观察表现",
                        "success_criteria": "打开率>均值20%",
                    })

        # 从用户反馈中发现
        if user_feedback:
            needs = [f for f in user_feedback if any(k in f for k in ["想看", "想知道", "能不能"])]
            if needs:
                new_forms.append({
                    "name": "需求驱动内容",
                    "description": f"基于{len(needs)}条用户需求发现",
                    "inspiration": "用户未满足需求",
                    "user_needs": needs[:5],
                    "test_method": "针对最高频需求生成内容",
                    "success_criteria": "评论含'终于写了'或'期待已久'",
                })

        # 预设的创新形态库
        innovation_library = [
            {"name": "材料日记", "description": "以第一人称记录一种材料的一天",
             "inspiration": "用户评论'想知道混凝土在想什么'"},
            {"name": "造价诚实", "description": "行业价格黑箱揭秘系列",
             "inspiration": "从'造价说'衍生的更直白版本"},
            {"name": "工具人物", "description": "吊车、螺栓、安全帽的故事",
             "inspiration": "从'AKO人物'衍生到非人类主角"},
            {"name": "失败诚实", "description": "AKO公开分享失败案例",
             "inspiration": "行业都避谈失败，AKO反其道而行"},
        ]

        for form in innovation_library:
            if not any(f.get("name") == form["name"] for f in self.discovered_forms):
                new_forms.append(form)

        self.discovered_forms.extend(new_forms)
        logger.info(f"发现 {len(new_forms)} 个新内容形态")
        return new_forms

    def _find_common_traits(self, high_performers: List[Dict]) -> Dict:
        """找出高表现内容的共性特征"""
        traits = {"emerging_pattern": "", "common_elements": []}
        # 简化版：检测共性
        has_numbers = sum(1 for p in high_performers if p.get("has_numbers", False))
        has_person = sum(1 for p in high_performers if p.get("has_person", False))
        if has_numbers > len(high_performers) * 0.7:
            traits["common_elements"].append("数字驱动")
            traits["emerging_pattern"] = "数字+信任"
        if has_person > len(high_performers) * 0.7:
            traits["common_elements"].append("人物在场")
            traits["emerging_pattern"] = "人物+共情"
        return traits
