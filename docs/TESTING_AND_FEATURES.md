# Simple Agent 测试与功能文档

本文档整合了测试策略、测试总结、增强功能和安全防护功能。

---

## 目录

1. [测试策略与防护](#1-测试策略与防护)
2. [测试总结](#2-测试总结)
3. [增强 CLI 功能](#3-增强-cli-功能)
4. [深度防护系统](#4-深度防护系统)
5. [后台任务功能](#5-后台任务功能)

---

## 1. 测试策略与防护

### 1.1 问题背景

每个执行节点后添加测试节点会导致：
- ❌ 执行流程冗长
- ❌ 维护成本高
- ❌ 测试代码与业务代码耦合
- ❌ 难以覆盖边界情况

### 1.2 推荐方案：多层防护体系

#### 第一层：输入验证（Input Validation）

```python
def validate_weather_query(user_input: str) -> dict:
    """输入验证：确保查询合法"""
    if not user_input or len(user_input.strip()) < 2:
        raise ValueError("查询不能为空")
    
    return {
        'query': user_input,
        'date': datetime.now().isoformat(),
        'validated': True
    }
```

#### 第二层：断言检查（Assertion Checks）

```python
def execute_weather_query(query: str) -> WeatherResult:
    """执行天气查询，包含断言检查"""
    result = web_search_tool(query)
    
    # 断言：结果必须包含日期信息
    assert result.date is not None, "天气结果必须包含日期"
    
    # 断言：日期必须与当前日期一致
    today = datetime.now().date()
    assert abs((result.date - today).days) <= 1
    
    return result
```

#### 第三层：结果验证器（Result Validator）

```python
class WeatherResultValidator:
    @staticmethod
    def validate(result: WeatherResult) -> tuple[bool, str]:
        if not result.date:
            return False, "缺少日期信息"
        
        if not result.temperature:
            return False, "缺少温度信息"
        
        # 检查日期是否合理
        today = datetime.now().date()
        if result.date < today - timedelta(days=1):
            return False, f"日期过时：{result.date}"
        
        return True, ""
```

#### 第四层：测试脚本（独立运行）

```python
#!/usr/bin/env python3
# tests/test_weather_query.py

def test_weather_date_accuracy():
    """测试天气查询日期准确性"""
    result = query_weather("北京天气")
    
    assert result.date == datetime.now().date()
    assert result.temperature is not None
    assert result.conditions is not None

if __name__ == "__main__":
    test_weather_date_accuracy()
    print("✓ 测试通过")
```

#### 第五层：集成测试（CI/CD）

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: python tests/test_weather_query.py
```

### 1.3 何时使用哪种防护？

| 场景 | 推荐防护 | 理由 |
|------|---------|------|
| **关键业务逻辑** | 全部 5 层 | 天气、支付等不能出错 |
| **用户体验相关** | 第 1-3 层 | 输入验证 + 断言 + 结果验证 |
| **内部工具** | 第 2-3 层 | 断言 + 结果验证 |
| **原型开发** | 第 2 层 | 快速迭代，只保留关键断言 |

---

## 2. 测试总结

### 2.1 测试覆盖

#### 现有测试文件

| 文件 | 测试内容 | 状态 |
|------|----------|------|
| `test_agents.py` | Agent 配置加载、工具注册 | ✅ |
| `test_tool_execution.py` | 工具属性验证 | ✅ |
| `test_swarm.py` | Swarm 组件单元测试 | ✅ |
| `test_swarm_stage2.py` | 阶段 2 功能集成测试 | ✅ |
| `test_swarm_concurrent.py` | 并发执行测试 | ✅ 新增 |
| `test_rich_output.py` | 富文本输出测试 | ✅ 新增 |
| `test_task_queue.py` | 后台任务测试 | ✅ 新增 |

### 2.2 新增功能验证

#### 富文本输出模块 (`core/rich_output.py`)

**功能特性**:
- ✅ 彩色文本输出
- ✅ 表格展示
- ✅ 面板显示
- ✅ 进度条支持
- ✅ 代码高亮
- ✅ Markdown 渲染

**测试结果**: 10/10 通过 ✅

#### 并发执行测试

| 测试项 | 说明 | 状态 |
|--------|------|------|
| 并发执行（无依赖） | 3 个任务并发 | ✅ |
| 顺序执行（有依赖） | 依赖任务串行 | ✅ |
| 混合依赖执行 | 2 轮并发 | ✅ |
| 多 Agent 并发 | 5 任务 2 Agent | ✅ |
| 任务执行顺序 | 依赖顺序验证 | ✅ |

**测试结果**: 5/5 通过 ✅

### 2.3 性能对比

| 场景 | 任务数 | Agent 数 | 串行预期 | 实际耗时 | 提升 |
|------|--------|----------|----------|----------|------|
| 无依赖 | 3 | 3 | 1.5s | 0.50s | **3.0x** |
| 有依赖 | 3 | 1 | 0.9s | 0.91s | 1.0x |
| 混合依赖 | 4 | 4 | 1.2s | 0.61s | **2.0x** |
| 多 Agent | 5 | 2 | 1.5s | 0.31s | **4.8x** |

---

## 3. 增强 CLI 功能

### 3.1 阶段 1 功能集成

阶段 1 的 5 个核心功能已成功集成到 CLI：

1. **EnhancedMemory** - 增强型记忆系统
2. **TreeOfThought** - 思维树推理模式
3. **ReflectionLoop** - 反思循环
4. **SkillLibrary** - 技能学习系统
5. **EnhancedAgent** - 增强型 Agent

### 3.2 新增命令

#### `/enhanced [策略] <任务>`

使用增强型 Agent 执行任务。

```bash
# 自动选择策略
/enhanced 分析这段代码

# 指定策略
/enhanced direct 简单任务
/enhanced plan_reflect 需要规划的任务
/enhanced tree_of_thought 复杂决策问题
```

**策略说明**:
- `direct` - 直接执行，适用于简单任务
- `plan_reflect` - 规划反思模式，适用于中等复杂度任务
- `tree_of_thought` - 思维树推理，适用于复杂决策问题

#### `/memory`

查看当前记忆状态。

```bash
/memory          # 查看记忆状态
/memory clear    # 清空所有记忆
```

**输出示例**:
```
============================================================
记忆状态
============================================================
工作记忆：2 条
短期记忆：3 条
经验记录：5 条
反思总结：1 条

最近 3 条短期记忆：
  1. [✓] 分析代码结构...
  2. [✓] 生成测试代码...
  3. [✗] 修复 bug 失败...
```

#### `/skills`

查看技能库。

```bash
/skills    # 查看技能列表和统计
```

### 3.3 策略选择流程

1. **记忆检索**：检索相关历史经验
2. **复杂度评估**：基于关键词和相似度
3. **策略选择**：
   - 有高相似度成功经验 → `plan_reflect`
   - 复杂度高（>0.7）→ `tree_of_thought`
   - 中等复杂度（>0.4）→ `plan_reflect`
   - 低复杂度 → `direct`

### 3.4 组件关系

```
EnhancedAgent (增强型 Agent)
├── EnhancedMemory (记忆系统)
│   ├── working_memory (工作记忆)
│   ├── short_term (短期记忆)
│   └── long_term (长期记忆 - 向量数据库)
├── SkillLibrary (技能库)
│   └── builtin_skills (内置技能)
└── reasoning_modes (推理模式)
    ├── TreeOfThought (思维树)
    └── ReflectionLoop (反思循环)
```

---

## 4. 深度防护系统

### 4.1 工具列表

#### deep_protection.py - 深度防护主脚本

**功能**:
- 静态代码分析（AST 分析）
- Agent 智能审查
- 安全性检查
- 代码质量评估

**使用**:
```bash
# 检查单个文件
python scripts/deep_protection.py core/agent.py

# 检查所有 Python 文件
python scripts/deep_protection.py --all

# 输出 JSON 报告
python scripts/deep_protection.py --all --json > report.json

# 仅静态分析（不使用 Agent）
python scripts/deep_protection.py core/ --no-agent
```

#### agent_review.py - Agent 代码审查工具

**使用**:
```bash
# 审查单个文件
python scripts/agent_review.py core/agent.py

# 审查所有 Python 文件
python scripts/agent_review.py --all

# 输出报告到文件
python scripts/agent_review.py core/ -o review_report.txt
```

### 4.2 检查维度

#### 安全性 (Security)

| 检查项 | 严重程度 | 说明 |
|--------|---------|------|
| 硬编码密钥 | 🔴 Critical | 密码、API 密钥等敏感信息 |
| 代码注入 | 🔴 Critical | eval(), exec(), os.system() |
| 命令注入 | 🔴 Critical | subprocess shell=True |
| 反序列化 | 🔴 Critical | pickle.load() |
| 弱加密 | 🟡 Warning | MD5, SHA1 |

#### 代码质量 (Quality)

| 检查项 | 严重程度 | 说明 |
|--------|---------|------|
| 语法错误 | 🔴 Critical | Python 语法问题 |
| 圈复杂度 | 🟡 Warning | >10 表示复杂度过高 |
| 函数长度 | 🟡 Warning | >50 行建议拆分 |
| 文件长度 | 🟡 Warning | >500 行建议拆分 |

### 4.3 CLI 集成

```bash
# 在 CLI 中使用
[CLI Agent] 你：/review core/agent.py

# 审查所有 Python 文件
[CLI Agent] 你：/review --all
```

### 4.4 Git Hooks 集成

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "🔒 [Pre-commit] 运行深度防护检查..."

# 运行静态分析
python scripts/deep_protection.py --no-agent

if [ $? -ne 0 ]; then
    echo "❌ 深度防护检查失败"
    exit 1
fi

echo "✅ 深度防护检查通过"
```

---

## 5. 后台任务功能

### 5.1 功能概述

实现了完整的后台任务执行系统，解决了原有 CLI 在执行任务时阻塞用户输入的问题。

- ✅ **后台任务提交** - 使用 `/bg` 命令提交任务
- ✅ **任务状态跟踪** - 使用 `/tasks` 查看所有任务状态
- ✅ **任务结果获取** - 使用 `/result <task_id>` 查看结果
- ✅ **任务取消** - 使用 `/cancel <task_id>` 取消任务
- ✅ **并发控制** - 默认最多 3 个任务同时执行

### 5.2 新增文件

| 文件 | 功能 | 行数 |
|------|------|------|
| `core/task_handle.py` | 任务状态跟踪和数据模型 | ~220 |
| `core/task_queue.py` | 异步任务队列和后台执行 worker | ~350 |
| `tests/test_task_queue.py` | 单元测试 | ~370 |

### 5.3 CLI 命令

#### `/bg <任务>` - 后台执行任务

```bash
/bg 分析这个项目
✓ 任务已提交到后台执行：task_1_1772872049574
使用 /tasks 查看状态
```

#### `/tasks` - 列出所有后台任务

```bash
/tasks
============================================================
后台任务列表 (3 个)
============================================================
  🔄 [running   ] task_3 | 检查代码中的安全问题 | 0.5s
  🔄 [running   ] task_2 | 帮我写一个单元测试 | 0.6s
  ✅ [completed ] task_1 | 分析这个项目的代码结构 | 完成

统计：总计 3 | 等待 0 | 运行 2 | 完成 1 | 失败 0 | 取消 0
```

#### `/result <task_id>` - 查看任务结果

```bash
/result task_1_1772872049574
等待任务 task_1_1772872049574 完成...
✓ [详细的任务执行结果...]
```

#### `/cancel <task_id>` - 取消任务

```bash
/cancel task_1_1772872049574
✓ 已取消任务：task_1_1772872049574
```

### 5.4 技术实现

#### 并发控制

```python
class TaskQueue:
    def __init__(self, max_concurrent: int = 3):
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _execute_task(self, task_def, handle):
        async with self._semaphore:  # 限制并发数
            result = await task_def.coro
```

#### 任务状态机

```
PENDING -> RUNNING -> COMPLETED
                      |-> FAILED
                      |-> CANCELLED
```

### 5.5 性能验证

**并发执行测试**:
- 5 个任务（每个耗时 0.3 秒）
- 理论串行：1.5 秒
- 理论并行（3 并发）：~0.6 秒
- 实际耗时：~0.6-1.0 秒
- 性能提升：~33-60%

---

## 6. 运行测试

```bash
# 运行所有测试
python scripts/run_all_tests.py

# 单独运行
python tests/test_swarm.py
python tests/test_swarm_stage2.py
python tests/test_scaling.py
python tests/test_swarm_concurrent.py
python tests/test_rich_output.py
python tests/test_task_queue.py

# 运行演示
python examples/demo_swarm.py
```

---

## 7. 依赖安装

```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装 rich 库（富文本）
pip install rich>=13.0.0

# 安装向量数据库（长期记忆）
pip install chromadb>=0.4.0
pip install numpy>=1.24.0
```

---

**文档版本**: 2.0  
**最后更新**: 2026-03-08  
**合并自**: TEST_REVIEW_SUMMARY.md, TEST_STRATEGY.md, ENHANCED_CLI.md, DEEP_PROTECTION.md, BACKGROUND_TASK_FEATURE.md
