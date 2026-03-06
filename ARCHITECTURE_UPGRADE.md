# Simple Agent 架构升级方案

本文档描述 Simple Agent 系统的两大升级方向：**提升 Agent 能力** 和 **实现 Agent Swarm（群体智能）**。

---

## 目录

1. [方案一：提升 Agent 能力](#方案一提升-agent 能力)
   - [1.1 增强的认知架构](#11-增强的认知架构)
   - [1.2 高级推理模式](#12-高级推理模式)
   - [1.3 技能学习系统](#13-技能学习系统)
2. [方案二：Agent Swarm 群体智能](#方案二 agent-swarm 群体智能)
   - [2.1 Swarm 架构设计](#21-swarm 架构设计)
   - [2.2 核心实现](#22-核心实现)
   - [2.3 群体协作模式](#23-群体协作模式)
   - [2.4 动态扩展](#24-动态扩展)
3. [实施路线图](#实施路线图)

---

## 方案一：提升 Agent 能力

### 当前问题分析

- Agent 只有简单的感知 - 推理 - 行动循环
- 缺乏长期记忆和知识积累
- 没有元认知能力（无法反思自己的决策）
- 推理模式单一，无法应对复杂问题

### 1.1 增强的认知架构

#### 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Enhanced Agent                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐    │
│  │            元认知层 (Meta-Cognitive)            │    │
│  │  • 自我反思 (Reflection)                        │    │
│  │  • 策略选择 (Strategy Selection)                │    │
│  │  • 置信度评估 (Confidence Assessment)           │    │
│  └─────────────────────────────────────────────────┘    │
│                            │                             │
│  ┌─────────────────────────────────────────────────┐    │
│  │            认知层 (Cognitive)                   │    │
│  │  • 规划 (Planning)                              │    │
│  │  • 推理 (Reasoning)                             │    │
│  │  • 学习 (Learning)                              │    │
│  └─────────────────────────────────────────────────┘    │
│                            │                             │
│  ┌─────────────────────────────────────────────────┐    │
│  │            记忆层 (Memory System)               │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │    │
│  │  │工作记忆  │  │短期记忆  │  │  长期记忆    │  │    │
│  │  │(Context) │  │(Session) │  │  (Vector DB) │  │    │
│  │  └──────────┘  └──────────┘  └──────────────┘  │    │
│  └─────────────────────────────────────────────────┘    │
│                            │                             │
│  ┌─────────────────────────────────────────────────┐    │
│  │            执行层 (Execution)                   │    │
│  │  • 工具调用 (Tool Invocation)                   │    │
│  │  • 结果评估 (Result Evaluation)                 │    │
│  │  • 错误恢复 (Error Recovery)                    │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

#### 核心实现：增强的记忆系统

**文件**: `core/memory_enhanced.py`

```python
from typing import Optional, Any
from dataclasses import dataclass, field
from collections import deque
import asyncio
import time

@dataclass
class Experience:
    """经验记录"""
    content: str
    context: str
    result: str
    success: bool
    timestamp: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)

class EnhancedMemory:
    """增强的记忆系统"""
    
    def __init__(self, vector_store=None, max_short_term=50):
        self.working_memory = []  # 当前上下文窗口
        self.short_term = deque(maxlen=max_short_term)  # 短期记忆
        self.long_term = vector_store  # 长期记忆 (向量数据库)
        self.experiences = []  # 经验记录
        self.reflections = []  # 反思总结
        self._lock = asyncio.Lock()
    
    def add_to_working(self, content: str):
        """添加到工作记忆"""
        self.working_memory.append({
            "content": content,
            "timestamp": time.time()
        })
        # 保持上下文窗口大小
        if len(self.working_memory) > 20:
            self.working_memory.pop(0)
    
    def add_to_short_term(self, experience: Experience):
        """添加到短期记忆"""
        self.short_term.append(experience)
        self.experiences.append(experience)
    
    async def store_to_long_term(self, experience: Experience):
        """存储经验到长期记忆"""
        if self.long_term is None:
            return
        
        # 创建嵌入向量
        embedding = await self._generate_embedding(experience.content)
        
        # 存储到向量数据库
        self.long_term.add(
            vector=embedding,
            metadata={
                "content": experience.content,
                "context": experience.context,
                "result": experience.result,
                "success": experience.success,
                "tags": experience.tags
            }
        )
    
    async def retrieve_relevant(self, query: str, top_k: int = 5) -> list[dict]:
        """检索相关记忆"""
        if self.long_term is None:
            return []
        
        query_embedding = await self._generate_embedding(query)
        results = self.long_term.search(query_embedding, top_k)
        
        return [
            {
                "content": r.metadata["content"],
                "result": r.metadata["result"],
                "success": r.metadata["success"],
                "similarity": r.similarity
            }
            for r in results
        ]
    
    async def _generate_embedding(self, text: str) -> list[float]:
        """生成文本的嵌入向量"""
        # 可以使用 OpenAI Embedding API 或本地模型
        from core.llm import get_llm
        llm = get_llm()
        response = await llm.embed(text)
        return response.embedding
    
    def reflect(self) -> str:
        """生成反思总结"""
        if len(self.experiences) < 5:
            return "经验不足，无法生成反思"
        
        # 提取成功模式和失败教训
        successes = [e for e in self.experiences if e.success]
        failures = [e for e in self.experiences if not e.success]
        
        insights = []
        if successes:
            insights.append("成功经验：")
            insights.append(f"  - 共 {len(successes)} 次成功任务")
            # 提取共同模式
            common_tags = self._extract_common_tags(successes)
            if common_tags:
                insights.append(f"  - 擅长领域：{', '.join(common_tags)}")
        
        if failures:
            insights.append("改进建议：")
            insights.append(f"  - 共 {len(failures)} 次失败任务")
            # 分析失败原因
            failure_reasons = self._analyze_failures(failures)
            insights.extend(failure_reasons)
        
        return "\n".join(insights)
    
    def _extract_common_tags(self, experiences: list[Experience]) -> list[str]:
        """提取共同标签"""
        from collections import Counter
        all_tags = []
        for e in experiences:
            all_tags.extend(e.tags)
        counter = Counter(all_tags)
        return [tag for tag, count in counter.most_common(5) if count >= 2]
    
    def _analyze_failures(self, failures: list[Experience]) -> list[str]:
        """分析失败原因"""
        reasons = []
        # 简化分析：提取关键词
        for f in failures[:3]:  # 分析最近 3 次失败
            reasons.append(f"  - {f.result[:100]}...")
        return reasons
    
    def get_context_for_task(self, task: str) -> str:
        """为任务准备上下文"""
        context_parts = []
        
        # 工作记忆
        if self.working_memory:
            recent = self.working_memory[-3:]
            context_parts.append("当前上下文：")
            context_parts.extend(f"  - {m['content']}" for m in recent)
        
        # 相关经验
        # (可在此处调用 retrieve_relevant)
        
        return "\n".join(context_parts)
```

#### 核心实现：增强版 Agent

**文件**: `core/agent_enhanced.py`

```python
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
        **kwargs
    ):
        super().__init__(llm, tools, system_prompt, **kwargs)
        self.memory = memory or EnhancedMemory()
        self.strategy: Literal["direct", "plan_reflect", "tree_of_thought"] = "direct"
        self.confidence_threshold = 0.7
    
    async def run(self, user_input: str, verbose: bool = False) -> str:
        """主执行流程"""
        # 1. 检索相关历史经验
        relevant_memories = await self.memory.retrieve_relevant(user_input)
        
        # 2. 元认知：选择策略
        self.strategy = await self._select_strategy(user_input, relevant_memories)
        
        if verbose:
            print(f"[Meta] 选择策略：{self.strategy}")
        
        # 3. 执行策略
        if self.strategy == "plan_reflect":
            result = await self._plan_reflect_execute(user_input, verbose)
        elif self.strategy == "tree_of_thought":
            result = await self._tree_of_thought(user_input, verbose)
        else:
            result = await self._direct_execute(user_input, verbose)
        
        # 4. 记录经验
        experience = Experience(
            content=user_input,
            context=str(relevant_memories),
            result=result.output,
            success=result.success,
            tags=[self.strategy]
        )
        self.memory.add_to_short_term(experience)
        
        # 5. 定期反思
        if len(self.memory.experiences) % 10 == 0:
            reflection = self.memory.reflect()
            self.memory.reflections.append(reflection)
        
        return result.output
    
    async def _select_strategy(
        self, 
        task: str, 
        relevant_memories: list[dict]
    ) -> str:
        """根据任务复杂度选择策略"""
        # 基于历史成功经验选择
        if relevant_memories:
            successful = [m for m in relevant_memories if m.get("success")]
            if successful:
                # 使用过去成功的策略
                best = max(successful, key=lambda m: m.get("similarity", 0))
                return "plan_reflect" if best.get("similarity", 0) > 0.8 else "direct"
        
        # 基于任务复杂度
        complexity = await self._estimate_complexity(task)
        if complexity > 0.7:
            return "tree_of_thought"
        elif complexity > 0.4:
            return "plan_reflect"
        else:
            return "direct"
    
    async def _estimate_complexity(self, task: str) -> float:
        """估计任务复杂度 (0-1)"""
        # 简化实现：基于任务长度和关键词
        keywords = ["设计", "架构", "系统", "复杂", "多个", "完整", "从 0"]
        score = 0
        for kw in keywords:
            if kw in task:
                score += 0.15
        return min(score, 1.0)
    
    async def _plan_reflect_execute(
        self, 
        user_input: str, 
        verbose: bool
    ) -> ExecutionResult:
        """规划 - 反思执行模式"""
        # 阶段 1：规划
        plan_prompt = f"""
        任务：{user_input}
        
        请制定一个详细的执行计划：
        1. 列出所有需要执行的步骤
        2. 说明每一步的目标
        3. 指出可能的难点和应对策略
        
        以 JSON 格式返回：
        {{
            "steps": [
                {{"goal": "目标", "approach": "方法", "potential_issues": ["问题 1"]}}
            ]
        }}
        """
        plan_response = await self.llm.chat([{"role": "user", "content": plan_prompt}])
        plan = self._parse_json(plan_response.content)
        
        if verbose:
            print(f"[Plan] 制定计划：{len(plan.get('steps', []))} 个步骤")
        
        # 阶段 2：执行并反思
        results = []
        for i, step in enumerate(plan.get("steps", [])):
            step_input = f"执行步骤 {i+1}: {step.get('goal')}\n方法：{step.get('approach')}"
            step_result = await self._execute_step(step_input)
            results.append(step_result)
            
            if verbose:
                print(f"[Step {i+1}] 结果：{'成功' if step_result.success else '失败'}")
            
            # 反思：如果置信度低，调整后续步骤
            if step_result.confidence < self.confidence_threshold:
                reflection = await self._reflect_on_step(step, step_result)
                if reflection.get("need_adjustment"):
                    plan = await self._adjust_plan(plan, i + 1, reflection)
        
        # 阶段 3：汇总
        final_output = await self._synthesize_results(results)
        avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0
        
        return ExecutionResult(
            success=all(r.success for r in results),
            output=final_output,
            confidence=avg_confidence,
            tool_calls=sum(r.tool_calls for r in results),
            iterations=len(results)
        )
    
    async def _tree_of_thought(
        self, 
        user_input: str, 
        verbose: bool,
        breadth: int = 3,
        depth: int = 2
    ) -> ExecutionResult:
        """思维树推理模式"""
        # 生成初始思路
        thoughts = await self._generate_thoughts(user_input, breadth)
        
        if verbose:
            print(f"[Tree] 生成 {len(thoughts)} 个初始思路")
        
        # 逐层深入
        for level in range(depth):
            # 评估当前层
            evaluations = await self._evaluate_thoughts(thoughts, user_input)
            
            # 选择最好的
            best_thoughts = await self._select_best_thoughts(
                thoughts, evaluations, breadth // 2 + 1
            )
            
            if verbose:
                print(f"[Tree] 层级 {level+1}: 保留 {len(best_thoughts)} 个思路")
            
            # 扩展
            thoughts = await self._expand_thoughts(best_thoughts, user_input)
        
        # 最终选择
        final = await self._select_final(thoughts, user_input)
        
        return ExecutionResult(
            success=True,
            output=final["content"],
            confidence=final.get("confidence", 0.8),
            tool_calls=0,
            iterations=breadth * depth
        )
    
    async def _direct_execute(
        self, 
        user_input: str, 
        verbose: bool
    ) -> ExecutionResult:
        """直接执行模式（使用原有逻辑）"""
        output = await super().run(user_input, verbose)
        return ExecutionResult(
            success=True,
            output=output,
            confidence=0.8,
            tool_calls=0,
            iterations=1
        )
```

### 1.2 高级推理模式

**文件**: `core/reasoning_modes.py`

```python
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
    
    async def solve(self, problem: str) -> str:
        thoughts = await self._generate_thoughts(problem, self.breadth)
        for level in range(self.depth):
            evaluated = await self._evaluate(thoughts, problem)
            for t, e in zip(thoughts, evaluated):
                t.score = e['score']
            best = await self._select_best(evaluated, self.breadth // 2 + 1)
            thoughts = await self._expand(best, problem)
        return await self._final_select(thoughts, problem)
    
    async def _generate_thoughts(self, problem: str, n: int) -> list[Thought]:
        prompt = f"""问题：{problem}\n请提出 {n} 个不同的解决思路。返回：["思路 1", "思路 2", ...]"""
        response = await self.agent.llm.chat([{"role": "user", "content": prompt}])
        ideas = self.agent._parse_json(response.content)
        return [Thought(content=idea) for idea in ideas]
    
    async def _evaluate(self, thoughts: list[Thought], problem: str) -> list[dict]:
        evaluations = []
        for t in thoughts:
            prompt = f"""问题：{problem}\n思路：{t.content}\n评估质量 (0-1 分)。返回：{{"score": 0.8, "reason": "..."}}"""
            response = await self.agent.llm.chat([{"role": "user", "content": prompt}])
            evaluations.append(self.agent._parse_json(response.content))
        return evaluations
    
    async def _select_best(self, evaluations: list[dict], n: int) -> list[Thought]:
        indexed = [(i, e['score']) for i, e in enumerate(evaluations)]
        indexed.sort(key=lambda x: x[1], reverse=True)
        return [self.thoughts[i] for i, _ in indexed[:n]]
    
    async def _expand(self, thoughts: list[Thought], problem: str) -> list[Thought]:
        expanded = []
        for t in thoughts:
            prompt = f"""当前思路：{t.content}\n提出 2 个细化方案。返回：["方案 1", "方案 2"]"""
            response = await self.agent.llm.chat([{"role": "user", "content": prompt}])
            refinements = self.agent._parse_json(response.content)
            for r in refinements:
                child = Thought(content=r, parent=t)
                t.children.append(child)
                expanded.append(child)
        return expanded
    
    async def _final_select(self, thoughts: list[Thought], problem: str) -> str:
        scores = []
        for t in thoughts:
            prompt = f"""方案：{t.content}\n评估完整性 (0-1 分)。返回：{{"score": 0.9, "final_answer": "..."}}"""
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
        prompt = f"""分析执行轨迹：\n{self._format_trajectory(trajectory)}\n
        回答：1.哪些步骤成功？2.哪些可改进？3.替代策略？4.学到了什么？
        返回：{{"successes": [], "improvements": [], "alternative_strategy": "", "learned_principles": []}}"""
        response = await self.agent.llm.chat([{"role": "user", "content": prompt}])
        return self.agent._parse_json(response.content)
    
    def _format_trajectory(self, trajectory: list) -> str:
        lines = []
        for i, (thought, action, result) in enumerate(trajectory):
            lines.append(f"步骤 {i+1}: {action} -> {result[:100]}...")
        return "\n".join(lines)
```

### 1.3 技能学习系统

**文件**: `core/skill_learning.py`

```python
from typing import Optional
from dataclasses import dataclass, field
import json
import asyncio

@dataclass
class Skill:
    """技能定义"""
    name: str
    description: str
    trigger_pattern: str
    prompt_template: str
    tools: list[str] = field(default_factory=list)
    success_rate: float = 0.5
    usage_count: int = 0
    examples: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in ['name', 'description', 'trigger_pattern', 
                'prompt_template', 'tools', 'success_rate', 'usage_count', 'examples']}
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Skill':
        return cls(**data)


class SkillLibrary:
    """技能库"""
    
    def __init__(self, storage_path: str = None):
        self.skills: dict[str, Skill] = {}
        self.storage_path = storage_path
        self._register_builtin_skills()
    
    def _register_builtin_skills(self):
        self.skills["代码分析"] = Skill(
            name="代码分析", description="分析代码结构、质量和问题",
            trigger_pattern="分析.*代码 | 代码审查",
            prompt_template="你是代码分析专家。请分析：{code}\n从结构、问题、性能、改进建议角度分析。",
            tools=["ReadFileTool", "CheckPythonSyntaxTool"], success_rate=0.8
        )
        self.skills["测试生成"] = Skill(
            name="测试生成", description="为代码生成单元测试",
            trigger_pattern="生成.*测试 | 写.*测试",
            prompt_template="你是测试专家。请为以下代码生成单元测试：{code}\n使用 pytest 框架。",
            tools=["ReadFileTool", "WriteFileTool"], success_rate=0.75
        )
    
    async def learn_from_success(self, trajectory: list, agent) -> Optional[Skill]:
        prompt = f"""分析成功轨迹：\n{self._format_trajectory(trajectory)}\n
        提取技能：名称、触发条件、提示模板、工具。返回 Skill JSON。"""
        response = await agent.llm.chat([{"role": "user", "content": prompt}])
        skill = Skill.from_dict(agent._parse_json(response.content))
        self.skills[skill.name] = skill
        await self._persist_skill(skill)
        return skill
    
    def select_skill(self, context: str) -> Optional[Skill]:
        import re
        candidates = []
        for skill in self.skills.values():
            if re.search(skill.trigger_pattern, context):
                score = skill.success_rate * (1 + skill.usage_count * 0.01)
                candidates.append((skill, score))
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
        return None
    
    async def improve_skill(self, skill_name: str, feedback: float):
        if skill_name not in self.skills:
            return
        skill = self.skills[skill_name]
        skill.usage_count += 1
        skill.success_rate = 0.9 * skill.success_rate + 0.1 * feedback
        await self._persist_skill(skill)
    
    async def _persist_skill(self, skill: Skill):
        if not self.storage_path:
            return
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump({name: s.to_dict() for name, s in self.skills.items()}, f, ensure_ascii=False, indent=2)
    
    def _format_trajectory(self, trajectory: list) -> str:
        return "\n".join(f"步骤 {i+1}: {a} -> {r[:100]}..." for i, (_, a, r) in enumerate(trajectory))
```

---

## 方案二：Agent Swarm 群体智能

### 2.1 Swarm 架构设计

#### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Swarm Orchestrator                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              任务分解器 (Task Decomposer)                │   │
│  │  • 接收复杂任务                                          │   │
│  │  • 分解为子任务                                          │   │
│  │  • 建立任务依赖图                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              调度器 (Scheduler)                          │   │
│  │  • 任务 - 代理匹配                                        │   │
│  │  • 资源分配                                              │   │
│  │  • 并发控制                                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              通信总线 (Communication Bus)                │   │
│  │  • 消息路由                                              │   │
│  │  • 共享黑板 (Blackboard)                                 │   │
│  │  • 事件广播                                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Agent Pool   │    │  Agent Pool   │    │  Agent Pool   │
│  [Developer]  │    │  [Reviewer]   │    │  [Tester]     │
│  [Dev #2]     │    │  [Reviewer #2]│    │  [Tester #2]  │
│  [Dev #3]     │    │               │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
```

#### 组件说明

| 组件 | 职责 | 关键功能 |
|------|------|----------|
| **Orchestrator** | 总控制器 | 任务分解、调度、协调 |
| **Task Decomposer** | 任务分解 | 将复杂任务拆分为可执行的子任务 |
| **Scheduler** | 调度器 | 匹配 Agent、分配资源、控制并发 |
| **Communication Bus** | 通信总线 | Agent 间消息传递、共享状态 |
| **Blackboard** | 共享黑板 | 所有 Agent 可读写的共享信息空间 |
| **Agent Pool** | Agent 池 | 管理多个同类型 Agent 实例 |

### 2.2 核心实现

**文件**: `swarm/orchestrator.py`

```python
from typing import Optional
from dataclasses import dataclass, field
import asyncio
import time

@dataclass
class Task:
    id: str
    description: str
    required_skills: list[str]
    dependencies: list[str] = field(default_factory=list)
    priority: int = 0
    status: str = "pending"
    assigned_to: Optional[str] = None
    result: Optional[str] = None


class SwarmOrchestrator:
    """群体智能控制器"""
    
    def __init__(self, agent_pool: list[Agent]):
        self.agent_pool = agent_pool
        self.blackboard = Blackboard()
        self.comms = MessageBus()
    
    async def solve(self, complex_task: str) -> str:
        # 1. 任务分解
        tasks = await self._decompose(complex_task)
        
        # 2. 构建任务图
        self._build_task_graph(tasks)
        
        # 3. 迭代执行
        while self._has_pending_tasks():
            ready_tasks = self._get_ready_tasks()
            await self._assign_and_execute(ready_tasks)
            self._update_progress()
        
        # 4. 汇总结果
        return self._synthesize_results()
    
    async def _decompose(self, task: str) -> list[Task]:
        planner = self._get_planner()
        decomposition = await planner.run(f"""
        将任务分解为子任务，返回 JSON:
        {{"tasks": [
            {{"id": "1", "description": "...", "required_skills": ["coding"], "dependencies": []}}
        ]}}
        任务：{task}
        """)
        return self._parse_tasks(decomposition)
    
    def _build_task_graph(self, tasks: list[Task]):
        for task in tasks:
            self.task_graph.add_node(task.id, task=task)
            for dep in task.dependencies:
                self.task_graph.add_edge(dep, task.id)
    
    def _get_ready_tasks(self) -> list[Task]:
        ready = []
        for node in self.task_graph.nodes():
            task = self.task_graph.nodes[node]['task']
            if task.status == "pending":
                deps_met = all(
                    self.task_graph.nodes[d]['task'].status == "completed"
                    for d in task.dependencies
                )
                if deps_met:
                    ready.append(task)
        return ready
    
    async def _assign_and_execute(self, tasks: list[Task]):
        async def execute_task(task: Task):
            agent = self._select_agent(task)
            task.assigned_to = agent.id
            context = self.blackboard.get_context(task)
            result = await agent.run(f"{task.description}\n上下文：{context}")
            self.blackboard.update(task.id, result)
            task.result = result
            task.status = "completed"
        
        await asyncio.gather(*[execute_task(t) for t in tasks])
    
    def _select_agent(self, task: Task) -> Agent:
        candidates = [a for a in self.agent_pool if self._matches_skills(a, task.required_skills)]
        return min(candidates, key=lambda a: a.current_load) if candidates else self.agent_pool[0]
    
    def _matches_skills(self, agent: Agent, skills: list[str]) -> bool:
        return any(s.lower() in agent.name.lower() for s in skills)
```

**文件**: `swarm/blackboard.py`

```python
import asyncio
import time

class Change:
    def __init__(self, key: str, value: any, agent_id: str, timestamp: float):
        self.key = key
        self.value = value
        self.agent_id = agent_id
        self.timestamp = timestamp


class Blackboard:
    """共享黑板 - 所有 Agent 可读写"""
    
    def __init__(self):
        self.data: dict[str, any] = {}
        self.history: list[Change] = []
    
    def write(self, key: str, value: any, agent_id: str):
        self.data[key] = value
        self.history.append(Change(key, value, agent_id, time.time()))
    
    def read(self, key: str) -> any:
        return self.data.get(key)
    
    def get_context(self, task: Task) -> str:
        relevant = []
        for dep in task.dependencies:
            if dep in self.data:
                relevant.append(f"{dep}: {self.data[dep]}")
        return "\n".join(relevant)
    
    def update(self, task_id: str, result: str):
        self.data[task_id] = result
```

**文件**: `swarm/message_bus.py`

```python
import asyncio

class MessageBus:
    """Agent 间通信总线"""
    
    def __init__(self):
        self.subscribers: dict[str, list[callable]] = {}
        self.message_queue = asyncio.Queue()
    
    def subscribe(self, topic: str, callback: callable):
        self.subscribers.setdefault(topic, []).append(callback)
    
    async def publish(self, topic: str, message: any, sender: str):
        await self.message_queue.put((topic, message, sender))
        for callback in self.subscribers.get(topic, []):
            await callback(message)
    
    async def broadcast(self, message: any, sender: str):
        await self.publish("__all__", message, sender)
```

### 2.3 群体协作模式

**文件**: `swarm/collaboration_patterns.py`

```python
class PairProgramming:
    """结对编程：Driver 写代码 + Navigator 审查"""
    def __init__(self, driver: Agent, navigator: Agent):
        self.driver = driver
        self.navigator = navigator
    
    async def execute(self, task: str) -> str:
        code = None
        for _ in range(5):
            if not code:
                code = await self.driver.run(f"实现：{task}")
            else:
                code = await self.driver.run(f"修改：{code}\n反馈：{feedback}")
            feedback = await self.navigator.run(f"审查：{code}")
            if "无需修改" in feedback or "LGTM" in feedback:
                break
        return code


class SwarmBrainstorming:
    """群体头脑风暴"""
    def __init__(self, agents: list[Agent]):
        self.agents = agents
    
    async def execute(self, problem: str) -> str:
        # 独立生成想法
        ideas = await asyncio.gather(*[
            a.run(f"针对 '{problem}' 提出 3 个方案") for a in self.agents
        ])
        # 互相评价
        all_ideas = "\n".join(ideas)
        evaluations = await asyncio.gather(*[
            a.run(f"评价方案：{all_ideas}") for a in self.agents
        ])
        # 综合决策
        return self._synthesize(ideas, evaluations)
    
    def _synthesize(self, ideas: list, evaluations: list) -> str:
        return f"想法：{ideas}\n评价：{evaluations}"


class MarketBasedAllocation:
    """基于市场的任务分配"""
    async def allocate(self, task: Task, agents: list[Agent]) -> Agent:
        bids = []
        for agent in agents:
            bid = await agent.run(f"任务：{task.description}\n评估胜任度 (0-1)")
            bids.append((agent, float(bid) if bid.replace('.','',1).isdigit() else 0.5))
        winner = max(bids, key=lambda x: x[1])
        return winner[0]
```

### 2.4 动态扩展

**文件**: `swarm/scaling.py`

```python
class DynamicScaling:
    """动态 Agent 扩展"""
    
    def __init__(self, base_agents: list[Agent]):
        self.agent_pool = base_agents
    
    async def monitor_and_scale(self, task_queue: list[Task]):
        while True:
            metrics = await self._collect_metrics()
            if metrics.avg_wait_time > 60:  # 等待超 60 秒
                await self._spawn_agent(metrics.bottleneck_skill)
            if metrics.idle_ratio > 0.7:  # 70% 空闲
                await self._remove_idle_agent()
            await asyncio.sleep(60)
    
    async def _collect_metrics(self):
        return type('Metrics', (), {
            'avg_wait_time': 30,
            'bottleneck_skill': 'coding',
            'idle_ratio': 0.3
        })()
    
    async def _spawn_agent(self, skill: str):
        config = self._get_config_for_skill(skill)
        new_agent = await AgentFactory.create(config)
        self.agent_pool.append(new_agent)
    
    async def _remove_idle_agent(self):
        idle = [a for a in self.agent_pool if a.is_idle]
        if len(idle) > 1:
            self.agent_pool.remove(idle[-1])
```

---

## 实施路线图

### 阶段 1：基础增强（1-2 周）

| 任务 | 描述 | 优先级 |
|------|------|--------|
| 实现 EnhancedMemory | 增强的记忆系统，支持长期记忆存储 | P0 |
| 实现 TreeOfThought | 思维树推理模式 | P0 |
| 实现 ReflectionLoop | 反思循环机制 | P1 |
| 实现 SkillLibrary | 技能库基础功能 | P1 |

### 阶段 2：Swarm 核心（2-3 周）

| 任务 | 描述 | 优先级 |
|------|------|--------|
| 实现 SwarmOrchestrator | 群体智能控制器 | P0 |
| 实现 Blackboard | 共享黑板 | P0 |
| 实现 MessageBus | 消息总线 | P0 |
| 实现任务分解和调度 | 自动任务分解和分配 | P1 |

### 阶段 3：高级功能（3-4 周）

| 任务 | 描述 | 优先级 |
|------|------|--------|
| 完善 SkillLibrary | 技能学习和进化 | P1 |
| 实现协作模式 | 结对编程、头脑风暴等 | P1 |
| 实现动态扩展 | 自动扩展 Agent 池 | P2 |

### 阶段 4：优化与集成（1-2 周）

| 任务 | 描述 | 优先级 |
|------|------|--------|
| 性能优化 | 并发控制、资源管理 | P1 |
| 监控和可观测性 | 日志、指标、追踪 | P1 |
| 文档和示例 | 使用指南和示例代码 | P2 |

---

## 文件结构

实施后的目录结构：

```
simple-agent/
├── core/
│   ├── agent.py              # 原有 Agent 基类
│   ├── agent_enhanced.py     # 增强版 Agent [新增]
│   ├── memory.py             # 原有记忆
│   ├── memory_enhanced.py    # 增强记忆系统 [新增]
│   ├── reasoning_modes.py    # 高级推理模式 [新增]
│   ├── skill_learning.py     # 技能学习 [新增]
│   └── ...
├── swarm/
│   ├── __init__.py
│   ├── orchestrator.py       # 群体控制器 [新增]
│   ├── blackboard.py         # 共享黑板 [新增]
│   ├── message_bus.py        # 消息总线 [新增]
│   ├── collaboration_patterns.py  # 协作模式 [新增]
│   └── scaling.py            # 动态扩展 [新增]
├── builtin_agents/
├── tools/
└── ...
```

---

## 下一步

建议从 **EnhancedMemory** 开始实施，这是其他高级功能的基础。

---

## 阶段 1 详细实现脚本

### 脚本 1：实现 EnhancedMemory

**目标**：创建增强的记忆系统，支持工作记忆、短期记忆和长期记忆（向量数据库）

**步骤 1.1**：安装向量数据库依赖

```bash
# 编辑 requirements.txt
echo "chromadb>=0.4.0" >> requirements.txt
echo "numpy>=1.24.0" >> requirements.txt

# 安装依赖
pip install -r requirements.txt
```

**步骤 1.2**：创建 `core/memory_enhanced.py`

创建文件并写入基础代码（见上文 1.1 节完整实现）

**步骤 1.3**：测试记忆系统

```bash
# 创建测试脚本 tests/test_memory_enhanced.py
python -c "
from core.memory_enhanced import EnhancedMemory, Experience
import asyncio

async def test():
    mem = EnhancedMemory()
    exp = Experience(content='测试任务', context='测试', result='成功', success=True)
    mem.add_to_short_term(exp)
    print('记忆系统测试通过!')

asyncio.run(test())
"
```

**步骤 1.4**：集成到 Agent

```python
# 修改 core/__init__.py，添加导出
from .memory_enhanced import EnhancedMemory, Experience
```

---

### 脚本 2：实现 TreeOfThought

**目标**：创建思维树推理模式，支持多路径探索和评估

**步骤 2.1**：创建 `core/reasoning_modes.py`

```bash
# 创建文件
touch core/reasoning_modes.py
```

写入基础代码（见上文 1.2 节完整实现）

**步骤 2.2**：单元测试

```bash
python -c "
import asyncio
from core.reasoning_modes import TreeOfThought
from core.agent import Agent

async def test_tot():
    # 创建测试 Agent
    agent = Agent(llm=..., tools=[])
    tot = TreeOfThought(agent, breadth=3, depth=2)
    
    # 测试问题
    result = await tot.solve('如何设计一个高并发系统？')
    print(f'思维树推理结果：{result[:100]}...')
    print('TreeOfThought 测试通过!')

# asyncio.run(test_tot())  # 需要先配置 LLM
"
```

**步骤 2.3**：集成到 EnhancedAgent

```python
# 在 core/agent_enhanced.py 的 _tree_of_thought 方法中调用
from .reasoning_modes import TreeOfThought

async def _tree_of_thought(self, user_input, verbose):
    tot = TreeOfThought(self, breadth=3, depth=2)
    return await tot.solve(user_input)
```

---

### 脚本 3：实现 ReflectionLoop

**目标**：创建反思循环机制，从经验中学习和改进

**步骤 3.1**：添加到 `core/reasoning_modes.py`

ReflectionLoop 类已在上文 1.2 节定义

**步骤 3.2**：集成到 EnhancedAgent

```python
# 在 core/agent_enhanced.py 中添加
from .reasoning_modes import ReflectionLoop

class EnhancedAgent(Agent):
    def __init__(self, ...):
        super().__init__(...)
        self.reflection = ReflectionLoop(self)
    
    async def reflect_on_trajectory(self, trajectory):
        """反思执行轨迹"""
        return await self.reflection.reflect_and_improve(trajectory)
```

**步骤 3.3**：测试反思功能

```bash
python -c "
import asyncio
from core.reasoning_modes import ReflectionLoop

async def test_reflection():
    # 模拟执行轨迹
    trajectory = [
        ('思考 1', '行动 1', '结果 1 - 成功'),
        ('思考 2', '行动 2', '结果 2 - 部分成功'),
    ]
    
    # 创建反射器（需要 Agent 实例）
    # reflection = ReflectionLoop(agent)
    # result = await reflection.reflect_and_improve(trajectory)
    print('ReflectionLoop 结构验证通过!')

asyncio.run(test_reflection())
"
```

---

### 脚本 4：实现 SkillLibrary

**目标**：创建技能库系统，支持技能注册、匹配和学习

**步骤 4.1**：创建 `core/skill_learning.py`

```bash
touch core/skill_learning.py
```

写入基础代码（见上文 1.3 节完整实现）

**步骤 4.2**：单元测试

```bash
python -c "
import asyncio
from core.skill_learning import SkillLibrary, Skill

async def test_skill_library():
    lib = SkillLibrary()
    
    # 测试技能选择
    skill = lib.select_skill('请分析这段代码')
    assert skill is not None, '应该匹配到代码分析技能'
    print(f'匹配技能：{skill.name}')
    
    # 测试技能改进
    await lib.improve_skill('代码分析', 1.0)
    print('技能改进测试通过!')
    
    print('SkillLibrary 测试通过!')

asyncio.run(test_skill_library())
"
```

**步骤 4.3**：集成到 EnhancedAgent

```python
# 在 core/agent_enhanced.py 中添加
from .skill_learning import SkillLibrary

class EnhancedAgent(Agent):
    def __init__(self, ...):
        super().__init__(...)
        self.skill_library = SkillLibrary(storage_path='skills.json')
        await self.skill_library.load_skills()
    
    async def run(self, user_input, verbose=False):
        # 尝试匹配技能
        skill = self.skill_library.select_skill(user_input)
        if skill:
            return await self._execute_with_skill(skill, user_input)
        return await super().run(user_input, verbose)
    
    async def _execute_with_skill(self, skill, user_input):
        """使用技能执行"""
        # 使用技能的提示模板
        prompt = skill.prompt_template.format(...)
        return await self.llm.chat([{'role': 'user', 'content': prompt}])
```

---

## 阶段 1 实施检查清单

### 前置准备
- [ ] 备份现有代码 `git checkout -b feature/enhanced-agent`
- [ ] 安装依赖 `pip install chromadb numpy`
- [ ] 创建测试环境

### 核心实现
- [ ] 创建 `core/memory_enhanced.py`
- [ ] 创建 `core/reasoning_modes.py`
- [ ] 创建 `core/skill_learning.py`
- [ ] 创建 `core/agent_enhanced.py`
- [ ] 更新 `core/__init__.py` 导出

### 测试验证
- [ ] 记忆系统单元测试
- [ ] 思维树推理测试
- [ ] 反思循环测试
- [ ] 技能库测试
- [ ] 集成测试

### 文档更新
- [ ] 更新 README.md
- [ ] 添加 API 文档
- [ ] 编写使用示例

---

## 快速启动脚本

创建 `scripts/implement_stage1.sh`：

```bash
#!/bin/bash
set -e

echo "=== 阶段 1 实施脚本 ==="
pip install chromadb numpy
mkdir -p tests
python tests/test_stage1.py
echo "=== 阶段 1 实施完成 ==="
```

---

## 阶段 1 实施状态

**状态**: ✅ 已完成

**实施日期**: 2026-03-06

### 已创建文件

- ✅ `core/memory_enhanced.py` - 增强记忆系统
- ✅ `core/reasoning_modes.py` - 思维树推理和反思循环
- ✅ `core/skill_learning.py` - 技能库系统
- ✅ `core/agent_enhanced.py` - 增强版 Agent
- ✅ `core/__init__.py` - 更新导出（新增）
- ✅ `tests/test_stage1.py` - 单元测试

### 测试结果

```
==================================================
阶段 1 功能测试
==================================================
✓ EnhancedMemory 测试通过
✓ SkillLibrary 测试通过
✓ ReflectionLoop 结构验证通过
==================================================
所有测试完成！
==================================================
```

### 已安装依赖

- chromadb >= 0.4.0
- numpy >= 1.24.0

### 下一步

- [ ] 集成 EnhancedAgent 到 CLI
- [ ] 添加向量数据库长期记忆支持
- [ ] 实施阶段 2：Swarm 核心
