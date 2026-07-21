"""
失败案例库
结构化存储失败内容的"失败结构"，用于预警和避坑
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.database import get_db

logger = logging.getLogger(__name__)


class FailureCaseLibrary:
    """
    失败案例库

    功能:
    - 结构化记录失败内容的"失败结构"
    - 新内容生成前自动匹配失败模式
    - 定期分析失败共性，生成"避坑指南"
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.db = get_db()

        # 失败类型定义
        self.failure_types = {
            "low_engagement": "低互动（阅读高但点赞/评论极低）",
            "negative_feedback": "负面反馈（负面评论比例>30%）",
            "brand_mismatch": "品牌不符（不符合AKO调性）",
            "fact_error": "事实错误（技术参数/数据有误）",
            "hollow_content": "空洞内容（禁用词过多、缺乏具体性）",
            "timing_miss": "时机不当（在敏感时期发布不适宜内容）",
        }

        logger.info("FailureCaseLibrary 初始化完成")

    def record_failure(self, content_id: str, failure_type: str,
                       pattern: Dict, lesson: str,
                       avoidance_rule: str = "") -> Dict:
        """
        记录失败案例

        Args:
            content_id: 内容ID
            failure_type: 失败类型
            pattern: 失败模式 {trigger, context, consequence}
            lesson: 教训总结
            avoidance_rule: 规避规则

        Returns:
            失败案例记录
        """
        case = {
            "content_id": content_id,
            "failure_type": failure_type,
            "failure_pattern": pattern,
            "lesson": lesson,
            "avoidance_rule": avoidance_rule,
            "recorded_at": datetime.now().isoformat(),
        }

        # 保存到数据库
        if self.db.engine == "sqlite":
            placeholders = ", ".join(["?" for _ in range(4)])
        else:
            placeholders = ", ".join(["%s" for _ in range(4)])

        sql = f"""
        INSERT INTO failure_cases (content_id, failure_type, case_data, recorded_at)
        VALUES ({placeholders})
        """
        params = (
            content_id,
            failure_type,
            json.dumps(case, ensure_ascii=False),
            datetime.now().isoformat(),
        )
        self.db.execute(sql, params)
        logger.info(f"记录失败案例: {content_id} ({failure_type})")

        return case

    def check_risk(self, content_text: str, title: str = "") -> List[Dict]:
        """
        检查新内容的失败风险
        匹配历史失败模式

        Args:
            content_text: 内容文本
            title: 标题

        Returns:
            风险预警列表
        """
        risks = []

        # 检查空洞内容
        hollow_indicators = ["解决方案", "赋能", "打造", "引领", "生态", "闭环"]
        hollow_count = sum(1 for w in hollow_indicators if w in content_text)
        if hollow_count >= 3:
            risks.append({
                "risk_type": "hollow_content",
                "severity": "high",
                "detail": f"检测到{hollow_count}个空洞词汇: {[w for w in hollow_indicators if w in content_text]}",
                "suggestion": "用具体数字、场景、人物替代抽象概念",
            })

        # 检查缺乏具体性
        has_numbers = any(c.isdigit() for c in content_text)
        if not has_numbers and len(content_text) > 200:
            risks.append({
                "risk_type": "low_specificity",
                "severity": "medium",
                "detail": "长文中缺乏具体数字",
                "suggestion": "添加造价数据、技术参数、时间节点等具体信息",
            })

        # 检查缺乏人的在场
        person_markers = ["我", "师傅", "工友", "老周", "操作员"]
        has_person = any(m in content_text for m in person_markers)
        if not has_person and len(content_text) > 300:
            risks.append({
                "risk_type": "no_person_presence",
                "severity": "medium",
                "detail": "文中缺乏真实人物",
                "suggestion": "加入现场人物的对话、动作或感受",
            })

        # 检查标题
        if title and not any(c.isdigit() for c in title):
            risks.append({
                "risk_type": "title_no_number",
                "severity": "low",
                "detail": "标题不含数字",
                "suggestion": "含数字的标题打开率通常高20%",
            })

        return risks

    def get_avoidance_rules(self) -> List[Dict]:
        """获取所有避坑规则"""
        if self.db.engine == "sqlite":
            sql = "SELECT case_data FROM failure_cases ORDER BY recorded_at DESC LIMIT 100"
        else:
            sql = "SELECT case_data FROM failure_cases ORDER BY recorded_at DESC LIMIT 100"

        rows = self.db.fetch_all(sql)
        rules = []
        for row in rows:
            try:
                case = json.loads(row["case_data"])
                if case.get("avoidance_rule"):
                    rules.append({
                        "rule": case["avoidance_rule"],
                        "lesson": case.get("lesson", ""),
                        "failure_type": case.get("failure_type", ""),
                    })
            except (json.JSONDecodeError, KeyError):
                continue

        return rules

    def analyze_failure_patterns(self) -> Dict:
        """分析失败案例的共性模式"""
        if self.db.engine == "sqlite":
            sql = "SELECT case_data FROM failure_cases"
        else:
            sql = "SELECT case_data FROM failure_cases"

        rows = self.db.fetch_all(sql)
        if not rows:
            return {"total_cases": 0, "patterns": {}}

        type_counts = {}
        trigger_counts = {}
        lessons = []

        for row in rows:
            try:
                case = json.loads(row["case_data"])
                ft = case.get("failure_type", "unknown")
                type_counts[ft] = type_counts.get(ft, 0) + 1

                trigger = case.get("failure_pattern", {}).get("trigger", "")
                if trigger:
                    trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1

                if case.get("lesson"):
                    lessons.append(case["lesson"])
            except (json.JSONDecodeError, KeyError):
                continue

        return {
            "total_cases": len(rows),
            "type_distribution": type_counts,
            "top_triggers": sorted(trigger_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "lessons_summary": lessons[:20],
        }
