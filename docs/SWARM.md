# Simple Agent Swarm 使用指南

本文档整合了 Swarm 群体智能系统的完整使用指南，包括 Python API 使用和 CLI 交互界面使用。

---

## 目录

1. [Swarm 概述](#1-swarm-概述)
2. [快速开始](#2-快速开始)
3. [CLI 中使用 Swarm](#3-cli-中使用-swarm)
4. [Python API 使用](#4-python-api-使用)
5. [协作模式详解](#5-协作模式详解)
6. [高级用法](#6-高级用法)
7. [实际案例](#7-实际案例)
8. [最佳实践](#8-最佳实践)
9. [故障排查](#9-故障排查)

---

## 1. Swarm 概述

Swarm 系统提供多 Agent 协作能力，支持：
- 任务自动分解和调度
- 共享黑板通信
- 消息总线
- 多种协作模式

### 核心组件

| 组件 | 说明 |
|------|------|
| **SwarmOrchestrator** | 群体智能控制器，负责协调多个 Agent 的协作 |
| **Blackboard** | 共享黑板，用于 Agent 间的数据共享和通信 |
| **MessageBus** | 消息总线，支持 Agent 间的异步通信 |
| **TaskScheduler** | 任务调度器，负责任务的分配和执行管理 |

---

## 2. 快速开始

### 2.1 在 CLI 中使用（推荐）

启动 CLI 后，Swarm 已自动集成。直接提出复杂任务，系统会自动使用 Swarm 进行多 Agent 协作。

```bash
python cli.py
```

```
[CLI Agent] 你：帮我开发一个完整的用户登录系统

[CLI Agent] 任务判断：复杂任务
[CLI Agent] 委托给 Planner Agent 进行任务分解...

[Swarm] 分解任务为 5 个子任务：
  1. 设计数据库模型 (分配给 DatabaseAgent)
  2. 实现认证逻辑 (分配给 SecurityAgent)
  3. 创建 API 接口 (分配给 APIAgent)
  4. 编写前端表单 (分配给 FrontendAgent)
  5. 编写单元测试 (分配给 TestAgent)

[Swarm] 执行中...
  ✓ Task 1: DatabaseAgent 完成
  ✓ Task 2: SecurityAgent 完成
  ✓ Task 3: APIAgent 完成
  ✓ Task 4: FrontendAgent 完成
  ✓ Task 5: TestAgent 完成
```

### 2.2 使用 Python API

```python
import asyncio
from simple_agent.swarm import SwarmOrchestrator
from simple_agent.core import create_agent

# 创建 Agent 池
agents = [
    create_agent("你是一个 Python 开发者"),
    create_agent("你是一个测试专家"),
    create_agent("你是一个文档撰写者"),
]

# 创建 Orchestrator
orchestrator = SwarmOrchestrator(
    agent_pool=agents,
    max_iterations=50,
    verbose=True
)

# 执行复杂任务
async def main():
    result = await orchestrator.solve("帮我开发一个完整的用户登录系统")
    print(f"完成 {result.tasks_completed} 个任务")

asyncio.run(main())
```

---

## 3. CLI 中使用 Swarm

### 3.1 自动模式（推荐）

直接提出复杂任务，Planner Agent 会自动使用 Swarm：

```
[CLI Agent] 你：帮我分析这个项目的代码质量

[Swarm] 自动分解：
  1. 静态代码分析 (CodeAnalyzerAgent)
  2. 安全漏洞扫描 (SecurityAgent)
  3. 性能优化建议 (PerformanceAgent)
  4. 代码规范检查 (LinterAgent)
```

### 3.2 显式使用 Python API

在交互界面中可以运行 Python 代码：

```python
import asyncio
from simple_agent.swarm import SwarmOrchestrator, Task

# 创建 orchestrator
orchestrator = SwarmOrchestrator(
    agents=[
        create_agent("Python 开发专家"),
        create_agent("测试专家"),
    ]
)

# 运行 Swarm
async def run():
    result = await orchestrator.solve("帮我开发一个 REST API")
    return result

result = asyncio.run(run())
print(result)
```

---

## 4. Python API 使用

### 4.1 基本的 Swarm 执行

```python
from simple_agent.swarm import SwarmOrchestrator
from simple_agent.swarm.scheduler import Task

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

### 4.2 手动定义任务

```python
from simple_agent.swarm.scheduler import Task, TaskStatus

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

### 4.3 共享黑板使用

```python
from simple_agent.swarm import Blackboard

bb = Blackboard()

# 写入数据
bb.write("task1_result", "分析完成", "Agent1")
bb.write("design_doc", "数据库设计文档...", "Agent2")

# 读取数据
result = bb.read("task1_result")

# 获取任务上下文（自动包含依赖结果）
context = bb.get_context(task)

# 查看历史
history = bb.get_history("task1_result", limit=5)
```

### 4.4 消息总线使用

```python
from simple_agent.swarm import MessageBus

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

---

## 5. 协作模式详解

### 5.1 结对编程 (Pair Programming)

Driver 编写代码，Navigator 审查。

```python
from simple_agent.swarm.collaboration_patterns import PairProgramming

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

### 5.2 群体头脑风暴 (Swarm Brainstorming)

多个 Agent 头脑风暴，然后评估最佳方案。

```python
from simple_agent.swarm import SwarmBrainstorming

agents = [
    Agent(...),  # 架构师
    Agent(...),  # 技术专家
    Agent(...),  # 产品专家
]

sb = SwarmBrainstorming(agents)
result = await sb.execute("如何设计高并发系统？")

print(f"方案：{result.output}")
```

### 5.3 市场分配模式 (Market-Based Allocation)

Agent 基于能力投标，能力最强的 Agent 获得执行权。

```python
from simple_agent.swarm import MarketBasedAllocation

agents = [
    Agent(...),  # 资深开发
    Agent(...),  # 初级开发
]

mba = MarketBasedAllocation(agents)
winner, bid = await mba.allocate("实现核心算法")

print(f"获胜者：{winner.name}, 出价：{bid:.2f}")
```

### 5.4 代码审查循环 (Code Review Loop)

多轮代码审查，直到质量达标。

```python
from simple_agent.swarm import CodeReviewLoop

developer = Agent(...)
reviewers = [
    Agent(...),  # 代码审查员
    Agent(...),  # 安全审查员
]

crl = CodeReviewLoop(developer, reviewers, max_rounds=3)
result = await crl.execute("实现用户认证")

print(f"审查通过：{result.success}")
```

---

## 6. 高级用法

### 6.1 事件回调

```python
def on_task_start(task, agent):
    print(f"任务 {task.id} 开始，由 {agent.name} 执行")

def on_task_complete(task, result):
    print(f"任务 {task.id} 完成：{result[:50]}...")

orchestrator.on_task_start(on_task_start)
orchestrator.on_task_complete(on_task_complete)
```

### 6.2 状态监控

```python
# 获取执行状态
status = orchestrator.status
print(f"迭代：{status['iteration']}")
print(f"待处理：{status['pending']}")
print(f"运行中：{status['running']}")
print(f"已完成：{status['completed']}")
print(f"失败：{status['failed']}")
```

### 6.3 自定义 Swarm 配置

```python
from simple_agent.swarm import SwarmOrchestrator, Blackboard, MessageBus, TaskScheduler

# 自定义黑板和消息总线
blackboard = Blackboard(max_history=200)
message_bus = MessageBus()
scheduler = TaskScheduler()

orchestrator = SwarmOrchestrator(
    agents=[...],
    blackboard=blackboard,
    message_bus=message_bus,
    scheduler=scheduler,
    max_iterations=50,
    timeout=300  # 5 分钟超时
)
```

### 6.4 动态 Scaling

```python
from simple_agent.swarm.scaling import AutoScalingOrchestrator

# 自动 scaling orchestrator
auto_scaler = AutoScalingOrchestrator(
    base_agents=[base_agent1, base_agent2],
    min_agents=2,
    max_agents=10,
    scale_up_threshold=0.8,
    scale_down_threshold=0.3
)

result = await auto_scaler.solve("处理大量数据")
```

---

## 7. 实际案例

### 案例 1：开发 REST API

```
[CLI Agent] 你：帮我开发一个 REST API，支持用户 CRUD 操作

[Swarm] 自动执行：
  1. 设计数据模型 (DatabaseAgent)
  2. 实现 CRUD 接口 (APIAgent)
  3. 添加输入验证 (SecurityAgent)
  4. 编写 API 文档 (DocAgent)
  5. 创建集成测试 (TestAgent)

生成的文件：
  - models/user.py
  - api/routes/users.py
  - api/schemas/user.py
  - tests/test_users_api.py
  - docs/api/users.md
```

### 案例 2：代码重构

```
[CLI Agent] 你：重构这个模块，提高代码质量

[Swarm CodeReviewLoop] 多轮审查：
  Round 1: 
    - Reviewer1: 建议提取公共函数
    - Reviewer2: 建议添加类型注解
    Author 修改完成
  
  Round 2:
    - Reviewer1: 建议优化异常处理
    - Reviewer2: ✅ 通过审查
  
  Round 3:
    - Reviewer1: ✅ 通过审查
    - Reviewer2: ✅ 通过审查
  
✅ 代码质量达标！
```

### 案例 3：系统设计

```
[CLI Agent] 你：设计一个高并发的短链接系统

[Swarm Brainstorming] 头脑风暴：
  Agent1 (架构师): 使用 Redis 缓存 + MySQL 持久化
  Agent2 (DBA): 分库分表 + 读写分离
  Agent3 (运维): Kubernetes 部署 + 自动 scaling
  
[评估] 最佳方案：
  ✅ 架构：Redis Cluster + MySQL 分片
  ✅ 部署：K8s + HPA
  ✅ CDN: 缓存热门链接
```

---

## 8. 最佳实践

### 8.1 选择合适的 Agent

```python
# ✅ 好的做法：选择技能互补的 Agent
agents = [
    create_agent("Python 开发专家"),
    create_agent("测试专家"),
    create_agent("文档撰写专家"),
]

# ❌ 不好的做法：所有 Agent 技能相同
agents = [
    create_agent("Python 开发"),
    create_agent("Python 开发"),  # 重复
    create_agent("Python 开发"),  # 重复
]
```

### 8.2 合理设置任务依赖

```python
# ✅ 好的做法：明确任务依赖
tasks = [
    Task(description="设计数据库模型", id="design_db"),
    Task(description="实现 ORM 模型", id="orm", dependencies=["design_db"]),
    Task(description="编写 API 接口", id="api", dependencies=["orm"]),
]

# ❌ 不好的做法：忽略依赖导致执行顺序混乱
tasks = [
    Task(description="设计数据库模型"),
    Task(description="实现 ORM 模型"),  # 没有依赖，可能先执行
    Task(description="编写 API 接口"),
]
```

### 8.3 使用黑板共享上下文

```python
# ✅ 好的做法：在黑板上共享关键信息
blackboard.write("db_schema", schema_design, agent_id="DatabaseAgent")
blackboard.write("api_spec", api_design, agent_id="APIAgent")

# 后续 Agent 可以读取上下文
context = blackboard.get_context(current_task)
```

### 8.4 调试和监控

```python
# 启用详细日志
orchestrator = SwarmOrchestrator(
    agents=[...],
    verbose=True,  # 详细日志
    debug=True     # 调试模式
)

# 查看详细日志
@orchestrator.on_task_start
def on_task_start(task, agent):
    status = orchestrator.status
    print(f"进度：{status['completed']}/{status['total']} 任务")
```

---

## 9. 故障排查

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

### 常见问题

**Q: Swarm 和普通 Agent 有什么区别？**

A: 
- **普通 Agent**: 单个 Agent 独立完成任务
- **Swarm**: 多个 Agent 协作，自动分解任务、分配、合并结果

**Q: 什么时候应该使用 Swarm？**

A: 当任务需要：
- 多步骤协作
- 不同领域的专业知识
- 代码审查和质量保证
- 头脑风暴和方案评估

**Q: Swarm 的性能如何？**

A: 
- 简单任务：单个 Agent 更快
- 复杂任务：Swarm 可以并行执行，总时间更短
- 使用动态 scaling 可以根据负载自动调整 Agent 数量

---

## 10. 运行和测试

```bash
# 运行演示
python examples/demo_swarm.py

# 运行测试
python tests/test_swarm.py
python tests/test_swarm_stage2.py

# 运行并发测试
python tests/test_swarm_concurrent.py
```

---

**文档版本**: 2.0  
**最后更新**: 2026-03-08  
**合并自**: SWARM_USAGE.md, HOW_TO_USE_SWARM_IN_CLI.md
