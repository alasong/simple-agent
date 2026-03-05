# Simple Agent

最小 Agent 框架，一句话创建 Agent。

## 安装

```bash
pip install openai gnureadline
```

## 快速开始

```bash
# 设置环境变量
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选

# 一句话创建 Agent
python cli.py "文件管理助手"
```

## CLI 使用

```bash
# 交互模式
python cli.py "文件管理助手"

# 单次任务
python cli.py "文件管理助手" -t "读取 /tmp/test.txt"

# 指定工具标签
python cli.py "代码审查" --tags check,code

# 列出资源
python cli.py --list-tools
python cli.py --list-agents
```

## 交互命令

| 命令 | 说明 |
|------|------|
| `/new <描述>` | 创建新 Agent |
| `/update <描述>` | 更新提示词 |
| `/switch <名称>` | 切换 Agent |
| `/list` | 列出所有 Agent |
| `/info` | 显示全部信息 |
| `/clear` | 清空记忆 |
| `/save <路径>` | 保存 Agent |
| `/exit` | 退出 |

按 **Tab** 键自动补全命令。

## 代码使用

```python
from core import create_agent, update_prompt, get_agent

# 一句话创建
agent = create_agent("文件管理助手")

# 运行任务
result = agent.run("读取 /tmp/test.txt")

# 更新提示词
agent = update_prompt(agent, "更强大的文件助手")

# 获取已创建的 Agent
agent = get_agent("文件管理助手")

# 保存到文件
agent.save("my_agent.json")

# 从文件加载
from core import Agent
agent = Agent.load("my_agent.json")
```

## 架构

```
ResourceRepository (资源仓库)
├── 工具仓库 (导入即注册)
├── LLM 仓库 (环境变量配置)
└── Agent 注册表 (创建时注册)

create_agent(description)
└── 从仓库抽取资源 + 需求 → 新 Agent
```

## 目录结构

```
simple-agent/
├── core/              # 框架核心
│   ├── agent.py       # Agent 实体
│   ├── factory.py     # Agent 创建
│   ├── resource.py    # 资源仓库
│   ├── tool.py        # 工具基类
│   ├── memory.py      # 记忆系统
│   └── llm.py         # LLM 接口
├── tools/             # 工具插件
│   ├── file.py        # 文件读写
│   └── check.py       # 检查验证
├── cli.py             # 命令行入口
├── requirements.txt
└── README.md
```

## 扩展工具

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
                "param": {"type": "string"}
            },
            "required": ["param"]
        }
    
    def execute(self, param: str) -> ToolResult:
        return ToolResult(success=True, output=f"结果: {param}")
```

## 内置工具

| 工具 | 标签 | 说明 |
|------|------|------|
| ReadFileTool | file, io | 读取文件 |
| WriteFileTool | file, io | 写入文件 |
| CheckFileExistsTool | check, review | 检查文件存在 |
| CheckContentTool | check, review, code | 检查内容匹配 |
| CheckPythonSyntaxTool | check, review, code | 检查 Python 语法 |

## Agent 实体

Agent 是可部署的实体，支持：

- **序列化**: `agent.to_json()` / `agent.to_dict()`
- **持久化**: `agent.save(path)` / `Agent.load(path)`
- **独立运行**: 包含完整的 LLM、工具、记忆配置
