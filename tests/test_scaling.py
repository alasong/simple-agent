"""
动态扩展测试
"""
import asyncio
import sys
sys.path.insert(0, '/home/song/simple-agent')

from swarm.scaling import ScalingMetrics, AgentFactory, DynamicScaling, AutoScalingOrchestrator


class MockAgent:
    """模拟 Agent"""
    def __init__(self, name="Agent", skills=None, description=None, **kwargs):
        self.name = name
        self.instance_id = name or kwargs.get('instance_id', name)
        self.description = description or " ".join(skills or [])
        self.call_count = 0
    
    def run(self, user_input, verbose=False):
        self.call_count += 1
        return f"结果"


class MockOrchestrator:
    """模拟 Orchestrator"""
    def __init__(self, agents):
        self.agent_pool = agents
        self.task_graph = MockTaskGraph()
        self.scheduler = MockScheduler(agents)
    
    def get_all_tasks(self):
        return self.task_graph.tasks


class MockTaskGraph:
    def __init__(self):
        self.tasks = []
    
    def get_all_tasks(self):
        return self.tasks


class MockScheduler:
    def __init__(self, agents):
        self.agent_pool = agents
        self.agent_load = {a.instance_id: 0 for a in agents}
    
    def get_agent_stats(self):
        return {
            'avg_load': sum(self.agent_load.values()) / max(1, len(self.agent_load)),
            'load_distribution': self.agent_load.copy()
        }


async def test_scaling_metrics():
    """测试扩展指标"""
    metrics = ScalingMetrics(
        avg_wait_time=30,
        idle_ratio=0.5,
        task_queue_size=5,
        avg_load=0.6
    )
    
    # 默认不扩展
    assert not metrics.needs_scaling()
    assert not metrics.needs_shrinking()
    
    # 高负载需要扩展
    metrics.avg_wait_time = 70
    assert metrics.needs_scaling()
    
    # 低负载需要缩减
    metrics.avg_wait_time = 10
    metrics.idle_ratio = 0.8
    metrics.task_queue_size = 2
    metrics.avg_load = 0.2
    assert metrics.needs_shrinking()
    
    print('✓ ScalingMetrics 测试通过')


async def test_agent_factory():
    """测试 Agent 工厂"""
    factory = AgentFactory(agent_class=MockAgent)
    
    # 创建通用 Agent
    agent = await factory.create()
    assert isinstance(agent, MockAgent)
    
    # 创建特定技能 Agent
    agent = await factory.create(skill="coding", name="Coder")
    assert "coding" in agent.name.lower() or "coding" in agent.description.lower()
    
    # 注册自定义创建器
    def create_special_agent(name="Special"):
        a = MockAgent(name=name, skills=["special"])
        return a
    
    factory.register_creator("special", create_special_agent)
    agent = await factory.create(skill="special")
    assert "special" in agent.description
    
    print('✓ AgentFactory 测试通过')


async def test_dynamic_scaling():
    """测试动态扩展"""
    # 创建初始 Agent 池
    agents = [MockAgent(f"A{i}") for i in range(2)]
    orchestrator = MockOrchestrator(agents)
    
    # 创建动态扩展
    scaling = DynamicScaling(
        orchestrator,
        min_agents=1,
        max_agents=5,
        cooldown_seconds=1
    )
    
    # 设置工厂
    scaling.factory = AgentFactory(agent_class=MockAgent)
    
    initial_count = len(orchestrator.agent_pool)
    
    # 手动扩展
    from swarm.scaling import ScalingMetrics
    metrics = ScalingMetrics(
        avg_wait_time=70,
        idle_ratio=0.1,
        task_queue_size=15,
        bottleneck_skill="coding"
    )
    
    await scaling._scale_up(metrics)
    
    assert len(orchestrator.agent_pool) == initial_count + 1
    print(f'  扩展后 Agent 数量：{len(orchestrator.agent_pool)}')
    
    # 手动缩减
    metrics.idle_ratio = 0.9
    metrics.task_queue_size = 1
    metrics.avg_load = 0.1
    
    await scaling._scale_down(metrics)
    
    assert len(orchestrator.agent_pool) == initial_count
    print(f'  缩减后 Agent 数量：{len(orchestrator.agent_pool)}')
    
    print('✓ DynamicScaling 测试通过')


async def test_auto_scaling_orchestrator():
    """测试自动扩展 Orchestrator"""
    from swarm.orchestrator import SwarmOrchestrator
    
    agents = [MockAgent(f"A{i}") for i in range(2)]
    orchestrator = SwarmOrchestrator(agent_pool=agents, verbose=False)
    
    auto = AutoScalingOrchestrator(
        orchestrator,
        min_agents=1,
        max_agents=5,
        cooldown_seconds=1
    )
    
    # 验证代理
    assert auto.agent_pool == orchestrator.agent_pool
    assert auto.blackboard == orchestrator.blackboard
    
    print('✓ AutoScalingOrchestrator 结构测试通过')


async def test_scaling_callbacks():
    """测试扩展回调"""
    agents = [MockAgent(f"A{i}") for i in range(2)]
    orchestrator = MockOrchestrator(agents)
    
    scaling = DynamicScaling(orchestrator, min_agents=1, max_agents=5)
    scaling.factory = AgentFactory(agent_class=MockAgent)
    
    events = []
    
    def on_up(agent):
        events.append(("up", agent.name))
    
    def on_down(agent):
        events.append(("down", agent.name))
    
    scaling.on_scale_up(on_up)
    scaling.on_scale_down(on_down)
    
    # 触发扩展
    from swarm.scaling import ScalingMetrics
    await scaling._scale_up(ScalingMetrics(bottleneck_skill="coding"))
    await scaling._scale_down(ScalingMetrics(
        idle_ratio=0.9,
        task_queue_size=1,
        avg_load=0.1
    ))
    
    assert len(events) == 2
    assert events[0][0] == "up"
    assert events[1][0] == "down"
    
    print('✓ Scaling 回调测试通过')


async def main():
    print('=' * 60)
    print('动态扩展测试')
    print('=' * 60)
    
    tests = [
        test_scaling_metrics,
        test_agent_factory,
        test_dynamic_scaling,
        test_auto_scaling_orchestrator,
        test_scaling_callbacks,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f'✗ {test.__name__} 失败：{e}')
            import traceback
            traceback.print_exc()
            failed += 1
    
    print('=' * 60)
    print(f'测试完成：{passed} 通过，{failed} 失败')
    print('=' * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
