"""
群体协作模式（Collaboration Patterns）

常见的多 Agent 协作模式：
- 结对编程
- 群体头脑风暴
- 基于市场的任务分配
- 代码审查循环
"""

import asyncio
from typing import Optional, Any
from dataclasses import dataclass, field
import time


@dataclass
class CollaborationResult:
    """协作结果"""
    success: bool
    output: str
    participants: list[str] = field(default_factory=list)
    iterations: int = 0
    execution_time: float = 0.0
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output[:500],
            "participants": self.participants,
            "iterations": self.iterations,
            "execution_time": round(self.execution_time, 2)
        }


class PairProgramming:
    """结对编程模式
    
    Driver（驾驶员）：负责编写代码
    Navigator（导航员）：负责审查和指导
    
    模式特点：
    - 实时反馈
    - 持续改进
    - 质量保障
    """
    
    def __init__(self, driver: Any, navigator: Any, max_iterations: int = 5):
        self.driver = driver
        self.navigator = navigator
        self.max_iterations = max_iterations
    
    async def execute(self, task: str, verbose: bool = True) -> CollaborationResult:
        """执行结对编程"""
        start_time = time.time()
        code = None
        feedback = ""
        iterations = 0
        
        if verbose:
            print(f"\n[结对编程] 开始任务：{task[:100]}...")
            print(f"[结对编程] Driver: {self.driver.name}, Navigator: {self.navigator.name}")
        
        for i in range(self.max_iterations):
            iterations += 1
            
            if verbose:
                print(f"\n[迭代 {i+1}/{self.max_iterations}]")
            
            # Driver 编写/修改代码
            if not code:
                prompt = f"实现以下功能：\n{task}"
            else:
                prompt = f"根据以下反馈修改代码：\n\n原代码：\n{code}\n\n反馈：\n{feedback}\n\n请修改代码。"
            
            if verbose:
                print(f"[Driver] 编写代码...")
            
            code_result = await self._run_agent(self.driver, prompt)
            code = code_result
            
            if verbose:
                print(f"[Driver] 完成，代码长度：{len(code)} 字符")
            
            # Navigator 审查
            if verbose:
                print(f"[Navigator] 审查代码...")
            
            review_prompt = f"""审查以下代码：

任务：{task}

代码：
{code}

审查要点：
1. 是否正确实现了功能？
2. 代码质量和最佳实践
3. 潜在的问题和改进建议
4. 是否需要进一步修改？

如果代码已经完善，请回复 "LGTM" 或 "无需修改"。
否则，提供具体的修改建议。
"""
            feedback = await self._run_agent(self.navigator, review_prompt)
            
            if verbose:
                print(f"[Navigator] 反馈：{feedback[:100]}...")
            
            # 检查是否通过
            if self._is_approved(feedback):
                if verbose:
                    print(f"\n[结对编程] 审查通过！")
                break
        
        execution_time = time.time() - start_time
        
        return CollaborationResult(
            success=self._is_approved(feedback),
            output=code or "",
            participants=[self.driver.name, self.navigator.name],
            iterations=iterations,
            execution_time=execution_time,
            metadata={"final_feedback": feedback}
        )
    
    async def _run_agent(self, agent: Any, prompt: str) -> str:
        """运行 Agent"""
        if asyncio.iscoroutinefunction(agent.run):
            result = await agent.run(prompt, verbose=False)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: agent.run(prompt, verbose=False))
        return result
    
    def _is_approved(self, feedback: str) -> bool:
        """检查是否通过审查"""
        # 从配置加载关键词，避免硬编码
        from configs.common_keywords import CommonKeywordsConfig
        approval_keywords = CommonKeywordsConfig.get_approval_keywords()
        feedback_lower = feedback.lower()
        return any(kw in feedback_lower for kw in approval_keywords)


class SwarmBrainstorming:
    """群体头脑风暴模式
    
    多个 Agent 独立思考，然后互相评价，最后综合决策
    
    适用场景：
    - 方案设计
    - 问题求解
    - 创意生成
    """
    
    def __init__(self, agents: list[Any], evaluator: Optional[Any] = None):
        self.agents = agents
        self.evaluator = evaluator  # 可选的独立评估者
    
    async def execute(self, problem: str, verbose: bool = True) -> CollaborationResult:
        """执行头脑风暴"""
        start_time = time.time()
        
        if verbose:
            print(f"\n[头脑风暴] 问题：{problem[:100]}...")
            print(f"[头脑风暴] 参与者：{', '.join(a.name for a in self.agents)}")
        
        # 阶段 1：独立生成想法
        if verbose:
            print(f"\n[阶段 1] 独立生成想法...")
        
        idea_prompts = [
            f"针对以下问题，提出 3 个不同的解决方案：\n\n问题：{problem}\n\n"
            f"要求：\n"
            f"1. 每个方案应该有明确的思路\n"
            f"2. 说明方案的优缺点\n"
            f"3. 评估可行性（高/中/低）\n"
            f"\n以 JSON 格式返回：\n"
            f'{{"ideas": [{{"name": "方案名", "description": "描述", "pros": [], "cons": [], "feasibility": "高/中/低"}}]}}'
        ] * len(self.agents)
        
        # 并行生成想法
        ideas_tasks = []
        for agent, prompt in zip(self.agents, idea_prompts):
            ideas_tasks.append(self._run_agent(agent, prompt))
        
        ideas_results = await asyncio.gather(*ideas_tasks, return_exceptions=True)
        ideas = []
        for i, (agent, result) in enumerate(zip(self.agents, ideas_results)):
            if isinstance(result, Exception):
                if verbose:
                    print(f"[警告] {agent.name} 生成想法失败：{result}")
            else:
                ideas.append({
                    "agent": agent.name,
                    "content": result
                })
                if verbose:
                    print(f"[{agent.name}] 生成了想法")
        
        # 阶段 2：互相评价
        if verbose:
            print(f"\n[阶段 2] 互相评价...")
        
        all_ideas_text = "\n\n".join([
            f"来自 {idea['agent']}:\n{idea['content'][:500]}"
            for idea in ideas
        ])
        
        eval_prompt = f"""评价以下所有方案：

问题：{problem}

{all_ideas_text}

请：
1. 对每个方案进行评分（1-10 分）
2. 指出最佳方案并说明理由
3. 提出综合改进建议

返回 JSON：
{{"evaluations": [{{"idea_source": "来源", "score": 8, "comment": "评价"}}], "best_choice": "最佳方案", "suggestion": "综合建议"}}
"""
        
        evaluations = []
        for agent in self.agents:
            try:
                eval_result = await self._run_agent(agent, eval_prompt)
                evaluations.append({
                    "agent": agent.name,
                    "content": eval_result
                })
            except Exception as e:
                if verbose:
                    print(f"[警告] {agent.name} 评价失败：{e}")
        
        # 阶段 3：综合决策
        if verbose:
            print(f"\n[阶段 3] 综合决策...")
        
        synthesis_prompt = f"""综合所有想法和评价，给出最终方案：

问题：{problem}

想法：
{all_ideas_text[:1000]}

评价：
{str(evaluations)[:500]}

请：
1. 总结各方案的优点
2. 给出最终推荐方案
3. 说明实施步骤

返回清晰的最终答案。
"""
        
        # 使用第一个 Agent 进行综合（或者使用专门的 evaluator）
        final_agent = self.evaluator if self.evaluator else self.agents[0]
        final_result = await self._run_agent(final_agent, synthesis_prompt)
        
        execution_time = time.time() - start_time
        
        return CollaborationResult(
            success=True,
            output=final_result,
            participants=[a.name for a in self.agents],
            iterations=3,  # 3 个阶段
            execution_time=execution_time,
            metadata={"ideas_count": len(ideas), "evaluations_count": len(evaluations)}
        )
    
    async def _run_agent(self, agent: Any, prompt: str) -> str:
        """运行 Agent"""
        if asyncio.iscoroutinefunction(agent.run):
            result = await agent.run(prompt, verbose=False)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: agent.run(prompt, verbose=False))
        return result


class MarketBasedAllocation:
    """基于市场的任务分配模式
    
    Agent 通过"竞价"方式竞争任务，出价（胜任度评估）最高者获得任务
    
    优势：
    - 自适应任务分配
    - 发挥各 Agent 优势
    - 去中心化决策
    """
    
    def __init__(self, agents: list[Any]):
        self.agents = agents
    
    async def allocate(self, task_description: str, verbose: bool = True) -> tuple[Any, float]:
        """分配任务给最合适的 Agent
        
        Returns:
            (选中的 Agent, 胜出价)
        """
        if verbose:
            print(f"\n[市场分配] 任务：{task_description[:100]}...")
            print(f"[市场分配] 竞标者：{len(self.agents)} 个 Agent")
        
        # 收集竞标
        bids = []
        bid_tasks = []
        
        for agent in self.agents:
            bid_prompt = f"""评估你对以下任务的胜任度：

任务：{task_description}

你的能力和专长：{getattr(agent, 'description', agent.name)}

请评估你的胜任度（0.0-1.0 之间的数字）：
- 0.0: 完全不胜任
- 0.5: 一般胜任
- 1.0: 完全胜任

只返回一个数字，如：0.85
"""
            bid_tasks.append(self._run_agent(agent, bid_prompt))
        
        # 并行收集竞标
        bid_results = await asyncio.gather(*bid_tasks, return_exceptions=True)
        
        for agent, result in zip(self.agents, bid_results):
            if isinstance(result, Exception):
                if verbose:
                    print(f"[{agent.name}] 竞标失败：{result}")
                bids.append((agent, 0.5))  # 默认出价
            else:
                try:
                    # 提取数字
                    import re
                    numbers = re.findall(r'\d+\.?\d*', str(result))
                    bid = float(numbers[0]) if numbers else 0.5
                    bid = max(0.0, min(1.0, bid))  # 限制在 0-1 范围
                    bids.append((agent, bid))
                    if verbose:
                        print(f"[{agent.name}] 竞标：{bid:.2f}")
                except (ValueError, IndexError):
                    bids.append((agent, 0.5))
        
        # 选择最高出价者
        winner = max(bids, key=lambda x: x[1])
        
        if verbose:
            print(f"\n[市场分配] 胜出者：{winner[0].name} (出价：{winner[1]:.2f})")
        
        return winner
    
    async def _run_agent(self, agent: Any, prompt: str) -> str:
        """运行 Agent"""
        if asyncio.iscoroutinefunction(agent.run):
            result = await agent.run(prompt, verbose=False)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: agent.run(prompt, verbose=False))
        return result


class CodeReviewLoop:
    """代码审查循环模式
    
    多个 Reviewer 轮流审查，直到所有问题被解决
    
    流程：
    1. Developer 提交代码
    2. Reviewer1 审查
    3. Developer 修改
    4. Reviewer2 审查
    5. 循环直到通过
    """
    
    def __init__(self, developer: Any, reviewers: list[Any], max_rounds: int = 3):
        self.developer = developer
        self.reviewers = reviewers
        self.max_rounds = max_rounds
    
    async def execute(self, task: str, initial_code: Optional[str] = None, verbose: bool = True) -> CollaborationResult:
        """执行审查循环"""
        start_time = time.time()
        code = initial_code
        all_feedback = []
        rounds = 0
        
        if verbose:
            print(f"\n[审查循环] 任务：{task[:100]}...")
            print(f"[审查循环] Developer: {self.developer.name}")
            print(f"[审查循环] Reviewers: {', '.join(r.name for r in self.reviewers)}")
        
        for round_num in range(self.max_rounds):
            rounds += 1
            
            # 如果没有初始代码，Developer 先编写
            if not code:
                if verbose:
                    print(f"\n[回合 {round_num}] Developer 编写代码...")
                code = await self._run_agent(self.developer, f"实现：{task}")
            
            # 每个 Reviewer 审查
            round_feedback = []
            for reviewer in self.reviewers:
                if verbose:
                    print(f"[回合 {round_num}] {reviewer.name} 审查...")
                
                review_prompt = f"""审查代码：

任务：{task}

代码：
{code}

请指出：
1. 代码问题
2. 改进建议
3. 如果通过，回复"LGTM"
"""
                feedback = await self._run_agent(reviewer, review_prompt)
                round_feedback.append({
                    "reviewer": reviewer.name,
                    "feedback": feedback
                })
                
                if verbose:
                    print(f"[{reviewer.name}] {feedback[:50]}...")
            
            all_feedback.extend(round_feedback)
            
            # 检查是否所有 Reviewer 都通过
            all_approved = all(
                self._is_approved(fb["feedback"])
                for fb in round_feedback
            )
            
            if all_approved:
                if verbose:
                    print(f"\n[审查循环] 所有审查通过！")
                break
            
            # Developer 修改
            if verbose:
                print(f"\n[回合 {round_num}] Developer 根据反馈修改...")
            
            feedback_text = "\n\n".join([
                f"{fb['reviewer']}:\n{fb['feedback']}"
                for fb in round_feedback
            ])
            
            modify_prompt = f"""根据审查反馈修改代码：

原任务：{task}

当前代码：
{code}

审查反馈：
{feedback_text}

请修改代码以解决所有问题。
"""
            code = await self._run_agent(self.developer, modify_prompt)
        
        execution_time = time.time() - start_time
        all_approved = all(
            self._is_approved(fb["feedback"])
            for fb in all_feedback[-len(self.reviewers):]
        ) if all_feedback else False
        
        return CollaborationResult(
            success=all_approved,
            output=code or "",
            participants=[self.developer.name] + [r.name for r in self.reviewers],
            iterations=rounds,
            execution_time=execution_time,
            metadata={"feedback": all_feedback}
        )
    
    def _is_approved(self, feedback: str) -> bool:
        """检查是否通过"""
        # 从配置加载关键词，避免硬编码
        from configs.common_keywords import CommonKeywordsConfig
        approval_keywords = CommonKeywordsConfig.get_approval_keywords()
        return any(kw in feedback.lower() for kw in approval_keywords)
    
    async def _run_agent(self, agent: Any, prompt: str) -> str:
        """运行 Agent"""
        if asyncio.iscoroutinefunction(agent.run):
            result = await agent.run(prompt, verbose=False)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: agent.run(prompt, verbose=False))
        return result
