"""
Usage Tracker - 用量追踪

支持:
- Token 消耗统计
- 任务时长统计
- 按 Agent/用户维度统计
- 持久化存储
"""

import json
import os
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class TaskUsage:
    """单次任务用量"""
    task_id: str
    agent_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    duration: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DailyStats:
    """每日统计"""
    date: str  # YYYY-MM-DD
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_tokens: int = 0
    total_duration: float = 0.0
    tasks_by_agent: Dict[str, int] = field(default_factory=dict)


class UsageTracker:
    """用量追踪器"""

    def __init__(self, storage_path: Optional[str] = None):
        self._tasks: Dict[str, TaskUsage] = {}
        self._daily_stats: Dict[str, DailyStats] = {}
        self._storage_path = storage_path or self._get_default_storage_path()
        self._start_time = time.time()
        self._load_data()

    def _get_default_storage_path(self) -> str:
        """默认存储路径"""
        return os.path.join(
            os.path.dirname(__file__),
            "..",
            "output",
            "usage_stats.json"
        )

    @property
    def _stats_dir(self) -> str:
        """统计文件目录"""
        return os.path.join(
            os.path.dirname(__file__),
            "..",
            "output",
            "usage_stats"
        )

    def _get_daily_file(self, date_str: str) -> str:
        """获取指定日期的统计文件路径"""
        os.makedirs(self._stats_dir, exist_ok=True)
        return os.path.join(self._stats_dir, f"{date_str}.json")

    def _load_data(self):
        """从文件加载用量数据"""
        # 加载总任务数据
        if os.path.exists(self._storage_path):
            try:
                with open(self._storage_path, "r") as f:
                    data = json.load(f)
                    for task_data in data.get("tasks", []):
                        task = TaskUsage(
                            task_id=task_data["task_id"],
                            agent_name=task_data["agent_name"],
                            input_tokens=task_data.get("input_tokens", 0),
                            output_tokens=task_data.get("output_tokens", 0),
                            total_tokens=task_data.get("total_tokens", 0),
                            duration=task_data.get("duration", 0.0),
                            started_at=(
                                datetime.fromisoformat(task_data["started_at"])
                                if task_data.get("started_at") else None
                            ),
                            completed_at=(
                                datetime.fromisoformat(task_data["completed_at"])
                                if task_data.get("completed_at") else None
                            ),
                            status=task_data.get("status", "pending"),
                            metadata=task_data.get("metadata", {}),
                        )
                        self._tasks[task.task_id] = task
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"[UsageTracker] 警告：加载任务数据失败：{e}")

        # 加载最近的每日统计（最近 30 天）
        today = datetime.now().strftime("%Y-%m-%d")
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            file_path = self._get_daily_file(date)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        stats = DailyStats(
                            date=data["date"],
                            total_tasks=data.get("total_tasks", 0),
                            completed_tasks=data.get("completed_tasks", 0),
                            failed_tasks=data.get("failed_tasks", 0),
                            total_tokens=data.get("total_tokens", 0),
                            total_duration=data.get("total_duration", 0.0),
                            tasks_by_agent=data.get("tasks_by_agent", {}),
                        )
                        self._daily_stats[date] = stats
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"[UsageTracker] 警告：加载 {date} 统计数据失败：{e}")

    def _save_data(self):
        """保存用量数据到文件"""
        # 保存总任务数据（最近 1000 条）
        recent_tasks = list(self._tasks.values())[-1000:]
        data = {
            "tasks": [
                {
                    "task_id": t.task_id,
                    "agent_name": t.agent_name,
                    "input_tokens": t.input_tokens,
                    "output_tokens": t.output_tokens,
                    "total_tokens": t.total_tokens,
                    "duration": t.duration,
                    "started_at": t.started_at.isoformat() if t.started_at else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    "status": t.status,
                    "metadata": t.metadata,
                }
                for t in recent_tasks
            ]
        }
        with open(self._storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _save_daily_stats(self, date_str: str):
        """保存指定日期的统计数据"""
        if date_str not in self._daily_stats:
            return
        stats = self._daily_stats[date_str]
        file_path = self._get_daily_file(date_str)
        data = {
            "date": stats.date,
            "total_tasks": stats.total_tasks,
            "completed_tasks": stats.completed_tasks,
            "failed_tasks": stats.failed_tasks,
            "total_tokens": stats.total_tokens,
            "total_duration": stats.total_duration,
            "tasks_by_agent": stats.tasks_by_agent,
        }
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def start_task(self, task_id: str, agent_name: str, metadata: Optional[Dict] = None):
        """开始追踪任务"""
        task = TaskUsage(
            task_id=task_id,
            agent_name=agent_name,
            started_at=datetime.now(),
            status="running",
            metadata=metadata or {},
        )
        self._tasks[task_id] = task

    def update_tokens(self, task_id: str, input_tokens: int, output_tokens: int):
        """更新 token 使用量"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.input_tokens = input_tokens
            task.output_tokens = output_tokens
            task.total_tokens = input_tokens + output_tokens

    def complete_task(self, task_id: str, status: str = "completed"):
        """完成任务追踪"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.completed_at = datetime.now()
            task.status = status
            if task.started_at:
                task.duration = (task.completed_at - task.started_at).total_seconds()

            # 更新每日统计
            date_str = task.started_at.strftime("%Y-%m-%d") if task.started_at else datetime.now().strftime("%Y-%m-%d")
            self._update_daily_stats(task, date_str)

            # 保存到文件
            self._save_data()

    def _update_daily_stats(self, task: TaskUsage, date_str: str):
        """更新每日统计"""
        if date_str not in self._daily_stats:
            self._daily_stats[date_str] = DailyStats(date=date_str)

        stats = self._daily_stats[date_str]
        stats.total_tasks += 1
        if task.status == "completed":
            stats.completed_tasks += 1
        elif task.status == "failed":
            stats.failed_tasks += 1
        stats.total_tokens += task.total_tokens
        stats.total_duration += task.duration

        if task.agent_name not in stats.tasks_by_agent:
            stats.tasks_by_agent[task.agent_name] = 0
        stats.tasks_by_agent[task.agent_name] += 1

        # 保存到文件
        self._save_daily_stats(date_str)

    def get_task_usage(self, task_id: str) -> Optional[TaskUsage]:
        """获取任务用量"""
        return self._tasks.get(task_id)

    def get_total_usage(self) -> Dict[str, Any]:
        """获取总用量"""
        total_tokens = sum(t.total_tokens for t in self._tasks.values())
        total_duration = sum(t.duration for t in self._tasks.values())
        completed = sum(1 for t in self._tasks.values() if t.status == "completed")
        failed = sum(1 for t in self._tasks.values() if t.status == "failed")
        total = len(self._tasks)

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "total_tokens": total_tokens,
            "total_duration": total_duration,
            "success_rate": completed / total if total > 0 else 0.0,
            "avg_duration": total_duration / total if total > 0 else 0.0,
        }

    def get_daily_usage(self, days: int = 7) -> List[Dict]:
        """获取指定天数的用量统计"""
        result = []
        today = datetime.now()
        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            if date in self._daily_stats:
                stats = self._daily_stats[date]
                result.append({
                    "date": date,
                    "total_tasks": stats.total_tasks,
                    "completed_tasks": stats.completed_tasks,
                    "failed_tasks": stats.failed_tasks,
                    "total_tokens": stats.total_tokens,
                    "total_duration": stats.total_duration,
                    "tasks_by_agent": stats.tasks_by_agent,
                })
            else:
                result.append({
                    "date": date,
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "failed_tasks": 0,
                    "total_tokens": 0,
                    "total_duration": 0,
                    "tasks_by_agent": {},
                })
        return result

    def get_uptime(self) -> float:
        """获取运行时长"""
        return time.time() - self._start_time


# 全局追踪实例
_tracker_instance: Optional[UsageTracker] = None


def get_tracker() -> UsageTracker:
    """获取全局追踪实例"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = UsageTracker()
    return _tracker_instance


def init_tracker(storage_path: Optional[str] = None) -> UsageTracker:
    """初始化追踪实例"""
    global _tracker_instance
    _tracker_instance = UsageTracker(storage_path)
    return _tracker_instance
