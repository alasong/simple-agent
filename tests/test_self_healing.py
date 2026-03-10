"""
Self-Healing Tests - 自愈能力测试

测试 Agent 的自愈能力：
1. 异常定位和诊断
2. 自动重新生成 Agent
3. 继续执行未完成的任务
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestExceptionDiagnoser:
    """测试异常诊断器"""

    def test_network_error_diagnosis(self):
        """测试网络错误诊断"""
        from core.self_healing import ExceptionDiagnoser, ExceptionType

        diagnoser = ExceptionDiagnoser()

        # 模拟网络错误
        exception = ConnectionError("连接被拒绝")
        context = {"agent_name": "TestAgent", "task_description": "测试任务"}

        report = diagnoser.diagnose(exception, context)

        assert report.exception_type == ExceptionType.NETWORK_ERROR
        assert report.agent_name == "TestAgent"
        assert len(report.recovery_suggestions) > 0

    def test_timeout_error_diagnosis(self):
        """测试超时错误诊断"""
        from core.self_healing import ExceptionDiagnoser, ExceptionType

        diagnoser = ExceptionDiagnoser()

        exception = TimeoutError("请求超时")
        context = {"agent_name": "TestAgent", "task_description": "测试任务"}

        report = diagnoser.diagnose(exception, context)

        assert report.exception_type == ExceptionType.TIMEOUT_ERROR
        assert "超时" in report.error_message or "timeout" in report.error_message.lower()

    def test_recovery_suggestions_generation(self):
        """测试恢复建议生成"""
        from core.self_healing import ExceptionDiagnoser, ExceptionType

        diagnoser = ExceptionDiagnoser()

        # 网络错误
        exception = ConnectionError("无法连接到 API")
        context = {"agent_name": "TestAgent", "task_description": "测试任务"}
        report = diagnoser.diagnose(exception, context)

        assert len(report.recovery_suggestions) > 0
        assert any("网络" in s or "连接" in s for s in report.recovery_suggestions)


class TestRecoveryStrategy:
    """测试恢复策略选择"""

    def test_retry_strategy_for_timeout(self):
        """测试超时错误选择重试策略"""
        from core.self_healing import (
            SelfHealingCoordinator, ExceptionType, ExceptionReport, RecoveryStrategy
        )

        coordinator = SelfHealingCoordinator()

        # 模拟超时错误报告
        report = ExceptionReport(
            exception_type=ExceptionType.TIMEOUT_ERROR,
            error_message="请求超时",
            stack_trace="",
            agent_name="TestAgent",
            task_description="测试任务",
            timestamp="2026-03-10T12:00:00"
        )

        strategy = coordinator._select_recovery_strategy(report)

        # 超时应该选择重试
        assert strategy in [RecoveryStrategy.RETRY, RecoveryStrategy.REGENERATE_AGENT]

    def test_regenerate_strategy_for_crash(self):
        """测试崩溃错误选择重新生成策略"""
        from core.self_healing import (
            SelfHealingCoordinator, ExceptionType, ExceptionReport, RecoveryStrategy
        )

        coordinator = SelfHealingCoordinator()

        report = ExceptionReport(
            exception_type=ExceptionType.AGENT_CRASH,
            error_message="Agent 崩溃",
            stack_trace="",
            agent_name="TestAgent",
            task_description="测试任务",
            timestamp="2026-03-10T12:00:00"
        )

        strategy = coordinator._select_recovery_strategy(report)

        assert strategy == RecoveryStrategy.REGENERATE_AGENT


class TestAgentRegenerator:
    """测试 Agent 重新生成器"""

    def test_clone_agent(self):
        """测试克隆 Agent"""
        from core.self_healing import AgentRegenerator
        from core.agent import Agent

        regenerator = AgentRegenerator()

        # 创建原始 Agent
        original = Agent(
            name="TestAgent",
            max_iterations=5,
            instance_id="test-001"
        )

        # 克隆（clone 会生成新的 instance_id）
        cloned = regenerator._clone_agent(original)

        # 验证基本属性保持一致
        assert cloned.name == original.name
        assert cloned.max_iterations == original.max_iterations
        # 注意：clone 会生成新的 instance_id，用于隔离
        assert cloned.instance_id != original.instance_id or cloned.instance_id is None

    def test_regenerate_with_adjusted_config(self):
        """测试调整配置后重新生成"""
        from core.self_healing import AgentRegenerator
        from core.agent import Agent

        regenerator = AgentRegenerator()

        original = Agent(
            name="TestAgent",
            max_iterations=5,
            instance_id="test-001"
        )

        # 调整配置后重新生成
        new_agent = regenerator._regenerate_with_adjusted_config(original)

        # 迭代次数应该增加
        assert new_agent.max_iterations > original.max_iterations
        assert new_agent.instance_id != original.instance_id

    def test_switch_to_backup_agent(self):
        """测试切换到备用 Agent"""
        from core.self_healing import AgentRegenerator
        from core.agent import Agent

        regenerator = AgentRegenerator()

        original = Agent(
            name="Planner",
            max_iterations=5,
            instance_id="test-001"
        )

        # 应该返回一个备用 Agent（或新的同类型 Agent）
        backup = regenerator._switch_to_backup_agent(original)

        # 备用 Agent 应该是有效的 Agent 实例
        assert backup is not None
        assert hasattr(backup, 'name')
        assert hasattr(backup, 'run')


class TestTaskResumer:
    """测试任务恢复器"""

    def test_save_and_load_checkpoint(self, tmp_path):
        """测试保存和加载断点"""
        from core.self_healing import TaskResumer, ExecutionCheckpoint
        from core.agent import Agent

        checkpoint_dir = str(tmp_path / "checkpoints")
        resumer = TaskResumer(checkpoint_dir=checkpoint_dir)

        # 创建测试 Agent
        agent = Agent(name="TestAgent", instance_id="test-001")

        # 保存断点
        resumer.save_checkpoint(
            task_id="test-task-001",
            agent=agent,
            iteration=3,
            memory_messages=[{"role": "user", "content": "测试"}],
            pending_actions=[{"name": "tool1", "arguments": {}}],
            completed_actions=[]
        )

        # 加载断点
        checkpoint = resumer.load_checkpoint("test-task-001")

        assert checkpoint is not None
        assert checkpoint.task_id == "test-task-001"
        assert checkpoint.iteration == 3

    def test_clear_checkpoint(self, tmp_path):
        """测试清除断点"""
        from core.self_healing import TaskResumer
        from core.agent import Agent

        checkpoint_dir = str(tmp_path / "checkpoints")
        resumer = TaskResumer(checkpoint_dir=checkpoint_dir)
        agent = Agent(name="TestAgent")

        # 保存后清除
        resumer.save_checkpoint(
            task_id="test-task-002",
            agent=agent,
            iteration=1,
            memory_messages=[],
            pending_actions=[],
            completed_actions=[]
        )

        resumer.clear_checkpoint("test-task-002")

        # 清除后应该返回 None
        checkpoint = resumer.load_checkpoint("test-task-002")
        assert checkpoint is None


class TestSelfHealingCoordinator:
    """测试自愈协调器"""

    def test_handle_exception_flow(self):
        """测试异常处理流程"""
        from core.self_healing import (
            SelfHealingCoordinator, ExceptionType, ExceptionReport
        )
        from core.agent import Agent

        coordinator = SelfHealingCoordinator()
        agent = Agent(name="TestAgent")

        # 模拟异常
        exception = ConnectionError("连接失败")

        result = coordinator.handle_exception(
            agent=agent,
            exception=exception,
            task_description="测试任务"
        )

        # 验证恢复结果
        assert result is not None
        assert result.strategy is not None
        assert result.attempts >= 1

    def test_recovery_with_multiple_failures(self):
        """测试多次失败后的恢复"""
        from core.self_healing import SelfHealingCoordinator
        from core.agent import Agent

        coordinator = SelfHealingCoordinator()
        agent = Agent(name="Developer", max_iterations=5)

        # 模拟多次失败
        for i in range(3):
            exception = TimeoutError(f"超时 {i}")
            result = coordinator.handle_exception(
                agent=agent,
                exception=exception,
                task_description="测试任务"
            )

            # 每次都应该有恢复策略
            assert result is not None


class TestSelfHealingIntegration:
    """自愈集成测试"""

    def test_agent_with_self_healing_enabled(self):
        """测试启用自愈能力的 Agent"""
        from core.agent import Agent
        from core.tool import ToolResult

        # 创建一个简单的 Mock 工具
        class MockTool:
            name = "MockTool"

            def execute(self, **kwargs):
                # 第一次调用失败，第二次成功
                if not hasattr(self, 'called'):
                    self.called = True
                    return ToolResult(success=False, error="模拟失败")
                return ToolResult(success=True, output="成功")

        agent = Agent(
            name="TestAgent",
            max_iterations=5,
            tools=[MockTool()]
        )

        # 启用自愈能力运行
        # 注意：这是一个简化测试，实际自愈需要真实的异常场景
        result = agent.run(
            "测试任务",
            verbose=False,
            enable_self_healing=True
        )

        # 应该能够完成执行（即使工具失败）
        assert result is not None


class TestCheckpointPersistence:
    """测试断点持久化"""

    def test_checkpoint_file_format(self, tmp_path):
        """测试断点文件格式"""
        from core.self_healing import TaskResumer
        from core.agent import Agent
        import json

        checkpoint_dir = str(tmp_path / "checkpoints")
        resumer = TaskResumer(checkpoint_dir=checkpoint_dir)
        agent = Agent(name="TestAgent")

        # 保存断点
        resumer.save_checkpoint(
            task_id="format-test-001",
            agent=agent,
            iteration=2,
            memory_messages=[{"role": "user", "content": "测试"}],
            pending_actions=[],
            completed_actions=[]
        )

        # 检查文件内容
        import os
        checkpoint_file = os.path.join(checkpoint_dir, "format-test-001.json")
        assert os.path.exists(checkpoint_file)

        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 验证格式
        assert "task_id" in data
        assert "iteration" in data
        assert "memory_messages" in data
        assert "timestamp" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
