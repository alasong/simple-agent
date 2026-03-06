"""
报告生成器
"""
import json
from datetime import datetime
from typing import List
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端
import io
import base64

from .models import AnalysisResult, MarketInsight
from .config import SECTOR_CONFIGS

class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def generate_html_report(self, analysis_results: List[AnalysisResult], 
                           market_insight: MarketInsight) -> str:
        """生成HTML报告"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI驱动股市热点分析报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .header {{ text-align: center; background-color: #2c3e50; color: white; padding: 20px; border-radius: 10px; }}
                .summary-box {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .sector-analysis {{ background-color: white; margin: 20px 0; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .score-bar {{ height: 20px; background-color: #e0e0e0; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
                .score-fill {{ height: 100%; background-color: #3498db; }}
                .positive {{ background-color: #2ecc71; }}
                .negative {{ background-color: #e74c3c; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                .news-item {{ margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-left: 4px solid #3498db; }}
                .risk-high {{ border-left-color: #e74c3c; }}
                .risk-medium {{ border-left-color: #f39c12; }}
                .risk-low {{ border-left-color: #2ecc71; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>AI驱动股市热点分析报告</h1>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary-box">
                <h2>市场总览</h2>
                <p><strong>整体情绪:</strong> {'积极' if market_insight.overall_sentiment > 0.3 else ('消极' if market_insight.overall_sentiment < -0.3 else '中性')}</p>
                <p><strong>热门话题:</strong> {', '.join(market_insight.hot_topics)}</p>
                <p><strong>投资建议:</strong> {market_insight.recommendation}</p>
                <p><strong>风险等级:</strong> <span class="{f'risk-{market_insight.risk_level}'}">{market_insight.risk_level}</span></p>
                <p><strong>信心评分:</strong> {market_insight.confidence_score:.2f}</p>
            </div>
        """
        
        for result in analysis_results:
            # 分数条颜色
            trend_color = "positive" if result.trend_score > 0.5 else "negative"
            momentum_color = "positive" if result.momentum_score > 0 else "negative"
            sentiment_color = "positive" if result.sentiment_score > 0 else "negative"
            volatility_color = "positive" if result.volatility_score < 0.5 else "negative"
            
            html_content += f"""
            <div class="sector-analysis">
                <h2>{result.sector}行业分析</h2>
                <p>{result.summary}</p>
                
                <h3>关键指标</h3>
                <div><strong>趋势评分:</strong> <div class="score-bar"><div class="score-fill {trend_color}" style="width: {result.trend_score*100}%"></div></div> {result.trend_score:.2f}</div>
                <div><strong>动量评分:</strong> <div class="score-bar"><div class="score-fill {momentum_color}" style="width: {max(0, result.momentum_score)*100}%"></div></div> {result.momentum_score:.2f}</div>
                <div><strong>情绪评分:</strong> <div class="score-bar"><div class="score-fill {sentiment_color}" style="width: {max(0, result.sentiment_score)*100}%"></div></div> {result.sentiment_score:.2f}</div>
                <div><strong>波动评分:</strong> <div class="score-bar"><div class="score-fill {volatility_color}" style="width: {result.volatility_score*100}%"></div></div> {result.volatility_score:.2f}</div>
                
                <h3>重点关注股票</h3>
                <table>
                    <tr><th>股票代码</th><th>名称</th><th>价格</th><th>涨跌幅</th><th>成交量</th></tr>
            """
            
            for stock in result.top_stocks:
                change_class = "positive" if stock.change_percent >= 0 else "negative"
                html_content += f"""
                    <tr>
                        <td>{stock.symbol}</td>
                        <td>{stock.name}</td>
                        <td>¥{stock.price:.2f}</td>
                        <td class="{change_class}">{stock.change_percent:+.2f}%</td>
                        <td>{stock.volume:,}</td>
                    </tr>
                """
            
            html_content += "</table>"
            
            html_content += "<h3>关键新闻</h3>"
            for article in result.key_news:
                html_content += f"""
                <div class="news-item">
                    <h4>{article.title}</h4>
                    <p>{article.content[:100]}...</p>
                    <p><small>来源: {article.source} | 发布时间: {article.published_at.strftime('%Y-%m-%d %H:%M')}</small></p>
                </div>
                """
            
            html_content += "</div>"
        
        html_content += """
        </body>
        </html>
        """
        
        return html_content
    
    def generate_json_report(self, analysis_results: List[AnalysisResult], 
                           market_insight: MarketInsight) -> str:
        """生成JSON格式报告"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'market_insight': {
                'overall_sentiment': market_insight.overall_sentiment,
                'hot_topics': market_insight.hot_topics,
                'recommendation': market_insight.recommendation,
                'risk_level': market_insight.risk_level,
                'confidence_score': market_insight.confidence_score,
                'timestamp': market_insight.timestamp.isoformat()
            },
            'sector_analyses': [result.to_dict() for result in analysis_results]
        }
        
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    def generate_visualization(self, analysis_results: List[AnalysisResult]) -> str:
        """生成可视化图表"""
        sectors = [result.sector for result in analysis_results]
        trend_scores = [result.trend_score for result in analysis_results]
        momentum_scores = [result.momentum_score for result in analysis_results]
        sentiment_scores = [result.sentiment_score for result in analysis_results]
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        x = range(len(sectors))
        width = 0.25
        
        bars1 = ax.bar([i - width for i in x], trend_scores, width, label='趋势评分', color='#3498db')
        bars2 = ax.bar(x, momentum_scores, width, label='动量评分', color='#2ecc71')
        bars3 = ax.bar([i + width for i in x], sentiment_scores, width, label='情绪评分', color='#9b59b6')
        
        ax.set_xlabel('行业')
        ax.set_ylabel('评分')
        ax.set_title('各行业关键指标对比')
        ax.set_xticks(x)
        ax.set_xticklabels(sectors)
        ax.legend()
        
        # 在柱子上添加数值标签
        for bars in [bars1, bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.2f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom')
        
        ax.axhline(y=0, color='black', linewidth=0.5)
        
        # 将图表转换为base64字符串
        img_buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return img_base64