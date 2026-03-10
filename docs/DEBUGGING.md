# Simple Agent 调试系统文档

本文档整合了 Simple Agent 的调试功能、CLI 调试命令和调试最佳实践。

---

## 目录

1. [调试系统概述](#1-调试系统概述)
2. [默认调试模式](#2-默认调试模式)
3. [CLI 调试命令](#3-cli-调试命令)
4. [调试功能详解](#4-调试功能详解)
5. [调试最佳实践](#5-调试最佳实践)

---

## 1. 调试系统概述

调试功能支持跟踪和显示 Agent 及 Workflow 的使用情况，包括：
- 执行记录
- 性能统计
- 成功率分析
- 详细日志

### 调试级别

**基础调试**:
- 任务执行状态
- 简单进度指示
- 基本错误信息

**详细调试**:
- 详细的执行步骤
- 内部状态变化
- 工具调用详情

**深度调试**:
- 详细的内存使用
- 推理过程跟踪
- 性能指标收集

---

## 2. 默认调试模式

### 2.1 启动时状态

从 CLI 启动开始，**Debug 模式默认已启用**，无需手动开启。

```
============================================================
CLI Agent - 智能任务助手
============================================================

默认设置:
  - 隔离模式：✓ 已开启
  - 调试模式：✓ 已开启 (显示详细执行过程)
  - 使用 /debug off 可关闭调试模式
```

### 2.2 详细执行过程显示

```
[Debug] Agent 开始执行:
  名称：金融分析师
  输入：分析未来什么职业前景更好...

[Debug] Agent 执行完成:
  状态：✓ 成功
  时长：42.037s
```

### 2.3 Workflow 执行跟踪

```
============================================================
[Debug] Workflow 开始执行:
  名称：代码开发工作流
  描述：开发 - 审查 - 测试的完整流程
  输入：创建一个计算两个数之和的函数...
============================================================

[Debug] Workflow 步骤 1:
  名称：开发实现
  Agent: 开发工程师
  状态：✓ 成功
  时长：15.234s
```

### 2.4 关闭调试模式

```bash
# 关闭调试模式
/debug off

# 重新开启
/debug on
```

关闭后：
- 不再显示 `[Debug]` 开头的详细执行过程
- 调试跟踪器仍然记录执行数据
- 仍可使用 `/debug summary` 和 `/debug stats` 查看统计

---

## 3. CLI 调试命令

### 3.1 命令列表

| 命令 | 说明 |
|------|------|
| `/debug` | 切换调试模式 |
| `/debug on` | 启用调试模式 |
| `/debug off` | 关闭调试模式 |
| `/debug summary` | 显示调试摘要 |
| `/debug stats` | 显示详细统计信息 |

### 3.2 `/debug summary`

显示调试执行摘要，包括：
- Agent 执行总次数、成功/失败次数
- Workflow 执行总次数、成功/失败次数
- 总步骤数和步骤成功率
- 平均执行时长

```
[CLI Agent] 你：/debug summary

============================================================
调试执行摘要
============================================================

📊 Workflow 执行:
  总次数：3
  成功：3
  失败：0
  总时长：0.001s
  平均时长：0.000s
  总步骤：7
  成功步骤：7
  步骤成功率：100.0%

============================================================
```

### 3.3 `/debug stats`

显示详细的统计信息，包括：
- Agent 执行的详细统计（按 Agent 分类）
- Workflow 执行的详细统计（按 Workflow 分类）
- 每个 Agent/Workflow 的执行次数、平均耗时、工具调用次数

```
[CLI Agent] 你：/debug stats

============================================================
详细统计信息
============================================================

📊 Agent 执行统计:
  总执行次数：13
  成功：13
  失败：0
  成功率：100.0%
  平均耗时：0.005 秒

  按 Agent 分类:
    - 代码审查员:
        执行：6 次
        平均耗时：0.011 秒
        工具调用：0 次
    - 测试生成器:
        执行：4 次
        平均耗时：0.000 秒
        工具调用：0 次

📊 Workflow 执行统计:
  总执行次数：3
  成功：3
  失败：0
  成功率：100.0%
  平均耗时：0.000 秒
  总步骤数：7
  步骤成功率：100.0%

============================================================
```

---

## 4. 调试功能详解

### 4.1 启用/禁用调试

```python
from simple_agent.core import enable_debug, disable_debug

# 启用调试（详细模式）
enable_debug(verbose=True)

# 启用调试（简单模式）
enable_debug(verbose=False)

# 禁用调试
disable_debug()
```

### 4.2 Agent 调试

```python
from simple_agent.core import Agent

agent = Agent(llm=llm, name="MyAgent")

# 启用调试跟踪
result = agent.run("任务描述", verbose=False, debug=True)
```

### 4.3 Workflow 调试

```python
from simple_agent.core import Workflow, Agent

workflow = Workflow("代码审查流程")
workflow.add_step("读取", file_agent, output_key="content")
workflow.add_step("审查", review_agent, input_key="content")

# 启用调试跟踪
context = workflow.run("审查 ./src/code.py", verbose=False, debug=True)
```

### 4.4 获取执行记录

```python
from simple_agent.core import tracker

# 获取最近的 Agent 执行记录
agent_records = tracker.get_recent_agent_records(limit=10)
for record in agent_records:
    print(f"{record['agent_name']}: {record['duration']}s")

# 获取最近的 Workflow 执行记录
workflow_records = tracker.get_recent_workflow_records(limit=5)
for record in workflow_records:
    print(f"{record['workflow_name']}: {record['total_steps']} steps")
```

### 4.5 获取统计信息

```python
from simple_agent.core import tracker, get_debug_summary, print_debug_summary

# Agent 统计
agent_stats = tracker.get_agent_stats()
print(f"Agent 平均执行时间：{agent_stats['avg_duration']}s")

# Workflow 统计
workflow_stats = tracker.get_workflow_stats()
print(f"Workflow 步骤成功率：{workflow_stats['step_success_rate']}%")

# 获取摘要
summary = get_debug_summary()
print(summary)

# 打印格式化摘要
print_debug_summary()
```

### 4.6 清空记录

```python
from simple_agent.core import tracker

# 清空所有执行记录
tracker.clear()
```

---

## 5. 调试最佳实践

### 5.1 开发环境启用

```python
import os

if os.environ.get("DEBUG"):
    from simple_agent.core import enable_debug
    enable_debug(verbose=True)
```

### 5.2 性能分析

```python
from simple_agent.core import enable_debug, print_debug_summary, Agent

enable_debug(verbose=False)

# 执行多次测试
for i in range(10):
    agent = Agent(llm=llm)
    agent.run(f"测试任务 {i}", debug=True)

# 查看统计
print_debug_summary()
```

### 5.3 问题排查

```python
from simple_agent.core import enable_debug, tracker

enable_debug(verbose=True)

try:
    result = workflow.run(task, debug=True)
except Exception as e:
    # 查看执行记录
    records = tracker.get_recent_agent_records()
    for r in records:
        if not r['success']:
            print(f"失败：{r['agent_name']} - {r['error']}")
```

### 5.4 使用场景

#### ✅ 建议开启 Debug 模式的场景

1. **开发和测试阶段**
   - 查看 Agent 和 Workflow 的执行细节
   - 分析性能瓶颈
   - 排查问题

2. **学习使用系统**
   - 了解 Agent 如何处理任务
   - 观察 Workflow 的执行流程

3. **性能分析**
   - 查看每个 Agent 的执行时间
   - 分析 Workflow 各步骤的耗时

#### ❌ 可以关闭 Debug 模式的场景

1. **生产环境性能优先**
   - 减少输出日志量
   - 略微提升性能（约 1-2%）

2. **简单任务快速执行**
   - 执行大量简单任务
   - 不需要详细输出

---

## 6. 数据结构

### Agent 执行记录

```python
{
    "agent_name": "MyAgent",
    "agent_version": "1.0.0",
    "instance_id": "agent-1",
    "input": "任务描述...",
    "output": "执行结果...",
    "duration": 0.123,
    "tool_calls": 3,
    "iterations": 2,
    "success": True,
    "error": None,
    "timestamp": "2026-03-07T17:41:19.079977"
}
```

### Workflow 执行记录

```python
{
    "workflow_name": "代码审查流程",
    "description": "审查代码并生成报告",
    "duration": 0.123,
    "total_steps": 2,
    "successful_steps": 2,
    "success": True,
    "steps": [...],
    "timestamp": "2026-03-07T17:41:19.079977"
}
```

---

## 7. API 参考

### 函数

| 函数 | 说明 |
|------|------|
| `enable_debug(verbose=True)` | 启用调试跟踪 |
| `disable_debug()` | 禁用调试跟踪 |
| `get_debug_summary()` | 获取摘要字典 |
| `print_debug_summary()` | 打印格式化摘要 |

### 类

| 类 | 说明 |
|----|------|
| `DebugTracker` | 调试跟踪器（单例） |
| `AgentExecutionRecord` | Agent 执行记录 |
| `WorkflowStepRecord` | Workflow 步骤记录 |
| `WorkflowExecutionRecord` | Workflow 执行记录 |

### Tracker 方法

| 方法 | 说明 |
|------|------|
| `get_agent_stats()` | 获取 Agent 统计 |
| `get_workflow_stats()` | 获取 Workflow 统计 |
| `get_summary()` | 获取完整摘要 |
| `get_recent_agent_records(limit)` | 获取最近 Agent 记录 |
| `get_recent_workflow_records(limit)` | 获取最近 Workflow 记录 |
| `clear()` | 清空所有记录 |
| `print_summary()` | 打印摘要 |

---

## 8. 常见问题

**Q: 为什么统计信息显示 0 次执行？**

A: 可能是因为：
- 还没有执行任何 Agent 或 Workflow 任务
- 调试跟踪器被禁用（使用 `/debug on` 启用）
- 执行时没有使用 `debug=True` 参数

**Q: 统计信息会保存多久？**

A: 统计信息在当前会话期间有效。重启 CLI 后，统计信息会重置。

**Q: 如何清空统计信息？**

A: 目前不支持手动清空。重启 CLI 即可重置所有统计。

**Q: 统计信息影响性能吗？**

A: 调试跟踪的开销很小，可以忽略不计。但在生产环境中，如果不需要可以关闭调试模式。

**Q: 默认开启 debug 会影响性能吗？**

A: 影响非常小（约 1-2%），可以忽略不计。记录的数据占用内存也很少。

---

**文档版本**: 2.0  
**最后更新**: 2026-03-08  
**合并自**: DEBUG_FEATURES.md, CLI_DEBUG_COMMANDS.md, DEFAULT_DEBUG_MODE.md, CLI_AND_DEBUGGING_GUIDE.md
