# 阶段 1 增强功能快速启动指南

## 启动 CLI

```bash
python cli.py
```

CLI 会自动初始化增强型 Agent，显示：

```
[阶段 1] 增强型 Agent 已初始化
  - EnhancedMemory: 已启用
  - SkillLibrary: 3 个技能
  - 推理模式：TreeOfThought, ReflectionLoop
```

## 快速命令参考

### 增强型任务执行

```bash
# 自动选择策略（推荐）
/enhanced 分析这段代码

# 手动指定策略
/enhanced direct 简单问题
/enhanced plan_reflect 中等复杂度任务
/enhanced tree_of_thought 复杂决策问题
```

### 查看状态

```bash
/memory     # 查看记忆状态
/skills     # 查看技能库
/info       # 查看当前 Agent 详情
```

### 推理模式

```bash
/reasoning tot           # 思维树推理
/reasoning reflection    # 反思循环
```

## 完整示例

### 示例 1：代码分析

```bash
$ python cli.py

[CLI Agent] 你：/enhanced 分析 Python 代码的最佳实践

[增强型 Agent] 执行任务：分析 Python 代码的最佳实践
[Meta] 选择策略：plan_reflect
[Plan] 制定计划：3 个步骤
...

# 查看记忆
[CLI Agent] 你：/memory

============================================================
记忆状态
============================================================
工作记忆：5 条
短期记忆：1 条
经验记录：1 条
反思总结：0 条
```

### 示例 2：复杂系统设计

```bash
# 使用思维树推理
[CLI Agent] 你：/enhanced tree_of_thought 设计一个高并发系统

[增强型 Agent] 使用策略：tree_of_thought
[增强型 Agent] 执行任务：设计一个高并发系统
...

# 查看使用的技能
[CLI Agent] 你：/skills

技能库 (3 个技能)
  - 代码分析：成功率 80%
  - 测试生成：成功率 75%
  - 文档编写：成功率 85%
```

## 策略选择建议

| 任务类型 | 推荐策略 | 示例 |
|---------|---------|------|
| 简单问答 | `direct` | "你好", "解释一下函数" |
| 代码分析 | `plan_reflect` | "分析这段代码的问题" |
| 系统设计 | `tree_of_thought` | "设计一个电商平台" |
| 架构规划 | `plan_reflect` | "规划微服务架构" |
| 复杂决策 | `tree_of_thought` | "选择最佳技术方案" |

## 调试模式

开启详细输出和文件保存：

```bash
/debug on
/enhanced 分析这个项目
# 输出会保存到 ./cli_output/
```

## 测试

运行集成测试验证功能：

```bash
python test_enhanced_cli.py
```

预期输出：

```
✓ 增强型 Agent 创建成功
✓ 记忆状态正常
✓ TreeOfThought 已就绪
✓ ReflectionLoop 已就绪
所有测试通过!
```

## 常用工作流

### 代码审查工作流

```bash
# 1. 分析代码
/enhanced 分析这个文件的代码质量

# 2. 查看记忆
/memory

# 3. 生成测试
/enhanced 为这段代码生成单元测试

# 4. 编写文档
/enhanced 为这个模块编写文档
```

### 系统设计方案

```bash
# 1. 使用思维树探索多个方案
/enhanced tree_of_thought 设计消息队列系统

# 2. 使用规划反思完善最佳方案
/enhanced plan_reflect 基于上述方案详细设计

# 3. 记录经验
/memory  # 查看保存的经验
```

## 退出 CLI

```bash
/exit
```

## 更多信息

详细文档请查看：`ENHANCED_CLI.md`
