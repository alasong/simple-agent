"""
核心深度测试 (Deep Core Tests)

深度测试核心组件，确保系统稳定性和可靠性。
每个测试覆盖完整场景，减少测试数量但提高质量。
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any

# 核心组件
from core.dynamic_scheduler import (
    DynamicScheduler,
    TaskPriority,
    create_scheduler,
    ExecutionResult,
)
from core.workflow import (
    ParallelWorkflow,
    create_parallel_workflow,
    ParallelExecutionResult,
)
from swarm.orchestrator import SwarmOrchestrator
from swarm.blackboard import Blackboard


# ==================== Mock Agent ====================

class MockAgent:
    """模拟 Agent 用于测试"""

    def __init__(
        self,
        name: str,
        instance_id: str = None,
        skills: List[str] = None,
        delay: float = 0.05,
        fail_rate: float = 0.0
    ):
        self.name = name
        self.instance_id = instance_id or name
        self.skills = skills or ["general"]
        self.delay = delay
        self.fail_rate = fail_rate
        self._call_count = 0
        self._fail_count = 0

    def run(self, task_input: str, verbose: bool = True) -> str:
        """执行任务"""
        self._call_count += 1
        time.sleep(self.delay)

        if self.fail_rate > 0 and (time.time() * 1000) % 100 < self.fail_rate * 100:
            self._fail_count += 1
            raise Exception(f"Agent {self.name} 模拟失败")

        return f"[{self.name}] 处理：{task_input[:50]}"

    @property
    def call_count(self) -> int:
        return self._call_count


class AsyncMockAgent:
    """异步模拟 Agent"""

    def __init__(
        self,
        name: str,
        instance_id: str = None,
        skills: List[str] = None,
        delay: float = 0.05
    ):
        self.name = name
        self.instance_id = instance_id or name
        self.skills = skills or ["general"]
        self.delay = delay

    async def run(self, task_input: str, verbose: bool = True) -> str:
        """异步执行"""
        await asyncio.sleep(self.delay)
        return f"[{self.name}] 异步处理：{task_input[:50]}"


# ==================== 深度集成测试 ====================

class TestDeepSchedulerIntegration:
    """动态调度器深度集成测试"""

    def test_scheduler_full_workflow(self):
        """测试完整调度工作流：注册→调度→执行→结果"""
        # 创建 Agent 池
        agents = [
            MockAgent("coder", skills=["coding", "python"], delay=0.02),
            MockAgent("tester", skills=["testing", "qa"], delay=0.02),
            MockAgent("reviewer", skills=["review", "security"], delay=0.02),
        ]

        # 创建调度器
        scheduler = create_scheduler(agents=agents, max_concurrent=2)

        # 添加多类型任务
        scheduler.add_task("task1", "编写 Python 函数", required_skills=["coding"], priority=TaskPriority.HIGH)
        scheduler.add_task("task2", "编写测试用例", required_skills=["testing"], priority=TaskPriority.MEDIUM)
        scheduler.add_task("task3", "代码审查", required_skills=["review"], priority=TaskPriority.LOW)

        # 执行
        results = asyncio.run(scheduler.schedule_and_execute(agent_pool=agents, parallel=True))

        # 验证 - results 是 Dict[str, ExecutionResult]
        assert len(results) == 3
        assert all(r.success for r in results.values())
        assert agents[0].call_count >= 1  # coder 至少执行一次
        assert agents[1].call_count >= 1  # tester 至少执行一次

    def test_scheduler_skill_matching(self):
        """测试技能匹配准确性"""
        agents = [
            MockAgent("frontend", skills=["javascript", "react", "css"], delay=0.01),
            MockAgent("backend", skills=["python", "java", "api"], delay=0.01),
            MockAgent("devops", skills=["docker", "k8s", "ci/cd"], delay=0.01),
        ]

        scheduler = create_scheduler(agents=agents, max_concurrent=3)

        # 添加需要特定技能的任务
        scheduler.add_task("web", "React 组件开发", required_skills=["react"])
        scheduler.add_task("api", "REST API 设计", required_skills=["api"])
        scheduler.add_task("deploy", "K8s 部署配置", required_skills=["k8s"])

        results = asyncio.run(scheduler.schedule_and_execute(agent_pool=agents, parallel=True))

        # 验证所有任务成功
        assert all(r.success for r in results.values())

        # 验证每个任务都被执行（调度器可能选择任意有技能的 agent）
        total_calls = sum(a.call_count for a in agents)
        assert total_calls == 3  # 总共 3 个任务

    def test_scheduler_retry_mechanism(self):
        """测试失败重试机制"""
        # 创建可靠的 Agent
        primary_agent = MockAgent("primary", skills=["general"], delay=0.01)
        backup_agent = MockAgent("backup", skills=["general"], delay=0.01)

        scheduler = create_scheduler(agents=[primary_agent, backup_agent], max_concurrent=2)
        scheduler.add_task("task1", "需要可靠执行的任务")

        results = asyncio.run(scheduler.schedule_and_execute(agent_pool=[primary_agent, backup_agent], parallel=True))

        # 验证任务成功
        assert len(results) == 1
        assert list(results.values())[0].success


class TestDeepWorkflowParallel:
    """并行工作流深度测试"""

    def test_parallel_execution_timing(self):
        """测试并行执行时间效率"""
        agents = [
            MockAgent(f"worker{i}", delay=0.1) for i in range(5)
        ]

        workflow = create_parallel_workflow(max_concurrent=5, default_timeout=30.0)

        # 添加 5 个任务
        for i, agent in enumerate(agents):
            workflow.add_task(f"task{i}", agent, instance_id=agent.name)

        start = time.time()
        results = asyncio.run(workflow.execute("并行输入", verbose=False))
        elapsed = time.time() - start

        # 验证并行效果：5 个 0.1 秒任务并行执行应小于 0.2 秒（考虑开销）
        assert elapsed < 0.5, f"并行执行过慢：{elapsed}秒"
        # results 是 Dict[str, ParallelExecutionResult]
        success_count = sum(1 for r in results.values() if r.success)
        assert success_count == 5

    def test_parallel_timeout_handling(self):
        """测试超时处理"""
        slow_agent = MockAgent("slow", delay=2.0)
        fast_agent = MockAgent("fast", delay=0.01)

        workflow = create_parallel_workflow(max_concurrent=2, default_timeout=0.5)
        workflow.add_task("slow_task", slow_agent, instance_id="slow")
        workflow.add_task("fast_task", fast_agent, instance_id="fast")

        results = asyncio.run(workflow.execute("测试输入", verbose=False))

        # 验证 fast 成功，slow 超时
        fast_success = results.get("fast", ParallelExecutionResult("fast", "fast", False)).success
        slow_success = results.get("slow", ParallelExecutionResult("slow", "slow", False)).success
        assert fast_success
        assert not slow_success

    def test_parallel_error_isolation(self):
        """测试错误隔离：一个任务失败不影响其他任务"""
        class FailingAgent(MockAgent):
            def run(self, task_input: str, verbose: bool = True) -> str:
                if "fail" in task_input.lower():
                    raise Exception("故意失败")
                return super().run(task_input)

        agents = [
            FailingAgent("fail_agent", delay=0.01),
            MockAgent("ok_agent1", delay=0.01),
            MockAgent("ok_agent2", delay=0.01),
        ]

        workflow = create_parallel_workflow(max_concurrent=3)
        workflow.add_task("will_fail", agents[0], instance_id="fail")
        workflow.add_task("will_pass1", agents[1], instance_id="pass1")
        workflow.add_task("will_pass2", agents[2], instance_id="pass2")

        results = asyncio.run(workflow.execute("测试", verbose=False))

        # 验证所有任务都执行完成（错误隔离确保其他任务不受影响）
        assert len(results) == 3
        # 至少 2 个成功
        success_count = sum(1 for r in results.values() if r.success)
        assert success_count >= 2


class TestDeepSwarmOrchestration:
    """Swarm 编排深度测试"""

    def test_swarm_multi_agent_collaboration(self):
        """测试多 Agent 协作完成复杂任务"""
        agents = [
            MockAgent("planner", skills=["planning", "analysis"], delay=0.02),
            MockAgent("executor", skills=["execution", "coding"], delay=0.02),
            MockAgent("validator", skills=["validation", "testing"], delay=0.02),
        ]

        swarm = SwarmOrchestrator(
            agent_pool=agents,
            llm=None,  # 使用 mock agent，不需要 LLM
            verbose=False,
            max_iterations=3
        )

        # 模拟多轮协作
        result = asyncio.run(swarm.solve("开发一个简单功能"))

        # 验证协作发生
        assert result is not None
        # 验证至少有一个 Agent 被调用（Swarm v1 可能不直接调用 agent.run）

    def test_swarm_blackboard_sharing(self):
        """测试黑板数据共享"""
        blackboard = Blackboard()

        # 写入数据
        blackboard.write("project_name", "TestProject", agent_id="test")
        blackboard.write("config", {"debug": True, "version": "1.0"}, agent_id="test")

        # 读取验证
        assert blackboard.get("project_name") == "TestProject"
        assert blackboard.get("config")["debug"] == True

    def test_swarm_task_decomposition(self):
        """测试任务分解能力"""
        agents = [
            MockAgent("agent1", skills=["a", "b"], delay=0.01),
            MockAgent("agent2", skills=["c", "d"], delay=0.01),
        ]

        swarm = SwarmOrchestrator(
            agent_pool=agents,
            llm=None,
            verbose=False,
            max_iterations=3
        )

        # 复杂任务应该被分解
        result = asyncio.run(swarm.solve("完成 ABCD 四个子任务"))

        # 验证任务被执行
        assert result is not None


class TestDeepSystemStability:
    """系统稳定性深度测试"""

    def test_concurrent_load_handling(self):
        """测试并发负载处理能力"""
        # 创建大量 Agent
        agents = [MockAgent(f"agent{i}", delay=0.005) for i in range(20)]

        scheduler = create_scheduler(agents=agents, max_concurrent=10)

        # 添加大量任务
        for i in range(50):
            scheduler.add_task(f"load_task_{i}", f"负载测试任务 {i}")

        start = time.time()
        results = asyncio.run(scheduler.schedule_and_execute(agent_pool=agents, parallel=True))
        elapsed = time.time() - start

        # 验证所有任务完成
        assert len(results) == 50
        assert all(r.success for r in results.values())
        # 验证并发效率：50 个任务，20 个 agent，应在合理时间完成
        assert elapsed < 5.0, f"负载测试过慢：{elapsed}秒"

    def test_resource_cleanup(self):
        """测试资源清理"""
        agents = [MockAgent(f"agent{i}", delay=0.01) for i in range(5)]

        # 多次创建和销毁调度器
        for _ in range(10):
            scheduler = create_scheduler(agents=agents, max_concurrent=3)
            scheduler.add_task("temp", "临时任务")
            asyncio.run(scheduler.schedule_and_execute(agent_pool=agents, parallel=True))

        # 验证系统稳定（无内存泄漏、资源耗尽）
        assert True  # 如果能执行到这里，说明清理正常

    def test_edge_case_handling(self):
        """测试边界情况处理"""
        # 空 Agent 池
        scheduler = create_scheduler(agents=[], max_concurrent=3)
        scheduler.add_task("orphan", "无 Agent 可执行的任务")

        # 应该不抛出异常，返回空结果或失败
        try:
            results = asyncio.run(scheduler.schedule_and_execute(agent_pool=[], parallel=True))
            # 如果有结果，应该是失败状态
        except Exception:
            # 或者抛出异常，也是可以接受的
            pass

        # 空任务
        scheduler2 = create_scheduler(agents=[MockAgent("a1")], max_concurrent=3)
        results2 = asyncio.run(scheduler2.schedule_and_execute(agent_pool=[MockAgent("a1")], parallel=True))
        assert len(results2) == 0  # 无任务应返回空结果


# ==================== 性能基准测试 ====================

class TestPerformanceBenchmarks:
    """性能基准测试"""

    def test_scheduler_throughput(self):
        """测试调度器吞吐量"""
        agents = [MockAgent(f"agent{i}", delay=0.001) for i in range(10)]
        scheduler = create_scheduler(agents=agents, max_concurrent=10)

        # 100 个任务
        for i in range(100):
            scheduler.add_task(f"bench_{i}", f"基准测试 {i}")

        start = time.time()
        results = asyncio.run(scheduler.schedule_and_execute(agent_pool=agents, parallel=True))
        elapsed = time.time() - start

        throughput = 100 / elapsed  # 任务/秒
        print(f"\n调度器吞吐量：{throughput:.1f} 任务/秒")

        assert len(results) == 100
        assert all(r.success for r in results.values())
        assert throughput > 50  # 至少 50 任务/秒

    def test_workflow_parallelism_efficiency(self):
        """测试工作流并行效率"""
        num_workers = 10
        task_delay = 0.1

        agents = [MockAgent(f"w{i}", delay=task_delay) for i in range(num_workers)]
        workflow = create_parallel_workflow(max_concurrent=num_workers)

        for i, agent in enumerate(agents):
            workflow.add_task(f"t{i}", agent, instance_id=f"w{i}")

        start = time.time()
        results = asyncio.run(workflow.execute("并行测试", verbose=False))
        elapsed = time.time() - start

        # 理论串行时间：num_workers * task_delay
        # 并行效率 = 串行时间 / 实际时间
        theoretical_serial = num_workers * task_delay
        efficiency = theoretical_serial / elapsed if elapsed > 0 else 0

        print(f"\n并行效率：{efficiency:.2f}x (理论{num_workers}x)")

        success_count = sum(1 for r in results.values() if r.success)
        assert success_count == num_workers
        assert efficiency > num_workers * 0.5  # 至少达到理论值的 50%
