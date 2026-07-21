# -*- coding: utf-8 -*-
import os
from src.database import get_db
from dotenv import load_dotenv

# 加载环境变量（可选，不存在时不报错）
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'secrets.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

db = get_db()

# 1. 趋势数据
print("=" * 70)
print("[1] 趋势数据")
print("=" * 70)
sources = db.fetch_all("SELECT source, COUNT(1) as cnt FROM trend_data GROUP BY source")
for s in sources:
    print(f"  {s.get('source','')}: {s.get('cnt',0)} 条")

rows = db.fetch_all("SELECT keyword, tier, heat_index FROM trend_data WHERE source='wechat_index' AND heat_index > 0 ORDER BY heat_index DESC LIMIT 11")
if rows:
    print(f"\n  微信指数关键词(热度={rows[0]['heat_index']}):")
    for r in rows:
        print(f"    [{r.get('tier','')}] {r.get('keyword','')}")

# 2. 内容计划
print("\n" + "=" * 70)
print("[2] 内容计划")
print("=" * 70)
contents = db.fetch_all("SELECT article_id, column_name, title, platform, status, created_at FROM content ORDER BY created_at DESC")
if contents:
    for i, c in enumerate(contents, 1):
        print(f"\n  {i}. {c.get('title','')}")
        print(f"     栏目: {c.get('column_name','')} | 平台: {c.get('platform','')} | 状态: {c.get('status','')}")
        print(f"     ID: {c.get('article_id','')}")
else:
    print("  (暂无)")

# 3. 全表统计
print("\n" + "=" * 70)
print("[3] 全表统计")
print("=" * 70)
tables = ['crawled_data','competitor_data','trend_data','news_data','content',
          'publish_record','performance_data','strategy_adjustments',
          'content_dna','failure_cases','reader_evolution','cognition_updates','evolution_insights']
total = 0
for t in tables:
    row = db.fetch_one(f"SELECT COUNT(1) as c FROM {t}")
    c = row.get("c", 0) if row else 0
    total += c
    mark = " <<<" if c > 0 else ""
    print(f"  {t:<25} {c:>6}{mark}")
print(f"  {'─'*35}")
print(f"  {'总计':<25} {total:>6}")

db.close()
