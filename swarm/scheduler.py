"""
任务调度器（Task Scheduler）

负责任务分解、依赖管理和智能调度
"""

import asyncio
import time
from typing import Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import re


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """任务定义"""
    id: str
    description: str
    required_skills: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    priority: int = 0
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "required_skills": self.required_skills,
            "dependencies": self.dependencies,
            "priority": self.priority,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        if "status" in data and isinstance(data["status"], str):
            data["status"] = TaskStatus(data["status"])
        return cls(**data)
    
    def is_ready(self, completed_tasks: set[str]) -> bool:
        """检查任务是否准备执行（依赖已满足）"""
        if self.status != TaskStatus.PENDING:
            return False
        return all(dep in completed_tasks for dep in self.dependencies)
    
    def mark_running(self, agent_id: str):
        """标记为运行中"""
        self.status = TaskStatus.RUNNING
        self.assigned_to = agent_id
        self.started_at = time.time()
    
    def mark_completed(self, result: str):
        """标记为完成"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = time.time()
    
    def mark_failed(self, error: str):
        """标记为失败"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = time.time()
    
    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.retry_count < self.max_retries
    
    def reset_for_retry(self):
        """重置为可执行状态"""
        self.status = TaskStatus.PENDING
        self.assigned_to = None
        self.started_at = None
        self.retry_count += 1


class TaskDecomposer:
    """任务分解器"""
    
    def __init__(self, llm):
        self.llm = llm
    
    async def decompose(self, complex_task: str) -> list[Task]:
        """将复杂任务分解为子任务"""
        prompt = f"""将以下复杂任务分解为可独立执行的子任务。

任务：{complex_task}

要求：
1. 每个子任务应该是原子化的，可以独立执行
2. 明确任务间的依赖关系
3. 为每个任务指定所需的技能
4. 按执行顺序编号

返回 JSON 格式：
{{
    "tasks": [
        {{
            "id": "1",
            "description": "任务描述",
            "required_skills": ["coding", "analysis"],
            "dependencies": [],
            "priority": 1
        }},
        {{
            "id": "2", 
            "description": "任务描述",
            "required_skills": ["testing"],
            "dependencies": ["1"],
            "priority": 2
        }}
    ]
}}

技能类型包括：coding, testing, reviewing, analysis, research, writing, planning
"""
        
        response = await self.llm.chat([{"role": "user", "content": prompt}])
        content = response.get("content", "")
        
        # 解析 JSON
        try:
            # 尝试提取 JSON 内容
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                content = json_match.group()
            data = json.loads(content)
            tasks_data = data.get("tasks", [])
            
            tasks = []
            for t in tasks_data:
                task = Task(
                    id=str(t.get("id", "")),
                    description=t.get("description", ""),
                    required_skills=t.get("required_skills", []),
                    dependencies=t.get("dependencies", []),
                    priority=t.get("priority", 0)
                )
                tasks.append(task)
            
            return tasks
        except json.JSONDecodeError as e:
            # 解析失败时，返回单个任务
            return [Task(id="1", description=complex_task, required_skills=[])]


class TaskGraph:
    """任务依赖图"""
    
    def __init__(self):
        self.nodes: dict[str, Task] = {}
        self.edges: dict[str, list[str]] = {}  # task_id -> [dependent_task_ids]
    
    def add_task(self, task: Task):
        """添加任务"""
        self.nodes[task.id] = task
        self.edges[task.id] = []
    
    def build_from_tasks(self, tasks: list[Task]):
        """从任务列表构建图"""
        for task in tasks:
            self.add_task(task)
        
        # 构建反向依赖边
        for task in tasks:
            for dep in task.dependencies:
                if dep in self.edges:
                    self.edges[dep].append(task.id)
    
    def get_ready_tasks(self) -> list[Task]:
        """获取可执行的任务（依赖已满足）"""
        completed = {
            tid for tid, task in self.nodes.items() 
            if task.status == TaskStatus.COMPLETED
        }
        
        ready = []
        for task in self.nodes.values():
            if task.is_ready(completed):
                ready.append(task)
        
        # 按优先级排序
        ready.sort(key=lambda t: t.priority, reverse=True)
        return ready
    
    def has_pending_tasks(self) -> bool:
        """是否有待处理的任务"""
        return any(
            t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
            for t in self.nodes.values()
        )
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.nodes.get(task_id)
    
    def get_all_tasks(self) -> list[Task]:
        """获取所有任务"""
        return list(self.nodes.values())
    
    def get_execution_order(self) -> list[str]:
        """获取可能的执行顺序（拓扑排序）"""
        # 简化实现：按依赖数排序
        tasks = list(self.nodes.values())
        tasks.sort(key=lambda t: len(t.dependencies))
        return [t.id for t in tasks]


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, agent_pool: list[Any]):
        self.agent_pool = agent_pool
        self.agent_load: dict[str, int] = {a.instance_id: 0 for a in agent_pool}
        self._lock = asyncio.Lock()
    
    def select_agent(self, task: Task) -> Optional[Any]:
        """为任务选择合适的 Agent"""
        # 筛选满足技能要求的 Agent
        candidates = []
        for agent in self.agent_pool:
            if self._matches_skills(agent, task.required_skills):
                candidates.append(agent)
        
        if not candidates:
            # 没有匹配的，返回负载最低的
            candidates = self.agent_pool
        
        if not candidates:
            return None
        
        # 选择负载最低的
        candidates.sort(key=lambda a: self.agent_load.get(a.instance_id, 0))
        return candidates[0]
    
    def _matches_skills(self, agent: Any, required_skills: list[str]) -> bool:
        """检查 Agent 是否满足技能要求"""
        if not required_skills:
            return True
        
        # 简单的技能匹配：检查 Agent 名称或描述中是否包含技能关键词
        agent_name = getattr(agent, 'name', '').lower()
        agent_desc = getattr(agent, 'description', '').lower()
        agent_text = f"{agent_name} {agent_desc}"
        
        for skill in required_skills:
            if skill.lower() in agent_text:
                return True
        
        # 如果没有明确匹配，检查是否有通用的能力
        if 'coding' in required_skills and 'developer' in agent_name:
            return True
        if 'testing' in required_skills and 'tester' in agent_name:
            return True
        if 'reviewing' in required_skills and 'reviewer' in agent_name:
            return True
        
        return False
    
    async def assign_task(self, task: Task):
        """分配任务给 Agent"""
        async with self._lock:
            agent = self.select_agent(task)
            if agent:
                task.mark_running(agent.instance_id)
                self.agent_load[agent.instance_id] = \
                    self.agent_load.get(agent.instance_id, 0) + 1
            return agent
    
    def complete_task(self, task: Task):
        """任务完成，更新负载"""
        if task.assigned_to:
            self.agent_load[task.assigned_to] = max(
                0, self.agent_load.get(task.assigned_to, 0) - 1
            )
    
    def get_agent_stats(self) -> dict:
        """获取 Agent 负载统计"""
        return {
            "agents": len(self.agent_pool),
            "load_distribution": self.agent_load.copy(),
            "avg_load": sum(self.agent_load.values()) / max(1, len(self.agent_pool))
        }
