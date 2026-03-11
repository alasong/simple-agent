# 任务规划策略：拉人 vs 分解

## 核心问题

**什么时候拉人（AgentSwarm）？什么时候分解（Self-Decomposition）？**

这个问题触及系统架构的核心哲学。本文档说明当前的设计决策逻辑。

---

## 设计原则

### 1. 能力模型

系统中的任务执行能力分为两类：

| 能力类型 | 描述 | 典型 Agent |
|---------|------|-----------|
| **单 Agent 能力** | 单个 Agent 可独立完成的能力 | Developer, Reviewer, Tester, Planner |
| **多 Agent 协作能力** | 需要多个专业 Agent 协作完成的能力 | 复杂系统设计、大型项目规划 |

### 2. 规划层级

```
用户任务输入
    ↓
[ Planner Agent ]  ← 统一入口，负责决策
    ↓
   判断
    ↓
   ├─→ 直接执行 (BashTool / InvokeAgentTool)
   ├─→ 自分解 (MultiLevelTaskDecomposer)
   ├─→ 拉人协作 (SwarmOrchestrator)
   └─→ 迭代优化 (推理工具)
```

---

## 决策逻辑

### 第一层：任务类型判断

```python
if 任务是"简单执行类"（运行、执行、创建文件等）:
    → 直接调用 BashTool 或 InvokeAgentTool

elif 任务是"复杂任务":
    → 进入第二层判断
```

### 第二层：复杂度评估

```python
if 复杂度 <= 0.4:  # 简单复杂度
    → 使用单 Agent + 直接策略
    → 示例: "写一个 Python 函数", "分析数据"

elif 0.4 < 复杂度 <= 0.7:  # 中等复杂度
    → 使用自分解 + 单个 Agent
    → 示例: "开发一个模块", "设计数据库 Schema"

elif 复杂度 > 0.7:  # 高复杂度
    → 使用 SwarmOrchestrator（拉人协作）
    → 示例: "开发完整系统", "设计企业架构"
```

### 第三层：任务特征分析

对于高复杂度任务，进一步分析：

| 任务特征 | 策略 | 原因 |
|---------|------|------|
| **需要多专业领域** | 拉人 (Swarm) | 单 Agent 无法具备所有专业能力 |
| **有明确依赖关系** | 分解 + 调度 | 可以用 Task Scheduler 管理依赖 |
| **需要群体智慧** | 拉人 + 投票 | SwarmVotingTool 或 MultiPathOptimizerTool |
| **探索性任务** | 分解 + 思维树 | TreeOfThought 策略 |

---

## 当前实现

### 1. Planner Agent 的决策

位置: `builtin_agents/configs/planner.yaml`

```yaml
# Planner Agent 根据任务类型自动选择策略：
# - 方案设计/规划类 → MultiPathOptimizerTool (拉人并行探索)
# - 代码/文档优化类 → IterativeOptimizerTool (自分解迭代)
# - 重大决策/选择类 → SwarmVotingTool (拉人投票)
# - 复杂问题探索类 → TreeOfThoughtTool (自分解探索)
# - 简单执行类 → InvokeAgentTool/CreateWorkflowTool (直接执行)
```

### 2. TaskDecomposer (自分解)

位置: `core/task_decomposer.py`

**适用场景**：
- 任务在一个 Agent 的能力范围内
- 任务可以分解为顺序或并行的子任务
- 任务需要多次迭代优化

**分解层级**：
```
Level 1: Goal Decomposition
  └─ 任务 → 3-5 个关键里程碑

Level 2: Task Breakdown
  └─ 里程碑 → 2-4 个具体任务

Level 3: Action Planning
  └─ 任务 → 原子操作 (可分配给 Agent)
```

**代码示例**：
```python
from simple_agent.core.task_decomposer import create_decomposer

decomposer = create_decomposer(llm)
result = await decomposer.decompose("开发一个电子商务系统")

# 输出:
# - Goal: 完成需求分析 (3 个任务)
# - Goal: 完成系统设计 (4 个任务)
# - Goal: 完成开发测试 (5 个任务)
```

### 3. SwarmOrchestrator (拉人协作)

位置: `swarm/orchestrator.py`

**适用场景**：
- 任务需要多个专业 Agent 协作
- 任务复杂度很高，单 Agent 难以处理
- 需要群体智能决策

**工作流程**：
```
1. 任务分解 (TaskDecomposer)
   └─ 复杂任务 → 子任务列表

2. 构建任务图 (TaskGraph)
   └─ 分析任务依赖关系

3. 智能调度 (TaskSchedulerV2)
   └─ 基于技能匹配 + 负载均衡分配 Agent

4. 并行/顺序执行
   └─ 无依赖：ParallelWorkflow 并行
   └─ 有依赖：TaskSchedulerV2 处理
```

**代码示例**：
```python
from simple_agent.swarm.orchestrator import SwarmOrchestratorBuilder

swarm = (SwarmOrchestratorBuilder()
    .with_agents([developer, reviewer, tester, architect])
    .with_llm(llm)
    .with_max_concurrent(5)
    .build())

result = await swarm.solve("开发一个高并发系统")
# automatically:
# -分解任务给 architect (设计)
# -分解任务给 developer (编码)
# -分解任务给 reviewer (审查)
# -分解任务给 tester (测试)
```

---

## 策略选择矩阵

| 任务复杂度 | 专业性需求 | 推荐策略 | 对应工具 |
|----------|-----------|---------|---------|
| 低 | 单一 | 自分解 + DirectStrategy | BashTool, InvokeAgentTool |
| 中 | 单一 | 自分解 + PlanReflectStrategy | TaskDecomposer + Workflow |
| 高 | 单一 | 自分解 + TreeOfThoughtStrategy | TaskDecomposer + TreeOfThought |
| 低 | 多专业 | 拉人 + 并行 | SwarmOrchestrator (无依赖) |
| 中 | 多专业 | 拉人 + 调度 | SwarmOrchestrator + Scheduler |
| 高 | 多专业 | 拉人 + 群体智慧 | SwarmVotingTool / MultiPathOptimizerTool |

---

## 实际案例分析

### 案例 1: "写一个 Python 函数"

```
复杂度: 0.2 (低)
专业性: Python 编程 (单一)
策略: 直接执行
执行: InvokeAgentTool(developer, "写一个 Python 函数")
```

**为什么不分解？**
- 复杂度低，单 Agent 可快速完成
- 分解开销大于直接执行

### 案例 2: "开发一个电商系统"

```
复杂度: 0.85 (高)
专业性: 需求分析、架构设计、前端、后端、数据库、测试 (多专业)
策略: 拉人协作
执行:
  1. SwarmOrchestrator 启动
  2. 分解任务给 architect (系统设计)
  3. 分解任务给 developer (后端开发)
  4. 分解任务给 developer (前端开发)
  5. 分解任务给 data_analyst (数据库设计)
  6. 分解任务给 tester (测试)
  7. 分解任务给 reviewer (代码审查)
```

**为什么拉人？**
- 需要多专业领域协作
- 单 Agent 无法具备所有技能
- 群体智能可提高质量

### 案例 3: "优化现有代码"

```
复杂度: 0.5 (中)
专业性: 代码优化 (单一)
策略: 自分解 + 迭代优化
执行: IterativeOptimizerTool
  1. 生成初始方案
  2. 质量评估
  3. 生成改进建议
  4. 优化方案
  5. 循环直到达到质量阈值
```

**为什么不大规模拉人？**
- 专业性需求单一
- 优化是迭代过程，适合单 Agent 深入思考

---

## 决策算法伪代码

```python
async def decide_strategy(user_input: str) -> Strategy:
    """决策算法：选择最优执行策略"""

    # Step 1: 任务分类
    task_type = classify_task(user_input)

    if task_type == "simple_execution":
        return Strategy.DIRECT
    elif task_type == "complex_task":
        complexity = await estimate_complexity(user_input)

        if complexity <= 0.4:
            return Strategy.DECOMPOSE_SIMPLE
        elif complexity <= 0.7:
            return Strategy.DECOMPOSE_ITERATIVE
        else:
            # Step 2: 专业性分析
           专业性需求 = analyze_professional_requirements(user_input)

            if 专业性需求 == "single":
                return Strategy.DECOMPOSE_ADVANCED
            else:  # multiple professional areas
                return Strategy.SWARM_COLLABORATION

    elif task_type == "decision_making":
        return Strategy.SWARM_VOTING
    elif task_type == "exploration":
        return Strategy.TREE_OF_THOUGHT


async def estimate_complexity(user_input: str) -> float:
    """估计任务复杂度"""
    # 基于关键词、长度、抽象程度等特征
    keywords = get_complexity_keywords()
    score = 0

    for kw in keywords:
        if kw in user_input:
            score += 0.15

    return min(score, 1.0)


def analyze_professional_requirements(user_input: str) -> str:
    """分析专业性需求"""
    # 检查任务是否涉及多个专业领域
    skills_needed = extract_skills(user_input)

    if len(skills_needed) <= 2:
        return "single"
    else:
        return "multiple"
```

---

## 如何显式选择策略

### 使用 Planner Agent (推荐)

Planner Agent 是统一入口，会自动选择策略：

```python
# CLI 中 Planner Agent 是默认入口
```


## 策略对比总结

| 维度 | 自分解 (Decomposition) | 拉人协作 (Swarm) |
|-----|---------------------|-----------------|
| **适用任务** | 单一专业的复杂任务 | 多专业协作任务 |
| **Agent 数量** | 1-2 个 | 3-10+ 个 |
| **执行方式** | 顺序/并行分解 | 并行 + 调度 |
| **优势** | 快速、开销小 | 质量高、覆盖广 |
| **劣势** | 能力受限 | 开销大、耗时长 |
| **使用时机** | 复杂度 <= 0.7 | 复杂度 > 0.7 或多专业 |

---

## 最佳实践

### 1. 优先自分解

对于大多数任务，自分解是更好的选择：
- 开销小
- 执行快
- 灵活性高

```python
# 推荐：自分解
await decomposer.decompose("开发模块A")

# 不必要：拉人
await swarm.solve("开发模块A")  # 太重了
```

### 2. 复杂任务用 Swarm

当任务需要多专业协作时，必须用 Swarm：

```python
# 推荐：Swarm
await swarm.solve("开发完整系统")

# 不现实：自分解
await decomposer.decompose("开发完整系统")  # 难以覆盖所有专业
```

### 3. 渐进式策略

可以从简单策略开始，逐步升级：

```
第一次尝试: 直接执行
    ↓ 失败
    ↓
升级: 自分解
    ↓ 失败 (需要其他专业 Agent)
    ↓
升级: Swarm 协作
```

---

## 未来优化方向

### 1. 自适应策略选择

当前：根据复杂度阈值硬编码

优化：使用 ML 模型学习最优策略

```python
# 未来版本
strategy = model.predict_strategy(user_input, agent_pool)
```

### 2. 混合策略

当前：分解 vs 拉人是二选一

优化：先分解，遇到专业限制时动态拉人

```python
# 未来版本
decompose(task)
    if needs_professional_skill_not_in_pool:
        summon_specialist_agent()
    else:
        continue_decompose()
```

### 3. 成本意识策略

当前：不考虑执行成本

优化：根据任务重要性和成本选择策略

```python
# 未来版本
if task.importance <= LOW:
    strategy = DIRECT
elif task.importance <= MEDIUM:
    strategy = DECOMPOSE
else:  # HIGH or CRITICAL
    strategy = SWARM  # 投入更多资源
```
