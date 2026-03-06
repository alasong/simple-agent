# Simple Agent - 智能 Agent 系统文档

## 项目概述

Simple Agent 是一个灵活的、可扩展的智能 Agent 系统，支持自定义 Agent 创建、工作流自动化和多 Agent 协作。

## 架构设计

### 核心组件

1. **核心框架 (core/)**
   - `agent.py`: Agent 基类和执行引擎
   - `tool.py`: 工具接口和注册系统
   - `llm.py`: LLM 抽象接口
   - `session.py`: 会话管理
   - `config_loader.py`: 配置加载器
   - `resource.py`: 资源仓库

2. **内置 Agents (builtin_agents/)**
   - CLI Agent: 用户交互入口
   - Planner Agent: 任务规划
   - Developer Agent: 代码开发
   - Reviewer Agent: 代码审查
   - Tester Agent: 测试生成

3. **工具系统 (tools/)**
   - 文件操作工具
   - Web 搜索工具
   - Agent 调用工具
   - 工作流工具
   - 补充说明工具

4. **配置系统 (config/)**
   - `settings.yaml`: 通用设置
   - `apis.yaml`: API 端点配置
   - `builtin_agents/configs/`: Agent 配置

## 功能特性

### 1. 多 Agent 协作
- 支持多个专业 Agent 协同工作
- 自动任务分发和协调
- 结果汇总和整合

### 2. 工作流创建
- 定义 Agent 执行顺序
- 条件分支和循环
- 错误处理和重试

### 3. 工具扩展
- 丰富的内置工具集
- 自定义工具开发
- 工具自动注册

### 4. 会话管理
- 自动保存会话状态
- 历史会话恢复
- 会话导出和导入

### 5. 配置驱动
- YAML 配置文件
- 环境变量支持
- 动态配置重载

## 技术栈

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
# 或
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

## 使用方法

### 命令行使用

```bash
# 启动 CLI Agent
python cli.py

# 或者使用安装后的命令
simple-agent
```

### 创建工作流

```python
from builtin_agents import create_builtin_agent

# 创建 CLI Agent
cli_agent = create_builtin_agent("cli")

# 使用 CreateWorkflowTool 创建工作流
```

### 自定义 Agent

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

## 配置说明

### settings.yaml

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

### apis.yaml

```yaml
bing_search:
  url: "https://api.bing.microsoft.com/v7.0/search"

google_search:
  url: "https://customsearch.googleapis.com/customsearch/v1"
```

## 内置 Agent

### CLI Agent
- 用户交互入口
- 简单问题直接回答
- 复杂任务自动分发
- 工具：WebSearchTool, GetCurrentDateTool, ExplainReasonTool, SupplementTool

### Planner Agent
- 复杂任务规划
- 多 Agent 协调
- 任务分解和分配

### Developer Agent
- 代码开发和实现
- 代码审查和修改
- 文档编写

### Reviewer Agent
- 代码质量检查
- 最佳实践验证
- 改进建议

### Tester Agent
- 测试用例生成
- 单元测试编写
- 集成测试设计

## 工具系统

### 内置工具列表

- **文件操作**: `ReadFileTool`, `WriteFileTool`
- **检查工具**: `CheckFileExistsTool`, `CheckContentTool`, `CheckPythonSyntaxTool`
- **Agent 工具**: `InvokeAgentTool`, `CreateWorkflowTool`, `ListAgentsTool`
- **搜索工具**: `WebSearchTool`
- **时间工具**: `GetCurrentDateTool`
- **补充工具**: `ExplainReasonTool`, `SupplementTool`

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

## 会话管理

会话自动保存到 `~/.simple-agent/sessions/` 目录。

会话文件包含：
- 对话历史
- Agent 状态
- 工具使用记录
- 上下文信息

## 扩展性

系统设计具有良好的扩展性：

- **添加 Agent**: 在 `custom_agents/` 创建 YAML 配置
- **开发工具**: 实现 `BaseTool` 接口
- **工作流模板**: 定义复杂执行流程
- **集成服务**: 通过工具调用外部 API

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

## 许可证

MIT License
