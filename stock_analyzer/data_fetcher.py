"""
数据获取模块
"""
import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import time
import logging

from .models import StockData, NewsArticle
from core.config_loader import get_config

# yfinance 为可选依赖
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None

logger = logging.getLogger(__name__)

# Mock 数据开关
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
MOCK_DATA_DIR = Path(__file__).parent / "mock_data"


def _load_mock_news() -> List[Dict]:
    """加载 mock 新闻数据"""
    mock_file = MOCK_DATA_DIR / "news.json"
    if mock_file.exists():
        with open(mock_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


class DataFetcher:
    """数据获取器"""
    
    def __init__(self):
        config = get_config()
        user_agent = config.get('user_agent', 'StockAnalyzer/1.0')
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent
        })
        
    def fetch_stock_data(self, symbols: List[str]) -> List[StockData]:
        """获取股票数据"""
        if not YFINANCE_AVAILABLE:
            logger.warning("yfinance 未安装，无法获取股票数据")
            return []
        
        stocks = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="1d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = info.get('previousClose', current_price)
                    change = current_price - prev_close
                    change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
                    
                    stock_data = StockData(
                        symbol=symbol,
                        name=info.get('longName', symbol),
                        price=current_price,
                        change=change,
                        change_percent=change_percent,
                        volume=int(hist['Volume'].iloc[-1]),
                        market_cap=info.get('marketCap'),
                        pe_ratio=info.get('trailingPE'),
                        pb_ratio=info.get('priceToBook')
                    )
                    stocks.append(stock_data)
                
                # 避免API限制
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                continue
        
        return stocks
    
    def fetch_news(self, query: str, max_articles: int = 10) -> List[NewsArticle]:
        """获取新闻数据"""
        articles = []
        
        # 检查是否使用 mock 数据
        if USE_MOCK_DATA:
            return self._fetch_mock_news(query, max_articles)
        
        # 尝试使用真实 API
        # 注意：需要在环境变量中配置 NEWS_API_KEY
        try:
            from .config import get_news_api_key
            api_key = get_news_api_key()
            # 这里可以添加真实 API 调用
            # 目前降级使用 mock 数据
            logger.info("News API 未配置或不可用，使用 mock 数据")
            return self._fetch_mock_news(query, max_articles)
        except ValueError:
            # API key 未配置，使用 mock 数据
            logger.info("News API key 未配置，使用 mock 数据")
            return self._fetch_mock_news(query, max_articles)
    
    def _fetch_mock_news(self, query: str, max_articles: int = 10) -> List[NewsArticle]:
        """从 mock 数据文件加载新闻"""
        articles = []
        mock_news = _load_mock_news()
        
        for item in mock_news:
            if len(articles) >= max_articles:
                break
            
            # 简单的关键词匹配
            if query.lower() in item.get('title', '').lower() or \
               query.lower() in item.get('content', '').lower() or \
               query == "":  # 空查询返回所有
                article = NewsArticle(
                    title=item['title'],
                    content=item['content'],
                    source=item['source'],
                    published_at=datetime.now() - timedelta(hours=len(articles) * 2),
                    sentiment_score=item.get('sentiment_score', 0.5),
                    relevance_score=item.get('relevance_score', 0.5),
                    url=item.get('url', '')
                )
                articles.append(article)
        
        return articles
    
    def fetch_historical_data(self, symbol: str, period: str = "1mo") -> pd.DataFrame:
        """获取历史数据"""
        if not YFINANCE_AVAILABLE:
            logger.warning("yfinance 未安装，无法获取历史数据")
            return pd.DataFrame()
        
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            return hist
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, hist_data: pd.DataFrame) -> Dict[str, Any]:
        """计算技术指标"""
        if hist_data.empty:
            return {}
        
        # 简单移动平均线
        hist_data['SMA_20'] = hist_data['Close'].rolling(window=20).mean()
        hist_data['SMA_50'] = hist_data['Close'].rolling(window=50).mean()
        
        # RSI
        delta = hist_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # 波动率
        volatility = hist_data['Close'].pct_change().rolling(window=20).std() * (252 ** 0.5)
        
        latest_data = hist_data.iloc[-1]
        
        return {
            'sma_20': latest_data['SMA_20'],
            'sma_50': latest_data['SMA_50'],
            'rsi': latest_data['RSI'] if not pd.isna(latest_data['RSI']) else None,
            'volatility': latest_data['Volatility'] if not pd.isna(latest_data['Volatility']) else None
        }
