# 测试指南 (Testing Guide)

Simple Agent 系统的测试策略和最佳实践。

## 测试概览

项目共有 **122 个测试**，覆盖以下关键组件：

- 核心调度器 (DynamicScheduler)
- 并行工作流 (ParallelWorkflow)
- Swarm 群体智能 (SwarmOrchestrator)
- 工具执行 (Tools)
- Agent 系统

## 快速开始

### 1. 日常测试 (推荐每日执行)

```bash
# 运行日常核心测试 (约 30 秒)
./tests/run_daily_tests.sh
```

这会运行：
- `test_deep_core.py` - 14 个深度集成测试
- `test_tool_execution.py` - 工具执行测试
- `test_domains.py` - 领域测试

### 2. 快速测试 (代码修改后快速验证)

```bash
# 快速测试 (5 分钟内)
./tests/run_quick_tests.sh
```

只运行 `test_deep_core.py`，验证核心功能正常。

### 3. 完整测试套件 (发布前)

```bash
# 完整测试 (约 5-10 分钟)
./tests/run_all_tests.sh
```

运行所有测试文件，确保系统完全正常。

## 测试文件结构

### 核心深度测试 (强烈推荐)

| 文件 | 测试数 | 说明 |
|------|--------|------|
| `test_deep_core.py` | 14 | 核心组件深度集成测试 |

**测试分类**:

```
TestDeepSchedulerIntegration (3 个)
├── test_scheduler_full_workflow       # 完整调度工作流
├── test_scheduler_skill_matching      # 技能匹配
└── test_scheduler_retry_mechanism     # 重试机制

TestDeepWorkflowParallel (3 个)
├── test_parallel_execution_timing     # 并行执行时间
├── test_parallel_timeout_handling     # 超时处理
└── test_parallel_error_isolation      # 错误隔离

TestDeepSwarmOrchestration (3 个)
├── test_swarm_multi_agent_collaboration  # 多 Agent 协作
├── test_swarm_blackboard_sharing         # 黑板共享
└── test_swarm_task_decomposition         # 任务分解

TestDeepSystemStability (3 个)
├── test_concurrent_load_handling      # 并发负载
├── test_resource_cleanup              # 资源清理
└── test_edge_case_handling            # 边界情况

TestPerformanceBenchmarks (2 个)
├── test_scheduler_throughput          # 吞吐量基准
└── test_workflow_parallelism_efficiency # 并行效率
```

### 组件单元测试

| 文件 | 测试数 | 说明 |
|------|--------|------|
| `test_dynamic_scheduler.py` | 29 | 动态调度器单元测试 |
| `test_workflow_parallel.py` | 30 | 并行工作流单元测试 |
| `test_swarm_integration.py` | 16 | Swarm 集成测试 |

### 其他测试

| 文件 | 说明 |
|------|------|
| `test_agents.py` | Agent 基础测试 |
| `test_domains.py` | 领域系统测试 |
| `test_workflow_integration.py` | 工作流集成测试 |
| `test_swarm_concurrent.py` | Swarm 并发测试 |

## 运行测试

### pytest 命令

```bash
# 运行单个测试文件
./venv/bin/python -m pytest tests/test_deep_core.py -v

# 运行单个测试类
./venv/bin/python -m pytest tests/test_deep_core.py::TestDeepSchedulerIntegration -v

# 运行单个测试
./venv/bin/python -m pytest tests/test_deep_core.py::TestDeepSchedulerIntegration::test_scheduler_full_workflow -v

# 运行特定模式的测试
./venv/bin/python -m pytest tests/ -k "scheduler" -v

# 并行加速测试
./venv/bin/python -m pytest tests/ -n auto
```

### 测试选项

```bash
# 详细输出
./venv/bin/python -m pytest tests/ -v

# 详细日志
./venv/bin/python -m pytest tests/ -v -s

# 失败后停止
./venv/bin/python -m pytest tests/ -x

# 失败后进入调试器
./venv/bin/python -m pytest tests/ --pdb

# 显示慢测试
./venv/bin/python -m pytest tests/ -v --durations=10
```

## 测试覆盖率

```bash
# 安装 coverage
pip install pytest-cov

# 生成覆盖率报告
./venv/bin/python -m pytest tests/ --cov=core --cov=swarm --cov-report=html

# 查看覆盖率摘要
./venv/bin/python -m pytest tests/ --cov=core --cov=swarm --cov-report=term

# 生成 XML 报告 (CI/CD)
./venv/bin/python -m pytest tests/ --cov=core --cov=swarm --cov-report=xml
```

## 持续集成

### GitHub Actions 示例

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest-cov

    - name: Run deep tests
      run: ./tests/run_daily_tests.sh

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
```

## 编写测试

### Mock Agent 示例

```python
class MockAgent:
    """模拟 Agent 用于测试"""

    def __init__(
        self,
        name: str,
        skills: List[str] = None,
        delay: float = 0.05
    ):
        self.name = name
        self.skills = skills or ["general"]
        self.delay = delay
        self._call_count = 0

    def run(self, task_input: str, verbose: bool = True) -> str:
        self._call_count += 1
        time.sleep(self.delay)
        return f"[{self.name}] 处理：{task_input}"

    @property
    def call_count(self) -> int:
        return self._call_count
```

### 测试示例

```python
import pytest
import asyncio
from simple_agent.core.dynamic_scheduler import create_scheduler, TaskPriority

class TestSchedulerBasic:
    """基础调度器测试"""

    def test_scheduler_creation(self):
        """测试调度器创建"""
        agents = [MockAgent("agent1")]
        scheduler = create_scheduler(agents=agents, max_concurrent=3)
        assert scheduler is not None

    def test_register_agent(self):
        """测试 Agent 注册"""
        scheduler = create_scheduler(agents=[], max_concurrent=3)
        agent = MockAgent("new_agent")
        scheduler.register_agent(agent)
        assert "new_agent" in scheduler.agents

    @pytest.mark.asyncio
    async def test_execute_task(self):
        """测试任务执行"""
        agent = MockAgent("executor", delay=0.01)
        scheduler = create_scheduler(agents=[agent], max_concurrent=3)
        scheduler.add_task("task1", "测试任务")

        results = await scheduler.schedule_and_execute(
            agent_pool=[agent],
            parallel=True
        )

        assert len(results) == 1
        assert results["task1"].success is True
```

## 性能基准

当前性能指标 (参考值)：

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 调度器吞吐量 | > 50 任务/秒 | 100 个任务，10 个 Agent |
| 并行效率 | > 5x | 10 个并发任务 |
| 日常测试时间 | < 30 秒 | run_daily_tests.sh |
| 快速测试时间 | < 5 分钟 | run_quick_tests.sh |

## 故障排查

### 常见问题

**Q: 测试超时**

```bash
# 增加超时时间 (pytest-timeout)
pip install pytest-timeout
./venv/bin/python -m pytest tests/ --timeout=60
```

**Q: 异步测试失败**

```bash
# 确保 asyncio 模式正确
./venv/bin/python -m pytest tests/ --asyncio-mode=auto
```

**Q: 测试依赖失败**

```bash
# 清理 __pycache__
find tests/ -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# 重新运行
./venv/bin/python -m pytest tests/ --cache-clear
```

**Q: 内存泄漏**

```bash
# 使用 pytest-leaks 检测
pip install pytest-leaks
./venv/bin/python -m pytest tests/ --leaks
```

## 测试最佳实践

1. **测试独立性**: 每个测试应独立运行，不依赖其他测试的状态

2. **Mock 外部依赖**: 使用 Mock Agent 模拟 LLM、API 等外部依赖

3. **覆盖边界条件**: 测试空输入、超时、失败等边界情况

4. **保持测试快速**: 单个测试应在 1 秒内完成，使用 delay=0.01 等小技巧

5. **有意义的断言**: 断言应清晰表达测试意图，便于调试

6. **定期清理**: 删除过时的测试，保持测试集精简
