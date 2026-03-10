"""
动态调度器 (Dynamic Scheduler)

负责任务调度、Agent 匹配、失败重试和实时监控

架构:
┌─────────────────────────────────────────────────────────┐
│              DynamicScheduler                           │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Task-Agent Matcher                               │  │
│  │  - 基于技能匹配                                   │  │
│  │  - 考虑负载平衡                                   │  │
│  │  - 优先级调度                                     │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Retry Manager                                    │  │
│  │  - 指数退避重试                                   │  │
│  │  - 降级策略                                       │  │
│  │  - 失败隔离                                       │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Real-time Monitor                                │  │
│  │  - 任务进度跟踪                                   │  │
│  │  - Agent 状态监控                                  │  │
│  │  - 动态调整调度                                   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import random


class SchedulerStatus(Enum):
    """调度器状态"""
    IDLE = "idle"           # 空闲
    RUNNING = "running"     # 运行中
    PAUSED = "paused"       # 已暂停
    STOPPED = "stopped"     # 已停止


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 1    # 关键
    HIGH = 2        # 高
    MEDIUM = 3      # 中
    LOW = 4         # 低


@dataclass
class AgentInfo:
    """Agent 信息"""
    instance_id: str
    name: str
    skills: List[str] = field(default_factory=list)
    current_load: int = 0
    max_load: int = 5
    success_rate: float = 1.0
    avg_execution_time: float = 0.0
    is_available: bool = True
    last_task_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'instance_id': self.instance_id,
            'name': self.name,
            'skills': self.skills,
            'current_load': self.current_load,
            'max_load': self.max_load,
            'success_rate': self.success_rate,
            'avg_execution_time': self.avg_execution_time,
            'is_available': self.is_available
        }


@dataclass
class ScheduledTask:
    """已调度的任务"""
    id: str
    description: str
    required_skills: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_agent: Optional[str] = None
    status: str = "pending"
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'description': self.description,
            'required_skills': self.required_skills,
            'priority': self.priority.value,
            'assigned_agent': self.assigned_agent,
            'status': self.status,
            'retry_count': self.retry_count,
            'result': self.result,
            'error': self.error,
            'dependencies': self.dependencies
        }

    def is_ready(self, completed_tasks: set[str]) -> bool:
        """检查任务是否准备执行"""
        if self.status != "pending":
            return False
        return all(dep in completed_tasks for dep in self.dependencies)

    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.retry_count < self.max_retries

    def reset_for_retry(self):
        """重置为可执行状态"""
        self.status = "pending"
        self.assigned_agent = None
        self.started_at = None
        self.retry_count += 1


@dataclass
class ExecutionResult:
    """执行结果"""
    task_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    agent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'success': self.success,
            'result': self.result,
            'error': self.error,
            'execution_time': self.execution_time,
            'agent_id': self.agent_id
        }


class DynamicScheduler:
    """动态调度器"""

    def __init__(
        self,
        agents: Optional[List[Any]] = None,
        llm=None,
        max_concurrent_tasks: int = 5,
        retry_delay_base: float = 1.0,
        retry_delay_max: float = 30.0
    ):
        """
        初始化调度器

        Args:
            agents: Agent 列表
            llm: LLM 实例，用于智能匹配
            max_concurrent_tasks: 最大并发任务数
            retry_delay_base: 重试基础延迟（秒）
            retry_delay_max: 最大重试延迟（秒）
        """
        self.agents: Dict[str, AgentInfo] = {}
        self.tasks: Dict[str, ScheduledTask] = {}
        self.llm = llm
        self.max_concurrent_tasks = max_concurrent_tasks
        self.retry_delay_base = retry_delay_base
        self.retry_delay_max = retry_delay_max

        # 状态
        self.status = SchedulerStatus.IDLE
        self._running = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # 默认不暂停

        # 执行跟踪
        self._completed_tasks: set[str] = set()
        self._failed_tasks: set[str] = set()
        self._current_executions: Dict[str, asyncio.Task] = {}

        # 统计信息
        self._total_tasks_scheduled = 0
        self._total_tasks_completed = 0
        self._total_tasks_failed = 0
        self._agent_task_count: Dict[str, int] = defaultdict(int)
        self._agent_success_count: Dict[str, int] = defaultdict(int)
        self._agent_execution_times: Dict[str, List[float]] = defaultdict(list)

        # 回调
        self._on_task_start: Optional[Callable] = None
        self._on_task_complete: Optional[Callable] = None
        self._on_task_failed: Optional[Callable] = None

        # 注册 Agents
        if agents:
            for agent in agents:
                self.register_agent(agent)

    def register_agent(self, agent: Any, skills: Optional[List[str]] = None):
        """
        注册 Agent

        Args:
            agent: Agent 实例
            skills: 技能列表（如果不提供，从 Agent 名称推断）
        """
        instance_id = getattr(agent, 'instance_id', getattr(agent, 'name', str(agent)))
        name = getattr(agent, 'name', 'Unknown')

        # 自动推断技能
        if not skills:
            skills = self._infer_skills(agent)

        self.agents[instance_id] = AgentInfo(
            instance_id=instance_id,
            name=name,
            skills=skills
        )

    def _infer_skills(self, agent: Any) -> List[str]:
        """从 Agent 推断技能"""
        name = getattr(agent, 'name', '').lower()
        description = getattr(agent, 'description', '').lower()
        text = f"{name} {description}"

        # 从配置加载技能关键词，避免硬编码
        from configs.common_keywords import CommonKeywordsConfig
        skill_keywords = CommonKeywordsConfig.get_skill_keywords()

        skills = []
        for skill, keywords in skill_keywords.items():
            if any(kw in text for kw in keywords):
                skills.append(skill)

        # 默认技能
        if not skills:
            skills.append('general')

        return skills

    def add_task(
        self,
        task_id: str,
        description: str,
        required_skills: Optional[List[str]] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: Optional[List[str]] = None
    ) -> ScheduledTask:
        """
        添加任务

        Args:
            task_id: 任务 ID
            description: 任务描述
            required_skills: 所需技能
            priority: 优先级
            dependencies: 依赖的任务 ID

        Returns:
            ScheduledTask: 创建的任务
        """
        task = ScheduledTask(
            id=task_id,
            description=description,
            required_skills=required_skills or [],
            priority=priority,
            dependencies=dependencies or []
        )
        self.tasks[task_id] = task
        self._total_tasks_scheduled += 1
        return task

    def select_agent_for_task(self, task: ScheduledTask) -> Optional[str]:
        """
        为任务选择合适的 Agent

        匹配算法:
        1. 筛选满足技能要求的 Agent
        2. 排除不可用或超负载的 Agent
        3. 根据成功率和负载计算得分
        4. 选择得分最高的 Agent

        Args:
            task: 任务

        Returns:
            str: 选中的 Agent ID，如果没有合适的返回 None
        """
        candidates = []

        for agent_id, agent_info in self.agents.items():
            # 检查可用性
            if not agent_info.is_available:
                continue
            if agent_info.current_load >= agent_info.max_load:
                continue

            # 检查技能匹配
            if task.required_skills:
                if not self._matches_skills(agent_info, task.required_skills):
                    continue

            # 计算得分
            score = self._calculate_agent_score(agent_info, task)
            candidates.append((agent_id, score))

        if not candidates:
            return None

        # 按得分排序，选择最高的
        candidates.sort(key=lambda x: x[1], reverse=True)

        # 前几名中随机选择，避免总是选择同一个 Agent
        top_n = min(3, len(candidates))
        top_candidates = candidates[:top_n]

        # 加权随机选择（得分高的概率大）
        total_score = sum(s for _, s in top_candidates)
        if total_score > 0:
            weights = [s / total_score for _, s in top_candidates]
            selected = random.choices(top_candidates, weights=weights, k=1)[0]
        else:
            selected = random.choice(top_candidates)

        return selected[0]

    def _matches_skills(self, agent: AgentInfo, required_skills: List[str]) -> bool:
        """检查 Agent 是否满足技能要求"""
        if not required_skills:
            return True

        agent_skills_lower = [s.lower() for s in agent.skills]

        for skill in required_skills:
            skill_lower = skill.lower()
            # 精确匹配
            if skill_lower in agent_skills_lower:
                return True
            # 模糊匹配
            if any(skill_lower in s or s in skill_lower for s in agent_skills_lower):
                return True

        return False

    def _calculate_agent_score(self, agent: AgentInfo, task: ScheduledTask) -> float:
        """
        计算 Agent 得分

        考虑因素:
        - 技能匹配度 (40%)
        - 成功率 (30%)
        - 当前负载 (20%)
        - 平均执行时间 (10%)

        Returns:
            float: 得分 (0-1)
        """
        # 技能匹配度
        if task.required_skills:
            matching_skills = sum(
                1 for s in task.required_skills
                if any(s.lower() in agent_skill.lower() or agent_skill.lower() in s.lower()
                       for agent_skill in agent.skills)
            )
            skill_score = matching_skills / len(task.required_skills)
        else:
            skill_score = 1.0

        # 成功率
        success_score = agent.success_rate

        # 负载得分（负载越低得分越高）
        load_score = 1.0 - (agent.current_load / max(agent.max_load, 1))

        # 执行时间得分（时间越短得分越高，归一化到 0-1）
        if agent.avg_execution_time > 0:
            time_score = 1.0 / (1.0 + agent.avg_execution_time / 60.0)  # 60 秒基准
        else:
            time_score = 1.0

        # 加权得分
        total_score = (
            skill_score * 0.4 +
            success_score * 0.3 +
            load_score * 0.2 +
            time_score * 0.1
        )

        return total_score

    async def execute_task(
        self,
        task: ScheduledTask,
        agent: Any,
        verbose: bool = True
    ) -> ExecutionResult:
        """
        执行任务

        Args:
            task: 任务
            agent: 执行任务的 Agent
            verbose: 是否打印详细过程

        Returns:
            ExecutionResult: 执行结果
        """
        agent_id = getattr(agent, 'instance_id', getattr(agent, 'name', str(agent)))
        start_time = time.time()

        try:
            # 更新任务状态
            task.status = "running"
            task.started_at = start_time
            task.assigned_agent = agent_id

            # 更新 Agent 负载
            if agent_id in self.agents:
                self.agents[agent_id].current_load += 1
                self.agents[agent_id].last_task_time = start_time

            # 回调
            if self._on_task_start:
                await self._on_task_start(task, agent)

            if verbose:
                print(f"[执行] 任务 {task.id} -> Agent {agent_id}")

            # 准备输入
            task_input = task.description

            # 执行任务（支持同步和异步 Agent）
            if asyncio.iscoroutinefunction(agent.run):
                result = await agent.run(task_input, verbose=False)
            else:
                # 同步执行
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: agent.run(task_input, verbose=False))

            # 计算执行时间
            execution_time = time.time() - start_time

            # 更新 Agent 统计
            self._update_agent_stats(agent_id, True, execution_time)

            # 更新任务状态
            task.status = "completed"
            task.completed_at = time.time()
            task.result = result
            self._completed_tasks.add(task.id)
            self._total_tasks_completed += 1

            # 回调
            if self._on_task_complete:
                await self._on_task_complete(task, result)

            if verbose:
                print(f"[完成] 任务 {task.id} (耗时：{execution_time:.2f}s)")

            return ExecutionResult(
                task_id=task.id,
                success=True,
                result=result,
                execution_time=execution_time,
                agent_id=agent_id
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)

            # 更新 Agent 统计
            self._update_agent_stats(agent_id, False, execution_time)

            # 更新任务状态
            task.error = error_msg

            if verbose:
                print(f"[失败] 任务 {task.id}: {error_msg}")

            return ExecutionResult(
                task_id=task.id,
                success=False,
                error=error_msg,
                execution_time=execution_time,
                agent_id=agent_id
            )
        finally:
            # 释放 Agent 负载
            if agent_id in self.agents:
                self.agents[agent_id].current_load -= 1

    def _update_agent_stats(self, agent_id: str, success: bool, execution_time: float):
        """更新 Agent 统计信息"""
        if agent_id not in self.agents:
            return

        agent_info = self.agents[agent_id]

        # 更新任务计数
        self._agent_task_count[agent_id] += 1
        if success:
            self._agent_success_count[agent_id] += 1

        # 更新成功率
        total = self._agent_task_count[agent_id]
        success_count = self._agent_success_count[agent_id]
        agent_info.success_rate = success_count / total if total > 0 else 1.0

        # 更新平均执行时间
        self._agent_execution_times[agent_id].append(execution_time)
        # 只保留最近 10 次
        if len(self._agent_execution_times[agent_id]) > 10:
            self._agent_execution_times[agent_id] = self._agent_execution_times[agent_id][-10:]
        agent_info.avg_execution_time = sum(self._agent_execution_times[agent_id]) / len(self._agent_execution_times[agent_id])

    async def execute_with_retry(
        self,
        task: ScheduledTask,
        agent: Any,
        verbose: bool = True
    ) -> ExecutionResult:
        """
        带重试的执行

        使用指数退避策略:
        - 第 1 次重试：延迟 1-2 秒
        - 第 2 次重试：延迟 2-4 秒
        - 第 3 次重试：延迟 4-8 秒
        - ...

        Args:
            task: 任务
            agent: Agent
            verbose: 是否打印详细过程

        Returns:
            ExecutionResult: 执行结果
        """
        last_result = None

        while task.can_retry() or last_result is None:
            result = await self.execute_task(task, agent, verbose)
            last_result = result

            if result.success:
                return result

            # 失败，准备重试
            task.reset_for_retry()

            if not task.can_retry():
                break

            # 计算延迟（指数退避 + 随机抖动）
            delay = min(
                self.retry_delay_base * (2 ** task.retry_count),
                self.retry_delay_max
            )
            jitter = random.uniform(0.1, 0.3) * delay
            total_delay = delay + jitter

            if verbose:
                print(f"[重试] 任务 {task.id}，{total_delay:.1f}秒后重试 (第 {task.retry_count} 次)")

            await asyncio.sleep(total_delay)

            # 重试时可能更换 Agent
            if task.retry_count > 0:
                new_agent_id = self.select_agent_for_task(task)
                if new_agent_id and new_agent_id != agent:
                    agent = self._get_agent_by_id(new_agent_id)
                    if verbose:
                        print(f"[调度] 任务 {task.id} 重新分配给 Agent {new_agent_id}")

        # 所有重试失败
        task.status = "failed"
        task.completed_at = time.time()
        self._failed_tasks.add(task.id)
        self._total_tasks_failed += 1

        if self._on_task_failed:
            await self._on_task_failed(task, last_result.error if last_result else "Unknown error")

        return last_result

    def _get_agent_by_id(self, agent_id: str) -> Optional[Any]:
        """根据 ID 获取 Agent 实例"""
        # 这个方法需要外部传入 Agent 池才能工作
        # 这里返回 None，实际使用时需要重写或传入 Agent 池
        return None

    async def schedule_and_execute(
        self,
        tasks: Optional[List[ScheduledTask]] = None,
        agent_pool: Optional[List[Any]] = None,
        verbose: bool = True,
        parallel: bool = True
    ) -> Dict[str, ExecutionResult]:
        """
        调度并执行任务

        Args:
            tasks: 任务列表，如果不提供则使用 self.tasks
            agent_pool: Agent 池，如果不提供则使用已注册的 Agent
            verbose: 是否打印详细过程
            parallel: 是否并行执行

        Returns:
            Dict[str, ExecutionResult]: 任务 ID 到执行结果的映射
        """
        if tasks is None:
            tasks = list(self.tasks.values())

        if not tasks:
            return {}

        # 如果没有 agent_pool，尝试从已注册的 Agent 获取
        # 注意：这里需要外部提供实际的 Agent 实例
        if agent_pool is None:
            raise ValueError("需要提供 agent_pool 或预先注册 Agent")

        self._running = True
        self.status = SchedulerStatus.RUNNING
        results: Dict[str, ExecutionResult] = {}

        try:
            if parallel:
                # 并行执行
                results = await self._execute_parallel(tasks, agent_pool, verbose)
            else:
                # 顺序执行
                results = await self._execute_sequential(tasks, agent_pool, verbose)

        finally:
            self._running = False
            self.status = SchedulerStatus.IDLE

        return results

    async def _execute_parallel(
        self,
        tasks: List[ScheduledTask],
        agent_pool: List[Any],
        verbose: bool = True
    ) -> Dict[str, ExecutionResult]:
        """并行执行任务"""
        results = {}
        completed_tasks: set[str] = set()
        pending_tasks = list(tasks)

        while pending_tasks:
            # 获取就绪任务
            ready_tasks = [
                t for t in pending_tasks
                if t.is_ready(completed_tasks)
            ]

            if not ready_tasks:
                if pending_tasks:
                    # 有任务但未就绪，检查是否有失败任务阻塞
                    blocked = any(
                        any(dep in self._failed_tasks for dep in t.dependencies)
                        for t in pending_tasks
                    )
                    if blocked:
                        # 有任务被失败任务阻塞，标记为失败
                        for t in pending_tasks:
                            if any(dep in self._failed_tasks for dep in t.dependencies):
                                t.status = "failed"
                                t.error = "依赖任务失败"
                                self._failed_tasks.add(t.id)
                        continue

                # 没有就绪任务，退出
                break

            # 限制并发数
            batch = ready_tasks[:self.max_concurrent_tasks]

            # 为每个任务分配 Agent 并执行
            execution_tasks = []
            for task in batch:
                agent_id = self.select_agent_for_task(task)
                if agent_id:
                    # 查找对应的 Agent 实例
                    for agent in agent_pool:
                        a_id = getattr(agent, 'instance_id', getattr(agent, 'name', str(agent)))
                        if a_id == agent_id:
                            execution_tasks.append(self.execute_with_retry(task, agent, verbose))
                            pending_tasks.remove(task)
                            break
                else:
                    # 没有合适的 Agent，降级处理
                    if agent_pool:
                        agent = min(agent_pool, key=lambda a: getattr(a, '_current_load', 0))
                        execution_tasks.append(self.execute_with_retry(task, agent, verbose))
                        pending_tasks.remove(task)

            if not execution_tasks:
                break

            # 并行执行
            batch_results = await asyncio.gather(*execution_tasks, return_exceptions=True)

            # 处理结果
            for task, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    task.status = "failed"
                    task.error = str(result)
                    self._failed_tasks.add(task.id)
                    results[task.id] = ExecutionResult(
                        task_id=task.id,
                        success=False,
                        error=str(result)
                    )
                elif isinstance(result, ExecutionResult):
                    results[task.id] = result
                    if result.success:
                        completed_tasks.add(task.id)
                    else:
                        self._failed_tasks.add(task.id)

        return results

    async def _execute_sequential(
        self,
        tasks: List[ScheduledTask],
        agent_pool: List[Any],
        verbose: bool = True
    ) -> Dict[str, ExecutionResult]:
        """顺序执行任务"""
        results = {}
        completed_tasks: set[str] = set()

        # 拓扑排序
        sorted_tasks = self._topological_sort(tasks)

        for task in sorted_tasks:
            if task.is_ready(completed_tasks):
                agent_id = self.select_agent_for_task(task)
                if agent_id:
                    for agent in agent_pool:
                        a_id = getattr(agent, 'instance_id', getattr(agent, 'name', str(agent)))
                        if a_id == agent_id:
                            result = await self.execute_with_retry(task, agent, verbose)
                            results[task.id] = result
                            if result.success:
                                completed_tasks.add(task.id)
                            break
                else:
                    # 降级：选择负载最低的 Agent
                    agent = min(agent_pool, key=lambda a: getattr(a, '_current_load', 0))
                    result = await self.execute_with_retry(task, agent, verbose)
                    results[task.id] = result
                    if result.success:
                        completed_tasks.add(task.id)
            else:
                task.status = "blocked"
                task.error = "依赖未满足"
                results[task.id] = ExecutionResult(
                    task_id=task.id,
                    success=False,
                    error="依赖任务未完成"
                )

        return results

    def _topological_sort(self, tasks: List[ScheduledTask]) -> List[ScheduledTask]:
        """拓扑排序"""
        # 构建依赖图
        task_map = {t.id: t for t in tasks}
        in_degree = {t.id: 0 for t in tasks}

        for task in tasks:
            for dep in task.dependencies:
                if dep in task_map:
                    in_degree[task.id] += 1

        # Kahn 算法
        queue = [t for t in tasks if in_degree[t.id] == 0]
        result = []

        while queue:
            # 按优先级排序
            queue.sort(key=lambda t: t.priority.value)
            task = queue.pop(0)
            result.append(task)

            for t in tasks:
                if task.id in t.dependencies:
                    in_degree[t.id] -= 1
                    if in_degree[t.id] == 0:
                        queue.append(t)

        return result

    def pause(self):
        """暂停调度"""
        self._pause_event.clear()
        self.status = SchedulerStatus.PAUSED

    def resume(self):
        """恢复调度"""
        self._pause_event.set()
        self.status = SchedulerStatus.RUNNING

    def stop(self):
        """停止调度"""
        self._running = False
        self._pause_event.set()
        self.status = SchedulerStatus.STOPPED

    async def wait_for_pause(self):
        """等待直到未暂停状态"""
        await self._pause_event.wait()

    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            'status': self.status.value,
            'running': self._running,
            'total_tasks': len(self.tasks),
            'completed': len(self._completed_tasks),
            'failed': len(self._failed_tasks),
            'pending': len(self.tasks) - len(self._completed_tasks) - len(self._failed_tasks),
            'agents': {aid: info.to_dict() for aid, info in self.agents.items()},
            'stats': {
                'total_scheduled': self._total_tasks_scheduled,
                'total_completed': self._total_tasks_completed,
                'total_failed': self._total_tasks_failed
            }
        }

    def get_agent_load(self, agent_id: str) -> int:
        """获取 Agent 当前负载"""
        return self.agents.get(agent_id, AgentInfo("", "")).current_load

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务"""
        return self.tasks.get(task_id)

    def on_task_start(self, callback: Callable[[ScheduledTask, Any], Awaitable[None]]):
        """注册任务开始回调"""
        self._on_task_start = callback

    def on_task_complete(self, callback: Callable[[ScheduledTask, Any], Awaitable[None]]):
        """注册任务完成回调"""
        self._on_task_complete = callback

    def on_task_failed(self, callback: Callable[[ScheduledTask, str], Awaitable[None]]):
        """注册任务失败回调"""
        self._on_task_failed = callback


# 便捷函数
def create_scheduler(
    agents: Optional[List[Any]] = None,
    llm=None,
    max_concurrent: int = 5
) -> DynamicScheduler:
    """创建调度器"""
    return DynamicScheduler(agents=agents, llm=llm, max_concurrent_tasks=max_concurrent)


# 从 dependency_graph 的任务图创建调度任务
def create_tasks_from_graph(graph: Any) -> List[ScheduledTask]:
    """
    从任务依赖图创建调度任务

    Args:
        graph: TaskGraph 实例

    Returns:
        List[ScheduledTask]: 调度任务列表
    """
    tasks = []

    for node in graph.get_all_tasks():
        priority_map = {1: TaskPriority.CRITICAL, 2: TaskPriority.HIGH,
                        3: TaskPriority.MEDIUM, 4: TaskPriority.LOW}
        priority = priority_map.get(getattr(node, 'priority', 3), TaskPriority.MEDIUM)

        # 获取依赖
        dependencies = []
        if hasattr(graph, 'graph'):
            dependencies = list(graph.graph.predecessors(node.id))

        task = ScheduledTask(
            id=node.id,
            description=getattr(node, 'name', node.id),
            required_skills=[getattr(node, 'agent_type', 'general')],
            priority=priority,
            dependencies=dependencies,
            metadata=getattr(node, 'metadata', {})
        )
        tasks.append(task)

    return tasks
