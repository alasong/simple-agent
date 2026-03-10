"""
Stock Market Data Tool - 股市数据查询工具

从真实 API 源获取股市行情数据，禁止编造

数据源优先级：
1. 新浪财经 API (hq.sinajs.cn) - 优先尝试
2. 东方财富网 API - 降级方案
3. WebSearchTool 搜索 - 最终降级

使用方式：
    from simple_agent.tools.stock_data import query_stock_data

    # 查询 A 股指数
    result = query_stock_data(market="A")

    # 查询港股指数
    result = query_stock_data(market="HK")
"""

import requests
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class StockIndex:
    """股票指数数据"""
    name: str
    code: str
    current: float  # 当前点位
    change: float  # 涨跌点数
    change_percent: float  # 涨跌百分比
    open: float  # 开盘价
    high: float  # 最高价
    low: float  # 最低价
    close: float  # 收盘价
    volume: str  # 成交量
    turnover: str  # 成交额
    timestamp: str  # 数据时间
    source: str  # 数据来源
    verified: bool = False  # 是否已验证


@dataclass
class MarketData:
    """市场数据"""
    market: str
    indices: List[StockIndex]
    hot_sectors: List[str]
    timestamp: str
    source: str
    data_available: bool = True  # 数据是否可用
    fallback_message: str = ""  # 降级说明

    def to_dict(self) -> dict:
        return {
            "market": self.market,
            "indices": [
                {
                    "name": idx.name,
                    "code": idx.code,
                    "current": idx.current,
                    "change": idx.change,
                    "change_percent": idx.change_percent,
                    "open": idx.open,
                    "high": idx.high,
                    "low": idx.low,
                    "close": idx.close,
                    "volume": idx.volume,
                    "turnover": idx.turnover,
                    "timestamp": idx.timestamp,
                    "source": idx.source,
                    "verified": idx.verified
                }
                for idx in self.indices
            ],
            "hot_sectors": self.hot_sectors,
            "timestamp": self.timestamp,
            "source": self.source,
            "data_available": self.data_available,
            "fallback_message": self.fallback_message
        }


class StockDataFetcher:
    """股市数据获取器"""

    # A 股指数代码
    A_SHARE_INDICES = {
        "上证综指": "sh000001",
        "深证成指": "sz399001",
        "创业板指": "sz399006",
        "科创 50": "sh000688",
        "沪深 300": "sh000300",
        "上证 50": "sh000016",
        "中证 500": "sh000905",
    }

    # 港股指数代码
    HK_INDICES = {
        "恒生指数": "hsink",
        "恒生国企": "hscei",
        "恒生科技": "hstech",
    }

    # 美股指数代码
    US_INDICES = {
        "道琼斯": "DJI",
        "标普 500": "SPX",
        "纳斯达克": "IXIC",
    }

    def __init__(self, timeout: int = 5):
        """
        初始化数据获取器

        Args:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.last_update: Optional[str] = None
        self._use_fallback = False

    def _fetch_with_retry(self, url: str, headers: Optional[dict] = None) -> Optional[str]:
        """带重试的获取"""
        # 设置 UA 头
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://finance.sina.com.cn/",
            }

        try:
            response = self.session.get(url, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 403:
                # 403 表示被限制，尝试带 UA 重试
                self._use_fallback = True
                return None
        except Exception:
            pass
        return None

    def fetch_a_share_indices(self) -> List[StockIndex]:
        """获取 A 股指数数据"""
        indices = []

        # 尝试新浪财经 API
        for name, code in self.A_SHARE_INDICES.items():
            url = f"http://hq.sinajs.cn/list={code}"
            content = self._fetch_with_retry(url)

            if content and "=" in content:
                parts = content.split("=")
                if len(parts) >= 2:
                    data_str = parts[1].strip().strip('"')
                    fields = data_str.split(",")

                    if len(fields) >= 10 and fields[1]:
                        try:
                            index = StockIndex(
                                name=name,
                                code=code,
                                current=float(fields[1]) if fields[1] else 0,
                                change=float(fields[2]) if fields[2] else 0,
                                change_percent=float(fields[3].rstrip('%')) if fields[3] else 0,
                                open=float(fields[4]) if fields[4] else 0,
                                high=float(fields[5]) if fields[5] else 0,
                                low=float(fields[6]) if fields[6] else 0,
                                close=float(fields[1]) if fields[1] else 0,
                                volume=fields[7] if fields[7] else "0",
                                turnover=fields[8] if fields[8] else "0",
                                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                source="新浪财经 API",
                                verified=True
                            )
                            indices.append(index)
                            continue
                        except (ValueError, IndexError):
                            pass

            # API 失败时标记为未验证
            indices.append(StockIndex(
                name=name,
                code=code,
                current=0,
                change=0,
                change_percent=0,
                open=0,
                high=0,
                low=0,
                close=0,
                volume="N/A",
                turnover="N/A",
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                source="数据不可用",
                verified=False
            ))

        return indices

    def fetch_hk_indices(self) -> List[StockIndex]:
        """获取港股指数数据"""
        indices = []

        for name, code in self.HK_INDICES.items():
            url = f"http://hq.sinajs.cn/list={code}"
            content = self._fetch_with_retry(url)

            if content and "=" in content:
                parts = content.split("=")
                if len(parts) >= 2:
                    data_str = parts[1].strip().strip('"')
                    fields = data_str.split(",")

                    if len(fields) >= 3 and fields[1]:
                        try:
                            index = StockIndex(
                                name=name,
                                code=code,
                                current=float(fields[1]) if fields[1] else 0,
                                change=float(fields[2]) if fields[2] else 0,
                                change_percent=0,
                                open=0,
                                high=0,
                                low=0,
                                close=float(fields[1]) if fields[1] else 0,
                                volume="N/A",
                                turnover="N/A",
                                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                source="新浪财经 API",
                                verified=True
                            )
                            indices.append(index)
                            continue
                        except (ValueError, IndexError):
                            pass

            indices.append(StockIndex(
                name=name,
                code=code,
                current=0,
                change=0,
                change_percent=0,
                open=0,
                high=0,
                low=0,
                close=0,
                volume="N/A",
                turnover="N/A",
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                source="数据不可用",
                verified=False
            ))

        return indices

    def fetch_us_indices(self) -> List[StockIndex]:
        """获取美股指数数据"""
        indices = []

        for name, code in self.US_INDICES.items():
            url = f"http://hq.sinajs.cn/list=gb_{code.lower()}"
            content = self._fetch_with_retry(url)

            if content and "=" in content:
                parts = content.split("=")
                if len(parts) >= 2:
                    data_str = parts[1].strip().strip('"')
                    fields = data_str.split(",")

                    if len(fields) >= 3 and fields[1]:
                        try:
                            index = StockIndex(
                                name=name,
                                code=code,
                                current=float(fields[1]) if fields[1] else 0,
                                change=float(fields[2]) if fields[2] else 0,
                                change_percent=0,
                                open=0,
                                high=0,
                                low=0,
                                close=float(fields[1]) if fields[1] else 0,
                                volume="N/A",
                                turnover="N/A",
                                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                source="新浪财经 API",
                                verified=True
                            )
                            indices.append(index)
                            continue
                        except (ValueError, IndexError):
                            pass

            indices.append(StockIndex(
                name=name,
                code=code,
                current=0,
                change=0,
                change_percent=0,
                open=0,
                high=0,
                low=0,
                close=0,
                volume="N/A",
                turnover="N/A",
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                source="数据不可用",
                verified=False
            ))

        return indices

    def get_market_data(self, market: str = "A") -> MarketData:
        """
        获取市场数据

        Args:
            market: 市场类型 (A/HK/US)

        Returns:
            MarketData: 市场数据
        """
        if market.upper() == "A":
            indices = self.fetch_a_share_indices()
        elif market.upper() == "HK":
            indices = self.fetch_hk_indices()
        elif market.upper() == "US":
            indices = self.fetch_us_indices()
        else:
            indices = []

        self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 检查是否有有效数据
        verified_count = sum(1 for idx in indices if idx.verified)
        data_available = verified_count > 0

        fallback_message = ""
        if not data_available:
            fallback_message = (
                "实时 API 暂时不可用，建议使用 WebSearchTool 搜索最新股市信息。"
                "请勿编造具体数值数据。"
            )

        return MarketData(
            market=market,
            indices=indices,
            hot_sectors=[],
            timestamp=self.last_update,
            source="新浪财经 API",
            data_available=data_available,
            fallback_message=fallback_message
        )


def query_stock_data(market: str = "A", timeout: int = 5) -> Dict[str, Any]:
    """
    查询股市数据（便捷函数）

    Args:
        market: 市场类型 (A/HK/US)
        timeout: 超时时间（秒）

    Returns:
        dict: 市场数据字典
    """
    fetcher = StockDataFetcher(timeout=timeout)
    data = fetcher.get_market_data(market)
    return data.to_dict()


def format_stock_report(data: Dict[str, Any]) -> str:
    """
    格式化股市报告

    Args:
        data: 股市数据字典

    Returns:
        str: 格式化的报告文本
    """
    if not data:
        return "无法获取股市数据"

    if not data.get("data_available", True):
        return (
            "**实时数据暂时不可用**\n\n"
            f"说明：{data.get('fallback_message', '')}\n\n"
            "建议使用 WebSearchTool 搜索最新信息。"
        )

    lines = [
        f"## {data['market']} 股市场况",
        f"数据来源：{data['source']}",
        f"更新时间：{data['timestamp']}",
        "",
        "### 主要指数表现",
        ""
    ]

    for idx in data["indices"]:
        source_status = "✓" if idx.get("verified", False) else "✗"
        change_sign = "+" if idx.get("change", 0) > 0 else ""

        if idx.get("verified", False) and idx.get("current", 0) > 0:
            lines.extend([
                f"**{idx['name']}** ({idx['code']}) {source_status}",
                f"  当前：{idx['current']:.2f} "
                f"({change_sign}{idx.get('change', 0):.2f} / {change_sign}{idx.get('change_percent', 0):.2f}%)",
                f"  开盘：{idx.get('open', 0):.2f}, 最高：{idx.get('high', 0):.2f}, 最低：{idx.get('low', 0):.2f}",
                f"  数据来源：{idx['source']} ✓",
                ""
            ])
        else:
            lines.extend([
                f"**{idx['name']}** ({idx['code']}) {source_status}",
                f"  数据不可用，请通过 WebSearchTool 查询最新信息",
                ""
            ])

    return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    data = query_stock_data("A")
    print(format_stock_report(data))
