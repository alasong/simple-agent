"""
股市热点分析引擎
"""
from typing import List, Dict, Any
import numpy as np
from datetime import datetime, timedelta
import statistics
import logging

from .models import StockData, NewsArticle, AnalysisResult
from .data_fetcher import DataFetcher
from .config import SECTOR_CONFIGS

logger = logging.getLogger(__name__)

class StockAnalyzer:
    """股票分析器"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
    
    def analyze_sector(self, sector_key: str) -> AnalysisResult:
        """分析特定行业"""
        config = SECTOR_CONFIGS[sector_key]
        
        # 获取股票数据
        stocks = self.data_fetcher.fetch_stock_data(config.related_stocks[:5])  # 只取前5只
        
        # 获取相关新闻
        news = self.data_fetcher.fetch_news(" ".join(config.keywords), max_articles=5)
        
        # 计算各项评分
        trend_score = self.calculate_trend_score(stocks)
        momentum_score = self.calculate_momentum_score(stocks)
        sentiment_score = self.calculate_sentiment_score(news)
        volatility_score = self.calculate_volatility_score(stocks)
        
        # 生成摘要
        summary = self.generate_summary(sector_key, trend_score, momentum_score, 
                                       sentiment_score, volatility_score, stocks)
        
        return AnalysisResult(
            sector=config.name,
            trend_score=trend_score,
            momentum_score=momentum_score,
            sentiment_score=sentiment_score,
            volatility_score=volatility_score,
            top_stocks=stocks,
            key_news=news,
            summary=summary
        )
    
    def calculate_trend_score(self, stocks: List[StockData]) -> float:
        """计算趋势评分 (0-1)"""
        if not stocks:
            return 0.5
        
        positive_count = sum(1 for stock in stocks if stock.change_percent > 0)
        return positive_count / len(stocks)
    
    def calculate_momentum_score(self, stocks: List[StockData]) -> float:
        """计算动量评分 (-1 to 1)"""
        if not stocks:
            return 0.0
        
        avg_change = sum(stock.change_percent for stock in stocks) / len(stocks)
        # 将百分比转换为-1到1的范围
        return max(-1.0, min(1.0, avg_change / 10.0))
    
    def calculate_sentiment_score(self, news: List[NewsArticle]) -> float:
        """计算情绪评分 (-1 to 1)"""
        if not news:
            return 0.0
        
        weighted_sentiment = sum(
            article.sentiment_score * article.relevance_score 
            for article in news
        )
        total_relevance = sum(article.relevance_score for article in news)
        
        if total_relevance == 0:
            return 0.0
        
        return weighted_sentiment / total_relevance
    
    def calculate_volatility_score(self, stocks: List[StockData]) -> float:
        """计算波动率评分 (0-1)"""
        if not stocks or len(stocks) < 2:
            return 0.5
        
        prices = [stock.price for stock in stocks]
        if len(set(prices)) == 1:  # 所有价格相同
            return 0.0
        
        # 使用价格的标准差作为波动率指标
        std_dev = statistics.stdev(prices)
        mean_price = statistics.mean(prices)
        
        if mean_price == 0:
            return 0.5
        
        coefficient_of_variation = std_dev / mean_price
        
        # 将变异系数映射到0-1范围
        return min(1.0, coefficient_of_variation * 10)
    
    def generate_summary(self, sector_key: str, trend_score: float, 
                        momentum_score: float, sentiment_score: float, 
                        volatility_score: float, stocks: List[StockData]) -> str:
        """生成分析摘要"""
        sector_name = SECTOR_CONFIGS[sector_key].name
        
        # 根据各项评分生成摘要
        trend_desc = "上升" if trend_score > 0.6 else ("下降" if trend_score < 0.4 else "平稳")
        momentum_desc = "强劲" if momentum_score > 0.3 else ("疲软" if momentum_score < -0.3 else "中性")
        sentiment_desc = "积极" if sentiment_score > 0.3 else ("消极" if sentiment_score < -0.3 else "中性")
        volatility_desc = "高" if volatility_score > 0.7 else ("低" if volatility_score < 0.3 else "中等")
        
        top_gainer = max(stocks, key=lambda x: x.change_percent) if stocks else None
        
        summary = (
            f"{sector_name}行业整体呈现{trend_desc}趋势，市场动量表现{momentum_desc}，"
            f"媒体情绪偏向{sentiment_desc}，市场波动性为{volatility_desc}。"
        )
        
        if top_gainer:
            summary += f"其中{top_gainer.name}涨幅最大，达到{top_gainer.change_percent:.2f}%。"
        
        return summary
    
    def get_comprehensive_analysis(self) -> List[AnalysisResult]:
        """获取综合分析"""
        results = []
        
        for sector_key in SECTOR_CONFIGS.keys():
            try:
                result = self.analyze_sector(sector_key)
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing sector {sector_key}: {e}")
                continue
        
        return results