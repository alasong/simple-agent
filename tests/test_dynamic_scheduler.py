"""
动态调度器测试 (Dynamic Scheduler Tests)

测试 DynamicScheduler 类的核心功能:
- Agent 注册和技能匹配
- 任务调度算法
- 失败重试机制
- 并行执行
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any

# 被测试模块
from scheduler.scheduler import (
    DynamicScheduler,
    AgentInfo,
    ScheduledTask,
    TaskPriority,
    ExecutionResult,
    SchedulerStatus,
    create_scheduler,
    create_tasks_from_graph,
)


# ==================== Mock Agent ====================

class MockAgent:
    """模拟 Agent 用于测试"""

    def __init__(
        self,
        name: str,
        instance_id: str = None,
        skills: List[str] = None,
        fail_rate: float = 0.0,
        delay: float = 0.1
    ):
        self.name = name
        self.instance_id = instance_id or name
        self.skills = skills or ["general"]
        self.fail_rate = fail_rate
        self.delay = delay
        self._call_count = 0
        self._fail_count = 0

    def run(self, task_input: str, verbose: bool = True) -> str:
        """执行任务（模拟）"""
        self._call_count += 1

        # 模拟延迟
        time.sleep(self.delay)

        # 模拟失败
        if self.fail_rate > 0 and time.time() % 1 < self.fail_rate:
            self._fail_count += 1
            raise Exception(f"Agent {self.name} 模拟失败")

        return f"Agent {self.name} 执行结果：{task_input[:50]}"

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def fail_count(self) -> int:
        return self._fail_count


class AsyncMockAgent:
    """异步模拟 Agent"""

    def __init__(
        self,
        name: str,
        instance_id: str = None,
        skills: List[str] = None,
        delay: float = 0.1
    ):
        self.name = name
        self.instance_id = instance_id or name
        self.skills = skills or ["general"]
        self.delay = delay

    async def run(self, task_input: str, verbose: bool = True) -> str:
        """异步执行任务"""
        await asyncio.sleep(self.delay)
        return f"Async Agent {self.name} 执行结果：{task_input[:50]}"


# ==================== AgentInfo 测试 ====================

class TestAgentInfo:
    """测试 AgentInfo 类"""

    def test_agent_info_creation(self):
        """测试 AgentInfo 创建"""
        agent = AgentInfo(
            instance_id="agent-1",
            name="Test Agent",
            skills=["coding", "testing"]
        )

        assert agent.instance_id == "agent-1"
        assert agent.name == "Test Agent"
        assert agent.skills == ["coding", "testing"]
        assert agent.current_load == 0
        assert agent.max_load == 5
        assert agent.success_rate == 1.0
        assert agent.is_available == True

    def test_agent_info_to_dict(self):
        """测试 AgentInfo 序列化"""
        agent = AgentInfo(
            instance_id="agent-1",
            name="Test Agent",
            skills=["coding"],
            current_load=2,
            success_rate=0.9
        )

        data = agent.to_dict()

        assert data["instance_id"] == "agent-1"
        assert data["name"] == "Test Agent"
        assert data["skills"] == ["coding"]
        assert data["current_load"] == 2
        assert data["success_rate"] == 0.9


# ==================== ScheduledTask 测试 ====================

class TestScheduledTask:
    """测试 ScheduledTask 类"""

    def test_task_creation(self):
        """测试任务创建"""
        task = ScheduledTask(
            id="task-1",
            description="Test task",
            required_skills=["coding"],
            priority=TaskPriority.HIGH
        )

        assert task.id == "task-1"
        assert task.description == "Test task"
        assert task.required_skills == ["coding"]
        assert task.priority == TaskPriority.HIGH
        assert task.status == "pending"
        assert task.retry_count == 0

    def test_task_is_ready(self):
        """测试任务就绪检查"""
        # 无依赖任务
        task1 = ScheduledTask(id="t1", description="Task 1")
        assert task1.is_ready(set()) == True
        assert task1.is_ready({"other-task"}) == True

        # 有依赖任务
        task2 = ScheduledTask(id="t2", description="Task 2", dependencies=["t1"])
        assert task2.is_ready(set()) == False
        assert task2.is_ready({"t1"}) == True
        assert task2.is_ready({"t1", "other"}) == True

    def test_task_retry(self):
        """测试任务重试"""
        task = ScheduledTask(id="t1", description="Task 1", max_retries=3)

        assert task.can_retry() == True
        assert task.retry_count == 0

        task.reset_for_retry()
        assert task.retry_count == 1
        assert task.status == "pending"

        task.reset_for_retry()
        task.reset_for_retry()
        assert task.retry_count == 3
        assert task.can_retry() == False


# ==================== DynamicScheduler 测试 ====================

class TestDynamicScheduler:
    """测试 DynamicScheduler 类"""

    def test_scheduler_creation(self):
        """测试调度器创建"""
        scheduler = DynamicScheduler()

        assert scheduler.status == SchedulerStatus.IDLE
        assert scheduler._running == False
        assert scheduler.max_concurrent_tasks == 5
        assert len(scheduler.agents) == 0
        assert len(scheduler.tasks) == 0

    def test_register_agent(self):
        """测试 Agent 注册"""
        scheduler = DynamicScheduler()

        agent = MockAgent(name="Dev Agent", skills=["coding", "testing"])
        scheduler.register_agent(agent, skills=["coding", "testing"])

        assert "Dev Agent" in scheduler.agents
        agent_info = scheduler.agents["Dev Agent"]
        assert agent_info.name == "Dev Agent"
        assert "coding" in agent_info.skills
        assert "testing" in agent_info.skills

    def test_register_agent_auto_skills(self):
        """测试自动推断技能"""
        scheduler = DynamicScheduler()

        # Developer Agent
        dev_agent = MockAgent(name="Developer")
        scheduler.register_agent(dev_agent)
        assert "coding" in scheduler.agents["Developer"].skills

        # Tester Agent
        test_agent = MockAgent(name="Tester")
        scheduler.register_agent(test_agent)
        assert "testing" in scheduler.agents["Tester"].skills

        # Reviewer Agent
        review_agent = MockAgent(name="Reviewer")
        scheduler.register_agent(review_agent)
        assert "reviewing" in scheduler.agents["Reviewer"].skills

    def test_add_task(self):
        """测试添加任务"""
        scheduler = DynamicScheduler()

        task = scheduler.add_task(
            task_id="task-1",
            description="Test task",
            required_skills=["coding"],
            priority=TaskPriority.HIGH,
            dependencies=[]
        )

        assert task.id == "task-1"
        assert len(scheduler.tasks) == 1
        assert scheduler._total_tasks_scheduled == 1

    def test_select_agent_for_task(self):
        """测试 Agent 选择"""
        scheduler = DynamicScheduler()

        # 注册多个 Agent
        coding_agent = MockAgent(name="Coder", skills=["coding"])
        test_agent = MockAgent(name="Tester", skills=["testing"])
        general_agent = MockAgent(name="General", skills=["general"])

        scheduler.register_agent(coding_agent)
        scheduler.register_agent(test_agent)
        scheduler.register_agent(general_agent)

        # 需要 coding 技能的任务
        task = ScheduledTask(id="t1", description="Code task", required_skills=["coding"])
        selected = scheduler.select_agent_for_task(task)

        assert selected == "Coder"

        # 需要 testing 技能的任务
        task2 = ScheduledTask(id="t2", description="Test task", required_skills=["testing"])
        selected2 = scheduler.select_agent_for_task(task2)

        assert selected2 == "Tester"

    def test_agent_load_balancing(self):
        """测试负载平衡"""
        scheduler = DynamicScheduler()

        # 注册两个相同的 Agent
        agent1 = MockAgent(name="Agent1", skills=["general"])
        agent2 = MockAgent(name="Agent2", skills=["general"])

        scheduler.register_agent(agent1)
        scheduler.register_agent(agent2)

        # 模拟 Agent1 已有负载（超过最大负载）
        scheduler.agents["Agent1"].current_load = 5  # max_load is 5
        scheduler.agents["Agent2"].current_load = 0

        # 选择 Agent，应该选择负载较低的 Agent2
        # 注意：当 Agent1 负载达到最大时，会被排除在候选外
        task = ScheduledTask(id="t1", description="Task", required_skills=[])
        selected = scheduler.select_agent_for_task(task)

        # Agent1 已满负载，应该选择 Agent2
        assert selected == "Agent2"

    def test_agent_score_calculation(self):
        """测试 Agent 得分计算"""
        scheduler = DynamicScheduler()

        # 高成功率 Agent
        good_agent = AgentInfo(
            instance_id="good",
            name="Good Agent",
            skills=["coding"],
            success_rate=0.95,
            current_load=1,
            avg_execution_time=5.0
        )

        # 低成功率 Agent
        bad_agent = AgentInfo(
            instance_id="bad",
            name="Bad Agent",
            skills=["coding"],
            success_rate=0.5,
            current_load=1,
            avg_execution_time=10.0
        )

        scheduler.agents["good"] = good_agent
        scheduler.agents["bad"] = bad_agent

        task = ScheduledTask(id="t1", description="Task", required_skills=["coding"])

        good_score = scheduler._calculate_agent_score(good_agent, task)
        bad_score = scheduler._calculate_agent_score(bad_agent, task)

        # 高成功率 Agent 得分应该更高
        assert good_score > bad_score

    def test_skill_matching(self):
        """测试技能匹配"""
        scheduler = DynamicScheduler()

        agent = AgentInfo(
            instance_id="agent-1",
            name="Test Agent",
            skills=["coding", "python", "testing"]
        )

        # 精确匹配
        assert scheduler._matches_skills(agent, ["coding"]) == True
        assert scheduler._matches_skills(agent, ["python"]) == True

        # 部分匹配
        assert scheduler._matches_skills(agent, ["coding", "testing"]) == True

        # 不匹配
        assert scheduler._matches_skills(agent, ["design"]) == False

        # 空技能要求（总是匹配）
        assert scheduler._matches_skills(agent, []) == True

    def test_scheduler_pause_resume(self):
        """测试暂停/恢复"""
        scheduler = DynamicScheduler()

        assert scheduler.status == SchedulerStatus.IDLE

        scheduler.pause()
        assert scheduler.status == SchedulerStatus.PAUSED

        scheduler.resume()
        assert scheduler.status == SchedulerStatus.RUNNING

        scheduler.stop()
        assert scheduler.status == SchedulerStatus.STOPPED


# ==================== 异步执行测试 ====================

class TestAsyncExecution:
    """测试异步执行"""

    @pytest.mark.asyncio
    async def test_execute_task_success(self):
        """测试任务执行成功"""
        scheduler = DynamicScheduler()

        agent = AsyncMockAgent(name="AsyncAgent", skills=["coding"], delay=0.01)
        scheduler.register_agent(agent)

        task = ScheduledTask(id="t1", description="Test task", required_skills=["coding"])

        result = await scheduler.execute_task(task, agent, verbose=False)

        assert result.success == True
        assert result.task_id == "t1"
        assert result.agent_id == "AsyncAgent"
        assert result.execution_time >= 0.01
        assert "AsyncAgent" in result.result

    @pytest.mark.asyncio
    async def test_execute_task_failure(self):
        """测试任务执行失败"""
        scheduler = DynamicScheduler()

        agent = MockAgent(name="FailAgent", skills=["coding"], fail_rate=1.0, delay=0.01)
        scheduler.register_agent(agent)

        task = ScheduledTask(id="t1", description="Test task", required_skills=["coding"])

        result = await scheduler.execute_task(task, agent, verbose=False)

        assert result.success == False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_with_retry(self):
        """测试带重试的执行"""
        scheduler = DynamicScheduler(
            retry_delay_base=0.01,
            retry_delay_max=0.05
        )

        # 创建一个总是失败的 Agent
        fail_agent = MockAgent(name="FailAgent", skills=["coding"], fail_rate=1.0, delay=0.01)
        scheduler.register_agent(fail_agent)

        task = ScheduledTask(id="t1", description="Test task", max_retries=2)

        result = await scheduler.execute_with_retry(task, fail_agent, verbose=False)

        # 最终应该失败
        assert result.success == False
        # 应该尝试了多次
        assert task.retry_count == 2
        assert task.status == "failed"

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """测试并行执行"""
        scheduler = DynamicScheduler(max_concurrent_tasks=3)

        # 注册多个 Agent
        agents = [
            AsyncMockAgent(name=f"Agent{i}", skills=["general"], delay=0.1)
            for i in range(3)
        ]

        for agent in agents:
            scheduler.register_agent(agent)

        # 添加多个任务
        tasks = [
            ScheduledTask(id=f"t{i}", description=f"Task {i}")
            for i in range(3)
        ]

        for task in tasks:
            scheduler.tasks[task.id] = task

        # 执行
        results = await scheduler.schedule_and_execute(
            tasks=tasks,
            agent_pool=agents,
            verbose=False,
            parallel=True
        )

        # 验证结果
        assert len(results) == 3
        assert all(r.success for r in results.values())

    @pytest.mark.asyncio
    async def test_sequential_execution_with_dependencies(self):
        """测试带依赖的顺序执行"""
        scheduler = DynamicScheduler()

        agent = AsyncMockAgent(name="Agent", skills=["general"], delay=0.01)
        scheduler.register_agent(agent)

        # 添加有依赖的任务
        task1 = ScheduledTask(id="t1", description="Task 1")
        task2 = ScheduledTask(id="t2", description="Task 2", dependencies=["t1"])
        task3 = ScheduledTask(id="t3", description="Task 3", dependencies=["t2"])

        tasks = [task1, task2, task3]

        results = await scheduler.schedule_and_execute(
            tasks=tasks,
            agent_pool=[agent],
            verbose=False,
            parallel=False
        )

        # 所有任务应该成功
        assert all(r.success for r in results.values())

    @pytest.mark.asyncio
    async def test_concurrent_limit(self):
        """测试并发限制"""
        max_concurrent = 2
        scheduler = DynamicScheduler(max_concurrent_tasks=max_concurrent)

        agent = AsyncMockAgent(name="Agent", skills=["general"], delay=0.1)
        scheduler.register_agent(agent)

        # 添加多个任务
        tasks = [
            ScheduledTask(id=f"t{i}", description=f"Task {i}")
            for i in range(5)
        ]

        results = await scheduler.schedule_and_execute(
            tasks=tasks,
            agent_pool=[agent],
            verbose=False,
            parallel=True
        )

        # 所有任务应该完成
        assert len(results) == 5


# ==================== 统计和状态测试 ====================

class TestSchedulerStats:
    """测试调度器统计"""

    def test_get_status(self):
        """测试获取状态"""
        scheduler = DynamicScheduler()

        # 添加 Agent 和任务
        agent = MockAgent(name="Agent", skills=["general"])
        scheduler.register_agent(agent)

        scheduler.add_task("t1", "Task 1")
        scheduler.add_task("t2", "Task 2", dependencies=["t1"])

        status = scheduler.get_status()

        assert status["status"] == "idle"
        assert status["total_tasks"] == 2
        assert status["completed"] == 0
        assert status["failed"] == 0
        assert "Agent" in status["agents"]

    def test_agent_load_tracking(self):
        """测试 Agent 负载跟踪"""
        scheduler = DynamicScheduler()

        agent = MockAgent(name="Agent", skills=["general"])
        scheduler.register_agent(agent)

        assert scheduler.get_agent_load("Agent") == 0

        # 模拟负载增加
        scheduler.agents["Agent"].current_load = 3
        assert scheduler.get_agent_load("Agent") == 3

    def test_task_tracking(self):
        """测试任务跟踪"""
        scheduler = DynamicScheduler()

        task = scheduler.add_task("t1", "Task 1")

        result = scheduler.get_task("t1")
        assert result == task

        result = scheduler.get_task("nonexistent")
        assert result is None


# ==================== 便捷函数测试 ====================

class TestHelperFunctions:
    """测试便捷函数"""

    def test_create_scheduler(self):
        """测试创建调度器"""
        agents = [MockAgent(name="Agent1"), MockAgent(name="Agent2")]

        scheduler = create_scheduler(agents=agents, max_concurrent=10)

        assert scheduler.max_concurrent_tasks == 10
        assert len(scheduler.agents) == 2

    def test_create_tasks_from_graph(self):
        """测试从图创建任务"""
        # 这里需要 dependency_graph 的 TaskGraph
        # 简化测试
        from core.dependency_graph import TaskGraph

        graph = TaskGraph()
        graph.add_task("t1", "Task 1", "Description 1", agent_type="developer")
        graph.add_task("t2", "Task 2", "Description 2", dependencies=["t1"])

        tasks = create_tasks_from_graph(graph)

        assert len(tasks) == 2
        assert tasks[0].id == "t1"
        assert tasks[1].dependencies == ["t1"]


# ==================== 回调测试 ====================

class TestCallbacks:
    """测试回调功能"""

    @pytest.mark.asyncio
    async def test_task_start_callback(self):
        """测试任务开始回调"""
        scheduler = DynamicScheduler()
        callback_called = False

        async def on_task_start(task, agent):
            nonlocal callback_called
            callback_called = True

        scheduler.on_task_start(on_task_start)

        agent = AsyncMockAgent(name="Agent", skills=["general"], delay=0.01)
        scheduler.register_agent(agent)

        task = ScheduledTask(id="t1", description="Task")

        await scheduler.execute_task(task, agent, verbose=False)

        assert callback_called == True

    @pytest.mark.asyncio
    async def test_task_complete_callback(self):
        """测试任务完成回调"""
        scheduler = DynamicScheduler()
        callback_result = None

        async def on_task_complete(task, result):
            nonlocal callback_result
            callback_result = result

        scheduler.on_task_complete(on_task_complete)

        agent = AsyncMockAgent(name="Agent", skills=["general"], delay=0.01)
        scheduler.register_agent(agent)

        task = ScheduledTask(id="t1", description="Task")

        await scheduler.execute_task(task, agent, verbose=False)

        assert callback_result is not None

    @pytest.mark.asyncio
    async def test_task_failed_callback(self):
        """测试任务失败回调"""
        scheduler = DynamicScheduler(retry_delay_base=0.01, retry_delay_max=0.05)
        callback_called = False

        async def on_task_failed(task, error):
            nonlocal callback_called
            callback_called = True

        scheduler.on_task_failed(on_task_failed)

        agent = MockAgent(name="FailAgent", skills=["general"], fail_rate=1.0, delay=0.01)
        scheduler.register_agent(agent)

        task = ScheduledTask(id="t1", description="Task", max_retries=0)

        await scheduler.execute_with_retry(task, agent, verbose=False)

        assert callback_called == True


# ==================== 集成测试 ====================

class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流"""
        scheduler = DynamicScheduler(max_concurrent_tasks=2)

        # 注册 Agent
        agents = [
            AsyncMockAgent(name=f"Agent{i}", skills=["general"], delay=0.05)
            for i in range(2)
        ]
        for agent in agents:
            scheduler.register_agent(agent)

        # 添加任务
        scheduler.add_task("t1", "Task 1")
        scheduler.add_task("t2", "Task 2")
        scheduler.add_task("t3", "Task 3", dependencies=["t1", "t2"])
        scheduler.add_task("t4", "Task 4", priority=TaskPriority.HIGH)

        # 执行
        results = await scheduler.schedule_and_execute(
            agent_pool=agents,
            verbose=False,
            parallel=True
        )

        # 验证
        assert len(results) == 4
        assert all(r.success for r in results.values())

        # 验证状态
        status = scheduler.get_status()
        assert status["completed"] == 4
        assert status["failed"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
