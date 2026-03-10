"""
高级推理模式 - 思维树推理和反思循环
"""
from typing import Optional
from dataclasses import dataclass


@dataclass
class Thought:
    """思维节点"""
    content: str
    score: float = 0.0
    parent: Optional['Thought'] = None
    children: list['Thought'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class TreeOfThought:
    """思维树推理"""
    
    def __init__(self, agent, breadth: int = 3, depth: int = 3):
        self.agent = agent
        self.breadth = breadth
        self.depth = depth
        self.thoughts = []
    
    async def solve(self, problem: str) -> str:
        """使用思维树解决问题"""
        self.thoughts = await self._generate_thoughts(problem, self.breadth)
        
        for level in range(self.depth):
            evaluated = await self._evaluate(problem)
            for t, e in zip(self.thoughts, evaluated):
                t.score = e['score']
            best = await self._select_best(self.breadth // 2 + 1)
            self.thoughts = await self._expand(best, problem)
        
        return await self._final_select(problem)
    
    async def _generate_thoughts(self, problem: str, n: int) -> list[Thought]:
        """生成 N 个初始思路"""
        prompt = f"""问题：{problem}

请提出 {n} 个不同的解决思路，每个思路用一句话描述。
以 JSON 数组格式返回：["思路 1", "思路 2", ...]"""
        
        response = await self.agent.llm.chat([{"role": "user", "content": prompt}])
        ideas = self.agent._parse_json(response.content)
        return [Thought(content=idea) for idea in ideas]
    
    async def _evaluate(self, problem: str) -> list[dict]:
        """评估每个思路"""
        evaluations = []
        for t in self.thoughts:
            prompt = f"""问题：{problem}
思路：{t.content}

评估这个思路的质量 (0-1 分)：
- 可行性
- 完整性
- 效率

返回 JSON: {{"score": 0.8, "reason": "..."}}"""
            response = await self.agent.llm.chat([{"role": "user", "content": prompt}])
            evaluations.append(self.agent._parse_json(response.content))
        return evaluations
    
    async def _select_best(self, n: int) -> list[Thought]:
        """选择得分最高的 N 个"""
        indexed = [(i, e['score']) for i, e in enumerate(await self._evaluate(""))]
        indexed.sort(key=lambda x: x[1], reverse=True)
        return [self.thoughts[i] for i, _ in indexed[:n]]
    
    async def _expand(self, thoughts: list[Thought], problem: str) -> list[Thought]:
        """扩展思路"""
        expanded = []
        for t in thoughts:
            prompt = f"""问题：{problem}
当前思路：{t.content}

基于这个思路，提出 2 个更深入的细化方案。
返回 JSON: ["细化方案 1", "细化方案 2"]"""
            response = await self.agent.llm.chat([{"role": "user", "content": prompt}])
            refinements = self.agent._parse_json(response.content)
            for r in refinements:
                child = Thought(content=r, parent=t)
                t.children.append(child)
                expanded.append(child)
        return expanded
    
    async def _final_select(self, problem: str) -> str:
        """选择最终方案"""
        scores = []
        for t in self.thoughts:
            prompt = f"""问题：{problem}
方案：{t.content}

这是最终候选方案，请评估其完整性和可执行性 (0-1 分)。
返回 JSON: {{"score": 0.9, "final_answer": "完整答案..."}}"""
            response = await self.agent.llm.chat([{"role": "user", "content": prompt}])
            result = self.agent._parse_json(response.content)
            scores.append((t, result))
        
        best = max(scores, key=lambda x: x[1]['score'])
        return best[1].get('final_answer', best[0].content)


class ReflectionLoop:
    """反思循环"""
    
    def __init__(self, agent):
        self.agent = agent
    
    async def reflect_and_improve(self, trajectory: list) -> dict:
        """
        从执行轨迹中反思并改进
        
        trajectory: [(thought, action, result), ...]
        返回改进建议
        """
        prompt = f"""分析以下执行轨迹：

{self._format_trajectory(trajectory)}

请回答：
1. 哪些步骤是成功的？为什么？
2. 哪些步骤可以改进？如何改进？
3. 如果重新开始，会采用什么不同策略？
4. 从这个过程中学到了什么通用经验？

返回 JSON 格式：
{{
    "successes": ["成功点 1", ...],
    "improvements": ["改进点 1", ...],
    "alternative_strategy": "替代策略描述",
    "learned_principles": ["原则 1", ...]
}}"""
        response = await self.agent.llm.chat([{"role": "user", "content": prompt}])
        return self.agent._parse_json(response.content)
    
    def _format_trajectory(self, trajectory: list) -> str:
        """格式化执行轨迹"""
        lines = []
        for i, (thought, action, result) in enumerate(trajectory):
            lines.append(f"步骤 {i+1}:")
            lines.append(f"  思考：{thought}")
            lines.append(f"  行动：{action}")
            lines.append(f"  结果：{result}")
        return "\n".join(lines)
