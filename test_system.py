#!/usr/bin/env python
"""
测试脚本：验证AI驱动股市热点分析系统的基本功能
"""
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    try:
        from stock_analyzer.app import StockAnalysisApp
        from stock_analyzer.analyzer import StockAnalyzer
        from stock_analyzer.data_fetcher import DataFetcher
        from stock_analyzer.report_generator import ReportGenerator
        from stock_analyzer.models import StockData, NewsArticle, AnalysisResult, MarketInsight
        from stock_analyzer.config import SECTOR_CONFIGS
        print("✓ 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n测试基本功能...")
    try:
        # 创建分析器实例
        analyzer = StockAnalyzer()
        print("✓ 分析器实例创建成功")
        
        # 获取配置的行业列表
        sectors = list(SECTOR_CONFIGS.keys())
        print(f"✓ 配置的行业: {sectors}")
        
        # 创建报告生成器
        generator = ReportGenerator()
        print("✓ 报告生成器实例创建成功")
        
        return True
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")
        return False

def test_single_sector_analysis():
    """测试单个行业分析"""
    print("\n测试单个行业分析...")
    try:
        analyzer = StockAnalyzer()
        
        # 分析第一个行业
        sectors = list(SECTOR_CONFIGS.keys())
        if sectors:
            result = analyzer.analyze_sector(sectors[0])
            print(f"✓ {result.sector}行业分析完成")
            print(f"  趋势评分: {result.trend_score:.2f}")
            print(f"  动量评分: {result.momentum_score:.2f}")
            print(f"  情绪评分: {result.sentiment_score:.2f}")
            print(f"  波动评分: {result.volatility_score:.2f}")
            print(f"  关注股票数量: {len(result.top_stocks)}")
            print(f"  关键新闻数量: {len(result.key_news)}")
            return True
        else:
            print("✗ 没有配置任何行业")
            return False
    except Exception as e:
        print(f"✗ 单个行业分析测试失败: {e}")
        return False

def test_comprehensive_analysis():
    """测试综合分析"""
    print("\n测试综合分析...")
    try:
        analyzer = StockAnalyzer()
        results = analyzer.get_comprehensive_analysis()
        print(f"✓ 综合分析完成，分析了 {len(results)} 个行业")
        
        for result in results:
            print(f"  - {result.sector}: 趋势={result.trend_score:.2f}, 情绪={result.sentiment_score:.2f}")
        
        # 生成市场洞察
        insight = analyzer.generate_market_insight(results)
        print(f"✓ 市场洞察生成完成")
        print(f"  整体情绪: {insight.overall_sentiment:.2f}")
        print(f"  风险等级: {insight.risk_level}")
        print(f"  信心评分: {insight.confidence_score:.2f}")
        
        return True
    except Exception as e:
        print(f"✗ 综合分析测试失败: {e}")
        return False

def test_report_generation():
    """测试报告生成"""
    print("\n测试报告生成...")
    try:
        analyzer = StockAnalyzer()
        results = analyzer.get_comprehensive_analysis()
        insight = analyzer.generate_market_insight(results)
        
        generator = ReportGenerator()
        
        # 生成HTML报告
        html_report = generator.generate_html_report(results, insight)
        print(f"✓ HTML报告生成成功 (长度: {len(html_report)} 字符)")
        
        # 生成JSON报告
        json_report = generator.generate_json_report(results, insight)
        print(f"✓ JSON报告生成成功 (长度: {len(json_report)} 字符)")
        
        # 生成可视化图表
        chart_base64 = generator.generate_visualization(results)
        print(f"✓ 可视化图表生成成功 (长度: {len(chart_base64)} 字符)")
        
        return True
    except Exception as e:
        print(f"✗ 报告生成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("AI驱动股市热点分析系统 - 功能测试")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tests = [
        test_imports,
        test_basic_functionality,
        test_single_sector_analysis,
        test_comprehensive_analysis,
        test_report_generation
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"测试完成: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("✓ 所有测试通过！系统功能正常。")
        return 0
    else:
        print("✗ 部分测试失败，请检查系统配置。")
        return 1

if __name__ == "__main__":
    exit(main())