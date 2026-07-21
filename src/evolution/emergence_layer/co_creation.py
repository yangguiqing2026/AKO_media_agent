"""读者共创 - 从单向输出到双向进化"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ReaderCoCreation:
    """
    读者共创机制

    从单向输出到双向进化
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        logger.info("ReaderCoCreation 初始化完成")

    def co_create(self, reader_input: List[Dict]) -> List[Dict]:
        """
        基于读者输入共创内容

        Args:
            reader_input: 读者输入列表 [{type: "question/comment/idea", text: "...", source: "..."}]

        Returns:
            共创内容建议
        """
        if not reader_input:
            return []

        suggestions = []

        for inp in reader_input:
            text = inp.get("text", "")
            input_type = inp.get("type", "comment")

            if input_type == "question":
                suggestion = self._question_to_content(text)
            elif input_type == "idea":
                suggestion = self._idea_to_content(text)
            else:
                suggestion = self._comment_to_content(text)

            if suggestion:
                suggestions.append(suggestion)

        logger.info(f"共创建议生成: {len(suggestions)} 条")
        return suggestions

    def _question_to_content(self, question: str) -> Dict:
        """将读者问题转化为内容"""
        if "造价" in question or "多少钱" in question:
            return {
                "content_idea": "《读者问造价》系列",
                "column": "造价说",
                "description": f"针对读者问题'{question[:50]}'做一期透明造价解读",
                "evolution": "从'AKO讲造价'到'读者问、AKO答'",
            }
        elif "怎么" in question or "如何" in question:
            return {
                "content_idea": "《技术诚实》回应系列",
                "column": "0154技术谈",
                "description": f"针对读者技术问题'{question[:50]}'做深度解答",
                "evolution": "从'AKO讲技术'到'读者驱动的技术解读'",
            }
        else:
            return {
                "content_idea": "《读者来信》栏目",
                "column": "AKO建造志",
                "description": f"回应读者问题'{question[:50]}'",
                "evolution": "建立读者对话机制",
            }

    def _idea_to_content(self, idea: str) -> Dict:
        """将读者创意转化为内容"""
        return {
            "content_idea": "《读者的建筑》栏目",
            "column": "AKO建造志",
            "description": f"基于读者创意'{idea[:50]}'共创内容",
            "evolution": "从'AKO讲述'到'AKO与读者共同讲述'",
        }

    def _comment_to_content(self, comment: str) -> Dict:
        """从评论中发现内容机会"""
        if any(k in comment for k in ["想看", "希望", "能不能"]):
            return {
                "content_idea": "需求响应内容",
                "column": "待定",
                "description": f"回应读者需求'{comment[:50]}'",
                "evolution": "读者需求驱动内容生产",
            }
        return None
