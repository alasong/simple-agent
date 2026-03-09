#!/usr/bin/env python3
"""
测试简化后的架构

验证架构改进的正确性：
1. Agent 统一实现（序列化、克隆、错误增强内置）
2. Strategy Pattern
3. WorkflowGenerator
4. AsyncAgentAdapter
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


class TestAgentUnified(unittest.TestCase):
    """测试 Agent 统一实现"""

    def test_agent_import(self):
        """测试 1: Agent 导入"""
        from core.agent import Agent
        self.assertIsNotNone(Agent)

    def test_agent_error_enhancer_import(self):
        """测试 2: AgentErrorEnhancer 导入"""
        from core.agent import AgentErrorEnhancer
        self.assertIsNotNone(AgentErrorEnhancer)

    def test_agent_creation(self):
        """测试 3: Agent 创建"""
        from core.agent import Agent

        llm = MockLLM()
        agent = Agent(llm=llm, name="TestAgent")

        self.assertEqual(agent.name, "TestAgent")
        self.assertIsNotNone(agent.memory)
        self.assertIsNotNone(agent.tool_registry)

    def test_agent_serialization(self):
        """测试 4: Agent 序列化"""
        from core.agent import Agent

        llm = MockLLM()
        agent = Agent(llm=llm, name="TestAgent")

        # 序列化
        data = agent.to_dict()

        self.assertEqual(data["name"], "TestAgent")
        self.assertIn("memory", data)
        self.assertIn("tools", data)

    def test_agent_clone(self):
        """测试 5: Agent 克隆"""
        from core.agent import Agent

        llm = MockLLM()
        original = Agent(llm=llm, name="Original", instance_id="orig-1")

        # 克隆
        cloned = original.clone(new_instance_id="cloned-1")

        # 验证独立内存
        self.assertEqual(cloned.name, original.name)
        self.assertEqual(cloned.instance_id, "cloned-1")
        self.assertIsNot(original.memory, cloned.memory)


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

    def test_strategy_execution(self):
        """测试 2: 策略执行"""
        from core.strategies import DirectStrategy

        strategy = DirectStrategy()
        # 策略应该可以被实例化
        self.assertIsNotNone(strategy)


class TestWorkflowGenerator(unittest.TestCase):
    """测试工作流生成器"""

    def test_workflow_generator_import(self):
        """测试 1: 工作流生成器导入"""
        from core.workflow_generator import WorkflowGenerator
        self.assertIsNotNone(WorkflowGenerator)


class TestAsyncAgentAdapter(unittest.TestCase):
    """测试异步 Agent 适配器"""

    def test_async_adapter_import(self):
        """测试 1: 异步适配器导入"""
        from core.async_adapter import AsyncAgentAdapter
        self.assertIsNotNone(AsyncAgentAdapter)


class TestArchitectureIntegration(unittest.TestCase):
    """测试架构集成"""

    def test_all_modules_importable(self):
        """测试 1: 所有模块可导入"""
        from core import (
            Agent,
            AgentInfo,
            AgentErrorEnhancer,
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
        from core import Agent
        from core.resource import repo

        try:
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
    suite.addTests(loader.loadTestsFromTestCase(TestAgentUnified))
    suite.addTests(loader.loadTestsFromTestCase(TestStrategyPattern))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestAsyncAgentAdapter))
    suite.addTests(loader.loadTestsFromTestCase(TestArchitectureIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
