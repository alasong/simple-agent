"""
AI驱动股市热点分析系统使用示例
"""
from stock_analyzer.app import StockAnalysisApp
from stock_analyzer.analyzer import StockAnalyzer
from stock_analyzer.models import AnalysisResult, MarketInsight

def example_usage():
    """演示如何使用股市分析系统"""
    print("=== AI驱动股市热点分析系统使用示例 ===\n")
    
    # 创建分析应用实例
    app = StockAnalysisApp()
    
    print("1. 执行完整分析...")
    analysis_results, market_insight = app.run_analysis()
    
    print("\n2. 显示分析结果...")
    for result in analysis_results:
        print(f"\n--- {result.sector}行业分析 ---")
        print(f"趋势评分: {result.trend_score:.2f}")
        print(f"动量评分: {result.momentum_score:.2f}")
        print(f"情绪评分: {result.sentiment_score:.2f}")
        print(f"波动评分: {result.volatility_score:.2f}")
        print(f"摘要: {result.summary}")
        
        print(f"\n关注股票 ({len(result.top_stocks)}只):")
        for i, stock in enumerate(result.top_stocks[:3]):  # 显示前3只
            print(f"  {i+1}. {stock.name} ({stock.symbol}) - ¥{stock.price:.2f} ({stock.change_percent:+.2f}%)")
        
        print(f"\n关键新闻 ({len(result.key_news)}篇):")
        for i, article in enumerate(result.key_news[:2]):  # 显示前2篇
            print(f"  {i+1}. {article.title}")
            print(f"     来源: {article.source}, 情绪分: {article.sentiment_score:.2f}")
    
    print(f"\n3. 市场总体洞察:")
    print(f"整体情绪: {'积极' if market_insight.overall_sentiment > 0.3 else ('消极' if market_insight.overall_sentiment < -0.3 else '中性')}")
    print(f"热门话题: {', '.join(market_insight.hot_topics)}")
    print(f"投资建议: {market_insight.recommendation}")
    print(f"风险等级: {market_insight.risk_level}")
    print(f"信心评分: {market_insight.confidence_score:.2f}")
    
    print(f"\n4. 生成并保存报告...")
    app.save_reports(analysis_results, market_insight, './example_reports')
    print("报告已保存到 ./example_reports 目录")

def advanced_example():
    """高级用法示例"""
    print("\n=== 高级用法示例 ===\n")
    
    # 直接使用分析器进行特定行业分析
    analyzer = StockAnalyzer()
    
    # 分析特定行业
    print("分析固态电池行业...")
    solid_battery_result = analyzer.analyze_sector("solid_state_battery")
    print(f"趋势评分: {solid_battery_result.trend_score:.2f}")
    print(f"情绪评分: {solid_battery_result.sentiment_score:.2f}")
    
    print("\n分析半导体设备行业...")
    semicond_result = analyzer.analyze_sector("semiconductor_equipment")
    print(f"动量评分: {semicond_result.momentum_score:.2f}")
    print(f"波动评分: {semicond_result.volatility_score:.2f}")
    
    print("\n分析AI算力行业...")
    ai_result = analyzer.analyze_sector("ai_computing")
    print(f"情绪评分: {ai_result.sentiment_score:.2f}")
    print(f"趋势评分: {ai_result.trend_score:.2f}")

if __name__ == "__main__":
    example_usage()
    advanced_example()
    print("\n示例执行完成！")