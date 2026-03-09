# Simple Agent

多 Agent 协作系统，支持群体智能、任务自动分解、智能调度和多种协作模式。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行 CLI（交互模式）
python cli.py

# 运行 CLI（单次任务）
python cli.py "帮我分析这个项目"
```

## 本地服务化模式

```bash
# 启动 API 服务（后台）
python cli.py --start

# 查看状态
python cli.py --status

# 启动 Web UI
python -m webui.app --port 3000

# 访问 API 文档
# http://localhost:8000/docs
```

## 核心功能

- **多 Agent 协作**: 内置 25+ 专业 Agent（Developer, Reviewer, Tester 等）
- **群体智能**: SwarmOrchestrator 自动分解和调度任务
- **动态调度**: 基于技能和优先级的智能任务分配
- **并行工作流**: 支持并发执行多个任务
- **API 服务**: RESTful API 支持企业集成
- **Web 界面**: 可视化任务管理和监控

## 项目结构

```
simple-agent/
├── cli.py                 # CLI 入口
├── core/                  # 核心模块
│   ├── agent.py           # Agent 基类
│   ├── workflow.py        # 工作流编排
│   ├── dynamic_scheduler.py  # 动态调度器
│   └── api_server.py      # API 服务
├── swarm/                 # 群体智能
│   ├── orchestrator.py    # 编排器
│   ├── scheduler.py       # 调度器
│   └── blackboard.py      # 共享黑板
├── builtin_agents/        # 内置 Agent (25+)
├── webui/                 # Web 界面
├── integrations/          # IM 集成 (飞书/钉钉)
└── tests/                 # 测试
```

## 内置 Agent

| 类别 | Agent |
|------|-------|
| 开发 | developer, architect, reviewer, tester, deployer |
| 产品 | product_manager, documenter, planner |
| AI/ML | ai_researcher, ml_engineer, nlp_engineer, cv_engineer |
| 数据 | data_analyst, data_engineer, quant_analyst |
| 金融 | financial_analyst, trading_strategist, risk_manager |

## 运行测试

```bash
# 快速测试
python -m pytest tests/test_deep_core.py -v

# API 测试
python -m pytest tests/test_api_server.py -v

# 完整测试
python -m pytest tests/ -v
```

## 文档

- [架构文档](docs/ARCHITECTURE.md)
- [Swarm 使用指南](docs/SWARM.md)
- [本地服务化文档](docs/SERVICE.md)
- [内置 Agent 列表](docs/BUILTIN_AGENTS.md)

## 依赖

- Python 3.8+
- FastAPI, Uvicorn (API 服务)
- Pydantic (数据验证)
- NetworkX (图算法)
- Rich (富文本输出)

## License

Apache 2.0
