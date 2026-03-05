# Simple Agent

最小 Agent 框架，支持单 Agent 和多 Agent 工作流协作。

## 安装

```bash
pip install openai gnureadline
```

## 环境变量

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选
```

## 快速开始

### 单 Agent 模式

```bash
python agent_cli.py "文件管理助手"
```

### 多 Agent 工作流模式

```bash
python workflow_cli.py "代码审查流程"
```

---

## CLI 工具

### Agent CLI (单智能体)

```bash
# 交互模式
python agent_cli.py "文件管理助手"

# 单次任务
python agent_cli.py "文件管理助手" -t "读取 /tmp/test.txt"

# 指定工具标签
python agent_cli.py "代码审查" --tags check,code

# 列出工具仓库
python agent_cli.py --list-tools
```

#### 交互命令

| 命令 | 说明 |
|------|------|
| `/new <描述>` | 创建新 Agent |
| `/update <描述>` | 更新提示词 |
| `/switch <名称>` | 切换 Agent |
| `/list` | 列出所有 Agent |
| `/info` | 显示 Agent 信息（提示词、工具、LLM、上下文） |
| `/clear` | 清空记忆 |
| `/save` | 保存 Agent 到 `./agents/` |
| `/load <名称>` | 从 `./agents/` 加载 Agent |
| `/exit` | 退出 |

**Tab 补全**: 支持命令和文件名自动补全。

### Workflow CLI (多 Agent 协作)

```bash
# 交互模式
python workflow_cli.py "代码审查流程"

# 生成并运行任务
python workflow_cli.py "代码审查流程" -t "检查 /tmp/code.py"
```

#### 交互命令

| 命令 | 说明 |
|------|------|
| `/new <描述>` | 创建新 Workflow |
| `/list` | 列出所有 Workflow |
| `/info` | 显示 Workflow 信息（步骤、Agent） |
| `/agents` | 列出所有 Agent |
| `/save` | 保存 Workflow 到 `./workflows/` |
| `/load <名称>` | 从 `./workflows/` 加载 Workflow（包含完整 Agent 实例） |
| `/exit` | 退出 |

**Tab 补全**: 支持命令和文件名自动补全。

#### 调试功能

在任务后添加 `--debug` 参数，将各步骤结果保存到文件：

```bash
# 交互模式
> 检查 /tmp/code.py --debug

# 命令行
python workflow_cli.py "代码审查流程" -t "检查 /tmp/code.py" --debug
python workflow_cli.py "代码审查流程" -t "检查 /tmp/code.py" -o "./debug_output"
```

输出目录结构：
```
./workflow_debug/
├── 00_initial_input.txt          # 初始输入
├── 01_步骤名_output.txt          # 步骤 1 结果
├── 02_步骤名_output.txt          # 步骤 2 结果
└── files/                        # 生成的文件（如有）
```

---

## 代码使用

### 单 Agent

```python
from core import create_agent, update_prompt, get_agent

# 一句话创建（自动推断工具）
agent = create_agent("文件管理助手")

# 运行任务
result = agent.run("读取 /tmp/test.txt")

# 更新提示词
agent = update_prompt(agent, "更强大的文件助手")

# 获取已创建的 Agent
agent = get_agent("文件管理助手")

# 保存/加载
agent.save("./agents/my_agent.json")
from core import Agent
agent = Agent.load("./agents/my_agent.json")
```

### 多 Agent 工作流

```python
from core import generate_workflow, create_workflow, create_agent

# 自动生成工作流
workflow = generate_workflow("代码审查流程：读取文件 → 检查语法 → 生成报告")

# 运行工作流
result = workflow.run("检查 /tmp/code.py")

# 调试模式：保存各步骤结果到文件
result = workflow.run("检查 /tmp/code.py", output_dir="./debug_output")

# 手动创建工作流
read_agent = create_agent("读取文件", tags=["file"])
check_agent = create_agent("检查语法", tags=["check", "code"])
report_agent = create_agent("生成报告", tags=["file"])

workflow = create_workflow(
    name="代码审查",
    steps=[
        {"name": "读取", "agent": read_agent, "output_key": "content"},
        {"name": "检查", "agent": check_agent, "input_key": "content"},
        {"name": "报告", "agent": report_agent},
    ]
)

result = workflow.run("检查 /tmp/code.py")

# 保存/加载
workflow.save("./workflows/review.json")
from core import Workflow
workflow = Workflow.load("./workflows/review.json")
```

---

## 工作流特性

### 上下文共享机制

工作流中所有 Agent 共享上下文：

1. **初始任务**: 保存到 `_initial_input`
2. **步骤结果**: 每步结果保存到 `_last_output` 和指定 `output_key`
3. **上下文传递**: 下一步可以看到之前所有步骤的结果

```python
workflow = Workflow("示例流程", shared_memory=True)
workflow.add_step("步骤 1", agent1, output_key="step1_result")
workflow.add_step("步骤 2", agent2, input_key="step1_result")

# 步骤 2 的 Agent 会收到：
# - 初始任务
# - 步骤 1 的结果摘要
# - 当前任务
```

### StepResult 类型

每步执行结果自动解析为：

| 类型 | 说明 | 检测方式 |
|------|------|----------|
| `TEXT` | 文本字符串 | 默认 |
| `FILE` | 单个文件路径 | 检测到文件路径 |
| `FILES` | 多个文件 | 检测到多个文件路径 |
| `JSON` | 结构化数据 | 检测到 ```json 代码块 |

```python
# 获取结果
context = workflow.run("任务")
last_output = context["_last_output"]
step_result = context["_step_results"]["步骤名称"]

# 获取生成的文件
files = workflow.get_all_files()
```

---

## 架构设计

```
ResourceRepository (资源仓库)
├── ToolRepository   # 工具仓库（导入即注册）
├── LLMRepository    # LLM 仓库（环境变量配置）
└── AgentRegistry    # Agent 注册表

create_agent(description)
└── 从仓库抽取资源 + 需求 → 新 Agent
```

### 目录结构

```
simple-agent/
├── core/              # 框架核心
│   ├── agent.py       # Agent 实体（序列化、运行）
│   ├── factory.py     # Agent 创建工厂
│   ├── resource.py    # 资源仓库
│   ├── workflow.py    # 多 Agent 工作流
│   ├── tool.py        # 工具基类
│   ├── memory.py      # 记忆系统
│   └── llm.py         # LLM 接口
├── tools/             # 工具插件
│   ├── file.py        # 文件操作工具
│   └── check.py       # 检查验证工具
├── agent_cli.py       # 单 Agent CLI
├── workflow_cli.py    # 多 Agent CLI
├── requirements.txt
└── README.md
```

---

## 扩展工具

### 方式 1: 使用装饰器

```python
from core import BaseTool, ToolResult, tool

@tool(tags=["custom"])
class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "工具描述"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "参数说明"}
            },
            "required": ["param"]
        }
    
    def execute(self, param: str) -> ToolResult:
        return ToolResult(success=True, output=f"结果：{param}")
```

### 方式 2: 继承基类

```python
from core import BaseTool, ToolResult

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "工具描述"
    
    @property
    def parameters(self) -> dict:
        return {...}
    
    def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, output="结果")
```

### 工具标签

工具通过标签分类，创建 Agent 时自动匹配：

| 标签 | 用途 |
|------|------|
| `file` | 文件操作 |
| `io` | 输入输出 |
| `check` | 检查验证 |
| `review` | 代码审查 |
| `code` | 代码相关 |

---

## 内置工具

| 工具 | 标签 | 说明 |
|------|------|------|
| `ReadFileTool` | file, io | 读取文件内容 |
| `WriteFileTool` | file, io | 写入文件 |
| `CheckFileExistsTool` | check, review | 检查文件是否存在 |
| `CheckContentTool` | check, review, code | 检查内容匹配 |
| `CheckPythonSyntaxTool` | check, review, code | 检查 Python 语法 |

---

## Agent 实体

Agent 是可部署的实体，支持：

- **序列化**: `agent.to_json()` / `agent.to_dict()`
- **持久化**: `agent.save(path)` / `Agent.load(path)`
- **独立运行**: 包含完整的 LLM、工具、记忆配置
- **版本管理**: `agent.version` 记录创建/更新时间

---

## Workflow 实体

Workflow 是多 Agent 协作流程，支持：

- **序列化**: `workflow.to_json()` / `workflow.to_dict()` (包含完整 Agent 定义)
- **持久化**: `workflow.save(path)` / `Workflow.load(path)` (重建所有 Agent)
- **共享上下文**: 步骤间共享执行上下文
- **自动解析**: 自动检测结果类型（文本/文件/JSON）
