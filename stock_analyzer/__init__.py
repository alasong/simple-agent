"""
AI驱动股市热点分析系统
入口文件
"""
from stock_analyzer.app import StockAnalysisApp
from stock_analyzer.analyzer import StockAnalyzer
from stock_analyzer.data_fetcher import DataFetcher
from stock_analyzer.report_generator import ReportGenerator
from stock_analyzer.models import *
from stock_analyzer.config import *

__version__ = "1.0.0"
__author__ = "AI Stock Analyzer Team"

def run_full_analysis(output_dir="./reports"):
    """
    运行完整的股市热点分析
    :param output_dir: 报告输出目录
    :return: 分析结果和市场洞察
    """
    app = StockAnalysisApp()
    analysis_results, market_insight = app.run_analysis()
    app.save_reports(analysis_results, market_insight, output_dir)
    return analysis_results, market_insight

def quick_analysis():
    """
    快速分析，返回结果但不生成报告
    :return: 分析结果和市场洞察
    """
    app = StockAnalysisApp()
    return app.run_analysis()

# 导出主要类和函数，方便外部使用
__all__ = [
    'StockAnalysisApp',
    'StockAnalyzer', 
    'DataFetcher',
    'ReportGenerator',
    'StockData',
    'NewsArticle', 
    'AnalysisResult',
    'MarketInsight',
    'SECTOR_CONFIGS',
    'run_full_analysis',
    'quick_analysis'
]

if __name__ == "__main__":
    # 如果直接运行此文件，执行完整分析
    import sys
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "./reports"
    run_full_analysis(output_dir)