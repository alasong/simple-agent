# 调试功能文档

## 概述

调试功能支持跟踪和显示 Agent 及 Workflow 的使用情况，包括：
- 执行记录
- 性能统计
- 成功率分析
- 详细日志

## 快速开始

### 启用调试

```python
from core import enable_debug, Agent, Workflow

# 启用调试（详细模式）
enable_debug(verbose=True)

# 或者简单模式
enable_debug(verbose=False)
```

### 禁用调试

```python
from core import disable_debug

disable_debug()
```

---

## Agent 调试

### 基本使用

```python
from core import Agent

llm = OpenAILLM()
agent = Agent(llm=llm, name="MyAgent")

# 启用调试跟踪
result = agent.run("任务描述", verbose=False, debug=True)
```

### 输出示例

```
[Debug] Agent 开始执行:
  名称：MyAgent
  实例 ID: agent-1
  输入：任务描述...

[Debug] Agent 执行完成:
  状态：✓ 成功
  时长：0.123s
```

---

## Workflow 调试

### 基本使用

```python
from core import Workflow, Agent

# 创建工作流
workflow = Workflow("代码审查流程")
workflow.add_step("读取", file_agent, output_key="content")
workflow.add_step("审查", review_agent, input_key="content")

# 启用调试跟踪
context = workflow.run("审查 ./src/code.py", verbose=False, debug=True)
```

### 输出示例

```
============================================================
[Debug] Workflow 开始执行:
  名称：代码审查流程
  描述：审查代码并生成报告
  输入：审查 ./src/code.py...
============================================================

[Debug] Workflow 步骤 1:
  名称：读取
  Agent: FileAgent
  状态：✓ 成功
  时长：0.045s

[Debug] Workflow 步骤 2:
  名称：审查
  Agent: ReviewAgent
  状态：✓ 成功
  时长：0.078s

============================================================
[Debug] Workflow 执行完成:
  总步骤：2
  成功：2/2
  总时长：0.123s
============================================================
```

---

## 统计信息

### 获取摘要

```python
from core import get_debug_summary, print_debug_summary

# 获取摘要字典
summary = get_debug_summary()
print(summary)

# 打印格式化摘要
print_debug_summary()
```

### 摘要内容

```python
{
    'agent': {
        'count': 5,
        'successful': 5,
        'failed': 0,
        'total_duration': 0.615,
        'avg_duration': 0.123,
        'total_tool_calls': 12,
        'by_agent': {
            'FileAgent': {
                'count': 2,
                'success_rate': 100.0,
                'avg_duration': 0.045
            },
            'ReviewAgent': {
                'count': 3,
                'success_rate': 100.0,
                'avg_duration': 0.078
            }
        }
    },
    'workflow': {
        'count': 1,
        'successful': 1,
        'failed': 0,
        'total_duration': 0.615,
        'avg_duration': 0.615,
        'total_steps': 2,
        'successful_steps': 2,
        'step_success_rate': 100.0
    },
    'timestamp': '2026-03-07T17:41:19.079977'
}
```

### 打印摘要示例

```
============================================================
[调试摘要] 执行统计
============================================================

📊 Agent 执行:
  总次数：5
  成功：5
  失败：0
  总时长：0.615s
  平均时长：0.123s
  工具调用：12 次

  按 Agent 统计:
    FileAgent:
      执行：2 次
      成功率：100.0%
      平均：0.045s
    ReviewAgent:
      执行：3 次
      成功率：100.0%
      平均：0.078s

📊 Workflow 执行:
  总次数：1
  成功：1
  失败：0
  总时长：0.615s
  平均时长：0.615s
  总步骤：2
  成功步骤：2
  步骤成功率：100.0%

============================================================
```

---

## 高级用法

### 获取执行记录

```python
from core import tracker

# 获取最近的 Agent 执行记录
agent_records = tracker.get_recent_agent_records(limit=10)
for record in agent_records:
    print(f"{record['agent_name']}: {record['duration']}s")

# 获取最近的 Workflow 执行记录
workflow_records = tracker.get_recent_workflow_records(limit=5)
for record in workflow_records:
    print(f"{record['workflow_name']}: {record['total_steps']} steps")
```

### 获取统计信息

```python
from core import tracker

# Agent 统计
agent_stats = tracker.get_agent_stats()
print(f"Agent 平均执行时间：{agent_stats['avg_duration']}s")

# Workflow 统计
workflow_stats = tracker.get_workflow_stats()
print(f"Workflow 步骤成功率：{workflow_stats['step_success_rate']}%")
```

### 清空记录

```python
from core import tracker

# 清空所有执行记录
tracker.clear()
```

---

## 调试器配置

### DebugTracker 属性

```python
from core import tracker

# 启用/禁用
tracker.enabled = True  # 启用
tracker.enabled = False  # 禁用

# 详细模式
tracker.verbose = True  # 详细输出
tracker.verbose = False  # 简单输出
```

### 全局函数

```python
from core import enable_debug, disable_debug

# 启用（详细模式）
enable_debug(verbose=True)

# 启用（简单模式）
enable_debug(verbose=False)

# 禁用
disable_debug()
```

---

## 记录数据结构

### AgentExecutionRecord

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

### WorkflowStepRecord

```python
{
    "workflow_name": "代码审查流程",
    "step_name": "读取",
    "step_index": 1,
    "agent_name": "FileAgent",
    "instance_id": "file-agent-1",
    "duration": 0.045,
    "success": True,
    "error": None
}
```

### WorkflowExecutionRecord

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

## 最佳实践

### 1. 开发环境启用

```python
import os

if os.environ.get("DEBUG"):
    from core import enable_debug
    enable_debug(verbose=True)
```

### 2. 性能分析

```python
from core import enable_debug, print_debug_summary, Agent

enable_debug(verbose=False)

# 执行多次测试
for i in range(10):
    agent = Agent(llm=llm)
    agent.run(f"测试任务 {i}", debug=True)

# 查看统计
print_debug_summary()
```

### 3. 问题排查

```python
from core import enable_debug, tracker

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

---

## API 参考

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

## 示例代码

### 完整示例

```python
from core import (
    Agent, Workflow, 
    enable_debug, print_debug_summary
)
from core.llm import OpenAILLM

# 启用调试
enable_debug(verbose=True)

# 创建 Agent
llm = OpenAILLM()
agent1 = Agent(llm=llm, name="分析 Agent")
agent2 = Agent(llm=llm, name="报告 Agent")

# 创建工作流
workflow = Workflow("分析报告流程")
workflow.add_step("分析", agent1, output_key="analysis")
workflow.add_step("生成报告", agent2, input_key="analysis")

# 执行并调试
result = workflow.run("分析以下数据：...", debug=True)

# 查看统计
print_debug_summary()
```

---

**最后更新**: 2026-03-07  
**版本**: 1.0.0
