"""
Real-time Data Fetcher - 实时数据获取器

整合多种数据源，获取真实网络数据：
- 股票/金融数据（yfinance）
- 新闻资讯（RSS/新闻 API）
- 网络搜索（多引擎）
- 社交媒体热点

使用示例：
    from tools.realtime_fetcher import RealtimeFetcher

    fetcher = RealtimeFetcher()

    # 获取股市热点
    news = fetcher.get_stock_market_news()

    # 获取股票实时数据
    stock = fetcher.get_stock_quote("600519.ss")

    # 搜索最新信息
    results = fetcher.search_web("今日科技新闻")
"""

import os
import json
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class StockQuote:
    """股票行情"""
    symbol: str
    name: str
    price: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    volume: int = 0
    market_cap: int = 0
    high: float = 0.0
    low: float = 0.0
    open: float = 0.0
    previous_close: float = 0.0
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.price,
            "change": self.change,
            "change_percent": self.change_percent,
            "volume": self.volume,
            "market_cap": self.market_cap,
            "high": self.high,
            "low": self.low,
            "open": self.open,
            "previous_close": self.previous_close,
            "timestamp": self.timestamp
        }

    def summary(self) -> str:
        """生成摘要"""
        arrow = "↑" if self.change >= 0 else "↓"
        return (
            f"{self.name} ({self.symbol}): {self.price:.2f} "
            f"{arrow} {self.change:+.2f} ({self.change_percent:+.2f}%)"
        )


@dataclass
class NewsItem:
    """新闻条目"""
    title: str
    source: str
    url: str
    published: str
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "published": self.published,
            "summary": self.summary
        }


@dataclass
class MarketReport:
    """市场报告"""
    market: str
    timestamp: str
    indices: Dict[str, float] = field(default_factory=dict)
    hot_sectors: List[str] = field(default_factory=list)
    top_gainers: List[StockQuote] = field(default_factory=list)
    top_losers: List[StockQuote] = field(default_factory=list)
    news: List[NewsItem] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "market": self.market,
            "timestamp": self.timestamp,
            "indices": self.indices,
            "hot_sectors": self.hot_sectors,
            "top_gainers": [s.to_dict() for s in self.top_gainers],
            "top_losers": [s.to_dict() for s in self.top_losers],
            "news": [n.to_dict() for n in self.news],
            "summary": self.summary
        }


class RealtimeFetcher:
    """实时数据获取器"""

    # A 股股票代码后缀
    A_STOCK_SUFFIX = {
        "sh": ".SS",  # 上交所
        "sz": ".SZ"   # 深交所
    }

    def __init__(self, timeout: int = 10):
        """
        初始化

        Args:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout
        self._session = None

    @property
    def session(self):
        """获取 requests session"""
        if self._session is None:
            import requests
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/120.0.0.0 Safari/537.36"
            })
        return self._session

    def get_stock_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        获取股票实时行情

        Args:
            symbol: 股票代码（如 600519.ss 或 sh600519）

        Returns:
            StockQuote 对象，失败返回 None
        """
        # 尝试 yfinance
        quote = self._get_stock_yfinance(symbol)
        if quote:
            return quote

        # 尝试从网页获取
        quote = self._get_stock_web(symbol)
        return quote

    def _get_stock_yfinance(self, symbol: str) -> Optional[StockQuote]:
        """通过 yfinance 获取股票行情"""
        try:
            import yfinance as yf

            # 处理股票代码格式
            symbol = self._normalize_symbol(symbol)

            stock = yf.Ticker(symbol)
            info = stock.info
            fast_info = stock.fast_info

            # 获取实时数据
            price = fast_info.get('lastPrice', info.get('regularMarketPrice', 0))
            change = fast_info.get('regularMarketChange', 0)
            change_percent = fast_info.get('regularMarketChangePercent', 0)

            quote = StockQuote(
                symbol=symbol,
                name=info.get("shortName", info.get("name", symbol)),
                price=price,
                change=change,
                change_percent=change_percent,
                volume=info.get("volume", 0),
                market_cap=info.get("marketCap", 0),
                high=info.get("dayHigh", 0),
                low=info.get("dayLow", 0),
                open=info.get("open", 0),
                previous_close=info.get("previousClose", 0),
                timestamp=datetime.now().isoformat()
            )
            return quote

        except ImportError:
            pass
        except Exception as e:
            print(f"[yfinance] 获取股票 {symbol} 失败：{e}")

        return None

    def _get_stock_web(self, symbol: str) -> Optional[StockQuote]:
        """通过网页获取股票行情"""
        try:
            from bs4 import BeautifulSoup

            # 使用 Yahoo Finance 网页版
            symbol = self._normalize_symbol(symbol)
            url = f"https://finance.yahoo.com/quote/{symbol}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/120.0.0.0 Safari/537.36"
            }

            response = self.session.get(url, headers=headers, timeout=self.timeout)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # 尝试解析 Yahoo Finance 页面
            # 注意：Yahoo Finance 页面结构可能变化，这里使用通用选择器
            price_text = ""
            for selector in ['fin-streamer[data-field="regularMarketPrice"]',
                           'span[data-field="regularMarketPrice"]']:
                elem = soup.select_one(selector)
                if elem:
                    price_text = elem.get_text(strip=True)
                    break

            if price_text:
                try:
                    price = float(price_text.replace(',', ''))
                    return StockQuote(
                        symbol=symbol,
                        name=symbol,
                        price=price,
                        timestamp=datetime.now().isoformat()
                    )
                except ValueError:
                    pass

        except Exception as e:
            print(f"[Web] 获取股票 {symbol} 失败：{e}")

        return None

    def _normalize_symbol(self, symbol: str) -> str:
        """标准化股票代码格式"""
        symbol = symbol.strip().upper()

        # 处理 A 股代码
        if symbol.startswith("SH"):
            return symbol[2:] + ".SS"
        elif symbol.startswith("SZ"):
            return symbol[2:] + ".SZ"
        elif symbol.startswith("60") or symbol.startswith("68"):
            return symbol + ".SS"
        elif symbol.startswith("00") or symbol.startswith("30"):
            return symbol + ".SZ"

        return symbol

    def get_stock_market_news(
        self,
        market: str = "A 股",
        num_results: int = 10
    ) -> List[NewsItem]:
        """
        获取股市新闻

        Args:
            market: 市场（A 股/港股/美股）
            num_results: 返回结果数量

        Returns:
            NewsItem 列表
        """
        news_items = []

        # 尝试从网页获取
        news_items.extend(self._get_news_web(market, num_results))

        # 尝试使用 WebSearch 工具
        if len(news_items) < num_results:
            search_results = self.search_web(f"{market} 今日热点 新闻", num_results=num_results)
            for r in search_results:
                news_items.append(NewsItem(
                    title=r.get("title", ""),
                    source=r.get("source", ""),
                    url=r.get("url", ""),
                    published=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    summary=r.get("snippet", "")[:200]
                ))

        return news_items[:num_results]

    def _get_news_web(self, market: str, num_results: int) -> List[NewsItem]:
        """从网页获取新闻"""
        news_items = []

        try:
            from bs4 import BeautifulSoup

            # 东方财富网滚动新闻
            urls = {
                "A 股": "https://news.eastmoney.com/kxzc/",
                "港股": "https://news.eastmoney.com/gg/",
                "美股": "https://news.eastmoney.com/gjs/"
            }

            url = urls.get(market, urls["A 股"])
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/120.0.0.0 Safari/537.36"
            }

            response = self.session.get(url, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # 查找新闻条目
                for item in soup.select('.news-item, .article, li')[:num_results]:
                    title_elem = item.select_one('a.title, a, h3, .title')
                    time_elem = item.select_one('.time, .date, span, small')

                    if title_elem:
                        news_items.append(NewsItem(
                            title=title_elem.get_text(strip=True)[:100],
                            source="东方财富网",
                            url="https://news.eastmoney.com" + title_elem.get('href', '') if title_elem.get('href', '').startswith('/') else title_elem.get('href', ''),
                            published=time_elem.get_text(strip=True) if time_elem else "",
                            summary=""
                        ))

        except Exception as e:
            print(f"[Web News] 获取失败：{e}")

        return news_items

    def search_web(
        self,
        query: str,
        num_results: int = 10,
        news_only: bool = False
    ) -> List[Dict]:
        """
        搜索网页/新闻

        Args:
            query: 搜索词
            num_results: 返回结果数量
            news_only: 只搜索新闻

        Returns:
            搜索结果列表
        """
        # 使用现有的 WebSearch
        try:
            from tools.web_search import WebSearch
            results = WebSearch(
                query=query,
                num_results=num_results
            )

            return [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "source": self._extract_domain(r.url)
                }
                for r in results.search_results
            ]

        except Exception as e:
            print(f"[WebSearch] 搜索失败：{e}")
            return []

    def _extract_domain(self, url: str) -> str:
        """从 URL 提取域名"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc or url

    def get_market_report(self, market: str = "A 股") -> MarketReport:
        """
        获取市场报告

        Args:
            market: 市场名称

        Returns:
            MarketReport 对象
        """
        report = MarketReport(
            market=market,
            timestamp=datetime.now().isoformat()
        )

        # 获取主要指数
        indices = self._get_market_indices(market)
        report.indices = indices

        # 获取热门板块
        sectors = self._get_hot_sectors(market)
        report.hot_sectors = sectors

        # 获取新闻
        news = self.get_stock_market_news(market, num_results=10)
        report.news = news

        # 生成摘要
        report.summary = self._generate_market_summary(report)

        return report

    def _get_market_indices(self, market: str) -> Dict[str, float]:
        """获取市场主要指数"""
        indices = {}

        index_symbols = {
            "A 股": {
                "上证指数": "000001.SS",
                "深证成指": "399001.SZ",
                "创业板指": "399006.SZ"
            },
            "港股": {
                "恒生指数": "^HSI",
                "国企指数": "^HSCEI"
            },
            "美股": {
                "道琼斯": "^DJI",
                "纳斯达克": "^IXIC",
                "标普 500": "^GSPC"
            }
        }

        symbols = index_symbols.get(market, {})
        for name, symbol in symbols.items():
            quote = self.get_stock_quote(symbol)
            if quote and quote.price > 0:
                indices[name] = quote.price

        return indices

    def _get_hot_sectors(self, market: str) -> List[str]:
        """获取热门板块"""
        sectors = []

        # 尝试从网页获取
        try:
            from bs4 import BeautifulSoup

            url = "http://vip.stock.finance.sina.com.cn/quotes/services/view.php?table=cyb&sort=changepercent&order=desc"
            headers = {"User-Agent": "Mozilla/5.0"}

            response = self.session.get(url, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 解析板块数据
                # ...

        except Exception as e:
            print(f"[Sectors] 获取失败：{e}")

        #  fallback：从新闻中提取
        news = self.get_stock_market_news(market, num_results=20)
        sector_keywords = [
            "半导体", "芯片", "人工智能", "新能源", "电动车",
            "医药", "消费", "金融", "银行", "保险",
            "科技", "互联网", "游戏", "传媒", "光伏"
        ]

        sector_count = {}
        for item in news:
            for sector in sector_keywords:
                if sector in item.title or sector in item.summary:
                    sector_count[sector] = sector_count.get(sector, 0) + 1

        # 按提及次数排序
        sectors = sorted(
            sector_count.keys(),
            key=lambda x: sector_count[x],
            reverse=True
        )[:10]

        return sectors

    def _generate_market_summary(self, report: MarketReport) -> str:
        """生成市场摘要"""
        lines = [
            f"【{report.market} 市场报告】",
            f"更新时间：{report.timestamp}",
            ""
        ]

        # 指数
        if report.indices:
            lines.append("主要指数:")
            for name, value in report.indices.items():
                lines.append(f"  - {name}: {value:.2f}")
            lines.append("")

        # 热门板块
        if report.hot_sectors:
            lines.append("热门板块:")
            for sector in report.hot_sectors[:5]:
                lines.append(f"  - {sector}")
            lines.append("")

        # 最新新闻
        if report.news:
            lines.append("最新新闻:")
            for i, item in enumerate(report.news[:5], 1):
                lines.append(f"  {i}. {item.title}")
            lines.append("")

        return "\n".join(lines)


# 便捷函数
def get_stock(symbol: str) -> Optional[StockQuote]:
    """快速获取股票行情"""
    return RealtimeFetcher().get_stock_quote(symbol)


def get_market_news(market: str = "A 股", num: int = 10) -> List[NewsItem]:
    """快速获取市场新闻"""
    return RealtimeFetcher().get_stock_market_news(market, num)


def get_market_report(market: str = "A 股") -> MarketReport:
    """获取市场报告"""
    return RealtimeFetcher().get_market_report(market)


def search_web(query: str, num: int = 10) -> List[Dict]:
    """快速搜索网页"""
    return RealtimeFetcher().search_web(query, num)
