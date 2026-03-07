#!/usr/bin/env python3
"""
测试重构后的架构

验证架构改进的正确性：
1. Agent 模块化 (AgentCore, AgentSerializer, AgentErrorEnhancer, AgentCloner)
2. DI Container
3. Strategy Pattern
4. WorkflowGenerator
5. AsyncAgentAdapter
"""

import sys
import os
import asyncio
import unittest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MockLLM:
    """模拟 LLM 用于测试"""
    
    def chat(self, messages: list, **kwargs) -> dict:
        """模拟聊天"""
        return {
            "content": "Hello, I am a test response",
            "tool_calls": []
        }


class MockTool:
    """模拟工具用于测试"""
    name = "MockTool"
    description = "A mock tool"
    
    def execute(self, **kwargs):
        from core.tool import ToolResult
        return ToolResult(success=True, output="Mock result")


class TestAgentModular(unittest.TestCase):
    """测试 Agent 模块化"""
    
    def test_agent_core_import(self):
        """测试 1: AgentCore 导入"""
        from core.agent_core import AgentCore
        self.assertIsNotNone(AgentCore)
    
    def test_agent_serializer_import(self):
        """测试 2: AgentSerializer 导入"""
        from core.agent_serializer import AgentSerializer
        self.assertIsNotNone(AgentSerializer)
    
    def test_agent_error_enhancer_import(self):
        """测试 3: AgentErrorEnhancer 导入"""
        from core.agent_error_enhancer import AgentErrorEnhancer
        self.assertIsNotNone(AgentErrorEnhancer)
    
    def test_agent_cloner_import(self):
        """测试 4: AgentCloner 导入"""
        from core.agent_cloner import AgentCloner
        self.assertIsNotNone(AgentCloner)
    
    def test_agent_facade(self):
        """测试 5: Agent Facade 模式"""
        from core import Agent
        from core.llm import OpenAILLM
        
        # 创建 Agent
        llm = MockLLM()
        agent = Agent(llm=llm, name="TestAgent")
        
        # 测试基本功能
        self.assertEqual(agent.name, "TestAgent")
        self.assertIsNotNone(agent.memory)
        self.assertIsNotNone(agent.tool_registry)
    
    def test_agent_serializer_functionality(self):
        """测试 6: Agent 序列化功能"""
        from core import Agent
        from core.agent_serializer import AgentSerializer
        
        llm = MockLLM()
        agent = Agent(llm=llm, name="SerializeTest")
        
        # 序列化
        data = agent.to_dict()
        self.assertIn("name", data)
        self.assertEqual(data["name"], "SerializeTest")
    
    def test_agent_error_enhancer_functionality(self):
        """测试 7: Agent 错误增强功能"""
        from core.agent_error_enhancer import AgentErrorEnhancer
        
        enhancer = AgentErrorEnhancer()
        
        # 测试 WebSearchTool 错误增强
        enhanced = enhancer.enhance_with_suggestions(
            "WebSearchTool",
            {"query": "天气"},
            "timeout error"
        )
        
        self.assertIn("错误", enhanced)
        self.assertIn("应对建议", enhanced)
    
    def test_agent_cloner_functionality(self):
        """测试 8: Agent 克隆功能"""
        from core import Agent
        from core.agent_cloner import AgentCloner
        
        llm = MockLLM()
        original = Agent(llm=llm, name="Original", instance_id="original-1")
        
        # 克隆
        cloned = AgentCloner.clone(original, "cloned-1")
        
        # 验证独立内存
        self.assertEqual(cloned.name, original.name)
        self.assertEqual(cloned.instance_id, "cloned-1")
        self.assertIsNot(original.memory, cloned.memory)


class TestDIContainer(unittest.TestCase):
    """测试依赖注入容器"""
    
    def test_container_import(self):
        """测试 1: DIContainer 导入"""
        from core.container import DIContainer
        self.assertIsNotNone(DIContainer)
    
    def test_container_register_get(self):
        """测试 2: 注册和获取服务"""
        from core.container import DIContainer
        
        container = DIContainer()
        
        # 注册
        container.register(str, "test_value")
        
        # 获取
        value = container.get(str)
        self.assertEqual(value, "test_value")
    
    def test_container_singleton(self):
        """测试 3: 单例模式"""
        from core.container import DIContainer
        
        container = DIContainer()
        
        class TestService:
            pass
        
        container.register(TestService, TestService, is_singleton=True)
        
        # 两次获取应该是同一实例
        s1 = container.get(TestService)
        s2 = container.get(TestService)
        
        self.assertIs(s1, s2)
    
    def test_container_factory(self):
        """测试 4: 工厂函数"""
        from core.container import DIContainer
        
        container = DIContainer()
        
        counter = [0]
        def factory():
            counter[0] += 1
            return f"instance-{counter[0]}"
        
        container.register_factory(str, factory)
        
        # 每次获取都调用工厂
        v1 = container.get(str)
        v2 = container.get(str)
        
        self.assertEqual(v1, "instance-1")
        self.assertEqual(v2, "instance-2")


class TestStrategyPattern(unittest.TestCase):
    """测试策略模式"""
    
    def test_strategies_import(self):
        """测试 1: 策略导入"""
        from core.strategies import (
            ExecutionStrategy,
            DirectStrategy,
            PlanReflectStrategy,
            TreeOfThoughtStrategy,
            StrategyFactory
        )
        self.assertIsNotNone(ExecutionStrategy)
        self.assertIsNotNone(DirectStrategy)
    
    def test_direct_strategy(self):
        """测试 2: 直接策略"""
        from core.strategies import DirectStrategy
        from core import Agent
        
        strategy = DirectStrategy()
        llm = MockLLM()
        agent = Agent(llm=llm)
        
        # 执行
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            strategy.execute(agent, "test task")
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.output)
    
    def test_strategy_factory(self):
        """测试 3: 策略工厂"""
        from core.strategies import StrategyFactory
        
        # 创建不同策略
        direct = StrategyFactory.create("direct")
        plan_reflect = StrategyFactory.create("plan_reflect")
        
        self.assertIsNotNone(direct)
        self.assertIsNotNone(plan_reflect)
    
    def test_enhanced_agent_with_strategy(self):
        """测试 4: EnhancedAgent 使用策略模式"""
        from core.agent_enhanced import EnhancedAgent
        from core.llm import OpenAILLM
        
        # 使用默认策略创建
        llm = MockLLM()
        agent = EnhancedAgent(llm=llm, strategy_name="direct")
        
        # 切换策略
        agent.set_strategy("plan_reflect")
        
        self.assertIsNotNone(agent._strategy)


class TestWorkflowGenerator(unittest.TestCase):
    """测试工作流生成器"""
    
    def test_workflow_generator_import(self):
        """测试 1: WorkflowGenerator 导入"""
        from core.workflow_generator import WorkflowGenerator
        self.assertIsNotNone(WorkflowGenerator)
    
    def test_workflow_generator_function(self):
        """测试 2: generate_workflow 函数"""
        from core import generate_workflow
        
        # 测试函数存在
        self.assertIsNotNone(generate_workflow)
    
    def test_workflow_structure(self):
        """测试 3: Workflow 结构"""
        from core import Workflow, Agent
        from core.llm import OpenAILLM
        
        llm = MockLLM()
        agent = Agent(llm=llm)
        
        workflow = Workflow("Test Workflow")
        workflow.add_step("Step1", agent)
        
        self.assertEqual(len(workflow.steps), 1)
        self.assertEqual(workflow.name, "Test Workflow")


class TestAsyncAdapter(unittest.TestCase):
    """测试异步适配器"""
    
    def test_async_adapter_import(self):
        """测试 1: AsyncAgentAdapter 导入"""
        from core.async_adapter import AsyncAgentAdapter
        self.assertIsNotNone(AsyncAgentAdapter)
    
    def test_async_adapter_wrapper(self):
        """测试 2: 包装同步 Agent"""
        from core import Agent
        from core.async_adapter import AsyncAgentAdapter
        
        llm = MockLLM()
        sync_agent = Agent(llm=llm, name="SyncAgent")
        
        # 包装
        async_agent = AsyncAgentAdapter(sync_agent)
        
        # 验证属性代理
        self.assertEqual(async_agent.name, "SyncAgent")
        self.assertIsNotNone(async_agent.memory)
    
    def test_async_adapter_run(self):
        """测试 3: 异步执行"""
        from core import Agent
        from core.async_adapter import AsyncAgentAdapter
        
        llm = MockLLM()
        sync_agent = Agent(llm=llm)
        async_agent = AsyncAgentAdapter(sync_agent)
        
        # 异步执行
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            async_agent.run("test task")
        )
        
        self.assertIsNotNone(result)


class TestArchitectureIntegration(unittest.TestCase):
    """测试架构集成"""
    
    def test_all_modules_importable(self):
        """测试 1: 所有模块可导入"""
        from core import (
            Agent,
            AgentCore,
            AgentSerializer,
            AgentErrorEnhancer,
            AgentCloner,
            DIContainer,
            ExecutionStrategy,
            DirectStrategy,
            PlanReflectStrategy,
            TreeOfThoughtStrategy,
            StrategyFactory,
            AsyncAgentAdapter,
            WorkflowGenerator,
            EnhancedAgent
        )
        
        # 如果导入成功，测试通过
        self.assertTrue(True)
    
    def test_no_circular_dependency(self):
        """测试 2: 无循环依赖"""
        # 如果以下导入成功，说明没有严重的循环依赖
        try:
            from core import Agent
            from core.resource import repo
            from core.factory import create_agent
            
            # 尝试创建 Agent
            llm = MockLLM()
            agent = Agent(llm=llm)
            
            self.assertIsNotNone(agent)
        except ImportError as e:
            self.fail(f"循环依赖导致导入失败：{e}")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestAgentModular))
    suite.addTests(loader.loadTestsFromTestCase(TestDIContainer))
    suite.addTests(loader.loadTestsFromTestCase(TestStrategyPattern))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestAsyncAdapter))
    suite.addTests(loader.loadTestsFromTestCase(TestArchitectureIntegration))
    
    # 运行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
