# simple-agent 发展方向 - 执行摘要

## 与 OpenClaw 对比结论

### 定位差异

| | simple-agent | OpenClaw |
|---|---|---|
| **定位** | 多 Agent 协作研究框架 | 个人 AI 助手平台 |
| **目标用户** | 研究者/开发者/企业 | 终端用户 |
| **核心价值** | 群体智能 + 任务编排 | 渠道集成 + 始终在线 |
| **代码规模** | ~11K 行 | ~50K+ 行 |
| **渠道支持** | CLI only | 25+ 通信平台 |
| **Stars** | - | 280K+ |

### simple-agent 优势领域

✅ **多 Agent 协作** - SwarmOrchestrator 群体智能
✅ **任务分解** - 三级分解 (Goal→Task→Action) + 依赖图
✅ **智能调度** - DynamicScheduler 技能匹配/负载平衡
✅ **并行执行** - ParallelWorkflow asyncio 并发
✅ **极简架构** - 26 个核心文件 vs 150+ 文件
✅ **易学习** - Python 代码直观，适合教学/研究

### OpenClaw 优势领域

✅ **渠道丰富** - WhatsApp/Telegram/Slack 等 25+ 平台
✅ **生产就绪** - 完整安全设计 (DM 配对/TCC 权限)
✅ **跨平台** - macOS/iOS/Android/Web
✅ **插件生态** - ClawHub 技能市场
✅ **远程访问** - Tailscale Serve/Funnel

---

## 战略方向：差异化竞争

**核心原则**: 不做 OpenClaw 的复制品，专注多 Agent 协作研究

```
OpenClaw: 个人助手 → 渠道集成 → 插件生态 → 商业化
simple-agent: 多 Agent 协作 → 智能编排 → 研究平台 → 企业方案
```

---

## 发展路线图

### 短期 (1-3 个月) - 完善核心能力

**优先级 1: 基础功能**
- [ ] 会话管理 (多会话隔离/持久化)
- [ ] 技能市场原型 (本地注册/加载)
- [ ] CLI 增强 (自动补全/命令搜索)
- [ ] 文档站点 (MkDocs + 示例)

**优先级 2: 协作增强**
- [ ] 新增 3 种协作模式 (Team/Market/Pair)
- [ ] Agent 能力发现和匹配
- [ ] 多 Agent 结果聚合策略

### 中期 (3-6 个月) - 平台化

**方向 A: 研究平台**
- 实验框架 (A/B 测试协作策略)
- 指标收集 (成功率/时长/成本)
- 可视化仪表板
- 基准测试集

**方向 B: 企业自动化**
- 工作流模板 (Code Review/数据处理)
- REST API 网关
- 权限管理 (RBAC + 审计)
- 监控告警

**方向 C: 技能生态**
- 技能注册中心
- YAML 配置技能
- 技能沙箱 (安全执行)

### 长期 (6-12 个月) - 研究标准

**愿景**: 多 Agent 协作研究的事实标准

**里程碑**:
- 1-2 篇学术论文
- GitHub 1K+ stars
- 10+ 社区贡献者
- 3-5 个企业生产案例
- 50+ 社区技能

---

## 架构演进

### 当前架构 (v1.0)
```
CLI → Swarm → Core
```

### 目标架构 (v2.0)
```
Interface Layer (CLI/Web/API/SDK)
        ↓
Skill Platform (Hub/Runner/Sandbox)
        ↓
Multi-Agent Collaboration (Swarm/Team/Market/Pair/Review)
        ↓
Intelligent Orchestration (Decomposer/Scheduler/Workflow)
        ↓
Core Foundation (Agent/Memory/LLM/Tools)
        ↓
Observability (Metrics/Tracing/Dashboard)
```

### 架构原则
1. 核心不超过 30 个文件
2. 插件化扩展
3. 向后兼容
4. 渐进式重构

---

## 关键指标

| 维度 | 当前 | Q2 目标 | Q4 目标 |
|------|------|--------|--------|
| GitHub Stars | - | 500 | 1000 |
| 月活用户 | - | 50 | 200 |
| 核心文件数 | 26 | ≤30 | ≤30 |
| 测试覆盖率 | 75% | 80% | 85% |
| 文档覆盖率 | 60% | 80% | 95% |

---

## 立即行动项 (Next 2 Weeks)

1. **会话管理** (`core/session_manager.py`)
   - 多会话隔离
   - JSON 持久化
   - CLI 命令 (`/session new/load/list`)

2. **技能配置加载** (`core/skill_config.py`)
   - YAML 配置解析
   - 内置技能注册
   - 技能依赖管理

3. **CLI 增强**
   - 集成 `argcomplete`
   - 命令历史搜索
   - 错误提示优化

4. **文档站点**
   - MkDocs 搭建
   - API 文档生成
   - 10 个使用示例

---

## 总结

simple-agent 不应复制 OpenClaw 的"全渠道个人助手"路线，而应专注于：

**差异化定位**: 多 Agent 协作研究框架
**目标用户**: 研究者、开发者、企业
**核心价值**: 群体智能 + 任务编排 + 极简架构
**生态策略**: Python 生态 + 技能市场 + 学术合作

通过差异化竞争，simple-agent 有望成为多 Agent 协作研究领域的事实标准。

---

详细文档：`docs/ROADMAP.md`
对比分析：`docs/OPENCLAW_COMPARISON.md`
架构文档：`docs/ARCHITECTURE.md`
