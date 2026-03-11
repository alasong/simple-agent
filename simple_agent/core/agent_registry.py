"""
Agent Registry - 统一的 Agent 注册中心

解决 Agent 脱管问题的核心方案：
1. 所有 Agent 必须注册后才能使用
2. 全局唯一的 Instance ID 管理
3. 生命周期追踪（创建、使用、销毁）
4. 自动检测和回收脱管 Agent

使用方式:
    # 1. 注册 Agent
    registry = get_agent_registry()
    registry.register(agent, source="scheduler")

    # 2. 获取已注册的 Agent
    agent = registry.get("agent-instance-id")

    # 3. 获取所有可用 Agent
    agents = registry.list_agents()

    # 4. 清理脱管 Agent
    registry.cleanup_orphans(timeout=3600)

    # 5. 在任务执行中跟踪
    with registry.track_execution(agent, task_id):
        result = agent.run(task)
"""

import threading
import time
import uuid
from typing import Optional, Dict, Any, List, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextlib import contextmanager
import weakref


class AgentStatus(Enum):
    """Agent 状态"""
    IDLE = "idle"               # 空闲
    RUNNING = "running"         # 执行中
    PAUSED = "paused"           # 已暂停
    ERROR = "error"             # 错误
    OFFLINE = "offline"         # 离线
    ORPHANED = "orphaned"       # 脱管


class AgentSource(Enum):
    """Agent 来源"""
    BUILTIN = "builtin"         # 内置 Agent
    CUSTOM = "custom"           # 自定义 Agent
    SCHEDULER = "scheduler"     # 调度器创建
    SWARM = "swarm"             # 群体智能创建
    CLI = "cli"                 # CLI 创建
    API = "api"                 # API 创建
    USER = "user"               # 用户创建


@dataclass
class AgentRecord:
    """Agent 记录"""
    instance_id: str
    agent: Any
    name: str
    source: AgentSource
    status: AgentStatus = AgentStatus.IDLE
    created_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)
    task_id: Optional[str] = None
    parent_id: Optional[str] = None  # 父 Agent ID（用于克隆追踪）
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "instance_id": self.instance_id,
            "name": self.name,
            "source": self.source.value,
            "status": self.status.value,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "last_active_at": datetime.fromtimestamp(self.last_active_at).isoformat(),
            "task_id": self.task_id,
            "parent_id": self.parent_id,
            "metadata": self.metadata
        }


@dataclass
class ExecutionRecord:
    """执行记录"""
    record_id: str
    instance_id: str
    task_id: str
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    status: str = "running"
    result: Optional[Any] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "instance_id": self.instance_id,
            "task_id": self.task_id,
            "started_at": datetime.fromtimestamp(self.started_at).isoformat(),
            "completed_at": datetime.fromtimestamp(self.completed_at).isoformat() if self.completed_at else None,
            "status": self.status,
            "result": str(self.result) if self.result else None,
            "error": self.error
        }


class AgentRegistry:
    """
    Agent 注册中心

    核心功能:
    1. 统一注册：所有 Agent 必须注册后才能使用
    2. 唯一 ID：保证 Instance ID 全局唯一
    3. 生命周期管理：追踪创建、使用、销毁
    4. 脱管检测：自动发现并回收脱管 Agent
    5. 克隆追踪：追踪 Agent 克隆链
    """

    def __init__(self):
        self._agents: Dict[str, AgentRecord] = {}
        self._executions: Dict[str, ExecutionRecord] = {}
        self._orphaned: Set[str] = set()
        self._clone_chains: Dict[str, List[str]] = {}  # parent_id -> [child_ids]

        # 线程锁
        self._lock = threading.RLock()

        # 回调
        self._on_register: List[Callable[[AgentRecord], None]] = []
        self._on_unregister: List[Callable[[str], None]] = []
        self._on_status_change: List[Callable[[str, AgentStatus], None]] = []
        self._on_orphan_detected: List[Callable[[str], None]] = []

        # 配置
        self._orphan_timeout = 3600  # 1 小时无活动视为脱管
        self._cleanup_interval = 300  # 5 分钟检查一次

        # 后台清理线程
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = True
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """启动后台清理线程"""
        def cleanup_loop():
            while self._running:
                self.cleanup_orphans()
                time.sleep(self._cleanup_interval)

        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def stop(self):
        """停止后台线程"""
        self._running = False

    # ==================== 注册/注销 ====================

    def register(
        self,
        agent: Any,
        source: AgentSource = AgentSource.USER,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        注册 Agent

        Args:
            agent: Agent 实例
            source: Agent 来源
            parent_id: 父 Agent ID（如果是克隆的）
            metadata: 额外元数据

        Returns:
            str: Instance ID
        """
        with self._lock:
            # 获取或生成 Instance ID
            instance_id = getattr(agent, 'instance_id', None)
            if not instance_id:
                instance_id = self._generate_instance_id(agent)
                agent.instance_id = instance_id

            # 检查是否已注册
            if instance_id in self._agents:
                return instance_id  # 已注册，直接返回

            # 获取 Agent 名称
            name = getattr(agent, 'name', 'Unknown')

            # 创建记录
            record = AgentRecord(
                instance_id=instance_id,
                agent=agent,
                name=name,
                source=source,
                parent_id=parent_id,
                metadata=metadata or {}
            )

            self._agents[instance_id] = record

            # 追踪克隆链
            if parent_id:
                if parent_id not in self._clone_chains:
                    self._clone_chains[parent_id] = []
                self._clone_chains[parent_id].append(instance_id)

            # 触发回调
            for callback in self._on_register:
                try:
                    callback(record)
                except Exception:
                    pass

            return instance_id

    def unregister(self, instance_id: str, force: bool = False):
        """
        注销 Agent

        Args:
            instance_id: Instance ID
            force: 是否强制注销（即使正在执行）
        """
        with self._lock:
            if instance_id not in self._agents:
                return

            record = self._agents[instance_id]

            # 检查状态
            if record.status == AgentStatus.RUNNING and not force:
                raise ValueError(f"Agent {instance_id} 正在执行中，无法注销")

            # 删除记录
            del self._agents[instance_id]

            # 从克隆链中移除
            if record.parent_id and record.parent_id in self._clone_chains:
                self._clone_chains[record.parent_id].remove(instance_id)

            # 触发回调
            for callback in self._on_unregister:
                try:
                    callback(instance_id)
                except Exception:
                    pass

    # ==================== 获取 Agent ====================

    def get(self, instance_id: str) -> Optional[Any]:
        """获取 Agent 实例"""
        with self._lock:
            record = self._agents.get(instance_id)
            return record.agent if record else None

    def get_record(self, instance_id: str) -> Optional[AgentRecord]:
        """获取 Agent 记录"""
        with self._lock:
            return self._agents.get(instance_id)

    def list_agents(
        self,
        status: Optional[AgentStatus] = None,
        source: Optional[AgentSource] = None
    ) -> List[AgentRecord]:
        """
        列出 Agent

        Args:
            status: 按状态过滤
            source: 按来源过滤

        Returns:
            Agent 记录列表
        """
        with self._lock:
            result = list(self._agents.values())

            if status:
                result = [r for r in result if r.status == status]
            if source:
                result = [r for r in result if r.source == source]

            return result

    def list_active_agents(self) -> List[AgentRecord]:
        """列出活跃 Agent（非离线/脱管）"""
        with self._lock:
            return [
                r for r in self._agents.values()
                if r.status not in (AgentStatus.OFFLINE, AgentStatus.ORPHANED)
            ]

    # ==================== 状态管理 ====================

    def update_status(
        self,
        instance_id: str,
        status: AgentStatus,
        task_id: Optional[str] = None
    ):
        """更新 Agent 状态"""
        with self._lock:
            if instance_id not in self._agents:
                raise ValueError(f"Agent {instance_id} 未注册")

            record = self._agents[instance_id]
            old_status = record.status
            record.status = status
            record.last_active_at = time.time()

            if task_id:
                record.task_id = task_id

            # 触发回调
            for callback in self._on_status_change:
                try:
                    callback(instance_id, status)
                except Exception:
                    pass

    def mark_busy(self, instance_id: str, task_id: str):
        """标记 Agent 为忙碌"""
        self.update_status(instance_id, AgentStatus.RUNNING, task_id)

    def mark_idle(self, instance_id: str):
        """标记 Agent 为空闲"""
        self.update_status(instance_id, AgentStatus.IDLE, None)

    # ==================== 执行跟踪 ====================

    @contextmanager
    def track_execution(self, agent: Any, task_id: str):
        """
        跟踪执行上下文

        用法:
            with registry.track_execution(agent, "task-123"):
                result = agent.run(task)
        """
        instance_id = getattr(agent, 'instance_id', None)
        if not instance_id:
            instance_id = self.register(agent)

        record_id = str(uuid.uuid4())

        # 创建执行记录
        exec_record = ExecutionRecord(
            record_id=record_id,
            instance_id=instance_id,
            task_id=task_id
        )

        with self._lock:
            self._executions[record_id] = exec_record

            # 更新 Agent 状态
            if instance_id in self._agents:
                self._agents[instance_id].status = AgentStatus.RUNNING
                self._agents[instance_id].task_id = task_id

        try:
            yield exec_record
            exec_record.status = "completed"
            exec_record.completed_at = time.time()
        except Exception as e:
            exec_record.status = "error"
            exec_record.error = str(e)
            exec_record.completed_at = time.time()
            raise
        finally:
            with self._lock:
                # 更新 Agent 状态
                if instance_id in self._agents:
                    self._agents[instance_id].status = AgentStatus.IDLE
                    self._agents[instance_id].task_id = None
                    self._agents[instance_id].last_active_at = time.time()

    def get_execution_history(
        self,
        instance_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> List[ExecutionRecord]:
        """获取执行历史"""
        with self._lock:
            result = list(self._executions.values())

            if instance_id:
                result = [r for r in result if r.instance_id == instance_id]
            if task_id:
                result = [r for r in result if r.task_id == task_id]

            return result

    # ==================== 脱管检测和清理 ====================

    def detect_orphans(self, timeout: Optional[float] = None) -> List[str]:
        """
        检测脱管 Agent

        Args:
            timeout: 超时时间（秒），默认使用配置值

        Returns:
            脱管 Agent ID 列表
        """
        timeout = timeout or self._orphan_timeout
        now = time.time()
        orphans = []

        with self._lock:
            for instance_id, record in self._agents.items():
                # 跳过已标记的
                if record.status in (AgentStatus.OFFLINE, AgentStatus.ORPHANED):
                    continue

                # 检查超时
                if now - record.last_active_at > timeout:
                    orphans.append(instance_id)

        return orphans

    def mark_orphan(self, instance_id: str):
        """标记为脱管 Agent"""
        with self._lock:
            if instance_id in self._agents:
                self._agents[instance_id].status = AgentStatus.ORPHANED
                self._orphaned.add(instance_id)

                # 触发回调
                for callback in self._on_orphan_detected:
                    try:
                        callback(instance_id)
                    except Exception:
                        pass

    def cleanup_orphans(self, timeout: Optional[float] = None) -> int:
        """
        清理脱管 Agent

        Args:
            timeout: 超时时间（秒）

        Returns:
            清理的 Agent 数量
        """
        orphans = self.detect_orphans(timeout)
        cleaned = 0

        for instance_id in orphans:
            try:
                self.mark_orphan(instance_id)
                # 可以选择自动注销
                # self.unregister(instance_id, force=True)
                cleaned += 1
            except Exception:
                pass

        return cleaned

    def recover_orphan(self, instance_id: str) -> bool:
        """
        恢复脱管 Agent

        Args:
            instance_id: Agent ID

        Returns:
            是否成功
        """
        with self._lock:
            if instance_id not in self._agents:
                return False

            record = self._agents[instance_id]
            if record.status != AgentStatus.ORPHANED:
                return False

            record.status = AgentStatus.IDLE
            record.last_active_at = time.time()
            self._orphaned.discard(instance_id)
            return True

    # ==================== 克隆追踪 ====================

    def get_clone_chain(self, instance_id: str) -> List[str]:
        """获取克隆链（所有后代）"""
        with self._lock:
            result = []
            self._collect_clones(instance_id, result)
            return result

    def _collect_clones(self, instance_id: str, result: List[str]):
        """递归收集克隆"""
        if instance_id in self._clone_chains:
            for child_id in self._clone_chains[instance_id]:
                result.append(child_id)
                self._collect_clones(child_id, result)

    def get_parent(self, instance_id: str) -> Optional[str]:
        """获取父 Agent ID"""
        with self._lock:
            record = self._agents.get(instance_id)
            return record.parent_id if record else None

    # ==================== 统计和监控 ====================

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            total = len(self._agents)
            by_status = {}
            by_source = {}

            for record in self._agents.values():
                # 按状态统计
                status = record.status.value
                by_status[status] = by_status.get(status, 0) + 1

                # 按来源统计
                source = record.source.value
                by_source[source] = by_source.get(source, 0) + 1

            return {
                "total_agents": total,
                "by_status": by_status,
                "by_source": by_source,
                "orphaned_count": len(self._orphaned),
                "active_executions": len([e for e in self._executions.values() if e.status == "running"])
            }

    def get_orphaned_agents(self) -> List[AgentRecord]:
        """获取所有脱管 Agent"""
        with self._lock:
            return [
                self._agents[iid] for iid in self._orphaned
                if iid in self._agents
            ]

    # ==================== 工具方法 ====================

    def _generate_instance_id(self, agent: Any) -> str:
        """生成唯一 Instance ID"""
        name = getattr(agent, 'name', 'agent')
        timestamp = str(int(time.time() * 1000))
        unique = str(uuid.uuid4())[:8]
        return f"{name.lower().replace(' ', '_')}_{timestamp}_{unique}"

    # ==================== 回调注册 ====================

    def on_register(self, callback: Callable[[AgentRecord], None]):
        """注册 Agent 注册回调"""
        self._on_register.append(callback)

    def on_unregister(self, callback: Callable[[str], None]):
        """注册 Agent 注销回调"""
        self._on_unregister.append(callback)

    def on_status_change(self, callback: Callable[[str, AgentStatus], None]):
        """注册状态变更回调"""
        self._on_status_change.append(callback)

    def on_orphan_detected(self, callback: Callable[[str], None]):
        """注册脱管检测回调"""
        self._on_orphan_detected.append(callback)


# ==================== 全局单例 ====================

_registry_instance: Optional[AgentRegistry] = None
_registry_lock = threading.Lock()


def get_agent_registry() -> AgentRegistry:
    """获取全局 Agent 注册中心单例"""
    global _registry_instance

    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = AgentRegistry()

    return _registry_instance


def reset_registry():
    """重置注册中心（用于测试）"""
    global _registry_instance
    with _registry_lock:
        if _registry_instance:
            _registry_instance.stop()
        _registry_instance = AgentRegistry()


# 便捷函数
def register_agent(agent: Any, source: str = "user") -> str:
    """便捷注册 Agent"""
    source_map = {
        "builtin": AgentSource.BUILTIN,
        "custom": AgentSource.CUSTOM,
        "scheduler": AgentSource.SCHEDULER,
        "swarm": AgentSource.SWARM,
        "cli": AgentSource.CLI,
        "api": AgentSource.API,
        "user": AgentSource.USER
    }
    return get_agent_registry().register(
        agent,
        source=source_map.get(source.lower(), AgentSource.USER)
    )


def get_agent(instance_id: str) -> Optional[Any]:
    """便捷获取 Agent"""
    return get_agent_registry().get(instance_id)


def list_agents(status: Optional[str] = None) -> List[Any]:
    """便捷列出 Agent"""
    registry = get_agent_registry()
    status_filter = None
    if status:
        try:
            status_filter = AgentStatus(status.lower())
        except ValueError:
            pass

    records = registry.list_agents(status=status_filter)
    return [r.agent for r in records]


__all__ = [
    "AgentRegistry",
    "AgentRecord",
    "AgentStatus",
    "AgentSource",
    "ExecutionRecord",
    "get_agent_registry",
    "register_agent",
    "get_agent",
    "list_agents",
    "reset_registry"
]
