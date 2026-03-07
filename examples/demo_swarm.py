"""
Swarm 演示脚本

展示群体智能系统的各种功能
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swarm import (
    SwarmOrchestrator,
    Blackboard,
    MessageBus,
    PairProgramming,
    SwarmBrainstorming,
    MarketBasedAllocation,
    CodeReviewLoop,
)
from swarm.scheduler import Task, TaskStatus


class DemoAgent:
    """演示用 Agent"""
    
    def __init__(self, name: str, role: str = ""):
        self.name = name
        self.role = role
        self.instance_id = name
        self.description = f"{role} - {name}"
    
    def run(self, user_input: str, verbose: bool = False) -> str:
        """模拟执行"""
        if verbose:
            print(f"  [{self.name}] 处理：{user_input[:50]}...")
        
        # 简单模拟响应
        if "分解" in user_input:
            return "任务已分解为 3 个子任务"
        elif "审查" in user_input or "review" in user_input.lower():
            return "LGTM - 代码质量良好"
        elif "实现" in user_input or "code" in user_input.lower():
            return f"def solution():\n    # {self.name} 实现的代码\n    return 'result'"
        elif "方案" in user_input or "idea" in user_input.lower():
            return f"{self.name} 的方案：采用模块化设计"
        else:
            return f"{self.name} 完成：{user_input[:30]}"


async def demo_basic_swarm():
    """演示基本的 Swarm 执行"""
    print("\n" + "=" * 60)
    print("演示 1: 基本的 Swarm 任务执行")
    print("=" * 60)
    
    # 创建 Agent 池
    agents = [
        DemoAgent("Analyzer", "需求分析师"),
        DemoAgent("Developer", "开发工程师"),
        DemoAgent("Tester", "测试工程师"),
    ]
    
    # 创建 Orchestrator
    orchestrator = SwarmOrchestrator(
        agent_pool=agents,
        max_iterations=10,
        verbose=True
    )
    
    # 手动创建任务（不依赖 LLM 分解）
    tasks = [
        Task(id="1", description="分析需求", required_skills=["analysis"]),
        Task(id="2", description="实现功能", required_skills=["coding"], dependencies=["1"]),
        Task(id="3", description="测试功能", required_skills=["testing"], dependencies=["2"]),
    ]
    orchestrator._build_task_graph(tasks)
    
    # 执行
    result = await orchestrator._execute_loop("开发一个功能")
    
    print(f"\n结果：{result.output[:300]}...")
    print(f"完成：{result.tasks_completed} 个任务")
    print(f"失败：{result.tasks_failed} 个任务")


async def demo_pair_programming():
    """演示结对编程"""
    print("\n" + "=" * 60)
    print("演示 2: 结对编程")
    print("=" * 60)
    
    driver = DemoAgent("Driver", "代码编写者")
    navigator = DemoAgent("Navigator", "代码审查者")
    
    pp = PairProgramming(driver, navigator, max_iterations=3)
    result = await pp.execute("实现一个排序函数", verbose=True)
    
    print(f"\n结对编程结果：")
    print(f"成功：{result.success}")
    print(f"迭代次数：{result.iterations}")
    print(f"输出：{result.output[:200]}...")


async def demo_brainstorming():
    """演示头脑风暴"""
    print("\n" + "=" * 60)
    print("演示 3: 群体头脑风暴")
    print("=" * 60)
    
    agents = [
        DemoAgent("Engineer1", "架构师"),
        DemoAgent("Engineer2", "技术专家"),
        DemoAgent("Engineer3", "产品专家"),
    ]
    
    sb = SwarmBrainstorming(agents)
    result = await sb.execute("如何设计一个高可用的系统？", verbose=True)
    
    print(f"\n头脑风暴结果：")
    print(f"参与者：{', '.join(result.participants)}")
    print(f"输出：{result.output[:300]}...")


async def demo_market_allocation():
    """演示市场分配"""
    print("\n" + "=" * 60)
    print("演示 4: 基于市场的任务分配")
    print("=" * 60)
    
    agents = [
        DemoAgent("Coder", "资深开发"),
        DemoAgent("Juniour", "初级开发"),
    ]
    
    mba = MarketBasedAllocation(agents)
    winner, bid = await mba.allocate("实现核心算法", verbose=True)
    
    print(f"\n任务分配结果：")
    print(f"获胜者：{winner.name}")
    print(f"竞标价格：{bid:.2f}")


async def demo_code_review():
    """演示代码审查循环"""
    print("\n" + "=" * 60)
    print("演示 5: 代码审查循环")
    print("=" * 60)
    
    developer = DemoAgent("Dev", "开发者")
    reviewers = [
        DemoAgent("Reviewer1", "高级审查员"),
        DemoAgent("Reviewer2", "安全审查员"),
    ]
    
    crl = CodeReviewLoop(developer, reviewers, max_rounds=2)
    result = await crl.execute("实现用户认证功能", verbose=True)
    
    print(f"\n审查循环结果：")
    print(f"成功：{result.success}")
    print(f"轮次：{result.iterations}")
    print(f"参与者：{', '.join(result.participants)}")


async def demo_blackboard():
    """演示共享黑板"""
    print("\n" + "=" * 60)
    print("演示 6: 共享黑板通信")
    print("=" * 60)
    
    bb = Blackboard()
    
    # Agent1 写入
    bb.write("task1_result", "分析完成", "Analyzer")
    bb.write("task2_result", "代码已实现", "Developer")
    
    print(f"黑板数据：{bb.get_all()}")
    print(f"任务上下文：{bb.get_context(type('Task', (), {'dependencies': ['task1_result']})())}")
    
    # 查看历史
    history = bb.get_history("task1_result")
    print(f"变更历史：{history}")


async def main():
    """运行所有演示"""
    print("\n" + "=" * 70)
    print(" " * 20 + "Swarm 群体智能演示")
    print("=" * 70)
    
    demos = [
        demo_blackboard,
        demo_basic_swarm,
        demo_pair_programming,
        demo_brainstorming,
        demo_market_allocation,
        demo_code_review,
    ]
    
    for demo in demos:
        try:
            await demo()
        except Exception as e:
            print(f"\n演示失败：{e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("所有演示完成！")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
