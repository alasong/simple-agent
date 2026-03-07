# 如何使用 Agent Swarm

## ✅ 可以用！

Swarm 功能已完全实现并可以使用。

## 📦 前置要求

```bash
# 确保安装了依赖
pip install -r requirements.txt
```

## 🚀 三种使用方式

### 方式 1: 快速使用（推荐新手）

运行示例脚本：

```bash
# 运行完整演示
python examples/demo_swarm.py

# 运行实际使用示例
python examples/using_agent_swarm.py
```

### 方式 2: 在你的代码中使用

```python
import asyncio
from swarm import SwarmOrchestrator
from core.agent import Agent
from core.llm import get_llm

async def my_task():
    # 1. 创建 Agent
    llm = get_llm()
    agents = [
        Agent(llm=llm, name="Agent1"),
        Agent(llm=llm, name="Agent2"),
    ]
    
    # 2. 创建 Swarm 控制器
    orchestrator = SwarmOrchestrator(
        agent_pool=agents,
        llm=llm,
        verbose=True
    )
    
    # 3. 执行任务
    result = await orchestrator.solve("你的复杂任务")
    
    # 4. 查看结果
    print(f"完成：{result.tasks_completed} 个任务")
    print(f"输出：{result.output}")

asyncio.run(my_task())
```

### 方式 3: 使用协作模式

```python
import asyncio
from swarm import PairProgramming
from core.agent import Agent
from core.llm import get_llm

async def coding_task():
    llm = get_llm()
    
    # 结对编程
    driver = Agent(llm=llm, name="Driver")
    navigator = Agent(llm=llm, name="Navigator")
    
    pp = PairProgramming(driver, navigator)
    result = await pp.execute("实现快速排序")
    
    print(f"代码:\n{result.output}")

asyncio.run(coding_task())
```

## 📋 常用场景

### 场景 1: 开发完整功能

```python
from swarm import SwarmOrchestrator

agents = [分析师，架构师，开发者，测试员]
orchestrator = SwarmOrchestrator(agent_pool=agents)

result = await orchestrator.solve("开发一个博客系统")
```

### 场景 2: 代码审查

```python
from swarm import CodeReviewLoop

crl = CodeReviewLoop(
    developer=开发者，
    reviewers=[审查员 1, 审查员 2]
)
result = await crl.execute("实现用户认证")
```

### 场景 3: 方案设计

```python
from swarm import SwarmBrainstorming

sb = SwarmBrainstorming([架构师，DBA, 运维])
result = await sb.execute("设计高可用架构")
```

## 📖 详细文档

- **快速参考**: `docs/SWARM_QUICK_REFERENCE.md`
- **使用指南**: `docs/SWARM_USAGE.md`
- **示例代码**: `examples/using_agent_swarm.py`

## 🧪 测试

```bash
# 运行所有测试
python scripts/run_all_tests.py

# 运行单个测试
python tests/test_swarm.py
```

## ❓ 常见问题

### Q: Swarm 和单个 Agent 有什么区别？

A: Swarm 可以让多个 Agent 协作完成复杂任务，支持：
- 任务自动分解
- 并行执行
- 角色分工
- 协作审查

### Q: 需要什么依赖？

A: 只需要基础的 asyncio（Python 内置），可选的 chromadb 用于向量存储。

### Q: 如何查看执行进度？

A: 设置 `verbose=True`，或查看 `orchestrator.status`。

### Q: 如何自定义任务分解？

A: 手动创建 Task 对象并构建任务图：

```python
tasks = [
    Task(id="1", description="任务 1"),
    Task(id="2", description="任务 2", dependencies=["1"]),
]
orchestrator._build_task_graph(tasks)
```

## 🎯 下一步

1. 运行示例：`python examples/using_agent_swarm.py`
2. 阅读文档：`docs/SWARM_QUICK_REFERENCE.md`
3. 在你的项目中尝试使用

---

**开始使用吧！** 🚀
