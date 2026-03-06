import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
from models import StockData, NewsArticle, Config
import time
import random


class DataFetcher:
    """数据获取器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        
    def fetch_stock_data(self, symbols: List[str]) -> List[StockData]:
        """获取股票数据"""
        stocks = []
        for symbol in symbols:
            # 模拟API调用
            stock_data = self._mock_stock_data(symbol)
            stocks.append(stock_data)
            # 避免过于频繁的请求
            time.sleep(0.1)
        return stocks
    
    def _mock_stock_data(self, symbol: str) -> StockData:
        """模拟股票数据获取"""
        # 根据股票代码生成对应的名称
        names = {
            "002466.SZ": "天齐锂业",
            "300750.SZ": "宁德时代", 
            "688005.SH": "容百科技",
            "002371.SZ": "北方华创",
            "300604.SZ": "长川科技",
            "688012.SH": "中微公司",
            "000938.SZ": "紫光股份",
            "300253.SZ": "卫宁健康",
            "688111.SH": "金山办公"
        }
        
        name = names.get(symbol, f"股票{symbol}")
        
        # 生成模拟数据
        base_price = 50.0 + random.uniform(-20, 50)
        change = random.uniform(-5, 5)
        
        return StockData(
            symbol=symbol,
            name=name,
            price=round(base_price, 2),
            change=round(change, 2),
            change_percent=round((change / base_price) * 100, 2),
            volume=int(random.uniform(1000000, 10000000)),
            market_cap=random.uniform(1e9, 1e11),
            pe_ratio=round(random.uniform(10, 50), 2),
            timestamp=datetime.now(),
            historical_prices=self._generate_historical_prices(base_price)
        )
    
    def _generate_historical_prices(self, current_price: float) -> List[Dict[str, Any]]:
        """生成历史价格数据"""
        prices = []
        price = current_price
        for i in range(30):  # 最近30天
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            change = random.uniform(-3, 3)
            price = max(price + change, 1.0)  # 确保价格大于0
            prices.append({
                "date": date,
                "price": round(price, 2),
                "volume": int(random.uniform(1000000, 10000000))
            })
        return prices[::-1]  # 返回正序排列
    
    def fetch_news_data(self, keywords: List[str], limit: int = 10) -> List[NewsArticle]:
        """获取新闻数据"""
        articles = []
        for keyword in keywords:
            for i in range(limit // len(keywords)):
                article = self._mock_news_article(keyword, i)
                articles.append(article)
        return articles[:limit]
    
    def _mock_news_article(self, keyword: str, index: int) -> NewsArticle:
        """模拟新闻文章数据"""
        titles = {
            "固态电池": [
                f"{keyword}技术取得重大突破，产业链迎发展机遇",
                f"政策利好加持，{keyword}市场前景广阔",
                f"多家企业布局{keyword}赛道，竞争加剧",
                f"{keyword}产业化进程加速，投资机会显现"
            ],
            "半导体设备": [
                f"国产{keyword}迎来发展良机，自主可控成趋势",
                f"政策扶持力度加大，{keyword}产业加速崛起",
                f"{keyword}龙头业绩增长，行业景气度提升",
                f"全球{keyword}供应链重构，国产替代空间大"
            ],
            "AI算力": [
                f"{keyword}需求激增，相关企业受益明显",
                f"国家重视{keyword}建设，产业发展提速",
                f"云计算巨头加码{keyword}投入，市场扩容",
                f"{keyword}技术迭代加速，应用前景广泛"
            ]
        }
        
        # 获取对应关键词的标题列表
        keyword_titles = titles.get(keyword.split()[0], [f"{keyword}行业动态分析"])
        title = keyword_titles[index % len(keyword_titles)]
        
        # 生成随机情感分数
        sentiment = random.uniform(-0.5, 1.0)
        
        return NewsArticle(
            title=title,
            content=f"这里是关于{keyword}的详细新闻内容，包含了行业的最新动态、发展趋势以及投资机会分析。",
            source="财经资讯网",
            published_at=datetime.now() - timedelta(hours=random.randint(1, 24)),
            sentiment_score=round(sentiment, 3),
            keywords=[keyword],
            url=f"https://example.com/news/{keyword}_{index}"
        )
    
    def fetch_market_sentiment(self, text: str) -> float:
        """获取市场情绪分数"""
        # 模拟情感分析API
        # 实际应用中应调用真实的情感分析API
        return random.uniform(-1, 1)
    
    def get_sector_stocks(self, sector: str) -> List[StockData]:
        """获取特定行业的股票数据"""
        if sector not in self.config.sectors:
            raise ValueError(f"未知行业: {sector}")
        
        symbols = self.config.sectors[sector]["stocks"]
        return self.fetch_stock_data(symbols)
    
    def get_sector_news(self, sector: str) -> List[NewsArticle]:
        """获取特定行业的新闻数据"""
        if sector not in self.config.sectors:
            raise ValueError(f"未知行业: {sector}")
        
        keywords = self.config.sectors[sector]["keywords"]
        return self.fetch_news_data(keywords)