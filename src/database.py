"""
AKO Media Agent - 数据库管理模块
支持 MySQL / SQLite 数据库连接、建表、ORM基础
"""

import os
import logging
import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

# 尝试导入pymysql，失败则仅支持SQLite
try:
    import pymysql
    from pymysql.cursors import DictCursor
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False
    logger.debug("pymysql未安装，仅支持SQLite模式")


class DatabaseManager:
    """数据库管理器（支持MySQL和SQLite）"""

    def __init__(self, config: Optional[dict] = None):
        """
        初始化数据库连接

        Args:
            config: 数据库配置字典，若不传则从环境变量读取
        """
        self.engine = os.getenv("DB_ENGINE", "sqlite")
        self.config = config
        self._connection = None

        if self.engine == "mysql" and HAS_PYMYSQL:
            self.config = config or {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", 3306)),
                "user": os.getenv("DB_USER", "root"),
                "password": os.getenv("DB_PASSWORD", ""),
                "database": os.getenv("DB_NAME", "ako_media_agent"),
                "charset": "utf8mb4",
                "cursorclass": DictCursor,
            }
            logger.info("使用MySQL数据库")
        else:
            self.engine = "sqlite"
            self._db_path = os.getenv("SQLITE_PATH", os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "ako_media_agent.db"
            ))
            logger.info(f"使用SQLite数据库: {self._db_path}")

    def get_connection(self):
        """获取数据库连接"""
        if self._connection is None:
            if self.engine == "mysql":
                self._connection = pymysql.connect(**self.config)
            else:
                self._connection = sqlite3.connect(self._db_path)
                self._connection.row_factory = sqlite3.Row
            logger.info(f"数据库连接已建立 ({self.engine})")
        return self._connection

    @contextmanager
    def get_cursor(self):
        """获取数据库游标（上下文管理器）"""
        conn = self.get_connection()
        if self.engine == "mysql":
            cursor = conn.cursor()
        else:
            cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            cursor.close()

    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("数据库连接已关闭")

    def _adapt_sql(self, sql: str) -> str:
        """将MySQL SQL转换为SQLite兼容的SQL"""
        if self.engine != "sqlite":
            return sql
        import re
        sql = re.sub(r"COMMENT\s+'[^']*'", "", sql)
        sql = sql.replace("BIGINT AUTO_INCREMENT", "INTEGER")
        sql = re.sub(r"VARCHAR\(\d+\)", "TEXT", sql)
        sql = sql.replace(" JSON ", " TEXT ")
        sql = re.sub(r"\bFLOAT\b", "REAL", sql)
        sql = re.sub(r"\bINT\b", "INTEGER", sql)
        sql = sql.replace("BOOLEAN", "INTEGER")
        sql = re.sub(r"ON UPDATE CURRENT_TIMESTAMP", "", sql)
        sql = re.sub(r"ENGINE\s*=\s*\w+", "", sql)
        sql = re.sub(r"DEFAULT\s+CHARSET\s*=\s*\w+", "", sql)
        sql = re.sub(r"COLLATE\s*=\s*\w+", "", sql)
        sql = re.sub(r",?\s*INDEX\s+\w+\s*\([^)]+\)", "", sql)
        sql = re.sub(r"DATE_SUB\(NOW\(\),\s*INTERVAL\s+(\d+)\s+DAY\)", r"datetime('now', '-\1 days')", sql)
        sql = re.sub(r"DATE_SUB\(NOW\(\),\s*INTERVAL\s+(\d+)\s+HOUR\)", r"datetime('now', '-\1 hours')", sql)
        sql = re.sub(r"DATE_SUB\(CURDATE\(\),\s*INTERVAL\s+(\d+)\s+DAY\)", r"datetime('now', '-\1 days')", sql)
        # Handle %s placeholders in DATE_SUB
        sql = re.sub(r"DATE_SUB\(NOW\(\),\s*INTERVAL\s+%s\s+HOUR\)", r"datetime('now', '-' || ? || ' hours')", sql)
        sql = re.sub(r"DATE_SUB\(NOW\(\),\s*INTERVAL\s+%s\s+DAY\)", r"datetime('now', '-' || ? || ' days')", sql)
        # Convert GROUP_CONCAT(x SEPARATOR ' ') to GROUP_CONCAT(x, ' ')
        sql = re.sub(r"GROUP_CONCAT\((\w+)\s+SEPARATOR\s+'([^']*)'\)", r"GROUP_CONCAT(\1, '\2')", sql)
        sql = re.sub(r"SEPARATOR\s+'[^']*'", "", sql)
        # Convert MySQL %s placeholders to SQLite ?
        sql = sql.replace("%s", "?")
        # Convert NOW() to datetime('now')
        sql = re.sub(r"\bNOW\(\)", "datetime('now')", sql)
        return sql

    def execute(self, sql: str, params=None):
        """执行SQL语句"""
        sql = self._adapt_sql(sql)
        with self.get_cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor

    def fetch_all(self, sql: str, params=None):
        """查询所有结果"""
        sql = self._adapt_sql(sql)
        with self.get_cursor() as cursor:
            cursor.execute(sql, params or ())
            if self.engine == "sqlite":
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            return cursor.fetchall()

    def fetch_one(self, sql: str, params=None):
        """查询单条结果"""
        sql = self._adapt_sql(sql)
        with self.get_cursor() as cursor:
            cursor.execute(sql, params or ())
            if self.engine == "sqlite":
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    return dict(zip(columns, row))
                return None
            return cursor.fetchone()

    def create_tables(self):
        """创建所有数据表"""
        tables = [
            self._create_crawled_data_table(),
            self._create_competitor_data_table(),
            self._create_trend_data_table(),
            self._create_news_data_table(),
            self._create_content_table(),
            self._create_publish_record_table(),
            self._create_performance_table(),
            self._create_strategy_table(),
            self._create_content_dna_table(),
            self._create_failure_cases_table(),
            self._create_reader_evolution_table(),
            self._create_cognition_updates_table(),
            self._create_evolution_insights_table(),
        ]
        logger.info(f"成功创建/验证 {len(tables)} 张数据表")
        return tables

    def _create_crawled_data_table(self):
        """创建爬取数据表"""
        sql = """
        CREATE TABLE IF NOT EXISTS crawled_data (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            platform VARCHAR(20) NOT NULL COMMENT '平台标识',
            content_type VARCHAR(50) COMMENT '内容类型',
            title VARCHAR(500) COMMENT '标题',
            content TEXT COMMENT '内容正文',
            author VARCHAR(100) COMMENT '作者',
            publish_time DATETIME COMMENT '发布时间',
            likes INT DEFAULT 0 COMMENT '点赞数',
            comments INT DEFAULT 0 COMMENT '评论数',
            shares INT DEFAULT 0 COMMENT '转发数',
            favorites INT DEFAULT 0 COMMENT '收藏数',
            tags JSON COMMENT '标签列表',
            url VARCHAR(1000) COMMENT '原始链接',
            data_version INT DEFAULT 1 COMMENT '数据版本号',
            raw_data JSON COMMENT '原始数据',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_platform (platform),
            INDEX idx_publish_time (publish_time),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.execute(sql)
        return "crawled_data"

    def _create_competitor_data_table(self):
        """创建竞品数据表"""
        sql = """
        CREATE TABLE IF NOT EXISTS competitor_data (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            competitor_name VARCHAR(100) NOT NULL COMMENT '竞品名称',
            platform VARCHAR(20) COMMENT '平台',
            content_title VARCHAR(500) COMMENT '内容标题',
            content_url VARCHAR(1000) COMMENT '内容链接',
            publish_date DATE COMMENT '发布日期',
            content_theme VARCHAR(100) COMMENT '内容主题',
            likes INT DEFAULT 0,
            comments INT DEFAULT 0,
            shares INT DEFAULT 0,
            is_viral BOOLEAN DEFAULT FALSE COMMENT '是否爆款(互动>均值3倍)',
            notes TEXT COMMENT '备注',
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_competitor (competitor_name),
            INDEX idx_platform (platform),
            INDEX idx_publish_date (publish_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.execute(sql)
        return "competitor_data"

    def _create_trend_data_table(self):
        """创建趋势数据表"""
        sql = """
        CREATE TABLE IF NOT EXISTS trend_data (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            source VARCHAR(50) NOT NULL COMMENT '数据源(baidu/wechat/douyin/xhs)',
            keyword VARCHAR(200) NOT NULL COMMENT '关键词',
            tier VARCHAR(20) COMMENT '词级(tier1/tier2/tier3/longtail)',
            heat_index FLOAT COMMENT '热度指数',
            rank INT COMMENT '排名',
            related_words JSON COMMENT '关联词',
            trend_data JSON COMMENT '趋势曲线数据',
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_source_keyword (source, keyword),
            INDEX idx_recorded_at (recorded_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.execute(sql)
        return "trend_data"

    def _create_news_data_table(self):
        """创建新闻数据表"""
        sql = """
        CREATE TABLE IF NOT EXISTS news_data (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            source VARCHAR(200) NOT NULL COMMENT '来源',
            title VARCHAR(500) COMMENT '标题',
            summary TEXT COMMENT '摘要(大模型生成)',
            original_content TEXT COMMENT '原文内容',
            url VARCHAR(1000) COMMENT '原文链接',
            publish_time DATETIME COMMENT '发布时间',
            keywords JSON COMMENT '关键词',
            is_policy_change BOOLEAN DEFAULT FALSE COMMENT '是否政策变动',
            alert_sent BOOLEAN DEFAULT FALSE COMMENT '是否已发送告警',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_source (source),
            INDEX idx_publish_time (publish_time),
            INDEX idx_is_policy_change (is_policy_change)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.execute(sql)
        return "news_data"

    def _create_content_table(self):
        """创建内容表"""
        sql = """
        CREATE TABLE IF NOT EXISTS content (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            article_id VARCHAR(100) UNIQUE NOT NULL COMMENT '文章ID',
            column_name VARCHAR(50) COMMENT '所属栏目',
            title VARCHAR(500) COMMENT '标题',
            body TEXT COMMENT '正文(markdown)',
            images JSON COMMENT '配图URL列表',
            tags JSON COMMENT '标签',
            platform VARCHAR(20) COMMENT '目标平台',
            status VARCHAR(20) DEFAULT 'draft' COMMENT '状态: draft/review/published/withdrawn',
            version INT DEFAULT 1 COMMENT '版本号',
            thought_depth_score FLOAT COMMENT '思想厚度评分',
            predicted_engagement JSON COMMENT '预测互动数据',
            review_status VARCHAR(20) DEFAULT 'pending' COMMENT '审核状态',
            review_notes TEXT COMMENT '审核备注',
            scheduled_at DATETIME COMMENT '计划发布时间',
            published_at DATETIME COMMENT '实际发布时间',
            created_by VARCHAR(50) DEFAULT 'ai' COMMENT '创建者',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_article_id (article_id),
            INDEX idx_status (status),
            INDEX idx_platform (platform),
            INDEX idx_column (column_name),
            INDEX idx_scheduled_at (scheduled_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.execute(sql)
        return "content"

    def _create_publish_record_table(self):
        """创建发布记录表"""
        sql = """
        CREATE TABLE IF NOT EXISTS publish_record (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            article_id VARCHAR(100) NOT NULL COMMENT '文章ID',
            platform VARCHAR(20) NOT NULL COMMENT '平台',
            publish_url VARCHAR(1000) COMMENT '发布链接',
            publish_time DATETIME COMMENT '发布时间',
            status VARCHAR(20) COMMENT '状态: success/failed/withdrawn',
            error_message TEXT COMMENT '错误信息',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_article_id (article_id),
            INDEX idx_platform (platform),
            INDEX idx_publish_time (publish_time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.execute(sql)
        return "publish_record"

    def _create_performance_table(self):
        """创建表现追踪表"""
        sql = """
        CREATE TABLE IF NOT EXISTS performance_data (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            article_id VARCHAR(100) NOT NULL COMMENT '文章ID',
            platform VARCHAR(20) NOT NULL COMMENT '平台',
            reads INT DEFAULT 0 COMMENT '阅读量',
            likes INT DEFAULT 0 COMMENT '点赞数',
            comments INT DEFAULT 0 COMMENT '评论数',
            shares INT DEFAULT 0 COMMENT '转发数',
            favorites INT DEFAULT 0 COMMENT '收藏数',
            completion_rate FLOAT COMMENT '完读率',
            follower_growth INT DEFAULT 0 COMMENT '粉丝增长',
            negative_ratio FLOAT COMMENT '负面评论比例',
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_article_id (article_id),
            INDEX idx_platform (platform),
            INDEX idx_recorded_at (recorded_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.execute(sql)
        return "performance_data"

    def _create_strategy_table(self):
        """创建策略调整表"""
        sql = """
        CREATE TABLE IF NOT EXISTS strategy_adjustments (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            adjustment_type VARCHAR(50) NOT NULL COMMENT '调整类型',
            dimension VARCHAR(100) COMMENT '调整维度',
            old_value JSON COMMENT '旧值',
            new_value JSON COMMENT '新值',
            reason TEXT COMMENT '调整原因',
            auto_adjusted BOOLEAN DEFAULT FALSE COMMENT '是否自动调整',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_type (adjustment_type),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.execute(sql)
        return "strategy_adjustments"

    def _create_content_dna_table(self):
        """创建内容DNA表"""
        sql = """
        CREATE TABLE IF NOT EXISTS content_dna (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            content_id VARCHAR(100) NOT NULL COMMENT '关联内容ID',
            structure_genes JSON COMMENT '结构基因',
            style_genes JSON COMMENT '风格基因',
            thought_genes JSON COMMENT '思想基因',
            performance_genes JSON COMMENT '表现基因',
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_content_id (content_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        self.execute(sql)
        return "content_dna"

    def _create_failure_cases_table(self):
        """创建失败案例表"""
        sql = """
        CREATE TABLE IF NOT EXISTS failure_cases (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            content_id VARCHAR(100) COMMENT '关联内容ID',
            failure_type VARCHAR(50) NOT NULL COMMENT '失败类型',
            failure_pattern JSON COMMENT '失败模式',
            context JSON COMMENT '上下文',
            lesson TEXT COMMENT '教训',
            severity VARCHAR(20) COMMENT '严重程度',
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_failure_type (failure_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        self.execute(sql)
        return "failure_cases"

    def _create_reader_evolution_table(self):
        """创建读者画像进化表"""
        sql = """
        CREATE TABLE IF NOT EXISTS reader_evolution (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            segment_name VARCHAR(100) NOT NULL COMMENT '读者分群名称',
            interests JSON COMMENT '兴趣列表',
            engagement_pattern VARCHAR(200) COMMENT '互动模式',
            content_preference TEXT COMMENT '内容偏好',
            drift_detected BOOLEAN DEFAULT FALSE COMMENT '是否检测到漂移',
            drift_details JSON COMMENT '漂移详情',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_segment (segment_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        self.execute(sql)
        return "reader_evolution"

    def _create_cognition_updates_table(self):
        """创建AKO认知更新表"""
        sql = """
        CREATE TABLE IF NOT EXISTS cognition_updates (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(50) NOT NULL COMMENT '认知类别',
            topic VARCHAR(200) NOT NULL COMMENT '主题',
            old_belief TEXT COMMENT '旧认知',
            new_belief TEXT COMMENT '新认知',
            source TEXT COMMENT '来源',
            confidence FLOAT DEFAULT 0.5 COMMENT '置信度',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_category (category)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        self.execute(sql)
        return "cognition_updates"

    def _create_evolution_insights_table(self):
        """创建进化洞察表"""
        sql = """
        CREATE TABLE IF NOT EXISTS evolution_insights (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            insight_type VARCHAR(50) NOT NULL COMMENT '洞察类型',
            source_module VARCHAR(100) COMMENT '来源模块',
            content JSON COMMENT '洞察内容',
            confidence FLOAT DEFAULT 0.5 COMMENT '置信度',
            applied BOOLEAN DEFAULT FALSE COMMENT '是否已应用',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_type (insight_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        self.execute(sql)
        return "evolution_insights"


# 线程本地数据库实例（解决 SQLite 跨线程安全问题）
_local = threading.local()


def get_db() -> DatabaseManager:
    """获取当前线程的数据库实例（线程隔离）"""
    if not hasattr(_local, 'db_instance') or _local.db_instance is None:
        _local.db_instance = DatabaseManager()
    return _local.db_instance


def init_db():
    """初始化数据库（创建表）"""
    db = get_db()
    db.create_tables()
    logger.info("数据库初始化完成")
    return db
