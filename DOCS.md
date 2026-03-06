# AI驱动股市热点分析系统

一个集成固态电池、半导体设备、AI算力三个前沿科技领域的实时数据分析和智能评估系统。

## 项目概述

本项目是一个AI驱动的股市热点分析系统，旨在通过整合多个维度的数据（股价、交易量、新闻情绪等），为投资者提供热点板块预测和投资建议。系统重点关注三个前沿科技领域：固态电池、半导体设备和AI算力。

## 架构设计

### 核心组件

1. **数据获取层 (data_fetcher.py)**
   - 获取实时股价数据
   - 获取相关新闻资讯
   - 计算技术指标

2. **分析引擎 (analyzer.py)**
   - 计算趋势评分
   - 计算动量评分
   - 计算情绪评分
   - 计算波动评分

3. **报告生成器 (report_generator.py)**
   - 生成HTML可视化报告
   - 生成JSON数据报告
   - 生成可视化图表

4. **数据模型 (models.py)**
   - StockData: 股票数据模型
   - NewsArticle: 新闻文章模型
   - AnalysisResult: 分析结果模型
   - MarketInsight: 市场洞察模型

### 配置管理 (config.py)

定义了三个重点行业的配置：
- 固态电池: 关键词、相关股票、API端点
- 半导体设备: 关键词、相关股票、API端点
- AI算力: 关键词、相关股票、API端点

## 功能特性

### 1. 多维度数据整合
- 实时股价数据
- 交易量信息
- 市场新闻情绪
- 技术指标分析

### 2. 智能分析引擎
- **趋势评分**: 衡量行业整体上涨/下跌趋势
- **动量评分**: 衡量市场参与热度
- **情绪评分**: 基于新闻的情感分析
- **波动评分**: 衡量市场风险水平

### 3. 实时监控
- 持续跟踪三大热点行业
- 实时更新数据和评分
- 异常情况检测

### 4. 可视化报告
- HTML格式交互式报告
- JSON格式数据接口
- PNG格式可视化图表

### 5. 投资建议
- 基于数据分析的投资策略
- 风险评估和等级划分
- 信心评分机制

## 技术栈

- Python 3.7+
- yfinance: 股票数据获取
- requests: HTTP请求
- pandas: 数据处理
- numpy: 数值计算
- matplotlib: 数据可视化
- dataclasses: 数据模型定义

## 安装部署

### 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd stock-analyzer

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
# 或
pip install -e .
```

### API配置

在使用前需要配置API密钥：

```bash
export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_api_key"
export NEWS_API_KEY="your_news_api_key"
```

或者创建`.env`文件：

```
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
NEWS_API_KEY=your_news_api_key
```

## 使用方法

### 命令行使用

```bash
# 运行完整分析，默认输出到./reports目录
python -m stock_analyzer.app

# 指定输出目录
python -m stock_analyzer.app --output-dir ./my_reports

# 显示详细日志
python -m stock_analyzer.app --verbose
```

### 作为模块使用

```python
from stock_analyzer.app import StockAnalysisApp

app = StockAnalysisApp()
analysis_results, market_insight = app.run_analysis()
app.save_reports(analysis_results, market_insight, './my_reports')
```

## 输出说明

系统生成三种类型的输出：

1. **HTML报告**: 包含可视化图表和详细分析的网页
2. **JSON数据**: 结构化数据，便于进一步处理
3. **PNG图表**: 可视化指标对比图

## 扩展性设计

系统设计具有良好的扩展性：

- 可轻松添加新的行业配置
- 可调整分析算法和评分规则
- 可集成更多的数据源
- 可扩展报告类型和格式

## 注意事项

1. 本工具仅供学习和研究使用，不构成投资建议
2. 实际部署时需要有效的API密钥
3. 请遵守相关API的使用频率限制
4. 数据准确性取决于第三方API提供商

## 未来发展方向

1. 集成更多数据源（社交媒体、财报等）
2. 引入更复杂的情绪分析模型
3. 增加机器学习预测功能
4. 开发Web界面和API服务
5. 添加回测功能验证策略效果

## 许可证

MIT License