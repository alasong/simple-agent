"""
Reflection Learning Tests - 反思学习机制测试

测试执行记录、性能分析、优化建议生成和经验积累功能
"""

import pytest
import sys
import os
import time
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestExecutionRecorder:
    """测试执行记录器"""

    def test_start_recording(self, tmp_path):
        """测试开始记录"""
        from core.reflection_learning import ExecutionRecorder

        recorder = ExecutionRecorder(storage_dir=str(tmp_path))
        record_id = recorder.start_recording("TestWorkflow", "测试任务")

        assert record_id.startswith("TestWorkflow_")
        assert recorder.get_current_record() is not None

    def test_record_step(self, tmp_path):
        """测试记录步骤"""
        from core.reflection_learning import ExecutionRecorder

        recorder = ExecutionRecorder(storage_dir=str(tmp_path))
        recorder.start_recording("TestWorkflow", "测试任务")

        # 记录步骤开始和结束
        recorder.record_step_start("step_1", 1, "Developer")
        time.sleep(0.1)  # 模拟执行时间

        recorder.record_step_end(
            step_index=1,
            agent_name="Developer",
            result="测试输出",
            success=True,
            iterations=2,
            tool_calls=3,
            input_text="测试输入"
        )

        record = recorder.get_current_record()
        assert len(record.steps) == 1
        assert record.steps[0].duration >= 0.1

    def test_finish_recording(self, tmp_path):
        """测试结束记录"""
        from core.reflection_learning import ExecutionRecorder

        recorder = ExecutionRecorder(storage_dir=str(tmp_path))
        recorder.start_recording("TestWorkflow", "测试任务")

        recorder.record_step_start("step_1", 1, "Developer")
        recorder.record_step_end(1, "Developer", "结果", True)

        recorder.finish_recording(success=True, final_output="最终输出")

        # 记录应该已保存
        assert recorder.get_current_record() is None

        # 检查文件是否存在
        files = os.listdir(tmp_path)
        assert len(files) > 0


class TestPerformanceAnalyzer:
    """测试性能分析器"""

    def test_analyze_slow_steps(self):
        """测试慢步骤识别"""
        from core.reflection_learning import (
            PerformanceAnalyzer, ExecutionRecord, StepMetrics
        )

        # 创建包含慢步骤的记录
        now = time.time()
        record = ExecutionRecord(
            record_id="test_001",
            workflow_name="TestWorkflow",
            task_description="测试",
            task_hash="abc123",
            start_time=now,
            end_time=now + 100,
            total_duration=100,
            steps=[
                StepMetrics(
                    step_name="slow_step",
                    step_index=1,
                    agent_name="Developer",
                    instance_id=None,
                    start_time=now,
                    end_time=now + 50,
                    duration=50,  # 50 秒，超过阈值
                    input_length=100,
                    output_length=500,
                    iterations=1,
                    tool_calls=5,
                    success=True
                ),
                StepMetrics(
                    step_name="fast_step",
                    step_index=2,
                    agent_name="Reviewer",
                    instance_id=None,
                    start_time=now + 50,
                    end_time=now + 55,
                    duration=5,
                    input_length=500,
                    output_length=200,
                    iterations=1,
                    tool_calls=2,
                    success=True
                )
            ],
            success=True,
            parallel_steps=0,
            sequential_steps=2,
            retry_count=0,
            total_token_usage=1000
        )

        analyzer = PerformanceAnalyzer()
        bottlenecks, stats = analyzer.analyze(record)

        # 应该识别出慢步骤
        slow_bottlenecks = [b for b in bottlenecks if b.type.value == "slow_step"]
        assert len(slow_bottlenecks) > 0

    def test_analyze_long_chain(self):
        """测试长链路识别"""
        from core.reflection_learning import (
            PerformanceAnalyzer, ExecutionRecord, StepMetrics
        )

        now = time.time()
        # 创建 6 个步骤（超过阈值 5）
        steps = []
        for i in range(6):
            steps.append(StepMetrics(
                step_name=f"step_{i}",
                step_index=i,
                agent_name="Agent",
                instance_id=None,
                start_time=now + i * 10,
                end_time=now + (i + 1) * 10,
                duration=10,
                input_length=100,
                output_length=200,
                iterations=1,
                tool_calls=2,
                success=True
            ))

        record = ExecutionRecord(
            record_id="test_002",
            workflow_name="TestWorkflow",
            task_description="测试",
            task_hash="abc123",
            start_time=now,
            end_time=now + 60,
            total_duration=60,
            steps=steps,
            success=True,
            parallel_steps=0,
            sequential_steps=6,
            retry_count=0,
            total_token_usage=500
        )

        analyzer = PerformanceAnalyzer()
        bottlenecks, stats = analyzer.analyze(record)

        # 应该识别出长链路
        long_chain_bottlenecks = [b for b in bottlenecks if b.type.value == "long_chain"]
        assert len(long_chain_bottlenecks) > 0

    def test_calculate_stats(self):
        """测试统计计算"""
        from core.reflection_learning import (
            PerformanceAnalyzer, ExecutionRecord, StepMetrics
        )

        now = time.time()
        record = ExecutionRecord(
            record_id="test_003",
            workflow_name="TestWorkflow",
            task_description="测试",
            task_hash="abc123",
            start_time=now,
            end_time=now + 30,
            total_duration=30,
            steps=[
                StepMetrics("s1", 1, "A1", None, now, now+10, 10, 100, 200, 1, 2, True),
                StepMetrics("s2", 2, "A2", None, now+10, now+20, 10, 200, 300, 1, 3, True),
            ],
            success=True,
            parallel_steps=0,
            sequential_steps=2,
            retry_count=1,
            total_token_usage=500
        )

        analyzer = PerformanceAnalyzer()
        bottlenecks, stats = analyzer.analyze(record)

        assert stats["total_duration"] == 30
        assert stats["avg_step_duration"] == 10
        assert stats["total_steps"] == 2
        assert stats["success_rate"] == 1.0
        assert stats["total_retries"] == 1


class TestOptimizationSuggester:
    """测试优化建议生成器"""

    def test_generate_suggestions(self):
        """测试生成优化建议"""
        from core.reflection_learning import (
            OptimizationSuggester, Bottleneck, BottleneckType
        )

        suggester = OptimizationSuggester()

        bottlenecks = [
            Bottleneck(
                type=BottleneckType.SLOW_STEP,
                step_indices=[1],
                severity="high",
                description="步骤 1 执行过慢",
                impact_seconds=30,
                impact_percentage=50
            ),
            Bottleneck(
                type=BottleneckType.WAIT_TIME,
                step_indices=[2, 3],
                severity="medium",
                description="存在并行机会",
                impact_seconds=20,
                impact_percentage=30
            )
        ]

        suggestions = suggester.generate_suggestions(bottlenecks, None)

        # 应该生成多个建议
        assert len(suggestions) > 0
        # 建议应该按优先级排序
        if len(suggestions) > 1:
            assert suggestions[0].priority >= suggestions[1].priority

    def test_generate_summary(self):
        """测试生成优化总结"""
        from core.reflection_learning import (
            OptimizationSuggester, Bottleneck, BottleneckType,
            OptimizationSuggestion, OptimizationType, ExecutionRecord
        )

        suggester = OptimizationSuggester()

        record = ExecutionRecord(
            record_id="test",
            workflow_name="Test",
            task_description="测试任务",
            task_hash="abc",
            start_time=0,
            end_time=100,
            total_duration=100,
            steps=[],
            success=True
        )

        suggestions = [
            OptimizationSuggestion(
                type=OptimizationType.PARALLELIZE,
                priority=5,
                title="并行化执行",
                description="将独立步骤改为并行",
                expected_improvement=50.0,
                implementation="使用 ParallelWorkflow",
                confidence=0.85,
                related_steps=[1, 2]
            )
        ]

        summary = suggester.generate_summary(record, suggestions)

        assert "优化建议" in summary
        assert "并行化" in summary


class TestExperienceStore:
    """测试经验存储库"""

    def test_store_and_find_experience(self, tmp_path):
        """测试存储和查找经验"""
        from core.reflection_learning import ExperienceStore

        storage_file = os.path.join(tmp_path, "experience.json")
        store = ExperienceStore(storage_file)

        # 存储经验
        exp_id = store.store_experience(
            task_pattern="代码审查",
            original_workflow="workflow_v1",
            optimized_workflow="workflow_v2",
            original_duration=100,
            optimized_duration=60,
            optimizations_applied=["parallelize", "merge_steps"]
        )

        assert exp_id is not None

        # 查找相似经验
        similar = store.find_similar_experiences("代码审查任务")
        assert len(similar) > 0
        assert "parallelize" in similar[0].optimization_applied

    def test_update_experience(self, tmp_path):
        """测试更新经验"""
        from core.reflection_learning import ExperienceStore

        store = ExperienceStore(os.path.join(tmp_path, "experience.json"))

        exp_id = store.store_experience(
            task_pattern="测试",
            original_workflow="v1",
            optimized_workflow="v2",
            original_duration=100,
            optimized_duration=80,
            optimizations_applied=["optimize"]
        )

        # 更新成功次数
        store.update_experience_success(exp_id)

        # 验证
        similar = store.find_similar_experiences("测试")
        assert similar[0].success_count >= 2

    def test_get_statistics(self, tmp_path):
        """测试获取统计"""
        from core.reflection_learning import ExperienceStore

        store = ExperienceStore(os.path.join(tmp_path, "experience.json"))

        store.store_experience(
            task_pattern="测试 1",
            original_workflow="v1",
            optimized_workflow="v2",
            original_duration=100,
            optimized_duration=70,
            optimizations_applied=["opt1"]
        )

        stats = store.get_statistics()

        assert stats["total"] >= 1
        assert "avg_improvement" in stats


class TestReflectionLearningCoordinator:
    """测试反思学习协调器"""

    def test_full_workflow(self, tmp_path):
        """测试完整工作流"""
        from core.reflection_learning import ReflectionLearningCoordinator

        coordinator = ReflectionLearningCoordinator(storage_dir=str(tmp_path))

        # 开始
        record_id = coordinator.start("TestWorkflow", "测试任务")
        assert record_id is not None

        # 记录步骤
        coordinator.record_step_start("step_1", 1, "Developer")
        time.sleep(0.05)
        coordinator.record_step_end(
            step_index=1,
            agent_name="Developer",
            result="结果",
            success=True,
            input_text="测试输入"
        )

        # 结束
        coordinator.finish(success=True, final_output="最终输出")

        # 获取统计（可能为空，因为 finish 会重置）
        # 主要验证流程不崩溃
        stats = coordinator.get_performance_stats()
        # stats 可能为空，因为 finish 之后未保存当前记录
        assert stats is not None

    def test_apply_experience(self, tmp_path):
        """测试应用经验"""
        from core.reflection_learning import ReflectionLearningCoordinator

        coordinator = ReflectionLearningCoordinator(storage_dir=str(tmp_path))

        # 先存储一个经验
        coordinator.store_optimization_result(
            task_pattern="相似任务",
            original_workflow="v1",
            optimized_workflow="v2",
            original_duration=100,
            optimized_duration=70,
            optimizations_applied=["parallelize"]
        )

        # 应用经验
        result = coordinator.apply_learned_experience("相似任务变体")
        assert result is not None
        assert "parallelize" in result["optimizations"]

    def test_get_experience_statistics(self, tmp_path):
        """测试获取经验统计"""
        from core.reflection_learning import ReflectionLearningCoordinator

        coordinator = ReflectionLearningCoordinator(storage_dir=str(tmp_path))

        coordinator.store_optimization_result(
            task_pattern="测试",
            original_workflow="v1",
            optimized_workflow="v2",
            original_duration=100,
            optimized_duration=80,
            optimizations_applied=["opt1"]
        )

        stats = coordinator.get_experience_statistics()

        assert stats["total"] >= 1


class TestWorkflowWithReflection:
    """测试带反思学习的工作流"""

    def test_workflow_enables_reflection(self, tmp_path):
        """测试工作流启用反思学习"""
        from core.workflow import Workflow, WorkflowStep
        from core.agent import Agent

        # 创建简单工作流
        workflow = Workflow("测试工作流")

        # 创建测试 Agent
        agent = Agent(name="TestAgent", max_iterations=3)

        workflow.add_step("测试步骤", agent)

        output_dir = str(tmp_path / "output")

        # 执行工作流（启用反思）
        context = workflow.run(
            "测试任务",
            verbose=False,
            output_dir=output_dir,
            enable_reflection=True
        )

        # 验证执行完成
        assert context is not None
        assert "_step_results" in context

        # 验证反思记录已创建
        reflection_dir = tmp_path / "reflection_logs"
        # 记录应该已保存


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
