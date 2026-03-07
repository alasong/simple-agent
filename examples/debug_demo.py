#!/usr/bin/env python3
"""
调试功能演示

展示如何使用调试功能跟踪 Agent 和 Workflow 的执行
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    Agent, Workflow,
    enable_debug, disable_debug,
    print_debug_summary, get_debug_summary,
    tracker
)


class MockLLM:
    """模拟 LLM 用于演示"""
    
    def chat(self, messages: list, **kwargs) -> dict:
        last_msg = messages[-1]["content"] if messages else ""
        return {
            "content": f"[响应] 处理：{last_msg[:50]}",
            "tool_calls": []
        }


def demo_agent_debug():
    """演示 Agent 调试"""
    print("\n" + "="*70)
    print("演示 1: Agent 调试跟踪")
    print("="*70)
    
    llm = MockLLM()
    agent = Agent(llm=llm, name="演示 Agent")
    
    # 启用调试
    enable_debug(verbose=True)
    
    # 执行多次
    for i in range(3):
        print(f"\n--- 执行 {i+1} ---")
        result = agent.run(f"任务 {i+1}", verbose=False, debug=True)
    
    # 查看记录
    records = tracker.get_recent_agent_records()
    print(f"\n最近执行记录：{len(records)} 条")
    for r in records:
        print(f"  - {r['agent_name']}: {r['duration']:.3f}s")
    
    disable_debug()


def demo_workflow_debug():
    """演示 Workflow 调试"""
    print("\n" + "="*70)
    print("演示 2: Workflow 调试跟踪")
    print("="*70)
    
    llm = MockLLM()
    
    # 创建多个 Agent
    agent1 = Agent(llm=llm, name="分析 Agent")
    agent2 = Agent(llm=llm, name="处理 Agent")
    agent3 = Agent(llm=llm, name="报告 Agent")
    
    # 创建工作流
    workflow = Workflow("数据处理流程")
    workflow.add_step("分析", agent1, output_key="analysis")
    workflow.add_step("处理", agent2, input_key="analysis", output_key="processed")
    workflow.add_step("报告", agent3, input_key="processed")
    
    # 启用调试
    enable_debug(verbose=True)
    
    # 执行工作流
    context = workflow.run("处理数据：...", verbose=False, debug=True)
    
    disable_debug()


def demo_statistics():
    """演示统计功能"""
    print("\n" + "="*70)
    print("演示 3: 统计信息")
    print("="*70)
    
    llm = MockLLM()
    
    # 创建多个 Agent 执行
    enable_debug(verbose=False)
    
    agents = [
        Agent(llm=llm, name="Agent-A"),
        Agent(llm=llm, name="Agent-B"),
        Agent(llm=llm, name="Agent-C"),
    ]
    
    for agent in agents:
        agent.run("测试任务", debug=True)
    
    # 创建工作流执行
    workflow = Workflow("测试流程")
    workflow.add_step("步骤 1", agents[0])
    workflow.add_step("步骤 2", agents[1])
    workflow.run("测试", debug=True)
    
    # 获取统计
    summary = get_debug_summary()
    
    print("\n📊 Agent 统计:")
    agent_stats = summary['agent']
    print(f"  总执行：{agent_stats['count']} 次")
    print(f"  平均时长：{agent_stats['avg_duration']:.3f}s")
    
    if 'by_agent' in agent_stats:
        print("\n  按 Agent:")
        for name, stats in agent_stats['by_agent'].items():
            print(f"    {name}: {stats['count']}次, {stats['avg_duration']:.3f}s")
    
    print("\n📊 Workflow 统计:")
    wf_stats = summary['workflow']
    print(f"  总执行：{wf_stats['count']} 次")
    print(f"  步骤成功率：{wf_stats['step_success_rate']}%")
    
    disable_debug()


def demo_summary_display():
    """演示摘要显示"""
    print("\n" + "="*70)
    print("演示 4: 格式化摘要显示")
    print("="*70)
    
    llm = MockLLM()
    enable_debug(verbose=False)
    
    # 多次执行
    for i in range(5):
        agent = Agent(llm=llm, name=f"Agent-{i%2}")
        agent.run(f"任务 {i}", debug=True)
    
    # 打印摘要
    print_debug_summary()
    
    disable_debug()


if __name__ == "__main__":
    demo_agent_debug()
    demo_workflow_debug()
    demo_statistics()
    demo_summary_display()
    
    print("\n" + "="*70)
    print("演示完成!")
    print("="*70)
