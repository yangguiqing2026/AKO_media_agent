"""
MediaCrawler 合规运行配置文件
基于 MediaCrawler (GitHub 27K⭐, MIT License)
"""

# =============================================================================
# 基础采集配置
# =============================================================================

# 关键词矩阵
KEYWORDS = [
    # 一级词
    "装配式建筑",
    "模块化住宅",
    # 二级词
    "陶粒混凝土",
    "预制墙板",
    "快速建房",
    # 三级词
    "农村自建房",
    "轻钢别墅",
    "集装箱房",
    # 长尾词
    "贵阳装配式建筑",
    "贵州模块化建筑",
    "三层别墅造价",
]

# 目标平台: xhs | dy | wb | bili | zhihu | wechat | shipinhao
PLATFORM = "xhs"
ALL_PLATFORMS = ["xhs", "dy", "wb", "bili", "zhihu", "wechat", "shipinhao"]

# 数据采集选项
ENABLE_GET_COMMENTS = True
SAVE_DATA_OPTION = "db"  # csv | json | db

# =============================================================================
# 合规配置 (v1.2)
# =============================================================================

COMPLIANCE = {
    # 代理IP配置
    "proxy_rotation_interval": 2,      # 秒，轮换间隔
    "proxy_provider": "bright_data",    # bright_data | dataimpulse
    "proxy_pool_size": 10,
    "geo_distribution": True,           # 多省市分散
    
    # 账号池配置
    "account_pool_size": 5,             # 5个不同手机号注册账号
    "account_daily_limit": 100,         # 单账号日请求≤100次
    "auto_switch_on_fail": True,        # 登录态失效自动切换
    "alert_on_switch": True,            # 切换时邮件告警
    
    # 请求频率控制
    "daily_request_limit": 500,         # 单平台≤500条/日
    "min_request_interval": 2.0,        # 最小间隔2秒
    "request_jitter": 0.5,              # 随机抖动±0.5秒
    "active_hours": [9, 23],            # 09:00-23:00活跃时段
    
    # 验证码处理
    "auto_pause_on_captcha": True,      # 遇到验证码自动暂停
    "captcha_alert": True,              # 验证码告警
    
    # 数据保留
    "log_retention_days": 180,          # 日志保留6个月
    "data_anonymization": True,         # 隐私数据脱敏
}

# =============================================================================
# 数据采集边界
# =============================================================================

DATA_BOUNDARY = {
    # 允许的操作
    "allowed": [
        "仅采集公开页面",
        "用于学习研究和品牌监测",
        "遵守各平台robots.txt",
    ],
    # 禁止的操作
    "forbidden": [
        "不登录抓取私密内容",
        "不绕过反爬机制",
        "不采集用户隐私信息(手机号、地址等)",
        "不采集付费/会员内容",
        "不批量采集用户关系链",
        "不售卖数据",
    ],
}

# =============================================================================
# 各平台特定配置
# =============================================================================

PLATFORM_CONFIG = {
    "xhs": {
        "name": "小红书",
        "data_types": ["笔记", "评论", "点赞", "收藏"],
        "search_type": "keyword_and_user",
    },
    "dy": {
        "name": "抖音",
        "data_types": ["视频", "评论", "点赞", "转发"],
        "search_type": "keyword_and_user_homepage",
    },
    "wb": {
        "name": "微博",
        "data_types": ["帖子", "评论", "转发"],
        "search_type": "keyword_and_hot_search",
    },
    "bili": {
        "name": "B站",
        "data_types": ["视频", "弹幕", "评论"],
        "search_type": "keyword",
    },
    "zhihu": {
        "name": "知乎",
        "data_types": ["问答", "文章", "评论"],
        "search_type": "keyword",
    },
    "wechat": {
        "name": "公众号",
        "data_types": ["文章", "阅读数(估算)"],
        "search_type": "sogou_wechat",
    },
    "shipinhao": {
        "name": "视频号",
        "data_types": ["视频", "互动数据"],
        "search_type": "keyword",
    },
}

# =============================================================================
# 告警配置
# =============================================================================

ALERT_CONFIG = {
    "enabled": True,
    "channels": ["email"],
    "recipients": ["admin@akobuild.cloud"],
    "events": [
        "account_switch",
        "captcha_detected",
        "daily_limit_reached",
        "platform_error",
    ],
}
