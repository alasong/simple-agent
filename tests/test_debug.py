#!/usr/bin/env python3
"""
调试功能测试
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import (
    Agent, Workflow, 
    enable_debug, disable_debug,
    print_debug_summary, get_debug_summary
)
from core.llm import OpenAILLM


class MockLLM:
    def chat(self, messages: list, **kwargs) -> dict:
        last_msg = messages[-1]["content"] if messages else ""
        
        if "step" in last_msg.lower() or "步骤" in last_msg:
            return {
                "content": f"完成步骤：{last_msg[:50]}",
                "tool_calls": []
            }
        
        return {
            "content": f"响应：{last_msg[:100]}",
            "tool_calls": []
        }


def test_agent_debug():
    """测试 Agent 调试跟踪"""
    print("\n" + "="*60)
    print("测试 1: Agent 调试跟踪")
    print("="*60)
    
    llm = MockLLM()
    agent = Agent(llm=llm, name="TestAgent")
    
    result = agent.run("Hello, test!", verbose=False, debug=True)
    print(f"Agent 执行结果：{result[:100]}...")


def test_workflow_debug():
    """测试 Workflow 调试跟踪"""
    print("\n" + "="*60)
    print("测试 2: Workflow 调试跟踪")
    print("="*60)
    
    llm = MockLLM()
    
    agent1 = Agent(llm=llm, name="Agent1")
    agent2 = Agent(llm=llm, name="Agent2")
    
    workflow = Workflow("测试工作流")
    workflow.add_step("步骤 1", agent1, output_key="result1")
    workflow.add_step("步骤 2", agent2, input_key="result1", output_key="result2")
    
    context = workflow.run("初始输入", verbose=False, debug=True)
    print(f"Workflow 执行完成")


def test_debug_summary():
    """测试调试摘要"""
    print("\n" + "="*60)
    print("测试 3: 调试摘要")
    print("="*60)
    
    summary = get_debug_summary()
    print(f"调试摘要：{summary}")
    
    print_debug_summary()


def test_verbose_debug():
    """测试详细调试输出"""
    print("\n" + "="*60)
    print("测试 4: 详细调试输出")
    print("="*60)
    
    enable_debug(verbose=True)
    
    llm = MockLLM()
    agent = Agent(llm=llm, name="VerboseAgent")
    
    result = agent.run("详细测试", verbose=True, debug=True)
    print(f"结果：{result}")
    
    disable_debug()


if __name__ == "__main__":
    test_agent_debug()
    test_workflow_debug()
    test_debug_summary()
    test_verbose_debug()
    
    print("\n" + "="*60)
    print("所有调试测试完成!")
    print("="*60)
