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
        **kwargs
    ):
        super().__init__(llm, tools, system_prompt, **kwargs)
        self.memory_enhanced = memory or EnhancedMemory()
        self.skill_library = skill_library
        
        # 使用策略模式
        self._strategy_name = strategy_name
        self._strategy = StrategyFactory.create(strategy_name)
        self.confidence_threshold = 0.7
    
    async def run(self, user_input: str, verbose: bool = False) -> str:
        """主执行流程 - 使用策略模式"""
        # 动态选择策略
        relevant = await self.memory_enhanced.retrieve_relevant(user_input)
        strategy_name = await self._select_strategy_name(user_input, relevant)
        
        # 更新策略
        if strategy_name != self._strategy_name:
            self._strategy_name = strategy_name
            self._strategy = StrategyFactory.create(strategy_name)
        
        if verbose:
            print(f"[Meta] 选择策略：{self._strategy_name}")
        
        # 执行策略
        result = await self._strategy.execute(self, user_input, verbose)
        
        # 记录经验
        exp = Experience(
            content=user_input,
            context=str(relevant),
            result=result.output,
            success=result.success,
            tags=[self._strategy_name]
        )
        self.memory_enhanced.add_to_short_term(exp)
        
        if len(self.memory_enhanced.experiences) % 10 == 0:
            reflection = self.memory_enhanced.reflect()
            self.memory_enhanced.reflections.append(reflection)
        
        return result.output
    
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
        keywords = ["设计", "架构", "系统", "复杂", "多个", "完整", "从 0"]
        score = sum(0.15 for kw in keywords if kw in task)
        return min(score, 1.0)
    
    def set_strategy(self, strategy_name: str):
        """设置执行策略"""
        self._strategy_name = strategy_name
        self._strategy = StrategyFactory.create(strategy_name)
