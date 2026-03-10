# Simple Agent 架构设计

## 1. 架构概览

Simple Agent 是一个多层架构的智能代理系统，支持复杂的多代理协作和智能任务执行。

### 1.1 核心价值

- **群体智能**: 通过多 Agent 协同完成复杂任务
- **智能任务管理**: 自动任务分解、智能调度和依赖管理
- **专业化协作**: 多种协作模式适应不同场景
- **模块化设计**: 组件职责分明，便于维护和扩展

### 1.2 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面层 (UI Layer)                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │  CLI Agent  •  交互模式  •  命令处理            │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                  协作编排层 (Orchestration Layer)        │
│  ┌─────────────────────────────────────────────────┐   │
│  │  SwarmOrchestrator  •  TaskScheduler            │   │
│  │  Blackboard  •  MessageBus                      │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                   核心功能层 (Core Layer)                │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Agent  •  LLM  •  Tools  •  Memory             │   │
│  │  SelfHealing  •  ReflectionLearning             │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 三层架构详解

### 2.1 用户界面层

**CLI Agent** - 统一的用户交互入口：
- 交互模式：支持对话式任务提交
- 命令系统：`/help`, `/debug`, `/session` 等
- 输出管理：结果展示和文件保存

**API 服务** - HTTP 接口（可选）：
- REST API：`POST /api/v1/agent/run`
- WebSocket：实时任务进度推送
- Swagger 文档：`/docs`

### 2.2 协作编排层

**SwarmOrchestrator** - 群体智能控制器：
- 任务分解：将复杂任务分解为子任务
- Agent 分配：根据技能匹配合适的 Agent
- 执行协调：管理任务执行顺序和依赖
- 结果汇总：整合多个 Agent 的输出

**TaskScheduler** - 任务调度器：
- 技能匹配：根据任务要求选择 Agent
- 优先级调度：支持高优先级任务插队
- 并发控制：限制同时执行的任务数
- 失败重试：自动重试失败的 Agent

**Blackboard** - 共享黑板：
- 数据共享：Agent 间共享中间结果
- 上下文管理：维护任务执行上下文
- 历史追踪：记录数据变更历史

**MessageBus** - 消息总线：
- 发布订阅：支持事件驱动架构
- 广播通知：向所有 Agent 发送消息
- 异步通信：解耦 Agent 间通信

### 2.3 核心功能层

**Agent** - 基础代理：
- LLM 调用：与语言模型交互
- 工具执行：调用外部工具
- 记忆管理：维护对话历史
- 推理循环：思考 - 行动 - 观察

**Tools** - 工具集：
- 文件操作：`ReadFileTool`, `WriteFileTool`
- Bash 执行：`BashTool`
- 网络搜索：`WebSearchTool`
- HTTP 请求：`HttpTool`
- 推理工具：`TreeOfThought`, `IterativeOptimizer`

**Memory** - 记忆系统：
- 短期记忆：当前任务上下文
- 长期记忆：持久化存储
- 技能库：学习并复用技能

**SelfHealing** - 自愈系统：
- 熔断器：避免重复失败
- 降级策略：快速替代方案
- 记忆压缩：解决上下文过长
- Agent 池：快速切换备用 Agent

**ReflectionLearning** - 反思学习：
- 执行记录：详细记录性能指标
- 性能分析：识别瓶颈
- 优化建议：生成改进方案
- 经验复用：在类似任务中应用

---

## 3. 核心组件

### 3.1 Agent

```python
from simple_agent.core import Agent, OpenAILLM

llm = OpenAILLM()
agent = Agent(
    llm=llm,
    name="Developer",
    system_prompt="你是软件开发专家",
    tools=[...],
    max_iterations=20
)
```

### 3.2 SwarmOrchestrator

```python
from simple_agent.swarm import SwarmOrchestrator

orchestrator = SwarmOrchestrator(
    agent_pool=[agent1, agent2, ...],
    max_iterations=50,
    verbose=True
)
result = await orchestrator.solve("复杂任务")
```

### 3.3 TaskScheduler

```python
from simple_agent.core.dynamic_scheduler import create_scheduler, TaskPriority

scheduler = create_scheduler(agents=[...], max_concurrent=3)
scheduler.add_task("t1", "任务", required_skills=["coding"], priority=TaskPriority.HIGH)
results = await scheduler.schedule_and_execute(agent_pool=[...], parallel=True)
```

### 3.4 Blackboard

```python
from simple_agent.swarm import Blackboard

bb = Blackboard()
bb.write("key", "value", agent_id="Agent1")
result = bb.get("key")
context = bb.get_context(task)
```

---

## 4. 设计原理

### 4.1 模块化

每个组件有单一职责，通过接口交互：
- Agent 只关注任务执行
- Scheduler 只关注任务分配
- Orchestrator 只关注整体协调

### 4.2 可扩展

- **新 Agent**: 实现统一的 Agent 接口
- **新工具**: 继承 `BaseTool` 类
- **新协作模式**: 实现协作模式接口

### 4.3 容错性

- **熔断器**: 避免重复失败
- **重试机制**: 自动重试临时失败
- **降级策略**: 提供替代方案
- **增量保存**: 定期保存进度

### 4.4 可观测性

- **调试模式**: 详细执行日志
- **性能统计**: 耗时、成功率等
- **追踪记录**: 完整执行历史

---

## 5. 架构演进

### 阶段 1: Agent 能力增强
- ✅ 增强记忆系统
- ✅ 推理模式
- ✅ 技能学习

### 阶段 2: Swarm 核心
- ✅ 任务分解
- ✅ 智能调度
- ✅ 协作模式

### 阶段 3: 动态扩展
- ✅ 动态扩缩容
- ✅ 负载均衡
- ✅ 资源优化

### 阶段 4: 自愈系统
- ✅ 熔断器
- ✅ 降级策略
- ✅ 记忆压缩
- ✅ Agent 池
- ✅ 增量检查点

### 阶段 5: 反思学习
- ✅ 执行记录
- ✅ 性能分析
- ✅ 优化建议
- ✅ 经验存储

---

## 6. 相关文件

- **[01-QUICKSTART.md](./01-QUICKSTART.md)** - 快速开始
- **[03-USER-GUIDE.md](./03-USER-GUIDE.md)** - 使用指南
- **[04-DEVELOPMENT.md](./04-DEVELOPMENT.md)** - 开发指南
- **[05-ADVANCED.md](./05-ADVANCED.md)** - 高级功能
