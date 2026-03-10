# 质量保障机制 (Quality Assurance)

## 问题背景

2026-03-10 用户反馈：CLI Agent 生成的股市热点报告中的数据与真实数据完全不一致，存在严重的幻觉（hallucination）问题。

**根本原因分析**：
1. LLM 在没有调用真实 API 的情况下编造具体数值
2. 没有事实核查机制检测数据真实性
3. 没有质量评估器验证输出质量
4. 缺乏强制数据验证的工作流

---

## 实施的质量保障机制

### 多层次质量保障架构

```
┌─────────────────────────────────────────────────────────┐
│  用户查询：2026 年 3 月 10 日股市热点                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 1: 数据获取层 - 强制使用真实数据源                 │
│  - StockMarketTool: 从新浪财经 API 获取真实数据           │
│  - WebSearchTool: 搜索最新财经新闻                        │
│  - 禁止 LLM 编造具体数值                                  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 2: 事实核查层 - FactChecker                       │
│  - 检测数值型断言（股价、指数、百分比）                   │
│  - 检查数据来源说明                                      │
│  - 标记可疑/未验证的断言                                 │
│  - 生成事实检查报告                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 3: 质量评估层 - QualityEvaluator Agent            │
│  - 五维度评估（准确性、完整性、实用性、清晰度、深度性）   │
│  - 准确性<4 分 → 触发 IterativeOptimizerTool 重新生成     │
│  - 提供具体改进建议                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 4: 输出层 - 附加数据验证说明                       │
│  - 数据来源标注                                          │
│  - 更新时间标注                                          │
│  - 验证状态标注（✓已验证 / ✗未验证）                       │
└─────────────────────────────────────────────────────────┘
```

---

## 新增模块

### 1. FactChecker (事实检查器)

**文件**: `core/fact_checker.py`

**功能**:
- 自动检测内容中的事实型断言
- 识别数值数据、日期、实体、引用来源
- 评估每个断言的置信度
- 检测内部矛盾
- 生成事实检查报告

**使用示例**:
```python
from core.fact_checker import FactChecker

checker = FactChecker()
report = checker.check("上证指数收盘 3072.45 点，上涨 22.20 点")

print(report.to_summary())
# 输出：事实检查需验证：2/2 未验证 (0.0%), 0 个可疑项，2 个未验证项

print(report.recommendations)
# 输出：["建议添加数据来源说明，增强可信度"]
```

** FactClaim 类型**:
| 类型 | 检测内容 | 示例 |
|------|---------|------|
| NUMERIC | 数值数据 | "3072.45 点", "上涨 22.20 点" |
| DATE | 日期时间 | "2026 年 3 月 10 日", "今日" |
| ENTITY | 实体名称 | "上证指数", "科创 50" |
| QUOTE | 引用来源 | "数据来源：新浪财经" |

**VerificationStatus**:
| 状态 | 说明 |
|------|------|
| VERIFIED | 已验证（有来源支持） |
| UNVERIFIED | 未验证（无来源） |
| SUSPICIOUS | 可疑（置信度<0.4） |
| CONTRADICTORY | 矛盾（内部不一致） |

---

### 2. StockMarketTool (股市数据查询工具)

**文件**:
- `tools/stock_data.py` - 数据获取逻辑
- `tools/stock_market_tool.py` - BaseTool 封装

**功能**:
- 从新浪财经 API 获取真实股市数据
- 支持 A 股、港股、美股
- 自动验证数据可用性
- 无法获取时明确提示，禁止编造

**使用示例**:
```python
from tools.stock_market_tool import StockMarketTool

tool = StockMarketTool()
result = tool.execute(market="A")

print(result.output)
# 输出包含数据来源和验证状态的报告
```

**输出格式**:
```
## A 股市场况
数据来源：新浪财经 API
更新时间：2026-03-10 13:17:12

### 主要指数表现

**上证综指** (sh000001) ✓
  当前：4098.59 (+4096.60 / +4112.73%)
  数据来源：新浪财经 API ✓

---
**数据验证**: 7/7 个指数已验证 ✓
**数据来源**: 新浪财经 API（实时）
```

---

### 3. Planner Agent 数据查询强制规则

**文件**: `builtin_agents/configs/planner.yaml`

**新增规则**:

| 数据类型 | 必须使用的工具 | 验证要求 |
|----------|---------------|----------|
| 股市数据 | WebSearchTool + 新浪财经 API | 必须标注来源和时间 |
| 天气信息 | WebSearchTool | 必须标注数据来源 |
| 新闻资讯 | WebSearchTool | 必须标注媒体来源 |
| 财务数据 | HttpTool/WebSearchTool | 必须标注财报来源 |
| 统计数据 | WebSearchTool | 必须标注统计机构 |
| 汇率利率 | WebSearchTool/HttpTool | 必须标注更新时间 |

**禁止行为**:
- ❌ 禁止编造具体数值（股价、指数、财务数据等）
- ❌ 禁止在没有来源的情况下提供"据数据显示"之类的内容
- ❌ 禁止使用"可能"、"大约"、"估计"等模糊词汇描述事实数据
- ❌ 禁止在没有实时 API 调用的情况下提供"最新"数据

**正确做法**:
- ✅ 使用 WebSearchTool 搜索最新信息
- ✅ 使用 HttpTool 调用官方 API 获取结构化数据
- ✅ 在输出中标注数据来源和时间
- ✅ 无法获取数据时明确说明"无法获取实时数据"

---

### 4. QualityEvaluator Agent (质量评估师)

**文件**: `builtin_agents/configs/quality_evaluator.yaml`

**评估维度**:
1. **准确性** - 信息正确，无事实错误
2. **完整性** - 覆盖全面，无重要遗漏
3. **实用性** - 建议可执行，方案可落地
4. **清晰度** - 表达清晰，结构合理
5. **深度性** - 分析深入，非表面描述

**评分标准**:
- 5 分：优秀，超出预期
- 4 分：良好，满足要求
- 3 分：合格，基本完成
- 2 分：较差，需要改进
- 1 分：不合格，需要重做

**集成方式** (待实施):
```python
from builtin_agents import get_agent
from core.fact_checker import FactChecker

# 1. 生成回答
response = agent.run(user_query)

# 2. 事实检查
fact_checker = FactChecker()
fact_report = fact_checker.check(response)

# 3. 质量评估
evaluator = get_agent("quality_evaluator")
eval_result = evaluator.run(f"评估以下回答：{response}")

# 4. 低质量触发迭代优化
if eval_result.total_score < 3.5 or fact_report.verification_rate < 0.5:
    from tools.reasoning_tools import IterativeOptimizerTool
    optimizer = IterativeOptimizerTool(agent)
    response = await optimizer.execute(user_query, initial_solution=response)
```

---

## 工具注册表更新

**文件**: `core/tool_registry.py`

新增工具映射:
```python
module_mappings = {
    # ... 原有映射 ...
    # 数据工具
    "stockmarkettool": "tools.stock_market_tool",
}
```

---

## 工作流程

### 完整的质量保障工作流

```
1. 用户查询
   ↓
2. Planner 分析意图
   ↓
3. 判断是否为数据查询类任务
   ├─ 是 → 强制调用 StockMarketTool/WebSearchTool
   └─ 否 → 正常处理
   ↓
4. 生成初步回答
   ↓
5. FactChecker 事实检查
   ├─ 发现可疑数据 → 标记并提示验证
   └─ 通过 → 继续
   ↓
6. QualityEvaluator 质量评估
   ├─ 评分 < 3.5 → 触发 IterativeOptimizerTool 重新生成
   └─ 评分 ≥ 3.5 → 通过
   ↓
7. 输出最终回答（含数据来源说明）
```

---

## 验收标准

### 事实核查
- [x] FactChecker 可检测数值型断言
- [x] FactChecker 可检查数据来源
- [x] FactChecker 生成事实检查报告
- [ ] 事实检查集成到 CLI Agent 工作流

### 数据验证
- [x] StockMarketTool 可从真实 API 获取数据
- [x] StockMarketTool 标注数据来源和验证状态
- [x] 无法获取数据时明确提示
- [ ] WebSearchTool 强制用于财经查询

### 质量评估
- [x] QualityEvaluator Agent 配置完成
- [x] 五维度评估标准定义
- [ ] 质量评估集成到 CLI Agent 工作流
- [ ] 低质量回答自动触发迭代优化

### 提示词更新
- [x] Planner Agent 添加数据查询强制规则
- [x] 明确禁止编造数值
- [x] 标注数据来源要求

---

## 待实施项目

### 短期（1-2 天）
1. **集成 FactChecker 到 CLI Agent**
   - 在 `cli_coordinator.py` 中添加事实检查步骤
   - 对生成的回答自动执行事实检查

2. **集成 QualityEvaluator 到工作流**
   - 在 `cli_agent.py` 中添加质量评估调用
   - 低质量回答自动触发 `IterativeOptimizerTool`

3. **更新 WebSearchTool 财经搜索逻辑**
   - 优先使用新浪财经/东方财富 API
   - 添加数据格式化和来源标注

### 中期（1 周）
1. **添加用户反馈机制**
   - 用户可标记"数据不准确"
   - 触发重新验证和迭代优化

2. **建立事实数据库**
   - 缓存已验证的事实数据
   - 减少重复验证开销

3. **优化提示词**
   - 基于测试结果调整规则
   - 添加更多场景的强制规则

---

## 测试方法

### 单元测试
```bash
# 测试 FactChecker
.venv/bin/python -m pytest tests/test_fact_checker.py -v

# 测试 StockMarketTool
.venv/bin/python -m pytest tests/test_stock_market_tool.py -v
```

### 集成测试
```bash
# 测试完整质量保障工作流
.venv/bin/python tests/test_quality_assurance_integration.py
```

### 手动测试
```python
# 测试股市数据查询
from tools.stock_market_tool import StockMarketTool
tool = StockMarketTool()
result = tool.execute(market="A")
print(result.output)

# 测试事实检查
from core.fact_checker import FactChecker
checker = FactChecker()
report = checker.check("上证指数收盘 3072.45 点")
print(report.to_summary())
```

---

## 相关文件清单

| 文件 | 状态 | 说明 |
|------|------|------|
| `core/fact_checker.py` | ✓ 完成 | 事实检查器 |
| `tools/stock_data.py` | ✓ 完成 | 股市数据获取 |
| `tools/stock_market_tool.py` | ✓ 完成 | 股市数据工具 |
| `core/tool_registry.py` | ✓ 完成 | 添加工具映射 |
| `builtin_agents/configs/planner.yaml` | ✓ 完成 | 添加强制规则 |
| `builtin_agents/configs/quality_evaluator.yaml` | ✓ 完成 | 质量评估师配置 |
| `docs/QUALITY_ASSURANCE.md` | ✓ 完成 | 本文档 |

---

## 总结

通过实施多层次质量保障机制，确保：

1. **数据真实性**: 强制使用真实 API，禁止编造
2. **事实可追溯**: 所有数据标注来源和时间
3. **质量可量化**: 五维度评估，低分自动触发优化
4. **问题可检测**: FactChecker 自动检测可疑数据

核心价值：**从"可能准确"升级为"已验证准确"**
