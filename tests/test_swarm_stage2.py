#!/usr/bin/env python3
"""
阶段 2 功能测试 - Swarm 核心
"""
import asyncio
import sys
sys.path.insert(0, '/home/song/simple-agent')


async def test_blackboard():
    """测试共享黑板"""
    from swarm.blackboard import Blackboard
    
    bb = Blackboard()
    bb.write("task1", "结果 1", "Agent1")
    bb.write("task2", "结果 2", "Agent2")
    
    assert bb.read("task1") == "结果 1"
    assert len(bb.get_all()) == 2
    
    print('✓ Blackboard 测试通过')


async def test_message_bus():
    """测试消息总线"""
    from swarm.message_bus import MessageBus
    
    bus = MessageBus()
    received = []
    
    async def callback(msg):
        received.append(msg.content)
    
    bus.subscribe("test", callback)
    
    await bus.start()
    await bus.publish("test", "hello", "sender")
    await asyncio.sleep(0.2)
    await bus.stop()
    
    assert len(received) > 0
    assert received[0] == "hello"
    
    print('✓ MessageBus 测试通过')


async def test_task_scheduler():
    """测试任务调度器"""
    from swarm.scheduler import Task, TaskScheduler, TaskGraph
    
    # 模拟 Agent
    class MockAgent:
        def __init__(self, name, skills):
            self.name = name
            self.instance_id = name
            self.description = " ".join(skills)
    
    agents = [
        MockAgent("Developer", ["coding"]),
        MockAgent("Tester", ["testing"]),
    ]
    
    scheduler = TaskScheduler(agents)
    task = Task(id="1", description="编码任务", required_skills=["coding"])
    
    selected = scheduler.select_agent(task)
    assert selected.name == "Developer"
    
    print('✓ TaskScheduler 测试通过')


async def test_swarm_orchestrator():
    """测试群体控制器"""
    from swarm.orchestrator import SwarmOrchestrator
    from swarm.scheduler import Task
    
    # 模拟 Agent
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.instance_id = name
            self.description = "通用 Agent"
        
        def run(self, user_input, verbose=False):
            return f"{self.name} 完成：{user_input[:30]}"
    
    agents = [MockAgent("Agent1"), MockAgent("Agent2")]
    
    orchestrator = SwarmOrchestrator(agent_pool=agents, verbose=False)
    
    # 创建任务
    tasks = [
        Task(id="1", description="任务 1"),
        Task(id="2", description="任务 2", dependencies=["1"]),
    ]
    orchestrator._build_task_graph(tasks)
    
    # 执行
    result = await orchestrator._execute_loop("测试任务")
    
    assert hasattr(result, 'tasks_completed')
    assert hasattr(result, 'execution_time')
    
    print('✓ SwarmOrchestrator 测试通过')


async def test_collaboration_patterns():
    """测试协作模式"""
    from swarm.collaboration_patterns import PairProgramming, MarketBasedAllocation
    
    # 模拟 Agent
    class MockAgent:
        def __init__(self, name, role=""):
            self.name = name
            self.instance_id = name
            self.description = role
            self.run_count = 0
        
        def run(self, user_input, verbose=False):
            self.run_count += 1
            if "审查" in user_input or "review" in user_input.lower():
                return "LGTM"
            elif "实现" in user_input:
                return "def solution(): pass"
            elif "评估" in user_input or "bid" in user_input.lower():
                return "0.8"
            return "完成"
    
    # 测试结对编程
    driver = MockAgent("Driver")
    navigator = MockAgent("Navigator")
    pp = PairProgramming(driver, navigator, max_iterations=2)
    result = await pp.execute("实现功能", verbose=False)
    assert result.success == True
    
    # 测试市场分配
    agents = [MockAgent("Agent1", "expert"), MockAgent("Agent2", "junior")]
    mba = MarketBasedAllocation(agents)
    winner, bid = await mba.allocate("任务", verbose=False)
    assert winner in agents
    assert 0.0 <= bid <= 1.0
    
    print('✓ Collaboration Patterns 测试通过')


async def test_integration():
    """集成测试：完整的 Swarm 流程"""
    from swarm.orchestrator import SwarmOrchestrator
    from swarm.scheduler import Task
    from swarm.blackboard import Blackboard
    from swarm.message_bus import MessageBus
    
    # 模拟 Agent
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.instance_id = name
            self.description = "通用"
        
        def run(self, user_input, verbose=False):
            return f"结果：{user_input[:20]}"
    
    # 创建组件
    agents = [MockAgent("A1"), MockAgent("A2")]
    orchestrator = SwarmOrchestrator(agent_pool=agents, verbose=False)
    
    # 验证组件初始化
    assert isinstance(orchestrator.blackboard, Blackboard)
    assert isinstance(orchestrator.message_bus, MessageBus)
    assert orchestrator.scheduler.agent_pool == agents
    
    print('✓ Integration 测试通过')


async def main():
    print('=' * 60)
    print('阶段 2 功能测试 - Swarm 核心')
    print('=' * 60)
    
    tests = [
        test_blackboard,
        test_message_bus,
        test_task_scheduler,
        test_swarm_orchestrator,
        test_collaboration_patterns,
        test_integration,
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
