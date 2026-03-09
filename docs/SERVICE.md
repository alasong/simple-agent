# Simple Agent 本地服务化文档

本文档描述了 Simple Agent 从 CLI 工具升级为本地服务化平台的功能和使用方法。

---

## 目录

1. [概述](#1-概述)
2. [Phase 1: API 网关](#2-phase-1-api-网关)
3. [Phase 2: 守护进程模式](#3-phase-2-守护进程模式)
4. [Phase 3: Web UI](#4-phase-3-web-ui)
5. [Phase 4: IM 集成](#5-phase-4-im-集成可选)
6. [API 参考](#6-api-参考)
7. [常见问题](#7-常见问题)

---

## 1. 概述

Simple Agent 本地服务化平台提供以下能力：

- **HTTP API**: 将 Agent 和 Workflow 封装为 RESTful API
- **守护进程**: 后台运行，支持 start/stop/status
- **Web 界面**: 浏览器可视化操作
- **IM 集成**: 飞书/钉钉/Telegram 机器人（可选）

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面层                            │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐           │
│  │  Web UI   │  │   CLI     │  │ IM Bot    │           │
│  │  (React)  │  │ (Bash)    │  │ (Feishu)  │           │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘           │
│        │              │              │                   │
│        └──────────────┼──────────────┘                   │
│                       │                                   │
│        ┌──────────────▼──────────────┐                   │
│        │      API Gateway (FastAPI)  │                   │
│        │   认证 | 限流 | 路由 | 追踪   │                   │
│        └──────────────┬──────────────┘                   │
└───────────────────────┼─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   核心功能层                             │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐           │
│  │  Agent    │  │ Workflow  │  │  Swarm    │           │
│  │  Engine   │  │  Engine   │  │  Engine   │           │
│  └───────────┘  └───────────┘  └───────────┘           │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Phase 1: API 网关

### 2.1 启动 API 服务

```bash
# 直接启动
python -m core.api_server --port 8000

# 后台运行
python cli.py --start

# 查看状态
python cli.py --status

# 查看日志
python cli.py --logs 100
```

### 2.2 API 文档

访问 http://localhost:8000/docs 查看 Swagger 文档。

### 2.3 首次启动

首次启动时会自动生成默认 API Key：

```
[提示] 未检测到 API Key，已生成默认 Key:
  API Key: sk-xxxxxxxxxxxxxxxxxxxx
  请保存此 Key，刷新页面后将无法再次查看
```

### 2.4 使用示例

```bash
# 运行 Agent
curl -X POST "http://localhost:8000/api/v1/agent/run?X-API-Key=sk-xxx" \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "developer", "input": "分析当前目录"}'

# 查询任务状态
curl "http://localhost:8000/api/v1/task/{task_id}/status?X-API-Key=sk-xxx"

# 获取系统指标
curl "http://localhost:8000/api/v1/metrics?X-API-Key=sk-xxx"
```

---

## 3. Phase 2: 守护进程模式

### 3.1 命令列表

| 命令 | 说明 |
|------|------|
| `cli.py --start` | 启动守护进程 |
| `cli.py --stop` | 停止守护进程 |
| `cli.py --restart` | 重启守护进程 |
| `cli.py --status` | 查看状态 |
| `cli.py --logs [行数]` | 查看日志 |
| `cli.py --install-service` | 生成 systemd/launchd 配置 |

### 3.2 系统服务集成

#### Linux (systemd)

```bash
# 生成服务配置
python cli.py --install-service

# 安装服务
sudo tee /etc/systemd/system/simple-agent.service << 'EOF'
[Unit]
Description=Simple Agent API Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/simple-agent
ExecStart=/path/to/venv/bin/python -m core.api_server --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable simple-agent
sudo systemctl start simple-agent

# 查看状态
sudo systemctl status simple-agent
```

#### macOS (launchd)

```bash
# 生成配置
python cli.py --install-service

# 安装服务
mkdir -p ~/Library/LaunchAgents
# 保存生成的 plist 到 ~/Library/LaunchAgents/simple-agent.plist
launchctl load -w ~/Library/LaunchAgents/simple-agent.plist
```

---

## 4. Phase 3: Web UI

### 4.1 启动 Web UI

```bash
# 启动 Web UI 服务（默认端口 3000）
python -m webui.app --port 3000

# 访问 http://localhost:3000
```

### 4.2 功能

- **任务提交**: 选择 Agent，输入任务描述
- **任务列表**: 查看历史任务
- **实时结果**: 查看任务输出
- **Agent 管理**: 浏览可用 Agent

### 4.3 截图

```
┌─────────────────────────────────────────┐
│  🤖 Simple Agent | 多 Agent 协作平台      │
│                              ● 服务运行中 │
├─────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ │
│ │ 📝 提交任务      │ │ 📋 任务列表      │ │
│ │                 │ │ [刷新] [清空]   │ │
│ │ API Key: [sk-]  │ │                 │ │
│ │ Agent: [下拉]   │ │ 任务 1: 运行中   │ │
│ │ 任务描述：      │ │ 任务 2: 已完成   │ │
│ │ [文本框]        │ │ 任务 3: 已完成   │ │
│ │                 │ │                 │ │
│ │ [🚀 提交任务]   │ │                 │ │
│ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────┤
│ 📤 输出结果                              │
│ ┌─────────────────────────────────────┐ │
│ │ 任务输出将显示在这里...              │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 5. Phase 4: IM 集成（可选）

### 5.1 飞书机器人

```bash
# 启动飞书机器人
python -m integrations.feishu \
  --app-id=cli_xxx \
  --app-secret=xxx \
  --api-key=sk-xxx \
  --port=8080
```

### 5.2 可用命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/status` | 查看系统状态 |
| `/agents` | 列出可用 Agent |
| `/run <任务>` | 运行 Agent 任务 |

### 5.3 配置飞书应用

1. 登录 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 获取 App ID 和 App Secret
4. 配置事件订阅（Webhook 地址）
5. 发布应用

---

## 6. API 参考

### 6.1 健康检查

```http
GET /api/v1/health
```

响应:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600.5,
  "timestamp": "2026-03-09T14:00:00"
}
```

### 6.2 运行 Agent

```http
POST /api/v1/agent/run
Content-Type: application/json
X-API-Key: sk-xxx

{
  "agent_name": "developer",
  "input": "分析当前目录",
  "config": {
    "timeout": 300,
    "debug": true
  }
}
```

响应:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "message": "任务已提交，正在处理中"
}
```

### 6.3 查询任务状态

```http
GET /api/v1/task/{task_id}/status?X-API-Key=sk-xxx
```

响应:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "output": "分析结果...",
  "files": ["output.txt"],
  "created_at": "2026-03-09T14:00:00",
  "completed_at": "2026-03-09T14:01:30",
  "duration": 90.5
}
```

### 6.4 执行 Workflow

```http
POST /api/v1/workflow/execute
Content-Type: application/json
X-API-Key: sk-xxx

{
  "steps": [
    {
      "agent_name": "developer",
      "name": "开发",
      "input_key": "input"
    },
    {
      "agent_name": "reviewer",
      "name": "审查",
      "input_key": "开发"
    }
  ],
  "inputs": {
    "input": "编写一个 Python 函数"
  }
}
```

### 6.5 系统指标

```http
GET /api/v1/metrics?X-API-Key=sk-xxx
```

响应:
```json
{
  "total_tasks": 100,
  "completed_tasks": 95,
  "failed_tasks": 3,
  "success_rate": 0.95,
  "avg_duration": 45.2,
  "total_tokens": 150000,
  "active_agents": 2,
  "uptime": 86400.0
}
```

### 6.6 Agent 列表

```http
GET /api/v1/agent/list?X-API-Key=sk-xxx
```

### 6.7 每日用量

```http
GET /api/v1/usage/daily?days=7&X-API-Key=sk-xxx
```

---

## 7. 常见问题

### Q1: API Key 丢失怎么办？

A: 删除 `core/config/api_keys.json` 文件，重启服务会生成新的默认 Key。

### Q2: 如何修改 API 端口？

A: 使用 `--port` 参数：
```bash
python -m core.api_server --port 9000
```

### Q3: 守护进程启动失败？

A: 查看日志：
```bash
python cli_new.py --logs 100
```

常见原因：
- 端口已被占用
- 虚拟环境未激活
- 依赖未安装

### Q4: Web UI 无法连接 API？

A: 确保 API 服务运行在 8000 端口，或修改 Web UI 中的 API_BASE 配置。

### Q5: 如何启用 CORS？

A: 在 `core/api_server.py` 中修改 `allow_origins` 列表。

---

## 依赖

```txt
# Phase 1-3 核心依赖
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
python-multipart>=0.0.6
websockets>=11.0
aiofiles>=23.0
pydantic>=2.0

# Phase 4 IM 集成（可选）
flask>=2.0.0
requests>=2.25.0
```

---

## 文件结构

```
simple-agent/
├── core/
│   ├── api_models.py       # Pydantic 数据模型
│   ├── api_auth.py         # API Key 认证
│   ├── usage_tracker.py    # 用量追踪
│   ├── api_routes.py       # API 路由
│   ├── api_server.py       # FastAPI 主服务
│   ├── session_store.py    # 会话持久化
│   ├── websocket_server.py # WebSocket 推送
│   └── daemon.py           # 守护进程管理
├── webui/
│   ├── app.py              # Web UI 服务
│   ├── frontend/
│   │   └── index.html      # 前端页面
│   └── __init__.py
├── integrations/
│   ├── feishu.py           # 飞书集成
│   └── __init__.py
├── cli_new.py              # CLI 入口（新增守护进程命令）
└── docs/
    └── SERVICE.md          # 本文档
```

---

**文档版本**: 1.0.0
**最后更新**: 2026-03-09
