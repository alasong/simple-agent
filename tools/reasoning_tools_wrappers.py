"""
推理工具包装器 - 将推理功能封装为 BaseTool 继承的工具

这些工具可以被 Agent 直接调用，通过 ToolRegistry 自动发现
"""

import asyncio
from typing import Optional, Any, List
from core.tool import BaseTool, ToolResult


# ==================== TreeOfThoughtTool ====================

class TreeOfThoughtTool(BaseTool):
    """
    思维树多路径探索工具

    通过生成多个不同思路、评估评分、扩展最优思路的方式，
    探索多个解决方案路径，避免陷入局部最优。

    适用于：
    - 架构设计：探索多个技术方案
    - 决策问题：评估多个选项
    - 创新任务：需要多角度思考
    """

    @property
    def name(self) -> str:
        return "TreeOfThoughtTool"

    @property
    def description(self) -> str:
        return "思维树多路径探索：生成多个不同解决思路，评估后扩展最优的，形成树状推理结构，最终选择最佳方案。适用于需要探索多个解决方案的复杂问题。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "problem": {
                    "type": "string",
                    "description": "待解决的问题"
                },
                "breadth": {
                    "type": "integer",
                    "description": "每层生成的思路数量（默认 3）",
                    "default": 3
                },
                "depth": {
                    "type": "integer",
                    "description": "最大深度/迭代层数（默认 3）",
                    "default": 3
                }
            },
            "required": ["problem"]
        }

    def execute(
        self,
        problem: str,
        breadth: int = 3,
        depth: int = 3,
        **kwargs
    ) -> ToolResult:
        """执行思维树推理"""
        try:
            from tools.reasoning_tools import TreeOfThoughtTool as ToT

            # 获取当前 Agent（从调用上下文）
            agent = kwargs.get('agent')
            if not agent:
                return ToolResult(
                    success=False,
                    output="错误：TreeOfThoughtTool 需要 Agent 上下文才能执行"
                )

            # 创建工具并执行
            tool = ToT(agent, breadth=breadth, depth=depth)
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(tool.execute(problem, verbose=False))

            output = (
                f"思维树推理完成\n\n"
                f"最佳方案（评分：{result.get('best_score', 0):.2f}）:\n"
                f"{result.get('best_solution', '')}\n\n"
                f"探索了 {result.get('total_thoughts', 0)} 个思路，"
                f"树深度：{result.get('tree_depth', 0)}, "
                f"耗时：{result.get('execution_time', 0):.2f}秒"
            )

            return ToolResult(success=True, output=output)

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"思维树推理失败：{str(e)}",
                error=str(e)
            )


# ==================== IterativeOptimizerTool ====================

class IterativeOptimizerTool(BaseTool):
    """
    多轮迭代优化工具

    通过多轮迭代和独立质量评估，持续优化方案质量，
    达到阈值后自动停止。

    适用于：
    - 代码优化：持续改进代码质量
    - 方案完善：多轮审查和改进
    - 文档润色：迭代优化表达
    """

    @property
    def name(self) -> str:
        return "IterativeOptimizerTool"

    @property
    def description(self) -> str:
        return "多轮迭代优化：生成初始方案后，通过质量评估→改进建议→优化方案的循环，持续提升方案质量，达到阈值自动停止。适用于需要持续改进的场景。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "problem": {
                    "type": "string",
                    "description": "待解决的问题"
                },
                "initial_solution": {
                    "type": "string",
                    "description": "初始方案（可选，不提供则自动生成）"
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "最大迭代次数（默认 3）",
                    "default": 3
                },
                "quality_threshold": {
                    "type": "number",
                    "description": "质量阈值 0-1（默认 0.75，达到后停止）",
                    "default": 0.75
                }
            },
            "required": ["problem"]
        }

    def execute(
        self,
        problem: str,
        initial_solution: Optional[str] = None,
        max_iterations: int = 3,
        quality_threshold: float = 0.75,
        **kwargs
    ) -> ToolResult:
        """执行迭代优化"""
        try:
            from tools.reasoning_tools import IterativeOptimizerTool as IOT

            agent = kwargs.get('agent')
            if not agent:
                return ToolResult(
                    success=False,
                    output="错误：IterativeOptimizerTool 需要 Agent 上下文"
                )

            tool = IOT(agent, max_iterations=max_iterations, quality_threshold=quality_threshold)
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                tool.execute(problem, initial_solution=initial_solution, verbose=False)
            )

            output = (
                f"迭代优化完成（成功：{result.get('success', False)}）\n\n"
                f"优化后方案（评分：{result.get('final_score', 0):.2f}）:\n"
                f"{result.get('best_solution', '')}\n\n"
                f"迭代次数：{result.get('total_iterations', 0)}, "
                f"耗时：{result.get('execution_time', 0):.2f}秒"
            )

            return ToolResult(success=True, output=output)

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"迭代优化失败：{str(e)}",
                error=str(e)
            )


# ==================== SwarmVotingTool ====================

class SwarmVotingTool(BaseTool):
    """
    群体投票决策工具

    多个 Agent 独立生成方案，互相评分，通过多轮投票淘汰，
    最终选出群体共识最优方案。

    适用于：
    - 技术选型：多个方案投票
    - 产品方向：集体决策
    - 重大决定：避免个人偏见
    """

    @property
    def name(self) -> str:
        return "SwarmVotingTool"

    @property
    def description(self) -> str:
        return "群体投票决策：多个 Agent 独立提出方案，互相评分，多轮投票淘汰，选出群体共识最优。适用于需要集思广益、避免个人偏见的重大决策。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "problem": {
                    "type": "string",
                    "description": "待解决的问题"
                },
                "voting_rounds": {
                    "type": "integer",
                    "description": "投票轮数（默认 2）",
                    "default": 2
                },
                "agent_names": {
                    "type": "array",
                    "description": "参与投票的 Agent 名称列表（可选，默认使用所有可用 Agent）",
                    "items": {"type": "string"}
                }
            },
            "required": ["problem"]
        }

    def execute(
        self,
        problem: str,
        voting_rounds: int = 2,
        agent_names: Optional[List[str]] = None,
        **kwargs
    ) -> ToolResult:
        """执行群体投票"""
        try:
            from tools.reasoning_tools import SwarmVotingTool as SVT
            from core.agent import Agent

            # 获取 Agent 池
            agent_pool = kwargs.get('agent_pool', [])
            if not agent_pool:
                return ToolResult(
                    success=False,
                    output="错误：SwarmVotingTool 需要 Agent 池"
                )

            # 筛选指定 Agent（如果提供）
            if agent_names:
                agents = [a for a in agent_pool if a.name in agent_names]
            else:
                agents = agent_pool[:5]  # 最多 5 个

            if len(agents) < 2:
                return ToolResult(
                    success=False,
                    output="错误：至少需要 2 个 Agent 参与投票"
                )

            tool = SVT(agents, voting_rounds=voting_rounds)
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(tool.execute(problem, verbose=False))

            winning = result.get('winning_proposal', {})
            output = (
                f"群体投票完成\n\n"
                f"获胜方案（{winning.get('agent', 'Unknown')}, 评分：{winning.get('score', 0):.2f}）:\n"
                f"{winning.get('content', '')}\n\n"
                f"共 {len(result.get('all_proposals', []))} 个方案参与投票，"
                f"经过 {voting_rounds} 轮投票选出"
            )

            return ToolResult(success=True, output=output)

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"群体投票失败：{str(e)}",
                error=str(e)
            )


# ==================== MultiPathOptimizerTool ====================

class MultiPathOptimizerTool(BaseTool):
    """
    多路径并行优化工具

    同时生成 N 个不同方向的初始方案，每轮迭代后保留 Top-K 个继续优化，
    最终选择最优方案。融合了群体智慧和迭代优化的优势。

    适用于：
    - 复杂系统设计：多方向探索
    - 营销策略：多方案并行优化
    - 职业规划：多条路径评估
    """

    @property
    def name(self) -> str:
        return "MultiPathOptimizerTool"

    @property
    def description(self) -> str:
        return "多路径并行优化：同时探索多个不同方向（如保守型、激进型、平衡型），每轮迭代保留 Top-K 个，最终选择最优。融合群体智慧和迭代优化，找到全局最优解。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "problem": {
                    "type": "string",
                    "description": "待解决的问题"
                },
                "num_paths": {
                    "type": "integer",
                    "description": "同时探索的路径数（默认 3）",
                    "default": 3
                },
                "keep_top_k": {
                    "type": "integer",
                    "description": "每轮保留的路径数（默认 2）",
                    "default": 2
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "最大迭代次数（默认 3）",
                    "default": 3
                }
            },
            "required": ["problem"]
        }

    def execute(
        self,
        problem: str,
        num_paths: int = 3,
        keep_top_k: int = 2,
        max_iterations: int = 3,
        **kwargs
    ) -> ToolResult:
        """执行多路径优化"""
        try:
            from tools.reasoning_tools import MultiPathOptimizerTool as MPO

            agent = kwargs.get('agent')
            if not agent:
                return ToolResult(
                    success=False,
                    output="错误：MultiPathOptimizerTool 需要 Agent 上下文"
                )

            tool = MPO(
                agent,
                num_paths=num_paths,
                keep_top_k=keep_top_k,
                max_iterations=max_iterations
            )
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(tool.execute(problem, verbose=False))

            best = result.get('best_solution', {})
            output = (
                f"多路径优化完成\n\n"
                f"最优方案（方向：{best.get('direction', 'Unknown')}, "
                f"评分：{best.get('score', 0):.2f}）:\n"
                f"{best.get('content', '')}\n\n"
                f"最终有 {len(result.get('final_paths', []))} 个路径，"
                f"耗时：{result.get('execution_time', 0):.2f}秒"
            )

            return ToolResult(success=True, output=output)

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"多路径优化失败：{str(e)}",
                error=str(e)
            )


__all__ = [
    "TreeOfThoughtTool",
    "IterativeOptimizerTool",
    "SwarmVotingTool",
    "MultiPathOptimizerTool"
]
