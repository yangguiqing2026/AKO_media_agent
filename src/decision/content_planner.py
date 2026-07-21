"""
内容规划器
规则引擎：热点响应/竞品跟进/常青内容/品牌事件/政策响应
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from src.database import get_db

logger = logging.getLogger(__name__)


class ContentPlanner:
    """
    内容规划器

    功能:
    - 热点响应（2小时内）
    - 竞品跟进（48小时内）
    - 常青内容（按排期）
    - 品牌事件（自动触发）
    - 政策响应（4小时内）
    """

    def __init__(self, config: dict):
        self.config = config
        decision_config = config.get("layers", {}).get("decision", {})
        planner_config = decision_config.get("content_planner", {})
        self.rules = planner_config.get("rules", {})
        self.db = get_db()

        # 内容栏目
        self.columns = [
            "AKO建造志", "造价说", "黄昏建筑",
            "0154技术谈", "工地24时", "AKO人物",
        ]

        logger.info("ContentPlanner 初始化完成")

    def generate_daily_plan(self) -> Dict:
        """
        生成每日内容计划

        Returns:
            内容计划
        """
        plan = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tasks": [],
        }

        # 检查热点响应
        hot_topics = self._check_hot_topics()
        if hot_topics:
            plan["tasks"].extend(hot_topics)

        # 检查竞品跟进
        competitor_follow = self._check_competitor_follow()
        if competitor_follow:
            plan["tasks"].extend(competitor_follow)

        # 检查常青内容排期
        evergreen = self._check_evergreen_schedule()
        if evergreen:
            plan["tasks"].extend(evergreen)

        # 检查政策响应
        policy_news = self._check_policy_news()
        if policy_news:
            plan["tasks"].extend(policy_news)

        logger.info(f"生成内容计划: {len(plan['tasks'])} 个任务")

        # 持久化到数据库
        self._save_plan_to_db(plan)
        return plan

    def generate_weekly_plan(self) -> Dict:
        """生成7日内容排期表"""
        plan = {
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "daily_plans": [],
        }

        for i in range(7):
            date = datetime.now() + timedelta(days=i)
            daily = self.generate_daily_plan()
            daily["date"] = date.strftime("%Y-%m-%d")
            plan["daily_plans"].append(daily)

        return plan

    def generate_monthly_plan(self) -> Dict:
        """生成30日内容排期表"""
        plan = {
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "summary": {},
            "weekly_plans": [],
        }

        for week in range(4):
            weekly = self.generate_weekly_plan()
            plan["weekly_plans"].append(weekly)

        return plan

    def _check_hot_topics(self) -> List[Dict]:
        """检查热点话题"""
        # TODO: 从趋势数据中检测高热度话题
        sql = """
        SELECT keyword, heat_index FROM trend_data
        WHERE recorded_at >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
        AND heat_index > 80
        ORDER BY heat_index DESC
        LIMIT 5
        """
        results = self.db.fetch_all(sql)

        tasks = []
        for r in results:
            tasks.append({
                "type": "hot_topic",
                "priority": "high",
                "topic": r["keyword"],
                "heat_index": r["heat_index"],
                "response_deadline": "2小时内",
                "action": "生成选题建议+初稿",
            })

        return tasks

    def _check_competitor_follow(self) -> List[Dict]:
        """检查竞品爆款跟进"""
        sql = """
        SELECT competitor_name, content_title, content_theme
        FROM competitor_data
        WHERE is_viral = TRUE
        AND recorded_at >= DATE_SUB(NOW(), INTERVAL 48 HOUR)
        """
        results = self.db.fetch_all(sql)

        tasks = []
        for r in results:
            tasks.append({
                "type": "competitor_follow",
                "priority": "medium",
                "competitor": r["competitor_name"],
                "topic": r["content_title"],
                "response_deadline": "48小时内",
                "action": "生成差异化版本",
            })

        return tasks

    def _check_evergreen_schedule(self) -> List[Dict]:
        """检查常青内容排期"""
        # 根据栏目频率检查是否需要发布
        return [
            {
                "type": "evergreen",
                "column": "AKO建造志",
                "frequency": "周更",
                "action": "检查本周是否已发布",
            },
        ]

    def _check_policy_news(self) -> List[Dict]:
        """检查政策新闻"""
        sql = """
        SELECT title, url FROM news_data
        WHERE is_policy_change = TRUE
        AND alert_sent = FALSE
        AND created_at >= DATE_SUB(NOW(), INTERVAL 4 HOUR)
        """
        results = self.db.fetch_all(sql)

        tasks = []
        for r in results:
            tasks.append({
                "type": "policy_response",
                "priority": "high",
                "title": r["title"],
                "response_deadline": "4小时内",
                "action": "生成政策解读文章",
            })

        return tasks

    def _save_plan_to_db(self, plan: Dict):
        """将内容计划持久化到content表"""
        for task in plan.get("tasks", []):
            task_type = task.get("type", "evergreen")
            topic = task.get("topic", "") or task.get("column", "") or task.get("title", "")
            column = task.get("column", "")

            if not column:
                if task_type == "hot_topic":
                    column = "AKO建造志"
                elif task_type == "competitor_follow":
                    column = "造价说"
                elif task_type == "policy_response":
                    column = "0154技术谈"
                else:
                    column = self.columns[len(plan["tasks"]) % len(self.columns)]

            if task_type == "hot_topic":
                title = f"热点响应：{topic}——AKO视角解读"
            elif task_type == "competitor_follow":
                title = f"竞品跟进：{topic}的差异化思考"
            elif task_type == "policy_response":
                title = f"政策解读：{topic}"
            else:
                title = f"{column}：{plan['date']}定期内容"

            article_id = f"plan-{plan['date']}-{uuid.uuid4().hex[:8]}"

            try:
                self.db.execute(
                    """INSERT INTO content (article_id, column_name, title, body, platform, status, created_by)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        article_id,
                        column,
                        title,
                        f"# {title}\n\n**类型**: {task_type}\n**优先级**: {task.get('priority', 'medium')}\n**话题**: {topic}\n**响应时限**: {task.get('response_deadline', '按计划')}\n**行动**: {task.get('action', '生成内容')}\n",
                        "wechat",
                        "draft",
                        "ai",
                    ),
                )
            except Exception as e:
                logger.warning(f"保存内容计划失败: {e}")

        logger.info(f"已保存 {len(plan.get('tasks', []))} 条内容计划到数据库")
