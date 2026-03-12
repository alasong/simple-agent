"""
增强版 Agent - 支持高级认知功能

使用策略模式支持多种执行策略
"""
from typing import Optional
from dataclasses import dataclass
from .agent import Agent
from .memory_enhanced import EnhancedMemory, Experience
from .strategies import (
    ExecutionStrategy,
    DirectStrategy,
    PlanReflectStrategy,
    TreeOfThoughtStrategy,
    ExecutionResult,
    StrategyFactory
)
from .strategy_router import StrategyRouter, StrategyResult


class EnhancedAgent(Agent):
    """增强版 Agent，支持高级认知功能"""

    def __init__(
        self,
        llm,
        tools=None,
        system_prompt=None,
        memory: Optional[EnhancedMemory] = None,
        skill_library=None,
        strategy_name: str = "direct",
        strategy_router: Optional[StrategyRouter] = None,
        **kwargs
    ):
        super().__init__(llm, tools, system_prompt, **kwargs)
        self.memory_enhanced = memory or EnhancedMemory()
        self.skill_library = skill_library

        # 保留原有策略模式（作为备选）
        self._strategy_name = strategy_name
        self._strategy = StrategyFactory.create(strategy_name)

        # 使用统一的 StrategyRouter（优先使用）
        self.strategy_router = strategy_router

        # 设置默认的 agent_pool = [self]
        if self.strategy_router and not self.strategy_router.agent_pool:
            self.strategy_router.agent_pool = [self]

        self.confidence_threshold = 0.7
    
    async def run(self, user_input: str, verbose: bool = False) -> str:
        """主执行流程 - 使用策略模式"""
        # 优先使用 StrategyRouter 进行决策
        if self.strategy_router:
            result = await self.strategy_router.route(user_input)
            strategy_name = result.strategy.value
            if verbose:
                print(f"[Meta] StrategyRouter 选择策略：{strategy_name}")
        else:
            # 保留原有策略选择逻辑（向后兼容）
            relevant = await self.memory_enhanced.retrieve_relevant(user_input)
            strategy_name = await self._select_strategy_name(user_input, relevant)

        # 更新策略
        if strategy_name != self._strategy_name:
            self._strategy_name = strategy_name
            self._strategy = StrategyFactory.create(strategy_name)

        if verbose and not self.strategy_router:
            print(f"[Meta] 选择策略：{self._strategy_name}")

        # 执行策略
        strategy_result = await self._strategy.execute(self, user_input, verbose)

        # 记录经验
        exp = Experience(
            content=user_input,
            context=str(strategy_result.suggested_agents) if hasattr(strategy_result, 'suggested_agents') else "",
            result=strategy_result.output if hasattr(strategy_result, 'output') else str(strategy_result),
            success=strategy_result.success if hasattr(strategy_result, 'success') else True,
            tags=[self._strategy_name]
        )
        self.memory_enhanced.add_to_short_term(exp)

        if len(self.memory_enhanced.experiences) % 10 == 0:
            reflection = self.memory_enhanced.reflect()
            self.memory_enhanced.reflections.append(reflection)

        return strategy_result.output if hasattr(strategy_result, 'output') else str(strategy_result)
    
    async def _select_strategy_name(self, task: str, relevant: list) -> str:
        """根据任务复杂度选择策略名"""
        if relevant:
            successful = [m for m in relevant if m.get("success")]
            if successful:
                best = max(successful, key=lambda m: float(m.get("similarity", 0) or 0))
                similarity = float(best.get("similarity", 0) or 0)
                return "plan_reflect" if similarity > 0.8 else "direct"
        
        complexity = await self._estimate_complexity(task)
        if complexity > 0.7:
            return "tree_of_thought"
        elif complexity > 0.4:
            return "plan_reflect"
        return "direct"
    
    async def _estimate_complexity(self, task: str) -> float:
        # 从配置加载关键词，避免硬编码
        from configs.common_keywords import CommonKeywordsConfig
        keywords = CommonKeywordsConfig.get_complexity_keywords()
        score = sum(0.15 for kw in keywords if kw in task)
        return min(score, 1.0)
    
    def set_strategy(self, strategy_name: str):
        """设置执行策略"""
        self._strategy_name = strategy_name
        self._strategy = StrategyFactory.create(strategy_name)
