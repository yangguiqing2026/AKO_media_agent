# -*- coding: utf-8 -*-
"""
数据库模块单元测试
"""
import os
import sys
import unittest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import DatabaseManager, get_db


class TestDatabaseManager(unittest.TestCase):
    """测试 DatabaseManager"""

    def setUp(self):
        """每个测试前执行"""
        # 使用临时数据库文件
        self.db_path = ":memory:"
        os.environ["DB_ENGINE"] = "sqlite"

    def test_init_sqlite(self):
        """测试 SQLite 初始化"""
        db = DatabaseManager()
        self.assertEqual(db.engine, "sqlite")

    def test_get_connection(self):
        """测试获取数据库连接"""
        db = DatabaseManager()
        conn = db.get_connection()
        self.assertIsNotNone(conn)
        db.close()

    def test_create_tables(self):
        """测试建表"""
        db = DatabaseManager()
        tables = db.create_tables()
        self.assertEqual(len(tables), 13)
        db.close()

    def test_fetch_all(self):
        """测试查询所有结果"""
        db = DatabaseManager()
        db.create_tables()
        db.execute("INSERT INTO content (article_id, title, platform) VALUES (?, ?, ?)",
                   ("test_001", "测试标题", "wechat"))
        results = db.fetch_all("SELECT * FROM content WHERE article_id = ?", ("test_001",))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "测试标题")
        db.close()

    def test_fetch_one(self):
        """测试查询单条结果"""
        db = DatabaseManager()
        db.create_tables()
        db.execute("INSERT INTO content (article_id, title, platform) VALUES (?, ?, ?)",
                   ("test_002", "单条标题", "douyin"))
        result = db.fetch_one("SELECT * FROM content WHERE article_id = ?", ("test_002",))
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "单条标题")
        db.close()

    def test_get_db_singleton(self):
        """测试全局数据库单例"""
        db1 = get_db()
        db2 = get_db()
        self.assertIs(db1, db2)
        db1.close()


if __name__ == "__main__":
    unittest.main()