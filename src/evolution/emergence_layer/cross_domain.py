"""跨领域知识迁移 - 从文学/纪录片/科学传播迁移到建筑内容"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class CrossDomainTransfer:
    """
    跨领域知识迁移器

    从其他领域学习，迁移到建筑内容
    """

    def __init__(self, config: dict = None):
        self.config = config or {}

        # 预设迁移模式库
        self.transfer_library = {
            "文学->建筑": {
                "source_pattern": "海明威的'冰山理论'（只写1/8，藏7/8）",
                "target_application": "AKO建造志：只写现场切片，藏技术厚度",
                "example": "'老周抽了根烟'背后藏着整个验收标准",
                "method": "留白叙事：不说完，让读者自己连",
            },
            "纪录片->建筑": {
                "source_pattern": "《人生一串》的烟火气叙事",
                "target_application": "工地24时：不解说，只呈现",
                "example": "金属碰撞声+风声+远处的车声=工地的真实",
                "method": "环境音叙事：用声音代替文字",
            },
            "科学传播->建筑": {
                "source_pattern": "费曼的'用简单语言解释复杂概念'",
                "target_application": "0154技术谈：用身体感知解释技术参数",
                "example": "'5-10MPa' = '三个人站在上面，没晃'",
                "method": "类比法：把抽象变成可感知的",
            },
            "新闻->建筑": {
                "source_pattern": "特稿的非虚构写作",
                "target_application": "AKO人物：用场景开头，不用介绍开头",
                "example": "'凌晨五点，老周已经在工地了' > '老周是AKO的优秀员工'",
                "method": "场景先行：让读者先进入现场",
            },
            "美食->建筑": {
                "source_pattern": "美食纪录片的'食材溯源'叙事",
                "target_application": "造价说：从一块墙板的价格追溯到工厂",
                "example": "'357元/平米'背后是陶粒从哪来、怎么烧、谁在运",
                "method": "溯源法：一个数字展开一条链",
            },
        }

        logger.info("CrossDomainTransfer 初始化完成")

    def transfer(self, source_domain: str = None, target_domain: str = "建筑") -> List[Dict]:
        """获取迁移建议"""
        if source_domain:
            key = f"{source_domain}->{target_domain}"
            if key in self.transfer_library:
                return [self.transfer_library[key]]
            return []

        return list(self.transfer_library.values())

    def suggest_for_content(self, content_type: str) -> List[Dict]:
        """根据内容类型推荐迁移策略"""
        suggestions = {
            "AKO建造志": ["文学->建筑", "纪录片->建筑"],
            "造价说": ["美食->建筑", "科学传播->建筑"],
            "黄昏建筑": ["文学->建筑"],
            "0154技术谈": ["科学传播->建筑"],
            "工地24时": ["纪录片->建筑", "新闻->建筑"],
            "AKO人物": ["新闻->建筑"],
        }

        keys = suggestions.get(content_type, [])
        return [self.transfer_library[k] for k in keys if k in self.transfer_library]
