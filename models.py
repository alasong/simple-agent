from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import json


@dataclass
class StockData:
    """股票数据模型"""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: float
    pe_ratio: float
    timestamp: datetime
    historical_prices: List[Dict[str, Any]] = None


@dataclass
class NewsArticle:
    """新闻文章模型"""
    title: str
    content: str
    source: str
    published_at: datetime
    sentiment_score: float
    keywords: List[str]
    url: str = ""


@dataclass
class TechnicalIndicators:
    """技术指标模型"""
    rsi: float
    macd: float
    moving_average_short: float
    moving_average_long: float
    bollinger_bands: Dict[str, float]
    volatility: float


@dataclass
class AnalysisResult:
    """分析结果模型"""
    sector: str
    trend_score: float
    momentum_score: float
    sentiment_score: float
    volume_score: float
    overall_score: float
    recommendation: str
    confidence: float
    technical_indicators: TechnicalIndicators
    related_news: List[NewsArticle]
    stock_data: List[StockData]


@dataclass
class MarketInsight:
    """市场洞察模型"""
    sector_analysis: List[AnalysisResult]
    top_recommendations: List[AnalysisResult]
    risk_assessment: str
    investment_strategy: str
    update_time: datetime
    summary: str


@dataclass
class Config:
    """系统配置模型"""
    sectors: Dict[str, Dict[str, Any]]
    api_endpoints: Dict[str, str]
    sentiment_thresholds: Dict[str, float]
    analysis_weights: Dict[str, float]

    @staticmethod
    def default_config():
        return Config(
            sectors={
                "固态电池": {
                    "keywords": ["固态电池", "锂电池", "新能源", "储能"],
                    "stocks": ["002466.SZ", "300750.SZ", "688005.SH"],
                    "api_endpoint": "/api/stock/battery"
                },
                "半导体设备": {
                    "keywords": ["半导体", "芯片", "集成电路", "光刻机"],
                    "stocks": ["002371.SZ", "300604.SZ", "688012.SH"],
                    "api_endpoint": "/api/stock/semiconductor"
                },
                "AI算力": {
                    "keywords": ["人工智能", "算力", "GPU", "数据中心"],
                    "stocks": ["000938.SZ", "300253.SZ", "688111.SH"],
                    "api_endpoint": "/api/stock/ai"
                }
            },
            api_endpoints={
                "stock_api": "https://api.example.com/stock",
                "news_api": "https://api.example.com/news",
                "sentiment_api": "https://api.example.com/sentiment"
            },
            sentiment_thresholds={
                "positive": 0.5,
                "negative": -0.5,
                "neutral": 0.0
            },
            analysis_weights={
                "trend": 0.3,
                "momentum": 0.2,
                "sentiment": 0.25,
                "volume": 0.15,
                "volatility": 0.1
            }
        )