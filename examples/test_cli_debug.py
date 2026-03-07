#!/usr/bin/env python3
"""
CLI Debug 命令测试脚本

测试 /debug summary 和 /debug stats 命令的功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import enable_debug, Agent, Workflow
from core import print_debug_summary, tracker

# 创建模拟 LLM
class MockLLM:
    def chat(self, messages: list, **kwargs) -> dict:
        last_msg = messages[-1]["content"] if messages else ""
        return {
            "content": f"[响应] 处理：{last_msg[:50]}",
            "tool_calls": []
        }


def setup_test_data():
    """创建测试数据"""
    print("=" * 60)
    print("准备测试数据...")
    print("=" * 60)
    
    # 启用调试
    enable_debug(verbose=False)
    
    llm = MockLLM()
    
    # 创建多个 Agent
    agent1 = Agent(llm=llm, name="代码审查员", version="1.0")
    agent2 = Agent(llm=llm, name="测试生成器", version="1.0")
    agent3 = Agent(llm=llm, name="文档助手", version="1.0")
    
    print("\n✓ 创建 3 个 Agent")
    
    # 运行 Agent 多次
    print("\n执行 Agent 任务...")
    for i in range(3):
        result = agent1.run(f"审查这段代码：test_{i}.py", debug=True)
        print(f"  - 代码审查员执行 {i+1}/3")
    
    for i in range(2):
        result = agent2.run(f"生成测试用例：test_{i}.py", debug=True)
        print(f"  - 测试生成器执行 {i+1}/2")
    
    result = agent3.run("编写文档说明", debug=True)
    print(f"  - 文档助手执行 1/1")
    
    # 创建 Workflow
    print("\n创建工作流...")
    workflow1 = Workflow("代码审查工作流")
    workflow1.add_step("静态分析", agent1)
    workflow1.add_step("生成测试", agent2)
    workflow1.add_step("更新文档", agent3)
    
    workflow2 = Workflow("快速审查工作流")
    workflow2.add_step("快速审查", agent1)
    
    print("✓ 创建 2 个工作流")
    
    # 运行 Workflow
    print("\n执行工作流任务...")
    result = workflow1.run("审查 main.py", debug=True)
    print("  - 代码审查工作流执行 1/2")
    
    result = workflow1.run("审查 utils.py", debug=True)
    print("  - 代码审查工作流执行 2/2")
    
    result = workflow2.run("快速审查 config.py", debug=True)
    print("  - 快速审查工作流执行 1/1")
    
    print("\n✓ 测试数据准备完成")
    print("=" * 60)


def test_debug_summary():
    """测试 /debug summary 命令"""
    print("\n" + "=" * 60)
    print("测试：/debug summary 命令")
    print("=" * 60)
    
    print("\n调用 print_debug_summary():\n")
    print_debug_summary()


def test_debug_stats():
    """测试 /debug stats 命令"""
    print("\n" + "=" * 60)
    print("测试：/debug stats 命令")
    print("=" * 60)
    
    # 获取 Agent 统计
    agent_stats = tracker.get_agent_stats()
    print("\n📊 Agent 执行统计:")
    print(f"  总执行次数：{agent_stats.get('count', 0)}")
    print(f"  成功：{agent_stats.get('successful', 0)}")
    print(f"  失败：{agent_stats.get('failed', 0)}")
    if agent_stats.get('count', 0) > 0:
        print(f"  成功率：{agent_stats.get('success_rate', 0):.1%}")
        print(f"  平均耗时：{agent_stats.get('avg_duration', 0):.3f}秒")
    
    # 按 Agent 分类统计
    if 'by_agent' in agent_stats and agent_stats['by_agent']:
        print(f"\n  按 Agent 分类:")
        for agent_name, stats in agent_stats['by_agent'].items():
            print(f"    - {agent_name}:")
            print(f"        执行：{stats.get('count', 0)} 次")
            print(f"        平均耗时：{stats.get('avg_duration', 0):.3f}秒")
            print(f"        工具调用：{stats.get('total_tool_calls', 0)} 次")
    
    # 获取 Workflow 统计
    workflow_stats = tracker.get_workflow_stats()
    print(f"\n📊 Workflow 执行统计:")
    print(f"  总执行次数：{workflow_stats.get('count', 0)}")
    print(f"  成功：{workflow_stats.get('successful', 0)}")
    print(f"  失败：{workflow_stats.get('failed', 0)}")
    if workflow_stats.get('count', 0) > 0:
        print(f"  成功率：{workflow_stats.get('success_rate', 0):.1%}")
        print(f"  平均耗时：{workflow_stats.get('avg_duration', 0):.3f}秒")
        print(f"  总步骤数：{workflow_stats.get('total_steps', 0)}")
        print(f"  步骤成功率：{workflow_stats.get('step_success_rate', 0):.1%}")
    
    # 按 Workflow 分类统计
    if 'by_workflow' in workflow_stats and workflow_stats['by_workflow']:
        print(f"\n  按 Workflow 分类:")
        for workflow_name, stats in workflow_stats['by_workflow'].items():
            print(f"    - {workflow_name}:")
            print(f"        执行：{stats.get('count', 0)} 次")
            print(f"        平均步骤：{stats.get('avg_steps', 0):.1f}")
            print(f"        平均耗时：{stats.get('avg_duration', 0):.3f}秒")


def test_recent_records():
    """测试获取最近执行记录"""
    print("\n" + "=" * 60)
    print("测试：获取最近执行记录")
    print("=" * 60)
    
    # 获取最近的 Agent 执行记录
    agent_records = tracker.get_recent_agent_records(limit=5)
    print(f"\n最近 5 条 Agent 执行记录:")
    for i, record in enumerate(agent_records, 1):
        print(f"  {i}. {record['agent_name']} - {record['duration']:.3f}s - {'✓' if record['success'] else '✗'}")
    
    # 获取最近的 Workflow 执行记录
    workflow_records = tracker.get_recent_workflow_records(limit=5)
    print(f"\n最近 5 条 Workflow 执行记录:")
    for i, record in enumerate(workflow_records, 1):
        print(f"  {i}. {record['workflow_name']} - {record['total_steps']}步 - {record['duration']:.3f}s - {'✓' if record['success'] else '✗'}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("CLI Debug 命令测试")
    print("=" * 60)
    
    # 设置测试数据
    setup_test_data()
    
    # 测试各种命令
    test_debug_summary()
    test_debug_stats()
    test_recent_records()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print("\n提示：")
    print("  在 CLI 交互模式中，可以使用以下命令查看调试信息:")
    print("    /debug summary  - 显示调试摘要")
    print("    /debug stats    - 显示详细统计信息")
    print("    /debug on       - 启用调试模式")
    print("    /debug off      - 关闭调试模式")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
