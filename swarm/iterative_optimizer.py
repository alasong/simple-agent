"""
多轮迭代优化器 (Iterative Optimizer)

通过多轮迭代和独立质量评估，持续优化方案质量。

功能：
- 多轮迭代优化
- 独立质量评估
- 质量阈值自动停止
- 迭代历史追溯
"""

import asyncio
import json
import time
from typing import Optional, Any, List, Dict
from dataclasses import dataclass, field


@dataclass
class IterationResult:
    """单次迭代结果"""
    iteration: int
    content: str
    score: float
    improvements: List[str] = field(default_factory=list)
    duration: float = 0.0

    def to_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "score": round(self.score, 2),
            "improvements": self.improvements,
            "duration": round(self.duration, 2)
        }


@dataclass
class OptimizationResult:
    """优化结果"""
    success: bool
    output: str
    final_score: float
    total_iterations: int
    iterations: List[IterationResult] = field(default_factory=list)
    execution_time: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output[:500],
            "final_score": round(self.final_score, 2),
            "total_iterations": self.total_iterations,
            "iterations": [i.to_dict() for i in self.iterations],
            "execution_time": round(self.execution_time, 2)
        }


class IterativeOptimizer:
    """多轮迭代优化器

    通过以下流程进行迭代优化：
    1. 生成初始方案
    2. 独立质量评估
    3. 基于反馈优化
    4. 重复直到达到阈值或最大轮数
    """

    def __init__(
        self,
        agents: List[Any],
        evaluator: Optional[Any] = None,
        quality_checker: Optional[Any] = None,
        max_iterations: int = 3,
        quality_threshold: float = 0.7,
        score_type: str = "normalized"  # "normalized" (0-1) or "raw" (1-5)
    ):
        """
        初始化迭代优化器

        Args:
            agents: 参与优化的 Agent 列表
            evaluator: 独立质量评估器（可选）
            quality_checker: 质量检查器（可选）
            max_iterations: 最大迭代轮数
            quality_threshold: 质量阈值（达到后停止迭代）
            score_type: 评分类型 ("normalized" 0-1 或 "raw" 1-5)
        """
        self.agents = agents
        self.evaluator = evaluator
        self.quality_checker = quality_checker
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.score_type = score_type

    async def execute(
        self,
        problem: str,
        initial_solution: Optional[str] = None,
        verbose: bool = True
    ) -> OptimizationResult:
        """
        执行迭代优化

        Args:
            problem: 要解决的问题
            initial_solution: 初始方案（可选）
            verbose: 是否输出详细日志

        Returns:
            OptimizationResult: 优化结果
        """
        start_time = time.time()
        iterations = []

        if verbose:
            print(f"\n[迭代优化] 问题：{problem[:100]}...")
            print(f"[迭代优化] 最大迭代轮数：{self.max_iterations}")
            print(f"[迭代优化] 质量阈值：{self.quality_threshold}")
            print(f"[迭代优化] Agent 数量：{len(self.agents)}")

        # 生成/使用初始方案
        if initial_solution:
            current_solution = initial_solution
            if verbose:
                print(f"\n[迭代优化] 使用初始方案，长度：{len(current_solution)}")
        else:
            if verbose:
                print(f"\n[迭代优化] 生成初始方案...")
            current_solution = await self._generate_initial_solution(problem)

        # 评估初始方案
        if verbose:
            print(f"\n[迭代优化] 评估初始方案...")

        initial_score = await self._evaluate_quality(current_solution, problem)
        normalized_initial = self._normalize_score(initial_score)

        if verbose:
            print(f"[迭代优化] 初始评分：{initial_score} (归一化：{normalized_initial:.2f})")

        # 记录初始迭代
        iterations.append(IterationResult(
            iteration=0,
            content=current_solution,
            score=normalized_initial,
            duration=time.time() - start_time
        ))

        # 检查是否已达到阈值
        if normalized_initial >= self.quality_threshold:
            if verbose:
                print(f"\n[迭代优化] 初始方案已达到质量阈值，无需迭代")

            return OptimizationResult(
                success=True,
                output=current_solution,
                final_score=normalized_initial,
                total_iterations=0,
                iterations=iterations,
                execution_time=time.time() - start_time
            )

        # 迭代优化
        best_solution = current_solution
        best_score = normalized_initial

        for i in range(1, self.max_iterations + 1):
            if verbose:
                print(f"\n{'='*50}")
                print(f"[迭代优化] 第 {i}/{self.max_iterations} 轮迭代")
                print(f"[迭代优化] 当前最佳评分：{best_score:.2f}")

            iter_start = time.time()

            # 生成改进建议
            if verbose:
                print(f"[迭代优化] 生成改进建议...")

            feedback = await self._generate_feedback(best_solution, problem)

            # 优化方案
            if verbose:
                print(f"[迭代优化] 优化方案...")

            optimized = await self._optimize_solution(
                best_solution,
                problem,
                feedback
            )

            # 评估优化后的方案
            if verbose:
                print(f"[迭代优化] 评估优化方案...")

            new_score = await self._evaluate_quality(optimized, problem)
            normalized_new = self._normalize_score(new_score)

            iter_duration = time.time() - iter_start

            if verbose:
                print(f"[迭代优化] 新评分：{new_score} (归一化：{normalized_new:.2f})")

            # 记录迭代结果
            improvement = self._extract_improvements(feedback)
            iterations.append(IterationResult(
                iteration=i,
                content=optimized,
                score=normalized_new,
                improvements=improvement,
                duration=iter_duration
            ))

            # 更新最佳方案
            if normalized_new > best_score:
                if verbose:
                    print(f"[迭代优化] 发现更优方案！提升：{normalized_new - best_score:.2f}")

                best_solution = optimized
                best_score = normalized_new

                # 检查是否达到阈值
                if best_score >= self.quality_threshold:
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

        return OptimizationResult(
            success=best_score >= self.quality_threshold,
            output=best_solution,
            final_score=best_score,
            total_iterations=len(iterations) - 1,  # 减去初始轮
            iterations=iterations,
            execution_time=execution_time
        )

    async def _generate_initial_solution(self, problem: str) -> str:
        """生成初始方案"""
        # 使用第一个 Agent 生成初始方案
        agent = self.agents[0]

        prompt = f"""针对以下问题，生成一个全面的解决方案：

问题：{problem}

要求：
1. 方案应该完整、可执行
2. 包含具体的步骤和方法
3. 考虑可能的边界情况
4. 提供清晰的结论

请生成详细的解决方案。
"""

        return await self._run_agent(agent, prompt)

    async def _evaluate_quality(self, content: str, problem: str) -> float:
        """评估方案质量"""
        # 优先使用独立评估器
        if self.evaluator:
            return await self._evaluate_with_evaluator(content, problem)

        # 使用质量检查器
        if self.quality_checker:
            report = self.quality_checker.check(content)
            return report.pass_rate

        # 使用 Agent 评估
        return await self._evaluate_with_agent(content, problem)

    async def _evaluate_with_evaluator(self, content: str, problem: str) -> float:
        """使用独立评估器进行评估"""
        prompt = f"""评估以下方案的质量：

问题：{problem}

方案：
{content}

请严格按照以下 JSON 格式返回评估结果：
{{
    "scores": {{
        "accuracy": 4,
        "completeness": 3,
        "practicality": 4,
        "clarity": 5,
        "depth": 3
    }},
    "total_score": 3.8,
    "feedback": "评估意见"
}}
"""

        try:
            result = await self._run_agent(self.evaluator, prompt)
            # 尝试解析 JSON
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return float(data.get("total_score", 3.0))
        except Exception:
            pass

        # 降级处理
        return await self._evaluate_with_agent(content, problem)

    async def _evaluate_with_agent(self, content: str, problem: str) -> float:
        """使用 Agent 进行评估"""
        # 使用另一个 Agent 进行评估
        evaluator = self.agents[1] if len(self.agents) > 1 else self.agents[0]

        prompt = f"""评估以下方案的质量（1-5 分）：

问题：{problem}

方案：
{content}

评分标准：
- 5 分：优秀，超出预期
- 4 分：良好，满足要求
- 3 分：合格，基本完成
- 2 分：较差，需要改进
- 1 分：不合格，需要重做

只返回一个数字，如：4.2
"""

        try:
            result = await self._run_agent(evaluator, prompt)
            import re
            numbers = re.findall(r'\d+\.?\d*', str(result))
            if numbers:
                return float(numbers[0])
        except Exception:
            pass

        return 3.0  # 默认分数

    def _normalize_score(self, score: float) -> float:
        """将分数归一化到 0-1 范围"""
        if self.score_type == "raw":
            # 原始分数 1-5，归一化到 0-1
            return (score - 1) / 4
        else:
            # 假设已经是 0-1 范围
            return min(1.0, max(0.0, score))

    async def _generate_feedback(self, content: str, problem: str) -> str:
        """生成改进建议"""
        agent = self.agents[1] if len(self.agents) > 1 else self.agents[0]

        prompt = f"""分析以下方案，提供具体的改进建议：

问题：{problem}

方案：
{content}

请指出：
1. 方案的优点
2. 存在的问题或不足
3. 具体的改进建议（至少 3 条）
4. 如果需要，提供示例或参考

请以清晰的格式返回改进建议。
"""

        return await self._run_agent(agent, prompt)

    def _extract_improvements(self, feedback: str) -> List[str]:
        """从反馈中提取改进建议"""
        improvements = []

        # 简单提取以数字开头的行
        lines = feedback.split("\n")
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                # 清理格式
                clean_line = line.lstrip("0123456789.、-•")
                if clean_line and len(clean_line) > 5:
                    improvements.append(clean_line.strip())

        return improvements[:5]  # 最多 5 条

    async def _optimize_solution(
        self,
        current: str,
        problem: str,
        feedback: str
    ) -> str:
        """基于反馈优化方案"""
        agent = self.agents[0]

        prompt = f"""根据以下反馈，优化现有方案：

问题：{problem}

当前方案：
{current}

改进建议：
{feedback}

请：
1. 保留当前方案的优点
2. 针对每个改进建议进行优化
3. 提供优化后的完整方案
4. 说明做了哪些改进

返回优化后的完整方案。
"""

        return await self._run_agent(agent, prompt)

    async def _run_agent(self, agent: Any, prompt: str) -> str:
        """运行 Agent"""
        if asyncio.iscoroutinefunction(agent.run):
            result = await agent.run(prompt, verbose=False)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: agent.run(prompt, verbose=False))
        return result


def create_optimizer(
    agents: List[Any],
    **kwargs
) -> IterativeOptimizer:
    """工厂函数：创建迭代优化器"""
    return IterativeOptimizer(agents=agents, **kwargs)
