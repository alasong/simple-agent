"""
依赖图管理器 (Dependency Graph Manager)

使用 networkx 管理任务依赖关系，支持:
- 构建任务 DAG（有向无环图）
- 拓扑排序确定执行顺序
- 关键路径分析
- 自动识别可并行任务簇

架构:
┌─────────────────────────────────────────────────────────┐
│              TaskGraph                                  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  - 使用 networkx.DiGraph 存储依赖关系            │  │
│  │  - 节点：任务/动作                               │  │
│  │  - 边：依赖关系                                  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
"""

import networkx as nx
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"       # 等待中
    READY = "ready"          # 可执行（依赖已满足）
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    BLOCKED = "blocked"      # 被阻塞


@dataclass
class TaskNode:
    """任务节点"""
    id: str
    name: str
    description: str
    agent_type: Optional[str] = None
    estimated_time: float = 1.0
    priority: int = 3
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'agent_type': self.agent_type,
            'estimated_time': self.estimated_time,
            'priority': self.priority,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'metadata': self.metadata
        }


class TaskGraph:
    """任务依赖图"""
    
    def __init__(self):
        """初始化任务图"""
        self.graph = nx.DiGraph()
        self._nodes: Dict[str, TaskNode] = {}
    
    def add_task(self, task_id: str, name: str, description: str,
                 dependencies: Optional[List[str]] = None,
                 agent_type: Optional[str] = None,
                 estimated_time: float = 1.0,
                 priority: int = 3,
                 metadata: Optional[Dict] = None) -> TaskNode:
        """
        添加任务节点
        
        Args:
            task_id: 任务 ID
            name: 任务名称
            description: 任务描述
            dependencies: 依赖的任务 ID 列表
            agent_type: 适合的 Agent 类型
            estimated_time: 预计耗时（小时）
            priority: 优先级（1-4，1 为最高）
            metadata: 额外元数据
        
        Returns:
            TaskNode: 创建的任务节点
        """
        # 创建节点
        node = TaskNode(
            id=task_id,
            name=name,
            description=description,
            agent_type=agent_type,
            estimated_time=estimated_time,
            priority=priority,
            metadata=metadata or {}
        )
        
        # 添加到图
        self.graph.add_node(task_id)
        self._nodes[task_id] = node
        
        # 添加依赖边
        if dependencies:
            for dep_id in dependencies:
                if dep_id in self._nodes:
                    self.graph.add_edge(dep_id, task_id)
                else:
                    # 依赖不存在，先添加一个空节点
                    self.graph.add_node(dep_id)
                    self.graph.add_edge(dep_id, task_id)
        
        return node
    
    def add_task_from_action(self, action: Any, goal_id: str = "", 
                            task_id: str = "") -> TaskNode:
        """
        从 Action 对象添加任务
        
        Args:
            action: Action 对象（来自 task_decomposer）
            goal_id: 所属目标 ID（可选）
            task_id: 所属任务 ID（可选）
        
        Returns:
            TaskNode: 创建的任务节点
        """
        metadata = {
            'goal_id': goal_id,
            'parent_task_id': task_id,
            'required_skills': getattr(action, 'required_skills', [])
        }
        
        return self.add_task(
            task_id=action.id,
            name=getattr(action, 'name', 'Unnamed Task'),
            description=getattr(action, 'description', ''),
            dependencies=getattr(action, 'dependencies', []),
            agent_type=getattr(action, 'agent_type', 'developer'),
            estimated_time=getattr(action, 'estimated_time', 1.0),
            priority=getattr(action, 'priority', 3) if hasattr(action.priority, 'value') else action.priority,
            metadata=metadata
        )
    
    def get_ready_tasks(self) -> List[TaskNode]:
        """
        获取所有可执行的任务（入度为 0 且状态为 PENDING）
        
        Returns:
            List[TaskNode]: 可执行的任务列表
        """
        ready_tasks = []
        for node_id, node in self._nodes.items():
            if node.status == TaskStatus.PENDING:
                # 检查入度（依赖是否都已完成）
                in_degree = self.graph.in_degree(node_id)
                if in_degree == 0:
                    node.status = TaskStatus.READY
                    ready_tasks.append(node)
                else:
                    # 检查所有依赖是否已完成
                    deps_completed = all(
                        self._nodes.get(dep_id, TaskNode("", "", "")).status == TaskStatus.COMPLETED
                        for dep_id in self.graph.predecessors(node_id)
                    )
                    if deps_completed:
                        node.status = TaskStatus.READY
                        ready_tasks.append(node)
        
        # 按优先级排序
        ready_tasks.sort(key=lambda x: x.priority)
        return ready_tasks
    
    def get_parallel_clusters(self) -> List[List[str]]:
        """
        获取可并行执行的任务簇（拓扑分层）
        
        Returns:
            List[List[str]]: 每层可并行执行的任务 ID 列表
        """
        try:
            # 使用拓扑分层
            layers = list(nx.topological_generations(self.graph))
            return layers
        except nx.NetworkXUnfeasible:
            # 存在环，无法拓扑排序
            # 返回所有节点作为单层
            return [list(self.graph.nodes())]
    
    def get_critical_path(self) -> List[str]:
        """
        获取关键路径（最长路径）
        
        Returns:
            List[str]: 关键路径上的任务 ID 列表
        """
        try:
            # 基于任务执行时间的加权最长路径
            # 这里简化为节点数最长的路径
            return nx.dag_longest_path(self.graph)
        except Exception:
            # 如果计算失败，返回空列表
            return []
    
    def get_critical_path_length(self) -> float:
        """
        获取关键路径长度（预计总耗时）
        
        Returns:
            float: 关键路径的总耗时
        """
        critical_path = self.get_critical_path()
        total_time = sum(
            self._nodes.get(node_id, TaskNode("", "", "")).estimated_time
            for node_id in critical_path
        )
        return total_time
    
    def remove_completed(self, task_id: str):
        """
        移除已完成的任务
        """
        if task_id in self._nodes:
            node = self._nodes[task_id]
            node.status = TaskStatus.COMPLETED
            self.graph.remove_node(task_id)
            del self._nodes[task_id]
    
    def mark_failed(self, task_id: str, error: str):
        """
        标记任务失败
        """
        if task_id in self._nodes:
            node = self._nodes[task_id]
            node.status = TaskStatus.FAILED
            node.error = error
    
    def set_result(self, task_id: str, result: Any):
        """
        设置任务执行结果
        """
        if task_id in self._nodes:
            node = self._nodes[task_id]
            node.result = result
    
    def get_task(self, task_id: str) -> Optional[TaskNode]:
        """
        获取任务节点
        """
        return self._nodes.get(task_id)
    
    def get_all_tasks(self) -> List[TaskNode]:
        """
        获取所有任务节点
        """
        return list(self._nodes.values())
    
    def get_pending_count(self) -> int:
        """
        获取待执行任务数
        """
        return sum(1 for node in self._nodes.values() 
                  if node.status in [TaskStatus.PENDING, TaskStatus.READY])
    
    def get_completed_count(self) -> int:
        """
        获取已完成任务数
        """
        return sum(1 for node in self._nodes.values() 
                  if node.status == TaskStatus.COMPLETED)
    
    def is_complete(self) -> bool:
        """
        检查是否所有任务都已完成
        """
        return self.get_pending_count() == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典表示
        """
        return {
            'nodes': [node.to_dict() for node in self._nodes.values()],
            'edges': list(self.graph.edges()),
            'stats': {
                'total': len(self._nodes),
                'pending': self.get_pending_count(),
                'completed': self.get_completed_count(),
                'critical_path_length': self.get_critical_path_length()
            }
        }
    
    @classmethod
    def from_decomposition_result(cls, result: Any) -> 'TaskGraph':
        """
        从分解结果创建任务图
        
        Args:
            result: DecompositionResult 对象
        
        Returns:
            TaskGraph: 任务图
        """
        graph = cls()
        
        # 添加所有动作
        for goal in getattr(result, 'goals', []):
            for task in getattr(goal, 'tasks', []):
                for action in getattr(task, 'actions', []):
                    graph.add_task_from_action(
                        action=action,
                        goal_id=getattr(goal, 'id', ''),
                        task_id=getattr(task, 'id', '')
                    )
        
        return graph


# 便捷函数
def create_task_graph() -> TaskGraph:
    """创建任务图"""
    return TaskGraph()

def build_graph_from_actions(actions: List[Any]) -> TaskGraph:
    """
    从动作列表构建任务图
    
    Args:
        actions: Action 对象列表
    
    Returns:
        TaskGraph: 构建好的任务图
    """
    graph = TaskGraph()
    
    for action in actions:
        graph.add_task_from_action(action)
    
    return graph
