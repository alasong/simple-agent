"""
Execution Strategies - 执行策略模式

支持多种 Agent 执行策略：
- Direct: 直接执行
- PlanReflect: 规划 - 反思
- TreeOfThought: 思维树
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    output: str
    confidence: float
    tool_calls: int
    iterations: int


class ExecutionStrategy(ABC):
    """执行策略抽象基类"""
    
    @abstractmethod
    async def execute(self, agent, task: str, verbose: bool = False) -> ExecutionResult:
        """
        执行策略
        
        Args:
            agent: Agent 实例
            task: 任务描述
            verbose: 是否打印详细过程
        
        Returns:
            ExecutionResult
        """
        pass


class DirectStrategy(ExecutionStrategy):
    """直接执行策略"""
    
    async def execute(self, agent, task: str, verbose: bool = False) -> ExecutionResult:
        """直接执行任务"""
        # super().run 是同步方法
        output = agent.run(task, verbose=verbose)
        return ExecutionResult(
            success=True,
            output=output,
            confidence=0.8,
            tool_calls=0,
            iterations=1
        )


class PlanReflectStrategy(ExecutionStrategy):
    """规划 - 反思执行策略"""
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
    
    async def execute(self, agent, task: str, verbose: bool = False) -> ExecutionResult:
        """规划 - 反思执行"""
        # 制定计划
        plan_prompt = f"""任务：{task}

请制定详细的执行计划，返回 JSON:
{{"steps": [{{"goal": "目标", "approach": "方法", "potential_issues": ["问题"]}}]}}"""
        
        plan_response = await agent.llm.chat([{"role": "user", "content": plan_prompt}])
        plan = self._parse_json(plan_response.content)
        
        if verbose:
            print(f"[Plan] 制定计划：{len(plan.get('steps', []))} 个步骤")
        
        results = []
        for i, step in enumerate(plan.get("steps", [])):
            step_input = f"执行步骤 {i+1}: {step.get('goal')}\n方法：{step.get('approach')}"
            step_result = await self._execute_step(agent, step_input)
            results.append(step_result)
            
            if verbose:
                print(f"[Step {i+1}] 结果：{'成功' if step_result.success else '失败'}")
            
            # 低置信度时调整
            if step_result.confidence < self.confidence_threshold:
                await self._adjust_step(agent, step, step_result)
        
        output = self._synthesize_results(results)
        avg_conf = sum(r.confidence for r in results) / len(results) if results else 0
        
        return ExecutionResult(
            success=all(r.success for r in results),
            output=output,
            confidence=avg_conf,
            tool_calls=sum(r.tool_calls for r in results),
            iterations=len(results)
        )
    
    async def _execute_step(self, agent, step_input: str) -> ExecutionResult:
        """执行单步"""
        output = await agent.llm.chat([{"role": "user", "content": step_input}])
        return ExecutionResult(
            success=True,
            output=output.content or "",
            confidence=0.75,
            tool_calls=0,
            iterations=1
        )
    
    async def _adjust_step(self, agent, step, result):
        """调整步骤（可扩展）"""
        pass
    
    def _synthesize_results(self, results: list) -> str:
        """汇总结果"""
        return "\n\n".join(r.output for r in results)
    
    def _parse_json(self, content: str) -> dict:
        """解析 JSON"""
        import json
        try:
            return json.loads(content)
        except:
            return {"steps": []}


class TreeOfThoughtStrategy(ExecutionStrategy):
    """思维树执行策略"""
    
    def __init__(self, breadth: int = 3, depth: int = 2):
        self.breadth = breadth
        self.depth = depth
    
    async def execute(self, agent, task: str, verbose: bool = False) -> ExecutionResult:
        """思维树推理"""
        from .reasoning_modes import TreeOfThought
        tot = TreeOfThought(agent, breadth=self.breadth, depth=self.depth)
        output = await tot.solve(task)
        
        return ExecutionResult(
            success=True,
            output=output,
            confidence=0.8,
            tool_calls=0,
            iterations=self.breadth * self.depth
        )


# 策略工厂
class StrategyFactory:
    """策略工厂"""
    
    _strategies = {
        "direct": DirectStrategy,
        "plan_reflect": PlanReflectStrategy,
        "tree_of_thought": TreeOfThoughtStrategy,
    }
    
    @classmethod
    def create(cls, strategy_name: str, **kwargs) -> ExecutionStrategy:
        """创建策略实例"""
        strategy_class = cls._strategies.get(strategy_name)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        return strategy_class(**kwargs)
    
    @classmethod
    def list_strategies(cls) -> List[str]:
        """列出所有可用策略"""
        return list(cls._strategies.keys())
