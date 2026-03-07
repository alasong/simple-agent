#!/usr/bin/env python3
"""
Swarm 实际使用示例

展示如何在实际项目中使用 Swarm 功能
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import Agent
from core.llm import get_llm
from swarm import (
    SwarmOrchestrator,
    PairProgramming,
    SwarmBrainstorming,
    CodeReviewLoop,
)
from swarm.scheduler import Task


# ==================== 示例 1: 基本的 Swarm 任务执行 ====================

async def example_basic_swarm():
    """基本的 Swarm 任务执行"""
    print("\n" + "="*70)
    print("示例 1: 基本的 Swarm 任务执行")
    print("="*70)
    
    llm = get_llm()
    
    # 创建多个 Agent
    agents = [
        Agent(llm=llm, name="分析师", description="需求分析专家", 
              system_prompt="你是需求分析专家，擅长理解和分析需求"),
        Agent(llm=llm, name="架构师", description="系统架构专家",
              system_prompt="你是系统架构师，擅长设计高可用系统"),
        Agent(llm=llm, name="开发者", description="软件开发专家",
              system_prompt="你是资深开发工程师，擅长编写高质量代码"),
    ]
    
    # 创建 Swarm 控制器
    orchestrator = SwarmOrchestrator(
        agent_pool=agents,
        llm=llm,
        max_iterations=20,
        verbose=True
    )
    
    # 执行任务（会自动分解）
    result = await orchestrator.solve("设计一个简单的待办事项管理系统")
    
    print(f"\n{'='*70}")
    print(f"执行完成")
    print(f"完成任务数：{result.tasks_completed}")
    print(f"失败任务数：{result.tasks_failed}")
    print(f"耗时：{result.execution_time:.2f}秒")
    print(f"{'='*70}\n")
    
    return result


# ==================== 示例 2: 手动定义任务 ====================

async def example_manual_tasks():
    """手动定义任务执行"""
    print("\n" + "="*70)
    print("示例 2: 手动定义任务")
    print("="*70)
    
    llm = get_llm()
    
    agents = [
        Agent(llm=llm, name="Developer", 
              system_prompt="你是开发工程师，负责实现功能"),
        Agent(llm=llm, name="Tester",
              system_prompt="你是测试工程师，负责编写测试"),
    ]
    
    orchestrator = SwarmOrchestrator(
        agent_pool=agents,
        llm=llm,
        verbose=True
    )
    
    # 手动定义任务
    tasks = [
        Task(
            id="1",
            description="实现一个计算器类，支持加减乘除",
            required_skills=["coding"],
            dependencies=[]
        ),
        Task(
            id="2",
            description="为计算器编写单元测试",
            required_skills=["testing"],
            dependencies=["1"]
        ),
    ]
    
    orchestrator._build_task_graph(tasks)
    result = await orchestrator._execute_loop("开发计算器功能")
    
    print(f"\n{'='*70}")
    print(f"执行完成")
    print(f"完成任务数：{result.tasks_completed}")
    print(f"{'='*70}\n")
    
    return result


# ==================== 示例 3: 结对编程 ====================

async def example_pair_programming():
    """结对编程示例"""
    print("\n" + "="*70)
    print("示例 3: 结对编程")
    print("="*70)
    
    llm = get_llm()
    
    driver = Agent(
        llm=llm,
        name="Driver",
        system_prompt="你负责编写代码。直接输出代码，不要过多解释。"
    )
    
    navigator = Agent(
        llm=llm,
        name="Navigator",
        system_prompt="你负责审查代码。检查代码的正确性、性能和可读性。"
    )
    
    pp = PairProgramming(
        driver=driver,
        navigator=navigator,
        max_iterations=5
    )
    
    result = await pp.execute("实现一个冒泡排序算法")
    
    print(f"\n{'='*70}")
    print(f"结对编程完成")
    print(f"是否通过：{result.success}")
    print(f"迭代次数：{result.iterations}")
    print(f"代码:\n{result.output}")
    print(f"{'='*70}\n")
    
    return result


# ==================== 示例 4: 头脑风暴 ====================

async def example_brainstorming():
    """头脑风暴示例"""
    print("\n" + "="*70)
    print("示例 4: 群体头脑风暴")
    print("="*70)
    
    llm = get_llm()
    
    agents = [
        Agent(llm=llm, name="技术专家",
              system_prompt="你是技术专家，关注技术可行性"),
        Agent(llm=llm, name="产品专家",
              system_prompt="你是产品专家，关注用户体验"),
        Agent(llm=llm, name="商业专家",
              system_prompt="你是商业专家，关注商业价值"),
    ]
    
    sb = SwarmBrainstorming(agents)
    
    result = await sb.execute("如何设计一个受欢迎的社交应用？")
    
    print(f"\n{'='*70}")
    print(f"头脑风暴完成")
    print(f"参与者：{', '.join(result.participants)}")
    print(f"方案:\n{result.output}")
    print(f"{'='*70}\n")
    
    return result


# ==================== 示例 5: 代码审查循环 ====================

async def example_code_review():
    """代码审查循环示例"""
    print("\n" + "="*70)
    print("示例 5: 代码审查循环")
    print("="*70)
    
    llm = get_llm()
    
    developer = Agent(
        llm=llm,
        name="Developer",
        system_prompt="你负责编写和修改代码"
    )
    
    reviewers = [
        Agent(
            llm=llm,
            name="代码审查员",
            system_prompt="你负责审查代码质量和最佳实践"
        ),
        Agent(
            llm=llm,
            name="安全审查员",
            system_prompt="你负责审查代码安全性"
        ),
    ]
    
    crl = CodeReviewLoop(
        developer=developer,
        reviewers=reviewers,
        max_rounds=3
    )
    
    result = await crl.execute("实现用户登录功能")
    
    print(f"\n{'='*70}")
    print(f"代码审查完成")
    print(f"是否通过：{result.success}")
    print(f"审查轮次：{result.iterations}")
    print(f"参与者：{', '.join(result.participants)}")
    print(f"{'='*70}\n")
    
    return result


# ==================== 主函数 ====================

async def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print(" " * 20 + "Swarm 实际使用示例")
    print("="*70)
    
    examples = [
        ("基本 Swarm", example_basic_swarm),
        ("手动任务", example_manual_tasks),
        ("结对编程", example_pair_programming),
        ("头脑风暴", example_brainstorming),
        ("代码审查", example_code_review),
    ]
    
    results = []
    for name, example in examples:
        try:
            print(f"\n>>> 运行：{name}\n")
            result = await example()
            results.append((name, result, None))
        except Exception as e:
            print(f"\n>>> {name} 失败：{e}\n")
            results.append((name, None, e))
            import traceback
            traceback.print_exc()
    
    # 汇总
    print("\n" + "="*70)
    print("示例运行汇总")
    print("="*70)
    for name, result, error in results:
        status = "✓ 成功" if result else f"✗ 失败：{error}"
        print(f"{status}: {name}")
    
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
