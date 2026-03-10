"""
Session Store - 会话持久化存储

支持:
- 任务状态持久化
- 会话恢复（重启后）
- JSON 文件存储
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path
from dataclasses import dataclass, field, asdict

from .api.models import TaskStatus


@dataclass
class SessionTask:
    """会话任务"""
    task_id: str
    type: str  # "agent" or "workflow"
    agent_name: Optional[str] = None
    workflow_name: Optional[str] = None
    input: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    config: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    output: Optional[str] = None
    files: List[str] = field(default_factory=list)
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionStore:
    """会话持久化存储"""

    def __init__(self, storage_dir: Optional[str] = None):
        self._storage_dir = storage_dir or self._default_storage_dir()
        self._sessions: Dict[str, SessionTask] = {}
        self._ensure_storage_dir()
        self._load_sessions()

    def _default_storage_dir(self) -> str:
        """默认存储目录"""
        return os.path.join(
            os.path.dirname(__file__),
            "..",
            "sessions"
        )

    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        Path(self._storage_dir).mkdir(parents=True, exist_ok=True)

    def _get_storage_file(self) -> str:
        """获取存储文件路径"""
        return os.path.join(self._storage_dir, "sessions.json")

    def _load_sessions(self):
        """从文件加载会话"""
        storage_file = self._get_storage_file()
        if os.path.exists(storage_file):
            try:
                with open(storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for task_data in data:
                        task = SessionTask(**task_data)
                        self._sessions[task.task_id] = task
                print(f"[SessionStore] 已加载 {len(self._sessions)} 个会话")
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"[SessionStore] 警告：加载会话失败：{e}")

    def _save_sessions(self):
        """保存会话到文件"""
        storage_file = self._get_storage_file()
        data = []
        for task in self._sessions.values():
            task_dict = asdict(task)
            data.append(task_dict)
        with open(storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def create_task(
        self,
        task_type: str,
        agent_name: Optional[str] = None,
        workflow_name: Optional[str] = None,
        input: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        创建新任务

        Args:
            task_type: 任务类型（"agent" 或 "workflow"）
            agent_name: Agent 名称
            workflow_name: Workflow 名称
            input: 输入文本
            inputs: 输入字典
            config: 配置选项
            metadata: 元数据

        Returns:
            任务 ID
        """
        task_id = str(uuid.uuid4())
        task = SessionTask(
            task_id=task_id,
            type=task_type,
            agent_name=agent_name,
            workflow_name=workflow_name,
            input=input,
            inputs=inputs,
            config=config or {},
            status=TaskStatus.PENDING,
            metadata=metadata or {},
        )
        self._sessions[task_id] = task
        self._save_sessions()
        return task_id

    def get_task(self, task_id: str) -> Optional[SessionTask]:
        """获取任务"""
        return self._sessions.get(task_id)

    def update_status(self, task_id: str, status: TaskStatus):
        """更新任务状态"""
        if task_id in self._sessions:
            task = self._sessions[task_id]
            task.status = status

            if status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = datetime.now().isoformat()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                task.completed_at = datetime.now().isoformat()
                if task.started_at:
                    start = datetime.fromisoformat(task.started_at)
                    end = datetime.fromisoformat(task.completed_at)
                    task.duration = (end - start).total_seconds()

            self._save_sessions()

    def update_output(self, task_id: str, output: str, files: Optional[List[str]] = None):
        """更新任务输出"""
        if task_id in self._sessions:
            task = self._sessions[task_id]
            task.output = output
            if files:
                task.files = files
            self._save_sessions()

    def update_error(self, task_id: str, error: str):
        """更新任务错误"""
        if task_id in self._sessions:
            task = self._sessions[task_id]
            task.error = error
            self._save_sessions()

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100,
    ) -> List[SessionTask]:
        """
        列出任务

        Args:
            status: 按状态筛选
            limit: 返回数量限制

        Returns:
            任务列表
        """
        tasks = list(self._sessions.values())

        # 按状态筛选
        if status:
            tasks = [t for t in tasks if t.status == status]

        # 按创建时间排序（最新的在前）
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        # 限制数量
        return tasks[:limit]

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self._sessions:
            del self._sessions[task_id]
            self._save_sessions()
            return True
        return False

    def get_active_tasks(self) -> List[SessionTask]:
        """获取活跃任务"""
        return [
            t for t in self._sessions.values()
            if t.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
        ]

    def recover_tasks(self) -> List[SessionTask]:
        """
        恢复未完成的任务

        当服务重启后，将 PENDING/RUNNING 状态的任务恢复为 FAILED

        Returns:
            恢复的任务列表
        """
        recovered = []
        for task in self._sessions.values():
            if task.status == TaskStatus.RUNNING:
                # 服务重启时正在运行的任务，标记为失败
                task.status = TaskStatus.FAILED
                task.error = "服务重启，任务中断"
                task.completed_at = datetime.now().isoformat()
                recovered.append(task)
        if recovered:
            self._save_sessions()
        return recovered

    def cleanup_old_tasks(self, days: int = 30) -> int:
        """
        清理旧任务

        Args:
            days: 保留天数

        Returns:
            清理的任务数
        """
        cutoff = datetime.now() - timedelta(days=days)
        to_delete = []

        for task_id, task in self._sessions.items():
            if task.completed_at:
                completed = datetime.fromisoformat(task.completed_at)
                if completed < cutoff:
                    to_delete.append(task_id)

        for task_id in to_delete:
            del self._sessions[task_id]

        self._save_sessions()
        return len(to_delete)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._sessions)
        by_status = {}
        by_agent = {}

        for task in self._sessions.values():
            # 按状态统计
            status = task.status.value
            by_status[status] = by_status.get(status, 0) + 1

            # 按 Agent 统计
            if task.agent_name:
                by_agent[task.agent_name] = by_agent.get(task.agent_name, 0) + 1

        return {
            "total": total,
            "by_status": by_status,
            "by_agent": by_agent,
        }


# 全局实例
_store_instance: Optional[SessionStore] = None


def get_store() -> SessionStore:
    """获取全局存储实例"""
    global _store_instance
    if _store_instance is None:
        _store_instance = SessionStore()
    return _store_instance


def init_store(storage_dir: Optional[str] = None) -> SessionStore:
    """初始化存储实例"""
    global _store_instance
    _store_instance = SessionStore(storage_dir)
    return _store_instance
