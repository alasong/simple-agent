# 自愈系统架构

## 统一架构设计

自愈系统采用**三层架构**设计，将核心自愈能力和高效增强手段统一管理：

```
┌─────────────────────────────────────────────────────────┐
│                    Coordinator                          │
│                   (统一自愈协调器)                       │
│              SelfHealingCoordinator                     │
├─────────────────────────────────────────────────────────┤
│  Core Layer (核心层)   │  Enhancement Layer (增强层)    │
│  ├─ ExceptionDiagnoser │  ├─ CircuitBreaker            │
│  ├─ AgentRegenerator   │  ├─ FallbackProvider          │
│  └─ TaskResumer        │  ├─ MemoryCompactor           │
│                        │  ├─ AgentPool                 │
│                        │  ├─ IncrementalCheckpoint     │
│                        │  └─ GracefulDegradation       │
└─────────────────────────────────────────────────────────┘
```

## 模块说明

### Core Layer (核心层)

处理 Agent 执行级别的异常恢复：

| 模块 | 职责 | 执行时间 |
|------|------|---------|
| `ExceptionDiagnoser` | 异常类型识别、根本原因分析 | <0.1s |
| `AgentRegenerator` | 克隆/调整配置/切换备用 Agent | ~1s |
| `TaskResumer` | 保存和加载执行断点 | ~0.1s |

### Enhancement Layer (增强层)

提供高效预防和优化手段：

| 模块 | 职责 | 执行时间 | 性能提升 |
|------|------|---------|---------|
| `CircuitBreaker` | 熔断器 - 避免重复失败 | 0s | 避免雪崩 |
| `FallbackProvider` | 快速降级 - 替代方案 | <0.1s | 50x |
| `MemoryCompactor` | 记忆压缩 - 解决上下文过长 | ~0.5s | 恢复执行 |
| `AgentPool` | Agent 池 - 快速切换 | <0.1s | 10x |
| `IncrementalCheckpointManager` | 增量检查点 - 高效保存 | ~0.05s | 10x |
| `GracefulDegradation` | 优雅降级 - 资源自适应 | <0.1s | 避免崩溃 |

## 统一入口

所有自愈能力通过 `SelfHealingCoordinator` 统一提供：

```python
from core.self_healing import SelfHealingCoordinator

coordinator = SelfHealingCoordinator()

# 核心层功能
result = coordinator.handle_exception(agent, exception, task_description)

# 增强层功能（通过 Coordinator 代理）
coordinator.can_execute_tool("WebSearchTool")     # 熔断器检查
coordinator.try_fallback(...)                      # 降级策略
coordinator.try_compact_memory(...)                # 记忆压缩
coordinator.warmup_agents(["Planner"])             # Agent 池预热
coordinator.get_agent("Developer")                 # 快速获取 Agent
coordinator.save_increment(...)                    # 增量保存
coordinator.check_degradation(metrics)             # 优雅降级
```

## 数据流

```
Agent.run() 中发生异常
       │
       ▼
SelfHealingCoordinator.handle_exception()
       │
       ├── ExceptionDiagnoser.diagnose() → ExceptionReport
       │
       ├── _select_recovery_strategy() → RecoveryStrategy
       │
       ├── _execute_recovery() → RecoveryResult
       │       │
       │       ├── RETRY → 原 Agent 重试
       │       ├── REGENERATE_AGENT → AgentRegenerator.regenerate()
       │       ├── SWITCH_AGENT → AgentRegenerator._switch_to_backup_agent()
       │       └── SKIP_STEP → 跳过当前步骤
       │
       └── [增强层联动]
               ├── CircuitBreaker.record_failure()
               ├── FallbackProvider.execute_fallback()
               └── GracefulDegradation.degrade()
```

## 自愈策略选择

| 异常类型 | 恢复策略 | 说明 |
|---------|---------|------|
| `TIMEOUT_ERROR` | RETRY | 超时错误，直接重试 |
| `NETWORK_ERROR` | RETRY | 网络错误，直接重试 |
| `LLM_ERROR` | SWITCH_AGENT | LLM 错误，切换备用 Agent |
| `AGENT_CRASH` | REGENERATE_AGENT | Agent 崩溃，重新生成 |
| `TOOL_ERROR` (持久性) | SKIP_STEP | 工具持久性错误，跳过 |
| `TOOL_ERROR` (临时) | RETRY | 工具临时错误，重试 |
| `UNKNOWN` | REGENERATE_AGENT | 未知错误，重新生成 |

## 增强层联动

### 1. 熔断器 + 降级

```python
# 工具失败时
coordinator.record_tool_result("WebSearchTool", success=False, error="网络错误")

# 熔断器自动判断是否熔断
# 如果熔断，can_execute_tool() 返回 False

if not coordinator.can_execute_tool("WebSearchTool"):
    # 自动切换到降级策略
    fallback = coordinator.try_fallback(...)
```

### 2. 记忆压缩

```python
# 当消息数量超过阈值时自动压缩
compressed, summary = coordinator.try_compact_memory(messages, task_id)
# messages: 100 → compressed: 15
```

### 3. Agent 池快速切换

```python
# 预热常用 Agent
coordinator.warmup_agents(["Planner", "Developer", "Reviewer"])

# 需要切换时 <0.1s
agent = coordinator.get_agent("Developer")
```

### 4. 增量状态保存

```python
# 每步执行后保存增量（~0.05s）
coordinator.save_increment(task_id, "iteration", {"iteration": 5})

# 失败后加载状态
state = coordinator.load_checkpoint(task_id)
```

### 5. 优雅降级

```python
# 根据指标自动降级
metrics = {"consecutive_failures": 5}
if coordinator.check_degradation(metrics):
    # 已自动降级
    config = coordinator.get_current_config()
    # config: {"max_iterations": 8, ...}
```

## 使用示例

### 完整自愈流程

```python
from core.self_healing import SelfHealingCoordinator
from core.agent import Agent

coordinator = SelfHealingCoordinator()

# 1. 预热 Agent 池
coordinator.warmup_agents(["Planner", "Developer"])

# 2. 获取 Agent（快速切换）
agent = coordinator.get_agent("Developer")
if not agent:
    agent = Agent(name="Developer")

# 3. 执行任务并启用自愈
task_id = "task-001"
messages = []

for iteration in range(10):
    try:
        # 保存增量状态
        coordinator.save_increment(task_id, "iteration", {"iteration": iteration})

        # 检查工具可用性
        if not coordinator.can_execute_tool("WebSearchTool"):
            # 使用降级
            fallback = coordinator.try_fallback(
                "WebSearchTool",
                {"query": "查询"},
                "网络错误"
            )
            continue

        # 执行工具
        result = tool.execute()
        coordinator.record_tool_result("WebSearchTool", success=True)

    except Exception as e:
        # 记录失败
        coordinator.record_tool_result(
            "WebSearchTool",
            success=False,
            error=str(e)
        )

        # 自愈处理
        result = coordinator.handle_exception(
            agent=agent,
            exception=e,
            task_description="查询任务",
            context={"failed_tool": "WebSearchTool"}
        )

        # 切换新 Agent
        if result.new_agent:
            agent = result.new_agent

        # 检查是否需要降级
        coordinator.check_degradation({"consecutive_failures": 3})

# 4. 状态监控
status = coordinator.get_status()
print(f"自愈状态：{status}")
```

## 测试

```bash
# 运行所有自愈测试
pytest tests/test_self_healing.py tests/test_self_healing_enhanced.py -v

# 运行核心测试（确保无回归）
pytest tests/test_deep_core.py -v
```

## 文件结构

```
core/
  self_healing.py           # 统一自愈系统（~1100 行）
    - Core Layer: ExceptionDiagnoser, AgentRegenerator, TaskResumer
    - Enhancement Layer: CircuitBreaker, FallbackProvider, MemoryCompactor,
                         AgentPool, IncrementalCheckpointManager, GracefulDegradation
    - Coordinator: SelfHealingCoordinator (统一入口)

tests/
  test_self_healing.py           # 14 个核心测试
  test_self_healing_enhanced.py  # 28 个增强测试

docs/
  SELF_HEALING.md           # 原有自愈文档
  SELF_HEALING_QUICKREF.md  # 快速参考
  SELF_HEALING_ARCH.md      # 本文档
```

## 设计原则

### 1. 内敛统一
- 单一入口：`SelfHealingCoordinator`
- 统一数据模型：`ExceptionReport`, `RecoveryResult`
- 一致的接口风格

### 2. 分层解耦
- 核心层：处理 Agent 级别异常
- 增强层：提供高效预防手段
- 层间松耦合，通过 Coordinator 聚合

### 3. 性能优先
- 熔断器：0s 开销
- 降级策略：<0.1s
- 增量保存：~0.05s
- Agent 切换：<0.1s

### 4. 渐进增强
- 核心自愈功能始终可用
- 增强功能可选启用/禁用
- 优雅降级保证系统可用性

## 验收标准

- [x] 42 个自愈测试全部通过
- [x] 14 个核心深度测试全部通过
- [x] 统一架构，无重复代码
- [x] 单一入口文件 `core/self_healing.py`
- [x] 文档完整
