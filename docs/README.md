# Simple Agent 文档中心

## 📚 文档概览

本目录包含 Simple Agent 系统的所有文档，包括 Swarm 群体智能、Agent 开发、输出管理等。

## 🔙 返回主目录

查看 **[项目根目录 README](../README.md)** 获取项目概览和快速开始指南。

## 🚀 快速开始

### 在 CLI 交互 UI 中使用 Swarm

**想快速体验？** 直接在交互界面中使用 Swarm！

1. 启动交互模式：`python cli.py`
2. 直接输入复杂任务，Swarm 会自动执行
3. 查看详细说明：**[HOW_TO_USE_SWARM_IN_CLI.md](./HOW_TO_USE_SWARM_IN_CLI.md)**

**示例**:
```
[CLI Agent] 你：帮我开发一个完整的用户登录系统
[Swarm] 自动分解任务并分配给多个 Agent 协作完成
```

### 使用 Python API

**想深入使用？** 查看 **[HOW_TO_USE_SWARM.md](./HOW_TO_USE_SWARM.md)** - 最简单易懂的使用指南！

## 🗂️ 完整文件索引

查看 **[FILE_INDEX.md](./FILE_INDEX.md)** 获取所有文件的详细索引和定位指南。

## 📚 文档列表

### 1. 快速开始

- **[SWARM_QUICK_REFERENCE.md](./SWARM_QUICK_REFERENCE.md)** - 快速参考卡片
  - 常用 API 和导入方式
  - 快速开始示例
  - 配置选项速查
  - 调试技巧

**适用场景**: 快速查找 API 用法和示例代码

---

### 2. CLI 交互 UI 使用

- **[HOW_TO_USE_SWARM_IN_CLI.md](./HOW_TO_USE_SWARM_IN_CLI.md)** - 交互 UI 使用指南 ⭐ NEW
  - 快速开始：在 CLI 中直接使用 Swarm
  - 5 种协作模式详解和示例
  - 高级用法：自定义配置、事件监听、动态 scaling
  - 实际案例：REST API 开发、代码重构、系统设计
  - 调试和监控技巧
  - 常见问题解答

**适用场景**: 想在交互界面中快速使用 Swarm

---

### 3. 代码开发流程

- **[AGENT_CODE_DEVELOPMENT.md](./AGENT_CODE_DEVELOPMENT.md)** - Agent 代码开发详解 ⭐ NEW
  - Agent 开发和写入代码的完整流程
  - WriteFileTool 实现原理
  - 工具调用机制和智能失败恢复
  - 实际案例分析（Pair Programming 等）
  - 自定义工具和调试技巧

**适用场景**: 理解 Agent 如何实际编写和写入代码

---

### 4. 逐步写入机制

- **[INCREMENTAL_CODE_WRITING.md](./INCREMENTAL_CODE_WRITING.md)** - 逐步写入机制详解 ⭐ NEW
  - 软件开发任务是一次性写入还是逐步写入？
  - Agent 层面的逐步写入实现
  - Swarm 层面的任务依赖和顺序执行
  - 实际案例分析（单 Agent vs Swarm）
  - 当前实现的限制和最佳实践

**适用场景**: 了解代码写入的时间顺序和依赖管理

---

### 5. 使用指南

- **[SWARM_USAGE.md](./SWARM_USAGE.md)** - 详细使用指南
  - 快速开始教程
  - 所有协作模式详解
  - 高级用法和最佳实践
  - 实际用例演示
  - 故障排查指南

**适用场景**: 系统学习和深入理解

---

### 6. 实施总结

- **[SWARM_IMPLEMENTATION_SUMMARY.md](./SWARM_IMPLEMENTATION_SUMMARY.md)** - 实施总结文档
  - 完成的组件清单
  - 测试结果汇总
  - 代码统计
  - 技术亮点
  - 下一步计划

**适用场景**: 了解项目整体情况和进度

---

### 6. 架构升级方案

- **[../ARCHITECTURE_UPGRADE.md](../ARCHITECTURE_UPGRADE.md)** - 架构升级完整方案
  - 阶段 1：Agent 能力增强
  - 阶段 2：Swarm 核心实现
  - 阶段 3：动态扩展和监控
  - 实施路线图

**适用场景**: 了解整体架构设计和演进路线

---

### 8. 输出目录管理

- **[OUTPUT_DIRECTORY.md](./OUTPUT_DIRECTORY.md)** - 输出目录管理指南 ⭐ NEW
  - 输出目录结构和配置
  - 如何避免污染根目录
  - 使用 OutputManagerTool
  - 清理和维护
  - 常见问题

**适用场景**: 管理生成的文件，保持项目整洁

---

### 9. 其他技术文档

以下是项目中产生的技术文档：

- **[ARCHITECTURE_UPGRADE.md](./ARCHITECTURE_UPGRADE.md)** - 完整架构升级方案
- **[DEEP_PROTECTION.md](./DEEP_PROTECTION.md)** - 深度保护机制
- **[DEEP_PROTECTION_SUMMARY.md](./DEEP_PROTECTION_SUMMARY.md)** - 深度保护总结
- **[DEVOPS.md](./DEVOPS.md)** - DevOps 相关文档
- **[ENHANCED_CLI.md](./ENHANCED_CLI.md)** - 增强 CLI 功能
- **[INTEGRATION_REPORT.md](./INTEGRATION_REPORT.md)** - 集成报告
- **[QUICKSTART_ENHANCED.md](./QUICKSTART_ENHANCED.md)** - 快速开始（增强版）
- **[README_DEEP_PROTECTION.md](./README_DEEP_PROTECTION.md)** - 深度保护 README
- **[README_STAGE1.md](./README_STAGE1.md)** - 阶段 1 README

**适用场景**: 了解项目技术细节和演进历史

---

## 🚀 快速导航

### 我想要...

| 需求 | 查看文档 | 章节 |
|------|---------|------|
| **在 CLI 中使用 Swarm** | [CLI 交互 UI 使用指南](./HOW_TO_USE_SWARM_IN_CLI.md) | 快速开始 |
| 快速上手 Swarm | [快速参考](./SWARM_QUICK_REFERENCE.md) | 快速开始 |
| 了解如何使用结对编程 | [使用指南](./SWARM_USAGE.md) | 协作模式 → 结对编程 |
| 了解如何使用头脑风暴 | [使用指南](./SWARM_USAGE.md) | 协作模式 → 头脑风暴 |
| 配置动态扩展 | [快速参考](./SWARM_QUICK_REFERENCE.md) | 配置选项 |
| 查看测试结果 | [实施总结](./SWARM_IMPLEMENTATION_SUMMARY.md) | 测试结果 |
| 了解架构设计 | [架构升级方案](../ARCHITECTURE_UPGRADE.md) | 方案二：Agent Swarm |
| 运行演示 | [使用指南](./SWARM_USAGE.md) | 运行演示 |
| 排查问题 | [使用指南](./SWARM_USAGE.md) | 故障排查 |

---

## 📦 组件清单

### 核心组件

| 组件 | 说明 | 文档位置 |
|------|------|---------|
| **SwarmOrchestrator** | 群体智能控制器 | [使用指南](./SWARM_USAGE.md#1-基本的-swarm-执行) |
| **Blackboard** | 共享黑板 | [使用指南](./SWARM_USAGE.md#3-共享黑板使用) |
| **MessageBus** | 消息总线 | [使用指南](./SWARM_USAGE.md#4-消息总线使用) |
| **TaskScheduler** | 任务调度器 | [架构升级方案](../ARCHITECTURE_UPGRADE.md#22-核心实现) |

### 协作模式

| 模式 | 说明 | 文档位置 |
|------|------|---------|
| **PairProgramming** | 结对编程 | [使用指南](./SWARM_USAGE.md#1-结对编程) |
| **SwarmBrainstorming** | 群体头脑风暴 | [使用指南](./SWARM_USAGE.md#2-群体头脑风暴) |
| **MarketBasedAllocation** | 市场分配 | [使用指南](./SWARM_USAGE.md#3-市场分配任务) |
| **CodeReviewLoop** | 代码审查循环 | [使用指南](./SWARM_USAGE.md#4-代码审查循环) |

### 高级功能

| 组件 | 说明 | 文档位置 |
|------|------|---------|
| **DynamicScaling** | 动态扩展 | [快速参考](./SWARM_QUICK_REFERENCE.md#9-动态扩展) |
| **AutoScalingOrchestrator** | 自动扩展 | [实施总结](./SWARM_IMPLEMENTATION_SUMMARY.md#4-动态扩展) |

---

## 🧪 测试和演示

### 运行测试

```bash
# 运行所有测试
python scripts/run_all_tests.py

# 单独运行
python tests/test_swarm.py
python tests/test_swarm_stage2.py
python tests/test_scaling.py
```

### 运行演示

```bash
#  Swarm 功能演示
python examples/demo_swarm.py
```

---

## 📊 项目状态

| 阶段 | 状态 | 进度 |
|------|------|------|
| 阶段 1: Agent 能力增强 | ✅ 完成 | 100% |
| 阶段 2: Swarm 核心 | ✅ 完成 | 100% |
| 阶段 3: 动态扩展 | ✅ 完成 | 100% |
| 阶段 3: 监控可观测性 | 🔄 进行中 | 0% |

**总计**: 33 个测试用例，全部通过 ✓

---

## 🔗 相关链接

- **项目根目录**: `../`
- **Swarm 源码**: `../swarm/`
- **测试目录**: `../tests/`
- **示例目录**: `../examples/`

---

## 📝 更新日志

### 2026-03-07

- ✅ 完成阶段 2：Swarm 核心实现
- ✅ 完成阶段 3：动态扩展功能
- ✅ 创建完整文档体系
- ✅ 33 个测试用例全部通过

### 2026-03-06

- ✅ 完成阶段 1：Agent 能力增强
- ✅ 增强记忆系统
- ✅ 高级推理模式
- ✅ 技能学习系统

---

## 💡 使用建议

1. **新手用户**: 从 [快速参考](./SWARM_QUICK_REFERENCE.md) 开始，快速了解基本用法
2. **深入使用**: 阅读 [使用指南](./SWARM_USAGE.md)，学习高级功能和最佳实践
3. **架构理解**: 查看 [架构升级方案](../ARCHITECTURE_UPGRADE.md)，了解设计思路
4. **问题排查**: 参考 [使用指南](./SWARM_USAGE.md) 的故障排查章节

---

## 📧 反馈和支持

如有问题或建议，请：
1. 查看相关文档章节
2. 检查故障排查指南
3. 运行测试验证环境
