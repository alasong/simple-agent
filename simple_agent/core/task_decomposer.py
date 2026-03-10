"""
多级任务分解器 (Multi-Level Task Decomposer)

将复杂任务分解为多个层级:
- Level 1: 目标分解 (Goal) - 关键里程碑
- Level 2: 任务分解 (Task) - 具体任务
- Level 3: 动作分解 (Action) - 原子操作

架构:
┌─────────────────────────────────────────────────────────┐
│           MultiLevelTaskDecomposer                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Level 1: Goal Decomposition                      │  │
│  │  复杂任务 → 关键里程碑 (3-5 个)                    │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Level 2: Task Breakdown                          │  │
│  │  里程碑 → 具体任务 (每个里程碑 2-4 个任务)          │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Level 3: Action Planning                         │  │
│  │  任务 → 原子操作 (可分配给 Agent)                  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class PriorityLevel(Enum):
    """优先级等级"""
    CRITICAL = 1    # 关键路径
    HIGH = 2        # 高优先级
    MEDIUM = 3      # 中优先级
    LOW = 4         # 低优先级


@dataclass
class Action:
    """原子操作"""
    id: str
    name: str
    description: str
    agent_type: str           # 适合执行此操作的 Agent 类型
    required_skills: List[str]  # 所需技能
    estimated_time: float = 1.0  # 预计耗时（小时）
    priority: PriorityLevel = PriorityLevel.MEDIUM
    dependencies: List[str] = field(default_factory=list)  # 依赖的动作 ID
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'agent_type': self.agent_type,
            'required_skills': self.required_skills,
            'estimated_time': self.estimated_time,
            'priority': self.priority.value,
            'dependencies': self.dependencies
        }


@dataclass
class Task:
    """具体任务"""
    id: str
    name: str
    description: str
    goal_id: str              # 所属目标 ID
    actions: List[Action] = field(default_factory=list)
    estimated_time: float = 0.0
    priority: PriorityLevel = PriorityLevel.MEDIUM
    
    def __post_init__(self):
        if not self.estimated_time and self.actions:
            self.estimated_time = sum(a.estimated_time for a in self.actions)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'goal_id': self.goal_id,
            'actions': [a.to_dict() for a in self.actions],
            'estimated_time': self.estimated_time,
            'priority': self.priority.value
        }


@dataclass
class Goal:
    """关键目标/里程碑"""
    id: str
    name: str
    description: str
    tasks: List[Task] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)  # 成功标准
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'tasks': [t.to_dict() for t in self.tasks],
            'success_criteria': self.success_criteria
        }


@dataclass
class DecompositionResult:
    """分解结果"""
    original_task: str
    goals: List[Goal] = field(default_factory=list)
    total_actions: int = 0
    estimated_total_time: float = 0.0
    
    def __post_init__(self):
        self.total_actions = sum(
            len(a.actions) for g in self.goals for t in g.tasks
        )
        self.estimated_total_time = sum(
            t.estimated_time for g in self.goals for t in g.tasks
        )
    
    def get_all_actions(self) -> List[Action]:
        """获取所有原子操作"""
        actions = []
        for goal in self.goals:
            for task in goal.tasks:
                actions.extend(task.actions)
        return actions
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_task': self.original_task,
            'goals': [g.to_dict() for g in self.goals],
            'total_actions': self.total_actions,
            'estimated_total_time': self.estimated_total_time
        }


class MultiLevelTaskDecomposer:
    """多级任务分解器"""
    
    def __init__(self, llm):
        """
        初始化分解器
        
        Args:
            llm: LLM 实例，用于智能分解
        """
        self.llm = llm
        self.max_depth = 3  # 最多 3 层分解
    
    async def decompose(self, task: str, verbose: bool = True) -> DecompositionResult:
        """
        多级分解任务
        
        Args:
            task: 原始任务描述
            verbose: 是否打印详细过程
        
        Returns:
            DecompositionResult: 分解结果
        """
        if verbose:
            print(f"\n[任务分解] 开始分解任务：{task[:100]}...")
        
        # Level 1: 目标分解
        if verbose:
            print("[任务分解] Level 1: 分解为关键目标...")
        goals = await self._decompose_goals(task, verbose)
        
        # Level 2: 任务分解
        if verbose:
            print("[任务分解] Level 2: 分解目标为具体任务...")
        for goal in goals:
            tasks = await self._decompose_tasks(goal, task, verbose)
            goal.tasks = tasks
        
        # Level 3: 动作分解
        if verbose:
            print("[任务分解] Level 3: 分解任务为原子操作...")
        for goal in goals:
            for task_item in goal.tasks:
                actions = await self._decompose_actions(task_item, verbose)
                task_item.actions = actions
                # 计算任务耗时
                task_item.estimated_time = sum(a.estimated_time for a in actions)
        
        # 构建结果
        result = DecompositionResult(original_task=task, goals=goals)
        
        if verbose:
            print(f"\n[任务分解] 完成!")
            print(f"  - 目标数：{len(result.goals)}")
            print(f"  - 任务数：{sum(len(g.tasks) for g in result.goals)}")
            print(f"  - 原子操作数：{result.total_actions}")
            print(f"  - 预计总耗时：{result.estimated_total_time:.1f}小时")
        
        return result
    
    async def _decompose_goals(self, task: str, verbose: bool = True) -> List[Goal]:
        """
        Level 1: 将任务分解为关键目标（3-5 个里程碑）
        """
        prompt = f"""将以下任务分解为 3-5 个关键里程碑（目标）：

任务：{task}

每个里程碑应该是:
- 可衡量的具体成果
- 相对独立的模块
- 有明确的完成标准

请输出 JSON 格式（只输出 JSON，不要其他内容）:
{{
    "goals": [
        {{
            "id": "g1",
            "name": "目标 1 名称",
            "description": "目标 1 详细描述",
            "success_criteria": ["标准 1", "标准 2"]
        }},
        {{
            "id": "g2",
            "name": "目标 2 名称",
            "description": "目标 2 详细描述",
            "success_criteria": ["标准 1", "标准 2"]
        }}
    ]
}}
"""
        
        try:
            response = await self._llm_chat_json(prompt, verbose)
            goals_data = response.get('goals', [])
            
            goals = []
            for g in goals_data:
                goals.append(Goal(
                    id=g.get('id', f"g{len(goals)+1}"),
                    name=g.get('name', 'Unnamed Goal'),
                    description=g.get('description', ''),
                    success_criteria=g.get('success_criteria', [])
                ))
            
            # 如果没有分解出目标，创建一个默认目标
            if not goals:
                goals.append(Goal(
                    id="g1",
                    name="完成任务",
                    description=task,
                    success_criteria=["任务完成"]
                ))
            
            return goals
        
        except Exception as e:
            if verbose:
                print(f"[警告] 目标分解失败：{e}，使用默认分解")
            # 降级处理：创建单个目标
            return [Goal(
                id="g1",
                name="完成任务",
                description=task,
                success_criteria=["任务完成"]
            )]
    
    async def _decompose_tasks(self, goal: Goal, original_task: str, 
                               verbose: bool = True) -> List[Task]:
        """
        Level 2: 将目标分解为具体任务（每个目标 2-4 个任务）
        """
        prompt = f"""将以下目标分解为 2-4 个具体任务：

原始任务：{original_task}

目标：{goal.name}
目标描述：{goal.description}

每个任务应该是:
- 具体可执行的工作项
- 可以在合理时间内完成（1-4 小时）
- 有明确的输出

请输出 JSON 格式:
{{
    "tasks": [
        {{
            "id": "t1",
            "name": "任务 1 名称",
            "description": "任务 1 详细描述"
        }},
        {{
            "id": "t2",
            "name": "任务 2 名称",
            "description": "任务 2 详细描述"
        }}
    ]
}}
"""
        
        try:
            response = await self._llm_chat_json(prompt, verbose)
            tasks_data = response.get('tasks', [])
            
            tasks = []
            for t in tasks_data:
                tasks.append(Task(
                    id=t.get('id', f"t{len(tasks)+1}"),
                    name=t.get('name', 'Unnamed Task'),
                    description=t.get('description', ''),
                    goal_id=goal.id
                ))
            
            # 如果没有分解出任务，创建一个默认任务
            if not tasks:
                tasks.append(Task(
                    id="t1",
                    name=f"实现{goal.name}",
                    description=goal.description,
                    goal_id=goal.id
                ))
            
            return tasks
        
        except Exception as e:
            if verbose:
                print(f"[警告] 任务分解失败：{e}，使用默认分解")
            return [Task(
                id="t1",
                name=f"实现{goal.name}",
                description=goal.description,
                goal_id=goal.id
            )]
    
    async def _decompose_actions(self, task: Task, verbose: bool = True) -> List[Action]:
        """
        Level 3: 将任务分解为原子操作（可分配给 Agent 执行）
        """
        prompt = f"""将以下任务分解为原子操作（每个操作可由一个 Agent 独立执行）：

任务：{task.name}
任务描述：{task.description}

原子操作应该是:
- 可由单个 Agent 执行
- 有明确的输入输出
- 预计耗时在 1 小时内

可用的 Agent 类型：developer, reviewer, tester, architect, documenter, data_analyst

请输出 JSON 格式:
{{
    "actions": [
        {{
            "id": "a1",
            "name": "操作 1 名称",
            "description": "操作 1 描述",
            "agent_type": "developer",
            "required_skills": ["python", "file_operations"],
            "estimated_time": 0.5,
            "priority": 2,
            "dependencies": []
        }},
        {{
            "id": "a2",
            "name": "操作 2 名称",
            "description": "操作 2 描述",
            "agent_type": "reviewer",
            "required_skills": ["code_review"],
            "estimated_time": 0.3,
            "priority": 2,
            "dependencies": ["a1"]
        }}
    ]
}}
"""
        
        try:
            response = await self._llm_chat_json(prompt, verbose)
            actions_data = response.get('actions', [])
            
            actions = []
            for a in actions_data:
                priority_value = a.get('priority', 3)
                try:
                    priority = PriorityLevel(priority_value)
                except ValueError:
                    priority = PriorityLevel.MEDIUM
                
                actions.append(Action(
                    id=a.get('id', f"a{len(actions)+1}"),
                    name=a.get('name', 'Unnamed Action'),
                    description=a.get('description', ''),
                    agent_type=a.get('agent_type', 'developer'),
                    required_skills=a.get('required_skills', []),
                    estimated_time=float(a.get('estimated_time', 1.0)),
                    priority=priority,
                    dependencies=a.get('dependencies', [])
                ))
            
            # 如果没有分解出动作，创建一个默认动作
            if not actions:
                actions.append(Action(
                    id="a1",
                    name=f"执行 {task.name}",
                    description=task.description,
                    agent_type="developer",
                    required_skills=["general"],
                    estimated_time=1.0,
                    priority=PriorityLevel.MEDIUM
                ))
            
            return actions
        
        except Exception as e:
            if verbose:
                print(f"[警告] 动作分解失败：{e}，使用默认分解")
            return [Action(
                id="a1",
                name=f"执行 {task.name}",
                description=task.description,
                agent_type="developer",
                required_skills=["general"],
                estimated_time=1.0,
                priority=PriorityLevel.MEDIUM
            )]
    
    async def _llm_chat_json(self, prompt: str, verbose: bool = True) -> Dict[str, Any]:
        """
        调用 LLM 并解析 JSON 响应
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm.chat(messages)
            content = response.get("content", "")
            
            # 尝试提取 JSON（处理 LLM 可能添加的额外文本）
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
            else:
                # 尝试直接解析
                return json.loads(content)
        
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失败：{e}")
        except Exception as e:
            raise ValueError(f"LLM 调用失败：{e}")
    
    def decompose_sync(self, task: str, verbose: bool = True) -> DecompositionResult:
        """
        同步版本的 decompose 方法（用于不支持 async 的场景）
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 在已有循环中运行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = loop.run_in_executor(
                        executor,
                        lambda: asyncio.run(self.decompose(task, verbose))
                    )
                    return asyncio.run_coroutine_threadsafe(future, loop).result()
            else:
                return loop.run_until_complete(self.decompose(task, verbose))
        except RuntimeError:
            # 没有事件循环，创建新的
            return asyncio.run(self.decompose(task, verbose))


# 便捷函数
def create_decomposer(llm=None) -> MultiLevelTaskDecomposer:
    """创建任务分解器"""
    from simple_agent.core.llm import OpenAILLM
    return MultiLevelTaskDecomposer(llm or OpenAILLM())
