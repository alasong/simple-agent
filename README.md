# AI驱动股市热点分析工具

一个集成固态电池、半导体设备、AI算力三个前沿科技领域的实时数据分析和智能评估系统。

## 功能特点

- **多维度数据整合**: 结合股价、交易量、新闻情绪等多源数据
- **智能分析引擎**: 计算趋势、动量、情绪、波动等多项指标
- **实时监控**: 对三大热点行业进行持续跟踪分析
- **可视化报告**: 生成详细的HTML、JSON格式分析报告
- **投资建议**: 基于数据分析提供投资策略建议

## 技术架构

- **数据获取层**: 通过API获取实时股价和新闻数据
- **分析引擎**: 多维度评分算法，综合评估各行业状况
- **报告生成**: HTML可视化界面与JSON数据接口
- **配置管理**: 支持灵活的行业和股票配置

## 安装依赖

```bash
pip install -r requirements.txt
```

或直接安装：

```bash
pip install -e .
```

## 使用方法

### 命令行使用

```bash
# 运行完整分析，默认输出到./reports目录
python -m stock_analyzer.app

# 指定输出目录
python -m stock_analyzer.app --output-dir ./my_reports

# 仅生成JSON格式报告
python -m stock_analyzer.app --format json

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

## 配置说明

在 `stock_analyzer/config.py` 中可以配置：

- 各行业关键词
- 相关股票列表
- API端点设置
- 分析参数

## 输出示例

工具会生成以下类型的输出：

- **HTML报告**: 包含可视化图表和详细分析的网页
- **JSON数据**: 结构化数据，便于进一步处理
- **PNG图表**: 可视化指标对比图

## 数据模型

- `StockData`: 股票基础数据
- `NewsArticle`: 新闻文章数据
- `AnalysisResult`: 单个行业的分析结果
- `MarketInsight`: 整体市场洞察

## API配置

需要在环境变量中设置：

- `ALPHA_VANTAGE_API_KEY`: 股价数据API密钥
- `NEWS_API_KEY`: 新闻数据API密钥

## 注意事项

1. 本工具仅供学习和研究使用，不构成投资建议
2. 实际部署时需要有效的API密钥
3. 请遵守相关API的使用频率限制
4. 数据准确性取决于第三方API提供商

## 扩展性

系统设计具有良好的扩展性，可轻松添加新的行业或调整分析算法。

## 许可证

MIT License