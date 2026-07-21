# -*- coding: utf-8 -*-
"""
AKO Media Agent - Web UI 服务
提供可视化的系统操作界面
"""
import os
import sys
import json
import logging
from datetime import datetime, timedelta

# 限制 OpenBLAS/numpy 线程数和内存（防止后台任务内存溢出）
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify, request, send_from_directory
from dotenv import load_dotenv

# 加载环境变量
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'secrets.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

from src.database import get_db, init_db

logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
)
app.config['SECRET_KEY'] = os.urandom(24).hex()


# =============================================================================
# 页面路由
# =============================================================================

@app.route('/')
def index():
    """主仪表盘"""
    return render_template('dashboard.html')


@app.route('/crawler')
def crawler_page():
    """数据采集页面"""
    return render_template('crawler.html')


@app.route('/analysis')
def analysis_page():
    """智能分析页面"""
    return render_template('analysis.html')


@app.route('/content')
def content_page():
    """内容管理页面"""
    return render_template('content.html')


@app.route('/feedback')
def feedback_page():
    """反馈与报告页面"""
    return render_template('feedback.html')


@app.route('/evolution')
def evolution_page():
    """进化层页面"""
    return render_template('evolution.html')


# =============================================================================
# API 路由 - 仪表盘
# =============================================================================

@app.route('/api/dashboard')
def api_dashboard():
    """仪表盘总览数据"""
    db = get_db()
    data = {}

    # 采集统计
    crawl_count = db.fetch_one("SELECT COUNT(1) as c FROM crawled_data")
    data['crawled_total'] = crawl_count['c'] if crawl_count else 0

    # 各平台采集量
    platforms = db.fetch_all(
        "SELECT platform, COUNT(1) as cnt FROM crawled_data GROUP BY platform"
    )
    data['platforms'] = {p['platform']: p['cnt'] for p in platforms} if platforms else {}

    # 内容统计
    content_stats = db.fetch_one(
        "SELECT COUNT(1) as total, SUM(CASE WHEN status='draft' THEN 1 ELSE 0 END) as draft, "
        "SUM(CASE WHEN status='published' THEN 1 ELSE 0 END) as published FROM content"
    )
    if content_stats:
        data['content_total'] = content_stats['total'] or 0
        data['content_draft'] = content_stats['draft'] or 0
        data['content_published'] = content_stats['published'] or 0

    # 趋势数据量
    trend_count = db.fetch_one("SELECT COUNT(1) as c FROM trend_data")
    data['trend_total'] = trend_count['c'] if trend_count else 0

    # 竞品数据量
    comp_count = db.fetch_one("SELECT COUNT(1) as c FROM competitor_data")
    data['competitor_total'] = comp_count['c'] if comp_count else 0

    # 表现数据汇总
    perf_summary = db.fetch_one(
        "SELECT SUM(reads) as t_reads, SUM(likes) as t_likes, "
        "SUM(comments) as t_comments, SUM(shares) as t_shares FROM performance_data"
    )
    if perf_summary:
        data['total_reads'] = perf_summary['t_reads'] or 0
        data['total_likes'] = perf_summary['t_likes'] or 0
        data['total_comments'] = perf_summary['t_comments'] or 0
        data['total_shares'] = perf_summary['t_shares'] or 0

    db.close()
    return jsonify(data)


# =============================================================================
# API 路由 - 数据采集
# =============================================================================

@app.route('/api/crawler/recent')
def api_crawler_recent():
    """最近采集数据"""
    db = get_db()
    rows = db.fetch_all(
        "SELECT platform, title, author, likes, publish_time, created_at "
        "FROM crawled_data ORDER BY created_at DESC LIMIT 20"
    )
    db.close()
    return jsonify([dict(r) for r in rows] if rows else [])


@app.route('/api/crawler/platform-stats')
def api_crawler_platform_stats():
    """各平台统计"""
    db = get_db()
    rows = db.fetch_all(
        "SELECT platform, COUNT(1) as cnt, SUM(likes) as t_likes "
        "FROM crawled_data GROUP BY platform"
    )
    db.close()
    return jsonify([dict(r) for r in rows] if rows else [])


@app.route('/api/crawler/accounts')
def api_crawler_accounts():
    """获取账号池状态"""
    from src.crawler.compliance.account_pool import AccountPool
    pool = AccountPool({})
    status = pool.get_pool_status()
    # 返回详细信息
    accounts_info = []
    platform_names = {
        "xhs": "小红书", "dy": "抖音", "wb": "微博",
        "bili": "哔哩哔哩", "zhihu": "知乎", "wechat": "微信公众号", "shipinhao": "视频号"
    }
    for platform, accounts in status.get("account_counts", {}).items():
        accounts_info.append({
            "platform": platform,
            "name": platform_names.get(platform, platform),
            "count": accounts,
        })
    # 补充没有账号的平台
    for platform, name in platform_names.items():
        if not any(a["platform"] == platform for a in accounts_info):
            accounts_info.append({"platform": platform, "name": name, "count": 0})
    return jsonify(accounts_info)


@app.route('/api/crawler/accounts/init', methods=['POST'])
def api_crawler_accounts_init():
    """一键初始化所有平台账号"""
    from src.crawler.compliance.account_pool import AccountPool
    pool = AccountPool({})
    result = pool.init_all_platform_accounts()
    created = sum(1 for v in result.values() if v.get("status") == "created")
    exists = sum(1 for v in result.values() if v.get("status") == "exists")
    return jsonify({
        "status": "success",
        "message": f"账号初始化完成: 新建 {created} 个，已存在 {exists} 个",
        "details": result,
    })


@app.route('/api/crawler/trigger', methods=['POST'])
def api_crawler_trigger():
    """手动触发采集（异步）"""
    platform = request.json.get('platform', '')
    full = request.json.get('full', False)

    def _run_crawl():
        try:
            from src.crawler.media_crawler import MediaCrawlerWrapper
            from src.database import get_db
            db = get_db()
            crawler = MediaCrawlerWrapper({})
            if platform:
                crawler.crawl_platform(platform)
            else:
                crawler.crawl_all_platforms()
            db.close()
            logger.info(f"采集任务完成: platform={platform}, full={full}")
        except Exception as e:
            logger.error(f"采集任务失败: {e}")

    thread = threading.Thread(target=_run_crawl, daemon=True)
    thread.start()

    return jsonify({'status': 'success', 'message': f'采集任务已启动: platform={platform or "all"}, full={full}'})


# =============================================================================
# API 路由 - 智能分析
# =============================================================================

@app.route('/api/analysis/trends')
def api_analysis_trends():
    """趋势数据"""
    db = get_db()
    rows = db.fetch_all(
        "SELECT keyword, source, tier, heat_index, recorded_at "
        "FROM trend_data ORDER BY heat_index DESC LIMIT 30"
    )
    db.close()
    return jsonify([dict(r) for r in rows] if rows else [])


@app.route('/api/analysis/competitors')
def api_analysis_competitors():
    """竞品数据"""
    db = get_db()
    rows = db.fetch_all(
        "SELECT competitor_name, platform, content_title, likes, comments, shares, is_viral, publish_date "
        "FROM competitor_data ORDER BY publish_date DESC LIMIT 20"
    )
    db.close()
    return jsonify([dict(r) for r in rows] if rows else [])


@app.route('/api/analysis/news')
def api_analysis_news():
    """新闻数据"""
    db = get_db()
    rows = db.fetch_all(
        "SELECT source, title, summary, is_policy_change, publish_time "
        "FROM news_data ORDER BY publish_time DESC LIMIT 20"
    )
    db.close()
    return jsonify([dict(r) for r in rows] if rows else [])


@app.route('/api/analysis/trigger', methods=['POST'])
def api_analysis_trigger():
    """手动触发分析（异步）"""
    def _run_analysis():
        try:
            from src.main import AKOMediaAgent
            agent = AKOMediaAgent()
            agent.initialize()
            agent.run_analysis()
            agent.shutdown()
            logger.info("智能分析完成")
        except Exception as e:
            logger.error(f"分析任务失败: {e}")

    thread = threading.Thread(target=_run_analysis, daemon=True)
    thread.start()
    return jsonify({'status': 'success', 'message': '智能分析已启动，请稍后刷新查看结果'})


# =============================================================================
# API 路由 - 内容管理
# =============================================================================

@app.route('/api/content/list')
def api_content_list():
    """内容列表"""
    status_filter = request.args.get('status', '')
    db = get_db()
    if status_filter:
        rows = db.fetch_all(
            "SELECT article_id, column_name, title, platform, status, thought_depth_score, "
            "predicted_engagement, created_at, scheduled_at, published_at "
            "FROM content WHERE status = ? ORDER BY created_at DESC LIMIT 50",
            (status_filter,)
        )
    else:
        rows = db.fetch_all(
            "SELECT article_id, column_name, title, platform, status, thought_depth_score, "
            "predicted_engagement, created_at, scheduled_at, published_at "
            "FROM content ORDER BY created_at DESC LIMIT 50"
        )
    db.close()
    return jsonify([dict(r) for r in rows] if rows else [])


@app.route('/api/content/<article_id>')
def api_content_detail(article_id):
    """内容详情"""
    db = get_db()
    row = db.fetch_one(
        "SELECT * FROM content WHERE article_id = ?", (article_id,)
    )
    db.close()
    if row:
        return jsonify(dict(row))
    return jsonify({'error': '未找到'}), 404


@app.route('/api/content/publish', methods=['POST'])
def api_content_publish():
    """发布内容（异步）"""
    platform = request.json.get('platform', '')
    stage = request.json.get('stage', 'review')

    def _run_publish():
        try:
            from src.main import AKOMediaAgent
            agent = AKOMediaAgent()
            agent.initialize()
            agent.run_publish(platform=platform or None, stage=stage)
            agent.shutdown()
            logger.info(f"发布任务完成: platform={platform}, stage={stage}")
        except Exception as e:
            logger.error(f"发布任务失败: {e}")

    thread = threading.Thread(target=_run_publish, daemon=True)
    thread.start()
    return jsonify({'status': 'success', 'message': f'发布任务已启动: platform={platform or "all"}, stage={stage}'})


@app.route('/api/content/delete', methods=['POST'])
def api_content_delete():
    """删除内容"""
    article_id = request.json.get('article_id', '')
    if not article_id:
        return jsonify({'status': 'error', 'message': '缺少 article_id'}), 400
    db = get_db()
    db.execute("DELETE FROM content WHERE article_id = ?", (article_id,))
    db.close()
    return jsonify({'status': 'success', 'message': f'已删除: {article_id}'})


@app.route('/api/content/generate', methods=['POST'])
def api_content_generate():
    """AI生成文案"""
    topic = request.json.get('topic', '')
    column = request.json.get('column', 'AKO建造志')
    platform = request.json.get('platform', 'wechat')

    if not topic:
        return jsonify({'status': 'error', 'message': '请提供选题'}), 400

    try:
        from src.execution.copywriter import Copywriter
        config = {
            "layers": {
                "execution": {
                    "copywriter": {
                        "provider": "deepseek",
                        "style_control": {"structure": "切片-展开-收束"},
                    }
                }
            }
        }
        writer = Copywriter(config)
        article = writer.generate_article(
            topic=topic,
            column=column,
            platform=platform,
        )

        # 保存到数据库
        import uuid
        article_id = f"gen-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        db = get_db()
        db.execute(
            """INSERT INTO content (article_id, column_name, title, body, platform, status, created_by,
               thought_depth_score, word_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                article_id,
                column,
                article.get("title", topic),
                article.get("body", ""),
                platform,
                "draft",
                "ai",
                article.get("thought_depth_score", 0),
                article.get("word_count", 0),
            ),
        )
        db.close()

        return jsonify({
            'status': 'success',
            'message': f'文案已生成并保存',
            'article': {
                'article_id': article_id,
                'title': article.get('title', ''),
                'body': article.get('body', ''),
                'word_count': article.get('word_count', 0),
                'style_score': article.get('style_score', 0),
                'thought_depth_score': article.get('thought_depth_score', 0),
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# =============================================================================
# API 路由 - 反馈报告
# =============================================================================

@app.route('/api/feedback/performance')
def api_feedback_performance():
    """表现数据"""
    db = get_db()
    rows = db.fetch_all(
        "SELECT article_id, platform, reads, likes, comments, shares, favorites, "
        "completion_rate, follower_growth, negative_ratio, recorded_at "
        "FROM performance_data ORDER BY recorded_at DESC LIMIT 30"
    )
    db.close()
    return jsonify([dict(r) for r in rows] if rows else [])


@app.route('/api/feedback/strategy')
def api_feedback_strategy():
    """策略调整记录"""
    db = get_db()
    rows = db.fetch_all(
        "SELECT adjustment_type, dimension, old_value, new_value, reason, auto_adjusted, created_at "
        "FROM strategy_adjustments ORDER BY created_at DESC LIMIT 20"
    )
    db.close()
    return jsonify([dict(r) for r in rows] if rows else [])


@app.route('/api/feedback/trigger', methods=['POST'])
def api_feedback_trigger():
    """手动触发反馈闭环"""
    weekly = request.json.get('weekly', False)
    monthly = request.json.get('monthly', False)
    try:
        from src.main import AKOMediaAgent
        agent = AKOMediaAgent()
        agent.initialize()
        agent.run_feedback(weekly=weekly, monthly=monthly)
        agent.shutdown()
        return jsonify({'status': 'success', 'message': '反馈闭环已完成'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# =============================================================================
# API 路由 - 全流水线
# =============================================================================

# =============================================================================
# API 路由 - 流水线（带进度）
# =============================================================================

import threading

# 流水线进度状态
_pipeline_progress = {
    "running": False,
    "step": 0,
    "total_steps": 6,
    "current": "",
    "steps": [
        "数据采集",
        "智能分析",
        "决策引擎",
        "执行发布",
        "反馈闭环",
        "自我进化",
    ],
    "message": "",
    "error": "",
}
_pipeline_lock = threading.Lock()


def _run_pipeline_with_progress():
    """在后台线程中运行流水线并更新进度"""
    global _pipeline_progress
    try:
        from src.main import AKOMediaAgent
        agent = AKOMediaAgent()
        agent.initialize()

        steps = [
            ("数据采集", lambda: agent.run_crawl()),
            ("智能分析", lambda: agent.run_analysis()),
            ("决策引擎", lambda: agent.run_decision()),
            ("执行发布", lambda: agent.run_publish(stage="draft")),
            ("反馈闭环", lambda: agent.run_feedback(weekly=True)),
            ("自我进化", lambda: agent.run_evolution()),
        ]

        for i, (name, fn) in enumerate(steps):
            with _pipeline_lock:
                _pipeline_progress["step"] = i + 1
                _pipeline_progress["current"] = name
                _pipeline_progress["message"] = f"正在执行: {name}..."

            try:
                fn()
            except Exception as e:
                logger.warning(f"流水线步骤 '{name}' 出错: {e}")

        agent.shutdown()

        with _pipeline_lock:
            _pipeline_progress["running"] = False
            _pipeline_progress["step"] = 6
            _pipeline_progress["current"] = "完成"
            _pipeline_progress["message"] = "流水线运行完成"

    except Exception as e:
        with _pipeline_lock:
            _pipeline_progress["running"] = False
            _pipeline_progress["error"] = str(e)
            _pipeline_progress["message"] = f"运行失败: {e}"


@app.route('/api/pipeline/start', methods=['POST'])
def api_pipeline_start():
    """启动完整流水线（异步带进度）"""
    global _pipeline_progress

    with _pipeline_lock:
        if _pipeline_progress["running"]:
            return jsonify({'status': 'error', 'message': '流水线正在运行中'})

        _pipeline_progress = {
            "running": True,
            "step": 0,
            "total_steps": 6,
            "current": "启动中",
            "steps": ["数据采集", "智能分析", "决策引擎", "执行发布", "反馈闭环", "自我进化"],
            "message": "正在启动流水线...",
            "error": "",
        }

    thread = threading.Thread(target=_run_pipeline_with_progress, daemon=True)
    thread.start()

    return jsonify({'status': 'success', 'message': '流水线已启动'})


@app.route('/api/pipeline/progress')
def api_pipeline_progress():
    """查询流水线进度"""
    with _pipeline_lock:
        return jsonify(dict(_pipeline_progress))


# =============================================================================
# API 路由 - 进化层
# =============================================================================

@app.route('/api/evolution/insights')
def api_evolution_insights():
    """进化洞察数据"""
    db = get_db()
    rows = db.fetch_all(
        "SELECT insight_type, source_module, content, confidence, applied, created_at "
        "FROM evolution_insights ORDER BY created_at DESC LIMIT 30"
    )
    db.close()
    return jsonify([dict(r) for r in rows] if rows else [])


@app.route('/api/evolution/cognition')
def api_evolution_cognition():
    """认知更新数据"""
    db = get_db()
    rows = db.fetch_all(
        "SELECT category, topic, old_belief, new_belief, confidence, updated_at "
        "FROM cognition_updates ORDER BY updated_at DESC LIMIT 20"
    )
    db.close()
    return jsonify([dict(r) for r in rows] if rows else [])


@app.route('/api/evolution/dna')
def api_evolution_dna():
    """内容DNA数据"""
    db = get_db()
    rows = db.fetch_all(
        "SELECT content_id, extracted_at FROM content_dna ORDER BY extracted_at DESC LIMIT 20"
    )
    db.close()
    return jsonify([dict(r) for r in rows] if rows else [])


@app.route('/api/evolution/trigger', methods=['POST'])
def api_evolution_trigger():
    """手动触发进化层（异步）"""
    def _run_evolution():
        try:
            from src.main import AKOMediaAgent
            agent = AKOMediaAgent()
            agent.initialize()
            agent.run_evolution()
            agent.shutdown()
            logger.info("进化层运行完成")
        except Exception as e:
            logger.error(f"进化层运行失败: {e}")

    thread = threading.Thread(target=_run_evolution, daemon=True)
    thread.start()
    return jsonify({'status': 'success', 'message': '进化层已启动，请稍后刷新查看结果'})


def main():
    """启动 Web UI 服务"""
    import argparse
    parser = argparse.ArgumentParser(description='AKO Media Agent - Web UI')
    parser.add_argument('--host', default='127.0.0.1', help='监听地址')
    parser.add_argument('--port', type=int, default=5000, help='监听端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    args = parser.parse_args()

    print("=" * 50)
    print("  AKO Media Agent - Web UI")
    print(f"  地址: http://{args.host}:{args.port}")
    print("=" * 50)

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()