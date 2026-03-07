"""
群体智能控制器（Swarm Orchestrator）

核心控制器，协调多个 Agent 完成复杂任务
"""

import asyncio
import time
from typing import Optional, Any, Callable, List
from dataclasses import dataclass, field
import uuid

from .blackboard import Blackboard
from .message_bus import MessageBus, Message
from .scheduler import TaskScheduler, TaskDecomposer, Task, TaskGraph, TaskStatus

# 富文本输出（可选）
try:
    from core.rich_output import RichOutput, TaskDisplayData
    RICH_OUTPUT_AVAILABLE = True
except ImportError:
    RICH_OUTPUT_AVAILABLE = False


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


class SwarmOrchestrator:
    """群体智能控制器"""
    
    def __init__(
        self,
        agent_pool: list[Any],
        llm=None,
        max_iterations: int = 50,
        verbose: bool = True,
        use_rich_output: bool = True
    ):
        self.agent_pool = agent_pool
        self.llm = llm
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.use_rich_output = use_rich_output and RICH_OUTPUT_AVAILABLE
        
        # 富文本输出器
        self.rich_output = RichOutput() if self.use_rich_output else None
        
        # 核心组件
        self.blackboard = Blackboard()
        self.message_bus = MessageBus()
        self.scheduler = TaskScheduler(agent_pool)
        self.task_graph = TaskGraph()
        
        # 任务分解器（需要 LLM）
        self.decomposer = TaskDecomposer(llm) if llm else None
        
        # 状态
        self._running = False
        self._iteration = 0
        self._start_time: float = 0
        self._result: Optional[SwarmResult] = None
        
        # 事件回调
        self._on_task_start: Optional[Callable] = None
        self._on_task_complete: Optional[Callable] = None
        self._on_swarm_complete: Optional[Callable] = None
        
        # 任务执行跟踪
        self._task_display_data: List[TaskDisplayData] = [] if RICH_OUTPUT_AVAILABLE else []
    
    async def solve(self, complex_task: str) -> SwarmResult:
        """解决复杂任务
        
        Args:
            complex_task: 复杂任务描述
        
        Returns:
            SwarmResult 执行结果
        """
        self._running = True
        self._start_time = time.time()
        self._iteration = 0
        self._result = None
        self._task_display_data = []
        
        # 使用富文本输出时显示标题
        if self.rich_output:
            self.rich_output.print_header("Swarm 开始执行任务", complex_task[:80])
        elif self.verbose:
            print(f"\n{'='*60}")
            print(f"Swarm 开始执行任务：{complex_task[:100]}...")
            print(f"{'='*60}\n")
        
        try:
            # 1. 任务分解
            if self.decomposer:
                tasks = await self._decompose(complex_task)
            else:
                # 没有 LLM，创建单个任务
                tasks = [Task(id="1", description=complex_task, required_skills=[])]
            
            if self.rich_output:
                self.rich_output.print_info(f"分解为 {len(tasks)} 个子任务")
            elif self.verbose:
                print(f"[分解] 分解为 {len(tasks)} 个子任务")
            
            # 展示并发任务（如果有多个无依赖任务）
            if self.rich_output and len(tasks) > 1:
                from core.rich_output import TaskDisplayData
                concurrent_tasks = [
                    TaskDisplayData(
                        id=t.id,
                        description=t.description,
                        status="pending",
                        agent="待分配"
                    )
                    for t in tasks if not t.dependencies
                ]
                if concurrent_tasks:
                    self.rich_output.show_concurrent_tasks(concurrent_tasks)
            
            # 2. 构建任务图
            self._build_task_graph(tasks)
            
            # 3. 启动消息总线
            await self.message_bus.start()
            
            # 4. 迭代执行
            result = await self._execute_loop(complex_task)
            
            # 5. 汇总结果（带富文本展示）
            self._result = result
            self._display_result(result, complex_task)
            
            return result
            
        except Exception as e:
            error_msg = f"Swarm 执行失败：{e}"
            if self.rich_output:
                self.rich_output.print_error(error_msg)
            elif self.verbose:
                print(f"[错误] {error_msg}")
            return SwarmResult(
                success=False,
                output=error_msg,
                execution_time=time.time() - self._start_time
            )
        finally:
            self._running = False
            await self.message_bus.stop()
    
    async def _decompose(self, task: str) -> list[Task]:
        """任务分解"""
        return await self.decomposer.decompose(task)
    
    def _build_task_graph(self, tasks: list[Task]):
        """构建任务依赖图"""
        self.task_graph.build_from_tasks(tasks)
    
    async def _execute_loop(self, original_task: str) -> SwarmResult:
        """执行循环"""
        tasks_completed = 0
        tasks_failed = 0
        
        while self._running and self._iteration < self.max_iterations:
            self._iteration += 1
            
            if self.verbose:
                print(f"\n[迭代 {self._iteration}] 检查可执行任务...")
            
            # 获取就绪任务
            ready_tasks = self.task_graph.get_ready_tasks()
            
            if not ready_tasks:
                if self.task_graph.has_pending_tasks():
                    # 有任务但未就绪，可能有循环依赖
                    if self.verbose:
                        print(f"[等待] 没有就绪任务，检查依赖...")
                    await asyncio.sleep(0.1)
                    continue
                else:
                    # 所有任务完成
                    break
            
            if self.verbose:
                task_ids = [t.id for t in ready_tasks]
                print(f"[就绪] {len(ready_tasks)} 个任务：{', '.join(task_ids)}")
            
            # 并行执行就绪任务
            execution_tasks = []
            for task in ready_tasks:
                # 分配任务
                agent = await self.scheduler.assign_task(task)
                if agent:
                    execution_tasks.append(self._execute_task(task, agent))
            
            if execution_tasks:
                # 并行执行
                results = await asyncio.gather(*execution_tasks, return_exceptions=True)
                
                # 处理结果
                for task, result in zip(ready_tasks, results):
                    if isinstance(result, Exception):
                        task.mark_failed(str(result))
                        tasks_failed += 1
                        if self.verbose:
                            print(f"[失败] 任务 {task.id}: {result}")
                    elif isinstance(result, bool) and result:
                        tasks_completed += 1
                        if self.verbose:
                            print(f"[完成] 任务 {task.id}: {task.result[:100] if task.result else ''}...")
                    else:
                        tasks_failed += 1
                        if self.verbose:
                            print(f"[失败] 任务 {task.id}")
            
            # 检查是否有进展
            if not execution_tasks and not ready_tasks:
                break
        
        # 生成最终结果
        return self._synthesize_results(original_task, tasks_completed, tasks_failed)
    
    async def _execute_task(self, task: Task, agent: Any) -> bool:
        """执行单个任务"""
        if self._on_task_start:
            await self._on_task_start(task, agent)
        
        try:
            # 准备上下文
            context = self.blackboard.get_context(task)
            
            # 构建任务输入
            task_input = task.description
            if context:
                task_input = f"{task_input}\n\n{context}"
            
            if self.verbose:
                print(f"[执行] 任务 {task.id} -> Agent {agent.name}")
            
            # 发布任务开始消息
            await self.message_bus.publish(
                f"task.{task.id}",
                {"status": "started", "agent": agent.name},
                "orchestrator"
            )
            
            # 执行任务（Agent.run 是同步的，使用 run_in_executor 避免阻塞）
            loop = asyncio.get_event_loop()
            if hasattr(agent, 'run'):
                # 如果是异步方法
                if asyncio.iscoroutinefunction(agent.run):
                    result = await agent.run(task_input, verbose=False)
                else:
                    result = await loop.run_in_executor(None, lambda: agent.run(task_input, verbose=False))
            else:
                result = f"Agent {agent.name} 无 run 方法"
            
            # 更新黑板
            self.blackboard.update(task.id, result, agent.instance_id or agent.name)
            
            # 标记完成
            task.mark_completed(result)
            self.scheduler.complete_task(task)
            
            # 发布完成消息
            await self.message_bus.publish(
                f"task.{task.id}",
                {"status": "completed", "result": result[:200]},
                agent.instance_id or agent.name
            )
            
            if self._on_task_complete:
                await self._on_task_complete(task, result)
            
            return True
            
        except Exception as e:
            task.mark_failed(str(e))
            self.scheduler.complete_task(task)
            
            await self.message_bus.publish(
                f"task.{task.id}",
                {"status": "failed", "error": str(e)},
                "orchestrator"
            )
            
            if self.verbose:
                print(f"[错误] 任务 {task.id} 执行失败：{e}")
            
            return False
    
    def _synthesize_results(self, original_task: str, completed: int, failed: int) -> SwarmResult:
        """汇总结果"""
        all_tasks = self.task_graph.get_all_tasks()
        completed_tasks = [t for t in all_tasks if t.status == TaskStatus.COMPLETED]
        failed_tasks = [t for t in all_tasks if t.status == TaskStatus.FAILED]
        
        # 构建结构化输出
        output_parts = []
        
        # 原始任务
        output_parts.append(f"任务：{original_task}")
        output_parts.append("")
        
        # 执行摘要
        output_parts.append("执行摘要：")
        output_parts.append(f"- 总任务数：{len(all_tasks)}")
        output_parts.append(f"- 完成：{completed}")
        output_parts.append(f"- 失败：{failed}")
        output_parts.append("")
        
        # 任务结果
        if completed_tasks:
            output_parts.append("已完成任务：")
            for task in completed_tasks:
                result_preview = (task.result or "")[:150]
                output_parts.append(f"- [{task.id}] {task.description}: {result_preview}...")
            output_parts.append("")
        
        if failed_tasks:
            output_parts.append("失败任务：")
            for task in failed_tasks:
                output_parts.append(f"- [{task.id}] {task.description}: {task.error or '未知错误'}")
            output_parts.append("")
        
        # 收集最终结果
        final_output = "\n".join(output_parts)
        
        # 如果有主要结果，提取
        main_results = [t.result for t in completed_tasks if t.result and len(t.result) > 50]
        if main_results:
            final_output += "\n\n主要结果:\n" + "\n".join(main_results[:3])
        
        execution_time = time.time() - self._start_time
        
        # 添加结构化数据
        result_data = SwarmResult(
            success=failed == 0,
            output=final_output,
            tasks_completed=completed,
            tasks_failed=failed,
            total_iterations=self._iteration,
            execution_time=execution_time,
            agent_stats=self.scheduler.get_agent_stats()
        )
        
        # 添加任务详情（用于富文本展示）
        result_data.task_details = []
        for task in all_tasks:
            result_data.task_details.append({
                "id": task.id,
                "description": task.description,
                "status": task.status.value,
                "result": task.result,
                "error": task.error,
                "agent": task.assigned_to
            })
        
        return result_data
    
    def _display_result(self, result: SwarmResult, original_task: str):
        """展示执行结果（支持富文本）"""
        if self.rich_output:
            # 使用富文本展示
            self.rich_output.show_swarm_result(result, original_task)
            
            # 展示任务详情表格
            if hasattr(result, 'task_details') and result.task_details:
                if RICH_OUTPUT_AVAILABLE:
                    task_data = []
                    for td in result.task_details:
                        task_data.append(TaskDisplayData(
                            id=td['id'],
                            description=td['description'],
                            status=td['status'],
                            agent=td.get('agent', ''),
                            result=td.get('result', ''),
                            error=td.get('error', '')
                        ))
                    self.rich_output.show_task_table(task_data, "任务执行详情")
        elif self.verbose:
            # 使用普通文本展示
            print(f"\n{'='*60}")
            print(f"Swarm 执行完成")
            print(f"完成：{result.tasks_completed} 任务，失败：{result.tasks_failed}")
            print(f"耗时：{result.execution_time:.2f}秒")
            print(f"{'='*60}\n")
    
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
        all_tasks = self.task_graph.get_all_tasks()
        return {
            "running": self._running,
            "iteration": self._iteration,
            "total_tasks": len(all_tasks),
            "pending": sum(1 for t in all_tasks if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in all_tasks if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in all_tasks if t.status == TaskStatus.FAILED),
            "blackboard_keys": list(self.blackboard.get_all().keys())
        }
    
    def __repr__(self) -> str:
        return f"<SwarmOrchestrator agents={len(self.agent_pool)} running={self._running}>"
