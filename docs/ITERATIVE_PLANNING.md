# 迭代规划 (Iterative Planning)

## 概述

Simple Agent 现在**默认使用迭代规划**处理复杂任务，而非一次性规划。

### 对比：一次性规划 vs 迭代规划

| 维度 | 一次性规划 | 迭代规划 |
|------|-----------|---------|
| **方案生成** | 单个方案，线性执行 | 多个方案，迭代优化 |
| **质量保障** | 无，依赖 LLM 单次输出 | 多轮评估，达标才输出 |
| **多样性** | 单一视角 | 多路径探索 |
| **决策方式** | 单个 Agent 决定 | 群体智慧/评估选择 |
| **适用场景** | 简单执行任务 | 复杂任务/方案设计 |

---

## 迭代规划工作流程

```
用户输入
    ↓
判断任务类型
    ↓
├─ 简单执行类 → 直接调用工具执行
└─ 复杂任务
       ↓
    自动选择推理工具
       ↓
    ┌─────────────────────────────────────┐
    │  迭代规划循环                        │
    │  1. 生成初始方案                     │
    │  2. 质量评估                         │
    │  3. 识别不足 → 生成改进建议          │
    │  4. 优化方案                         │
    │  5. 回到步骤 2，直到：               │
    │     - 质量达到阈值，或               │
    │     - 达到最大迭代次数               │
    └─────────────────────────────────────┘
       ↓
    输出最优方案
```

---

## 自动工具选择

Planner Agent 根据任务类型自动选择合适的迭代工具：

### 任务类型判断规则

| 任务类型 | 关键词 | 使用工具 | 默认配置 |
|----------|--------|---------|---------|
| **方案设计/规划类** | "设计"、"规划"、"方案"、"计划"、"策略" | MultiPathOptimizerTool | 3 路径，保留 Top-2，迭代 3 轮 |
| **代码/文档优化类** | "优化"、"改进"、"完善"、"代码"、"文档" | IterativeOptimizerTool | 3 轮，阈值 0.75 |
| **重大决策/选择类** | "选择"、"决策"、"哪个"、"如何选" | SwarmVotingTool | 2 轮投票 |
| **复杂问题探索类** | "分析"、"探讨"、"研究"、"为什么" | TreeOfThoughtTool | breadth=3, depth=3 |
| **简单执行类** | "运行"、"执行"、"创建文件" | CreateWorkflowTool / BashTool | 直接执行，不迭代 |

### 例外情况（不迭代）

以下情况直接执行，不启用迭代规划：
- 简单查询类任务（天气、时间、简单搜索）
- 明确的单步操作（创建文件、运行命令）
- 用户明确要求"快速"、"立即"执行

---

## 工具详解

### 1. MultiPathOptimizerTool - 多路径并行优化

**适用场景**：方案设计、系统架构、营销策略等需要多方向探索的任务

**工作原理**：
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

**API**：
```python
from tools.reasoning_tools import MultiPathOptimizerTool

tool = MultiPathOptimizerTool(
    agent,
    num_paths=3,        # 同时探索 3 个方向
    keep_top_k=2,       # 每轮保留 2 个
    max_iterations=3    # 最大迭代次数
)

result = await tool.execute("设计电商营销活动系统")
print(f"最优方案：{result['best_solution']['content']}")
print(f"方向：{result['best_solution']['direction']}")
print(f"评分：{result['best_solution']['score']}")
```

**返回结构**：
```json
{
  "best_solution": {
    "direction": "平衡实用型",
    "content": "最优方案内容",
    "score": 0.89
  },
  "final_paths": [...],
  "execution_time": 45.2
}
```

---

### 2. IterativeOptimizerTool - 多轮迭代优化

**适用场景**：代码优化、文档润色、方案完善等需要持续改进的任务

**工作原理**：
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

**API**：
```python
from tools.reasoning_tools import IterativeOptimizerTool

tool = IterativeOptimizerTool(
    agent,
    max_iterations=3,     # 最大迭代次数
    quality_threshold=0.75 # 质量阈值
)

result = await tool.execute("优化以下代码...", initial_solution=code)
print(f"最终评分：{result['final_score']}")
print(f"迭代次数：{result['total_iterations']}")
```

**返回结构**：
```json
{
  "success": true,
  "best_solution": "优化后的方案",
  "final_score": 0.85,
  "total_iterations": 2,
  "iterations": [...]
}
```

---

### 3. SwarmVotingTool - 群体投票决策

**适用场景**：技术选型、产品方向、重大决策等需要集思广益的任务

**工作原理**：
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

**API**：
```python
from tools.reasoning_tools import SwarmVotingTool

tool = SwarmVotingTool(
    agents=[agent1, agent2, agent3],
    voting_rounds=2
)

result = await tool.execute("选择最适合创业公司的技术栈")
print(f"获胜方案：{result['winning_proposal']['content']}")
print(f"提出 Agent: {result['winning_proposal']['agent']}")
print(f"评分：{result['winning_proposal']['score']}")
```

**返回结构**：
```json
{
  "winning_proposal": {
    "agent": "Agent2",
    "content": "获胜方案内容",
    "score": 0.88
  },
  "all_proposals": [...],
  "voting_rounds": 2
}
```

---

### 4. TreeOfThoughtTool - 思维树多路径探索

**适用场景**：复杂问题分析、架构设计、创新任务等需要多角度思考的场景

**工作原理**：
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

**API**：
```python
from tools.reasoning_tools import TreeOfThoughtTool

tool = TreeOfThoughtTool(
    agent,
    breadth=3,  # 每层生成 3 个思路
    depth=3     # 最大深度 3 层
)

result = await tool.execute("如何设计一个支持百万并发的即时通讯系统？")
print(f"最佳方案：{result['best_solution']}")
print(f"评分：{result['best_score']}")
print(f"探索了 {result['total_thoughts']} 个思路")
```

**返回结构**：
```json
{
  "best_solution": "最佳方案内容",
  "best_score": 0.92,
  "total_thoughts": 9,
  "tree_depth": 3,
  "all_thoughts": [...]
}
```

---

## 使用示例

### 示例 1：系统设计任务

**用户输入**："设计一个高并发的电商秒杀系统"

**Planner 自动选择**：MultiPathOptimizerTool

**执行流程**：
1. 生成 3 个不同方向的方案：
   - 保守型：基于 Redis 缓存 + 队列
   - 激进型：全链路异步 + 边缘计算
   - 平衡型：分层架构 + 本地缓存
2. 每轮迭代保留 Top-2 个方案
3. 迭代 3 轮后选择最优方案

**输出**：
```
### 最优方案（平衡实用型，评分：0.89）

**架构设计**：
1. 接入层：Nginx 负载均衡 + LVS
2. 缓存层：Redis 集群 + 本地缓存
3. 消息队列：Kafka 削峰填谷
4. 数据库：分库分表 + 读写分离

**核心优化点**：
- 库存预热到 Redis，扣减走异步队列
- 防超卖：Redis Lua 脚本 + 数据库乐观锁
- 防刷：限流 + 黑名单 + 验证码
...

---
迭代信息：
- 探索路径：3 个方向
- 最终保留：2 个方案
- 迭代轮数：3 轮
- 耗时：52.3 秒
```

---

### 示例 2：代码优化任务

**用户输入**："优化这段代码的性能和可读性"

**Planner 自动选择**：IterativeOptimizerTool

**执行流程**：
1. 生成初始优化方案
2. 质量评估（评分 0.65）
3. 生成改进建议：增加类型注解、优化循环
4. 优化后重新评估（评分 0.82）
5. 达到阈值，输出结果

**输出**：
```python
# 优化后的代码
from typing import List, Dict, Optional

def optimize_data_processing(
    items: List[Dict],
    batch_size: int = 100
) -> List[Dict]:
    """批量处理数据，优化内存使用"""
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        processed = process_batch(batch)
        results.extend(processed)
    return results
```

**迭代信息**：
- 迭代次数：2 轮
- 最终评分：0.82
- 耗时：18.5 秒

---

## 性能考虑

### 迭代次数与耗时

| 工具 | 典型迭代次数 | 典型耗时 | LLM 调用次数 |
|------|-------------|---------|-------------|
| MultiPathOptimizerTool | 3 轮 | 50-90 秒 | 9-18 次 |
| IterativeOptimizerTool | 2-3 轮 | 20-40 秒 | 4-6 次 |
| SwarmVotingTool | 2 轮 | 40-80 秒 | 6-12 次 |
| TreeOfThoughtTool | 3 层 | 30-60 秒 | 9-18 次 |

### 优化建议

| 场景 | 建议配置 |
|------|---------|
| 简单任务 | 降低迭代次数或直接执行 |
| 复杂任务 | 使用默认配置 |
| 追求质量 | 增加迭代次数，提高阈值 |
| 时间紧张 | 减少路径数，降低迭代轮数 |

---

## 配置

### Planner Agent 配置

```yaml
# builtin_agents/configs/planner.yaml
max_iterations: 15  # Planner Agent 最大迭代次数
tools:
  - MultiPathOptimizerTool  # 多路径优化
  - IterativeOptimizerTool  # 迭代优化
  - SwarmVotingTool         # 群体投票
  - TreeOfThoughtTool       # 思维树
```

### 调整迭代参数

可以通过修改工具调用的参数来调整迭代行为：

```python
# 减少迭代次数
tool = IterativeOptimizerTool(
    agent,
    max_iterations=2,       # 减少为 2 轮
    quality_threshold=0.70  # 降低阈值
)

# 增加多样性
tool = MultiPathOptimizerTool(
    agent,
    num_paths=5,            # 探索 5 个方向
    keep_top_k=3,           # 保留 3 个
    max_iterations=2        # 减少迭代轮数
)
```

---

## 验收标准

- [x] Planner Agent 默认使用迭代规划
- [x] 根据任务类型自动选择推理工具
- [x] 4 个推理工具已注册到 ToolRegistry
- [x] 工具可被 Planner Agent 调用
- [x] 文档更新完成

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `builtin_agents/configs/planner.yaml` | Planner Agent 配置（已更新） |
| `tools/reasoning_tools.py` | 推理工具核心实现 |
| `tools/reasoning_tools_wrappers.py` | BaseTool 封装 |
| `core/tool_registry.py` | 工具注册表 |
| `docs/ITERATIVE_PLANNING.md` | 本文档 |

---

## 总结

**核心价值**：
- 从"一次性规划"升级为"迭代规划"
- 从"单一方案"升级为"多路径探索"
- 从"可能准确"升级为"质量验证"

**默认行为**：
- 复杂任务自动启用迭代规划
- 根据任务类型选择合适的推理工具
- 质量达标或达到最大迭代次数后输出

**简单任务仍然直接执行**，不启用迭代规划，以保证响应速度。
