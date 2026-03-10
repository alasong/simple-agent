# Self-Healing Quick Reference

## 6 种高效自愈手段总览

| # | 手段 | 执行时间 | 核心 API | 适用场景 |
|---|------|---------|---------|---------|
| 1 | **熔断器** | 0s | `cb.can_execute()` | 避免重复调用失败工具 |
| 2 | **快速降级** | <0.1s | `provider.execute_fallback()` | 工具失败时提供替代方案 |
| 3 | **记忆压缩** | ~0.5s | `compactor.compact()` | 上下文过长导致 LLM 失败 |
| 4 | **Agent 池** | <0.1s | `pool.get()` | 需要快速切换 Agent |
| 5 | **增量检查点** | ~0.05s | `manager.save_increment()` | 大任务长时执行 |
| 6 | **优雅降级** | <0.1s | `gd.degrade()` | 资源不足/连续失败 |

---

## 统一入口

```python
from simple_agent.core.self_healing import SelfHealingCoordinator

coordinator = SelfHealingCoordinator()

# 所有 6 种自愈手段统一接口
coordinator.can_execute_tool("WebSearchTool")     # 熔断器
coordinator.try_fallback(...)                      # 降级
coordinator.try_compact_memory(...)                # 记忆压缩
coordinator.warmup_agents(["Planner"])             # Agent 池
coordinator.get_agent("Developer")                 # 快速获取 Agent
coordinator.save_increment(...)                    # 增量检查点
coordinator.check_degradation(metrics)             # 优雅降级
```

---

## 熔断器 (Circuit Breaker)

```python
from simple_agent.core.self_healing import CircuitBreaker

cb = CircuitBreaker()

# 执行前检查
if cb.can_execute("WebSearchTool"):
    result = tool.execute()
    cb.record_success("WebSearchTool")
else:
    # 使用降级
    pass

# 记录失败（3 次后熔断）
cb.record_failure("WebSearchTool", "错误")
```

**状态机**:
```
CLOSED →[3 次失败]→ OPEN →[60 秒]→ HALF_OPEN →[2 次成功]→ CLOSED
```

---

## 快速降级 (Fallback)

```python
from simple_agent.core.self_healing import FallbackProvider

provider = FallbackProvider()

result = provider.execute_fallback(
    "WebSearchTool",
    {"query": "查询"},
    "网络错误"
)

if result.success:
    print(result.content)  # 降级内容
    print(result.confidence)  # 置信度
```

**内置降级**:
- WebSearchTool → 本地知识
- HttpTool → 缓存
- StockMarketTool → 备用信息

---

## 记忆压缩 (Memory Compaction)

```python
from simple_agent.core.self_healing import MemoryCompactor

compactor = MemoryCompactor(max_messages=50)

if compactor.should_compact(messages):
    compressed, summary = compactor.compact(messages)
    # messages: 100 → compressed: 15
```

---

## Agent 池 (Agent Pool)

```python
from simple_agent.core.self_healing import AgentPool

pool = AgentPool(pool_size=5)
pool.warmup(["Planner", "Developer"])

# 快速切换 <0.1s
agent = pool.get("Developer")
```

---

## 增量检查点 (Incremental Checkpoint)

```python
from simple_agent.core.self_healing import IncrementalCheckpointManager

manager = IncrementalCheckpointManager()

# 保存增量 (0.05s)
manager.save_increment("task-001", "message", msg_data)

# 加载状态
state = manager.load_state("task-001")
```

---

## 优雅降级 (Graceful Degradation)

```python
from simple_agent.core.self_healing import GracefulDegradation

gd = GracefulDegradation()

# 4 个级别
# Level 1: Normal (max_iter=15)
# Level 2: Reduced (max_iter=8)
# Level 3: Minimal (max_iter=3)
# Level 4: Emergency (max_iter=1)

gd.degrade(reason="连续失败")
gd.apply_to_agent(agent)
```

---

## 性能对比

| 操作 | 传统 | 自愈 | 提升 |
|------|------|------|------|
| 工具失败处理 | ~5s | <0.1s | 50x |
| Agent 切换 | ~1s | <0.1s | 10x |
| 状态保存 | ~0.5s | ~0.05s | 10x |

---

## 测试

```bash
# 42 个自愈测试
pytest tests/test_self_healing.py tests/test_self_healing_enhanced.py -v
```

---

## 文件结构

```
core/
  self_healing.py           # 统一自愈系统（1100 行）
    - Core Layer: ExceptionDiagnoser, AgentRegenerator, TaskResumer
    - Enhancement Layer: CircuitBreaker, FallbackProvider, MemoryCompactor,
                         AgentPool, IncrementalCheckpointManager, GracefulDegradation
    - Coordinator: SelfHealingCoordinator (统一入口)

tests/
  test_self_healing.py           # 14 个核心测试
  test_self_healing_enhanced.py  # 28 个增强测试

docs/
  SELF_HEALING_QUICKREF.md  # 本文档
```
