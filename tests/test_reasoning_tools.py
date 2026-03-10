#!/usr/bin/env python3
"""
推理工具测试

测试新增的多路径探索工具：
- TreeOfThoughtTool: 思维树多路径探索
- IterativeOptimizerTool: 多轮迭代优化
- SwarmVotingTool: 群体投票决策
- MultiPathOptimizerTool: 多路径并行优化

使用方法:
    .venv/bin/python tests/test_reasoning_tools.py
"""

import sys
import os
import asyncio

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def create_test_agent():
    """创建测试用 Agent"""
    from core.agent import Agent
    from core.llm import get_llm

    llm = get_llm()
    return Agent(
        llm=llm,
        name="TestAgent",
        system_prompt="你是一个专业的助手，提供高质量的答案。"
    )


async def test_tree_of_thought():
    """测试思维树工具"""
    print("\n" + "=" * 60)
    print("测试：TreeOfThoughtTool - 思维树多路径探索")
    print("=" * 60)

    from tools.reasoning_tools import TreeOfThoughtTool

    agent = create_test_agent()
    tool = TreeOfThoughtTool(agent, breadth=3, depth=2)

    problem = "如何设计一个支持百万并发的即时通讯系统？"

    print(f"\n问题：{problem}")
    print(f"配置：breadth=3, depth=2")

    result = await tool.execute(problem, verbose=True)

    print(f"\n结果:")
    print(f"  最佳方案评分：{result.get('best_score', 0):.2f}")
    print(f"  总思路数：{result.get('total_thoughts', 0)}")
    print(f"  执行时间：{result.get('execution_time', 0):.2f}秒")
    print(f"\n最佳方案预览:")
    print(f"  {result.get('best_solution', '')[:300]}...")

    return result.get('success', False)


async def test_iterative_optimizer():
    """测试迭代优化工具"""
    print("\n" + "=" * 60)
    print("测试：IterativeOptimizerTool - 多轮迭代优化")
    print("=" * 60)

    from tools.reasoning_tools import IterativeOptimizerTool

    agent = create_test_agent()
    tool = IterativeOptimizerTool(agent, max_iterations=2, quality_threshold=0.7)

    problem = "编写一个 Python 函数，实现 LRU 缓存机制"

    print(f"\n问题：{problem}")
    print(f"配置：max_iterations=2, quality_threshold=0.7")

    result = await tool.execute(problem, verbose=True)

    print(f"\n结果:")
    print(f"  最终评分：{result.get('final_score', 0):.2f}")
    print(f"  迭代次数：{result.get('total_iterations', 0)}")
    print(f"  执行时间：{result.get('execution_time', 0):.2f}秒")
    print(f"  是否成功：{result.get('success', False)}")
    print(f"\n优化后方案预览:")
    print(f"  {result.get('best_solution', '')[:300]}...")

    return result.get('success', False)


async def test_swarm_voting():
    """测试群体投票工具"""
    print("\n" + "=" * 60)
    print("测试：SwarmVotingTool - 群体投票决策")
    print("=" * 60)

    from tools.reasoning_tools import SwarmVotingTool

    # 创建多个 Agent
    agents = [
        create_test_agent(),
        create_test_agent(),
        create_test_agent()
    ]

    tool = SwarmVotingTool(agents, voting_rounds=2)

    problem = "选择最适合创业公司的技术栈"

    print(f"\n问题：{problem}")
    print(f"参与 Agent: {len(agents)}个")
    print(f"投票轮数：2")

    result = await tool.execute(problem, verbose=True)

    print(f"\n结果:")
    print(f"  获胜方案 Agent: {result.get('winning_proposal', {}).get('agent', 'Unknown')}")
    print(f"  获胜方案评分：{result.get('winning_proposal', {}).get('score', 0):.2f}")
    print(f"  总方案数：{len(result.get('all_proposals', []))}")
    print(f"  执行时间：{result.get('execution_time', 0):.2f}秒")
    print(f"\n获胜方案预览:")
    print(f"  {result.get('winning_proposal', {}).get('content', '')[:300]}...")

    return result.get('success', False)


async def test_multi_path_optimizer():
    """测试多路径优化工具"""
    print("\n" + "=" * 60)
    print("测试：MultiPathOptimizerTool - 多路径并行优化")
    print("=" * 60)

    from tools.reasoning_tools import MultiPathOptimizerTool

    agent = create_test_agent()
    tool = MultiPathOptimizerTool(agent, num_paths=3, keep_top_k=2, max_iterations=2)

    problem = "设计一个电商网站的营销活动系统"

    print(f"\n问题：{problem}")
    print(f"配置：num_paths=3, keep_top_k=2, max_iterations=2")

    result = await tool.execute(problem, verbose=True)

    print(f"\n结果:")
    print(f"  最优方案方向：{result.get('best_solution', {}).get('direction', 'Unknown')}")
    print(f"  最优方案评分：{result.get('best_solution', {}).get('score', 0):.2f}")
    print(f"  最终路径数：{len(result.get('final_paths', []))}")
    print(f"  执行时间：{result.get('execution_time', 0):.2f}秒")
    print(f"\n最优方案预览:")
    print(f"  {result.get('best_solution', {}).get('content', '')[:300]}...")

    return result.get('success', False)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Simple Agent - 推理工具测试")
    print("=" * 60)

    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        choice = sys.argv[1].lower()
    else:
        # 非交互模式：运行全部测试
        print("\n运行全部测试...\n")
        run_all_tests()
        return

    # 选择测试
    tests = {
        "1": ("思维树", test_tree_of_thought),
        "2": ("迭代优化", test_iterative_optimizer),
        "3": ("群体投票", test_swarm_voting),
        "4": ("多路径优化", test_multi_path_optimizer),
        "all": ("全部测试", lambda: run_all_tests())
    }

    if choice in tests:
        name, test_func = tests[choice]
        print(f"\n运行：{name}")
        asyncio.run(test_func())
    else:
        print(f"无效选项：{choice}，运行全部测试")
        run_all_tests()

    print("\n测试完成!")


def run_all_tests():
    """运行全部测试"""
    results = {}

    # 测试 1: 思维树
    try:
        results['TreeOfThought'] = asyncio.run(test_tree_of_thought())
    except Exception as e:
        print(f"\nTreeOfThought 测试失败：{e}")
        results['TreeOfThought'] = False

    # 测试 2: 迭代优化
    try:
        results['IterativeOptimizer'] = asyncio.run(test_iterative_optimizer())
    except Exception as e:
        print(f"\nIterativeOptimizer 测试失败：{e}")
        results['IterativeOptimizer'] = False

    # 测试 3: 群体投票
    try:
        results['SwarmVoting'] = asyncio.run(test_swarm_voting())
    except Exception as e:
        print(f"\nSwarmVoting 测试失败：{e}")
        results['SwarmVoting'] = False

    # 测试 4: 多路径优化
    try:
        results['MultiPathOptimizer'] = asyncio.run(test_multi_path_optimizer())
    except Exception as e:
        print(f"\nMultiPathOptimizer 测试失败：{e}")
        results['MultiPathOptimizer'] = False

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name}: {status}")

    total_passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n总计：{total_passed}/{total} 通过")


if __name__ == "__main__":
    main()
