# Agent 代码开发流程详解

## 概述

Agent 开发和写入代码的流程分为以下几个步骤：

1. **理解需求** → Agent 通过 LLM 理解用户需求
2. **规划代码** → LLM 生成代码结构和实现方案
3. **调用工具** → 使用 `WriteFileTool` 写入文件
4. **验证结果** → 读取文件或使用其他工具验证

---

## 核心机制

### 1. Agent 执行流程

```
用户输入 → Agent.run() → LLM 推理 → 工具调用 → 写入文件
```

**核心代码位置**: `core/agent.py:317-392`

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
        
        content = response["content"]
        tool_calls = response["tool_calls"]
        
        # 3. 如果没有工具调用，返回结果
        if not tool_calls:
            self.memory.add_assistant(content)
            return content
        
        # 4. 行动：执行所有工具调用
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            arguments = tool_call["arguments"]
            tool_id = tool_call["id"]
            
            # 执行工具（如 WriteFileTool）
            result = self._execute_tool(tool_name, arguments)
            
            # 添加工具结果到记忆
            self.memory.add_tool_result(
                tool_call_id=tool_id,
                name=tool_name,
                content=result.output
            )
    
    return f"达到最大迭代次数 ({self.max_iterations})，任务可能未完成"
```

---

### 2. WriteFileTool 实现

**核心代码位置**: `tools/file.py:45-84`

```python
@tool(tags=["file", "io"], description="写入文件内容")
class WriteFileTool(BaseTool):
    """写文件工具"""
    
    @property
    def name(self) -> str:
        return "write_file"
    
    @property
    def description(self) -> str:
        return "将内容写入指定路径的文件"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要写入的文件路径"
                },
                "content": {
                    "type": "string",
                    "description": "要写入的内容"
                }
            },
            "required": ["file_path", "content"]
        }
    
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

---

### 3. 工具注册和使用

**工具注册**: `core/agent.py:94-100`

```python
# 注册工具
self.tool_registry = ToolRegistry()
self._tool_names: list[str] = []
if tools:
    for tool in tools:
        self.tool_registry.register(tool)
        self._tool_names.append(tool.__class__.__name__)
```

**工具执行**: `core/agent.py:228-233`

```python
def _execute_tool(self, tool_name: str, arguments: dict) -> ToolResult:
    """执行工具"""
    tool = self.tool_registry.get(tool_name)
    if not tool:
        return ToolResult(success=False, output="", error=f"未知工具：{tool_name}")
    return tool.execute(**arguments)
```

---

## 完整流程示例

### 示例 1：单次任务开发代码

```python
from core.agent import Agent
from core.llm import OpenAILLM
from tools.file import WriteFileTool, ReadFileTool

# 1. 创建 Agent
llm = OpenAILLM()
agent = Agent(
    llm=llm,
    tools=[WriteFileTool(), ReadFileTool()],  # 注册文件工具
    name="Developer",
    system_prompt="你是软件开发专家，擅长编写高质量代码"
)

# 2. 执行任务
result = agent.run(
    "帮我创建一个 Python 文件 calculator.py，实现一个计算器类，支持加减乘除",
    verbose=True
)

print(result)
```

**执行流程**:

```
[Agent Developer] 开始执行任务...

迭代 1:
  → LLM 思考：需要创建 calculator.py 文件
  → 调用 WriteFileTool:
    {
      "file_path": "calculator.py",
      "content": "class Calculator:\n    def add(self, a, b):...\n"
    }
  → WriteFileTool.execute() 写入文件
  → 返回：成功写入文件：calculator.py
  → Agent 记忆添加工具结果

迭代 2:
  → LLM 思考：任务已完成
  → 返回最终结果："已成功创建 calculator.py 文件..."

任务完成！
```

---

### 示例 2：Swarm 协作开发

```python
import asyncio
from swarm import SwarmOrchestrator
from core.agent import Agent
from core.llm import get_llm

llm = get_llm()

# 创建多个 Agent
agents = [
    Agent(llm=llm, name="架构师", 
          system_prompt="你是系统架构师，负责设计代码结构"),
    Agent(llm=llm, name="开发者",
          system_prompt="你是开发工程师，负责编写代码"),
    Agent(llm=llm, name="测试员",
          system_prompt="你是测试工程师，负责编写测试"),
]

# 创建 Swarm
orchestrator = SwarmOrchestrator(
    agent_pool=agents,
    llm=llm,
    verbose=True
)

# 执行复杂任务
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
[Swarm] 接收任务：开发用户管理系统

[Swarm] 任务分解:
  Task 1: 设计用户模型 → 分配给 架构师
  Task 2: 实现用户服务 → 分配给 开发者
  Task 3: 创建 API 接口 → 分配给 开发者
  Task 4: 编写单元测试 → 分配给 测试员

[执行循环]
  
  Task 1 (架构师):
    → LLM 设计 User 类
    → 调用 WriteFileTool 写入 models/user.py
    ✓ 完成
  
  Task 2 (开发者):
    → LLM 读取 models/user.py 理解结构
    → 调用 WriteFileTool 写入 services/user_service.py
    ✓ 完成
  
  Task 3 (开发者):
    → LLM 读取 user_service.py
    → 调用 WriteFileTool 写入 api/user_api.py
    ✓ 完成
  
  Task 4 (测试员):
    → LLM 读取所有文件理解结构
    → 调用 WriteFileTool 写入 tests/test_user.py
    ✓ 完成

[Swarm] 所有任务完成！
```

---

## 代码写入的关键组件

### 1. LLM 工具调用格式

LLM 返回的标准工具调用格式：

```json
{
  "content": "我将创建一个计算器文件...",
  "tool_calls": [
    {
      "id": "call_abc123",
      "type": "function",
      "function": {
        "name": "write_file",
        "arguments": {
          "file_path": "calculator.py",
          "content": "class Calculator:\n    ..."
        }
      }
    }
  ]
}
```

### 2. 工具解析器

**代码位置**: `core/tool_parser.py`

```python
class ToolCallParser:
    """从 LLM 返回的 content 中解析工具调用"""
    
    def parse(self, content: str) -> list:
        """
        解析 content 中的工具调用
        支持格式：
        ```tool
        {"name": "write_file", "arguments": {...}}
        ```
        """
        # 解析逻辑...
        return tool_calls
```

### 3. 工具注册表

**代码位置**: `core/tool.py`

```python
class ToolRegistry:
    """工具注册表"""
    
    def register(self, tool: BaseTool):
        """注册工具"""
        self.tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self.tools.get(name)
    
    def get_openai_tools(self) -> list:
        """获取 OpenAI 格式的工具定义"""
        return [tool.to_openai_format() for tool in self.tools.values()]
```

---

## 实际案例分析

### 案例：Pair Programming 模式开发代码

**代码位置**: `swarm/collaboration_patterns.py`

```python
class PairProgramming:
    """结对编程模式"""
    
    def __init__(self, driver: Agent, navigator: Agent):
        self.driver = driver      # 编写代码
        self.navigator = navigator  # 审查代码
    
    async def execute(self, task: str) -> str:
        """执行结对编程"""
        
        # 1. Driver 编写初版代码
        driver_code = await self.driver.run(f"编写代码：{task}")
        
        # 2. Navigator 审查代码
        review = await self.navigator.run(
            f"审查这段代码:\n{driver_code}\n"
            "提出改进建议并重新实现"
        )
        
        # 3. Driver 根据建议改进
        improved_code = await self.driver.run(
            f"根据审查建议改进代码:\n{review}"
        )
        
        # 4. 写入文件
        write_result = await self.driver.run(
            f"将以下代码写入文件 example.py:\n{improved_code}",
            tools=[WriteFileTool()]
        )
        
        return improved_code
```

**执行流程**:

```
[Pair Programming] 任务：实现快速排序

Round 1 - Driver:
  → 编写初版代码
  → 调用 WriteFileTool 写入 quicksort_v1.py
  → 返回代码

Round 1 - Navigator:
  → 读取 quicksort_v1.py
  → 审查代码，发现问题：
    - 缺少类型注解
    - 缺少文档字符串
    - 变量命名不清晰
  → 返回审查意见

Round 2 - Driver:
  → 根据审查意见改进代码
  → 添加类型注解、文档字符串
  → 优化变量命名
  → 调用 WriteFileTool 写入 quicksort_v2.py
  → 返回改进后的代码

Round 2 - Navigator:
  → 审查改进后的代码
  → ✅ 通过审查

[Pair Programming] 完成！
  最终文件：quicksort_v2.py
```

---

## 工具调用的智能失败恢复

**代码位置**: `core/agent.py:235-315`

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
            enhanced += "3. 使用 sudo 或修改权限\n"
        elif "no such file" in error.lower():
            enhanced += "1. 检查目录是否存在\n"
            enhanced += "2. 先创建目录再写入文件\n"
    # ... 更多建议
    
    return enhanced
```

这样，即使工具调用失败，LLM 也能收到建设性的反馈，采取替代方案。

---

## 高级用法

### 1. 自定义工具

创建自定义代码生成工具：

```python
from core.tool import BaseTool, ToolResult, tool

@tool(tags=["code", "generation"], description="生成代码")
class CodeGeneratorTool(BaseTool):
    
    @property
    def name(self) -> str:
        return "generate_code"
    
    @property
    def description(self) -> str:
        return "根据需求生成代码"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "description": "编程语言 (python, javascript, etc.)"
                },
                "requirement": {
                    "type": "string",
                    "description": "代码需求描述"
                },
                "output_path": {
                    "type": "string",
                    "description": "输出文件路径"
                }
            },
            "required": ["language", "requirement"]
        }
    
    def execute(self, language: str, requirement: str, 
                output_path: Optional[str] = None) -> ToolResult:
        # 使用 LLM 生成代码
        llm = OpenAILLM()
        prompt = f"生成{language}代码：{requirement}"
        response = llm.chat([{"role": "user", "content": prompt}])
        code = response["content"]
        
        # 可选：写入文件
        if output_path:
            with open(output_path, 'w') as f:
                f.write(code)
        
        return ToolResult(
            success=True,
            output=code,
            metadata={"file_path": output_path}
        )
```

### 2. 代码验证工具

```python
@tool(tags=["code", "validation"], description="验证代码")
class CodeValidationTool(BaseTool):
    
    @property
    def name(self) -> str:
        return "validate_code"
    
    def execute(self, file_path: str) -> ToolResult:
        # 运行 linter
        import subprocess
        result = subprocess.run(
            ["flake8", file_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return ToolResult(success=True, output="✅ 代码通过检查")
        else:
            return ToolResult(
                success=False,
                output=result.stdout,
                error=result.stderr
            )
```

---

## 调试技巧

### 1. 查看工具调用历史

```python
agent = Agent(llm=llm, tools=[WriteFileTool()])
result = agent.run("创建 test.py 文件")

# 查看记忆中的工具调用
for msg in agent.memory.messages:
    if msg['role'] == 'assistant' and 'tool_calls' in msg:
        print(f"工具调用：{msg['tool_calls']}")
    elif msg['role'] == 'tool':
        print(f"工具结果：{msg['content']}")
```

### 2. 启用详细日志

```python
agent.run("创建文件", verbose=True)
```

输出：
```
[Agent] 调用 LLM...
[Agent] LLM 返回 tool_calls: [...]
[Agent] 执行工具：write_file
[Tool] 写入文件：test.py
[Tool] 成功！
[Agent] 再次调用 LLM...
```

### 3. 检查生成的文件

```python
from tools.file import ReadFileTool

read_tool = ReadFileTool()
result = read_tool.execute(file_path="test.py")
print(result.output)  # 查看文件内容
```

---

## 总结

### Agent 代码开发流程

```
用户输入 
  ↓
Agent.run() 
  ↓
LLM 推理 (理解需求 + 规划代码) 
  ↓
生成工具调用 (WriteFileTool) 
  ↓
执行工具 (写入文件) 
  ↓
验证结果 (可选) 
  ↓
返回最终代码
```

### 关键组件

| 组件 | 位置 | 作用 |
|------|------|------|
| **Agent** | `core/agent.py` | 执行主体，协调 LLM 和工具 |
| **WriteFileTool** | `tools/file.py` | 实际写入文件的工具 |
| **ToolRegistry** | `core/tool.py` | 管理可用工具 |
| **ToolCallParser** | `core/tool_parser.py` | 解析工具调用 |
| **Memory** | `core/memory.py` | 保存对话和工具调用历史 |

### 核心代码片段

**Agent 主循环** (`core/agent.py:317-392`):
```python
def run(self, user_input: str, verbose: bool = True) -> str:
    self.memory.add_user(user_input)
    
    while iteration < self.max_iterations:
        # 1. LLM 推理
        response = self.llm.chat(messages, tools=...)
        
        # 2. 执行工具调用
        for tool_call in tool_calls:
            result = self._execute_tool(tool_call)
            self.memory.add_tool_result(...)
        
        # 3. 没有工具调用时返回
        if not tool_calls:
            return content
```

**WriteFileTool** (`tools/file.py:74-84`):
```python
def execute(self, file_path: str, content: str) -> ToolResult:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return ToolResult(success=True, output=f"成功写入文件：{file_path}")
```

### 最佳实践

1. **明确工具注册**: 创建 Agent 时注册需要的工具
2. **使用详细日志**: `verbose=True` 便于调试
3. **错误处理**: Agent 会自动提供智能应对建议
4. **Swarm 协作**: 复杂任务使用多个 Agent 协作
5. **验证结果**: 使用 ReadFileTool 验证写入的内容

---

## 相关文档

- [如何在 CLI 中使用 Swarm](./HOW_TO_USE_SWARM_IN_CLI.md)
- [Swarm 使用指南](./SWARM_USAGE.md)
- [快速参考](./SWARM_QUICK_REFERENCE.md)
