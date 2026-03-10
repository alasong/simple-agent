"""
群体智能控制器（Swarm Orchestrator）

核心控制器，协调多个 Agent 完成复杂任务

简化版本:
- 使用 Builder 模式简化配置
- 统一使用 v2 调度器（TaskSchedulerV2）和 ParallelWorkflow
- 移除 v1/v2 选择逻辑
"""

import asyncio
import time
from typing import Optional, Any, Callable, List
from dataclasses import dataclass, field


@dataclass
class SwarmResult:
    """Swarm 执行结果"""
    success: bool
    output: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_iterations: int = 0
    execution_time: float = 0.0
    agent_stats: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output[:500],
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "total_iterations": self.total_iterations,
            "execution_time": round(self.execution_time, 2),
            "agent_stats": self.agent_stats
        }


class SwarmOrchestratorBuilder:
    """
    SwarmOrchestrator 构建器

    使用 Builder 模式简化配置:

    示例:
        swarm = (SwarmOrchestratorBuilder()
            .with_agents([agent1, agent2, agent3])
            .with_llm(llm)
            .with_max_concurrent(3)
            .with_verbose(True)
            .build())
    """

    def __init__(self):
        self._agent_pool: List[Any] = []
        self._llm: Optional[Any] = None
        self._max_iterations: int = 50
        self._verbose: bool = True
        self._max_concurrent: int = 5
        self._use_rich_output: bool = True

    def with_agents(self, agents: List[Any]) -> "SwarmOrchestratorBuilder":
        """设置 Agent 池"""
        self._agent_pool = agents
        return self

    def with_llm(self, llm: Any) -> "SwarmOrchestratorBuilder":
        """设置 LLM"""
        self._llm = llm
        return self

    def with_max_iterations(self, max_iterations: int) -> "SwarmOrchestratorBuilder":
        """设置最大迭代次数"""
        self._max_iterations = max_iterations
        return self

    def with_verbose(self, verbose: bool) -> "SwarmOrchestratorBuilder":
        """设置详细输出"""
        self._verbose = verbose
        return self

    def with_max_concurrent(self, max_concurrent: int) -> "SwarmOrchestratorBuilder":
        """设置最大并发数"""
        self._max_concurrent = max_concurrent
        return self

    def with_rich_output(self, use_rich_output: bool) -> "SwarmOrchestratorBuilder":
        """设置是否使用富文本输出"""
        self._use_rich_output = use_rich_output
        return self

    def build(self) -> "SwarmOrchestrator":
        """构建 SwarmOrchestrator"""
        return SwarmOrchestrator(
            agent_pool=self._agent_pool,
            llm=self._llm,
            max_iterations=self._max_iterations,
            verbose=self._verbose,
            use_rich_output=self._use_rich_output,
            max_concurrent=self._max_concurrent
        )


class SwarmOrchestrator:
    """
    群体智能控制器

    简化后的版本:
    - 统一使用 v2 调度器和并行工作流
    - 移除 v1/v2 选择逻辑
    - 支持 Builder 模式配置
    """

    def __init__(
        self,
        agent_pool: List[Any],
        llm: Optional[Any] = None,
        max_iterations: int = 50,
        verbose: bool = True,
        use_rich_output: bool = True,
        max_concurrent: int = 5
    ):
        """
        初始化 SwarmOrchestrator

        Args:
            agent_pool: Agent 池
            llm: LLM 实例（用于任务分解）
            max_iterations: 最大迭代次数
            verbose: 是否输出详细过程
            use_rich_output: 是否使用富文本输出
            max_concurrent: 最大并发数
        """
        self.agent_pool = agent_pool
        self.llm = llm
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.use_rich_output = use_rich_output
        self.max_concurrent = max_concurrent

        # 延迟初始化组件
        self._scheduler = None
        self._task_graph = None
        self._decomposer = None
        self._rich_output = None

        # 状态
        self._running = False
        self._iteration = 0
        self._start_time: float = 0

        # 事件回调
        self._on_task_start: Optional[Callable] = None
        self._on_task_complete: Optional[Callable] = None
        self._on_swarm_complete: Optional[Callable] = None

    def _init_components(self):
        """延迟初始化组件"""
        if self._scheduler is None:
            # 导入 v2 调度器
            from simple_agent.swarm.task_scheduler import TaskSchedulerV2
            from simple_agent.swarm.scheduler.workflow_parallel import create_parallel_workflow

            self._scheduler = TaskSchedulerV2(
                self.agent_pool,
                llm=self.llm,
                max_concurrent=self.max_concurrent
            )
            self._workflow_factory = create_parallel_workflow

            # 任务分解器
            if self.llm:
                from simple_agent.swarm.task_scheduler import TaskDecomposer
                self._decomposer = TaskDecomposer(self.llm)

            # 富文本输出
            if self.use_rich_output:
                try:
                    from simple_agent.core.rich_output import RichOutput
                    self._rich_output = RichOutput()
                except ImportError:
                    self._rich_output = None

            # 任务图
            from simple_agent.swarm.task_scheduler import TaskGraph
            self._task_graph = TaskGraph()

    @property
    def scheduler(self):
        """获取调度器"""
        self._init_components()
        return self._scheduler

    @property
    def task_graph(self):
        """获取任务图"""
        self._init_components()
        return self._task_graph

    @property
    def decomposer(self):
        """获取任务分解器"""
        self._init_components()
        return self._decomposer

    @property
    def rich_output(self):
        """获取富文本输出器"""
        self._init_components()
        return self._rich_output

    async def solve(self, complex_task: str) -> SwarmResult:
        """
        解决复杂任务

        Args:
            complex_task: 复杂任务描述

        Returns:
            SwarmResult 执行结果
        """
        self._init_components()

        self._running = True
        self._start_time = time.time()
        self._iteration = 0

        # 显示任务开始
        if self._rich_output:
            self._rich_output.print_header("Swarm 开始执行任务", complex_task[:80])
        elif self.verbose:
            print(f"\n{'='*60}")
            print(f"Swarm 开始执行任务：{complex_task[:100]}...")
            print(f"{'='*60}\n")

        try:
            # 1. 任务分解
            if self._decomposer:
                tasks = await self._decomposer.decompose(complex_task)
            else:
                from simple_agent.swarm.scheduler import Task
                tasks = [Task(id="1", description=complex_task, required_skills=[])]

            if self._rich_output:
                self._rich_output.print_info(f"分解为 {len(tasks)} 个子任务")
            elif self.verbose:
                print(f"[分解] 分解为 {len(tasks)} 个子任务")

            # 2. 构建任务图
            self._task_graph.build_from_tasks(tasks)

            # 3. 执行
            result = await self._execute_loop(complex_task)

            # 4. 显示结果
            if self._rich_output:
                self._rich_output.show_swarm_result(result, complex_task)
            elif self.verbose:
                print(f"\n{'='*60}")
                print(f"Swarm 执行完成")
                print(f"完成：{result.tasks_completed} 任务，失败：{result.tasks_failed}")
                print(f"{'='*60}\n")

            return result

        except Exception as e:
            error_msg = f"Swarm 执行失败：{e}"
            if self._rich_output:
                self._rich_output.print_error(error_msg)
            elif self.verbose:
                print(f"[错误] {error_msg}")
            return SwarmResult(
                success=False,
                output=error_msg,
                execution_time=time.time() - self._start_time
            )
        finally:
            self._running = False

    async def _execute_loop(self, original_task: str) -> SwarmResult:
        """
        执行循环 - 使用 ParallelWorkflow

        根据任务依赖关系自动选择执行策略:
        - 无依赖：使用 ParallelWorkflow 并行执行
        - 有依赖：使用 TaskSchedulerV2 处理依赖
        """
        all_tasks = self._task_graph.get_all_tasks()
        has_dependencies = any(t.dependencies for t in all_tasks)

        if self.verbose:
            if has_dependencies:
                print(f"[执行] 检测到依赖，使用 TaskSchedulerV2 处理...")
            else:
                print(f"[执行] 无依赖，使用 ParallelWorkflow 并行执行...")

        if has_dependencies:
            return await self._execute_with_dependencies(original_task)
        else:
            return await self._execute_parallel(original_task)

    async def _execute_with_dependencies(self, original_task: str) -> SwarmResult:
        """有依赖的执行"""
        self._scheduler.build_from_tasks(self._task_graph.get_all_tasks())
        await self._scheduler.execute_all_parallel(verbose=self.verbose)

        completed = sum(1 for t in self._task_graph.get_all_tasks()
                       if t.status.name == "COMPLETED")
        failed = sum(1 for t in self._task_graph.get_all_tasks()
                    if t.status.name == "FAILED")

        return self._synthesize_results(original_task, completed, failed)

    async def _execute_parallel(self, original_task: str) -> SwarmResult:
        """无依赖并行执行"""
        workflow = self._workflow_factory(
            max_concurrent=self.max_concurrent,
            continue_on_error=True
        )

        for task in self._task_graph.get_all_tasks():
            agent = await self._scheduler.assign_task(task)
            if agent:
                workflow.add_task(
                    name=f"Task {task.id}",
                    agent=agent,
                    instance_id=task.id,
                    output_key=f"result_{task.id}"
                )

        exec_results = await workflow.execute(original_task, verbose=self.verbose)

        completed = 0
        failed = 0
        for task_id, result in exec_results.items():
            task = self._task_graph.get_task(task_id)
            if task:
                if result.success:
                    task.mark_completed(str(result.result))
                    completed += 1
                else:
                    task.mark_failed(result.error or "Unknown error")
                    failed += 1

        return self._synthesize_results(original_task, completed, failed)

    def _synthesize_results(
        self,
        original_task: str,
        completed: int,
        failed: int
    ) -> SwarmResult:
        """汇总结果"""
        all_tasks = self._task_graph.get_all_tasks()

        output_parts = [
            f"任务：{original_task}",
            "",
            "执行摘要：",
            f"- 总任务数：{len(all_tasks)}",
            f"- 完成：{completed}",
            f"- 失败：{failed}",
            ""
        ]

        # 已完成任务
        completed_tasks = [t for t in all_tasks if t.status.name == "COMPLETED"]
        if completed_tasks:
            output_parts.append("已完成任务：")
            for task in completed_tasks:
                preview = (task.result or "")[:150]
                output_parts.append(f"- [{task.id}] {task.description}: {preview}...")
            output_parts.append("")

        # 失败任务
        failed_tasks = [t for t in all_tasks if t.status.name == "FAILED"]
        if failed_tasks:
            output_parts.append("失败任务：")
            for task in failed_tasks:
                output_parts.append(
                    f"- [{task.id}] {task.description}: {task.error or '未知错误'}"
                )
            output_parts.append("")

        final_output = "\n".join(output_parts)

        return SwarmResult(
            success=failed == 0,
            output=final_output,
            tasks_completed=completed,
            tasks_failed=failed,
            total_iterations=self._iteration,
            execution_time=time.time() - self._start_time,
            agent_stats=self._scheduler.get_agent_stats() if self._scheduler else {}
        )

    def on_task_start(self, callback: Callable):
        """注册任务开始回调"""
        self._on_task_start = callback

    def on_task_complete(self, callback: Callable):
        """注册任务完成回调"""
        self._on_task_complete = callback

    def on_swarm_complete(self, callback: Callable):
        """注册 Swarm 完成回调"""
        self._on_swarm_complete = callback

    @property
    def status(self) -> dict:
        """获取当前状态"""
        all_tasks = self._task_graph.get_all_tasks() if self._task_graph else []
        return {
            "running": self._running,
            "iteration": self._iteration,
            "total_tasks": len(all_tasks),
            "completed": sum(1 for t in all_tasks if t.status.name == "COMPLETED"),
            "failed": sum(1 for t in all_tasks if t.status.name == "FAILED"),
        }

    def __repr__(self) -> str:
        return f"<SwarmOrchestrator agents={len(self.agent_pool)} running={self._running}>"
