"""
策略路由器示例

演示如何使用新的统一策略决策系统
"""

import asyncio
from simple_agent.core.strategy_router import (
    create_router,
    Strategy,
    ProfessionalAnalyzer,
    ComplexityEstimator
)


class MockAgent:
    """模拟 Agent 用于示例"""
    def __init__(self, name: str, skills: list = None):
        self.name = name
        self.instance_id = name
        self.skills = skills or ["general"]

    def run(self, task_input: str, verbose: bool = True) -> str:
        return f"{self.name} 处理: {task_input}"


async def demo_basic_usage():
    """基础用法示例"""
    print("=" * 60)
    print("策略路由器 - 基础示例")
    print("=" * 60)

    # 创建 Agent 池
    agents = [
        MockAgent("Developer", skills=["coding", "python"]),
        MockAgent("Reviewer", skills=["reviewing", "code_review"]),
        MockAgent("Tester", skills=["testing", "qa"]),
    ]

    # 创建策略路由器
    router = create_router(agent_pool=agents)

    # 测试不同任务
    tasks = [
        "写一个 Python 函数",
        "开发一个 Web 应用",
        "设计并实现一个完整的从0开始的系统架构方案",
    ]

    for task in tasks:
        print(f"\n任务: {task}")
        result = await router.route(task)

        print(f"  策略: {result.strategy.value}")
        print(f"  复杂度: {result.complexity_estimate:.2f}")
        print(f"  专业需求: {', '.join(result.professional_needs) or '无'}")
        print(f"  建议 Agent: {', '.join(result.suggested_agents) or '无'}")
        print(f"  原因: {result.reason}")


async def demo_threshold_config():
    """自定义阈值示例"""
    print("\n" + "=" * 60)
    print("自定义阈值示例")
    print("=" * 60)

    agents = [MockAgent("Developer", skills=["coding"])]

    # 使用更严格的阈值（更低的复杂度即视为高复杂度）
    strict_router = create_router(
        agent_pool=agents,
        complexity_thresholds={
            "low_max": 0.3,
            "medium_max": 0.6,
            "swarm_min": 0.6
        }
    )

    # 使用更宽松的阈值
    loose_router = create_router(
        agent_pool=agents,
        complexity_thresholds={
            "low_max": 0.5,
            "medium_max": 0.8,
            "swarm_min": 0.8
        }
    )

    task = "开发一个 Web 应用"

    print(f"\n任务: {task}")
    print("\n严格阈值:")
    result_strict = await strict_router.route(task)
    print(f"  策略: {result_strict.strategy.value} (复杂度: {result_strict.complexity_estimate:.2f})")

    print("\n宽松阈值:")
    result_loose = await loose_router.route(task)
    print(f"  策略: {result_loose.strategy.value} (复杂度: {result_loose.complexity_estimate:.2f})")


async def demo_integration_with_cli():
    """集成到 CLI Agent 的示例"""
    print("\n" + "=" * 60)
    print("集成示例：CLI Agent 中使用策略路由器")
    print("=" * 60)

    class SimpleCLI:
        """简化版 CLI Agent"""
        def __init__(self):
            self.agents = [
                MockAgent("Developer", skills=["coding"]),
                MockAgent("Designer", skills=["design"]),
            ]
            self.router = create_router(agent_pool=self.agents)

        async def handle_task(self, user_input: str):
            """处理用户任务"""
            # Step 1: 路由到最优策略
            result = await self.router.route(user_input)

            # Step 2: 根据策略执行
            print(f"\n[CLI Agent] 选择策略: {result.strategy.value}")
            print(f"[CLI Agent] 原因: {result.reason}")

            # 模拟执行
            if result.strategy == Strategy.DIRECT:
                print(f"[执行] 直接调用 InvokeAgentTool")
                agent = self.agents[0]
                return await agent.run(user_input)
            elif result.strategy == Strategy.SWARM:
                print(f"[执行] 使用 SwarmOrchestrator 协作")
                return f"Swarm 协作完成: {user_input}"
            elif result.strategy == Strategy.DECOMPOSE:
                print(f"[执行] 使用 TaskDecomposer 分解")
                return f"分解后执行: {user_input}"
            else:
                print(f"[执行] 使用高级推理工具")
                return f"高级推理完成: {user_input}"

    cli = SimpleCLI()

    tasks = [
        "写一个 Python 函数",
        "设计一个完整的 Web 应用",
    ]

    for task in tasks:
        print(f"\n{'='*40}")
        print(f"处理任务: {task}")
        print('='*40)
        result = await cli.handle_task(task)
        print(f"\n[结果] {result}")


async def demo_analyzers():
    """分析器使用示例"""
    print("\n" + "=" * 60)
    print("分析器使用示例")
    print("=" * 60)

    task = "设计并开发一个完整的系统架构方案"

    # 复杂度估计
    complexity = ComplexityEstimator.estimate(task)
    print(f"\n任务: {task}")
    print(f"复杂度: {complexity:.2f}")

    # 专业需求分析
    skills = ProfessionalAnalyzer.extract_skills(task)
    print(f"专业需求: {', '.join(skills) or '无'}")


async def main():
    """运行所有示例"""
    await demo_basic_usage()
    await demo_threshold_config()
    await demo_integration_with_cli()
    await demo_analyzers()

    print("\n" + "=" * 60)
    print("所有示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
