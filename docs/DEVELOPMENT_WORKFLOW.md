# Simple Agent 开发工作流文档

本文档整合了 Agent 代码开发流程、逐步写入机制和输出目录管理。

---

## 目录

1. [代码开发流程](#1-代码开发流程)
2. [逐步写入机制](#2-逐步写入机制)
3. [输出目录管理](#3-输出目录管理)

---

## 1. 代码开发流程

### 1.1 流程概述

Agent 开发和写入代码的流程分为以下几个步骤：

1. **理解需求** → Agent 通过 LLM 理解用户需求
2. **规划代码** → LLM 生成代码结构和实现方案
3. **调用工具** → 使用 `WriteFileTool` 写入文件
4. **验证结果** → 读取文件或使用其他工具验证

### 1.2 核心执行流程

```
用户输入 → Agent.run() → LLM 推理 → 工具调用 → 写入文件
```

**核心代码逻辑**:

```python
def run(self, user_input: str, verbose: bool = True) -> str:
    """主循环"""
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

### 1.3 WriteFileTool 实现

```python
@tool(tags=["file", "io"], description="写入文件内容")
class WriteFileTool(BaseTool):
    """写文件工具"""
    
    def execute(self, file_path: str, content: str) -> ToolResult:
        try:
            # 1. 创建目录（如果不存在）
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # 2. 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return ToolResult(success=True, output=f"成功写入文件：{file_path}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
```

### 1.4 完整流程示例

```python
from core.agent import Agent
from core.llm import OpenAILLM
from tools.file import WriteFileTool, ReadFileTool

# 1. 创建 Agent
llm = OpenAILLM()
agent = Agent(
    llm=llm,
    tools=[WriteFileTool(), ReadFileTool()],
    name="Developer",
    system_prompt="你是软件开发专家，擅长编写高质量代码"
)

# 2. 执行任务
result = agent.run(
    "帮我创建一个 Python 文件 calculator.py，实现一个计算器类",
    verbose=True
)
```

**执行流程**:

```
[Agent Developer] 开始执行任务...

迭代 1:
  → LLM 思考：需要创建 calculator.py 文件
  → 调用 WriteFileTool
  → WriteFileTool.execute() 写入文件
  → 返回：成功写入文件

迭代 2:
  → LLM 思考：任务已完成
  → 返回最终结果

任务完成！
```

### 1.5 Swarm 协作开发

```python
import asyncio
from swarm import SwarmOrchestrator
from core.agent import Agent

agents = [
    Agent(name="架构师", system_prompt="负责设计代码结构"),
    Agent(name="开发者", system_prompt="负责编写代码"),
    Agent(name="测试员", system_prompt="负责编写测试"),
]

orchestrator = SwarmOrchestrator(agent_pool=agents, llm=llm)

result = await orchestrator.solve(
    "开发一个完整的用户管理系统，包括：\n"
    "1. 用户模型（models/user.py）\n"
    "2. 用户服务（services/user_service.py）\n"
    "3. API 接口（api/user_api.py）\n"
    "4. 单元测试（tests/test_user.py）"
)
```

**Swarm 执行流程**:

```
[Swarm] 任务分解:
  Task 1: 设计用户模型 → 分配给 架构师
  Task 2: 实现用户服务 → 分配给 开发者
  Task 3: 创建 API 接口 → 分配给 开发者
  Task 4: 编写单元测试 → 分配给 测试员

[执行]
  Task 1 (架构师): 写入 models/user.py ✓
  Task 2 (开发者): 读取 models/user.py，写入 services/user_service.py ✓
  Task 3 (开发者): 写入 api/user_api.py ✓
  Task 4 (测试员): 读取所有文件，写入 tests/test_user.py ✓
```

### 1.6 Pair Programming 模式

```python
from swarm.collaboration_patterns import PairProgramming

pp = PairProgramming(
    driver=driver_agent,    # 编写代码
    navigator=navigator_agent  # 审查代码
)

# 多轮迭代
result = await pp.execute("开发一个功能")

# 流程:
# Round 1: Driver 写初版 → Navigator 审查
# Round 2: Driver 修改 → Navigator 再审
# Round 3: 通过，写入文件
```

### 1.7 智能失败恢复

当工具调用失败时，Agent 会提供智能应对建议：

```python
def _enhance_error_with_suggestions(self, tool_name, arguments, error):
    """增强错误信息，提供智能应对建议"""
    enhanced = f"错误：{error}\n\n"
    enhanced += "⚠️ **重要提示**：不要重复调用同一个工具！\n\n"
    enhanced += "💡 智能应对建议：\n"
    
    if tool_name == "write_file":
        if "permission" in error.lower():
            enhanced += "1. 检查文件权限\n"
            enhanced += "2. 尝试写入其他目录\n"
```

---

## 2. 逐步写入机制

### 2.1 核心问题

**问题：是一次性写入还是逐步写入？**

**答案：是逐步写入的**，但具体取决于任务复杂度和 Agent 的执行方式。

### 2.2 单次 Agent 执行（简单任务）

```python
agent = Agent(llm=llm, tools=[WriteFileTool()], name="Developer")
result = agent.run("创建一个 calculator.py 文件")
```

**执行流程（逐步）**:

```
迭代 1:
  → LLM 思考：需要创建文件
  → 调用 WriteFileTool(file_path="calculator.py", content="...")
  → 写入文件 ✅
  
迭代 2:
  → LLM 看到写入成功
  → 返回结果："已成功创建文件"
```

### 2.3 Swarm 执行（复杂任务）

```python
orchestrator = SwarmOrchestrator(agents=[架构师，开发者，测试员])
result = await orchestrator.solve("开发用户管理系统")
```

**Swarm 的逐步写入流程**:

```
Step 1: 任务分解
  Task 1: 创建 models/user.py (架构师)
  Task 2: 创建 services/user_service.py (开发者)
  Task 3: 创建 api/user_api.py (开发者)
  Task 4: 创建 tests/test_user.py (测试员)

Step 2: 按依赖执行
  
  迭代 1:
    → Task 1 (架构师) 写入 models/user.py ✅
  
  迭代 2:
    → Task 2 (开发者) 读取 models/user.py
    → 写入 services/user_service.py ✅
  
  迭代 3:
    → Task 3 (开发者) 写入 api/user_api.py ✅
  
  迭代 4:
    → Task 4 (测试员) 读取所有文件
    → 写入 tests/test_user.py ✅
```

### 2.4 为什么是逐步写入？

#### Agent 执行机制

```python
# Agent 的 while 循环
while iteration < max_iterations:
    # 每次迭代：
    # 1. 调用 LLM
    # 2. 执行工具（包括 WriteFileTool）
    # 3. 更新记忆
    # 4. 下一次迭代基于新的记忆
```

每次迭代只能执行 LLM 当前返回的工具调用，因此必然是逐步的。

#### 依赖关系

```python
Task(
    id="2",
    description="实现服务层",
    dependencies=["1"]  # ← 依赖 Task 1
)

# TaskGraph 保证顺序
ready_tasks = graph.get_ready_tasks()
# 只有 Task 1 完成后，Task 2 才会出现在 ready_tasks 中
```

### 2.5 当前实现的限制

#### 限制 1：单次迭代的工具调用数量

如果 LLM 一次返回多个 WriteFileTool 调用，会并行写入多个文件。

**影响**: 
- ✅ 对于独立文件没问题
- ⚠️ 对于有依赖的文件，可能导致后写入的文件无法参考先写入的

#### 限制 2：Agent 间的协调

如果没有使用 Swarm，单个 Agent 创建多个相关文件时，可能无法正确处理依赖。

**解决方案**: 使用 Swarm + 任务依赖

### 2.6 最佳实践

#### 使用 Swarm 和任务依赖

```python
from swarm import SwarmOrchestrator
from swarm.scheduler import Task

tasks = [
    Task(id="1", description="创建基础模型"),
    Task(id="2", description="创建服务层", dependencies=["1"]),
    Task(id="3", description="创建 API", dependencies=["2"]),
]

orchestrator._build_task_graph(tasks)
result = await orchestrator._execute_loop("开发用户系统")
```

#### 合理设置 max_iterations

```python
# 太小可能导致文件写不完
agent = Agent(max_iterations=3)  # 可能只够写 1-2 个文件

# 推荐
agent = Agent(max_iterations=20)  # 足够写多个文件
```

---

## 3. 输出目录管理

### 3.1 目录结构

所有生成的文件都保存在 `output/` 目录中，不会污染根目录。

```
simple-agent/
├── output/                    # 所有输出文件的根目录
│   ├── cli/                   # CLI 任务输出
│   │   ├── task_001/          # 按任务 ID 隔离
│   │   ├── task_002/
│   │   └── ...
│   ├── swarm/                 # Swarm 任务输出
│   │   ├── swarm_001/
│   │   └── ...
│   ├── generated/             # 代码生成输出
│   │   ├── project_name/
│   │   └── ...
│   └── reports/               # 报告文件
│       ├── code_review.md
│       └── ...
├── agents/                    # Agent 配置文件
├── workflows/                 # 工作流配置
└── ...                        # 源代码（保持干净）
```

### 3.2 配置说明

**配置文件位置**: `config/settings.yaml`

```yaml
directories:
  # 输出根目录
  output: "${OUTPUT_DIR:./output}"
  
  # 各类型输出
  cli_output: "${CLI_OUTPUT_DIR:./output/cli}"
  swarm_output: "${SWARM_OUTPUT_DIR:./output/swarm}"
  generated_code: "${GENERATED_CODE_DIR:./output/generated}"
  reports: "${REPORTS_DIR:./output/reports}"
```

### 3.3 环境变量覆盖

```bash
# 自定义 CLI 输出目录
export CLI_OUTPUT_DIR="./my_output/cli"

# 自定义 Swarm 输出目录
export SWARM_OUTPUT_DIR="./my_output/swarm"

# 运行
python cli.py "帮我写个函数"
```

### 3.4 使用方式

#### CLI 输出隔离

```bash
python cli.py "帮我写一个计算器"
# 输出保存到：output/cli/task_计算器/
```

#### Swarm 输出

```python
from swarm import SwarmOrchestrator

orchestrator = SwarmOrchestrator(agents=[...])
result = await orchestrator.solve("开发用户管理系统")
# 生成的文件保存到 output/swarm/ 或 output/generated/
```

#### 使用 BashTool 保存输出

```python
from tools.bash_tool import BashTool

bash = BashTool()
# 创建目录并复制文件
bash.execute(command="mkdir -p output/YYYY-MM-DD/project && cp result.txt output/YYYY-MM-DD/project/")
```

### 3.5 Git 忽略

`output/` 目录已添加到 `.gitignore`：

```gitignore
# 输出目录 - 所有生成的文件
output/
*.log
*.tmp
```

### 3.6 清理输出

```bash
# 清理所有输出
rm -rf output/*

# 清理特定日期的输出
rm -rf output/2026-03-07/

# 清理特定项目的输出
rm -rf output/generated/calculator/

# 清理 7 天前的输出
find output/ -type d -mtime +7 -exec rm -rf {} \;
```

### 3.7 最佳实践

#### 项目隔离

```python
# 好：项目隔离
manager.execute(project="project_a", ...)
manager.execute(project="project_b", ...)

# 不好：所有文件混在一起
manager.execute(...)  # 没有指定 project
```

#### 有意义的文件名

```python
# 好：有意义的文件名
manager.execute(filename="user_model", ...)

# 不好：使用默认文件名
manager.execute(...)  # 生成 task_12345.txt
```

---

## 4. 关键组件位置

| 组件 | 位置 | 作用 |
|------|------|------|
| **Agent** | `core/agent.py` | 执行主体，协调 LLM 和工具 |
| **WriteFileTool** | `tools/file.py` | 实际写入文件的工具 |
| **ToolRegistry** | `core/tool.py` | 管理可用工具 |
| **ToolCallParser** | `core/tool_parser.py` | 解析工具调用 |
| **Memory** | `core/memory.py` | 保存对话和工具调用历史 |

---

**文档版本**: 2.0  
**最后更新**: 2026-03-08  
**合并自**: AGENT_CODE_DEVELOPMENT.md, INCREMENTAL_CODE_WRITING.md, OUTPUT_DIRECTORY.md
