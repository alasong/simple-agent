import json
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from typing import List
from models import MarketInsight, AnalysisResult
import os


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        # 设置中文字体以支持中文显示
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def generate_html_report(self, insight: MarketInsight, output_path: str = "report.html"):
        """生成HTML报告"""
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI驱动股市热点分析报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 10px;
            margin-top: 30px;
        }}
        .summary {{
            background-color: #e8f6f3;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #1abc9c;
            margin: 20px 0;
        }}
        .recommendation {{
            background-color: #fef9e7;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #f39c12;
            margin: 20px 0;
        }}
        .risk {{
            background-color: #fadbd8;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #e74c3c;
            margin: 20px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .score-badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            font-weight: bold;
            color: white;
        }}
        .high {{ background-color: #27ae60; }}
        .medium {{ background-color: #f39c12; }}
        .low {{ background-color: #e74c3c; }}
        .chart-container {{
            text-align: center;
            margin: 30px 0;
        }}
        .news-item {{
            background-color: #f8f9fa;
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
            border-left: 3px solid #95a5a6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>AI驱动股市热点分析报告</h1>
        <p><strong>报告生成时间:</strong> {insight.update_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <h3>📈 市场概览</h3>
            <p>{insight.summary}</p>
        </div>
        
        <div class="recommendation">
            <h3>💡 投资策略</h3>
            <p>{insight.investment_strategy}</p>
        </div>
        
        <div class="risk">
            <h3>⚠️ 风险提示</h3>
            <p>{insight.risk_assessment}</p>
        </div>
        
        <h2>📊 各行业分析详情</h2>
        <table>
            <thead>
                <tr>
                    <th>行业</th>
                    <th>趋势得分</th>
                    <th>动量得分</th>
                    <th>情绪得分</th>
                    <th>成交量得分</th>
                    <th>综合得分</th>
                    <th>投资建议</th>
                    <th>置信度</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for result in insight.sector_analysis:
            # 根据综合得分分配颜色等级
            score_class = "low"
            if result.overall_score >= 0.7:
                score_class = "high"
            elif result.overall_score >= 0.5:
                score_class = "medium"
                
            html_content += f"""
                <tr>
                    <td><strong>{result.sector}</strong></td>
                    <td>{result.trend_score:.3f}</td>
                    <td>{result.momentum_score:.3f}</td>
                    <td>{result.sentiment_score:.3f}</td>
                    <td>{result.volume_score:.3f}</td>
                    <td><span class="score-badge {score_class}">{result.overall_score:.3f}</span></td>
                    <td>{result.recommendation}</td>
                    <td>{result.confidence:.1f}</td>
                </tr>
"""
        
        html_content += """
            </tbody>
        </table>
        
        <h2>🏆 推荐关注行业</h2>
"""
        
        for result in insight.top_recommendations:
            html_content += f"""
        <div class="news-item">
            <h3>{result.sector} - {result.recommendation}</h3>
            <p><strong>综合得分:</strong> {result.overall_score:.3f} | 
               <strong>置信度:</strong> {result.confidence:.1f} | 
               <strong>技术指标:</strong> RSI={result.technical_indicators.rsi}, 
               波动率={result.technical_indicators.volatility:.4f}</p>
        </div>
"""
        
        html_content += """
        <h2>📈 技术指标详情</h2>
"""
        
        for result in insight.sector_analysis:
            html_content += f"""
        <div class="news-item">
            <h3>{result.sector} 技术指标</h3>
            <p><strong>RSI:</strong> {result.technical_indicators.rsi} | 
               <strong>MACD:</strong> {result.technical_indicators.macd} | 
               <strong>短期均线:</strong> {result.technical_indicators.moving_average_short} | 
               <strong>长期均线:</strong> {result.technical_indicators.moving_average_long} | 
               <strong>波动率:</strong> {result.technical_indicators.volatility}</p>
            <p><strong>布林带:</strong> 上轨={result.technical_indicators.bollinger_bands['upper']}, 
               中轨={result.technical_indicators.bollinger_bands['middle']}, 
               下轨={result.technical_indicators.bollinger_bands['lower']}</p>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML报告已生成: {output_path}")
    
    def generate_json_report(self, insight: MarketInsight, output_path: str = "report.json"):
        """生成JSON报告"""
        report_data = {
            "report_metadata": {
                "generated_at": insight.update_time.isoformat(),
                "version": "1.0",
                "description": "AI驱动的股市热点分析报告"
            },
            "market_summary": {
                "summary": insight.summary,
                "investment_strategy": insight.investment_strategy,
                "risk_assessment": insight.risk_assessment
            },
            "sector_analysis": [],
            "top_recommendations": []
        }
        
        for result in insight.sector_analysis:
            sector_data = {
                "sector": result.sector,
                "scores": {
                    "trend": result.trend_score,
                    "momentum": result.momentum_score,
                    "sentiment": result.sentiment_score,
                    "volume": result.volume_score,
                    "overall": result.overall_score
                },
                "recommendation": result.recommendation,
                "confidence": result.confidence,
                "technical_indicators": {
                    "rsi": result.technical_indicators.rsi,
                    "macd": result.technical_indicators.macd,
                    "moving_average_short": result.technical_indicators.moving_average_short,
                    "moving_average_long": result.technical_indicators.moving_average_long,
                    "bollinger_bands": result.technical_indicators.bollinger_bands,
                    "volatility": result.technical_indicators.volatility
                },
                "related_news_count": len(result.related_news),
                "stock_data_count": len(result.stock_data)
            }
            report_data["sector_analysis"].append(sector_data)
        
        for result in insight.top_recommendations:
            recommendation = {
                "sector": result.sector,
                "overall_score": result.overall_score,
                "recommendation": result.recommendation,
                "confidence": result.confidence
            }
            report_data["top_recommendations"].append(recommendation)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"JSON报告已生成: {output_path}")
    
    def generate_visualization(self, insight: MarketInsight, output_path: str = "visualization.png"):
        """生成可视化图表"""
        sectors = [result.sector for result in insight.sector_analysis]
        overall_scores = [result.overall_score for result in insight.sector_analysis]
        trend_scores = [result.trend_score for result in insight.sector_analysis]
        sentiment_scores = [result.sentiment_score for result in insight.sector_analysis]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('AI驱动股市热点分析可视化报告', fontsize=16, fontweight='bold')
        
        # 综合得分柱状图
        bars1 = ax1.bar(sectors, overall_scores, color=['#2ecc71' if s >= 0.7 else '#f39c12' if s >= 0.5 else '#e74c3c' for s in overall_scores])
        ax1.set_title('各行业综合得分')
        ax1.set_ylabel('得分')
        ax1.tick_params(axis='x', rotation=45)
        
        # 在柱子上显示数值
        for bar, score in zip(bars1, overall_scores):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{score:.3f}',
                    ha='center', va='bottom')
        
        # 趋势得分与情绪得分对比
        x = range(len(sectors))
        ax2.plot(x, trend_scores, marker='o', linewidth=2, label='趋势得分', color='#3498db')
        ax2.plot(x, sentiment_scores, marker='s', linewidth=2, label='情绪得分', color='#9b59b6')
        ax2.set_title('趋势得分 vs 情绪得分')
        ax2.set_ylabel('得分')
        ax2.set_xticks(x)
        ax2.set_xticklabels(sectors, rotation=45)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 各项得分雷达图（仅展示第一个行业作为示例）
        if insight.sector_analysis:
            first_result = insight.sector_analysis[0]
            labels = ['趋势', '动量', '情绪', '成交量']
            stats = [first_result.trend_score, first_result.momentum_score, 
                    first_result.sentiment_score, first_result.volume_score]
            
            angles = [n / float(len(labels)) * 2 * 3.14159 for n in range(len(labels))]
            angles += angles[:1]  # 闭合图形
            stats += stats[:1]
            
            ax3 = plt.subplot(2, 2, 3, projection='polar')
            ax3.plot(angles, stats, 'o-', linewidth=2, color='#e67e22')
            ax3.fill(angles, stats, alpha=0.25, color='#e67e22')
            ax3.set_xticks(angles[:-1])
            ax3.set_xticklabels(labels)
            ax3.set_title(f'{first_result.sector} 各项指标雷达图', pad=20)
        
        # 成交量得分分布
        volume_scores = [result.volume_score for result in insight.sector_analysis]
        bars4 = ax4.bar(sectors, volume_scores, color='#1abc9c')
        ax4.set_title('各行业成交量得分')
        ax4.set_ylabel('成交量得分')
        ax4.tick_params(axis='x', rotation=45)
        
        # 在柱子上显示数值
        for bar, score in zip(bars4, volume_scores):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{score:.3f}',
                    ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"可视化图表已生成: {output_path}")
    
    def generate_full_report(self, insight: MarketInsight, output_dir: str = "."):
        """生成完整报告（HTML、JSON、PNG）"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        html_path = os.path.join(output_dir, "report.html")
        json_path = os.path.join(output_dir, "report.json")
        png_path = os.path.join(output_dir, "visualization.png")
        
        self.generate_html_report(insight, html_path)
        self.generate_json_report(insight, json_path)
        self.generate_visualization(insight, png_path)
        
        print(f"完整报告已生成在目录: {output_dir}")
        print(f"  - HTML报告: {html_path}")
        print(f"  - JSON数据: {json_path}")
        print(f"  - 可视化图: {png_path}")