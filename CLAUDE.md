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
./venv/bin/python cli.py

# 运行 CLI（单次任务）
./venv/bin/python cli.py "任务描述"

# 运行示例
./venv/bin/python examples/demo_swarm.py

# ===== 本地服务化模式 =====

# 启动 API 服务（后台运行）
./venv/bin/python cli.py --start

# 查看守护进程状态
./venv/bin/python cli.py --status

# 查看日志
./venv/bin/python cli.py --logs 100

# 停止守护进程
./venv/bin/python cli.py --stop

# 直接启动 API 服务（前台）
./venv/bin/python -m core.api_server --port 8000

# 启动 Web UI
./venv/bin/python -m webui.app --port 3000

# 访问 http://localhost:8000/docs 查看 API 文档
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
- `self_healing.py` - 自愈系统（熔断器、降级、记忆压缩、Agent 池、增量检查点、优雅降级）
- `reflection_learning.py` - 反思学习系统（执行记录、性能分析、优化建议、经验存储）

### core/ - 本地服务化 (Phase 1-2)
- `api_models.py` - Pydantic 数据模型
- `api_auth.py` - API Key 认证（支持速率限制）
- `usage_tracker.py` - 用量追踪（token/时长）
- `api_routes.py` - API 路由定义
- `api_server.py` - FastAPI 主服务
- `session_store.py` - 会话持久化存储
- `websocket_server.py` - WebSocket 实时推送
- `daemon.py` - 守护进程管理（systemd/launchd）

### webui/ - Web 界面 (Phase 3)
- `app.py` - Web UI 服务
- `frontend/index.html` - 前端页面（任务提交/列表/输出）

### integrations/ - IM 集成 (Phase 4)
- `feishu.py` - 飞书机器人集成

### tests/ - 测试 (71+ 个测试)
- `test_deep_core.py` - 14 个核心深度集成测试 (推荐)
- `test_dynamic_scheduler.py` - 29 个测试
- `test_workflow_parallel.py` - 30 个测试
- `test_swarm_integration.py` - 16 个测试
- `test_self_healing.py` - 14 个自愈核心测试
- `test_self_healing_enhanced.py` - 28 个自愈增强测试
- `test_reflection_learning.py` - 15 个反思学习测试
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

### SelfHealing (自愈系统)
```python
from core.self_healing import SelfHealingCoordinator

coordinator = SelfHealingCoordinator()

# 工具执行前检查（熔断器）
if not coordinator.can_execute_tool("WebSearchTool"):
    # 使用降级策略
    fallback = coordinator.try_fallback(...)

# 异常处理
result = coordinator.handle_exception(agent, exception, task)
# 返回：RecoveryResult(new_agent=..., should_retry=...)

# 其他功能
coordinator.try_compact_memory(messages, task_id)  # 记忆压缩
coordinator.get_agent("Developer")  # Agent 池快速切换
coordinator.save_increment(task_id, "iteration", {...})  # 增量保存
```

### ReflectionLearning (反思学习)
```python
from core.workflow import Workflow

workflow = Workflow("CodeReview")
# ... add steps ...

# 执行时启用反思学习
result = workflow.run(
    initial_input="审查代码",
    enable_reflection=True  # 自动记录、分析、生成建议
)

# 获取优化建议
from core.reflection_learning import get_learning_coordinator
coordinator = get_learning_coordinator()
suggestions = coordinator.get_optimization_suggestions()
```

## 依赖

- `rich>=13.0.0` - 富文本输出
- `networkx>=2.5` - 图算法（依赖管理、关键路径）
- `requests>=2.25.1` - HTTP 请求
- 其他：pandas, numpy, matplotlib, yfinance

### 本地服务化依赖 (Phase 1-4)

- `fastapi>=0.100.0` - API 框架
- `uvicorn[standard]>=0.23.0` - ASGI 服务器
- `python-multipart>=0.0.6` - 文件上传支持
- `websockets>=11.0` - WebSocket 支持
- `aiofiles>=23.0` - 异步文件 I/O
- `pydantic>=2.0` - 数据验证
- `pyyaml>=5.4` - YAML 配置加载

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
- `docs/SERVICE.md` - 本地服务化文档 (新增)
- `docs/SELF_HEALING_ARCH.md` - 自愈系统架构设计
- `docs/SELF_HEALING_QUICKREF.md` - 自愈系统快速参考
- `docs/REFLECTION_LEARNING.md` - 反思学习系统文档 (新增)
- `tests/README.md` - 测试运行说明
- `REFACTOR_PROGRESS.md` - 重构进度和新增功能
