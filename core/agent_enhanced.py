"""
增强版 Agent - 支持高级认知功能
"""
from typing import Optional, Literal
from dataclasses import dataclass
from .agent import Agent
from .memory_enhanced import EnhancedMemory, Experience


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    output: str
    confidence: float
    tool_calls: int
    iterations: int


class EnhancedAgent(Agent):
    """增强版 Agent，支持高级认知功能"""
    
    def __init__(
        self,
        llm,
        tools=None,
        system_prompt=None,
        memory: Optional[EnhancedMemory] = None,
        skill_library=None,
        **kwargs
    ):
        super().__init__(llm, tools, system_prompt, **kwargs)
        self.memory_enhanced = memory or EnhancedMemory()
        self.skill_library = skill_library
        self.strategy: Literal["direct", "plan_reflect", "tree_of_thought"] = "direct"
        self.confidence_threshold = 0.7
    
    async def run(self, user_input: str, verbose: bool = False) -> str:
        """主执行流程"""
        relevant = await self.memory_enhanced.retrieve_relevant(user_input)
        self.strategy = await self._select_strategy(user_input, relevant)
        
        if verbose:
            print(f"[Meta] 选择策略：{self.strategy}")
        
        if self.strategy == "plan_reflect":
            result = await self._plan_reflect_execute(user_input, verbose)
        elif self.strategy == "tree_of_thought":
            result = await self._tree_of_thought(user_input, verbose)
        else:
            result = await self._direct_execute(user_input, verbose)
        
        exp = Experience(
            content=user_input,
            context=str(relevant),
            result=result.output,
            success=result.success,
            tags=[self.strategy]
        )
        self.memory_enhanced.add_to_short_term(exp)
        
        if len(self.memory_enhanced.experiences) % 10 == 0:
            reflection = self.memory_enhanced.reflect()
            self.memory_enhanced.reflections.append(reflection)
        
        return result.output
    
    async def _select_strategy(self, task: str, relevant: list) -> str:
        """根据任务复杂度选择策略"""
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
    
    async def _plan_reflect_execute(self, user_input: str, verbose: bool) -> ExecutionResult:
        """规划 - 反思执行模式"""
        plan_prompt = f"""任务：{user_input}

请制定详细的执行计划，返回 JSON:
{{"steps": [{{"goal": "目标", "approach": "方法", "potential_issues": ["问题"]}}]}}"""
        
        plan_response = await self.llm.chat([{"role": "user", "content": plan_prompt}])
        plan = self._parse_json(plan_response.content)
        
        if verbose:
            print(f"[Plan] 制定计划：{len(plan.get('steps', []))} 个步骤")
        
        results = []
        for i, step in enumerate(plan.get("steps", [])):
            step_input = f"执行步骤 {i+1}: {step.get('goal')}\n方法：{step.get('approach')}"
            step_result = await self._execute_step(step_input)
            results.append(step_result)
            
            if verbose:
                print(f"[Step {i+1}] 结果：{'成功' if step_result.success else '失败'}")
            
            if step_result.confidence < self.confidence_threshold:
                await self._adjust_step(step, step_result)
        
        output = await self._synthesize_results(results)
        avg_conf = sum(r.confidence for r in results) / len(results) if results else 0
        
        return ExecutionResult(
            success=all(r.success for r in results),
            output=output,
            confidence=avg_conf,
            tool_calls=sum(r.tool_calls for r in results),
            iterations=len(results)
        )
    
    async def _tree_of_thought(self, user_input: str, verbose: bool) -> ExecutionResult:
        """思维树推理"""
        from .reasoning_modes import TreeOfThought
        tot = TreeOfThought(self, breadth=3, depth=2)
        output = await tot.solve(user_input)
        
        return ExecutionResult(
            success=True,
            output=output,
            confidence=0.8,
            tool_calls=0,
            iterations=6
        )
    
    async def _direct_execute(self, user_input: str, verbose: bool) -> ExecutionResult:
        """直接执行"""
        # super().run 是同步方法，不需要 await
        output = super().run(user_input, verbose)
        return ExecutionResult(
            success=True,
            output=output,
            confidence=0.8,
            tool_calls=0,
            iterations=1
        )
    
    async def _execute_step(self, step_input: str) -> ExecutionResult:
        """执行单步"""
        output = await self.llm.chat([{"role": "user", "content": step_input}])
        return ExecutionResult(True, output.content or "", 0.75, 0, 1)
    
    async def _adjust_step(self, step, result):
        """调整步骤"""
        pass
    
    async def _synthesize_results(self, results: list) -> str:
        """汇总结果"""
        return "\n\n".join(r.output for r in results)
    
    def _parse_json(self, content: str) -> dict:
        """解析 JSON"""
        import json
        try:
            return json.loads(content)
        except:
            return {}
