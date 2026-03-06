import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from models import (
    StockData, NewsArticle, TechnicalIndicators, 
    AnalysisResult, MarketInsight, Config
)
from data_fetcher import DataFetcher
import statistics


class Analyzer:
    """分析引擎"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def calculate_trend_score(self, stock_data: List[StockData]) -> float:
        """计算趋势得分"""
        if not stock_data:
            return 0.0
        
        # 基于最近价格变动计算趋势
        recent_data = []
        for stock in stock_data:
            if stock.historical_prices:
                recent_prices = [p['price'] for p in stock.historical_prices[-7:]]  # 最近7天
                if len(recent_prices) >= 2:
                    start_price = recent_prices[0]
                    end_price = recent_prices[-1]
                    trend = (end_price - start_price) / start_price
                    recent_data.append(trend)
        
        if not recent_data:
            return 0.0
        
        avg_trend = sum(recent_data) / len(recent_data)
        # 归一化到0-1范围
        score = max(0, min(1, (avg_trend + 0.1) * 5))  # 假设最大跌幅-20%，最大涨幅+20%
        return round(score, 3)
    
    def calculate_momentum_score(self, stock_data: List[StockData]) -> float:
        """计算动量得分"""
        if not stock_data:
            return 0.0
        
        momentums = []
        for stock in stock_data:
            if stock.historical_prices and len(stock.historical_prices) >= 14:
                # 计算14日动量 (当前价格相对于14日前的价格变化)
                past_price = stock.historical_prices[-14]['price']
                current_price = stock.price
                momentum = (current_price - past_price) / past_price
                momentums.append(momentum)
        
        if not momentums:
            return 0.5  # 默认中性分数
        
        # 将动量转换为0-1范围的分数
        avg_momentum = sum(momentums) / len(momentums)
        score = max(0, min(1, (avg_momentum + 0.1) * 5))  # 假设最大跌幅-20%，最大涨幅+20%
        return round(score, 3)
    
    def calculate_sentiment_score(self, news_articles: List[NewsArticle]) -> float:
        """计算情绪得分"""
        if not news_articles:
            return 0.5  # 中性分数
        
        sentiments = [article.sentiment_score for article in news_articles]
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        # 将情感分数转换为0-1范围
        # 假设情感分数范围为-1到1，映射到0-1
        score = (avg_sentiment + 1) / 2
        return round(max(0, min(1, score)), 3)
    
    def calculate_volume_score(self, stock_data: List[StockData]) -> float:
        """计算成交量得分"""
        if not stock_data:
            return 0.5  # 中性分数
        
        volumes = [stock.volume for stock in stock_data]
        avg_volume = sum(volumes) / len(volumes)
        
        # 计算相对平均成交量的得分
        # 这里简化处理，实际应用中可能需要与历史成交量对比
        # 使用对数函数避免极端值影响
        log_avg_vol = np.log(avg_volume + 1) if avg_volume > 0 else 0
        # 将对数值归一化到0-1范围
        normalized_score = min(1, log_avg_vol / 20)  # 假设最大对数值为20
        return round(normalized_score, 3)
    
    def calculate_volatility_score(self, stock_data: List[StockData]) -> float:
        """计算波动率得分（较低波动得更高分）"""
        if not stock_data:
            return 0.5
        
        volatilities = []
        for stock in stock_data:
            if stock.historical_prices and len(stock.historical_prices) >= 10:
                prices = [p['price'] for p in stock.historical_prices]
                returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                volatility = statistics.stdev(returns) if len(returns) > 1 else 0
                volatilities.append(volatility)
        
        if not volatilities:
            return 0.5
        
        avg_volatility = sum(volatilities) / len(volatilities)
        # 波动率越低，得分越高，使用指数衰减函数
        score = np.exp(-avg_volatility * 100)  # 乘以100是为了适应股票价格波动幅度
        return round(max(0, min(1, score)), 3)
    
    def calculate_technical_indicators(self, stock_data: List[StockData]) -> TechnicalIndicators:
        """计算技术指标"""
        if not stock_data or not stock_data[0].historical_prices:
            # 返回默认技术指标
            return TechnicalIndicators(
                rsi=50.0,
                macd=0.0,
                moving_average_short=0.0,
                moving_average_long=0.0,
                bollinger_bands={"upper": 0.0, "middle": 0.0, "lower": 0.0},
                volatility=0.0
            )
        
        # 简化的技术指标计算
        latest_stock = stock_data[0]
        prices = [p['price'] for p in latest_stock.historical_prices]
        
        # RSI计算（简化的14日RSI）
        if len(prices) >= 14:
            gains = []
            losses = []
            for i in range(1, 14):
                change = prices[-i] - prices[-i-1]
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))
            
            avg_gain = sum(gains) / 14 if gains else 0
            avg_loss = sum(losses) / 14 if losses else 0.01  # 避免除零
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        else:
            rsi = 50.0
        
        # 移动平均线
        short_ma = sum(prices[-5:]) / 5 if len(prices) >= 5 else prices[-1] if prices else 0
        long_ma = sum(prices[-20:]) / 20 if len(prices) >= 20 else prices[-1] if prices else 0
        
        # 布林带
        middle_band = sum(prices[-20:]) / 20 if len(prices) >= 20 else prices[-1]
        std_dev = np.std(prices[-20:]) if len(prices) >= 20 else 0
        upper_band = middle_band + (std_dev * 2)
        lower_band = middle_band - (std_dev * 2)
        
        # MACD（简化版）
        ema_short = short_ma
        ema_long = long_ma
        macd_line = ema_short - ema_long
        
        # 波动率
        if len(prices) > 1:
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            volatility = np.std(returns) * np.sqrt(252)  # 年化波动率
        else:
            volatility = 0.2  # 默认20%年化波动率
        
        return TechnicalIndicators(
            rsi=round(rsi, 2),
            macd=round(macd_line, 4),
            moving_average_short=round(short_ma, 2),
            moving_average_long=round(long_ma, 2),
            bollinger_bands={
                "upper": round(upper_band, 2),
                "middle": round(middle_band, 2),
                "lower": round(lower_band, 2)
            },
            volatility=round(volatility, 4)
        )
    
    def generate_recommendation(self, scores: Dict[str, float]) -> Tuple[str, float]:
        """生成投资建议和置信度"""
        # 综合各项得分计算总体表现
        weights = self.config.analysis_weights
        overall_score = (
            scores['trend'] * weights['trend'] +
            scores['momentum'] * weights['momentum'] +
            scores['sentiment'] * weights['sentiment'] +
            scores['volume'] * weights['volume'] +
            scores['volatility'] * weights['volatility']
        )
        
        # 生成建议
        if overall_score >= 0.7:
            recommendation = "强烈推荐"
            confidence = 0.9
        elif overall_score >= 0.5:
            recommendation = "推荐关注"
            confidence = 0.75
        elif overall_score >= 0.3:
            recommendation = "谨慎观察"
            confidence = 0.6
        else:
            recommendation = "暂不推荐"
            confidence = 0.5
        
        return recommendation, confidence
    
    def analyze_sector(self, sector: str, fetcher: DataFetcher) -> AnalysisResult:
        """分析特定行业"""
        # 获取行业股票数据
        stock_data = fetcher.get_sector_stocks(sector)
        
        # 获取行业新闻数据
        news_data = fetcher.get_sector_news(sector)
        
        # 计算各项得分
        trend_score = self.calculate_trend_score(stock_data)
        momentum_score = self.calculate_momentum_score(stock_data)
        sentiment_score = self.calculate_sentiment_score(news_data)
        volume_score = self.calculate_volume_score(stock_data)
        volatility_score = self.calculate_volatility_score(stock_data)
        
        scores = {
            'trend': trend_score,
            'momentum': momentum_score,
            'sentiment': sentiment_score,
            'volume': volume_score,
            'volatility': volatility_score
        }
        
        # 计算综合得分
        weights = self.config.analysis_weights
        overall_score = (
            trend_score * weights['trend'] +
            momentum_score * weights['momentum'] +
            sentiment_score * weights['sentiment'] +
            volume_score * weights['volume'] +
            volatility_score * weights['volatility']
        )
        
        # 生成投资建议和置信度
        recommendation, confidence = self.generate_recommendation(scores)
        
        # 计算技术指标
        technical_indicators = self.calculate_technical_indicators(stock_data)
        
        return AnalysisResult(
            sector=sector,
            trend_score=trend_score,
            momentum_score=momentum_score,
            sentiment_score=sentiment_score,
            volume_score=volume_score,
            overall_score=round(overall_score, 3),
            recommendation=recommendation,
            confidence=round(confidence, 3),
            technical_indicators=technical_indicators,
            related_news=news_data,
            stock_data=stock_data
        )
    
    def generate_market_insight(self, analysis_results: List[AnalysisResult]) -> MarketInsight:
        """生成市场洞察报告"""
        # 筛选出推荐等级较高的行业
        top_recommendations = sorted(
            analysis_results, 
            key=lambda x: x.overall_score, 
            reverse=True
        )[:3]  # 取前3名
        
        # 风险评估
        high_volatility_sectors = [
            result for result in analysis_results 
            if result.technical_indicators.volatility > 0.3
        ]
        
        if high_volatility_sectors:
            risk_assessment = f"需要注意以下行业的高波动风险: {', '.join([s.sector for s in high_volatility_sectors])}"
        else:
            risk_assessment = "整体市场波动性处于正常范围"
        
        # 投资策略
        strong_sectors = [r for r in analysis_results if r.recommendation == "强烈推荐"]
        if strong_sectors:
            strategy = f"重点关注{len(strong_sectors)}个强势行业: {', '.join([s.sector for s in strong_sectors])}，建议积极配置"
        else:
            strategy = "当前市场机会较为分散，建议均衡配置并密切关注政策动向"
        
        # 总结
        best_sector = max(analysis_results, key=lambda x: x.overall_score)
        summary = f"{best_sector.sector}行业表现最为突出，综合得分为{best_sector.overall_score:.3f}，建议重点关注"
        
        return MarketInsight(
            sector_analysis=analysis_results,
            top_recommendations=top_recommendations,
            risk_assessment=risk_assessment,
            investment_strategy=strategy,
            update_time=datetime.now(),
            summary=summary
        )