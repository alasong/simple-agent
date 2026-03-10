# Simple Agent 开发指南

## 1. 代码开发流程

### 1.1 Agent 执行流程

```
用户输入 → Agent.run() → LLM 推理 → 工具调用 → 写入文件
```

**核心代码逻辑**:

```python
def run(self, user_input: str, verbose: bool = True) -> str:
    """Agent 主循环"""
    # 1. 感知：添加用户输入到记忆
    self.memory.add_user(user_input)

    iteration = 0
    while iteration < self.max_iterations:
        iteration += 1

        # 2. 推理：调用 LLM
        response = self.llm.chat(
            messages=self.memory.get_messages(),
            tools=self.tool_registry.get_openai_tools()
        )

        # 3. 如果没有工具调用，返回结果
        if not tool_calls:
            return content

        # 4. 行动：执行所有工具调用
        for tool_call in tool_calls:
            result = self._execute_tool(tool_name, arguments)
            self.memory.add_tool_result(...)

    return "达到最大迭代次数"
```

### 1.2 逐步写入机制

Agent 是**逐步写入**文件的，每次迭代可能写入一个文件：

```python
# 迭代 1: LLM 决定创建 file1.py → WriteFileTool 执行
# 迭代 2: LLM 决定创建 file2.py → WriteFileTool 执行
# 迭代 3: LLM 确认完成 → 返回结果
```

### 1.3 Swarm 多文件开发

```python
from simple_agent.swarm import SwarmOrchestrator, Task

tasks = [
    Task(id="1", description="创建 models/user.py"),
    Task(id="2", description="创建 services/user_service.py", dependencies=["1"]),
    Task(id="3", description="创建 api/user_api.py", dependencies=["2"]),
    Task(id="4", description="创建 tests/test_user.py", dependencies=["2", "3"]),
]

orchestrator = SwarmOrchestrator(agent_pool=agents)
orchestrator.task_graph.build_from_tasks(tasks)
result = await orchestrator.solve("开发用户管理系统")
```

---

## 2. 创建自定义 Agent

### 2.1 YAML 配置方式

创建 `configs/my_agent.yaml`:

```yaml
name: 数据分析师
version: 1.0.0
description: 专注于数据分析和可视化
system_prompt: |
  你是数据分析专家，擅长:
  - 数据清洗和预处理
  - 统计分析和可视化
  - 生成分析报告
tools:
  - ReadFileTool
  - WriteFileTool
  - BashTool
  - WebSearchTool
max_iterations: 20
```

加载:
```python
from simple_agent.builtin_agents import load_agent
agent = load_agent("configs/my_agent.yaml")
```

### 2.2 代码方式

```python
from simple_agent.core import Agent, OpenAILLM
from simple_agent.tools import ReadFileTool, WriteFileTool

llm = OpenAILLM()
agent = Agent(
    llm=llm,
    name="DataAnalyst",
    system_prompt="你是数据分析专家",
    tools=[ReadFileTool(), WriteFileTool()],
    max_iterations=20
)
```

---

## 3. 创建自定义工具

### 3.1 继承 BaseTool

```python
from simple_agent.core import BaseTool, ToolResult
from dataclasses import dataclass

@dataclass
class MyCustomTool(BaseTool):
    """自定义工具"""

    @property
    def name(self) -> str:
        return "my_custom_tool"

    @property
    def description(self) -> str:
        return "执行自定义操作"

    def execute(self, param1: str, param2: int = 10) -> ToolResult:
        try:
            result = f"处理结果：{param1}, {param2}"
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
```

### 3.2 注册工具

```python
from simple_agent.core import ToolRegistry

registry = ToolRegistry()
registry.register(MyCustomTool)

# 使用
agent = Agent(tools=[MyCustomTool(), ...])
```

---

## 4. 调试技巧

### 4.1 启用调试模式

```python
from simple_agent.core import enable_debug

enable_debug(verbose=True)
```

### 4.2 查看详细日志

```python
agent = Agent(...)
result = agent.run("任务", verbose=True, debug=True)
```

### 4.3 获取执行统计

```python
from simple_agent.core import tracker

stats = tracker.get_agent_stats()
print(f"执行次数：{stats['total_executions']}")
print(f"平均耗时：{stats['avg_duration']}s")
print(f"成功率：{stats['success_rate']}")
```

### 4.4 使用 CLI 调试命令

```bash
python cli.py

# 启用调试
/debug on

# 查看摘要
/debug summary

# 查看详细统计
/debug stats
```

---

## 5. 测试

### 5.1 运行测试

```bash
# 日常测试 (推荐，约 30 秒)
./tests/run_daily_tests.sh

# 快速测试 (5 分钟内)
./tests/run_quick_tests.sh

# 完整测试 (约 5-10 分钟)
./tests/run_all_tests.sh

# 深度测试
.venv/bin/python -m pytest tests/test_deep_core.py -v
```

### 5.2 编写测试

```python
import pytest
from simple_agent.core import Agent, OpenAILLM

class TestMyAgent:
    def test_simple_task(self):
        agent = Agent(llm=OpenAILLM(), name="Test")
        result = agent.run("简单任务")
        assert result is not None

    def test_with_tools(self):
        agent = Agent(llm=OpenAILLM(), tools=[...])
        result = agent.run("使用工具的任务")
        assert result.success
```

---

## 6. 输出目录管理

### 6.1 目录结构

```
simple-agent/
├── output/
│   ├── cli/          # CLI 任务输出
│   │   ├── task_001/
│   │   └── ...
│   ├── swarm/        # Swarm 任务输出
│   │   ├── swarm_001/
│   │   └── ...
│   └── generated/    # 生成的代码
│       └── project_name/
└── ...
```

### 6.2 配置输出

```yaml
# configs/config.yaml
directories:
  output_root: "./output"
  cli_output: "./output/cli"
  swarm_output: "./output/swarm"
  generated_code: "./output/generated"
```

### 6.3 Git 忽略

```gitignore
# 输出目录
output/
*.log
*.tmp
```

---

## 7. 性能优化

### 7.1 并发设置

```python
# 增加并发数
orchestrator = SwarmOrchestrator(
    agent_pool=agents,
    max_concurrent=5  # 默认 3
)
```

### 7.2 缓存 Agent

```python
# 避免重复创建
agents_cache = {}

def get_agent(name: str):
    if name not in agents_cache:
        agents_cache[name] = create_agent(name)
    return agents_cache[name]
```

### 7.3 增量保存

```python
from simple_agent.core.self_healing import SelfHealingCoordinator

coordinator = SelfHealingCoordinator()

# 定期保存进度
coordinator.save_increment(task_id, "iteration", {"step": 1, "data": ...})
```

---

## 8. 常见问题

### Q: 如何追踪 Agent 执行过程？
A: 使用 `enable_debug(verbose=True)` 或 CLI 的 `/debug on` 命令。

### Q: 工具调用失败如何处理？
A: 实现错误处理逻辑，提供降级策略或使用重试机制。

### Q: 如何优化长任务执行？
A: 使用增量保存、设置检查点、合理设置 max_iterations。

### Q: 如何复用历史经验？
A: 使用反思学习系统，自动记录和应用成功经验。
