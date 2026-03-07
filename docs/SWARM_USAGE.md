# Swarm 群体智能使用指南

## 概述

Swarm 系统提供多 Agent 协作能力，支持：
- 任务自动分解和调度
- 共享黑板通信
- 消息总线
- 多种协作模式

## 快速开始

### 1. 基本的 Swarm 执行

```python
import asyncio
from swarm import SwarmOrchestrator
from swarm.scheduler import Task

# 创建 Agent 池
agents = [
    Agent(...),  # 分析师
    Agent(...),  # 开发者
    Agent(...),  # 测试者
]

# 创建 Orchestrator
orchestrator = SwarmOrchestrator(
    agent_pool=agents,
    llm=llm,  # 可选，用于自动任务分解
    max_iterations=50,
    verbose=True
)

# 执行复杂任务
result = await orchestrator.solve("开发一个 Web 应用")

print(f"成功：{result.success}")
print(f"完成：{result.tasks_completed} 个任务")
```

### 2. 手动定义任务

```python
from swarm.scheduler import Task, TaskStatus

tasks = [
    Task(
        id="1",
        description="分析需求",
        required_skills=["analysis"],
        dependencies=[],
        priority=1
    ),
    Task(
        id="2",
        description="设计数据库",
        required_skills=["design", "database"],
        dependencies=["1"],
        priority=2
    ),
    Task(
        id="3",
        description="实现 API",
        required_skills=["coding"],
        dependencies=["2"],
        priority=3
    ),
]

orchestrator._build_task_graph(tasks)
result = await orchestrator._execute_loop("开发项目")
```

### 3. 共享黑板使用

```python
from swarm import Blackboard

bb = Blackboard()

# 写入数据
bb.write("task1_result", "分析完成", "Agent1")
bb.write("design_doc", "数据库设计文档...", "Agent2")

# 读取数据
result = bb.read("task1_result")

# 获取任务上下文（自动包含依赖结果）
context = bb.get_context(task)  # task.dependencies 中的任务结果

# 查看历史
history = bb.get_history("task1_result", limit=5)
```

### 4. 消息总线使用

```python
from swarm import MessageBus

bus = MessageBus()

# 订阅主题
def on_message(msg):
    print(f"收到消息：{msg.content}")

bus.subscribe("task.update", on_message)

# 发布消息
await bus.publish("task.update", "任务完成", "sender_id")

# 广播
await bus.broadcast("所有人可见", "sender_id")

# 启动和停止
await bus.start()
await bus.stop()
```

## 协作模式

### 1. 结对编程

```python
from swarm import PairProgramming

driver = Agent(...)    # 驾驶员：编写代码
navigator = Agent(...) # 导航员：审查代码

pp = PairProgramming(
    driver=driver,
    navigator=navigator,
    max_iterations=5
)

result = await pp.execute("实现一个排序算法")

print(f"代码：{result.output}")
print(f"迭代次数：{result.iterations}")
```

### 2. 群体头脑风暴

```python
from swarm import SwarmBrainstorming

agents = [
    Agent(...),  # 架构师
    Agent(...),  # 技术专家
    Agent(...),  # 产品专家
]

sb = SwarmBrainstorming(agents)
result = await sb.execute("如何设计高并发系统？")

print(f"方案：{result.output}")
```

### 3. 市场分配任务

```python
from swarm import MarketBasedAllocation

agents = [
    Agent(...),  # 资深开发
    Agent(...),  # 初级开发
]

mba = MarketBasedAllocation(agents)
winner, bid = await mba.allocate("实现核心算法")

print(f"获胜者：{winner.name}, 出价：{bid:.2f}")
```

### 4. 代码审查循环

```python
from swarm import CodeReviewLoop

developer = Agent(...)
reviewers = [
    Agent(...),  # 代码审查员
    Agent(...),  # 安全审查员
]

crl = CodeReviewLoop(developer, reviewers, max_rounds=3)
result = await crl.execute("实现用户认证")

print(f"审查通过：{result.success}")
```

## 高级用法

### 1. 事件回调

```python
def on_task_start(task, agent):
    print(f"任务 {task.id} 开始，由 {agent.name} 执行")

def on_task_complete(task, result):
    print(f"任务 {task.id} 完成：{result[:50]}...")

orchestrator.on_task_start(on_task_start)
orchestrator.on_task_complete(on_task_complete)
```

### 2. 状态监控

```python
# 获取执行状态
status = orchestrator.status
print(f"迭代：{status['iteration']}")
print(f"待处理：{status['pending']}")
print(f"运行中：{status['running']}")
print(f"已完成：{status['completed']}")
print(f"失败：{status['failed']}")
```

### 3. 自定义任务分解

```python
# 不使用 LLM 自动分解，手动创建任务图
from swarm.scheduler import TaskGraph, Task

graph = TaskGraph()
tasks = [
    Task(id="1", description="任务 1"),
    Task(id="2", description="任务 2", dependencies=["1"]),
]

for task in tasks:
    graph.add_task(task)

orchestrator.task_graph = graph
result = await orchestrator._execute_loop("总任务")
```

## 实际用例

### 用例 1：代码开发流程

```python
from swarm import SwarmOrchestrator, PairProgramming, CodeReviewLoop

# 创建角色特定的 Agent
analyst = Agent(name="分析师", system_prompt="你是需求分析专家")
developer = Agent(name="开发者", system_prompt="你是资深开发工程师")
reviewer = Agent(name="审查员", system_prompt="你是代码审查专家")
tester = Agent(name="测试员", system_prompt="你是测试专家")

agents = [analyst, developer, reviewer, tester]

# 使用 Swarm 执行完整开发流程
orchestrator = SwarmOrchestrator(agent_pool=agents, llm=llm)
result = await orchestrator.solve("开发一个用户管理系统")
```

### 用例 2：技术方案设计

```python
from swarm import SwarmBrainstorming

# 多个专家头脑风暴
experts = [
    Agent(name="架构师", system_prompt="专注系统架构"),
    Agent(name="DBA", system_prompt="专注数据库设计"),
    Agent(name="运维", system_prompt="专注部署运维"),
]

sb = SwarmBrainstorming(experts)
result = await sb.execute("设计一个日活百万的社交系统")
```

### 用例 3：代码质量保障

```python
from swarm import PairProgramming, CodeReviewLoop

# 结对编程
driver = Agent(name="Driver")
navigator = Agent(name="Navigator", system_prompt="严格审查代码")

pp = PairProgramming(driver, navigator)
code = await pp.execute("实现快速排序")

# 额外审查
reviewers = [
    Agent(name="安全审查", system_prompt="关注安全问题"),
    Agent(name="性能审查", system_prompt="关注性能问题"),
]

crl = CodeReviewLoop(driver, reviewers)
final_code = await crl.execute("实现快速排序", initial_code=code)
```

## 运行演示

```bash
# 运行完整演示
python examples/demo_swarm.py

# 运行测试
python tests/test_swarm.py
python tests/test_swarm_stage2.py
```

## 最佳实践

1. **任务分解**：将复杂任务分解为独立的子任务，明确依赖关系
2. **技能匹配**：为 Agent 指定清晰的技能和角色描述
3. **负载均衡**：使用 TaskScheduler 自动分配任务
4. **状态监控**：定期检查 orchestrator.status 了解执行进度
5. **错误处理**：设置合理的 max_iterations 和任务重试次数

## 故障排查

### 任务卡住不动

检查任务依赖是否形成循环：
```python
for task in orchestrator.task_graph.get_all_tasks():
    print(f"{task.id}: 依赖 {task.dependencies}")
```

### Agent 选择不符合预期

检查 Agent 的技能描述：
```python
for agent in agents:
    print(f"{agent.name}: {agent.description}")
```

### 消息未收到

确保 MessageBus 已启动：
```python
await bus.start()
# ... 使用
await bus.stop()
```

## 性能优化

1. **并发执行**：独立任务会自动并行执行
2. **Agent 池大小**：根据任务类型调整 Agent 数量
3. **减少迭代**：设置合理的 max_iterations
4. **上下文管理**：使用 Blackboard 共享数据，避免重复计算
