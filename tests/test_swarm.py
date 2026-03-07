"""
Swarm 组件单元测试
"""

import asyncio
import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swarm.blackboard import Blackboard, Change
from swarm.message_bus import MessageBus, Message
from swarm.scheduler import Task, TaskStatus, TaskGraph, TaskScheduler, TaskDecomposer
from swarm.orchestrator import SwarmOrchestrator, SwarmResult
from swarm.collaboration_patterns import (
    PairProgramming,
    SwarmBrainstorming,
    MarketBasedAllocation,
    CodeReviewLoop,
    CollaborationResult
)


class MockAgent:
    """模拟 Agent 用于测试"""
    
    def __init__(self, name: str = "MockAgent", description: str = "", skills: list = None):
        self.name = name
        self.description = description or f"Mock agent with skills: {skills}"
        self.instance_id = name
        self.skills = skills or []
        self.run_count = 0
        self.last_input = None
    
    def run(self, user_input: str, verbose: bool = False) -> str:
        """模拟执行"""
        self.run_count += 1
        self.last_input = user_input
        
        # 简单响应：回显输入
        if "审查" in user_input or "review" in user_input.lower():
            return "LGTM 代码通过审查"
        elif "实现" in user_input:
            return f"def solution():\n    # 实现：{user_input[:50]}"
        elif "方案" in user_input or "想法" in user_input:
            return '{"ideas": [{"name": "方案 A", "description": "测试方案"}]}'
        else:
            return f"Agent {self.name} 处理：{user_input[:100]}"


class MockLLM:
    """模拟 LLM 用于测试"""
    
    async def chat(self, messages: list, **kwargs) -> dict:
        """模拟聊天"""
        last_msg = messages[-1]["content"] if messages else ""
        
        # 任务分解响应
        if "分解" in last_msg or "decompose" in last_msg.lower():
            return {
                "content": """{
                    "tasks": [
                        {
                            "id": "1",
                            "description": "分析需求",
                            "required_skills": ["analysis"],
                            "dependencies": [],
                            "priority": 1
                        },
                        {
                            "id": "2",
                            "description": "实现功能",
                            "required_skills": ["coding"],
                            "dependencies": ["1"],
                            "priority": 2
                        }
                    ]
                }"""
            }
        
        # 默认响应
        return {"content": "完成"}


class TestBlackboard(unittest.TestCase):
    """测试共享黑板"""
    
    def test_write_read(self):
        """测试读写"""
        bb = Blackboard()
        bb.write("key1", "value1", "agent1")
        
        self.assertEqual(bb.read("key1"), "value1")
        self.assertIsNone(bb.read("nonexistent"))
    
    def test_get_with_default(self):
        """测试带默认值的获取"""
        bb = Blackboard()
        self.assertEqual(bb.get("key", "default"), "default")
    
    def test_get_all(self):
        """测试获取所有"""
        bb = Blackboard()
        bb.write("k1", "v1", "a1")
        bb.write("k2", "v2", "a2")
        
        all_data = bb.get_all()
        self.assertEqual(len(all_data), 2)
        self.assertIn("k1", all_data)
    
    def test_history(self):
        """测试历史记录"""
        bb = Blackboard()
        bb.write("key", "v1", "a1")
        bb.write("key", "v2", "a2")
        
        history = bb.get_history("key")
        self.assertEqual(len(history), 2)
    
    def test_clear(self):
        """测试清空"""
        bb = Blackboard()
        bb.write("key", "value", "agent")
        bb.clear()
        
        self.assertEqual(len(bb.get_all()), 0)
        self.assertEqual(len(bb.history), 0)


class TestMessageBus(unittest.TestCase):
    """测试消息总线"""
    
    def setUp(self):
        self.bus = MessageBus()
    
    def tearDown(self):
        asyncio.run(self.bus.stop())
    
    def test_subscribe_publish(self):
        """测试订阅发布"""
        received = []
        
        async def callback(msg):
            received.append(msg)
        
        self.bus.subscribe("test", callback)
        
        async def run():
            await self.bus.start()
            await self.bus.publish("test", "hello", "sender")
            await asyncio.sleep(0.2)
        
        asyncio.run(run())
        
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].content, "hello")
    
    def test_broadcast(self):
        """测试广播"""
        received = []
        
        async def callback(msg):
            received.append(msg)
        
        self.bus.subscribe("__all__", callback)
        
        async def run():
            await self.bus.start()
            await self.bus.broadcast("msg", "sender")
            await asyncio.sleep(0.2)
        
        asyncio.run(run())
        
        self.assertGreater(len(received), 0)


class TestTask(unittest.TestCase):
    """测试任务定义"""
    
    def test_task_creation(self):
        """测试任务创建"""
        task = Task(id="1", description="Test task")
        self.assertEqual(task.id, "1")
        self.assertEqual(task.status, TaskStatus.PENDING)
    
    def test_task_dependencies(self):
        """测试依赖检查"""
        task = Task(
            id="1",
            description="Test",
            dependencies=["dep1", "dep2"]
        )
        
        self.assertFalse(task.is_ready(set()))
        self.assertTrue(task.is_ready({"dep1", "dep2"}))
    
    def test_task_mark_completed(self):
        """测试标记完成"""
        task = Task(id="1", description="Test")
        task.mark_running("agent1")
        task.mark_completed("result")
        
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(task.result, "result")
        self.assertIsNotNone(task.completed_at)


class TestTaskGraph(unittest.TestCase):
    """测试任务图"""
    
    def test_build_graph(self):
        """测试构建图"""
        tasks = [
            Task(id="1", description="Task 1"),
            Task(id="2", description="Task 2", dependencies=["1"]),
        ]
        
        graph = TaskGraph()
        graph.build_from_tasks(tasks)
        
        self.assertEqual(len(graph.nodes), 2)
    
    def test_get_ready_tasks(self):
        """测试获取就绪任务"""
        tasks = [
            Task(id="1", description="Task 1"),
            Task(id="2", description="Task 2", dependencies=["1"]),
        ]
        
        graph = TaskGraph()
        graph.build_from_tasks(tasks)
        
        # 初始只有任务 1 就绪
        ready = graph.get_ready_tasks()
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0].id, "1")
        
        # 完成任务 1 后，任务 2 就绪
        graph.get_task("1").mark_completed("done")
        ready = graph.get_ready_tasks()
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0].id, "2")


class TestTaskScheduler(unittest.TestCase):
    """测试任务调度器"""
    
    def test_select_agent(self):
        """测试 Agent 选择"""
        agents = [
            MockAgent("Developer", "I am a developer", ["coding"]),
            MockAgent("Tester", "I am a tester", ["testing"]),
        ]
        
        scheduler = TaskScheduler(agents)
        
        # 选择编码任务
        task = Task(id="1", description="Code", required_skills=["coding"])
        agent = scheduler.select_agent(task)
        self.assertEqual(agent.name, "Developer")
    
    def test_load_balancing(self):
        """测试负载均衡"""
        agents = [
            MockAgent("Agent1"),
            MockAgent("Agent2"),
        ]
        
        scheduler = TaskScheduler(agents)
        
        # 分配任务
        task1 = Task(id="1", description="Task 1")
        task2 = Task(id="2", description="Task 2")
        
        asyncio.run(scheduler.assign_task(task1))
        asyncio.run(scheduler.assign_task(task2))
        
        # 检查负载分布
        stats = scheduler.get_agent_stats()
        self.assertEqual(stats["avg_load"], 1.0)


class TestSwarmOrchestrator(unittest.TestCase):
    """测试群体控制器"""
    
    def test_basic_execution(self):
        """测试基本执行"""
        agents = [
            MockAgent("Agent1", "coding"),
            MockAgent("Agent2", "testing"),
        ]
        
        orchestrator = SwarmOrchestrator(
            agent_pool=agents,
            max_iterations=10,
            verbose=False
        )
        
        # 创建简单任务图
        tasks = [Task(id="1", description="Simple task")]
        orchestrator._build_task_graph(tasks)
        
        # 运行（使用同步包装）
        async def run():
            return await orchestrator._execute_loop("Test task")
        
        result = asyncio.run(run())
        
        self.assertIsInstance(result, SwarmResult)
        self.assertGreater(result.execution_time, 0)
    
    def test_status(self):
        """测试状态查询"""
        agents = [MockAgent("A1")]
        orchestrator = SwarmOrchestrator(agent_pool=agents, verbose=False)
        
        status = orchestrator.status
        self.assertIn("running", status)
        self.assertIn("iteration", status)


class TestCollaborationPatterns(unittest.TestCase):
    """测试协作模式"""
    
    def test_pair_programming(self):
        """测试结对编程"""
        driver = MockAgent("Driver", "I write code")
        navigator = MockAgent("Navigator", "I review code")
        
        pp = PairProgramming(driver, navigator, max_iterations=3)
        
        async def run():
            return await pp.execute("实现一个函数", verbose=False)
        
        result = asyncio.run(run())
        
        self.assertIsInstance(result, CollaborationResult)
        self.assertTrue(result.success)
        self.assertEqual(len(result.participants), 2)
    
    def test_market_allocation(self):
        """测试市场分配"""
        agents = [
            MockAgent("Agent1", "Expert coder", ["coding"]),
            MockAgent("Agent2", "Expert tester", ["testing"]),
        ]
        
        mba = MarketBasedAllocation(agents)
        
        async def run():
            return await mba.allocate("编写代码", verbose=False)
        
        winner, bid = asyncio.run(run())
        
        self.assertIn(winner, agents)
        self.assertGreaterEqual(bid, 0.0)
        self.assertLessEqual(bid, 1.0)
    
    def test_swarm_brainstorming_structure(self):
        """测试头脑风暴结构"""
        agents = [
            MockAgent("Agent1"),
            MockAgent("Agent2"),
            MockAgent("Agent3"),
        ]
        
        sb = SwarmBrainstorming(agents)
        
        # 验证初始化
        self.assertEqual(len(sb.agents), 3)


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Swarm 组件测试")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestBlackboard))
    suite.addTests(loader.loadTestsFromTestCase(TestMessageBus))
    suite.addTests(loader.loadTestsFromTestCase(TestTask))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskGraph))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestSwarmOrchestrator))
    suite.addTests(loader.loadTestsFromTestCase(TestCollaborationPatterns))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("所有测试通过！")
    else:
        print(f"测试失败：{len(result.failures)} 个失败，{len(result.errors)} 个错误")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
