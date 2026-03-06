from models import Config


def get_config():
    """获取系统配置"""
    return Config.default_config()


# 预设的行业配置
SECTOR_CONFIG = {
    "固态电池": {
        "keywords": ["固态电池", "锂电池", "新能源", "储能", "动力电池"],
        "stocks": ["002466.SZ", "300750.SZ", "688005.SH", "002812.SZ", "300014.SZ"],
        "api_endpoint": "/api/stock/battery"
    },
    "半导体设备": {
        "keywords": ["半导体", "芯片", "集成电路", "光刻机", "晶圆厂", "封测"],
        "stocks": ["002371.SZ", "300604.SZ", "688012.SH", "002307.SZ", "300623.SZ"],
        "api_endpoint": "/api/stock/semiconductor"
    },
    "AI算力": {
        "keywords": ["人工智能", "算力", "GPU", "数据中心", "云计算", "AI芯片"],
        "stocks": ["000938.SZ", "300253.SZ", "688111.SH", "002415.SZ", "000977.SZ"],
        "api_endpoint": "/api/stock/ai"
    }
}


# API端点配置
API_ENDPOINTS = {
    "stock_api": "https://api.example.com/stock",
    "news_api": "https://api.example.com/news",
    "sentiment_api": "https://api.example.com/sentiment"
}


# 情感阈值配置
SENTIMENT_THRESHOLDS = {
    "positive": 0.5,
    "negative": -0.5,
    "neutral": 0.0
}


# 分析权重配置
ANALYSIS_WEIGHTS = {
    "trend": 0.3,      # 趋势权重
    "momentum": 0.2,   # 动量权重
    "sentiment": 0.25, # 情绪权重
    "volume": 0.15,    # 成交量权重
    "volatility": 0.1  # 波动率权重（负向指标，但这里作为综合评估的一部分）
}