import subprocess
import sys
import os
import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端以避免显示问题

# 导入系统组件进行验证
from models import Config
from data_fetcher import DataFetcher
from analyzer import Analyzer
from report_generator import ReportGenerator

print("🔍 验证系统组件...")
try:
    config = Config.default_config()
    fetcher = DataFetcher(config)
    analyzer = Analyzer(config)
    reporter = ReportGenerator()
    print("✅ 所有组件导入成功")
except Exception as e:
    print(f"❌ 组件导入失败: {e}")

print("\n🚀 开始运行AI驱动股市热点分析系统...")

# 直接运行系统功能
def run_analysis():
    print("="*60)
    print("AI驱动股市热点分析系统")
    print("="*60)
    from datetime import datetime
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("分析行业: 固态电池, 半导体设备, AI算力")
    print("-"*60)
    
    # 初始化系统组件
    config = Config.default_config()
    fetcher = DataFetcher(config)
    analyzer = Analyzer(config)
    reporter = ReportGenerator()
    
    # 分析指定的行业
    sectors = ['固态电池', '半导体设备', 'AI算力']
    analysis_results = []
    
    for sector in sectors:
        print(f"\n正在分析行业: {sector}")
        
        try:
            result = analyzer.analyze_sector(sector, fetcher)
            analysis_results.append(result)
            
            print(f"  - 综合得分: {result.overall_score:.3f}")
            print(f"  - 投资建议: {result.recommendation}")
            print(f"  - 置信度: {result.confidence:.1f}")
                
        except Exception as e:
            print(f"分析行业 {sector} 时出错: {str(e)}")
            continue
    
    if not analysis_results:
        print("没有成功分析任何行业")
        return
    
    # 生成市场洞察报告
    market_insight = analyzer.generate_market_insight(analysis_results)
    
    # 生成完整报告
    reporter.generate_full_report(market_insight, ".")
    
    # 打印摘要信息
    print("\n" + "="*60)
    print("分析结果摘要:")
    print("="*60)
    
    print(f"\n📈 市场概览:")
    print(f"   {market_insight.summary}")
    
    print(f"\n💡 投资策略:")
    print(f"   {market_insight.investment_strategy}")
    
    print(f"\n⚠️ 风险提示:")
    print(f"   {market_insight.risk_assessment}")
    
    print(f"\n🏆 推荐关注行业:")
    for i, rec in enumerate(market_insight.top_recommendations, 1):
        print(f"   {i}. {rec.sector}: {rec.recommendation} (得分: {rec.overall_score:.3f})")
    
    print(f"\n📊 各行业详细得分:")
    for result in analysis_results:
        print(f"   • {result.sector}:")
        print(f"     - 趋势: {result.trend_score:.3f} | 动量: {result.momentum_score:.3f}")
        print(f"     - 情绪: {result.sentiment_score:.3f} | 成交量: {result.volume_score:.3f}")
        print(f"     - 综合: {result.overall_score:.3f} | 建议: {result.recommendation}")
    
    print("\n报告已生成完毕！")
    print("- HTML报告: report.html")
    print("- JSON数据: report.json") 
    print("- 可视化图: visualization.png")
    print("="*60)

# 执行分析
if __name__ == "__main__":
    run_analysis()