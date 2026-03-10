# Simple Agent 文档中心

## 📚 文档概览

本目录包含 Simple Agent 系统的所有整合文档。

---

## 文档结构

| 文档 | 说明 |
|------|------|
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | 架构设计、升级方案、审查报告 |
| **[SWARM.md](./SWARM.md)** | Swarm 群体智能使用指南 |
| **[DEBUGGING.md](./DEBUGGING.md)** | 调试系统、CLI 调试命令 |
| **[DEVELOPMENT_WORKFLOW.md](./DEVELOPMENT_WORKFLOW.md)** | 代码开发流程、逐步写入、输出目录管理 |
| **[TESTING_AND_FEATURES.md](./TESTING_AND_FEATURES.md)** | 测试策略、增强功能、深度防护、后台任务 |
| **[PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)** | 项目概述 |
| **[CLI_REFACTOR_PLAN.md](./CLI_REFACTOR_PLAN.md)** | CLI 重构计划 |
| **[DOCUMENTATION_SUMMARY.md](./DOCUMENTATION_SUMMARY.md)** | 文档整合总结 |

---

## 快速开始

### 在 CLI 中使用

```bash
python cli.py
```

直接输入复杂任务，Swarm 会自动执行：

```
[CLI Agent] 你：帮我开发一个完整的用户登录系统
[Swarm] 自动分解任务并分配给多个 Agent 协作完成
```

### 使用 Python API

```python
import asyncio
from simple_agent.swarm import SwarmOrchestrator
from simple_agent.core import create_agent

agents = [
    create_agent("Python 开发专家"),
    create_agent("测试专家"),
]

orchestrator = SwarmOrchestrator(agent_pool=agents)

async def main():
    result = await orchestrator.solve("开发一个 REST API")
    print(f"完成 {result.tasks_completed} 个任务")

asyncio.run(main())
```

---

## 快速导航

### 我想要...

| 需求 | 查看文档 |
|------|---------|
| 了解系统架构 | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| 使用 Swarm | [SWARM.md](./SWARM.md) |
| 调试问题 | [DEBUGGING.md](./DEBUGGING.md) |
| 开发代码 | [DEVELOPMENT_WORKFLOW.md](./DEVELOPMENT_WORKFLOW.md) |
| 运行测试 | [TESTING_AND_FEATURES.md](./TESTING_AND_FEATURES.md) |

---

## 核心组件

| 组件 | 说明 |
|------|------|
| **SwarmOrchestrator** | 群体智能控制器 |
| **Blackboard** | 共享黑板 |
| **MessageBus** | 消息总线 |
| **TaskScheduler** | 任务调度器 |
| **EnhancedMemory** | 增强记忆系统 |
| **SkillLibrary** | 技能库系统 |

---

## 协作模式

| 模式 | 说明 |
|------|------|
| **PairProgramming** | 结对编程（Driver + Navigator） |
| **SwarmBrainstorming** | 群体头脑风暴 |
| **MarketBasedAllocation** | 市场分配任务 |
| **CodeReviewLoop** | 代码审查循环 |

---

## 测试和演示

```bash
# 运行所有测试
python scripts/run_all_tests.py

# 单独运行
python tests/test_swarm.py
python tests/test_swarm_stage2.py
python tests/test_scaling.py

# 运行演示
python examples/demo_swarm.py
```

---

## 项目状态

| 阶段 | 状态 |
|------|------|
| 阶段 1: Agent 能力增强 | ✅ 完成 |
| 阶段 2: Swarm 核心 | ✅ 完成 |
| 阶段 3: 动态扩展 | ✅ 完成 |
| 监控可观测性 | 🔄 进行中 |

**总计**: 33 个测试用例，全部通过 ✓

---

## 更新日志

### 2026-03-08
- ✅ 整合所有文档到主题文件
- ✅ 创建 ARCHITECTURE.md（架构）
- ✅ 创建 SWARM.md（使用指南）
- ✅ 创建 DEBUGGING.md（调试）
- ✅ 创建 DEVELOPMENT_WORKFLOW.md（开发工作流）
- ✅ 创建 TESTING_AND_FEATURES.md（测试与功能）

### 2026-03-07
- ✅ 完成阶段 2：Swarm 核心实现
- ✅ 完成阶段 3：动态扩展功能
- ✅ 33 个测试用例全部通过

### 2026-03-06
- ✅ 完成阶段 1：Agent 能力增强
- ✅ 增强记忆系统、推理模式、技能学习

---

**返回**: [项目根目录](../README.md)
