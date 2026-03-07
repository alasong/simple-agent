# Swarm 快速参考

## 导入

```python
from swarm import (
    SwarmOrchestrator,
    Blackboard,
    MessageBus,
    PairProgramming,
    SwarmBrainstorming,
    MarketBasedAllocation,
    CodeReviewLoop,
    DynamicScaling,
    AutoScalingOrchestrator,
)
from swarm.scheduler import Task, TaskStatus, TaskGraph
```

## 快速开始

### 1. 基本使用

```python
# 创建 Agent 池
agents = [agent1, agent2, agent3]

# 创建 Orchestrator
orchestrator = SwarmOrchestrator(
    agent_pool=agents,
    llm=llm,
    verbose=True
)

# 执行任务
result = await orchestrator.solve("复杂任务")
```

### 2. 手动任务

```python
tasks = [
    Task(id="1", description="任务 1", dependencies=[]),
    Task(id="2", description="任务 2", dependencies=["1"]),
]
orchestrator._build_task_graph(tasks)
result = await orchestrator._execute_loop("总任务")
```

### 3. 共享黑板

```python
bb = Blackboard()
bb.write("key", "value", "agent_id")
value = bb.read("key")
context = bb.get_context(task)
```

### 4. 消息总线

```python
bus = MessageBus()
bus.subscribe("topic", callback)
await bus.publish("topic", "message", "sender")
await bus.start()
await bus.stop()
```

### 5. 结对编程

```python
pp = PairProgramming(driver, navigator)
result = await pp.execute("实现功能")
```

### 6. 头脑风暴

```python
sb = SwarmBrainstorming([agent1, agent2, agent3])
result = await sb.execute("问题描述")
```

### 7. 市场分配

```python
mba = MarketBasedAllocation(agents)
winner, bid = await mba.allocate("任务")
```

### 8. 代码审查

```python
crl = CodeReviewLoop(developer, [reviewer1, reviewer2])
result = await crl.execute("实现功能")
```

### 9. 动态扩展

```python
auto = AutoScalingOrchestrator(
    orchestrator,
    min_agents=2,
    max_agents=10
)
await auto.scaling.start()
result = await auto.solve("任务")
await auto.scaling.stop()
```

## 状态查询

```python
status = orchestrator.status
# {
#   'running': True,
#   'iteration': 5,
#   'pending': 3,
#   'running': 2,
#   'completed': 10,
#   'failed': 1
# }
```

## 事件回调

```python
def on_start(task, agent):
    print(f"开始：{task.id}")

def on_complete(task, result):
    print(f"完成：{task.id}")

orchestrator.on_task_start(on_start)
orchestrator.on_task_complete(on_complete)
```

## 配置选项

### SwarmOrchestrator

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| agent_pool | list | 必填 | Agent 列表 |
| llm | object | None | LLM 实例 |
| max_iterations | int | 50 | 最大迭代次数 |
| verbose | bool | True | 详细输出 |

### DynamicScaling

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| min_agents | int | 1 | 最小 Agent 数 |
| max_agents | int | 10 | 最大 Agent 数 |
| scale_up_threshold | float | 0.8 | 扩展阈值 |
| scale_down_threshold | float | 0.3 | 缩减阈值 |
| cooldown_seconds | int | 60 | 冷却时间 |

### PairProgramming

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| driver | Agent | 必填 | 驾驶员 |
| navigator | Agent | 必填 | 导航员 |
| max_iterations | int | 5 | 最大迭代 |

## 常用命令

```bash
# 运行所有测试
python scripts/run_all_tests.py

# 运行演示
python examples/demo_swarm.py

# 查看文档
cat docs/SWARM_USAGE.md
```

## 错误处理

```python
try:
    result = await orchestrator.solve("任务")
except Exception as e:
    print(f"错误：{e}")
    print(f"状态：{orchestrator.status}")
```

## 性能提示

1. **并发执行**: 独立任务自动并行
2. **合理设置 max_iterations**: 避免无限循环
3. **使用动态扩展**: 自动调整 Agent 数量
4. **监控状态**: 定期检查 status

## 调试技巧

```python
# 查看详细状态
print(orchestrator.status)

# 查看任务列表
for task in orchestrator.task_graph.get_all_tasks():
    print(f"{task.id}: {task.status} - {task.description}")

# 查看黑板数据
print(orchestrator.blackboard.get_all())

# 查看消息历史
print(orchestrator.message_bus.get_history())
```
