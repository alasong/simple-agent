# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Simple Agent 是一个多 Agent 协作系统，支持群体智能、任务自动分解、智能调度和多种协作模式。

## 常用命令

### 测试

```bash
# 日常核心测试 (推荐，约 30 秒)
./tests/run_daily_tests.sh

# 快速测试 (5 分钟内)
./tests/run_quick_tests.sh

# 完整测试套件 (约 5-10 分钟)
./tests/run_all_tests.sh

# 运行深度测试
./venv/bin/python -m pytest tests/test_deep_core.py -v

# 运行单个测试
./venv/bin/python -m pytest tests/test_deep_core.py::TestDeepSchedulerIntegration::test_scheduler_full_workflow -v
```

### 运行

```bash
# 运行 CLI（交互模式）
./venv/bin/python cli_new.py

# 运行 CLI（单次任务）
./venv/bin/python cli_new.py "任务描述"

# 运行示例
./venv/bin/python examples/demo_swarm.py
```

## 架构概览

系统采用三层架构：

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面层 (UI Layer)                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │  CLI Agent (cli_agent.py)                       │   │
│  │  CLI Coordinator (cli_coordinator.py)           │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                  协作编排层 (Orchestration Layer)        │
│  ┌─────────────────────────────────────────────────┐   │
│  │  SwarmOrchestrator - 群体智能控制器             │   │
│  │  TaskScheduler - 任务调度器                     │   │
│  │  Blackboard - 共享黑板                          │   │
│  │  MessageBus - 消息总线                          │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                   核心功能层 (Core Layer)                │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Agent - 基础代理                               │   │
│  │  DynamicScheduler - 动态调度器                  │   │
│  │  ParallelWorkflow - 并行工作流                  │   │
│  │  TaskDecomposer - 任务分解器                    │   │
│  │  DependencyGraph - 依赖图管理器                 │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 核心模块

### swarm/ - 群体智能
- `orchestrator.py` - SwarmOrchestrator: 群体智能控制器
- `scheduler.py` - TaskScheduler/TaskSchedulerV2: 任务调度器
- `blackboard.py` - Blackboard: 共享黑板
- `message_bus.py` - MessageBus: 消息总线
- `collaboration_patterns.py` - 协作模式（结对编程、头脑风暴等）

### core/ - 核心功能
- `agent.py` - Agent 基类
- `agent_enhanced.py` - 增强版 Agent
- `dynamic_scheduler.py` - 动态调度器（v2 新增）
- `workflow.py` - 工作流编排（顺序执行）
- `workflow_types.py` - 工作流类型定义（ResultType, StepResult, etc.）
- `workflow_parallel.py` - 并行工作流执行（ParallelWorkflow, ParallelStep）
- `task_decomposer.py` - 多级任务分解器
- `dependency_graph.py` - 依赖图管理器

### tests/ - 测试 (122 个测试)
- `test_deep_core.py` - 14 个核心深度集成测试 (推荐)
- `test_dynamic_scheduler.py` - 29 个测试
- `test_workflow_parallel.py` - 30 个测试
- `test_swarm_integration.py` - 16 个测试
- 详见 `tests/README.md`

### CLI 相关
- `cli_new.py` - 精简版 CLI 入口 (~200 行)
- `cli.py` - 完整版 CLI (1310 行)
- `cli_agent.py` - CLI Agent 实现
- `cli_coordinator.py` - CLI 协调器
- `cli_commands/` - CLI 命令模块

### builtin_agents/ - 内置 Agent (25 个)
- `configs/` - YAML 配置文件目录
- 核心开发：developer, architect, tester, deployer, reviewer
- 产品与设计：product_manager, documenter
- AI/ML：ai_researcher, ml_engineer, mlops_engineer, cv_engineer, nlp_engineer, prompt_engineer
- 数据与量化：data_analyst, data_engineer, quant_analyst, financial_analyst, credit_analyst, investment_advisor
- 交易与风险：trading_strategist, risk_manager, compliance_officer, planner
- 新增专家：security_agent, performance_agent
- 详见 `docs/BUILTIN_AGENTS.md`

## v2 新功能 (Phase 3-4)

### DynamicScheduler (动态调度器)
```python
from core.dynamic_scheduler import create_scheduler, TaskPriority

scheduler = create_scheduler(agents=[agent1, agent2], max_concurrent=3)
scheduler.add_task("t1", "任务描述", required_skills=["coding"], priority=TaskPriority.HIGH)
results = await scheduler.schedule_and_execute(agent_pool=agents, parallel=True)
```

### ParallelWorkflow (并行工作流)
```python
from core.workflow_parallel import create_parallel_workflow

workflow = create_parallel_workflow(max_concurrent=3, default_timeout=60.0)
workflow.add_task("Task A", agent_a, instance_id="project-a")
workflow.add_task("Task B", agent_b, instance_id="project-b")
results = await workflow.execute("基础输入", verbose=True)
```

### Swarm v2 集成
```python
from swarm.orchestrator import SwarmOrchestrator

# v2 模式：使用动态调度器和并行工作流
swarm = SwarmOrchestrator(
    agent_pool=agents,
    llm=llm,
    use_v2_scheduler=True,
    use_parallel_workflow=True,
    max_concurrent=3
)
result = await swarm.solve("复杂任务")
```

## 依赖

- `rich>=13.0.0` - 富文本输出
- `networkx>=2.5` - 图算法（依赖管理、关键路径）
- `requests>=2.25.1` - HTTP 请求
- 其他：pandas, numpy, matplotlib, yfinance

虚拟环境位于 `.venv/`，使用 `./venv/bin/python` 执行命令。

## 开发注意事项

1. **异步/同步兼容**: 系统同时支持同步和异步 Agent，使用 `AsyncAgentAdapter` 包装
2. **v2 功能可用时**: `TaskSchedulerV2` 和 `ParallelWorkflow` 在导入失败时自动降级到 v1
3. **测试**: 日常测试 `./tests/run_daily_tests.sh`，完整文档见 `tests/README.md`
4. **Progress 文档**: 重构进度记录在 `REFACTOR_PROGRESS.md`

## 文档

- `docs/ARCHITECTURE.md` - 架构文档
- `docs/SWARM.md` - Swarm 使用指南
- `docs/PROJECT_OVERVIEW.md` - 项目概述
- `docs/BUILTIN_AGENTS.md` - 内置 Agent 详细列表 (25 个)
- `docs/TESTING.md` - 测试指南
- `tests/README.md` - 测试运行说明
- `REFACTOR_PROGRESS.md` - 重构进度和新增功能
