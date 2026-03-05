# Simple Agent

最小 Agent 框架，一句话创建 Agent。

## 快速开始

```bash
# 安装依赖
pip install openai

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
| `/info` | 显示 Agent 信息 |
| `/prompt` | 查看提示词 |
| `/context` | 查看上下文 |
| `/clear` | 清空记忆 |
| `/exit` | 退出 |

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
├── core/           # 框架核心
│   ├── agent.py    # Agent 类
│   ├── factory.py  # Agent 创建
│   ├── resource.py # 资源仓库
│   ├── tool.py     # 工具基类
│   ├── memory.py   # 记忆系统
│   └── llm.py      # LLM 接口
├── tools/          # 工具插件
├── cli.py          # 命令行入口
└── README.md
```
