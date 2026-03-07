# Simple Agent - 智能任务管理系统

一个基于 AI 的智能任务管理系统，支持单 Agent 执行、Swarm 群体智能协作等多种模式。

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_BASE="https://api.openai.com/v1"
```

### 启动 CLI

```bash
python cli.py
```

## 📚 文档导航

**所有文档都在 [`docs/`](docs/) 目录中**

### 核心文档

| 文档 | 说明 |
|------|------|
| **[docs/README.md](docs/README.md)** | 📖 Swarm 系统文档总索引 |
| **[docs/HOW_TO_USE_SWARM_IN_CLI.md](docs/HOW_TO_USE_SWARM_IN_CLI.md)** | 💬 如何在 CLI 中使用 Swarm |
| **[docs/AGENT_CODE_DEVELOPMENT.md](docs/AGENT_CODE_DEVELOPMENT.md)** | 💻 Agent 代码开发流程详解 |
| **[docs/INCREMENTAL_CODE_WRITING.md](docs/INCREMENTAL_CODE_WRITING.md)** | 📝 逐步写入机制详解 |
| **[docs/OUTPUT_DIRECTORY.md](docs/OUTPUT_DIRECTORY.md)** | 📁 输出目录管理指南 |

### 使用指南

| 文档 | 说明 |
|------|------|
| **[docs/HOW_TO_USE_SWARM.md](docs/HOW_TO_USE_SWARM.md)** | Swarm Python API 使用指南 |
| **[docs/SWARM_USAGE.md](docs/SWARM_USAGE.md)** | Swarm 详细使用指南 |
| **[docs/SWARM_QUICK_REFERENCE.md](docs/SWARM_QUICK_REFERENCE.md)** | 快速参考卡片 |

### 技术文档

| 文档 | 说明 |
|------|------|
| **[docs/SWARM_IMPLEMENTATION_SUMMARY.md](docs/SWARM_IMPLEMENTATION_SUMMARY.md)** | Swarm 实施总结 |
| **[docs/ARCHITECTURE_SUMMARY.md](docs/ARCHITECTURE_SUMMARY.md)** | 架构升级总结 |
| **[docs/ARCHITECTURE_UPGRADE.md](docs/ARCHITECTURE_UPGRADE.md)** | 完整架构升级方案 |
| **[docs/FILE_INDEX.md](docs/FILE_INDEX.md)** | 完整文件索引 |

### 其他文档

| 文档 | 说明 |
|------|------|
| **[docs/DEEP_PROTECTION.md](docs/DEEP_PROTECTION.md)** | 深度保护机制 |
| **[docs/DEEP_PROTECTION_SUMMARY.md](docs/DEEP_PROTECTION_SUMMARY.md)** | 深度保护总结 |
| **[docs/DEVOPS.md](docs/DEVOPS.md)** | DevOps 相关文档 |
| **[docs/ENHANCED_CLI.md](docs/ENHANCED_CLI.md)** | 增强 CLI 功能 |
| **[docs/INTEGRATION_REPORT.md](docs/INTEGRATION_REPORT.md)** | 集成报告 |
| **[docs/QUICKSTART_ENHANCED.md](docs/QUICKSTART_ENHANCED.md)** | 快速开始（增强版） |

## 🎯 核心功能

### 1. CLI 交互模式

```bash
python cli.py
# 直接输入任务，如：
# "帮我写一个计算器"
# "开发一个用户管理系统"
```

### 2. Swarm 群体智能

多个 Agent 协作完成复杂任务：

```python
from swarm import SwarmOrchestrator

orchestrator = SwarmOrchestrator(agents=[...])
result = await orchestrator.solve("开发完整的用户管理系统")
```

### 3. 代码开发

Agent 自动编写代码并保存到 `output/` 目录：

- ✅ 逐步写入机制
- ✅ 任务依赖管理
- ✅ 代码审查循环
- ✅ 结对编程模式

### 4. 输出管理

所有生成的文件都保存到 `output/` 目录：

```
output/
├── cli/           # CLI 任务输出
├── swarm/         # Swarm 任务输出
├── generated/     # 代码生成
└── reports/       # 报告文件
```

## 📁 项目结构

```
simple-agent/
├── README.md                  # 本文件
├── docs/                      # 📚 所有文档
├── core/                      # 核心模块
│   ├── agent.py              # Agent 基类
│   ├── llm.py                # LLM 接口
│   └── ...
├── swarm/                     # 🤖 Swarm 模块
│   ├── orchestrator.py       # Swarm 控制器
│   ├── blackboard.py         # 共享黑板
│   └── ...
├── tools/                     # 🔧 工具集
│   ├── file.py               # 文件操作
│   └── output_manager.py     # 输出管理
├── cli.py                     # CLI 入口
├── config/                    # 配置文件
├── output/                    # 输出目录（自动生成）
└── ...
```

## 🔧 高级配置

### 自定义输出目录

```bash
export CLI_OUTPUT_DIR="./my_output/cli"
export SWARM_OUTPUT_DIR="./my_output/swarm"
export GENERATED_CODE_DIR="./my_output/code"
```

### 验证配置

```bash
python scripts/verify_output_dirs.py
```

## 🧪 测试

```bash
# 运行所有 Swarm 测试
python scripts/run_all_tests.py

# 单独运行测试
python tests/test_swarm.py
python tests/test_swarm_stage2.py
python tests/test_scaling.py
```

## 🎓 学习路径

### 新手入门

1. 阅读 [HOW_TO_USE_SWARM_IN_CLI.md](docs/HOW_TO_USE_SWARM_IN_CLI.md)
2. 运行 `python cli.py` 体验
3. 查看 [SWARM_QUICK_REFERENCE.md](docs/SWARM_QUICK_REFERENCE.md)

### 深入学习

1. 阅读 [AGENT_CODE_DEVELOPMENT.md](docs/AGENT_CODE_DEVELOPMENT.md)
2. 学习 [SWARM_USAGE.md](docs/SWARM_USAGE.md)
3. 研究 [INCREMENTAL_CODE_WRITING.md](docs/INCREMENTAL_CODE_WRITING.md)

### 掌握架构

1. 阅读 [ARCHITECTURE_UPGRADE.md](docs/ARCHITECTURE_UPGRADE.md)
2. 查看 [ARCHITECTURE_SUMMARY.md](docs/ARCHITECTURE_SUMMARY.md)
3. 参考 [FILE_INDEX.md](docs/FILE_INDEX.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📞 支持

如有问题，请查看：

1. [docs/README.md](docs/README.md) - 文档总索引
2. [docs/SWARM_USAGE.md](docs/SWARM_USAGE.md) - 使用指南
3. [docs/OUTPUT_DIRECTORY.md](docs/OUTPUT_DIRECTORY.md) - 输出管理

---

**开始使用**: `python cli.py`  
**查看所有文档**: [`docs/`](docs/)
