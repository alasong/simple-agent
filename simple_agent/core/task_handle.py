#!/usr/bin/env python3
"""
Task Handle - 任务状态跟踪和数据模型

提供异步任务的状态管理、结果获取和取消功能。
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Literal
from enum import Enum


class TaskStatusEnum(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"           # 等待执行
    RUNNING = "running"           # 正在执行
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消
    CONFIRMING = "confirming"     # 等待用户确认（交互式任务）


@dataclass
class TaskStatus:
    """任务状态数据类"""
    id: str
    input: str                          # 用户输入
    status: TaskStatusEnum              # 当前状态
    submitted_at: datetime              # 提交时间
    started_at: Optional[datetime] = None  # 开始时间
    completed_at: Optional[datetime] = None  # 完成时间
    result: Any = None                  # 执行结果
    error: Optional[str] = None         # 错误信息
    progress: str = ""                  # 进度描述
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "input": self.input,
            "status": self.status.value,
            "submitted_at": self.submitted_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": str(self.result)[:200] if self.result else None,
            "error": self.error,
            "progress": self.progress
        }
    
    @classmethod
    def create(cls, task_id: str, user_input: str) -> "TaskStatus":
        """创建新的任务状态"""
        return cls(
            id=task_id,
            input=user_input,
            status=TaskStatusEnum.PENDING,
            submitted_at=datetime.now()
        )


class TaskHandle:
    """
    任务句柄 - 表示一个后台执行的任务
    
    提供：
    - 状态查询
    - 结果获取（可阻塞）
    - 任务取消
    """
    
    def __init__(self, task_id: str):
        self.id = task_id
        self._status = TaskStatus.create(task_id, "")
        self._future: asyncio.Future = asyncio.Future()
        self._cancel_event = asyncio.Event()
        self._lock = asyncio.Lock()
    
    @property
    def status(self) -> TaskStatus:
        """获取当前状态（同步）"""
        return self._status
    
    @property
    def is_done(self) -> bool:
        """任务是否已完成（包括成功、失败、取消）"""
        return self._status.status in [
            TaskStatusEnum.COMPLETED,
            TaskStatusEnum.FAILED,
            TaskStatusEnum.CANCELLED
        ]
    
    @property
    def is_running(self) -> bool:
        """任务是否正在运行"""
        return self._status.status == TaskStatusEnum.RUNNING
    
    @property
    def is_pending(self) -> bool:
        """任务是否等待执行"""
        return self._status.status == TaskStatusEnum.PENDING

    @property
    def is_confirming(self) -> bool:
        """任务是否等待用户确认"""
        return self._status.status == TaskStatusEnum.CONFIRMING
    
    async def update_status(
        self,
        status: TaskStatusEnum,
        progress: str = "",
        result: Any = None,
        error: Optional[str] = None
    ):
        """更新任务状态"""
        async with self._lock:
            self._status.status = status
            self._status.progress = progress
            
            if status == TaskStatusEnum.RUNNING:
                self._status.started_at = datetime.now()
            elif status in [TaskStatusEnum.COMPLETED, TaskStatusEnum.FAILED, TaskStatusEnum.CANCELLED]:
                self._status.completed_at = datetime.now()
                if result is not None:
                    self._status.result = result
                if error is not None:
                    self._status.error = error
                
                # 设置 future，唤醒等待结果的协程
                if not self._future.done():
                    if status == TaskStatusEnum.COMPLETED:
                        self._future.set_result(result)
                    elif status == TaskStatusEnum.FAILED:
                        self._future.set_exception(Exception(error))
                    else:  # CANCELLED
                        self._future.cancel()
    
    def set_input(self, user_input: str):
        """设置任务输入（在提交时调用）"""
        self._status.input = user_input
    
    async def get_status(self) -> TaskStatus:
        """获取任务状态（异步）"""
        async with self._lock:
            return self._status
    
    async def result(self, timeout: Optional[float] = None) -> Any:
        """
        获取任务结果（阻塞直到完成）
        
        Args:
            timeout: 超时时间（秒），None 表示无限等待
        
        Returns:
            任务执行结果
        
        Raises:
            asyncio.TimeoutError: 超时
            Exception: 任务执行失败
            asyncio.CancelledError: 任务被取消
        """
        try:
            if timeout is not None:
                return await asyncio.wait_for(self._future, timeout=timeout)
            else:
                return await self._future
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"任务 {self.id} 执行超时")
    
    async def cancel(self) -> bool:
        """
        取消任务
        
        Returns:
            True 如果取消成功，False 如果任务已完成或无法取消
        """
        async with self._lock:
            if self.is_done:
                return False
            
            self._status.status = TaskStatusEnum.CANCELLED
            self._status.completed_at = datetime.now()
            self._status.progress = "已取消"
            
            # 触发取消事件
            self._cancel_event.set()
            
            # 取消 future
            if not self._future.done():
                self._future.cancel()
            
            return True
    
    def check_cancelled(self) -> bool:
        """检查任务是否被取消（供执行过程中轮询）"""
        return self._cancel_event.is_set()
    
    def get_elapsed_time(self) -> float:
        """获取已执行时间（秒）"""
        if not self._status.started_at:
            return 0.0
        
        end_time = self._status.completed_at or datetime.now()
        return (end_time - self._status.started_at).total_seconds()
    
    def __repr__(self) -> str:
        return f"TaskHandle(id={self.id}, status={self._status.status.value})"


@dataclass
class TaskDefinition:
    """任务定义 - 用于提交任务"""
    id: str
    input: str
    coro: Any  # Coroutine 对象
    callback: Optional[Any] = None  # 可选的完成回调
    priority: int = 0  # 优先级（数字越大优先级越高）
    metadata: dict = field(default_factory=dict)  # 元数据
    
    def __lt__(self, other):
        """实现小于比较，用于 PriorityQueue（优先级数字大的优先）"""
        # 负优先级比较（因为 PriorityQueue 是最小堆）
        return -self.priority < -other.priority
    
    def __eq__(self, other):
        """实现相等比较"""
        return self.priority == other.priority


def generate_task_id() -> str:
    """生成唯一的任务 ID"""
    import random
    timestamp = int(time.time() * 1000)
    random_suffix = random.randint(1000, 9999)
    return f"task_{timestamp}_{random_suffix}"
