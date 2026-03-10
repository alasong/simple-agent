# 多路径探索工具使用指南

## 概述

Simple Agent 现在支持多种高级推理模式，用于增强任务规划和决策能力：

| 工具 | 适用场景 | 核心优势 |
|------|---------|---------|
| **TreeOfThoughtTool** | 需要探索多个解决方案 | 避免陷入局部最优 |
| **IterativeOptimizerTool** | 需要持续改进方案质量 | 多轮迭代，自动停止 |
| **SwarmVotingTool** | 需要集思广益、重大决策 | 群体智慧，避免偏见 |
| **MultiPathOptimizerTool** | 需要同时探索多个方向 | 融合群体智慧和迭代优化 |

---

## 1. TreeOfThoughtTool - 思维树多路径探索

### 工作原理

```
问题
  │
  ▼
┌─────────────────────────────────────┐
│ 第 1 层：生成 N 个初始思路              │
│ ["思路 1", "思路 2", "思路 3"]        │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ 评估层：可行性/完整性/效率评分        │
│ 选择 Top-K 个思路                     │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ 扩展层：每个思路生成 2 个细化方案       │
│ 形成树状结构                          │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ 最终选择：评分最高的方案              │
└─────────────────────────────────────┘
```

### 使用方法

#### 直接在代码中使用

```python
from tools.reasoning_tools import TreeOfThoughtTool

# 创建工具
tool = TreeOfThoughtTool(agent, breadth=3, depth=3)

# 执行
result = await tool.execute("如何设计一个高并发系统？")

print(f"最佳方案：{result['best_solution']}")
print(f"评分：{result['best_score']}")
```

#### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `breadth` | 3 | 每层生成的思路数量 |
| `depth` | 3 | 最大深度（迭代层数） |
| `verbose` | True | 是否输出详细日志 |

### 适用场景

- 架构设计：探索多个技术方案
- 决策问题：评估多个选项
- 创新任务：需要多角度思考

---

## 2. IterativeOptimizerTool - 多轮迭代优化

### 工作流程

```
初始方案
    │
    ▼
┌───────────────────┐
│ 质量评估          │
│ 评分：0.65        │
└───────────────────┘
    │ < 阈值 0.75
    ▼
┌───────────────────┐
│ 生成改进建议      │
│ 1. 增加错误处理   │
│ 2. 优化性能...    │
└───────────────────┘
    │
    ▼
┌───────────────────┐
│ 优化方案          │
└───────────────────┘
    │
    ▼
┌───────────────────┐
│ 重新评估          │
│ 评分：0.82 ✓      │
└───────────────────┘
    │ >= 阈值
    ▼
  输出最终方案
```

### 使用方法

```python
from tools.reasoning_tools import IterativeOptimizerTool

# 创建工具
tool = IterativeOptimizerTool(
    agent,
    evaluator_agent=evaluator,  # 可选，独立评估器
    max_iterations=3,
    quality_threshold=0.75
)

# 执行（自动生成初始方案）
result = await tool.execute("编写一个 LRU 缓存实现")

# 或者提供初始方案
initial = "def lru_cache()..."
result = await tool.execute("编写一个 LRU 缓存实现", initial_solution=initial)

print(f"最终评分：{result['final_score']}")
print(f"迭代次数：{result['total_iterations']}")
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_iterations` | 3 | 最大迭代次数 |
| `quality_threshold` | 0.75 | 质量阈值（达到后停止） |
| `initial_solution` | None | 初始方案（可选） |

### 适用场景

- 代码优化：持续改进代码质量
- 方案完善：多轮审查和改进
- 文档润色：迭代优化表达

---

## 3. SwarmVotingTool - 群体投票决策

### 工作流程

```
第 1 步：各 Agent 独立生成方案
┌─────────────┬─────────────┬─────────────┐
│  Agent 1    │  Agent 2    │  Agent 3    │
│  方案 A     │  方案 B     │  方案 C     │
└─────────────┴─────────────┴─────────────┘
              │
              ▼
第 2 步：互相评分
┌─────────────┬─────────────┬─────────────┐
│  A: 0.85    │  B: 0.72    │  C: 0.90    │
└─────────────┴─────────────┴─────────────┘
              │
              ▼
第 3 步：淘汰最低分
┌─────────────┬─────────────┐
│  A: 0.85    │  C: 0.90    │
└─────────────┴─────────────┘
              │
              ▼
第 4 步：最终投票
    获胜方案：C (0.90)
```

### 使用方法

```python
from tools.reasoning_tools import SwarmVotingTool

# 创建多个 Agent
agents = [agent1, agent2, agent3]

# 创建工具
tool = SwarmVotingTool(agents, voting_rounds=2)

# 执行
result = await tool.execute("选择最适合创业公司的技术栈")

print(f"获胜方案：{result['winning_proposal']['content']}")
print(f"提出 Agent: {result['winning_proposal']['agent']}")
print(f"评分：{result['winning_proposal']['score']}")
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `voting_rounds` | 2 | 投票轮数 |
| `eliminate_lowest` | 0.3 | 每轮淘汰比例 |

### 适用场景

- 技术选型：多个方案投票
- 产品方向：集体决策
- 重大决定：避免个人偏见

---

## 4. MultiPathOptimizerTool - 多路径并行优化

### 工作流程

```
第 1 步：生成 N 个不同方向的方案
┌─────────────┬─────────────┬─────────────┐
│  保守型     │  激进型     │  平衡型     │
│  评分 0.70  │  评分 0.65  │  评分 0.72  │
└─────────────┴─────────────┴─────────────┘
        │           │           │
        ▼           ▼           ▼
第 2 步：保留 Top-K，迭代优化
┌─────────────┬─────────────┐
│  保守型     │  平衡型     │
│  优化后 0.78│  优化后 0.85│
└─────────────┴─────────────┘
        │           │
        ▼           ▼
第 3 步：选择最优
    获胜：平衡型 (0.85)
```

### 使用方法

```python
from tools.reasoning_tools import MultiPathOptimizerTool

# 创建工具
tool = MultiPathOptimizerTool(
    agent,
    num_paths=3,        # 同时探索 3 个方向
    keep_top_k=2,       # 每轮保留 2 个
    max_iterations=3
)

# 执行
result = await tool.execute("设计电商营销活动系统")

print(f"最优方向：{result['best_solution']['direction']}")
print(f"最优评分：{result['best_solution']['score']}")
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `num_paths` | 3 | 同时探索的路径数 |
| `keep_top_k` | 2 | 每轮保留的路径数 |
| `max_iterations` | 3 | 最大迭代次数 |
| `diversity_bonus` | 0.1 | 多样性加分系数 |

### 适用场景

- 复杂系统设计：多方向探索
- 营销策略：多方案并行优化
- 职业规划：多条路径评估

---

## 在 Planner Agent 中使用

Planner Agent 已配置这些工具，可以直接在对话中使用：

```
用户：这个架构设计问题比较复杂，用思维树分析一下
Planner: [自动调用 TreeOfThoughtTool]
```

### 工具调用示例

```json
{
  "name": "TreeOfThoughtTool",
  "arguments": {
    "problem": "如何设计一个支持百万并发的即时通讯系统？",
    "breadth": 4,
    "depth": 3
  }
}
```

---

## 测试

运行测试验证功能：

```bash
# 单元测试
.venv/bin/python -m pytest tests/test_reasoning_tools_unit.py -v

# 完整功能测试（需要 LLM）
.venv/bin/python tests/test_reasoning_tools.py
```

---

## 选择指南

| 需求 | 推荐工具 |
|------|---------|
| 需要探索多个不同方案 | TreeOfThoughtTool |
| 需要持续改进质量 | IterativeOptimizerTool |
| 需要集体智慧决策 | SwarmVotingTool |
| 需要多方向并行探索 | MultiPathOptimizerTool |
| 问题复杂，不确定方向 | MultiPathOptimizerTool |
| 有明确标准，追求最优 | IterativeOptimizerTool |
| 需要避免个人偏见 | SwarmVotingTool |
| 需要清晰的推理过程 | TreeOfThoughtTool |

---

## 最佳实践

### 1. 组合使用

```python
# 先用思维树探索多个方向
tree_result = await tree_tool.execute(problem)

# 再用迭代优化优化最佳方案
opt_result = await opt_tool.execute(
    problem,
    initial_solution=tree_result['best_solution']
)
```

### 2. 调整参数

- **简单问题**：减少 `breadth`、`depth`、`max_iterations`
- **复杂问题**：增加 `num_paths`、提高 `quality_threshold`
- **时间紧张**：减少迭代次数，使用单路径
- **追求质量**：增加投票轮数，提高阈值

### 3. 多样性保护

```python
# 多路径优化时，增加多样性加分
tool = MultiPathOptimizerTool(
    agent,
    diversity_bonus=0.15  # 提高多样性权重
)
```

---

## 性能考虑

| 工具 | 时间复杂度 | 建议配置 |
|------|-----------|---------|
| TreeOfThoughtTool | O(breadth × depth × LLM) | breadth=3, depth=3 |
| IterativeOptimizerTool | O(max_iterations × LLM) | max_iterations=3 |
| SwarmVotingTool | O(agents² × voting_rounds) | agents=3, rounds=2 |
| MultiPathOptimizerTool | O(num_paths × max_iterations × LLM) | paths=3, iterations=3 |

**注意**：所有工具都涉及多次 LLM 调用，建议根据任务复杂度调整参数。

---

## 故障排除

### 问题：工具执行时间过长

**解决**：
- 减少 `breadth`、`depth`、`max_iterations`
- 使用更小的 `num_paths`
- 减少 `voting_rounds`

### 问题：结果质量不稳定

**解决**：
- 提高 `quality_threshold`
- 增加 `evaluator_agent`（独立评估器）
- 使用 `SwarmVotingTool` 群体决策

### 问题：多样性不足

**解决**：
- 增加 `diversity_bonus`
- 增加 `num_paths`
- 在提示词中强调差异化
