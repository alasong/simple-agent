"""
高级推理工具 - 将推理模式封装为可调用的工具

包含：
- TreeOfThoughtTool: 思维树多路径探索
- IterativeOptimizerTool: 多轮迭代优化
- SwarmVotingTool: 群体投票决策
- MultiPathOptimizerTool: 多路径并行优化
"""

import asyncio
import json
import re
import time
from typing import Optional, Any, List, Dict
from dataclasses import dataclass, field


# ==================== TreeOfThought 工具 ====================

@dataclass
class ThoughtNode:
    """思维节点"""
    content: str
    score: float = 0.0
    parent: Optional['ThoughtNode'] = None
    children: List['ThoughtNode'] = field(default_factory=list)
    evaluation: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "score": round(self.score, 2),
            "evaluation": self.evaluation
        }


class TreeOfThoughtTool:
    """
    思维树多路径探索工具

    通过广度优先和深度优先的结合，探索多个解决方案路径

    使用示例:
        tool = TreeOfThoughtTool(agent)
        result = await tool.execute("如何设计一个高并发系统？")
    """

    def __init__(
        self,
        agent: Any,
        breadth: int = 3,  # 每层生成思路数
        depth: int = 3,    # 最大深度
        temperature: float = 0.7  # 创造性程度
    ):
        self.agent = agent
        self.breadth = breadth
        self.depth = depth
        self.temperature = temperature
        self.verbose = True

    async def execute(
        self,
        problem: str,
        breadth: Optional[int] = None,
        depth: Optional[int] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        执行思维树推理

        Args:
            problem: 待解决的问题
            breadth: 每层生成的思路数（可选，覆盖默认值）
            depth: 最大深度（可选，覆盖默认值）
            verbose: 是否输出详细日志

        Returns:
            包含最佳方案和完整思维树的字典
        """
        breadth = breadth or self.breadth
        depth = depth or self.depth
        self.verbose = verbose

        start_time = time.time()

        if verbose:
            print(f"\n[思维树] 问题：{problem[:100]}...")
            print(f"[思维树] 广度：{breadth}, 深度：{depth}")

        # 第 1 步：生成初始思路
        if verbose:
            print(f"\n[思维树] 第 1/3 步：生成初始思路...")

        thoughts = await self._generate_thoughts(problem, breadth)

        if verbose:
            print(f"[思维树] 生成了 {len(thoughts)} 个初始思路")
            for i, t in enumerate(thoughts, 1):
                print(f"  [{i}] {t.content[:50]}...")

        # 第 2 步：迭代扩展和评估
        for level in range(depth - 1):
            if verbose:
                print(f"\n[思维树] 第 {level + 2}/{depth + 1} 步：评估和扩展...")

            # 评估当前层
            evaluations = await self._evaluate_thoughts(problem, thoughts)
            for thought, eval_result in zip(thoughts, evaluations):
                thought.score = eval_result.get('score', 0.5)
                thought.evaluation = eval_result

            if verbose:
                print(f"[思维树] 评估完成，最高分：{max(t.score for t in thoughts):.2f}")

            # 选择 Top-K 扩展
            top_k = max(1, breadth // 2)
            thoughts.sort(key=lambda x: x.score, reverse=True)
            best_thoughts = thoughts[:top_k]

            if verbose:
                print(f"[思维树] 选择 Top-{top_k} 思路进行扩展")

            # 扩展下一层
            thoughts = await self._expand_thoughts(problem, best_thoughts, breadth // top_k + 1)

            if verbose:
                print(f"[思维树] 扩展后共 {len(thoughts)} 个思路")

        # 第 3 步：最终评估和选择
        if verbose:
            print(f"\n[思维树] 第 {depth + 1}/{depth + 2} 步：最终评估...")

        evaluations = await self._evaluate_thoughts(problem, thoughts)
        for thought, eval_result in zip(thoughts, evaluations):
            thought.score = eval_result.get('score', 0.5)
            thought.evaluation = eval_result

        # 选择最佳方案
        best_thought = max(thoughts, key=lambda x: x.score)

        if verbose:
            print(f"\n[思维树] 最终方案（评分：{best_thought.score:.2f}）:")
            print(f"  {best_thought.content[:200]}...")

        execution_time = time.time() - start_time

        return {
            "success": True,
            "best_solution": best_thought.content,
            "best_score": round(best_thought.score, 2),
            "total_thoughts": len(thoughts),
            "tree_depth": depth,
            "execution_time": round(execution_time, 2),
            "all_thoughts": [t.to_dict() for t in thoughts]
        }

    async def _generate_thoughts(self, problem: str, n: int) -> List[ThoughtNode]:
        """生成 N 个初始思路"""
        prompt = f"""问题：{problem}

请提出 {n} 个不同的解决思路。

要求：
1. 每个思路应该有明显的差异化
2. 思路应该具体、可执行
3. 覆盖不同的角度和方法

以 JSON 数组格式返回：
["思路 1：具体内容...", "思路 2：具体内容...", ...]
"""
        response = await self._run_agent(self.agent, prompt)
        ideas = self._parse_json_array(response)

        return [ThoughtNode(content=idea) for idea in ideas[:n]]

    async def _evaluate_thoughts(self, problem: str, thoughts: List[ThoughtNode]) -> List[Dict]:
        """评估每个思路的质量"""
        evaluations = []

        for thought in thoughts:
            prompt = f"""问题：{problem}
思路：{thought.content}

请评估这个思路的质量（0-1 分）：
- 可行性（是否可执行）
- 完整性（是否覆盖关键点）
- 效率（是否高效）
- 创新性（是否有独特价值）

返回 JSON 格式：
{{"score": 0.85, "feasibility": 0.9, "completeness": 0.8, "efficiency": 0.8, "innovation": 0.9, "reason": "评估理由..."}}
"""
            response = await self._run_agent(self.agent, prompt)
            eval_result = self._parse_json(response)
            evaluations.append(eval_result)

        return evaluations

    async def _expand_thoughts(
        self,
        problem: str,
        parent_thoughts: List[ThoughtNode],
        expansions_per_parent: int = 2
    ) -> List[ThoughtNode]:
        """扩展思路"""
        expanded = []

        for parent in parent_thoughts:
            prompt = f"""问题：{problem}
当前思路：{parent.content}

基于这个思路，提出 {expansions_per_parent} 个更深入的细化方案。

要求：
1. 每个细化方案应该是当前思路的具体化或延伸
2. 细化方案之间应该有差异化
3. 方案应该更具体、更可执行

返回 JSON 数组：
["细化方案 1...", "细化方案 2...", ...]
"""
            response = await self._run_agent(self.agent, prompt)
            refinements = self._parse_json_array(response)

            for refinement in refinements[:expansions_per_parent]:
                child = ThoughtNode(
                    content=refinement,
                    parent=parent,
                    score=parent.score  # 继承父节点评分作为初始值
                )
                parent.children.append(child)
                expanded.append(child)

        return expanded

    async def _run_agent(self, agent: Any, prompt: str) -> str:
        """运行 Agent"""
        if asyncio.iscoroutinefunction(agent.run):
            result = await agent.run(prompt, verbose=False)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: agent.run(prompt, verbose=False))
        return result

    def _parse_json(self, text: str) -> Dict:
        """解析 JSON 对象"""
        try:
            # 尝试直接解析
            return json.loads(text)
        except:
            # 尝试提取 JSON
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {}

    def _parse_json_array(self, text: str) -> List:
        """解析 JSON 数组"""
        try:
            return json.loads(text)
        except:
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return []


# ==================== Iterative Optimizer 工具 ====================

class IterativeOptimizerTool:
    """
    多轮迭代优化工具

    通过多轮迭代和独立质量评估，持续优化方案质量
    """

    def __init__(
        self,
        agent: Any,
        evaluator_agent: Optional[Any] = None,
        max_iterations: int = 3,
        quality_threshold: float = 0.75
    ):
        self.agent = agent
        self.evaluator_agent = evaluator_agent or agent
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.verbose = True

    async def execute(
        self,
        problem: str,
        initial_solution: Optional[str] = None,
        max_iterations: Optional[int] = None,
        quality_threshold: Optional[float] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        执行迭代优化

        Args:
            problem: 待解决的问题
            initial_solution: 初始方案（可选，不提供则自动生成）
            max_iterations: 最大迭代次数
            quality_threshold: 质量阈值（达到后停止）
            verbose: 是否输出详细日志

        Returns:
            包含优化结果和迭代历史的字典
        """
        max_iterations = max_iterations or self.max_iterations
        quality_threshold = quality_threshold or self.quality_threshold
        self.verbose = verbose

        start_time = time.time()
        iterations = []

        if verbose:
            print(f"\n[迭代优化] 问题：{problem[:100]}...")
            print(f"[迭代优化] 最大迭代：{max_iterations}, 质量阈值：{quality_threshold:.0%}")

        # 生成或使用初始方案
        if initial_solution:
            current_solution = initial_solution
            if verbose:
                print(f"[迭代优化] 使用初始方案，长度：{len(current_solution)}")
        else:
            if verbose:
                print(f"[迭代优化] 生成初始方案...")
            current_solution = await self._generate_solution(problem)

        # 评估初始方案
        if verbose:
            print(f"[迭代优化] 评估初始方案...")

        initial_score = await self._evaluate_quality(current_solution, problem)

        if verbose:
            print(f"[迭代优化] 初始评分：{initial_score:.2f}")

        iterations.append({
            "iteration": 0,
            "score": round(initial_score, 2),
            "content": current_solution
        })

        # 检查是否已达到阈值
        if initial_score >= quality_threshold:
            if verbose:
                print(f"[迭代优化] 初始方案已达到质量阈值，无需迭代")

            return {
                "success": True,
                "best_solution": current_solution,
                "final_score": round(initial_score, 2),
                "total_iterations": 0,
                "iterations": iterations,
                "execution_time": round(time.time() - start_time, 2)
            }

        # 迭代优化
        best_solution = current_solution
        best_score = initial_score

        for i in range(1, max_iterations + 1):
            if verbose:
                print(f"\n{'='*50}")
                print(f"[迭代优化] 第 {i}/{max_iterations} 轮迭代")
                print(f"[迭代优化] 当前最佳评分：{best_score:.2f}")

            iter_start = time.time()

            # 生成改进建议
            if verbose:
                print(f"[迭代优化] 生成改进建议...")

            feedback = await self._generate_feedback(best_solution, problem)

            # 优化方案
            if verbose:
                print(f"[迭代优化] 优化方案...")

            optimized = await self._optimize_solution(best_solution, problem, feedback)

            # 评估优化后的方案
            if verbose:
                print(f"[迭代优化] 评估优化方案...")

            new_score = await self._evaluate_quality(optimized, problem)

            iter_duration = time.time() - iter_start

            if verbose:
                print(f"[迭代优化] 新评分：{new_score:.2f} (变化：{new_score - best_score:+.2f})")

            iterations.append({
                "iteration": i,
                "score": round(new_score, 2),
                "content": optimized,
                "duration": round(iter_duration, 2)
            })

            # 更新最佳方案
            if new_score > best_score:
                if verbose:
                    print(f"[迭代优化] ✓ 发现更优方案！提升：{new_score - best_score:.2f}")

                best_solution = optimized
                best_score = new_score

                # 检查是否达到阈值
                if best_score >= quality_threshold:
                    if verbose:
                        print(f"\n[迭代优化] 已达到质量阈值，停止迭代")
                    break
            else:
                if verbose:
                    print(f"[迭代优化] 优化未带来提升，保留原方案")

        execution_time = time.time() - start_time

        if verbose:
            print(f"\n{'='*50}")
            print(f"[迭代优化] 优化完成")
            print(f"[迭代优化] 最终评分：{best_score:.2f}")
            print(f"[迭代优化] 总耗时：{execution_time:.2f}秒")

        return {
            "success": best_score >= quality_threshold,
            "best_solution": best_solution,
            "final_score": round(best_score, 2),
            "total_iterations": len(iterations) - 1,
            "iterations": iterations,
            "execution_time": round(execution_time, 2)
        }

    async def _generate_solution(self, problem: str) -> str:
        """生成初始方案"""
        prompt = f"""针对以下问题，生成一个全面的解决方案：

问题：{problem}

要求：
1. 方案应该完整、可执行
2. 包含具体的步骤和方法
3. 考虑可能的边界情况
4. 提供清晰的结论

请生成详细的解决方案。
"""
        return await self._run_agent(self.agent, prompt)

    async def _evaluate_quality(self, content: str, problem: str) -> float:
        """评估方案质量"""
        prompt = f"""评估以下方案的质量（0-1 分）：

问题：{problem}

方案：
{content[:3000]}

评分标准：
- 0.9-1.0: 优秀，超出预期
- 0.75-0.9: 良好，满足要求
- 0.6-0.75: 合格，基本完成
- 0.4-0.6: 较差，需要改进
- 0-0.4: 不合格，需要重做

只返回一个数字，如：0.85
"""
        response = await self._run_agent(self.evaluator_agent, prompt)

        # 提取数字
        numbers = re.findall(r'\d+\.?\d*', str(response))
        if numbers:
            score = float(numbers[0])
            return min(1.0, max(0.0, score))

        return 0.5

    async def _generate_feedback(self, content: str, problem: str) -> str:
        """生成改进建议"""
        prompt = f"""分析以下方案，提供具体的改进建议：

问题：{problem}

当前方案：
{content[:3000]}

请指出：
1. 方案的优点（保持）
2. 存在的问题或不足（至少 3 点）
3. 具体的改进建议（至少 3 条，越具体越好）
4. 是否有遗漏的重要考虑因素

请以清晰的格式返回改进建议。
"""
        return await self._run_agent(self.evaluator_agent, prompt)

    async def _optimize_solution(self, current: str, problem: str, feedback: str) -> str:
        """基于反馈优化方案"""
        prompt = f"""根据以下反馈，优化现有方案：

问题：{problem}

当前方案：
{current[:3000]}

改进建议：
{feedback}

请：
1. 保留当前方案的优点
2. 针对每个改进建议进行优化
3. 提供优化后的完整方案（不是只说改进点）
4. 在方案开头简要说明做了哪些改进

返回优化后的完整方案。
"""
        return await self._run_agent(self.agent, prompt)

    async def _run_agent(self, agent: Any, prompt: str) -> str:
        """运行 Agent"""
        if asyncio.iscoroutinefunction(agent.run):
            result = await agent.run(prompt, verbose=False)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: agent.run(prompt, verbose=False))
        return result


# ==================== Swarm Voting 工具 ====================

class SwarmVotingTool:
    """
    群体投票决策工具

    多个 Agent 独立生成方案 → 互相评分 → 投票选择最优

    适用于需要集思广益、避免个人偏见的场景
    """

    def __init__(
        self,
        agents: List[Any],
        voting_rounds: int = 2,
        eliminate_lowest: float = 0.3  # 每轮淘汰最低分的比例
    ):
        self.agents = agents
        self.voting_rounds = voting_rounds
        self.eliminate_lowest = eliminate_lowest
        self.verbose = True

    async def execute(
        self,
        problem: str,
        voting_rounds: Optional[int] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        执行群体投票决策

        Args:
            problem: 待解决的问题
            voting_rounds: 投票轮数
            verbose: 是否输出详细日志

        Returns:
            包含获胜方案和投票结果的字典
        """
        voting_rounds = voting_rounds or self.voting_rounds
        self.verbose = verbose

        start_time = time.time()

        if verbose:
            print(f"\n[群体投票] 问题：{problem[:100]}...")
            print(f"[群体投票] 参与 Agent: {len(self.agents)}个")
            print(f"[群体投票] 投票轮数：{voting_rounds}")

        # 第 1 步：各 Agent 独立生成方案
        if verbose:
            print(f"\n[群体投票] 第 1 步：各 Agent 独立生成方案...")

        proposals = await self._generate_proposals(problem)

        if verbose:
            print(f"[群体投票] 收到 {len(proposals)} 个方案")
            for i, (agent_name, proposal) in enumerate(proposals, 1):
                print(f"  [{i}] {agent_name}: {proposal[:50]}...")

        # 第 2 步：多轮投票
        current_proposals = proposals

        for round_num in range(1, voting_rounds + 1):
            if verbose:
                print(f"\n[群体投票] 第 {round_num}/{voting_rounds} 轮投票...")

            # 评分
            scores = await self._score_proposals(problem, current_proposals)

            if verbose:
                print(f"[群体投票] 评分完成:")
                for (agent_name, proposal), score in zip(current_proposals, scores):
                    print(f"  - {agent_name}: {score:.2f}")

            # 如果只剩一个方案，直接获胜
            if len(current_proposals) == 1:
                if verbose:
                    print(f"[群体投票] 唯一方案胜出")
                break

            # 淘汰最低分
            eliminate_count = max(1, int(len(current_proposals) * self.eliminate_lowest))
            scored_proposals = list(zip(current_proposals, scores))
            scored_proposals.sort(key=lambda x: x[1], reverse=True)

            if verbose:
                print(f"[群体投票] 淘汰最后 {eliminate_count} 名")

            current_proposals = [p for p, s in scored_proposals[:-eliminate_count]]

        # 最终获胜方案
        winner_proposal = current_proposals[0] if current_proposals else proposals[0]
        winner_score = scores[0] if scores else 0.0

        execution_time = time.time() - start_time

        if verbose:
            print(f"\n[群体投票] 投票完成")
            print(f"[群体投票] 获胜方案 ({winner_proposal[0]}): {winner_proposal[1][:100]}...")

        return {
            "success": True,
            "winning_proposal": {
                "agent": winner_proposal[0],
                "content": winner_proposal[1],
                "score": round(winner_score, 2)
            },
            "total_proposals": len(proposals),
            "voting_rounds": voting_rounds,
            "execution_time": round(execution_time, 2),
            "all_proposals": [
                {"agent": agent_name, "content": content}
                for agent_name, content in proposals
            ],
            "final_scores": [
                {"agent": agent_name, "score": round(score, 2)}
                for (agent_name, _), score in zip(proposals, scores)
            ]
        }

    async def _generate_proposals(self, problem: str) -> List[tuple]:
        """各 Agent 独立生成方案"""
        proposals = []

        for agent in self.agents:
            prompt = f"""针对以下问题，提出你的解决方案：

问题：{problem}

要求：
1. 方案应该完整、可执行
2. 体现你的专业判断和独特视角
3. 不必迎合他人观点，坚持你认为最优的方案
4. 在方案开头用一句话总结核心思路

请生成详细的解决方案。
"""
            response = await self._run_agent(agent, prompt)
            agent_name = getattr(agent, 'name', str(agent))
            proposals.append((agent_name, response))

        return proposals

    async def _score_proposals(
        self,
        problem: str,
        proposals: List[tuple]
    ) -> List[float]:
        """各 Agent 互相评分"""
        all_scores = []

        # 每个 Agent 对所有方案评分
        for voting_agent in self.agents:
            scores = []

            for agent_name, proposal in proposals:
                prompt = f"""作为独立评审，请评估以下方案的质量（0-1 分）：

问题：{problem}

方案（由{agent_name}提出）：
{proposal[:2000]}

评分标准：
- 可行性（是否可执行）
- 完整性（是否覆盖关键点）
- 效率（是否高效）
- 创新性（是否有独特价值）

只返回一个数字，如：0.85
"""
                response = await self._run_agent(voting_agent, prompt)
                numbers = re.findall(r'\d+\.?\d*', str(response))
                score = float(numbers[0]) if numbers else 0.5
                scores.append(min(1.0, max(0.0, score)))

            all_scores.append(scores)

        # 计算平均分
        num_proposals = len(proposals)
        final_scores = [
            sum(agent_scores[i] for agent_scores in all_scores) / len(all_scores)
            for i in range(num_proposals)
        ]

        return final_scores

    async def _run_agent(self, agent: Any, prompt: str) -> str:
        """运行 Agent"""
        if asyncio.iscoroutinefunction(agent.run):
            result = await agent.run(prompt, verbose=False)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: agent.run(prompt, verbose=False))
        return result


# ==================== Multi-Path Optimizer 工具 ====================

class MultiPathOptimizerTool:
    """
    多路径并行优化工具

    同时生成 N 个不同方向的初始方案
    每轮迭代后保留 Top-K 个继续优化
    最终选择最优方案

    结合了群体智慧和迭代优化的优势
    """

    def __init__(
        self,
        agent: Any,
        evaluator_agent: Optional[Any] = None,
        num_paths: int = 3,      # 同时探索的路径数
        keep_top_k: int = 2,     # 每轮保留的路径数
        max_iterations: int = 3, # 最大迭代次数
        diversity_bonus: float = 0.1  # 多样性加分
    ):
        self.agent = agent
        self.evaluator_agent = evaluator_agent or agent
        self.num_paths = num_paths
        self.keep_top_k = keep_top_k
        self.max_iterations = max_iterations
        self.diversity_bonus = diversity_bonus
        self.verbose = True

    async def execute(
        self,
        problem: str,
        num_paths: Optional[int] = None,
        keep_top_k: Optional[int] = None,
        max_iterations: Optional[int] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        执行多路径优化

        Args:
            problem: 待解决的问题
            num_paths: 同时探索的路径数
            keep_top_k: 每轮保留的路径数
            max_iterations: 最大迭代次数
            verbose: 是否输出详细日志

        Returns:
            包含最优方案和迭代历史的字典
        """
        num_paths = num_paths or self.num_paths
        keep_top_k = keep_top_k or self.keep_top_k
        max_iterations = max_iterations or self.max_iterations
        self.verbose = verbose

        start_time = time.time()

        if verbose:
            print(f"\n[多路径优化] 问题：{problem[:100]}...")
            print(f"[多路径优化] 路径数：{num_paths}, 保留 Top-{keep_top_k}, 最大迭代：{max_iterations}")

        # 第 1 步：生成多个不同方向的初始方案
        if verbose:
            print(f"\n[多路径优化] 第 1 步：生成 {num_paths} 个不同方向的初始方案...")

        paths = await self._generate_diverse_solutions(problem, num_paths)

        if verbose:
            print(f"[多路径优化] 生成了 {len(paths)} 个初始方案")
            for i, path in enumerate(paths, 1):
                print(f"  [{i}] {path['direction']}: {path['content'][:50]}... (评分：{path['score']:.2f})")

        # 第 2 步：多轮迭代优化
        iteration_history = []

        for iteration in range(1, max_iterations + 1):
            if verbose:
                print(f"\n{'='*50}")
                print(f"[多路径优化] 第 {iteration}/{max_iterations} 轮迭代")

            iter_start = time.time()

            # 淘汰最低分路径
            if len(paths) > keep_top_k:
                paths.sort(key=lambda x: x['score'], reverse=True)
                eliminated = paths[keep_top_k:]
                paths = paths[:keep_top_k]

                if verbose:
                    print(f"[多路径优化] 淘汰 {len(eliminated)} 个低分路径")
                    for path in eliminated:
                        print(f"  - {path['direction']}: {path['score']:.2f}")

            # 对每个路径进行优化
            optimized_paths = []
            for path in paths:
                if verbose:
                    print(f"\n[多路径优化] 优化路径：{path['direction']}")

                # 生成改进建议
                feedback = await self._generate_feedback(path['content'], problem)

                # 优化方案
                optimized_content = await self._optimize_solution(
                    path['content'], problem, feedback, path['direction']
                )

                # 重新评估
                new_score = await self._evaluate_quality(optimized_content, problem)

                # 多样性加分（与其他路径的差异程度）
                diversity_score = self._calculate_diversity(optimized_content, optimized_paths)
                new_score += diversity_score * self.diversity_bonus

                if verbose:
                    print(f"[多路径优化] 新评分：{new_score:.2f} (多样性加分：{diversity_score * self.diversity_bonus:.3f})")

                optimized_paths.append({
                    'direction': path['direction'],
                    'content': optimized_content,
                    'score': new_score,
                    'feedback': feedback
                })

            paths = optimized_paths
            iteration_history.append({
                'iteration': iteration,
                'paths': [
                    {'direction': p['direction'], 'score': round(p['score'], 2)}
                    for p in paths
                ],
                'duration': round(time.time() - iter_start, 2)
            })

        # 选择最优方案
        best_path = max(paths, key=lambda x: x['score'])
        execution_time = time.time() - start_time

        if verbose:
            print(f"\n{'='*50}")
            print(f"[多路径优化] 优化完成")
            print(f"[多路径优化] 最优方案：{best_path['direction']}")
            print(f"[多路径优化] 最终评分：{best_path['score']:.2f}")
            print(f"[多路径优化] 总耗时：{execution_time:.2f}秒")

        return {
            "success": True,
            "best_solution": {
                "direction": best_path['direction'],
                "content": best_path['content'],
                "score": round(best_path['score'], 2)
            },
            "final_paths": [
                {
                    "direction": p['direction'],
                    "score": round(p['score'], 2),
                    "content": p['content'][:500]
                }
                for p in paths
            ],
            "iteration_history": iteration_history,
            "execution_time": round(execution_time, 2)
        }

    async def _generate_diverse_solutions(self, problem: str, num_paths: int) -> List[Dict]:
        """生成多个不同方向的初始方案"""
        # 定义不同的思考方向
        directions = [
            "保守稳健型：注重可靠性、风险控制、循序渐进",
            "激进创新型：追求突破性、技术领先、快速迭代",
            "平衡实用型：兼顾效果与成本、注重实际可行性",
            "用户导向型：从用户体验出发、注重易用性和满意度",
            "技术驱动型：采用最新技术、注重架构先进性",
            "业务导向型：聚焦业务价值、快速见效"
        ]

        paths = []
        used_directions = directions[:num_paths]

        for direction in used_directions:
            prompt = f"""针对以下问题，从指定方向生成解决方案：

问题：{problem}

方向定位：{direction}

要求：
1. 方案应该体现该方向的特点
2. 方案应该完整、可执行
3. 提供清晰的实施步骤

请生成详细的解决方案。
"""
            response = await self._run_agent(self.agent, prompt)
            score = await self._evaluate_quality(response, problem)

            paths.append({
                'direction': direction.split('：')[0],  # 取方向名称
                'content': response,
                'score': score
            })

        return paths

    def _calculate_diversity(self, content: str, other_paths: List[Dict]) -> float:
        """计算与现有路径的多样性（简单版本：基于文本相似度）"""
        if not other_paths:
            return 1.0

        # 简单计算：基于文本重叠度
        content_words = set(content.lower().split())

        similarities = []
        for path in other_paths:
            other_words = set(path['content'].lower().split())
            if content_words and other_words:
                overlap = len(content_words & other_words) / len(content_words | other_words)
                similarities.append(overlap)

        if similarities:
            avg_similarity = sum(similarities) / len(similarities)
            return 1.0 - avg_similarity  # 相似度越低，多样性越高

        return 1.0

    async def _evaluate_quality(self, content: str, problem: str) -> float:
        """评估方案质量"""
        prompt = f"""评估以下方案的质量（0-1 分）：

问题：{problem}

方案：
{content[:3000]}

评分标准：
- 0.9-1.0: 优秀，超出预期
- 0.75-0.9: 良好，满足要求
- 0.6-0.75: 合格，基本完成
- 0.4-0.6: 较差，需要改进
- 0-0.4: 不合格，需要重做

只返回一个数字，如：0.85
"""
        response = await self._run_agent(self.evaluator_agent, prompt)
        numbers = re.findall(r'\d+\.?\d*', str(response))
        if numbers:
            score = float(numbers[0])
            return min(1.0, max(0.0, score))
        return 0.5

    async def _generate_feedback(self, content: str, problem: str) -> str:
        """生成改进建议"""
        prompt = f"""分析以下方案，提供具体的改进建议：

问题：{problem}

当前方案：
{content[:3000]}

请指出：
1. 方案的优点（保持）
2. 存在的问题或不足（至少 3 点）
3. 具体的改进建议（至少 3 条，越具体越好）

请返回改进建议。
"""
        return await self._run_agent(self.evaluator_agent, prompt)

    async def _optimize_solution(
        self,
        current: str,
        problem: str,
        feedback: str,
        direction: str
    ) -> str:
        """基于反馈优化方案"""
        prompt = f"""根据以下反馈，优化现有方案：

问题：{problem}
方向定位：{direction}

当前方案：
{current[:3000]}

改进建议：
{feedback}

请：
1. 保留当前方案的优点
2. 针对每个改进建议进行优化
3. 保持方案的方向定位不变
4. 提供优化后的完整方案

返回优化后的完整方案。
"""
        return await self._run_agent(self.agent, prompt)

    async def _run_agent(self, agent: Any, prompt: str) -> str:
        """运行 Agent"""
        if asyncio.iscoroutinefunction(agent.run):
            result = await agent.run(prompt, verbose=False)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: agent.run(prompt, verbose=False))
        return result


# ==================== 工厂函数 ====================

def create_tree_of_thought(
    agent: Any,
    breadth: int = 3,
    depth: int = 3
) -> TreeOfThoughtTool:
    """创建思维树工具"""
    return TreeOfThoughtTool(agent, breadth=breadth, depth=depth)


def create_iterative_optimizer(
    agent: Any,
    evaluator_agent: Optional[Any] = None,
    max_iterations: int = 3
) -> IterativeOptimizerTool:
    """创建迭代优化工具"""
    return IterativeOptimizerTool(agent, evaluator_agent=evaluator_agent, max_iterations=max_iterations)


def create_swarm_voting(
    agents: List[Any],
    voting_rounds: int = 2
) -> SwarmVotingTool:
    """创建群体投票工具"""
    return SwarmVotingTool(agents, voting_rounds=voting_rounds)


def create_multi_path_optimizer(
    agent: Any,
    evaluator_agent: Optional[Any] = None,
    num_paths: int = 3
) -> MultiPathOptimizerTool:
    """创建多路径优化工具"""
    return MultiPathOptimizerTool(agent, evaluator_agent=evaluator_agent, num_paths=num_paths)
