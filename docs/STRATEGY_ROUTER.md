# 策略路由器使用指南

## 概述

策略路由器（StrategyRouter）是统一的策略决策系统，负责根据任务特征自动选择最优执行策略。

## 架构

```
┌─────────────────────────────────────────────────────────┐
│           StrategyRouter                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │  输入层                                             │  │
│  │  - 任务描述                                         │  │
│  │  - Agent 池（用于专业能力分析）                      │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  分析层                                             │  │
│  │  - 任务复杂度估计 (ComplexityEstimator)             │  │
│  │  - 专业需求分析 (ProfessionalAnalyzer)              │  │
│  │  - Agent 池匹配度分析                               │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  决策层                                             │  │
│  │  - 根据三维评估选择最优策略                         │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 策略映射表

| 任务复杂度 | 专业需求 | Agent 池覆盖 | 策略 | 工具 |
|-----------|---------|-------------|------|------|
| ≤ 0.4 | 单一 | 有 | DIRECT | InvokeAgentTool |
| ≤ 0.4 | 多个 | 有 (≥80%) | SWARM | SwarmOrchestrator |
| ≤ 0.4 | 多个 | 无 | DECOMPOSE | TaskDecomposer |
| 0.4-0.7 | 单一 | 有 | PLAN_REFLECT | IterativeOptimizerTool |
| 0.4-0.7 | 多个 | 有 (≥80%) | SWARM | SwarmOrchestrator |
| 0.4-0.7 | 多个 | 无 | TREE_OF_THOUGHT | TreeOfThoughtTool |
| > 0.7 | 单一 | 有 | TREE_OF_THOUGHT | TreeOfThoughtTool |
| > 0.7 | 多个 | 有 (≥80%) | SWARM | SwarmOrchestrator |
| > 0.7 | 多个 | 无 | DECOMPOSE | TaskDecomposer |

## 使用示例

### 基础使用

```python
from simple_agent.core.strategy_router import create_router
from simple_agent.builtin_agents import create_agent_pool

# 创建 Agent 池
agents = [
    create_agent("developer", "coding"),
    create_agent("reviewer", "reviewing"),
    create_agent("tester", "testing")
]

# 创建路由器
router = create_router(agent_pool=agents)

# 执行路由
task = "开发一个 Web 应用"
result = asyncio.run(router.route(task))

# 查看结果
print(f"策略: {result.strategy.value}")
print(f"原因: {result.reason}")
print(f"建议 Agent: {result.suggested_agents}")
```

### 自定义阈值

```python
router = create_router(
    agent_pool=agents,
    complexity_thresholds={
        "low_max": 0.3,      # 低复杂度最大值
        "medium_max": 0.6,   # 中复杂度最大值
        "swarm_min": 0.6     # 使用 Swarm 的最小复杂度
    }
)
```

### 集成到 CLI Agent

```python
from simple_agent.core.strategy_router import StrategyRouter

class CLIAgent:
    def __init__(self):
        self.router = StrategyRouter(agent_pool=self.agent_pool)

    async def handle_task(self, task: str):
        # 路由任务到最优策略
        result = await self.router.route(task)

        # 根据策略执行
        if result.strategy == Strategy.SWARM:
            # 使用 SwarmOrchestrator 执行
            pass
        elif result.strategy == Strategy.PLAN_REFLECT:
            # 使用 IterativeOptimizerTool
            pass
        # ... 其他策略
```

## 分析器详情

### ComplexityEstimator（复杂度估计）

基于关键词匹配估计任务复杂度：

```python
from simple_agent.core.strategy_router import ComplexityEstimator

task = "设计一个完整的从0开始的系统架构方案"
complexity = ComplexityEstimator.estimate(task)
# 识别关键词: "设计", "完整", "从 0", "系统", "架构", "方案"
# 返回: 0.76 (高复杂度)
```

### ProfessionalAnalyzer（专业需求分析）

从任务描述中提取专业需求：

```python
from simple_agent.core.strategy_router import ProfessionalAnalyzer

task = "编写并测试一个 Python 函数"
skills = ProfessionalAnalyzer.extract_skills(task)
# 返回: ["coding", "testing"]
```

### Agent Coverage（Agent 池覆盖分析）

检查 Agent 池是否满足任务需求：

```python
from simple_agent.core.strategy_router import create_router

agents = [
    MockAgent(name="Dev", skills=["coding"]),
    MockAgent(name="Tester", skills=["testing"])
]
router = create_router(agent_pool=agents)

coverage = router._check_agent_coverage(["coding", "design"])
# 返回:
# {
#     "covered": False,
#     "uncovered": ["design"],
#     "coverage_rate": 0.5,
#     "covered_agents": ["Dev"]
# }
```

## 测试

所有测试位于 `tests/test_strategy_router.py`：

```bash
# 运行策略路由器测试
pytest tests/test_strategy_router.py -v

# 运行单个测试类
pytest tests/test_strategy_router.py::TestStrategyRouting -v

# 运行特定测试
pytest tests/test_strategy_router.py::TestStrategyRouting::test_low_complexity_single_skill -v
```

## 配置

复杂度关键词配置在 `configs/common_keywords.yaml`：

```yaml
complexity:
  keywords:
    - "设计": 0.15
    - "架构": 0.15
    - "系统": 0.12
    - "复杂": 0.12
    - "多个": 0.10
    - "完整": 0.10
    # ... 更多关键词
```

## 优势

1. **统一决策**：整合了 Planner Agent 和 CLI Agent 的决策逻辑
2. **可配置**：阈值和关键词从配置文件加载
3. **智能匹配**：基于三维度评估（复杂度、专业需求、Agent 覆盖）
4. **测试覆盖**：32 个单元测试保证可靠性
5. **易于集成**：简单的 API 设计

## 未来扩展

1. 添加 ML 模型学习最优策略
2. 实现混合策略（先分解，遇到专业限制时动态拉人）
3. 添加成本意识决策（根据任务重要性和成本选择策略）
4. 支持更多执行策略（SWARM_VOTING, MULTI_PATH）
