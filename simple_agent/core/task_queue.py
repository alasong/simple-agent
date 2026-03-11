#!/usr/bin/env python3
"""
Task Queue - 异步任务队列与后台执行

提供：
- 任务提交和管理
- 并发控制（限制同时执行的任务数）
- 后台执行 worker
- 任务状态跟踪
"""

import asyncio
import threading
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any, Awaitable, Union
from .task_handle import (
    TaskHandle, TaskStatus, TaskStatusEnum,
    TaskDefinition, generate_task_id
)


# 交互式任务回调（用于在主线程中获取用户确认）
_interactive_callback: Optional[Callable] = None
_interactive_callback_lock = threading.Lock()


def set_interactive_callback(callback: Optional[Callable]):
    """
    设置交互式任务回调

    当后台任务需要用户确认时，会调用此回调函数

    Args:
        callback: 回调函数，签名: lambda prompt: bool
                 返回 True 表示用户确认，False 表示取消
    """
    global _interactive_callback
    with _interactive_callback_lock:
        _interactive_callback = callback


def get_interactive_callback() -> Optional[Callable]:
    """获取交互式任务回调"""
    global _interactive_callback
    with _interactive_callback_lock:
        return _interactive_callback


class TaskQueue:
    """
    异步任务队列管理器
    
    特性：
    - 基于 asyncio.Queue 的 FIFO 队列
    - Semaphore 控制并发数量
    - 后台 worker 持续处理任务
    - 完整的任务状态跟踪
    """
    
    def __init__(self, max_concurrent: int = 3):
        """
        初始化任务队列
        
        Args:
            max_concurrent: 最大并发任务数（默认 3）
        """
        self.max_concurrent = max_concurrent
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._tasks: Dict[str, TaskHandle] = {}  # task_id -> TaskHandle
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()
        self._task_counter = 0
    
    async def start(self):
        """启动后台 worker"""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        print(f"[TaskQueue] 后台 worker 已启动（最大并发：{self.max_concurrent}）")
    
    async def stop(self, wait: bool = True):
        """
        停止后台 worker
        
        Args:
            wait: 是否等待正在运行的任务完成
        """
        if not self._running:
            return
        
        self._running = False
        
        if wait and self._worker_task:
            # 等待队列清空
            await self._queue.join()
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        print(f"[TaskQueue] 后台 worker 已停止")
    
    async def submit(
        self,
        task_id: Optional[str] = None,
        input_text: str = "",
        coro: Optional[Any] = None,
        callback: Optional[Callable] = None,
        priority: int = 0,
        interactive: bool = False
    ) -> TaskHandle:
        """
        提交任务到队列

        Args:
            task_id: 任务 ID（可选，自动生成）
            input_text: 用户输入描述
            coro: 协程对象（可选，如果提供则立即包装执行）
            callback: 完成回调函数（可选）
            priority: 优先级（数字越大优先级越高，默认 0）
            interactive: 是否为交互式任务（需要用户确认）

        Returns:
            TaskHandle 对象，用于跟踪任务状态
        """
        if task_id is None:
            task_id = generate_task_id()

        # 创建任务句柄
        handle = TaskHandle(task_id)
        handle.set_input(input_text)
        # 设置元数据（用于交互式任务标记）
        if hasattr(handle, 'set_metadata'):
            handle.set_metadata({"interactive": interactive})

        async with self._lock:
            self._tasks[task_id] = handle

        # 如果提供了协程，立即创建执行任务
        if coro is not None:
            task_def = TaskDefinition(
                id=task_id,
                input=input_text,
                coro=coro,
                callback=callback,
                priority=priority
            )
            # 使用负优先级实现最大优先级优先（PriorityQueue 是最小堆）
            await self._queue.put((-priority, task_def))

        return handle
    
    async def submit_sync(
        self,
        func: Callable,
        input_text: str = "",
        task_id: Optional[str] = None,
        callback: Optional[Callable] = None,
        priority: int = 0,
        **kwargs
    ) -> TaskHandle:
        """
        提交同步函数到队列（自动包装为协程）
        
        Args:
            func: 同步函数
            input_text: 用户输入描述
            task_id: 任务 ID（可选）
            callback: 完成回调函数（可选）
            priority: 优先级
            **kwargs: 传递给函数的参数
        
        Returns:
            TaskHandle 对象
        """
        # 创建协程包装器
        async def task_coro():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: func(**kwargs)
            )
        
        return await self.submit(
            task_id=task_id,
            input_text=input_text,
            coro=task_coro(),
            callback=callback,
            priority=priority
        )
    
    async def _worker(self):
        """后台 worker - 持续从队列获取并执行任务"""
        while self._running:
            try:
                # 从队列获取任务（带超时）
                try:
                    _, task_def = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                task_id = task_def.id

                # 检查任务是否被取消
                handle = self._tasks.get(task_id)
                if handle and handle.check_cancelled():
                    await handle.update_status(
                        TaskStatusEnum.CANCELLED,
                        progress="任务被取消"
                    )
                    self._queue.task_done()
                    continue

                # 检查任务是否等待用户确认（交互式任务）
                if handle and handle.status.status == TaskStatusEnum.CONFIRMING:
                    # 交互式任务不能在后台执行，需要用户手动确认
                    await handle.update_status(
                        TaskStatusEnum.PENDING,
                        progress="等待用户确认（交互式任务）"
                    )
                    self._queue.task_done()
                    continue

                # 执行任务（受 semaphore 限制）
                asyncio.create_task(self._execute_task(task_def, handle))

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[TaskQueue] Worker 错误：{e}")
    
    async def _execute_task(self, task_def: TaskDefinition, handle: TaskHandle):
        """执行单个任务"""
        task_id = task_def.id
        
        async with self._semaphore:
            try:
                # 更新状态为运行中
                await handle.update_status(
                    TaskStatusEnum.RUNNING,
                    progress="正在执行..."
                )
                
                # 执行协程
                if asyncio.iscoroutine(task_def.coro):
                    result = await task_def.coro
                else:
                    result = task_def.coro
                
                # 更新状态为完成
                await handle.update_status(
                    TaskStatusEnum.COMPLETED,
                    progress="执行完成",
                    result=result
                )
                
                # 调用回调
                if task_def.callback:
                    try:
                        if asyncio.iscoroutinefunction(task_def.callback):
                            await task_def.callback(task_id, result, None)
                        else:
                            task_def.callback(task_id, result, None)
                    except Exception as e:
                        print(f"[TaskQueue] 回调执行失败：{e}")
                
            except asyncio.CancelledError:
                await handle.update_status(
                    TaskStatusEnum.CANCELLED,
                    progress="任务被取消"
                )
            
            except Exception as e:
                # 更新状态为失败
                await handle.update_status(
                    TaskStatusEnum.FAILED,
                    progress=f"执行失败：{str(e)}",
                    error=str(e)
                )
                
                # 调用回调（传递错误）
                if task_def.callback:
                    try:
                        if asyncio.iscoroutinefunction(task_def.callback):
                            await task_def.callback(task_id, None, e)
                        else:
                            task_def.callback(task_id, None, e)
                    except Exception:
                        pass
            
            finally:
                # 标记任务完成
                self._queue.task_done()
    
    async def get_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        async with self._lock:
            handle = self._tasks.get(task_id)
            if handle:
                return await handle.get_status()
            return None
    
    async def list_tasks(
        self,
        status_filter: Optional[str] = None
    ) -> List[TaskStatus]:
        """
        列出所有任务
        
        Args:
            status_filter: 状态过滤（pending, running, completed, failed, cancelled）
        
        Returns:
            任务状态列表
        """
        async with self._lock:
            tasks = []
            for handle in self._tasks.values():
                status = await handle.get_status()
                
                if status_filter is None:
                    tasks.append(status)
                elif status_filter == "active" and status.status in [
                    TaskStatusEnum.PENDING,
                    TaskStatusEnum.RUNNING
                ]:
                    tasks.append(status)
                elif status_filter == "done" and status.status in [
                    TaskStatusEnum.COMPLETED,
                    TaskStatusEnum.FAILED,
                    TaskStatusEnum.CANCELLED
                ]:
                    tasks.append(status)
                elif status_filter == status.status.value:
                    tasks.append(status)
            
            # 按提交时间排序（最新的在前）
            tasks.sort(key=lambda s: s.submitted_at, reverse=True)
            return tasks
    
    async def cancel(self, task_id: str) -> bool:
        """取消任务"""
        async with self._lock:
            handle = self._tasks.get(task_id)
            if handle:
                return await handle.cancel()
            return False
    
    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """获取任务结果（阻塞直到完成）"""
        async with self._lock:
            handle = self._tasks.get(task_id)
            if not handle:
                raise ValueError(f"任务不存在：{task_id}")
        
        return await handle.result(timeout=timeout)
    
    def get_stats(self) -> dict:
        """获取队列统计信息"""
        pending = sum(1 for h in self._tasks.values() if h.is_pending)
        running = sum(1 for h in self._tasks.values() if h.is_running)
        completed = sum(1 for h in self._tasks.values() if h.status.status == TaskStatusEnum.COMPLETED)
        failed = sum(1 for h in self._tasks.values() if h.status.status == TaskStatusEnum.FAILED)
        cancelled = sum(1 for h in self._tasks.values() if h.status.status == TaskStatusEnum.CANCELLED)
        
        return {
            "total": len(self._tasks),
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "max_concurrent": self.max_concurrent,
            "queue_size": self._queue.qsize()
        }


# 全局任务队列实例
_global_queue: Optional[TaskQueue] = None


def get_global_task_queue(max_concurrent: int = 3) -> TaskQueue:
    """获取全局任务队列实例"""
    global _global_queue
    if _global_queue is None:
        _global_queue = TaskQueue(max_concurrent=max_concurrent)
    return _global_queue


async def init_global_task_queue(max_concurrent: int = 3) -> TaskQueue:
    """初始化并启动全局任务队列"""
    queue = get_global_task_queue(max_concurrent)
    await queue.start()
    return queue
