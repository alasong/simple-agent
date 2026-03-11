"""
策略路由器 (Strategy Router)

统一决策系统：根据任务特征自动选择最优执行策略

架构:
┌─────────────────────────────────────────────────────────┐
│           StrategyRouter                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │  输入层：任务 + Agent 池                            │  │
│  │  - 任务描述                                         │  │
│  │  - Agent 池（用于专业能力分析）                      │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  分析层：评估任务特征                              │  │
│  │  - 任务复杂度                                       │  │
│  │  - 专业需求分析                                     │  │
│  │  - Agent 池匹配度                                   │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  决策层：选择最优策略                              │  │
│  │  - strategy: 策略名称                              │  │
│  │  - reason: 决策理由                                │  │
│  │  - suggested_agents: 建议的 Agent                  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘

策略映射:
┌------------------+-----------+-------------------+-------------┐
| 任务复杂度       | 专业需求 | Agent 池匹配      | 策略         |
├------------------+-----------+-------------------+-------------┤
| ≤ 0.4 (低)       | 单一      | 有                | direct      |
| ≤ 0.4 (低)       | 多        | 有                | swarm       |
| ≤ 0.4 (低)       | 多        | 无                | decompose   |
| 0.4 - 0.7 (中)   | 单一      | 有                | plan_reflect|
| 0.4 - 0.7 (中)   | 多        | 有                | swarm       |
| 0.4 - 0.7 (中)   | 多        | 无                | tree_of_thought|
| > 0.7 (高)       | 单一      | 有                | tree_of_thought|
| > 0.7 (高)       | 多        | 有 (完整)         | swarm       |
| > 0.7 (高)       | 多        | 无 (完整)         | decompose   |
└------------------+-----------+-------------------+-------------┘
"""

import asyncio
import re
from typing import Optional, Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter

from simple_agent.core.llm import OpenAILLM
from simple_agent.core.config_loader import get_config


class Strategy(Enum):
    """执行策略"""
    DIRECT = "direct"               # 直接执行 - 简单任务，单 Agent
    DECOMPOSE = "decompose"         # 自分解 - 单 Agent 内部思考和分解
    PLAN_REFLECT = "plan_reflect"   # 计划-反思 - 迭代优化
    TREE_OF_THOUGHT = "tree_of_thought"  # 思维树 - 多路径探索
    SWARM = "swarm"                 # Swarm 协作 - 多专业 Agent 协作
    SWARM_VOTING = "swarm_voting"   # Swarm 投票 - 重大决策
    MULTI_PATH = "multi_path"       # 多路径并行优化


@dataclass
class StrategyResult:
    """决策结果"""
    strategy: Strategy
    reason: str
    confidence: float = 0.0
    suggested_agents: List[str] = field(default_factory=list)
    complexity_estimate: float = 0.0
    professional_needs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "reason": self.reason,
            "confidence": self.confidence,
            "suggested_agents": self.suggested_agents,
            "complexity_estimate": self.complexity_estimate,
            "professional_needs": self.professional_needs
        }


class ProfessionalAnalyzer:
    """专业需求分析器 - 基于关键词的任务专业需求分析"""

    # 技能关键词映射（从配置文件加载）
    SKILL_KEYWORDS = {
        "coding": ["code", "develop", "program", "write", "实现", "开发", "编码", "编写", "函数", "类", "模块"],
        "testing": ["test", "qa", "verify", "validate", "测试", "验证", "单元测试", "集成测试", "bug", "缺陷"],
        "reviewing": ["review", "audit", "check", "inspect", "审查", "审核", "检查", "代码审查", "评审"],
        "analysis": ["analyz", "research", "investigat", "分析", "研究", "调查", "调研", "数据", "统计"],
        "planning": ["plan", "计划", "规划", "方案"],
        "writing": ["write", "document", "explain", "文档", "说明", "写作", "描述", "介绍"],
        "debugging": ["debug", "fix", "troubleshoot", "调试", "修复", "解决", "问题"],
        "architect": ["architect", "架构", "系统设计", "技术方案", "架构设计"],
        "documenter": ["document", "编写文档", "技术文档"],
        "deployer": ["deploy", "release", "运维", "部署", "发布", "ci/cd"],
    }

    @classmethod
    def extract_skills(cls, task: str) -> List[str]:
        """从任务描述中提取所需技能

        匹配逻辑：
        1. 优先匹配较长的关键词（避免短词误匹配）
        2. 去除重复匹配
        3. 限制最多返回 5 个技能，避免过度匹配
        """
        skills = []
        task_lower = task.lower()

        # 先按技能类别匹配
        skill_matches = {}
        for skill, keywords in cls.SKILL_KEYWORDS.items():
            match_count = 0
            for kw in keywords:
                if kw.lower() in task_lower:
                    match_count += 1
            if match_count > 0:
                skill_matches[skill] = match_count

        # 按匹配数量排序，优先返回匹配度高的技能
        sorted_skills = sorted(skill_matches.items(), key=lambda x: x[1], reverse=True)

        # 限制最多返回 5 个技能
        for skill, _ in sorted_skills[:5]:
            skills.append(skill)

        return list(set(skills))  # 去重


class ComplexityEstimator:
    """复杂度估计器"""

    # 复杂度关键词（从配置文件加载）
    COMPLEXITY_KEYWORDS = {
        "设计": 0.15,
        "架构": 0.15,
        "系统": 0.12,
        "复杂": 0.12,
        "多个": 0.10,
        "完整": 0.10,
        "从 0": 0.15,
        "项目": 0.10,
        "流程": 0.10,
        "方案": 0.10,
        "规划": 0.12,
        "全面": 0.10,
        "整个": 0.10,
        "多步": 0.15,
        "多条件": 0.15,
        "并行": 0.10,
        "协作": 0.12,
        "群体": 0.12,
    }

    @classmethod
    def estimate(cls, task: str) -> float:
        """估计任务复杂度"""
        score = 0.0

        for kw, weight in cls.COMPLEXITY_KEYWORDS.items():
            if kw in task:
                score += weight

        return min(score, 1.0)


class StrategyRouter:
    """
    策略路由器 - 统一决策系统

    根据任务特征自动选择最优执行策略：
    - 任务复杂度分析
    - 专业需求分析
    - Agent 池匹配度分析
    """

    def __init__(
        self,
        agent_pool: Optional[List[Any]] = None,
        llm: Optional[OpenAILLM] = None,
        complexity_thresholds: Dict[str, float] = None
    ):
        """
        初始化策略路由器

        Args:
            agent_pool: Agent 池，用于专业能力分析
            llm: LLM 实例，用于复杂判断
            complexity_thresholds: 复杂度阈值配置
                {
                    "low_max": 0.4,      # 低复杂度最大值
                    "medium_max": 0.7,   # 中复杂度最大值
                    "swarm_min": 0.7     # 使用 Swarm 的最小复杂度
                }
        """
        self.agent_pool = agent_pool or []
        self.llm = llm or OpenAILLM()
        self.complexity_thresholds = complexity_thresholds or {
            "low_max": 0.4,
            "medium_max": 0.7,
            "swarm_min": 0.7
        }

        # 分析器
        self.complexity_estimator = ComplexityEstimator()
        self.professional_analyzer = ProfessionalAnalyzer()

    def _get_agent_skills(self) -> Dict[str, List[str]]:
        """获取 Agent 池的技能分布"""
        agent_skills = {}
        for agent in self.agent_pool:
            agent_id = getattr(agent, 'instance_id', getattr(agent, 'name', str(agent)))
            skills = getattr(agent, 'skills', [])

            # 如果 Agent 没有 skills 属性，从 name 推断
            if not skills:
                skills = self.professional_analyzer.extract_skills(agent_id)

            agent_skills[agent_id] = skills

        return agent_skills

    def _check_agent_coverage(self, required_skills: List[str]) -> Dict[str, Any]:
        """
        检查 Agent 池对所需技能的覆盖情况

        Returns:
            {
                "covered": bool,              # 是否完全覆盖
                "uncovered": List[str],       # 未覆盖的技能
                "coverage_rate": float,       # 覆盖率
                "covered_agents": List[str]   # 可以覆盖技能的 Agent
            }
        """
        if not required_skills:
            return {
                "covered": True,
                "uncovered": [],
                "coverage_rate": 1.0,
                "covered_agents": [a.instance_id for a in self.agent_pool]
            }

        agent_skills = self._get_agent_skills()
        covered_agents = set()
        uncovered = []

        for skill in required_skills:
            skill_covered = False
            for agent_id, skills in agent_skills.items():
                # 检查技能是否被覆盖
                for agent_skill in skills:
                    if skill.lower() in agent_skill.lower() or agent_skill.lower() in skill.lower():
                        covered_agents.add(agent_id)
                        skill_covered = True
                        break

            if not skill_covered:
                uncovered.append(skill)

        coverage_rate = 1.0 - (len(uncovered) / len(required_skills)) if required_skills else 1.0

        return {
            "covered": len(uncovered) == 0,
            "uncovered": uncovered,
            "coverage_rate": coverage_rate,
            "covered_agents": list(covered_agents),
            "total_required": len(required_skills),
            "total_covered": len(covered_agents)
        }

    async def _llm_analyze_task(self, task: str) -> Dict[str, Any]:
        """使用 LLM 分析任务（用于复杂判断）"""
        prompt = f"""你是一个任务分析专家。请分析以下任务的特征：

任务：{task}

请分析：
1. 任务复杂度（0-1 分数）
2. 需要的技能类型（如 coding, testing, planning, etc.）
3. 是否需要多专业协作（是/否）
4. 任务类型（设计/开发/测试/规划/决策/-other）

请只输出 JSON 格式：
{{
    "complexity": 0.0-1.0,
    "required_skills": ["skill1", "skill2"],
    "needs_multiple_professionals": true/false,
    "task_type": "design|development|testing|planning|decision|other"
}}
"""

        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            content = response.get("content", "")

            # 提取 JSON
            import json
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())

            return {
                "complexity": 0.5,
                "required_skills": [],
                "needs_multiple_professionals": False,
                "task_type": "other"
            }
        except Exception:
            return {
                "complexity": 0.5,
                "required_skills": [],
                "needs_multiple_professionals": False,
                "task_type": "other"
            }

    def _determine_strategy(
        self,
        complexity: float,
        professional_needs: List[str],
        agent_coverage: Dict[str, Any]
    ) -> StrategyResult:
        """
        根据任务特征确定策略

        决策矩阵:
        - 复杂度 ≤ 0.4: 直接执行或简单分解
        - 复杂度 0.4-0.7: 计划-反思或 TreeOfThought
        - 复杂度 > 0.7: TreeOfThought 或 Swarm（需要多专业时）
        """
        # 获取阈值
        low_max = self.complexity_thresholds["low_max"]
        medium_max = self.complexity_thresholds["medium_max"]
        swarm_min = self.complexity_thresholds["swarm_min"]

        # 判断是否需要多专业
        needs_multiple = len(professional_needs) > 2
        coverage_rate = agent_coverage.get("coverage_rate", 0.0)

        # 决策逻辑
        if complexity <= low_max:
            # 低复杂度任务
            if needs_multiple and coverage_rate >= 0.8:
                # 需要多专业且 Agent 池覆盖好 -> Swarm
                strategy = Strategy.SWARM
                reason = f"低复杂度多专业任务，Agent 池覆盖良好 ({coverage_rate:.0%})"
            elif needs_multiple:
                # 需要多专业但 Agent 池 coverage 不足 -> Decompose
                strategy = Strategy.DECOMPOSE
                reason = f"低复杂度多专业任务，但 Agent 池 coverage 不足 ({coverage_rate:.0%})，使用自分解"
            else:
                # 单专业低复杂度 -> Direct
                strategy = Strategy.DIRECT
                reason = "低复杂度单专业任务，直接执行"

        elif complexity <= medium_max:
            # 中等复杂度任务
            if needs_multiple and coverage_rate >= 0.8:
                # 中等复杂度多专业且 Agent 池好 -> Swarm
                strategy = Strategy.SWARM
                reason = f"中等复杂度多专业任务，Agent 池覆盖良好 ({coverage_rate:.0%})"
            elif needs_multiple:
                # 中等复杂度多专业但 coverage 不足 -> TreeOfThought
                strategy = Strategy.TREE_OF_THOUGHT
                reason = f"中等复杂度多专业任务，Agent 池 coverage 不足 ({coverage_rate:.0%})，使用思维树探索"
            else:
                # 单专业中复杂度 -> PlanReflect
                strategy = Strategy.PLAN_REFLECT
                reason = "中等复杂度单专业任务，使用计划-反思迭代"

        else:
            # 高复杂度任务
            if needs_multiple and coverage_rate >= 0.8:
                # 高复杂度多专业且 Agent 池完整 -> Swarm
                strategy = Strategy.SWARM
                reason = f"高复杂度多专业任务，Agent 池完整覆盖 ({coverage_rate:.0%})"
            elif needs_multiple:
                # 高复杂度多专业但 coverage 不足 -> Decompose
                strategy = Strategy.DECOMPOSE
                reason = f"高复杂度多专业任务，但 Agent 池 coverage 不足 ({coverage_rate:.0%})，使用自分解"
            else:
                # 高复杂度单专业 -> TreeOfThought
                strategy = Strategy.TREE_OF_THOUGHT
                reason = "高复杂度单专业任务，使用思维树多路径探索"

        # 确定建议的 Agent
        suggested_agents = agent_coverage.get("covered_agents", [])

        return StrategyResult(
            strategy=strategy,
            reason=reason,
            confidence=coverage_rate if needs_multiple else min(1.0, 0.7 + complexity * 0.3),
            suggested_agents=suggested_agents,
            complexity_estimate=complexity,
            professional_needs=professional_needs
        )

    async def route(self, task: str) -> StrategyResult:
        """
        路由任务到最优策略

        Args:
            task: 任务描述

        Returns:
            StrategyResult: 决策结果
        """
        # Step 1: 估计任务复杂度
        complexity = self.complexity_estimator.estimate(task)

        # Step 2: 分析专业需求
        professional_needs = self.professional_analyzer.extract_skills(task)

        # Step 3: 检查 Agent 池覆盖情况
        agent_coverage = self._check_agent_coverage(professional_needs)

        # Step 4: 使用 LLM 进行二次确认（可选）
        #如果专业需求复杂，使用 LLM 进一步分析
        if len(professional_needs) > 1 or complexity > 0.5:
            try:
                llm_analysis = await self._llm_analyze_task(task)
                # 修正复杂度估计
                if llm_analysis.get("complexity", 0) != 0:
                    complexity = (complexity + llm_analysis["complexity"]) / 2
                    professional_needs = llm_analysis.get("required_skills", professional_needs)
            except Exception:
                pass  # LLM 分析失败不影响主流程

        # Step 5: 确定策略
        result = self._determine_strategy(complexity, professional_needs, agent_coverage)

        return result

    def get_strategy_for_tool(self, result: StrategyResult) -> str:
        """
        将策略转换为工具名称

        Args:
            result: StrategyResult

        Returns:
            工具名称字符串
        """
        strategy_tool_map = {
            Strategy.DIRECT: "InvokeAgentTool",
            Strategy.DECOMPOSE: "TaskDecomposer",
            Strategy.PLAN_REFLECT: "IterativeOptimizerTool",
            Strategy.TREE_OF_THOUGHT: "TreeOfThoughtTool",
            Strategy.SWARM: "SwarmOrchestrator",
            Strategy.SWARM_VOTING: "SwarmVotingTool",
            Strategy.MULTI_PATH: "MultiPathOptimizerTool"
        }

        return strategy_tool_map.get(result.strategy, "InvokeAgentTool")

    def print_route_result(self, result: StrategyResult, prefix: str = ""):
        """打印路由结果（用于调试）"""
        print(f"{prefix}[策略路由] 任务复杂度: {result.complexity_estimate:.2f}")
        print(f"{prefix}[策略路由] 专业需求: {', '.join(result.professional_needs) or '无'}")
        print(f"{prefix}[策略路由] 建议策略: {result.strategy.value}")
        print(f"{prefix}[策略路由] 建议 Agent: {', '.join(result.suggested_agents) or '无'}")
        print(f"{prefix}[策略路由] 原因: {result.reason}")
        print(f"{prefix}[策略路由] 置信度: {result.confidence:.0%}")


# 便捷函数
def create_router(
    agent_pool: Optional[List[Any]] = None,
    llm: Optional[OpenAILLM] = None,
    complexity_thresholds: Optional[Dict[str, float]] = None
) -> StrategyRouter:
    """创建策略路由器

    Args:
        agent_pool: Agent 池
        llm: LLM 实例
        complexity_thresholds: 复杂度阈值配置

    Returns:
        StrategyRouter: 策略路由器实例
    """
    return StrategyRouter(
        agent_pool=agent_pool,
        llm=llm,
        complexity_thresholds=complexity_thresholds
    )
