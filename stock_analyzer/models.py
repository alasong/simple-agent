"""
股市热点分析工具数据模型
"""
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
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class NewsArticle:
    """新闻文章模型"""
    title: str
    content: str
    source: str
    published_at: datetime
    sentiment_score: float  # -1 to 1
    relevance_score: float  # 0 to 1
    url: str = ""

@dataclass
class AnalysisResult:
    """分析结果模型"""
    sector: str
    trend_score: float  # 0 to 1
    momentum_score: float  # -1 to 1
    sentiment_score: float  # -1 to 1
    volatility_score: float  # 0 to 1
    top_stocks: List[StockData]
    key_news: List[NewsArticle]
    summary: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'sector': self.sector,
            'trend_score': self.trend_score,
            'momentum_score': self.momentum_score,
            'sentiment_score': self.sentiment_score,
            'volatility_score': self.volatility_score,
            'top_stocks': [stock.__dict__ for stock in self.top_stocks],
            'key_news': [
                {
                    'title': article.title,
                    'source': article.source,
                    'published_at': article.published_at.isoformat(),
                    'sentiment_score': article.sentiment_score,
                    'relevance_score': article.relevance_score,
                    'url': article.url
                } for article in self.key_news
            ],
            'summary': self.summary,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class MarketInsight:
    """市场洞察模型"""
    overall_sentiment: float  # -1 to 1
    hot_topics: List[str]
    recommendation: str
    risk_level: str  # low, medium, high
    confidence_score: float  # 0 to 1
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()