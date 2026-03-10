"""
推理工具包装器 - 将推理工具封装为 LLM 可调用的格式

这些工具可以被添加到 Agent 的 tools 列表中，LLM 可以通过标准格式调用
"""

from typing import Any, Dict, Optional, List
import asyncio


class ReasoningToolsWrapper:
    """
    推理工具包装器

    将 TreeOfThought、IterativeOptimizer 等工具封装为 LLM 可调用的格式
    """

    def __init__(self, agent: Any, evaluator_agent: Optional[Any] = None):
        self.agent = agent
        self.evaluator_agent = evaluator_agent
        self._tools = {}
        self._init_tools()

    def _init_tools(self):
        """初始化工具"""
        # 延迟导入，避免循环依赖
        from tools.reasoning_tools import (
            TreeOfThoughtTool,
            IterativeOptimizerTool,
            SwarmVotingTool,
            MultiPathOptimizerTool,
            create_tree_of_thought,
            create_iterative_optimizer,
            create_swarm_voting,
            create_multi_path_optimizer
        )

        self._tools = {
            "TreeOfThoughtTool": TreeOfThoughtTool(self.agent),
            "IterativeOptimizerTool": IterativeOptimizerTool(self.agent, self.evaluator_agent),
        }

    def get_tool(self, name: str):
        """获取指定工具"""
        return self._tools.get(name)

    def get_tool_names(self) -> List[str]:
        """获取可用工具列表"""
        return list(self._tools.keys())


# ==================== 工具调用函数 ====================

async def call_tree_of_thought(
    agent: Any,
    problem: str,
    breadth: int = 3,
    depth: int = 3,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    调用思维树工具

    Args:
        agent: 执行 Agent
        problem: 待解决的问题
        breadth: 每层生成的思路数
        depth: 最大深度
        verbose: 是否输出详细日志

    Returns:
        包含最佳方案和思维树的字典
    """
    from tools.reasoning_tools import TreeOfThoughtTool

    tool = TreeOfThoughtTool(agent, breadth=breadth, depth=depth)
    return await tool.execute(problem, verbose=verbose)


async def call_iterative_optimizer(
    agent: Any,
    problem: str,
    initial_solution: Optional[str] = None,
    max_iterations: int = 3,
    quality_threshold: float = 0.75,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    调用迭代优化工具

    Args:
        agent: 执行 Agent
        problem: 待解决的问题
        initial_solution: 初始方案（可选）
        max_iterations: 最大迭代次数
        quality_threshold: 质量阈值
        verbose: 是否输出详细日志

    Returns:
        包含优化结果的字典
    """
    from tools.reasoning_tools import IterativeOptimizerTool

    tool = IterativeOptimizerTool(agent, max_iterations=max_iterations, quality_threshold=quality_threshold)
    return await tool.execute(problem, initial_solution=initial_solution, verbose=verbose)


async def call_swarm_voting(
    agents: List[Any],
    problem: str,
    voting_rounds: int = 2,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    调用群体投票工具

    Args:
        agents: 参与投票的 Agent 列表
        problem: 待解决的问题
        voting_rounds: 投票轮数
        verbose: 是否输出详细日志

    Returns:
        包含获胜方案的字典
    """
    from tools.reasoning_tools import SwarmVotingTool

    tool = SwarmVotingTool(agents, voting_rounds=voting_rounds)
    return await tool.execute(problem, voting_rounds=voting_rounds, verbose=verbose)


async def call_multi_path_optimizer(
    agent: Any,
    problem: str,
    num_paths: int = 3,
    keep_top_k: int = 2,
    max_iterations: int = 3,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    调用多路径优化工具

    Args:
        agent: 执行 Agent
        problem: 待解决的问题
        num_paths: 同时探索的路径数
        keep_top_k: 每轮保留的路径数
        max_iterations: 最大迭代次数
        verbose: 是否输出详细日志

    Returns:
        包含最优方案的字典
    """
    from tools.reasoning_tools import MultiPathOptimizerTool

    tool = MultiPathOptimizerTool(
        agent,
        num_paths=num_paths,
        keep_top_k=keep_top_k,
        max_iterations=max_iterations
    )
    return await tool.execute(problem, num_paths=num_paths, keep_top_k=keep_top_k, max_iterations=max_iterations, verbose=verbose)


# ==================== 便捷函数（供 Agent 直接调用） ====================

def run_tree_of_thought_sync(
    agent: Any,
    problem: str,
    breadth: int = 3,
    depth: int = 3
) -> str:
    """
    同步运行思维树（用于非异步环境）

    Returns:
        最佳方案文本
    """
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        call_tree_of_thought(agent, problem, breadth, depth, verbose=False)
    )
    return result.get("best_solution", "")


def run_iterative_optimizer_sync(
    agent: Any,
    problem: str,
    initial_solution: Optional[str] = None,
    max_iterations: int = 3
) -> str:
    """
    同步运行迭代优化（用于非异步环境）

    Returns:
        优化后的方案文本
    """
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        call_iterative_optimizer(agent, problem, initial_solution, max_iterations, verbose=False)
    )
    return result.get("best_solution", "")


def run_swarm_voting_sync(
    agents: List[Any],
    problem: str,
    voting_rounds: int = 2
) -> str:
    """
    同步运行群体投票（用于非异步环境）

    Returns:
        获胜方案文本
    """
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        call_swarm_voting(agents, problem, voting_rounds, verbose=False)
    )
    winning = result.get("winning_proposal", {})
    return winning.get("content", "")


def run_multi_path_optimizer_sync(
    agent: Any,
    problem: str,
    num_paths: int = 3,
    max_iterations: int = 3
) -> str:
    """
    同步运行多路径优化（用于非异步环境）

    Returns:
        最优方案文本
    """
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        call_multi_path_optimizer(agent, problem, num_paths, max_iterations=max_iterations, verbose=False)
    )
    best = result.get("best_solution", {})
    return best.get("content", "")
