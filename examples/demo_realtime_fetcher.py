#!/usr/bin/env python3
"""
实时数据获取示例

演示如何使用 RealtimeFetcher 获取真实网络数据：
- 股票实时行情
- 股市新闻
- 市场报告
- 网络搜索

使用方法:
    .venv/bin/python examples/demo_realtime_fetcher.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def demo_stock_quote():
    """演示获取股票行情"""
    print("=" * 60)
    print("演示：获取股票实时行情")
    print("=" * 60)

    from tools.realtime_fetcher import RealtimeFetcher

    fetcher = RealtimeFetcher()

    # 测试股票代码
    test_symbols = [
        ("贵州茅台", "600519.SS"),
        ("上证指数", "000001.SS"),
        ("腾讯控股", "0700.HK"),
        ("苹果", "AAPL"),
    ]

    for name, symbol in test_symbols:
        print(f"\n正在获取 {name} ({symbol}) ...")
        quote = fetcher.get_stock_quote(symbol)

        if quote:
            print(f"  价格：{quote.price}")
            print(f"  涨跌：{quote.change:+.2f} ({quote.change_percent:+.2f}%)")
            print(f"  成交量：{quote.volume:,}")
        else:
            print(f"  ❌ 获取失败")

    print()


def demo_market_news():
    """演示获取市场新闻"""
    print("=" * 60)
    print("演示：获取 A 股市场新闻")
    print("=" * 60)

    from tools.realtime_fetcher import RealtimeFetcher

    fetcher = RealtimeFetcher()
    news = fetcher.get_stock_market_news("A 股", num_results=10)

    print(f"获取到 {len(news)} 条新闻:\n")
    for i, item in enumerate(news[:5], 1):
        print(f"{i}. {item.title}")
        print(f"   来源：{item.source}")
        print(f"   时间：{item.published}")
        print()

    print()


def demo_market_report():
    """演示获取市场报告"""
    print("=" * 60)
    print("演示：获取 A 股市场报告")
    print("=" * 60)

    from tools.realtime_fetcher import RealtimeFetcher

    fetcher = RealtimeFetcher()
    report = fetcher.get_market_report("A 股")

    print(report.summary)
    print()


def demo_web_search():
    """演示网络搜索"""
    print("=" * 60)
    print("演示：网络搜索")
    print("=" * 60)

    from tools.realtime_fetcher import RealtimeFetcher

    fetcher = RealtimeFetcher()

    queries = [
        "今日科技新闻",
        "人工智能 最新进展",
        "新能源车 销量"
    ]

    for query in queries:
        print(f"\n搜索：{query}")
        results = fetcher.search_web(query, num_results=5)

        if results:
            for i, r in enumerate(results[:3], 1):
                print(f"  {i}. {r['title']}")
                print(f"     来源：{r['source']}")
        else:
            print("  ❌ 搜索失败")

    print()


def demo_realtime_data_for_agent():
    """演示为 Agent 获取实时数据"""
    print("=" * 60)
    print("演示：为 Agent 获取实时数据（股市热点）")
    print("=" * 60)

    from tools.realtime_fetcher import RealtimeFetcher, get_market_news, get_stock

    # 方法 1: 直接调用便捷函数
    print("\n方法 1: 使用便捷函数")

    # 获取市场新闻
    news = get_market_news("A 股", num=10)
    print(f"\n获取到 {len(news)} 条市场新闻")

    # 获取热门板块（从新闻中提取）
    sector_keywords = [
        "半导体", "芯片", "人工智能", "新能源", "电动车",
        "医药", "消费", "金融", "科技", "互联网"
    ]

    sector_count = {}
    for item in news:
        for sector in sector_keywords:
            if sector in item.title or sector in item.summary:
                sector_count[sector] = sector_count.get(sector, 0) + 1

    if sector_count:
        print("\n热门板块（按新闻提及次数）:")
        for sector, count in sorted(sector_count.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {sector}: {count} 次")

    # 方法 2: 使用 RealtimeFetcher 类
    print("\n方法 2: 使用 RealtimeFetcher 类")

    fetcher = RealtimeFetcher()
    report = fetcher.get_market_report("A 股")

    print("\n" + report.summary)

    print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Simple Agent - 实时数据获取演示")
    print("=" * 60)
    print()

    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        choice = sys.argv[1].lower()
    else:
        # 非交互模式：直接运行全部演示
        print("非交互模式：运行全部演示...\n")
        demo_realtime_data_for_agent()
        print("\n演示完成!")
        return

    # 选择演示内容
    demos = {
        "1": demo_stock_quote,
        "2": demo_market_news,
        "3": demo_market_report,
        "4": demo_web_search,
        "5": demo_realtime_data_for_agent,
        "all": lambda: [demos[k]() for k in ["1", "2", "3", "4", "5"]]
    }

    if choice in demos:
        demos[choice]()
    else:
        print(f"无效选项：{choice}，运行默认演示")
        demo_realtime_data_for_agent()

    print("\n演示完成!")


if __name__ == "__main__":
    main()
