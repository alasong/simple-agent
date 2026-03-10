"""
Task Scheduler - 定时任务调度器

支持:
- 一次性定时任务
- 周期性任务（cron 表达式）
- 任务轮询
- 任务队列管理
"""

import threading
import time
import schedule
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import os


class ScheduleType(str, Enum):
    """调度类型"""
    ONCE = "once"  # 一次性
    INTERVAL = "interval"  # 间隔
    CRON = "cron"  # cron 表达式


@dataclass
class ScheduledTask:
    """定时任务"""
    task_id: str
    name: str
    schedule_type: ScheduleType
    agent_name: str
    input: str
    config: Dict[str, Any] = field(default_factory=dict)

    # 调度配置
    run_at: Optional[datetime] = None  # 一次性执行时间
    interval_seconds: Optional[int] = None  # 间隔秒数
    cron_expression: Optional[str] = None  # cron 表达式

    # 状态
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    total_runs: int = 0
    failed_runs: int = 0

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    description: Optional[str] = None


class CronParser:
    """简易 Cron 表达式解析器

    支持格式：分 时 日 月 周
    例如：*/5 * * * *  (每 5 分钟)
    """

    @staticmethod
    def parse(expression: str) -> List[int]:
        """解析 cron 表达式，返回分钟间隔"""
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError(f"无效的 cron 表达式：{expression}")

        minute = parts[0]

        # 解析分钟
        if minute == "*":
            return list(range(60))
        elif minute.startswith("*/"):
            step = int(minute[2:])
            return list(range(0, 60, step))
        elif "-" in minute:
            start, end = map(int, minute.split("-"))
            return list(range(start, end + 1))
        else:
            return [int(minute)]

    @staticmethod
    def get_next_run(expression: str) -> datetime:
        """计算下次执行时间"""
        minutes = CronParser.parse(expression)
        now = datetime.now()

        # 找到下一个分钟
        for minute in minutes:
            if minute > now.minute:
                return now.replace(minute=minute, second=0, microsecond=0)

        # 如果今天的分钟都已过，明天第一个时间执行
        next_time = now + timedelta(days=1)
        return next_time.replace(minute=minutes[0], second=0, microsecond=0)


class TaskScheduler:
    """任务调度器"""

    def __init__(self, storage_path: Optional[str] = None):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._storage_path = storage_path or self._default_storage_path()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: Dict[str, Callable] = {}  # 任务执行回调
        self._load_tasks()

    def _default_storage_path(self) -> str:
        """默认存储路径"""
        return os.path.join(
            os.path.dirname(__file__),
            "..",
            "config",
            "scheduled_tasks.json"
        )

    def _load_tasks(self):
        """从文件加载任务"""
        if os.path.exists(self._storage_path):
            try:
                with open(self._storage_path, "r") as f:
                    data = json.load(f)
                    for task_data in data:
                        task = ScheduledTask(
                            task_id=task_data["task_id"],
                            name=task_data["name"],
                            schedule_type=ScheduleType(task_data["schedule_type"]),
                            agent_name=task_data["agent_name"],
                            input=task_data["input"],
                            config=task_data.get("config", {}),
                            run_at=(
                                datetime.fromisoformat(task_data["run_at"])
                                if task_data.get("run_at") else None
                            ),
                            interval_seconds=task_data.get("interval_seconds"),
                            cron_expression=task_data.get("cron_expression"),
                            enabled=task_data.get("enabled", True),
                            total_runs=task_data.get("total_runs", 0),
                            failed_runs=task_data.get("failed_runs", 0),
                            created_at=(
                                datetime.fromisoformat(task_data["created_at"])
                                if task_data.get("created_at") else datetime.now()
                            ),
                            description=task_data.get("description"),
                        )
                        self._tasks[task.task_id] = task

                # 恢复执行
                self.start()
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"[TaskScheduler] 警告：加载任务失败：{e}")

    def _save_tasks(self):
        """保存任务到文件"""
        os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
        data = []
        for task in self._tasks.values():
            data.append({
                "task_id": task.task_id,
                "name": task.name,
                "schedule_type": task.schedule_type.value,
                "agent_name": task.agent_name,
                "input": task.input,
                "config": task.config,
                "run_at": task.run_at.isoformat() if task.run_at else None,
                "interval_seconds": task.interval_seconds,
                "cron_expression": task.cron_expression,
                "enabled": task.enabled,
                "total_runs": task.total_runs,
                "failed_runs": task.failed_runs,
                "created_at": task.created_at.isoformat(),
                "description": task.description,
            })
        with open(self._storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _run_scheduler(self):
        """运行调度器（在独立线程中）"""
        while self._running:
            now = datetime.now()

            for task in list(self._tasks.values()):
                if not task.enabled:
                    continue

                # 检查是否需要执行
                should_run = False

                if task.schedule_type == ScheduleType.ONCE:
                    if task.run_at and task.run_at <= now:
                        should_run = True
                        task.enabled = False  # 一次性任务执行后禁用

                elif task.schedule_type == ScheduleType.INTERVAL:
                    if task.last_run:
                        elapsed = (now - task.last_run).total_seconds()
                        if elapsed >= task.interval_seconds:
                            should_run = True
                    else:
                        should_run = True

                elif task.schedule_type == ScheduleType.CRON:
                    if task.next_run and task.next_run <= now:
                        should_run = True
                        # 更新下次执行时间
                        task.next_run = CronParser.get_next_run(task.cron_expression)

                # 执行任务
                if should_run:
                    self._execute_task(task)

            # 每秒检查一次
            time.sleep(1)

    def _execute_task(self, task: ScheduledTask):
        """执行定时任务"""
        task.last_run = datetime.now()
        task.total_runs += 1

        # 调用回调函数执行实际任务
        if task.task_id in self._callbacks:
            try:
                callback = self._callbacks[task.task_id]
                callback(task)
            except Exception as e:
                task.failed_runs += 1
                print(f"[TaskScheduler] 任务执行失败 {task.name}: {e}")

        self._save_tasks()

    def register_callback(self, task_id: str, callback: Callable):
        """注册任务执行回调"""
        self._callbacks[task_id] = callback

    def create_once_task(
        self,
        name: str,
        agent_name: str,
        input: str,
        run_at: datetime,
        config: Optional[Dict] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> str:
        """创建一次性定时任务"""
        task_id = str(uuid.uuid4())
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_type=ScheduleType.ONCE,
            agent_name=agent_name,
            input=input,
            config=config or {},
            run_at=run_at,
            next_run=run_at,
            description=description,
            created_by=created_by,
        )
        self._tasks[task_id] = task
        self._save_tasks()
        return task_id

    def create_interval_task(
        self,
        name: str,
        agent_name: str,
        input: str,
        interval_seconds: int,
        config: Optional[Dict] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> str:
        """创建周期性任务（间隔）"""
        task_id = str(uuid.uuid4())
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_type=ScheduleType.INTERVAL,
            agent_name=agent_name,
            input=input,
            config=config or {},
            interval_seconds=interval_seconds,
            next_run=datetime.now(),
            description=description,
            created_by=created_by,
        )
        self._tasks[task_id] = task
        self._save_tasks()
        return task_id

    def create_cron_task(
        self,
        name: str,
        agent_name: str,
        input: str,
        cron_expression: str,
        config: Optional[Dict] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> str:
        """创建周期性任务（cron）"""
        task_id = str(uuid.uuid4())
        next_run = CronParser.get_next_run(cron_expression)

        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_type=ScheduleType.CRON,
            agent_name=agent_name,
            input=input,
            config=config or {},
            cron_expression=cron_expression,
            next_run=next_run,
            description=description,
            created_by=created_by,
        )
        self._tasks[task_id] = task
        self._save_tasks()
        return task_id

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务"""
        return self._tasks.get(task_id)

    def list_tasks(self, enabled_only: bool = False) -> List[ScheduledTask]:
        """列出任务"""
        tasks = list(self._tasks.values())
        if enabled_only:
            tasks = [t for t in tasks if t.enabled]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = True
            self._save_tasks()
            return True
        return False

    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = False
            self._save_tasks()
            return True
        return False

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            if task_id in self._callbacks:
                del self._callbacks[task_id]
            self._save_tasks()
            return True
        return False

    def start(self):
        """启动调度器"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()

    def stop(self):
        """停止调度器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)


# 全局实例
_scheduler_instance: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """获取全局调度器实例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler()
    return _scheduler_instance


def init_scheduler(storage_path: Optional[str] = None) -> TaskScheduler:
    """初始化调度器实例"""
    global _scheduler_instance
    _scheduler_instance = TaskScheduler(storage_path)
    return _scheduler_instance
