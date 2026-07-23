"""
AKO Media Agent - 主入口
AKO品牌自主媒体数据智能体

核心能力:
- 自主数据采集: 7×24小时抓取社交媒体、行业新闻、竞品动态
- 智能分析: NLP情感分析、主题聚类、关键词提取、互动预测
- 数据驱动决策: 自动生成内容策略、选题、发布时间
- 自动执行: 生成文案、配图、发布到各平台
- 反馈优化: 追踪表现数据，自动调整策略参数

核心原则: 思想厚度 > 传播效率，品牌高度 > 流量规模
"""

import argparse
import logging
import os
import sys
from datetime import datetime

import yaml

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, get_db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("AKO_media_agent")


class AKOMediaAgent:
    """AKO Media Agent 主类"""

    def __init__(self, config_path: str = None):
        """
        初始化 AKO Media Agent

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "AKO_media_agent_config.yaml"
        )
        self.config = self._load_config()
        self.db = None

        # 五层架构模块
        self.crawler = None
        self.analyzer = None
        self.decision_engine = None
        self.executor = None
        self.feedback_loop = None

        # 进化层模块
        self.evolution = None

    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f"配置文件加载成功: {self.config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"配置文件解析失败: {e}")
            raise

    def initialize(self):
        """初始化所有模块"""
        logger.info("=" * 60)
        logger.info("AKO Media Agent v1.2 初始化中...")
        logger.info("=" * 60)

        # 初始化数据库
        self.db = init_db()
        logger.info("[OK] 数据库初始化完成")

        # 初始化 Layer 1: 数据收集层
        if self.config.get("layers", {}).get("crawler", {}).get("enabled"):
            self._init_crawler()
            logger.info("[OK] Layer 1: 数据收集层初始化完成")

        # 初始化 Layer 2: 智能分析层
        if self.config.get("layers", {}).get("analysis", {}).get("enabled"):
            self._init_analyzer()
            logger.info("[OK] Layer 2: 智能分析层初始化完成")

        # 初始化 Layer 3: 决策引擎
        if self.config.get("layers", {}).get("decision", {}).get("enabled"):
            self._init_decision()
            logger.info("[OK] Layer 3: 决策引擎初始化完成")

        # 初始化 Layer 4: 执行层
        if self.config.get("layers", {}).get("execution", {}).get("enabled"):
            self._init_executor()
            logger.info("[OK] Layer 4: 执行层初始化完成")

        # 初始化 Layer 5: 反馈闭环
        if self.config.get("layers", {}).get("feedback", {}).get("enabled"):
            self._init_feedback()
            logger.info("[OK] Layer 5: 反馈闭环初始化完成")

        # 初始化 Evolution Layer: 进化层
        self._init_evolution()
        logger.info("[OK] Evolution Layer: 自我学习进化层初始化完成")

        logger.info("=" * 60)
        logger.info("AKO Media Agent 初始化完成")
        logger.info("=" * 60)

    def _init_crawler(self):
        """初始化数据收集层"""
        try:
            from src.crawler.media_crawler import MediaCrawlerWrapper
            from src.crawler.news_monitor import NewsMonitor
            from src.crawler.competitor_tracker import CompetitorTracker
            from src.crawler.trend_detector import TrendDetector

            self.crawler = {
                "media_crawler": MediaCrawlerWrapper(self.config),
                "news_monitor": NewsMonitor(self.config),
                "competitor_tracker": CompetitorTracker(self.config),
                "trend_detector": TrendDetector(self.config),
            }
        except ImportError as e:
            logger.warning(f"数据收集层初始化失败（缺少依赖）: {e}")
            self.crawler = None

    def _init_analyzer(self):
        """初始化智能分析层"""
        try:
            from src.analysis.sentiment_analyzer import SentimentAnalyzer
            from src.analysis.topic_cluster import TopicCluster
            from src.analysis.keyword_extractor import KeywordExtractor
            from src.analysis.engagement_predictor import EngagementPredictor
            from src.analysis.gap_analyzer import GapAnalyzer

            self.analyzer = {
                "sentiment": SentimentAnalyzer(self.config),
                "topic": TopicCluster(self.config),
                "keyword": KeywordExtractor(self.config),
                "engagement": EngagementPredictor(self.config),
                "gap": GapAnalyzer(self.config),
            }
        except ImportError as e:
            logger.warning(f"智能分析层初始化失败（缺少依赖）: {e}")
            self.analyzer = None

    def _init_decision(self):
        """初始化决策引擎"""
        try:
            from src.decision.content_planner import ContentPlanner
            from src.decision.title_optimizer import TitleOptimizer
            from src.decision.timing_optimizer import TimingOptimizer

            self.decision_engine = {
                "planner": ContentPlanner(self.config),
                "title": TitleOptimizer(self.config),
                "timing": TimingOptimizer(self.config),
            }
        except ImportError as e:
            logger.warning(f"决策引擎初始化失败（缺少依赖）: {e}")
            self.decision_engine = None

    def _init_executor(self):
        """初始化执行层"""
        try:
            from src.execution.copywriter import Copywriter
            from src.execution.visual_generator import VisualGenerator
            from src.execution.publisher import Publisher

            self.executor = {
                "copywriter": Copywriter(self.config),
                "visual": VisualGenerator(self.config),
                "publisher": Publisher(self.config),
            }
        except ImportError as e:
            logger.warning(f"执行层初始化失败（缺少依赖）: {e}")
            self.executor = None

    def _init_feedback(self):
        """初始化反馈闭环"""
        try:
            from src.feedback.performance_tracker import PerformanceTracker
            from src.feedback.strategy_adjuster import StrategyAdjuster
            from src.feedback.rollback_manager import RollbackManager

            self.feedback_loop = {
                "tracker": PerformanceTracker(self.config),
                "adjuster": StrategyAdjuster(self.config),
                "rollback": RollbackManager(self.config),
            }
        except ImportError as e:
            logger.warning(f"反馈闭环初始化失败（缺少依赖）: {e}")
            self.feedback_loop = None

    def _init_evolution(self):
        """初始化进化层"""
        try:
            from src.evolution.memory_layer.content_dna import ContentDNA
            from src.evolution.memory_layer.failure_case import FailureCaseLibrary
            from src.evolution.memory_layer.reader_evolution import ReaderEvolution
            from src.evolution.memory_layer.cognition_graph import AKOCognitionGraph
            from src.evolution.learning_layer.performance_learner import PerformanceDeepLearning
            from src.evolution.learning_layer.feedback_learner import FeedbackSemanticLearning
            from src.evolution.learning_layer.competitor_learner import CompetitorPatternLearning
            from src.evolution.learning_layer.knowledge_graph import IndustryKnowledgeGraph
            from src.evolution.emergence_layer.content_discovery import ContentFormDiscovery
            from src.evolution.emergence_layer.cross_domain import CrossDomainTransfer
            from src.evolution.emergence_layer.auto_tool import AutoToolDevelopment
            from src.evolution.emergence_layer.co_creation import ReaderCoCreation

            self.evolution = {
                # 记忆层
                "content_dna": ContentDNA(self.config),
                "failure_cases": FailureCaseLibrary(self.config),
                "reader_evolution": ReaderEvolution(self.config),
                "cognition_graph": AKOCognitionGraph(self.config),
                # 学习层
                "performance_learner": PerformanceDeepLearning(self.config),
                "feedback_learner": FeedbackSemanticLearning(self.config),
                "competitor_learner": CompetitorPatternLearning(self.config),
                "knowledge_graph": IndustryKnowledgeGraph(self.config),
                # 涌现层
                "content_discovery": ContentFormDiscovery(self.config),
                "cross_domain": CrossDomainTransfer(self.config),
                "auto_tool": AutoToolDevelopment(self.config),
                "co_creation": ReaderCoCreation(self.config),
            }
        except ImportError as e:
            logger.warning(f"进化层初始化失败（缺少依赖）: {e}")
            self.evolution = None

    # =========================================================================
    # 核心操作方法
    # =========================================================================

    def run_crawl(self, platform: str = None, full: bool = False):
        """运行数据采集"""
        logger.info(f"开始数据采集: platform={platform or 'all'}, full={full}")
        if self.crawler:
            if full:
                self.crawler["media_crawler"].crawl_all_platforms()
            elif platform:
                self.crawler["media_crawler"].crawl_platform(platform)
            self.crawler["news_monitor"].scan_news()
            self.crawler["trend_detector"].detect_trends()

    def run_analysis(self):
        """运行智能分析"""
        logger.info("开始智能分析...")
        if self.analyzer:
            self.analyzer["sentiment"].analyze_batch()
            self.analyzer["topic"].cluster_topics()
            self.analyzer["keyword"].extract_keywords()
            self.analyzer["gap"].analyze_gaps()

    def run_decision(self):
        """运行决策引擎"""
        logger.info("开始生成内容策略...")
        if self.decision_engine:
            plan = self.decision_engine["planner"].generate_daily_plan()
            titles = self.decision_engine["title"].optimize_titles(plan)
            timing = self.decision_engine["timing"].optimize_timing(titles)
            return timing

    def run_publish(self, platform: str = None, stage: str = "review"):
        """运行发布流程"""
        logger.info(f"开始发布流程: platform={platform or 'all'}, stage={stage}")
        if self.executor:
            self.executor["publisher"].publish_pending(platform=platform, stage=stage)

    def run_evolution(self):
        """运行进化层"""
        logger.info("开始运行进化层...")
        if not self.evolution:
            logger.warning("进化层未初始化")
            return

        # 记忆层：提取内容DNA
        logger.info("[记忆层] 提取内容DNA...")
        contents = self.db.fetch_all(
            "SELECT * FROM content WHERE status='published' ORDER BY published_at DESC LIMIT 50"
        )
        for content in contents:
            self.evolution["content_dna"].extract_dna(
                content_id=content.get("article_id", ""),
                title=content.get("title", ""),
                body=content.get("body", "") or "",
                performance=content,
            )

        # 记忆层：更新读者画像
        logger.info("[记忆层] 更新读者画像...")
        self.evolution["reader_evolution"].evolve(behavior_data=[])

        # 记忆层：更新认知图谱
        logger.info("[记忆层] 更新AKO认知图谱...")
        for c in contents[:10]:
            self.evolution["cognition_graph"].update(
                new_content=c.get("title", "")
            )

        # 学习层：分析表现数据
        logger.info("[学习层] 分析表现数据...")
        perf_data = self.db.fetch_all(
            "SELECT * FROM performance_data ORDER BY recorded_at DESC LIMIT 50"
        )
        for perf in perf_data:
            self.evolution["performance_learner"].analyze(
                content_dna={}, performance=perf
            )

        # 学习层：知识图谱构建
        logger.info("[学习层] 构建行业知识图谱...")
        crawled = self.db.fetch_all(
            "SELECT title, content FROM crawled_data ORDER BY created_at DESC LIMIT 100"
        )
        if crawled:
            for r in crawled[:50]:
                text = (r.get("title", "") or "") + " " + (r.get("content", "") or "")[:200]
                self.evolution["knowledge_graph"].expand(text)

        # 涌现层：发现新内容形态
        logger.info("[涌现层] 发现新内容形态...")
        self.evolution["content_discovery"].discover(
            performance_data=perf_data[:20] if perf_data else []
        )

        # 涌现层：跨领域迁移
        logger.info("[涌现层] 跨领域迁移分析...")
        self.evolution["cross_domain"].transfer(
            source_domain="装配式建筑", target_domain="建筑"
        )

        logger.info("进化层运行完成")

    def run_feedback(self, weekly: bool = False, monthly: bool = False):
        """运行反馈闭环"""
        logger.info("开始反馈闭环...")
        if self.feedback_loop:
            if weekly:
                self.feedback_loop["tracker"].generate_weekly_report()
            elif monthly:
                self.feedback_loop["tracker"].generate_monthly_report()
                self.feedback_loop["adjuster"].adjust_strategy()
            self.feedback_loop["rollback"].check_anomalies()

    def run_full_pipeline(self):
        """运行完整流水线：采集→分析→决策→执行→反馈→进化"""
        logger.info("=" * 60)
        logger.info("开始运行完整流水线...")
        logger.info("=" * 60)

        # Step 1: 数据采集
        logger.info(">>> Step 1/6: 数据采集")
        self.run_crawl()

        # Step 2: 智能分析
        logger.info(">>> Step 2/6: 智能分析")
        self.run_analysis()

        # Step 3: 决策引擎
        logger.info(">>> Step 3/6: 决策引擎")
        content_plan = self.run_decision()

        # Step 4: 执行发布
        logger.info(">>> Step 4/6: 执行发布")
        self.run_publish(stage="draft")

        # Step 5: 反馈闭环
        logger.info(">>> Step 5/6: 反馈闭环")
        self.run_feedback(weekly=True)

        # Step 6: 进化层
        logger.info(">>> Step 6/6: 自我学习进化")
        self.run_evolution()

        logger.info("=" * 60)
        logger.info("完整流水线运行完成！")
        logger.info("=" * 60)

    def get_status(self) -> dict:
        """获取系统状态"""
        return {
            "version": self.config.get("app", {}).get("version", "1.2.0"),
            "environment": self.config.get("app", {}).get("environment", "development"),
            "layers": {
                "crawler": self.crawler is not None,
                "analyzer": self.analyzer is not None,
                "decision": self.decision_engine is not None,
                "executor": self.executor is not None,
                "feedback": self.feedback_loop is not None,
                "evolution": self.evolution is not None,
            },
            "timestamp": datetime.now().isoformat(),
        }

    def shutdown(self):
        """关闭系统"""
        logger.info("AKO Media Agent 正在关闭...")
        if self.db:
            self.db.close()
        logger.info("AKO Media Agent 已关闭")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AKO Media Agent - AKO品牌自主媒体数据智能体",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
命令示例:
  python src/main.py start              # 启动所有服务
  python src/main.py crawl --full       # 全量数据采集
  python src/main.py analyze            # 运行智能分析
  python src/main.py publish --platform wechat  # 发布到公众号
  python src/main.py feedback --weekly  # 生成周报
  python src/main.py status             # 查看系统状态
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # start 命令
    subparsers.add_parser("start", help="启动所有服务")

    # crawl 命令
    crawl_parser = subparsers.add_parser("crawl", help="运行数据采集")
    crawl_parser.add_argument("--platform", type=str, help="目标平台")
    crawl_parser.add_argument("--full", action="store_true", help="全量采集")

    # analyze 命令
    subparsers.add_parser("analyze", help="运行智能分析")

    # decide 命令
    subparsers.add_parser("decide", help="运行决策引擎")

    # publish 命令
    publish_parser = subparsers.add_parser("publish", help="运行发布流程")
    publish_parser.add_argument("--platform", type=str, help="目标平台")
    publish_parser.add_argument("--stage", type=str, default="review",
                                choices=["draft", "review", "publish"],
                                help="发布阶段")

    # feedback 命令
    feedback_parser = subparsers.add_parser("feedback", help="运行反馈闭环")
    feedback_parser.add_argument("--weekly", action="store_true", help="生成周报")
    feedback_parser.add_argument("--monthly", action="store_true", help="生成月报")

    # evolve 命令
    subparsers.add_parser("evolve", help="运行进化层")

    # status 命令
    subparsers.add_parser("status", help="查看系统状态")

    # init-db 命令
    subparsers.add_parser("init-db", help="初始化数据库")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv("secrets.env")
    except ImportError:
        pass

    # 创建Agent实例
    agent = AKOMediaAgent()

    try:
        if args.command == "init-db":
            init_db()
            logger.info("数据库初始化完成")
            return

        agent.initialize()

        if args.command == "start":
            logger.info("启动完整流水线...")
            agent.run_full_pipeline()

        elif args.command == "crawl":
            agent.run_crawl(
                platform=getattr(args, "platform", None),
                full=getattr(args, "full", False)
            )

        elif args.command == "analyze":
            agent.run_analysis()

        elif args.command == "decide":
            agent.run_decision()

        elif args.command == "publish":
            agent.run_publish(
                platform=getattr(args, "platform", None),
                stage=getattr(args, "stage", "review")
            )

        elif args.command == "feedback":
            agent.run_feedback(
                weekly=getattr(args, "weekly", False),
                monthly=getattr(args, "monthly", False)
            )

        elif args.command == "evolve":
            agent.run_evolution()

        elif args.command == "status":
            status = agent.get_status()
            print("\n" + "=" * 50)
            print("AKO Media Agent 状态")
            print("=" * 50)
            for key, value in status.items():
                print(f"  {key}: {value}")
            print("=" * 50)

    except KeyboardInterrupt:
        logger.info("收到中断信号，正在退出...")
    except Exception as e:
        logger.error(f"运行错误: {e}", exc_info=True)
    finally:
        agent.shutdown()


if __name__ == "__main__":
    main()
