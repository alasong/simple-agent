# Simple Agent 使用指南

## 1. Swarm 群体智能

### 1.1 快速开始

```python
import asyncio
from simple_agent.swarm import SwarmOrchestrator
from simple_agent.core import create_agent

# 创建 Agent 池
agents = [
    create_agent("Python 开发专家"),
    create_agent("测试专家"),
    create_agent("文档专家"),
]

# 创建编排器
orchestrator = SwarmOrchestrator(agent_pool=agents, verbose=True)

# 执行任务
async def main():
    result = await orchestrator.solve("开发一个用户管理系统")
    print(f"完成 {result.tasks_completed} 个任务")

asyncio.run(main())
```

### 1.2 CLI 中使用 Swarm

```bash
python cli.py
# 直接输入复杂任务，Swarm 会自动执行
[CLI Agent] 你：帮我开发一个完整的用户登录系统

[Swarm] 自动分解任务:
  1. 设计数据库模型 (DatabaseAgent)
  2. 实现认证逻辑 (SecurityAgent)
  3. 创建 API 接口 (APIAgent)
  4. 编写前端表单 (FrontendAgent)
  5. 编写单元测试 (TestAgent)
```

### 1.3 定义任务依赖

```python
from simple_agent.swarm import Task

tasks = [
    Task(id="1", description="设计数据库模型"),
    Task(id="2", description="实现 ORM", dependencies=["1"]),
    Task(id="3", description="创建 API", dependencies=["2"]),
    Task(id="4", description="编写测试", dependencies=["2"]),
]

orchestrator.task_graph.build_from_tasks(tasks)
result = await orchestrator.solve("开发项目")
```

---

## 2. 协作模式

### 2.1 结对编程 (PairProgramming)

Driver 编写代码，Navigator 审查：

```python
from simple_agent.swarm.collaboration_patterns import PairProgramming

driver = create_agent("你是驾驶员，负责编写代码")
navigator = create_agent("你是导航员，负责审查代码")

pp = PairProgramming(driver=driver, navigator=navigator, max_iterations=5)
result = await pp.execute("实现一个排序算法")
```

**流程**:
1. Driver 编写初版代码
2. Navigator 审查并提出反馈
3. Driver 根据反馈修改
4. 重复直到通过审查

### 2.2 群体头脑风暴 (SwarmBrainstorming)

多个 Agent 共同讨论：

```python
from simple_agent.swarm.collaboration_patterns import SwarmBrainstorming

agents = [
    create_agent("架构师"),
    create_agent("技术专家"),
    create_agent("产品专家"),
]

sb = SwarmBrainstorming(agents=agents)
result = await sb.execute("如何设计高并发系统？")
```

### 2.3 代码审查循环 (CodeReviewLoop)

多轮审查直到质量达标：

```python
from simple_agent.swarm.collaboration_patterns import CodeReviewLoop

developer = create_agent("开发者")
reviewers = [
    create_agent("代码审查员"),
    create_agent("安全审查员"),
]

crl = CodeReviewLoop(developer, reviewers, max_rounds=3)
result = await crl.execute("实现用户认证")
```

---

## 3. 内置 Agent (26 个)

### 3.1 核心开发
- `developer` - Python 开发专家
- `architect` - 系统架构师
- `tester` - 测试专家
- `reviewer` - 代码审查员
- `deployer` - 部署专家

### 3.2 产品与设计
- `product_manager` - 产品经理
- `documenter` - 文档撰写专家

### 3.3 AI/ML
- `ai_researcher` - AI 研究员
- `ml_engineer` - 机器学习工程师
- `nlp_engineer` - NLP 工程师
- `cv_engineer` - 计算机视觉工程师

### 3.4 数据与量化
- `data_analyst` - 数据分析师
- `data_engineer` - 数据工程师
- `quant_analyst` - 量化分析师
- `financial_analyst` - 金融分析师

### 3.5 使用内置 Agent

```python
from simple_agent.builtin_agents import get_agent

# 获取 Agent
developer = get_agent("developer")
result = developer.run("帮我写一个函数")

# 列出所有内置 Agent
from simple_agent.builtin_agents import list_builtin_agents
print(list_builtin_agents())
```

---

## 4. 工具使用

### 4.1 文件工具

```python
from simple_agent.tools import ReadFileTool, WriteFileTool

# Agent 自动使用工具
agent = create_agent("开发者", tools=[ReadFileTool(), WriteFileTool()])
agent.run("读取 file.py 并修改")
```

### 4.2 Bash 工具

```python
from simple_agent.tools import BashTool

agent = create_agent("运维专家", tools=[BashTool()])
agent.run("运行测试并查看结果")
```

### 4.3 网络搜索

```python
from simple_agent.tools import WebSearchTool

agent = create_agent("研究员", tools=[WebSearchTool()])
agent.run("搜索最新的 Python 新闻")
```

---

## 5. 调试与监控

### 5.1 启用调试模式

```bash
python cli.py
/debug on
```

### 5.2 查看统计

```bash
# 执行摘要
/debug summary

# 详细统计
/debug stats
```

### 5.3 代码中调试

```python
from simple_agent.core import enable_debug

enable_debug(verbose=True)

agent = create_agent("测试")
result = agent.run("任务", debug=True)
```

---

## 6. 最佳实践

### 6.1 选择合适的 Agent

```python
# ✅ 好：技能互补
agents = [
    create_agent("Python 开发"),
    create_agent("测试"),
    create_agent("文档"),
]

# ❌ 差：技能重复
agents = [
    create_agent("Python 开发"),
    create_agent("Python 开发"),
    create_agent("Python 开发"),
]
```

### 6.2 合理设置任务依赖

```python
# ✅ 好：明确依赖
tasks = [
    Task(id="1", description="设计数据库"),
    Task(id="2", description="实现 ORM", dependencies=["1"]),
    Task(id="3", description="创建 API", dependencies=["2"]),
]
```

### 6.3 使用黑板共享上下文

```python
from simple_agent.swarm import Blackboard

bb = Blackboard()

# Agent1 写入
bb.write("db_schema", schema, agent_id="DatabaseAgent")

# Agent2 读取
schema = bb.get("db_schema")
```

### 6.4 设置合理的 max_iterations

```python
# 简单任务
agent = create_agent("简单任务", max_iterations=5)

# 复杂任务
agent = create_agent("复杂任务", max_iterations=30)

# Swarm 任务
orchestrator = SwarmOrchestrator(..., max_iterations=50)
```

---

## 7. 常见问题

### Q: 什么时候使用 Swarm？
A: 当任务需要多步骤协作、不同领域专业知识、或代码审查时。

### Q: 任务卡住不动怎么办？
A: 检查任务依赖是否形成循环，使用 `/debug stats` 查看状态。

### Q: 如何提高任务执行效率？
A:
1. 增加并发数 `max_concurrent`
2. 设置合理的任务依赖
3. 选择技能匹配的 Agent

### Q: 如何保存 Agent 配置？
A: 使用 `/save` 命令或 `agent.save()` 方法。
