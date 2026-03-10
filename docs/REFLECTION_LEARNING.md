# 反思学习系统

## 概述

反思学习系统通过在每次 workflow 执行后进行分析和总结，识别性能瓶颈并生成优化建议，持续提升后续执行效率。

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│              ReflectionLearningCoordinator              │
│                   (反思学习协调器)                       │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌─────────────────────────────┐ │
│  │ ExecutionRecorder│  │ PerformanceAnalyzer         │ │
│  │ - 开始记录        │  │ - 识别慢步骤                │ │
│  │ - 记录步骤        │  │ - 识别长链路                │ │
│  │ - 结束记录        │  │ - 识别冗余步骤              │ │
│  └──────────────────┘  │ - 识别重试开销              │ │
│                        │ - 识别并行机会              │ │
│  ┌──────────────────┐  └─────────────────────────────┘ │
│  │ExperienceStore   │  ┌─────────────────────────────┐ │
│  │ - 存储经验       │  │ OptimizationSuggester       │ │
│  │ - 查找相似经验   │  │ - 生成优化建议              │ │
│  │ - 更新成功次数   │  │ - 生成优化总结              │ │
│  └──────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. ExecutionRecorder (执行记录器)

记录详细的执行指标：

```python
from core.reflection_learning import ExecutionRecorder

recorder = ExecutionRecorder(storage_dir="./reflection_logs")

# 开始记录
record_id = recorder.start_recording(
    workflow_name="CodeReviewWorkflow",
    task_description="审查用户认证模块"
)

# 记录步骤开始
recorder.record_step_start(
    step_name="代码分析",
    step_index=1,
    agent_name="Developer"
)

# 记录步骤结束
recorder.record_step_end(
    step_index=1,
    agent_name="Developer",
    result="分析完成",
    success=True,
    iterations=2,
    tool_calls=5,
    input_text="源代码内容"
)

# 结束记录
recorder.finish_recording(
    success=True,
    final_output="审查报告"
)
```

**记录的指标**:
- 步骤执行时间
- 迭代次数
- 工具调用次数
- 输入/输出长度
- 并行/串行步骤数
- 重试次数

### 2. PerformanceAnalyzer (性能分析器)

识别性能瓶颈：

| 瓶颈类型 | 描述 | 识别阈值 |
|---------|------|---------|
| `slow_step` | 执行过慢的步骤 | >30 秒 |
| `long_chain` | 过长的串行链路 | >5 步 |
| `redundant_step` | 冗余步骤 | 相似输入/输出 |
| `retry_overhead` | 重试开销过大 | 重试次数>3 |
| `wait_time` | 可并行化的等待时间 | 独立步骤 |

```python
from core.reflection_learning import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()
bottlenecks, stats = analyzer.analyze(execution_record)

# bottlenecks: 瓶颈列表
# stats: 统计数据 {
#   "total_duration": 120.5,
#   "avg_step_duration": 24.1,
#   "total_steps": 5,
#   "success_rate": 1.0,
#   "total_retries": 2
# }
```

### 3. OptimizationSuggester (优化建议生成器)

基于瓶颈生成具体建议：

| 瓶颈类型 | 优化建议 | 预期提升 |
|---------|---------|---------|
| `slow_step` | 调整超时/切换 Agent | 20-50% |
| `long_chain` | 合并步骤 | 30-60% |
| `redundant_step` | 跳过冗余步骤 | 10-20% |
| `retry_overhead` | 增加重试间隔/切换策略 | 15-40% |
| `wait_time` | 并行化执行 | 40-70% |

```python
from core.reflection_learning import OptimizationSuggester

suggester = OptimizationSuggester()
suggestions = suggester.generate_suggestions(bottlenecks, record)

for suggestion in suggestions:
    print(f"[{suggestion.priority}] {suggestion.title}")
    print(f"   预期提升：{suggestion.expected_improvement}%")
    print(f"   实施方法：{suggestion.implementation}")
```

### 4. ExperienceStore (经验存储库)

存储和检索成功优化经验：

```python
from core.reflection_learning import ExperienceStore

store = ExperienceStore(storage_file="./experiences.json")

# 存储经验
exp_id = store.store_experience(
    task_pattern="代码审查",
    original_workflow="sequential_v1",
    optimized_workflow="parallel_v2",
    original_duration=120,
    optimized_duration=60,
    optimizations_applied=["parallelize", "merge_steps"]
)

# 查找相似经验
similar = store.find_similar_experiences("审查认证模块")
for exp in similar:
    print(f"相似度：{exp.similarity_score}")
    print(f"优化方案：{exp.optimizations_applied}")
    print(f"成功率：{exp.success_count / exp.total_count}")
```

## 使用 Workflow 集成

### 启用反思学习

```python
from core.workflow import Workflow

workflow = Workflow("CodeReviewWorkflow")
workflow.add_step("代码分析", developer_agent)
workflow.add_step("问题识别", reviewer_agent)
workflow.add_step("报告生成", documenter_agent)

# 执行时启用反思学习
result = workflow.run(
    initial_input="审查 src/auth.py",
    verbose=True,
    output_dir="./output",
    enable_reflection=True  # 启用反思学习
)
```

### 输出示例

```
===== Workflow 执行完成 =====
总耗时：120.5 秒
成功：是

===== 性能分析 =====
平均步骤耗时：40.2 秒
并行步骤：0
串行步骤：3
重试次数：2

===== 优化建议 =====
发现 3 个优化机会，预期总提升 45%:

[优先级 5] 并行化执行
  预期提升：40%
  实施方法：使用 ParallelWorkflow 执行独立步骤
  相关步骤：步骤 2, 3

[优先级 3] 调整超时配置
  预期提升：20%
  实施方法：步骤 1 的 timeout 从 30s 调整到 60s
  相关步骤：步骤 1

[优先级 2] 跳过冗余步骤
  预期提升：10%
  实施方法：步骤 2 与步骤 1 输出相似，可考虑合并
  相关步骤：步骤 1, 2
```

## CLI 使用

```bash
# 执行单次任务（默认启用反思学习）
.venv/bin/python cli.py "审查这个项目的认证模块"

# 查看经验统计
.venv/bin/python -c "
from core.reflection_learning import get_learning_coordinator
coordinator = get_learning_coordinator()
stats = coordinator.get_experience_statistics()
print(f'总经验数：{stats[\"total\"]}')
print(f'平均提升：{stats[\"avg_improvement\"]}%')
"
```

## 自愈系统联动

反思学习与自愈系统协同工作：

```python
from core.self_healing import SelfHealingCoordinator
from core.reflection_learning import ReflectionLearningCoordinator

# 自愈协调器
self_healing = SelfHealingCoordinator()

# 反思学习协调器
reflection = ReflectionLearningCoordinator()

# 执行 workflow
record_id = reflection.start("CodeReview", "审查代码")

try:
    # 执行中启用自愈
    result = workflow.run(
        input,
        enable_self_healing=True,  # 自愈
        enable_reflection=True     # 反思学习
    )
    reflection.finish(success=True, final_output=result)
except Exception as e:
    self_healing.handle_exception(agent, e, "审查任务")
    reflection.finish(success=False, error_message=str(e))

# 获取优化建议
suggestions = reflection.get_optimization_suggestions()

# 应用高优先级建议
for suggestion in suggestions:
    if suggestion.priority >= 4:
        apply_optimization(suggestion)
```

## 经验自动应用

```python
coordinator = ReflectionLearningCoordinator()

# 执行新任务前自动查找并应用经验
result = coordinator.apply_learned_experience("审查新的认证模块")

if result["found"]:
    print(f"应用了 {len(result['optimizations'])} 个优化:")
    for opt in result['optimizations']:
        print(f"  - {opt}")
```

## 配置文件

在 `configs/reflection_config.yaml` 中配置：

```yaml
reflection_learning:
  enabled: true
  storage_dir: "./reflection_logs"
  experience_file: "./experiences.json"

  # 性能阈值
  thresholds:
    slow_step_seconds: 30
    long_chain_steps: 5
    max_retries: 3

  # 优化建议
  suggestions:
    min_priority: 2  # 最低显示优先级
    max_suggestions: 5

  # 经验匹配
  experience:
    similarity_threshold: 0.6  # 最低相似度
    min_success_rate: 0.7      # 最低成功率
```

## 最佳实践

### 1. 持续优化循环

```
执行 → 分析 → 建议 → 应用 → 再执行
  ↑                              │
  └──────────────────────────────┘
```

### 2. 经验积累

- 每次成功优化后自动存储
- 相似任务自动应用历史经验
- 成功次数越多，优先级越高

### 3. 性能基线

定期查看统计建立基线：

```python
stats = coordinator.get_performance_stats()
print(f"平均执行时间：{stats['avg_duration']}秒")
print(f"平均优化提升：{stats['avg_improvement']}%")
```

### 4. 调优建议

| 场景 | 建议 |
|------|------|
| 慢步骤多 | 增加并行化 |
| 重试频繁 | 检查工具稳定性 |
| 长链路 | 考虑分解 workflow |
| 冗余步骤 | 简化流程 |

## 测试

```bash
# 运行反思学习测试
.venv/bin/python -m pytest tests/test_reflection_learning.py -v

# 运行自愈系统集成测试
.venv/bin/python -m pytest tests/test_self_healing.py -v
```

## 文件结构

```
core/
  reflection_learning.py    # 反思学习核心 (~900 行)
    - ExecutionRecorder
    - PerformanceAnalyzer
    - OptimizationSuggester
    - ExperienceStore
    - ReflectionLearningCoordinator

tests/
  test_reflection_learning.py  # 15 个测试

configs/
  reflection_config.yaml    # 配置文件 (可选)

docs/
  REFLECTION_LEARNING.md    # 本文档
```

## 设计原则

### 1. 非侵入式
- 默认启用，不影响现有 workflow
- 失败时自动降级，不中断执行

### 2. 数据驱动
- 基于实际执行数据生成建议
- 经验成功率可追溯

### 3. 持续改进
- 每次执行都有收获
- 经验库持续增长

### 4. 性能优先
- 分析时间 <1 秒
- 存储异步，不阻塞执行

## 验收标准

- [x] 执行记录完整
- [x] 瓶颈识别准确
- [x] 优化建议具体可执行
- [x] 经验存储可检索
- [x] workflow 集成无缝
- [x] 15 个测试全部通过
