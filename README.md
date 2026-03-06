# Simple Agent - 智能 Agent 系统

一个灵活的、可扩展的智能 Agent 系统，支持自定义 Agent 创建、工作流自动化和多 Agent 协作。

## 功能特点

- **多 Agent 协作**: 支持多个专业 Agent 协同工作，自动任务分发和协调
- **工作流创建**: 定义 Agent 执行顺序，支持条件分支、循环和错误处理
- **工具扩展**: 丰富的内置工具集，支持自定义工具开发和自动注册
- **会话管理**: 自动保存和恢复会话状态，支持历史会话追踪
- **配置驱动**: 通过 YAML 配置文件管理所有设置
- **环境变量支持**: 灵活的配置管理和动态重载

## 技术架构

### 核心组件

- **核心框架 (core/)**: Agent 基类、Tool 接口、LLM 抽象、会话管理、配置加载器、资源仓库
- **内置 Agents (builtin_agents/)**: CLI、Planner、Developer、Reviewer、Tester Agent
- **工具系统 (tools/)**: 文件操作、Web 搜索、Agent 调用、工作流工具等
- **配置系统 (config/)**: settings.yaml、apis.yaml、Agent 配置文件

### 技术栈

- Python 3.7+
- OpenAI API / 兼容 API
- YAML 配置
- 异步执行支持

## 安装部署

### 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd simple-agent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

或直接安装：

```bash
pip install -e .
```

### API 配置

在使用前配置 API 密钥：

```bash
export OPENAI_API_KEY="your_openai_api_key"
export BING_SEARCH_API_KEY="your_bing_api_key"
```

或者创建 `.env` 文件：

```
OPENAI_API_KEY=your_openai_api_key
BING_SEARCH_API_KEY=your_bing_api_key
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

### settings.yaml 示例

```yaml
directories:
  agents: "./agents"
  workflows: "./workflows"
  output: "./cli_output"
  sessions: "${HOME}/.simple-agent/sessions"

agent:
  max_iterations: 10

llm:
  default_model: "gpt-4o-mini"
  api_base: "https://api.openai.com/v1"
```

### apis.yaml 示例

```yaml
bing_search:
  url: "https://api.bing.microsoft.com/v7.0/search"

google_search:
  url: "https://customsearch.googleapis.com/customsearch/v1"
```

环境变量配置：

- `OPENAI_API_KEY`: OpenAI API 密钥
- `BING_SEARCH_API_KEY`: Bing 搜索 API 密钥
- `OUTPUT_DIR`: 自定义输出目录

## 内置 Agent

### CLI Agent
- 用户交互入口，处理简单问题和任务分发
- 工具：WebSearchTool, GetCurrentDateTool, ExplainReasonTool, SupplementTool

### Planner Agent
- 复杂任务规划、多 Agent 协调、任务分解和分配

### Developer Agent
- 代码开发和实现、代码审查和修改、文档编写

### Reviewer Agent
- 代码质量检查、最佳实践验证、改进建议

### Tester Agent
- 测试用例生成、单元测试编写、集成测试设计

## 工具系统

### 内置工具

- **文件操作**: `ReadFileTool`, `WriteFileTool`
- **检查工具**: `CheckFileExistsTool`, `CheckContentTool`, `CheckPythonSyntaxTool`
- **Agent 工具**: `InvokeAgentTool`, `CreateWorkflowTool`, `ListAgentsTool`
- **搜索工具**: `WebSearchTool`
- **时间工具**: `GetCurrentDateTool`
- **补充工具**: `ExplainReasonTool`, `SupplementTool`
- **输出管理**: `OutputManagerTool`

### 自定义工具

```python
from core import BaseTool, ToolResult

class MyCustomTool(BaseTool):
    @property
    def name(self) -> str:
        return "MyCustomTool"
    
    @property
    def description(self) -> str:
        return "我的自定义工具描述"
    
    @property
    def parameters(self) -> dict:
        return {...}
    
    def execute(self, **kwargs) -> ToolResult:
        # 实现工具逻辑
        return ToolResult(success=True, output="结果")
```

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

会话文件包含：
- 对话历史
- Agent 状态
- 工具使用记录
- 上下文信息

## 输出管理

任务执行结果按日期和项目分类保存在根目录的 `output/` 目录。

### 目录结构

```
output/
├── 2026-03-06/
│   ├── stock_analysis/
│   │   ├── analysis_result.txt
│   │   └── market_report.md
│   └── code_review/
│       └── review_summary.txt
├── 2026-03-07/
│   └── unclassified/
│       └── task_143052.txt
└── 2026-03-08/
    └── research/
        └── findings.json
```

### OutputManagerTool 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project | string | 否 | 项目名称，用于创建子目录 |
| filename | string | 否 | 文件名（不含路径） |
| content | string | 否 | 要保存的内容 |
| file_type | string | 否 | 文件类型：txt/md/json/log，默认 txt |

### 查找输出文件

```bash
# 查看今天的输出
ls output/$(date +%Y-%m-%d)/

# 查找特定项目的输出
find output/ -type d -name "stock_analysis"

# 查找所有 Markdown 文件
find output/ -name "*.md" -type f
```

### 最佳实践

- 为相关任务使用相同的项目名，便于查找
- 使用描述性的文件名
- 根据内容选择合适的文件类型（md/txt/json/log）
- 按日期自动分类便于定期整理和归档

## 最佳实践

1. **Agent 设计**: 每个 Agent 专注于单一职责
2. **工具开发**: 保持工具原子性和可组合性
3. **配置管理**: 使用环境变量管理敏感信息
4. **会话恢复**: 定期保存重要会话状态

## 故障排除

### 常见问题

1. **工具未找到**: 确保工具已正确注册到资源仓库
2. **配置加载失败**: 检查 YAML 文件格式和环境变量
3. **会话保存失败**: 确认存储目录权限和路径

## 扩展性

系统设计具有良好的扩展性：

- **添加 Agent**: 在 `custom_agents/` 创建 YAML 配置
- **开发工具**: 实现 `BaseTool` 接口
- **工作流模板**: 定义复杂执行流程
- **集成服务**: 通过工具调用外部 API

## 注意事项

1. 首次使用需要配置 API 密钥
2. 确保环境变量正确设置
3. 工作流和 Agent 配置保存在本地

## 许可证

MIT License
