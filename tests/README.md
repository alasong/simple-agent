# 测试指南 (Testing Guide)

## 测试概览

项目共有 **122 个测试**，覆盖核心调度器、并行工作流、Swarm 编排等关键组件。

## 快速开始

### 运行日常测试 (推荐每日执行)

```bash
# 日常核心测试 (约 30 秒)
./tests/run_daily_tests.sh
```

### 运行快速测试 (5 分钟内)

```bash
# 快速验证核心功能
./tests/run_quick_tests.sh
```

### 运行完整测试套件

```bash
# 完整测试 (约 5-10 分钟)
./tests/run_all_tests.sh
```

## 测试文件结构

### 核心深度测试 (推荐)

| 文件 | 测试数 | 说明 |
|------|--------|------|
| `test_deep_core.py` | 14 | 核心组件深度集成测试 |

**测试分类**:
- `TestDeepSchedulerIntegration` (3 个) - 动态调度器集成
- `TestDeepWorkflowParallel` (3 个) - 并行工作流
- `TestDeepSwarmOrchestration` (3 个) - Swarm 编排
- `TestDeepSystemStability` (3 个) - 系统稳定性
- `TestPerformanceBenchmarks` (2 个) - 性能基准

### 组件测试

| 文件 | 测试数 | 说明 |
|------|--------|------|
| `test_dynamic_scheduler.py` | 29 | 动态调度器单元测试 |
| `test_workflow_parallel.py` | 30 | 并行工作流单元测试 |
| `test_swarm_integration.py` | 16 | Swarm 集成测试 |

### 工具测试

| 文件 | 说明 |
|------|------|
| `test_tool_execution.py` | 工具执行测试 |
| `test_domains.py` | 领域测试 |
| `test_agents.py` | Agent 测试 |

### 其他测试

| 文件 | 说明 |
|------|------|
| `test_workflow_integration.py` | 工作流集成测试 |
| `test_swarm_concurrent.py` | Swarm 并发测试 |
| `test_scaling.py` | 扩展测试 |
| `test_task_queue.py` | 任务队列测试 |

## 运行单个测试

```bash
# 运行单个测试文件
./venv/bin/python -m pytest tests/test_deep_core.py -v

# 运行单个测试类
./venv/bin/python -m pytest tests/test_deep_core.py::TestDeepSchedulerIntegration -v

# 运行单个测试
./venv/bin/python -m pytest tests/test_deep_core.py::TestDeepSchedulerIntegration::test_scheduler_full_workflow -v

# 运行特定模式的测试
./venv/bin/python -m pytest tests/ -k "scheduler" -v
```

## 测试覆盖率

```bash
# 生成覆盖率报告
./venv/bin/python -m pytest tests/ --cov=core --cov=swarm --cov-report=html

# 查看覆盖率摘要
./venv/bin/python -m pytest tests/ --cov=core --cov=swarm --cov-report=term
```

## 持续集成

### GitHub Actions 配置

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run deep tests
        run: ./tests/run_daily_tests.sh
```

## 测试最佳实践

### 1. 编写测试

- 使用 MockAgent 模拟外部依赖
- 测试应独立、可重复执行
- 覆盖正常路径和异常路径
- 包含边界条件测试

### 2. 运行测试

- 开发时运行快速测试
- 提交前运行日常测试
- 发布前运行完整测试套件

### 3. 调试测试

```bash
# 详细输出
./venv/bin/python -m pytest tests/test_deep_core.py -v -s

# 失败时进入调试器
./venv/bin/python -m pytest tests/test_deep_core.py --pdb

# 打印日志
./venv/bin/python -m pytest tests/test_deep_core.py -v --log-cli-level=DEBUG
```

## 性能基准

当前性能指标:

- 调度器吞吐量：> 50 任务/秒
- 并行效率：> 5x (10 个并发任务)
- 日常测试执行时间：< 30 秒

## 故障排查

### 常见问题

**Q: 测试超时**
```bash
# 增加超时时间
./venv/bin/python -m pytest tests/ -v --timeout=60
```

**Q: 异步测试失败**
```bash
# 确保使用 asyncio 模式
./venv/bin/python -m pytest tests/ -v --asyncio-mode=auto
```

**Q: 资源泄漏**
```bash
# 运行资源清理测试
./venv/bin/python -m pytest tests/test_deep_core.py::TestDeepSystemStability -v
```
