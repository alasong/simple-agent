# Simple Agent 文档中心

## 📚 文档概览

Simple Agent 是一个多 Agent 协作系统，支持群体智能、任务自动分解、智能调度和多种协作模式。

---

## 核心文档（5 个）

| 文档 | 说明 |
|------|------|
| **[01-快速开始](./01-QUICKSTART.md)** | 快速入门、安装、基本使用 |
| **[02-架构设计](./02-ARCHITECTURE.md)** | 系统架构、核心组件、设计原理 |
| **[03-使用指南](./03-USER-GUIDE.md)** | Swarm 使用、协作模式、最佳实践 |
| **[04-开发指南](./04-DEVELOPMENT.md)** | 代码开发、调试、测试 |
| **[05-高级功能](./05-ADVANCED.md)** | 自愈系统、反思学习、软件开发支持 |

---

## 快速开始

### 安装

```bash
# 使用虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### 运行 CLI

```bash
# 交互模式
python cli.py

# 单次任务
python cli.py "帮我写一个计算器函数"
```

### 使用 Python API

```python
import asyncio
from simple_agent.swarm import SwarmOrchestrator
from simple_agent.core import create_agent

agents = [
    create_agent("Python 开发专家"),
    create_agent("测试专家"),
]

orchestrator = SwarmOrchestrator(agent_pool=agents)

async def main():
    result = await orchestrator.solve("开发一个 REST API")
    print(f"完成 {result.tasks_completed} 个任务")

asyncio.run(main())
```

---

## 其他文档

### 参考文档
- **[BUILTIN_AGENTS](./BUILTIN_AGENTS.md)** - 26 个内置 Agent 列表
- **[TOOLS](./TOOLS.md)** - 工具使用指南
- **[TESTING](./TESTING.md)** - 测试指南

### 服务化文档
- **[SERVICE](./SERVICE.md)** - 本地服务化、API、守护进程

### 项目信息
- **[ROADMAP](./ROADMAP.md)** - 项目路线图
- **[DIRECTION](./DIRECTION.md)** - 发展方向

---

## 归档文档（历史参考）

以下文档为历史整合文档，内容已整合到核心文档中：

- `reports/` - 各种报告和总结
- `scripts/` - 文档生成脚本

---

**返回**: [项目根目录](../README.md)
