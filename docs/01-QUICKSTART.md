# Simple Agent 快速开始

## 1. 安装

### 1.1 克隆项目

```bash
git clone <repository-url>
cd simple-agent
```

### 1.2 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows
```

### 1.3 安装依赖

```bash
pip install -r requirements.txt
```

---

## 2. 配置

### 2.1 配置 LLM API

创建或编辑 `configs/config.yaml`：

```yaml
llm:
  api_key: "your-api-key"
  model: "gpt-4"
  base_url: "https://api.openai.com/v1"
```

---

## 3. 使用 CLI

### 3.1 启动交互模式

```bash
python cli.py
```

启动后：
```
============================================================
CLI Agent - 智能任务助手
============================================================

输出目录：./output/cli
命令：/help | /exit | /list | /load | /workflow ...

[CLI Agent | default] 你：
```

### 3.2 常用命令

```bash
# 查看帮助
/help

# 退出
/exit

# 列出 Agent
/list

# 加载 Agent
/load developer

# 调试模式
/debug on
/debug summary
/debug stats

# 会话管理
/sessions
/session new <名称>
/session <名称>

# 守护进程
/start    # 启动 API 服务
/stop     # 停止服务
/status   # 查看状态
/logs     # 查看日志
```

### 3.3 单次任务模式

```bash
# 简单任务
python cli.py "帮我写一个 Python 函数，计算两个数的和"

# 带输出目录
python cli.py "分析这个项目的代码结构" -o ./output/analysis

# 调试模式
python cli.py "任务描述" --debug
```

---

## 4. 使用 Python API

### 4.1 基本 Agent

```python
from simple_agent.core import Agent, OpenAILLM, create_agent

# 方式 1：使用 create_agent
agent = create_agent("你是一个 Python 开发专家")
result = agent.run("帮我写一个排序函数")

# 方式 2：手动创建
llm = OpenAILLM()
agent = Agent(
    llm=llm,
    name="Developer",
    system_prompt="你是软件开发专家"
)
result = agent.run("任务描述")
```

### 4.2 Swarm 多 Agent 协作

```python
import asyncio
from simple_agent.swarm import SwarmOrchestrator
from simple_agent.core import create_agent

# 创建 Agent 池
agents = [
    create_agent("Python 开发专家"),
    create_agent("测试专家"),
    create_agent("文档专家"),
]

# 创建编排器
orchestrator = SwarmOrchestrator(
    agent_pool=agents,
    max_iterations=50,
    verbose=True
)

# 执行复杂任务
async def main():
    result = await orchestrator.solve("开发一个完整的用户管理系统")
    print(f"完成 {result.tasks_completed} 个任务")

asyncio.run(main())
```

### 4.3 定义任务依赖

```python
from simple_agent.swarm import SwarmOrchestrator, Task

tasks = [
    Task(id="1", description="设计数据库模型"),
    Task(id="2", description="实现 ORM", dependencies=["1"]),
    Task(id="3", description="创建 API", dependencies=["2"]),
]

orchestrator = SwarmOrchestrator(agent_pool=agents)
orchestrator.task_graph.build_from_tasks(tasks)

result = await orchestrator.solve("开发项目")
```

---

## 5. 输出目录

### 5.1 目录结构

```
simple-agent/
├── output/
│   ├── cli/          # CLI 任务输出
│   ├── swarm/        # Swarm 任务输出
│   └── generated/    # 生成的代码
├── configs/          # 配置文件
├── docs/             # 文档
└── ...
```

### 5.2 配置输出目录

```yaml
# configs/config.yaml
directories:
  output_root: "./output"
  cli_output: "./output/cli"
  swarm_output: "./output/swarm"
```

---

## 6. 下一步

- **[02-ARCHITECTURE.md](./02-ARCHITECTURE.md)** - 了解系统架构
- **[03-USER-GUIDE.md](./03-USER-GUIDE.md)** - 深入学习 Swarm 使用
- **[04-DEVELOPMENT.md](./04-DEVELOPMENT.md)** - 开发和调试指南
- **[05-ADVANCED.md](./05-ADVANCED.md)** - 高级功能

---

## 7. 常见问题

### Q: 如何查看 API 调用情况？
A: 使用 `/debug stats` 查看详细统计。

### Q: 任务执行失败怎么办？
A: 使用 `/debug on` 启用详细日志，查看具体错误。

### Q: 如何保存 Agent 配置？
A: 使用 `/save` 命令保存当前 Agent。

### Q: 如何切换会话？
A: 使用 `/session <名称>` 切换，或 `/session new <名称>` 创建新会话。
