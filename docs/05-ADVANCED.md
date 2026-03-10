# Simple Agent 高级功能

## 1. 自愈系统 (Self-Healing)

自愈系统提供 6 大增强功能，提升系统稳定性和容错能力。

### 1.1 熔断器 (Circuit Breaker)

避免重复调用失败的工具或 Agent：

```python
from simple_agent.core.self_healing import SelfHealingCoordinator

coordinator = SelfHealingCoordinator()

# 执行前检查
if not coordinator.can_execute_tool("WebSearchTool"):
    # 使用降级策略
    result = coordinator.try_fallback(...)
```

**特点**:
- 自动记录失败次数
- 达到阈值后自动熔断
- 0s 开销，不影响正常调用

### 1.2 降级策略 (Fallback)

提供快速替代方案：

```python
# 当主要工具失败时
recovery = coordinator.handle_exception(agent, exception, task)
if recovery.should_retry:
    # 使用备用 Agent 重试
    result = recovery.new_agent.run(task.input)
```

**特点**:
- 快速替代方案 (<0.1s)
- 支持 Agent 切换
- 支持策略降级

### 1.3 记忆压缩 (Memory Compression)

解决上下文过长问题：

```python
# 自动压缩过长的记忆
coordinator.try_compact_memory(messages, task_id)
```

**特点**:
- 保留关键信息
- 压缩冗长对话
- 约 0.5s 处理时间

### 1.4 Agent 池 (Agent Pool)

快速切换备用 Agent：

```python
# 获取可用 Agent
backup_agent = coordinator.get_agent("Developer")

# 快速切换
agent = coordinator.get_agent("Tester")
```

**特点**:
- 预加载常用 Agent
- 快速切换 (<0.1s)
- 支持技能匹配

### 1.5 增量检查点 (Incremental Checkpoint)

高效保存进度：

```python
# 保存迭代进度
coordinator.save_increment(task_id, "iteration", {
    "step": 5,
    "data": {...}
})
```

**特点**:
- 只保存变更部分
- 高效保存 (~0.05s)
- 支持恢复

### 1.6 优雅降级 (Graceful Degradation)

资源自适应：

```python
# 4 级别配置
# Level 1: 完整功能
# Level 2: 减少并发
# Level 3: 简化模型
# Level 4: 最小功能集
```

---

## 2. 反思学习系统 (Reflection Learning)

反思学习系统记录执行过程、分析性能、生成优化建议并复用经验。

### 2.1 启用反思学习

```python
from simple_agent.core.workflow import Workflow

workflow = Workflow("CodeReview")
workflow.add_step("审查", reviewer_agent)

# 启用反思学习
result = workflow.run(
    initial_input="审查代码",
    enable_reflection=True  # 自动记录、分析
)
```

### 2.2 获取优化建议

```python
from simple_agent.core.reflection_learning import get_learning_coordinator

coordinator = get_learning_coordinator()

# 获取建议
suggestions = coordinator.get_optimization_suggestions()

for suggestion in suggestions:
    print(f"任务：{suggestion.task_pattern}")
    print(f"建议：{suggestion.optimization}")
    print(f"预期提升：{suggestion.expected_improvement}")
```

### 2.3 经验复用

```python
# 在类似任务中应用历史经验
similar_tasks = coordinator.find_similar_tasks(current_task, threshold=0.8)

for task in similar_tasks:
    experience = coordinator.get_experience(task.id)
    if experience.success:
        # 应用成功经验
        apply_experience(experience)
```

### 2.4 性能分析

```python
# 识别瓶颈
analysis = coordinator.analyze_performance()

print(f"慢步骤：{analysis.slow_steps}")
print(f"长链路：{analysis.long_chains}")
print(f"冗余步骤：{analysis.redundant_steps}")
```

---

## 3. 软件开发支持

### 3.1 Git Worktree 管理

支持多项目并行开发：

```python
from simple_agent.core.dev.git_worktree import GitWorktreeManager

manager = GitWorktreeManager()

# 创建工作树
wt = manager.create_worktree("feature-1", branch="develop")

# 在工作树中执行
agent.run("在 worktree 中开发功能", worktree=wt)

# 清理
manager.remove_worktree("feature-1")
```

### 3.2 环境配置

```python
from simple_agent.core.dev.environment_setup import ProjectInitializer

init = ProjectInitializer()

# Python 项目
init.setup_python_project(
    path="./my_project",
    name="my_project",
    dependencies=["fastapi", "uvicorn"]
)

# Node.js 项目
init.setup_node_project(
    path="./my_frontend",
    framework="react"
)
```

### 3.3 开发流程自动化

```python
from simple_agent.core.dev.workflow import DevelopmentWorkflow

workflow = DevelopmentWorkflow()

# 代码审查流程
result = workflow.code_review(
    project_path="./src",
    include_tests=True,
    include_security=True
)

# 测试流程
result = workflow.run_tests(
    test_command="pytest",
    coverage=True
)
```

---

## 4. 本地服务化

### 4.1 启动 API 服务

```bash
# 后台启动
python cli.py --start

# 查看状态
python cli.py --status

# 查看日志
python cli.py --logs 100

# 停止服务
python cli.py --stop
```

### 4.2 API 使用

```bash
# 执行 Agent 任务
curl -X POST http://localhost:8000/api/v1/agent/run \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "developer", "input": "分析项目"}'

# 查询任务状态
curl http://localhost:8000/api/v1/task/{task_id}/status

# Swagger 文档
# 访问 http://localhost:8000/docs
```

### 4.3 WebSocket 实时推送

```python
import websocket

ws = websocket.connect("ws://localhost:8000/ws/task_status")

# 订阅任务
ws.send('{"type": "subscribe", "task_id": "xxx"}')

# 接收进度
while True:
    msg = ws.recv()
    print(f"进度更新：{msg}")
```

---

## 5. 定时任务

### 5.1 创建定时任务

```bash
# 每小时执行
python cli.py --schedule-create --name "每小时检查" \
  --agent developer --input "检查系统" --frequency 1hour

# 每天 9 点执行
python cli.py --schedule-create --name "每日晨报" \
  --agent developer --input "生成日报" --frequency at:09:00

# 每周一 10 点执行
python cli.py --schedule-create --name "每周周报" \
  --agent developer --input "生成周报" --frequency weekly:Monday:10:00
```

### 5.2 管理定时任务

```bash
# 列出任务
python cli.py --schedule-list

# 查看详情
python cli.py --schedule-get <task_id>

# 删除任务
python cli.py --schedule-delete <task_id>

# 启用/禁用
python cli.py --schedule-enable <task_id>
python cli.py --schedule-disable <task_id>
```

---

## 6. 质量保障

### 6.1 质量评估 Agent

```python
from simple_agent.builtin_agents import get_agent

evaluator = get_agent("quality_evaluator")

# 评估回答质量
result = evaluator.run("评估以下回答：[回答内容]")

# 输出
{
    "scores": {
        "accuracy": 4,
        "completeness": 3,
        "practicality": 4,
        "clarity": 5,
        "depth": 3
    },
    "total_score": 3.8,
    "passed": true,
    "feedback": "具体反馈...",
    "improvement_suggestions": ["建议 1", "建议 2"]
}
```

### 6.2 质量检查清单

```python
from simple_agent.core.quality_checker import QualityChecker

# 代码检查
checker = QualityChecker("code")
report = checker.check(code_content, context={})

print(f"通过率：{report.pass_rate}")
for item in report.results:
    print(f"{'✓' if item.passed else '✗'} {item.item}")
```

---

## 7. 性能基准

### 7.1 调度器吞吐量

```python
# 100 个任务，10 个 Agent，并发 10
# 吞吐量：>50 任务/秒
```

### 7.2 并行效率

```python
# 10 个 0.1s 任务并行
# 理论串行：1.0s
# 实际并行：<0.2s
# 并行效率：>5x
```

---

## 8. 相关文件

- **[01-QUICKSTART.md](./01-QUICKSTART.md)** - 快速开始
- **[02-ARCHITECTURE.md](./02-ARCHITECTURE.md)** - 架构设计
- **[03-USER-GUIDE.md](./03-USER-GUIDE.md)** - 使用指南
- **[04-DEVELOPMENT.md](./04-DEVELOPMENT.md)** - 开发指南
- **[SERVICE.md](./SERVICE.md)** - 服务化详细文档
- **[TESTING.md](./TESTING.md)** - 测试详细指南
