"""
AI驱动股市热点分析工具主应用
"""
import argparse
import sys
from datetime import datetime
from typing import List
import logging

from .analyzer import StockAnalyzer
from .report_generator import ReportGenerator
from .models import AnalysisResult, MarketInsight
from .config import get_sector_configs

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from core.config_loader import get_config

class StockAnalysisApp:
    """股市分析应用主类"""
    
    def __init__(self):
        self.analyzer = StockAnalyzer()
        self.report_generator = ReportGenerator()
        self._config = get_config()
    
    def _get_output_dir(self) -> str:
        """获取输出目录"""
        return self._config.get('directories.reports', './reports')
    
    def run_analysis(self) -> tuple[List[AnalysisResult], MarketInsight]:
        """运行完整分析"""
        logger.info("开始执行股市热点分析...")
        
        # 获取各行业分析结果
        analysis_results = self.analyzer.get_comprehensive_analysis()
        
        # 生成市场洞察
        market_insight = self.generate_market_insight(analysis_results)
        
        logger.info("分析完成")
        return analysis_results, market_insight
    
    def generate_market_insight(self, analysis_results: List[AnalysisResult]) -> MarketInsight:
        """基于分析结果生成市场洞察"""
        if not analysis_results:
            return MarketInsight(
                overall_sentiment=0.0,
                hot_topics=[],
                recommendation="暂无数据",
                risk_level="medium",
                confidence_score=0.0
            )
        
        # 计算整体情绪
        overall_sentiment = sum(r.sentiment_score for r in analysis_results) / len(analysis_results)
        
        # 获取行业配置
        sector_configs = get_sector_configs()
        
        # 提取热门话题
        hot_topics = list(sector_configs.keys())
        
        # 生成投资建议
        if overall_sentiment > 0.3:
            recommendation = "当前市场情绪积极，可适当增加相关板块配置"
        elif overall_sentiment < -0.3:
            recommendation = "当前市场情绪消极，建议谨慎操作，控制仓位"
        else:
            recommendation = "当前市场情绪中性，建议观望或进行结构性配置"
        
        # 评估风险等级
        avg_volatility = sum(r.volatility_score for r in analysis_results) / len(analysis_results)
        if avg_volatility > 0.7:
            risk_level = "high"
        elif avg_volatility > 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # 获取行业配置
        sector_configs = get_sector_configs()
        # 计算信心评分
        confidence_score = min(1.0, len(analysis_results) / len(sector_configs) * 0.8 + 0.2)
        
        return MarketInsight(
            overall_sentiment=overall_sentiment,
            hot_topics=hot_topics,
            recommendation=recommendation,
            risk_level=risk_level,
            confidence_score=confidence_score
        )
    
    def save_reports(self, analysis_results: List[AnalysisResult], 
                     market_insight: MarketInsight, output_dir: str = None):
        """保存分析报告"""
        import os
        from datetime import datetime
        
        # 使用配置的输出目录
        if output_dir is None:
            output_dir = self._get_output_dir()
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成报告文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成并保存HTML报告
        html_report = self.report_generator.generate_html_report(analysis_results, market_insight)
        html_path = f"{output_dir}/stock_analysis_{timestamp}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        logger.info(f"HTML报告已保存至: {html_path}")
        
        # 生成并保存JSON报告
        json_report = self.report_generator.generate_json_report(analysis_results, market_insight)
        json_path = f"{output_dir}/stock_analysis_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(json_report)
        logger.info(f"JSON报告已保存至: {json_path}")
        
        # 生成并保存可视化图表
        chart_base64 = self.report_generator.generate_visualization(analysis_results)
        chart_path = f"{output_dir}/visualization_{timestamp}.png"
        import base64
        with open(chart_path, 'wb') as f:
            f.write(base64.b64decode(chart_base64))
        logger.info(f"可视化图表已保存至: {chart_path}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI驱动股市热点分析工具')
    parser.add_argument('--output-dir', type=str, default='./reports', 
                       help='报告输出目录 (默认: ./reports)')
    parser.add_argument('--format', type=str, choices=['html', 'json', 'both'], 
                       default='both', help='输出格式 (默认: both)')
    parser.add_argument('--verbose', action='store_true', 
                       help='显示详细日志信息')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    app = StockAnalysisApp()
    
    try:
        # 执行分析
        analysis_results, market_insight = app.run_analysis()
        
        # 显示简要结果
        print("\n=== 股市热点分析结果 ===")
        for result in analysis_results:
            print(f"\n{result.sector}行业:")
            print(f"  趋势评分: {result.trend_score:.2f}")
            print(f"  动量评分: {result.momentum_score:.2f}")
            print(f"  情绪评分: {result.sentiment_score:.2f}")
            print(f"  波动评分: {result.volatility_score:.2f}")
            print(f"  摘要: {result.summary}")
        
        print(f"\n=== 市场总览 ===")
        print(f"整体情绪: {'积极' if market_insight.overall_sentiment > 0.3 else ('消极' if market_insight.overall_sentiment < -0.3 else '中性')}")
        print(f"热门话题: {', '.join(market_insight.hot_topics)}")
        print(f"投资建议: {market_insight.recommendation}")
        print(f"风险等级: {market_insight.risk_level}")
        print(f"信心评分: {market_insight.confidence_score:.2f}")
        
        # 保存报告
        app.save_reports(analysis_results, market_insight, args.output_dir)
        
        print(f"\n报告已保存至: {args.output_dir}")
        
    except KeyboardInterrupt:
        print("\n分析过程被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"分析过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()