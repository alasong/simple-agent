"""
动态扩展（Dynamic Scaling）

根据任务负载自动扩展或缩减 Agent 池
"""

import asyncio
import time
from typing import Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ScalingMetrics:
    """扩展指标"""
    avg_wait_time: float = 0.0  # 平均等待时间（秒）
    idle_ratio: float = 0.0     # 空闲 Agent 比例
    task_queue_size: int = 0    # 任务队列大小
    bottleneck_skill: str = ""  # 瓶颈技能
    avg_load: float = 0.0       # 平均负载
    peak_load: float = 0.0      # 峰值负载
    
    def needs_scaling(self) -> bool:
        """是否需要扩展"""
        return (
            self.avg_wait_time > 60 or  # 等待超过 60 秒
            self.task_queue_size > 10 or  # 队列超过 10 个任务
            (self.idle_ratio < 0.2 and self.avg_load > 0.8)  # 高负载且低空闲
        )
    
    def needs_shrinking(self) -> bool:
        """是否需要缩减"""
        return (
            self.idle_ratio > 0.7 and  # 70% 空闲
            self.task_queue_size < 3 and  # 队列少于 3 个任务
            self.avg_load < 0.3  # 平均负载低于 30%
        )


class AgentFactory:
    """Agent 工厂"""
    
    def __init__(self, agent_class: type = None, config_template: dict = None):
        self.agent_class = agent_class
        self.config_template = config_template or {}
        self._creators: dict[str, Callable] = {}
    
    def register_creator(self, skill: str, creator: Callable):
        """注册特定技能的创建器"""
        self._creators[skill] = creator
    
    async def create(self, skill: str = None, **kwargs) -> Any:
        """创建 Agent"""
        # 使用特定技能的创建器
        if skill and skill in self._creators:
            creator = self._creators[skill]
            if asyncio.iscoroutinefunction(creator):
                return await creator(**kwargs)
            return creator(**kwargs)
        
        # 使用默认创建器
        if self.agent_class:
            config = {**self.config_template, **kwargs}
            if skill:
                config['name'] = f"{skill.title()}Agent"
                config['description'] = f"Specialized in {skill}"
            
            return self.agent_class(**config)
        
        raise ValueError("未配置 Agent 创建器")


class DynamicScaling:
    """动态 Agent 扩展"""
    
    def __init__(
        self,
        orchestrator: Any,
        factory: AgentFactory = None,
        min_agents: int = 1,
        max_agents: int = 10,
        scale_up_threshold: float = 0.8,
        scale_down_threshold: float = 0.3,
        cooldown_seconds: int = 60
    ):
        self.orchestrator = orchestrator
        self.factory = factory or AgentFactory()
        self.min_agents = min_agents
        self.max_agents = max_agents
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.cooldown_seconds = cooldown_seconds
        
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._last_scale_time: float = 0
        self._metrics_history: list[ScalingMetrics] = []
        self._callbacks: dict[str, list[Callable]] = defaultdict(list)
    
    async def start(self):
        """启动自动扩展监控"""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        """停止自动扩展"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                # 收集指标
                metrics = await self._collect_metrics()
                self._metrics_history.append(metrics)
                
                # 检查是否需要扩展
                if time.time() - self._last_scale_time > self.cooldown_seconds:
                    if metrics.needs_scaling():
                        await self._scale_up(metrics)
                    elif metrics.needs_shrinking():
                        await self._scale_down(metrics)
                
                await asyncio.sleep(10)  # 每 10 秒检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[DynamicScaling] 监控错误：{e}")
                await asyncio.sleep(10)
    
    async def _collect_metrics(self) -> ScalingMetrics:
        """收集扩展指标"""
        agent_pool = self.orchestrator.agent_pool
        scheduler = self.orchestrator.scheduler
        
        # 获取负载统计
        stats = scheduler.get_agent_stats()
        avg_load = stats.get('avg_load', 0)
        load_distribution = stats.get('load_distribution', {})
        
        # 计算空闲比例
        idle_count = sum(1 for load in load_distribution.values() if load == 0)
        idle_ratio = idle_count / max(1, len(agent_pool))
        
        # 估计等待时间（简化：基于队列大小和平均处理时间）
        task_queue_size = len([
            t for t in self.orchestrator.task_graph.get_all_tasks()
            if t.status.value == 'pending'
        ])
        avg_wait_time = task_queue_size * 5  # 假设每个任务 5 秒
        
        # 识别瓶颈技能
        bottleneck_skill = self._identify_bottleneck()
        
        return ScalingMetrics(
            avg_wait_time=avg_wait_time,
            idle_ratio=idle_ratio,
            task_queue_size=task_queue_size,
            bottleneck_skill=bottleneck_skill,
            avg_load=avg_load,
            peak_load=max(load_distribution.values()) if load_distribution else 0
        )
    
    def _identify_bottleneck(self) -> str:
        """识别瓶颈技能"""
        # 分析等待中的任务，找出最常见的技能需求
        pending_tasks = [
            t for t in self.orchestrator.task_graph.get_all_tasks()
            if t.status == type('TaskStatus', (), {'PENDING': 'pending'}).PENDING
        ]
        
        skill_count = defaultdict(int)
        for task in pending_tasks:
            for skill in task.required_skills:
                skill_count[skill] += 1
        
        if skill_count:
            return max(skill_count.items(), key=lambda x: x[1])[0]
        return ""
    
    async def _scale_up(self, metrics: ScalingMetrics):
        """扩展 Agent 池"""
        skill = metrics.bottleneck_skill or "general"
        
        if len(self.orchestrator.agent_pool) >= self.max_agents:
            print(f"[DynamicScaling] 已达到最大 Agent 数量：{self.max_agents}")
            return
        
        print(f"[DynamicScaling] 扩展：添加 {skill} Agent...")
        
        try:
            new_agent = await self.factory.create(skill=skill)
            self.orchestrator.agent_pool.append(new_agent)
            
            # 更新调度器
            self.orchestrator.scheduler.agent_pool = self.orchestrator.agent_pool
            self.orchestrator.scheduler.agent_load[new_agent.instance_id or new_agent.name] = 0
            
            self._last_scale_time = time.time()
            
            await self._emit("scale_up", new_agent)
            
            print(f"[DynamicScaling] 已添加 Agent: {new_agent.name}")
            
        except Exception as e:
            print(f"[DynamicScaling] 扩展失败：{e}")
    
    async def _scale_down(self, metrics: ScalingMetrics):
        """缩减 Agent 池"""
        if len(self.orchestrator.agent_pool) <= self.min_agents:
            print(f"[DynamicScaling] 已达到最小 Agent 数量：{self.min_agents}")
            return
        
        # 找到最空闲的 Agent
        load_distribution = self.orchestrator.scheduler.agent_load
        idle_agents = [
            agent for agent in self.orchestrator.agent_pool
            if load_distribution.get(agent.instance_id or agent.name, 0) == 0
        ]
        
        if not idle_agents:
            return
        
        # 移除最空闲的（除了第一个）
        to_remove = idle_agents[-1] if len(idle_agents) > 1 else idle_agents[0]
        
        print(f"[DynamicScaling] 缩减：移除 Agent {to_remove.name}...")
        
        self.orchestrator.agent_pool.remove(to_remove)
        self.orchestrator.scheduler.agent_pool = self.orchestrator.agent_pool
        
        if to_remove.instance_id in self.orchestrator.scheduler.agent_load:
            del self.orchestrator.scheduler.agent_load[to_remove.instance_id]
        
        self._last_scale_time = time.time()
        
        await self._emit("scale_down", to_remove)
        
        print(f"[DynamicScaling] 已移除 Agent: {to_remove.name}")
    
    def on_scale_up(self, callback: Callable):
        """注册扩展回调"""
        self._callbacks["scale_up"].append(callback)
    
    def on_scale_down(self, callback: Callable):
        """注册缩减回调"""
        self._callbacks["scale_down"].append(callback)
    
    async def _emit(self, event: str, agent: Any):
        """触发事件"""
        for callback in self._callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(agent)
                else:
                    callback(agent)
            except Exception as e:
                print(f"[DynamicScaling] 回调执行失败：{e}")
    
    def get_metrics(self) -> ScalingMetrics:
        """获取当前指标"""
        if self._metrics_history:
            return self._metrics_history[-1]
        return ScalingMetrics()
    
    def get_history(self) -> list[ScalingMetrics]:
        """获取历史指标"""
        return self._metrics_history.copy()


class AutoScalingOrchestrator:
    """带自动扩展的 Swarm Orchestrator"""
    
    def __init__(self, orchestrator: Any, **scaling_kwargs):
        self.orchestrator = orchestrator
        self.factory = AgentFactory(
            agent_class=type(orchestrator.agent_pool[0]) if orchestrator.agent_pool else None
        )
        self.scaling = DynamicScaling(orchestrator, self.factory, **scaling_kwargs)
        
        # 设置回调
        self.scaling.on_scale_up(self._on_agent_added)
        self.scaling.on_scale_down(self._on_agent_removed)
    
    async def solve(self, task: str) -> Any:
        """解决任务（带自动扩展）"""
        # 启动自动扩展
        await self.scaling.start()
        
        try:
            # 执行任务
            result = await self.orchestrator.solve(task)
            return result
        finally:
            # 停止自动扩展
            await self.scaling.stop()
    
    def _on_agent_added(self, agent: Any):
        """Agent 添加回调"""
        print(f"[AutoScaling] Agent 池更新：{len(self.orchestrator.agent_pool)} 个 Agent")
    
    def _on_agent_removed(self, agent: Any):
        """Agent 移除回调"""
        print(f"[AutoScaling] Agent 池更新：{len(self.orchestrator.agent_pool)} 个 Agent")
    
    def __getattr__(self, name):
        """代理到内部 orchestrator"""
        return getattr(self.orchestrator, name)


# 使用示例
async def demo_auto_scaling():
    """演示自动扩展"""
    from swarm import SwarmOrchestrator
    from simple_agent.swarm.scheduler import Task
    
    # 模拟 Agent 类
    class MockAgent:
        def __init__(self, name="Agent", skills=None):
            self.name = name
            self.instance_id = name
            self.description = " ".join(skills or [])
        
        def run(self, user_input, verbose=False):
            return f"结果：{user_input[:20]}"
    
    # 创建初始 Agent 池
    initial_agents = [MockAgent(f"Agent{i}", ["coding"]) for i in range(2)]
    
    # 创建 Orchestrator
    orchestrator = SwarmOrchestrator(
        agent_pool=initial_agents,
        verbose=True
    )
    
    # 创建任务
    tasks = [
        Task(id=str(i), description=f"任务 {i}", required_skills=["coding"])
        for i in range(10)
    ]
    orchestrator._build_task_graph(tasks)
    
    # 创建自动扩展
    auto_scaling = AutoScalingOrchestrator(
        orchestrator,
        min_agents=2,
        max_agents=5,
        cooldown_seconds=10
    )
    
    # 执行（会自动扩展）
    result = await auto_scaling.solve("复杂任务")
    
    print(f"\n最终 Agent 数量：{len(orchestrator.agent_pool)}")
    print(f"任务完成：{result.tasks_completed}")


if __name__ == "__main__":
    asyncio.run(demo_auto_scaling())
