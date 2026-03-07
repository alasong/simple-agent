# 在交互 UI 中使用 Agent Swarm

## 快速开始

### 1. 启动交互模式

```bash
python cli.py
```

### 2. 使用 Swarm 解决复杂问题

在交互界面中，**Swarm 已经自动集成到 Planner Agent 中**。当你提出复杂任务时，系统会自动使用 Swarm 进行多 Agent 协作。

#### 示例对话

```
[CLI Agent] 你：帮我开发一个完整的用户登录系统

[CLI Agent] 任务判断：复杂任务
[CLI Agent] 委托给 Planner Agent 进行任务分解...

[Planner Agent] 正在调用 SwarmOrchestrator...
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

[Planner Agent] 合并结果...
[CLI Agent] 任务完成

结果：已生成完整的用户登录系统，包括：
- models/user.py (数据库模型)
- services/auth.py (认证服务)
- api/routes/auth.py (API 路由)
- templates/login.html (前端页面)
- tests/test_auth.py (单元测试)
```

---

## 显式使用 Swarm

### 方式 1：使用 Python API（推荐）

在交互界面中，你可以运行 Python 脚本来直接使用 Swarm：

```python
# 在交互界面中执行 Python 代码
import asyncio
from swarm import SwarmOrchestrator, Task
from core import create_agent

# 创建 orchestrator
orchestrator = SwarmOrchestrator(
    agents=[
        create_agent("你是一个 Python 开发者，擅长编写高质量代码"),
        create_agent("你是一个测试专家，擅长编写单元测试"),
        create_agent("你是一个文档撰写者，擅长编写技术文档"),
    ]
)

# 运行 Swarm
async def run():
    result = await orchestrator.solve("帮我开发一个完整的用户登录系统")
    return result

# 执行
result = asyncio.run(run())
print(result)
```

### 方式 2：使用示例脚本

```bash
# 在另一个终端运行示例
python examples/demo_swarm.py
```

---

## Swarm 协作模式

### 1. 基础 Swarm 模式（默认）

自动分解任务并分配给合适的 Agent。

```
[CLI Agent] 你：帮我分析这个项目的代码质量

[Swarm] 自动分解：
  1. 静态代码分析 (CodeAnalyzerAgent)
  2. 安全漏洞扫描 (SecurityAgent)
  3. 性能优化建议 (PerformanceAgent)
  4. 代码规范检查 (LinterAgent)
```

### 2. Pair Programming 模式

Driver 写代码，Navigator 审查。

```python
from swarm.collaboration_patterns import PairProgramming

pair_programming = PairProgramming(
    driver=driver_agent,
    navigator=navigator_agent
)

result = await pair_programming.execute("实现一个快速排序算法")
```

### 3. Swarm Brainstorming 模式

多个 Agent 头脑风暴，然后评估最佳方案。

```python
from swarm.collaboration_patterns import SwarmBrainstorming

brainstorming = SwarmBrainstorming(agents=[agent1, agent2, agent3])

ideas = await brainstorming.generate("设计一个高并发的消息队列系统")
best = await brainstorming.evaluate(ideas)
```

### 4. Market-Based Allocation 模式

Agent 竞标任务，能力最强的 Agent 获得执行权。

```python
from swarm.collaboration_patterns import MarketBasedAllocation

market = MarketBasedAllocation(agents=[agent1, agent2, agent3])

winner_bid, result = await market.allocate("优化数据库查询性能")
```

### 5. Code Review Loop 模式

多轮代码审查，直到质量达标。

```python
from swarm.collaboration_patterns import CodeReviewLoop

review_loop = CodeReviewLoop(
    author=author_agent,
    reviewers=[reviewer1, reviewer2]
)

final_code = await review_loop.review("优化这个函数的性能", original_code)
```

---

## 高级用法

### 1. 自定义 Swarm 配置

```python
from swarm import SwarmOrchestrator, Blackboard, MessageBus, TaskScheduler

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

### 2. 监听 Swarm 事件

```python
from swarm import SwarmOrchestrator

orchestrator = SwarmOrchestrator(agents=[...])

# 注册事件回调
@orchestrator.on_task_start
def on_task_start(task, agent):
    print(f"🚀 开始任务：{task.description}")
    print(f"   执行 Agent: {agent.name}")

@orchestrator.on_task_complete
def on_task_complete(task, agent, result):
    print(f"✅ 任务完成：{task.description}")
    print(f"   结果：{result[:100]}...")

@orchestrator.on_swarm_complete
def on_swarm_complete(results):
    print(f"🎉 Swarm 完成！共 {len(results)} 个结果")
```

### 3. 使用动态 scaling

```python
from swarm.scaling import AutoScalingOrchestrator

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

## 实际案例

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
    Author 修改完成
  
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

## 调试和监控

### 1. 查看详细日志

```python
orchestrator = SwarmOrchestrator(
    agents=[...],
    verbose=True,  # 详细日志
    debug=True     # 调试模式
)
```

### 2. 查看 Swarm 状态

```python
# 在事件回调中查看状态
@orchestrator.on_task_start
def on_task_start(task, agent):
    status = orchestrator.status
    print(f"进度：{status['completed']}/{status['total']} 任务")
    print(f"等待中：{len(status['waiting'])} 任务")
    print(f"执行中：{len(status['in_progress'])} 任务")
```

### 3. 超时控制

```python
orchestrator = SwarmOrchestrator(
    agents=[...],
    timeout=600,        # 10 分钟超时
    max_iterations=100  # 最多 100 次迭代
)
```

---

## 最佳实践

### 1. 选择合适的 Agent

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

### 2. 合理设置任务依赖

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

### 3. 使用黑板共享上下文

```python
# ✅ 好的做法：在黑板上共享关键信息
blackboard.write("db_schema", schema_design, agent_id="DatabaseAgent")
blackboard.write("api_spec", api_design, agent_id="APIAgent")

# 后续 Agent 可以读取上下文
context = blackboard.get_context(current_task)
```

---

## 常见问题

### Q1: Swarm 和普通 Agent 有什么区别？

**A:** 
- **普通 Agent**: 单个 Agent 独立完成任务
- **Swarm**: 多个 Agent 协作，自动分解任务、分配、合并结果

### Q2: 什么时候应该使用 Swarm？

**A:** 当任务需要：
- 多步骤协作
- 不同领域的专业知识
- 代码审查和质量保证
- 头脑风暴和方案评估

### Q3: Swarm 的性能如何？

**A:** 
- 简单任务：单个 Agent 更快
- 复杂任务：Swarm 可以并行执行，总时间更短
- 使用动态 scaling 可以根据负载自动调整 Agent 数量

### Q4: 如何查看 Swarm 的执行进度？

**A:** 使用事件回调或 `orchestrator.status` 属性查看实时状态。

### Q5: Swarm 失败了怎么办？

**A:** 
1. 检查超时设置是否合理
2. 增加 `max_iterations`
3. 检查 Agent 的技能是否匹配任务
4. 使用调试模式查看详细日志

---

## 总结

在交互 UI 中使用 Agent Swarm 有三种方式：

1. **自动模式**（推荐）：直接提出复杂任务，Planner Agent 会自动使用 Swarm
2. **Python API**：在交互界面中运行 Python 代码直接使用 Swarm
3. **示例脚本**：运行 `examples/demo_swarm.py` 查看演示

**核心优势**：
- ✅ 自动任务分解
- ✅ 多 Agent 协作
- ✅ 并行执行
- ✅ 质量保证（审查、测试）
- ✅ 灵活的协作模式

**开始使用**：
```bash
python cli.py
# 然后直接输入你的复杂任务！
```
