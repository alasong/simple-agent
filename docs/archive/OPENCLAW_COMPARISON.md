# simple-agent vs OpenClaw 架构对比分析

## 项目概览

| 维度 | simple-agent | OpenClaw |
|------|-------------|----------|
| **定位** | 最小化多 Agent 协作框架 | 个人 AI 助手平台 |
| **语言** | Python | TypeScript/Node.js |
| **代码规模** | ~25 个核心文件 | 150+ 文件 (packages + extensions) |
| **Star 数** | - | 280K+ |
| **许可** | MIT | MIT |
| **官网** | - | https://openclaw.ai |

---

## 架构对比

### 1. 核心架构模式

#### simple-agent
```
┌─────────────────────────────────────────┐
│              用户界面层                  │
│         CLI Agent / Coordinator         │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│           协作编排层                     │
│  SwarmOrchestrator │ TaskScheduler      │
│  Blackboard        │ MessageBus         │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│           核心功能层                     │
│  Agent │ DynamicScheduler │ Workflow    │
│  TaskDecomposer │ DependencyGraph       │
└─────────────────────────────────────────┘
```

#### OpenClaw
```
┌─────────────────────────────────────────────────────────┐
│                    客户端层                              │
│  CLI │ WebChat │ macOS App │ iOS/Android Nodes         │
└─────────────────────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────────────────────┐
│                 Gateway (控制平面)                       │
│  WebSocket 控制面 │ Sessions │ Channels │ Tools │ Cron  │
│  支持渠道：WhatsApp/Telegram/Slack/Discord/Signal 等 25+ │
└─────────────────────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────────────────────┐
│                 Pi Agent 运行时                          │
│  RPC 模式 │ 工具流 │ 块流 │ 多 Agent 路由                 │
└─────────────────────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────────────────────┐
│                 扩展层 (Extensions)                      │
│  channels/ │ tools/ │ nodes/ │ platforms/              │
└─────────────────────────────────────────────────────────┘
```

---

### 2. 工具系统设计

| 维度 | simple-agent | OpenClaw |
|------|-------------|----------|
| **哲学** | 极简主义 - 仅保留 bash 无法实现的功能 | 丰富功能 - 封装一切能力 |
| **核心工具数** | 11 个 | 100+ (Browser/Canvas/Nodes/Sessions 等) |
| **工具注册** | ResourceRepository 单例 | 插件化技能系统 (ClawHub) |
| **安全检查** | BashTool 三级检查机制 | DM 配对策略 + 权限控制 |
| **扩展方式** | 装饰器注册 | MCP 桥接 (mcporter) + 插件 API |

#### simple-agent 工具列表
```python
- BashTool (带三级安全检查)
- WebSearchTool
- WebFetchTool
- FileReadTool
- FileWriteTool
- GlobTool
- GrepTool
- AgentSpawnTool
- KnowledgeTool
- LLMTool
- WorkflowTool
```

#### OpenClaw 核心工具
```typescript
- browser.* (浏览器控制)
- canvas.* (A2UI 视觉工作区)
- camera.*, screen.record (设备能力)
- location.get (位置服务)
- system.run, system.notify (macOS 本地)
- sessions_*, channels_* (会话/渠道管理)
- 25+ 渠道集成 (WhatsApp/Telegram/Slack 等)
```

---

### 3. Agent 设计

| 维度 | simple-agent | OpenClaw |
|------|-------------|----------|
| **实现** | 单一类 (~350 行) | 分布式运行时 |
| **序列化** | JSON 文件持久化 | Session 模型 (内存 + 剪枝) |
| **克隆** | clone() 方法 | sessions_* 工具跨会话协调 |
| **多 Agent** | SwarmOrchestrator 群体智能 | Pi Agent + 会话隔离 + 路由 |
| **策略模式** | Direct/PlanReflect/TreeOfThought | Thinking Level (off/minimal/high/xhigh) |

#### simple-agent Agent 使用
```python
agent = Agent(
    llm=llm,
    tools=[BashTool(), WebSearchTool()],
    system_prompt="你是一个助手",
    name="Assistant"
)
result = agent.run("任务描述")

# 克隆
agent2 = agent.clone(new_instance_id="copy-1")

# 序列化
agent.save("agent.json")
agent = Agent.load("agent.json")
```

#### OpenClaw Agent 使用
```typescript
// Gateway 配置
{
  "agent": {
    "model": "gpt-4o",
    "thinking": "high",
    "verbose": true
  },
  "channels": {
    "telegram": { "token": "..." },
    "discord": { "clientId": "..." }
  }
}

// CLI 调用
openclaw agent --message "任务描述" --thinking high
```

---

### 4. 依赖管理

| 维度 | simple-agent | OpenClaw |
|------|-------------|----------|
| **模式** | ResourceRepository 单例 | 依赖注入 + 插件系统 |
| **删除组件** | DIContainer (功能重复) | - |
| **服务定位** | repo.get_tool(), repo.get_llm() | MCP 桥接 (mcporter) |
| **懒加载** | SwarmOrchestrator 组件延迟初始化 | Gateway 动态加载扩展 |

---

### 5. 渠道/通信集成

| 维度 | simple-agent | OpenClaw |
|------|-------------|----------|
| **支持渠道** | CLI 为主 | 25+ 渠道 |
| **渠道列表** | - | WhatsApp/Telegram/Slack/Discord/Google Chat/Signal/iMessage/BlueBubbles/IRC/Microsoft Teams/Matrix/Feishu/LINE/Mattermost/Nextcloud Talk/Nostr/Synology Chat/Tlon/Twitch/Zalo/Zalo Personal/WebChat |
| **DM 安全** | - | dmPolicy="pairing" (配对码机制) |
| **群组路由** | - | Mention 门禁 + 回复标签 + 分片路由 |

---

### 6. 部署与运行

| 维度 | simple-agent | OpenClaw |
|------|-------------|----------|
| **运行模式** | CLI 交互/脚本 | Gateway 守护进程 + 客户端 |
| **部署要求** | Python 虚拟环境 | Node.js ≥22 |
| **安装方式** | git clone + venv | npm/pnpm install -g |
| **配置** | 环境变量 + 代码配置 | YAML 配置 + CLI wizard |
| **远程访问** | - | Tailscale Serve/Funnel + SSH 隧道 |
| ** companion apps** | - | macOS 菜单 App / iOS / Android |

---

### 7. 安全设计

| 维度 | simple-agent | OpenClaw |
|------|-------------|----------|
| **DM 安全** | - | pairing 策略 (未知发送者配对码) |
| **命令安全** | BashTool 三级检查 | system.run TCC 权限控制 |
| **权限管理** | - | macOS TCC + elevated bash 分离 |
| **会话隔离** | instance_id | 会话模型 + 群组隔离 |
| **安全文档** | - | SECURITY.md + doctor 检查 |

---

### 8. 扩展性

| 维度 | simple-agent | OpenClaw |
|------|-------------|----------|
| **扩展模式** | 装饰器注册工具 | 插件系统 (npm 包) |
| **技能市场** | - | ClawHub (clawhub.ai) |
| **MCP 支持** | - | mcporter 桥接 |
| **内置技能** | 25 个内置 Agent | 少量捆绑技能 |
| **添加方式** | 代码内注册 | clawhub 搜索 + 安装 |

---

## 设计哲学对比

### simple-agent 原则
1. **工具极简** - 只做 bash 做不到的事
2. **高内聚** - 相关功能整合到单一模块
3. **最小抽象** - 避免过度工程化
4. **Python 优先** - 利用 Python 生态
5. **单用户场景** - 本地开发助手

### OpenClaw 原则
1. **渠道丰富** - 支持所有主流通信平台
2. **插件化** - 核心精简，能力通过插件扩展
3. **安全默认** - 配对策略 + 权限控制
4. **TypeScript 优先** - 易于理解和扩展
5. **个人助手** - 单用户、始终在线、本地优先

---

## 代码指标对比

| 指标 | simple-agent | OpenClaw |
|------|-------------|----------|
| **核心文件** | ~25 个 | 150+ 个 |
| **Agent 模块** | 1 个统一类 | 分布式运行时 |
| **工具数** | 11 个 | 100+ |
| **渠道集成** | 0 (CLI only) | 25+ |
| **测试数** | 122 个 | 完整测试基础设施 |
| **文档** | 6 个 MD 文档 | 完整 Docs 站点 |

---

## simple-agent 优势

1. **极简架构** - 25 个核心文件 vs 150+ 文件
2. **高内聚** - Agent 单一类 vs 分布式运行时
3. **易理解** - Python 代码直观，适合学习
4. **快速上手** - venv + git clone 即可运行
5. **智能工具** - BashTool 三级安全检查
6. **多 Agent 协作** - SwarmOrchestrator 群体智能
7. **动态调度** - DynamicScheduler + ParallelWorkflow

---

## OpenClaw 优势

1. **渠道丰富** - 25+ 通信平台集成
2. **生产就绪** - 280K+ stars, 完整生态
3. **安全设计** - DM 配对 + TCC 权限
4. **跨平台** - macOS/iOS/Android/Web
5. **插件生态** - ClawHub 技能市场
6. **远程访问** - Tailscale + SSH 隧道
7. **视觉工作区** - Canvas + A2UI

---

## 借鉴方向

### simple-agent 可借鉴 OpenClaw
1. **安全策略** - 添加 DM 配对类似的确认机制
2. **插件系统** - 考虑技能市场设计
3. **会话管理** - 增强 Session 模型和剪枝
4. **远程访问** - 支持 Tailscale/SSH 远程 Gateway
5. **视觉输出** - 考虑简单 Canvas/A2UI 类似功能

### OpenClaw 可借鉴 simple-agent
1. **工具极简** - 减少核心工具，优先系统命令
2. **高内聚设计** - 合并分散模块
3. **最小抽象** - 减少过度工程化
4. **Python 生态** - 利用丰富的 Python 库

---

## 总结

| 维度 | simple-agent | OpenClaw |
|------|-------------|----------|
| **定位** | 最小化学习/开发框架 | 生产级个人助手平台 |
| **复杂度** | 低 (适合学习) | 高 (功能完整) |
| **上手难度** | 简单 | 中等 (wizard 辅助) |
| **扩展性** | 代码内扩展 | 插件市场 |
| **安全性** | 基础 (BashTool 检查) | 完整 (配对 + 权限) |
| **生态** | 小型 | 大型 (280K+ stars) |

**选择建议**:
- **学习/原型**: simple-agent (简洁、易理解)
- **生产使用**: OpenClaw (功能完整、渠道丰富)
- **多 Agent 研究**: simple-agent (SwarmOrchestrator)
- **个人助手**: OpenClaw (25+ 渠道支持)

---

## 参考链接

- OpenClaw GitHub: https://github.com/openclaw/openclaw
- OpenClaw 官网: https://openclaw.ai
- OpenClaw 文档: https://docs.openclaw.ai
- ClawHub: https://clawhub.ai
- simple-agent 架构文档: docs/ARCHITECTURE.md
- simple-agent 测试指南: docs/TESTING.md
