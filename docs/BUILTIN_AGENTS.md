# 内置 Agent (Built-in Agents)

Simple Agent 系统内置了 25 个专业 Agent，覆盖软件开发、数据分析、金融投资等多个领域。

## Agent 列表

### 核心开发 (5 个)

| Agent | 配置 | 工具 | 领域 |
|-------|------|------|------|
| **开发工程师** | `developer.yaml` | ReadFileTool, WriteFileTool, BashTool | software_engineering, programming |
| **架构师** | `architect.yaml` | ReadFileTool, WriteFileTool, WebSearchTool | software_engineering, system_design |
| **测试工程师** | `tester.yaml` | ReadFileTool, WriteFileTool, BashTool | software_engineering, quality_assurance |
| **部署工程师** | `deployer.yaml` | ReadFileTool, WriteFileTool, BashTool | software_engineering, devops |
| **代码审查员** | `reviewer.yaml` | ReadFileTool, WriteFileTool | software_engineering, code_review |

### 产品与设计 (2 个)

| Agent | 配置 | 工具 | 领域 |
|-------|------|------|------|
| **产品经理** | `product_manager.yaml` | ReadFileTool, WriteFileTool, WebSearchTool | product_management, requirement_analysis, user_experience |
| **文档工程师** | `documenter.yaml` | ReadFileTool, WriteFileTool | software_engineering, technical_writing |

### AI 与机器学习 (6 个)

| Agent | 配置 | 工具 | 领域 |
|-------|------|------|------|
| **AI 研究员** | `ai_researcher.yaml` | ReadFileTool, WriteFileTool, WebSearchTool | artificial_intelligence, research |
| **机器学习工程师** | `ml_engineer.yaml` | ReadFileTool, WriteFileTool, BashTool | machine_learning, deep_learning |
| **MLOps 工程师** | `mlops_engineer.yaml` | ReadFileTool, WriteFileTool, BashTool | machine_learning, devops |
| **计算机视觉工程师** | `cv_engineer.yaml` | ReadFileTool, WriteFileTool, BashTool | computer_vision, deep_learning |
| **自然语言处理工程师** | `nlp_engineer.yaml` | ReadFileTool, WriteFileTool, BashTool | natural_language_processing, deep_learning |
| **提示词工程师** | `prompt_engineer.yaml` | ReadFileTool, WriteFileTool | prompt_engineering, llm |

### 数据与量化 (6 个)

| Agent | 配置 | 工具 | 领域 |
|-------|------|------|------|
| **数据分析师** | `data_analyst.yaml` | ReadFileTool, WriteFileTool, BashTool | data_science, analytics |
| **数据工程师** | `data_engineer.yaml` | ReadFileTool, WriteFileTool, BashTool | data_engineering, big_data |
| **量化分析师** | `quant_analyst.yaml` | ReadFileTool, WriteFileTool, BashTool | quantitative_finance, algorithmic_trading |
| **金融分析师** | `financial_analyst.yaml` | ReadFileTool, WriteFileTool, WebSearchTool | finance, investment_analysis |
| **信用分析师** | `credit_analyst.yaml` | ReadFileTool, WriteFileTool | credit_risk, financial_analysis |
| **投资顾问** | `investment_advisor.yaml` | ReadFileTool, WriteFileTool, WebSearchTool | investment, wealth_management |

### 交易与风险 (4 个)

| Agent | 配置 | 工具 | 领域 |
|-------|------|------|------|
| **交易策略师** | `trading_strategist.yaml` | ReadFileTool, WriteFileTool, BashTool | algorithmic_trading, quantitative_finance |
| **风险管理师** | `risk_manager.yaml` | ReadFileTool, WriteFileTool | risk_management, financial_analysis |
| **合规官** | `compliance_officer.yaml` | ReadFileTool, WriteFileTool, WebSearchTool | regulatory_compliance, risk_management |
| **任务规划师** | `planner.yaml` | InvokeAgentTool, CreateWorkflowTool, ListAgentsTool, WebSearchTool, BashTool | task_planning, project_management |

### 新增专家 (4 个) ✨

| Agent | 配置 | 工具 | 领域 |
|-------|------|------|------|
| **安全专家** | `security_agent.yaml` | ReadFileTool, WriteFileTool, BashTool | security_engineering, vulnerability_analysis |
| **性能优化专家** | `performance_agent.yaml` | ReadFileTool, WriteFileTool, BashTool | performance_optimization, system_tuning |

### CLI 专用 (1 个)

| Agent | 配置 | 工具 | 领域 |
|-------|------|------|------|
| **CLI Agent** | `cli.yaml` | ReadFileTool, WriteFileTool, BashTool | cli, automation |

## 工具说明

| 工具 | 功能 |
|------|------|
| `ReadFileTool` | 读取文件内容 |
| `WriteFileTool` | 写入/创建文件 |
| `BashTool` | 执行 shell 命令（环境安装、文件操作、运行程序） |
| `WebSearchTool` | 网络搜索 |
| `InvokeAgentTool` | 调用其他 Agent |
| `CreateWorkflowTool` | 创建工作流 |
| `ListAgentsTool` | 列出可用 Agent |

**设计理念**：
- 最小化工具集：只做 bash 做不到的事
- 环境优先：优先使用系统已有命令
- BashTool 可替代旧文档中的 `RunCommandTool`、`CheckPythonSyntaxTool`、`CheckFileExistsTool` 等

## Agent 配置格式

每个 Agent 配置文件包含以下字段：

```yaml
name: Agent 名称
version: 版本号
description: 简短描述
system_prompt: |
  详细的系统提示词，包含：
  - 专业领域
  - 核心能力
  - 工作方法
  - 交付标准
tools:
  - 工具 1
  - 工具 2
max_iterations: 15
domains:
  - 领域 1
  - 领域 2
```

## 使用方式

在 Swarm 编排器中使用内置 Agent：

```python
from swarm.orchestrator import SwarmOrchestrator
from builtin_agents import load_agents

# 加载所有内置 Agent
agents = load_agents('builtin_agents/configs/')

# 或者加载指定 Agent
agents = load_agents('builtin_agents/configs/', select=['developer', 'tester', 'architect'])

# 创建编排器
swarm = SwarmOrchestrator(
    agent_pool=agents,
    llm=llm,
    use_v2_scheduler=True
)

# 执行任务
result = await swarm.solve("开发一个 Web 应用")
```

## 领域分类

- `software_engineering` - 软件工程
- `system_design` - 系统设计
- `quality_assurance` - 质量保证
- `devops` - 开发运维
- `product_management` - 产品管理
- `artificial_intelligence` - 人工智能
- `machine_learning` - 机器学习
- `data_science` - 数据科学
- `quantitative_finance` - 量化金融
- `security_engineering` - 安全工程
