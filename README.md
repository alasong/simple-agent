# Simple Agent - 智能 Agent 系统

一个灵活的、可扩展的智能 Agent 系统，支持自定义 Agent 和工作流创建。

## 功能特点

- **多 Agent 协作**: 支持多个专业 Agent 协同工作
- **工作流创建**: 可创建工作流自动化复杂任务
- **工具扩展**: 丰富的工具集，支持自定义工具
- **会话管理**: 自动保存和恢复会话状态
- **配置驱动**: 通过 YAML 配置文件管理所有设置
- **环境变量支持**: 灵活的配置管理

## 技术架构

- **核心框架**: Agent、Tool、LLM 统一抽象接口
- **资源仓库**: 集中管理工具和 Agent 注册
- **配置系统**: YAML 配置 + 环境变量
- **工具系统**: 文件操作、Web 搜索、Agent 调用等
- **会话管理**: 持久化存储和历史追踪

## 安装依赖

```bash
pip install -r requirements.txt
```

或直接安装：

```bash
pip install -e .
```

## 快速开始

### 命令行使用

```bash
# 启动 CLI Agent
python cli.py

# 或者使用命令
simple-agent
```

### 创建工作流

1. 使用 `CreateWorkflowTool` 创建工作流
2. 定义 Agent 执行顺序
3. 保存并执行工作流

### 使用 Agent

```python
from builtin_agents import create_builtin_agent

# 创建 CLI Agent
cli_agent = create_builtin_agent("cli")

# 或者创建 Planner Agent
planner_agent = create_builtin_agent("planner")
```

## 配置说明

所有配置文件位于 `config/` 目录：

- `settings.yaml`: 通用设置（目录、API 密钥等）
- `apis.yaml`: API 端点配置
- `builtin_agents/configs/`: Agent 配置

环境变量配置：

- `OPENAI_API_KEY`: OpenAI API 密钥
- `BING_SEARCH_API_KEY`: Bing 搜索 API 密钥
- 其他配置参见 `config/settings.yaml`

## 内置 Agent

- **CLI Agent**: 用户交互入口，处理简单问题和任务分发
- **Planner Agent**: 复杂任务规划和协调
- **Developer Agent**: 代码开发和实现
- **Reviewer Agent**: 代码审查
- **Tester Agent**: 测试生成

## 工具系统

### 内置工具

- `ReadFileTool` / `WriteFileTool`: 文件读写
- `WebSearchTool`: Web 搜索
- `GetCurrentDateTool`: 获取当前时间
- `InvokeAgentTool`: 调用其他 Agent
- `CreateWorkflowTool`: 创建工作流
- `ListAgentsTool`: 列出可用 Agent
- `ExplainReasonTool`: 解释原因
- `SupplementTool`: 补充说明

### 自定义工具

可以通过实现 `BaseTool` 接口创建自定义工具。

## 自定义 Agent

在 `custom_agents/` 目录创建 YAML 配置文件：

```yaml
name: My Custom Agent
version: 1.0.0
description: 我的自定义 Agent
system_prompt: |
  你是专业的自定义 Agent...
tools:
  - ReadFileTool
  - WebSearchTool
max_iterations: 10
domains:
  - software_engineering
```

## 会话管理

会话自动保存到 `~/.simple-agent/sessions/` 目录。

## 注意事项

1. 首次使用需要配置 API 密钥
2. 确保环境变量正确设置
3. 工作流和 Agent 配置保存在本地

## 扩展性

系统设计具有良好的扩展性：

- 添加新的自定义 Agent
- 开发专用工具
- 创建工作流模板
- 集成外部服务

## 许可证

MIT License
