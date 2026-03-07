#!/usr/bin/env python3
"""
测试后台任务执行功能
"""

import asyncio
import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.task_handle import TaskHandle, TaskStatus, TaskStatusEnum, generate_task_id
from core.task_queue import TaskQueue, get_global_task_queue


def print_test(name: str, passed: bool, details: str = ""):
    """打印测试结果"""
    status = "✓" if passed else "✗"
    print(f"{status} {name:35} {details}")


class TestTaskHandle:
    """测试 TaskHandle"""
    
    async def test_create_handle(self):
        """测试创建任务句柄"""
        handle = TaskHandle("test_1")
        assert handle.id == "test_1"
        assert handle.is_pending
        assert not handle.is_running
        assert not handle.is_done
        print_test("创建任务句柄", True)
    
    async def test_update_status(self):
        """测试更新任务状态"""
        handle = TaskHandle("test_2")
        
        # 初始状态
        assert handle.status.status == TaskStatusEnum.PENDING
        
        # 更新为运行中
        await handle.update_status(TaskStatusEnum.RUNNING, progress="执行中...")
        assert handle.status.status == TaskStatusEnum.RUNNING
        assert handle.is_running
        assert handle.status.started_at is not None
        
        # 更新为完成
        await handle.update_status(
            TaskStatusEnum.COMPLETED,
            progress="完成",
            result="test_result"
        )
        assert handle.status.status == TaskStatusEnum.COMPLETED
        assert handle.is_done
        assert handle.status.result == "test_result"
        assert handle.status.completed_at is not None
        
        print_test("更新任务状态", True)
    
    async def test_get_result(self):
        """测试获取结果（阻塞）"""
        handle = TaskHandle("test_3")
        
        # 启动一个后台任务设置结果
        async def set_result_later():
            await asyncio.sleep(0.1)
            await handle.update_status(
                TaskStatusEnum.COMPLETED,
                result="async_result"
            )
        
        asyncio.create_task(set_result_later())
        
        # 等待结果
        result = await handle.result(timeout=1.0)
        assert result == "async_result"
        
        print_test("获取结果（阻塞）", True)
    
    async def test_cancel(self):
        """测试取消任务"""
        handle = TaskHandle("test_4")
        
        # 取消
        success = await handle.cancel()
        assert success is True
        assert handle.status.status == TaskStatusEnum.CANCELLED
        
        # 重复取消应该失败
        success2 = await handle.cancel()
        assert success2 is False
        
        print_test("取消任务", True)
    
    async def test_check_cancelled(self):
        """测试检查取消状态"""
        handle = TaskHandle("test_5")
        
        # 初始未取消
        assert not handle.check_cancelled()
        
        # 取消后
        await handle.cancel()
        assert handle.check_cancelled()
        
        print_test("检查取消状态", True)
    
    async def test_elapsed_time(self):
        """测试执行时间计算"""
        handle = TaskHandle("test_6")
        
        # 未开始时为 0
        assert handle.get_elapsed_time() == 0.0
        
        # 运行中
        await handle.update_status(TaskStatusEnum.RUNNING)
        await asyncio.sleep(0.1)
        elapsed = handle.get_elapsed_time()
        assert elapsed >= 0.1
        
        print_test("执行时间计算", True)


class TestTaskQueue:
    """测试 TaskQueue"""
    
    async def test_create_queue(self):
        """测试创建队列"""
        queue = TaskQueue(max_concurrent=2)
        assert queue.max_concurrent == 2
        assert queue.get_stats()["total"] == 0
        print_test("创建队列", True)
    
    async def test_submit_and_execute(self):
        """测试提交并执行任务"""
        queue = TaskQueue(max_concurrent=2)
        await queue.start()
        
        result_container = []
        
        async def simple_task():
            await asyncio.sleep(0.05)
            result_container.append("done")
            return "result"
        
        # 使用工厂函数创建协程，避免提前创建
        async def task_factory():
            return await queue.submit(
                input_text="测试任务",
                coro=simple_task()
            )
        
        handle = await task_factory()
        
        # 等待任务完成
        await asyncio.sleep(0.2)
        
        assert len(result_container) == 1
        assert handle.status.status == TaskStatusEnum.COMPLETED
        
        await queue.stop()
        print_test("提交并执行任务", True)
    
    async def test_concurrency_limit(self):
        """测试并发限制"""
        queue = TaskQueue(max_concurrent=2)
        await queue.start()
        
        running_count = 0
        max_running = 0
        lock = asyncio.Lock()
        
        async def tracking_task(task_id):
            nonlocal running_count, max_running
            async with lock:
                running_count += 1
                max_running = max(max_running, running_count)
            await asyncio.sleep(0.1)
            async with lock:
                running_count -= 1
            return task_id
        
        # 提交 5 个任务
        async def create_task_coro(i):
            return await queue.submit(
                input_text=f"任务{i}",
                coro=tracking_task(i)
            )
        
        # 并发提交任务
        handles = await asyncio.gather(*[create_task_coro(i) for i in range(5)])
        
        # 等待所有任务完成
        await asyncio.sleep(0.5)
        
        # 最大并发数不应超过限制
        assert max_running <= 2, f"最大并发 {max_running} 超过限制 2"
        
        await queue.stop()
        print_test("并发限制", True, f"实际最大并发：{max_running}")
    
    async def test_task_status(self):
        """测试任务状态跟踪"""
        queue = TaskQueue(max_concurrent=2)
        await queue.start()
        
        async def quick_task():
            await asyncio.sleep(0.05)
            return "done"
        
        handle = await queue.submit(
            input_text="状态测试",
            coro=quick_task()
        )
        
        # 等待完成
        await asyncio.sleep(0.2)
        
        status = await queue.get_status(handle.id)
        assert status is not None
        assert status.status == TaskStatusEnum.COMPLETED
        assert status.input == "状态测试"
        
        await queue.stop()
        print_test("任务状态跟踪", True)
    
    async def test_list_tasks(self):
        """测试列出任务"""
        queue = TaskQueue(max_concurrent=2)
        await queue.start()
        
        async def task():
            await asyncio.sleep(0.05)
            return "done"
        
        # 提交 3 个任务
        for i in range(3):
            await queue.submit(input_text=f"任务{i}", coro=task())
        
        await asyncio.sleep(0.3)
        
        tasks = await queue.list_tasks()
        assert len(tasks) == 3
        
        # 过滤已完成
        completed = await queue.list_tasks(status_filter="done")
        assert len(completed) == 3
        
        # 过滤运行中（应该没有）
        running = await queue.list_tasks(status_filter="active")
        assert len(running) == 0
        
        await queue.stop()
        print_test("列出任务", True, f"共{len(tasks)}个")
    
    async def test_list_tasks(self):
        """测试列出任务"""
        queue = TaskQueue(max_concurrent=2)
        await queue.start()
        
        async def task():
            await asyncio.sleep(0.05)
            return "done"
        
        # 提交 3 个任务
        for i in range(3):
            await queue.submit(input_text=f"任务{i}", coro=task())
        
        await asyncio.sleep(0.3)
        
        tasks = await queue.list_tasks()
        assert len(tasks) == 3
        
        # 过滤已完成
        completed = await queue.list_tasks(status_filter="done")
        assert len(completed) == 3
        
        # 过滤运行中（应该没有）
        running = await queue.list_tasks(status_filter="active")
        assert len(running) == 0
        
        await queue.stop()
        print_test("列出任务", True, f"共{len(tasks)}个")
    
    async def test_cancel_task(self):
        """测试取消任务"""
        queue = TaskQueue(max_concurrent=2)
        await queue.start()
        
        async def long_task():
            await asyncio.sleep(10)  # 长时间任务
            return "done"
        
        handle = await queue.submit(
            input_text="长任务",
            coro=long_task()
        )
        
        # 立即取消
        await asyncio.sleep(0.05)
        success = await queue.cancel(handle.id)
        
        # 等待一下看取消效果
        await asyncio.sleep(0.1)
        
        assert success is True
        assert handle.status.status == TaskStatusEnum.CANCELLED
        
        await queue.stop(wait=False)
        print_test("取消任务", True)
    
    async def test_get_stats(self):
        """测试统计信息"""
        queue = TaskQueue(max_concurrent=3)
        await queue.start()
        
        async def task():
            await asyncio.sleep(0.05)
            return "done"
        
        # 提交 5 个任务
        for i in range(5):
            await queue.submit(input_text=f"任务{i}", coro=task())
        
        await asyncio.sleep(0.3)
        
        stats = queue.get_stats()
        assert stats["total"] == 5
        assert stats["completed"] == 5
        assert stats["max_concurrent"] == 3
        
        await queue.stop()
        print_test("统计信息", True, f"总计{stats['total']},完成{stats['completed']}")


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("后台任务执行测试")
    print("="*60)
    
    # TestTaskHandle
    print("\n[TaskHandle 测试]")
    test_handle = TestTaskHandle()
    await test_handle.test_create_handle()
    await test_handle.test_update_status()
    await test_handle.test_get_result()
    await test_handle.test_cancel()
    await test_handle.test_check_cancelled()
    await test_handle.test_elapsed_time()
    
    # TestTaskQueue
    print("\n[TaskQueue 测试]")
    test_queue = TestTaskQueue()
    await test_queue.test_create_queue()
    await test_queue.test_submit_and_execute()
    await test_queue.test_concurrency_limit()
    await test_queue.test_task_status()
    await test_queue.test_list_tasks()
    await test_queue.test_cancel_task()
    await test_queue.test_get_stats()
    
    print("\n" + "="*60)
    print("✓ 全部测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
