"""
Task Scheduler Tests - 定时任务调度器测试

运行:
    python -m pytest tests/test_task_scheduler.py -v
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from core.task_scheduler import (
    TaskScheduler,
    ScheduledTask,
    ScheduleType,
    CronParser,
)


class TestCronParser:
    """测试 Cron 表达式解析器"""

    def test_parse_every_minute(self):
        """测试每分钟执行"""
        minutes = CronParser.parse("* * * * *")
        assert len(minutes) == 60
        assert minutes == list(range(60))

    def test_parse_every_5_minutes(self):
        """测试每 5 分钟执行"""
        minutes = CronParser.parse("*/5 * * * *")
        assert len(minutes) == 12
        assert minutes == [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]

    def test_parse_range(self):
        """测试范围"""
        minutes = CronParser.parse("0-30 * * * *")
        assert len(minutes) == 31
        assert minutes == list(range(31))

    def test_parse_single_minute(self):
        """测试单个分钟"""
        minutes = CronParser.parse("30 * * * *")
        assert minutes == [30]

    def test_get_next_run(self):
        """测试下次执行时间计算"""
        # 每 5 分钟执行
        next_run = CronParser.get_next_run("*/5 * * * *")
        assert next_run.second == 0
        assert next_run.microsecond == 0

    def test_invalid_cron_expression(self):
        """测试无效 cron 表达式"""
        with pytest.raises(ValueError):
            CronParser.parse("invalid")


class TestScheduledTask:
    """测试定时任务"""

    def test_create_once_task(self):
        """创建一次性任务"""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as storage_dir:
            storage_path = os.path.join(storage_dir, "tasks.json")
            scheduler = TaskScheduler(storage_path)

            run_at = datetime.now() + timedelta(minutes=1)
            task_id = scheduler.create_once_task(
                name="测试任务",
                agent_name="developer",
                input="测试输入",
                run_at=run_at,
                description="测试描述",
            )

            task = scheduler.get_task(task_id)
            assert task is not None
            assert task.name == "测试任务"
            assert task.schedule_type == ScheduleType.ONCE
            assert task.enabled is True

    def test_create_interval_task(self):
        """创建周期性任务（间隔）"""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as storage_dir:
            storage_path = os.path.join(storage_dir, "tasks.json")
            scheduler = TaskScheduler(storage_path)

            task_id = scheduler.create_interval_task(
                name="周期任务",
                agent_name="developer",
                input="测试输入",
                interval_seconds=3600,  # 每小时
                description="每小时执行一次",
            )

            task = scheduler.get_task(task_id)
            assert task is not None
            assert task.schedule_type == ScheduleType.INTERVAL
            assert task.interval_seconds == 3600

    def test_create_cron_task(self):
        """创建周期性任务（cron）"""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as storage_dir:
            storage_path = os.path.join(storage_dir, "tasks.json")
            scheduler = TaskScheduler(storage_path)

            task_id = scheduler.create_cron_task(
                name="Cron 任务",
                agent_name="developer",
                input="测试输入",
                cron_expression="*/5 * * * *",  # 每 5 分钟
                description="每 5 分钟执行一次",
            )

            task = scheduler.get_task(task_id)
            assert task is not None
            assert task.schedule_type == ScheduleType.CRON
            assert task.cron_expression == "*/5 * * * *"

    def test_list_tasks(self):
        """列出任务"""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as storage_dir:
            storage_path = os.path.join(storage_dir, "tasks.json")
            scheduler = TaskScheduler(storage_path)

            # 创建多个任务
            for i in range(3):
                scheduler.create_interval_task(
                    name=f"任务{i}",
                    agent_name="developer",
                    input="测试",
                    interval_seconds=60,
                )

            tasks = scheduler.list_tasks()
            assert len(tasks) == 3

    def test_enable_disable_task(self):
        """启用/禁用任务"""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as storage_dir:
            storage_path = os.path.join(storage_dir, "tasks.json")
            scheduler = TaskScheduler(storage_path)

            task_id = scheduler.create_interval_task(
                name="测试任务",
                agent_name="developer",
                input="测试",
                interval_seconds=60,
            )

            # 禁用
            assert scheduler.disable_task(task_id) is True
            task = scheduler.get_task(task_id)
            assert task.enabled is False

            # 启用
            assert scheduler.enable_task(task_id) is True
            task = scheduler.get_task(task_id)
            assert task.enabled is True

    def test_delete_task(self):
        """删除任务"""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as storage_dir:
            storage_path = os.path.join(storage_dir, "tasks.json")
            scheduler = TaskScheduler(storage_path)

            task_id = scheduler.create_interval_task(
                name="测试任务",
                agent_name="developer",
                input="测试",
                interval_seconds=60,
            )

            # 删除
            assert scheduler.delete_task(task_id) is True
            assert scheduler.get_task(task_id) is None

    def test_persistence(self):
        """测试持久化"""
        import tempfile
        import os

        storage_dir = tempfile.mkdtemp()
        try:
            storage_path = os.path.join(storage_dir, "tasks.json")

            # 创建调度器并添加任务
            scheduler1 = TaskScheduler(storage_path)
            task_id = scheduler1.create_interval_task(
                name="持久化测试",
                agent_name="developer",
                input="测试输入",
                interval_seconds=300,
                description="测试描述",
            )

            # 停止调度器
            scheduler1.stop()

            # 创建新调度器实例，应该从文件加载任务
            scheduler2 = TaskScheduler(storage_path)
            task = scheduler2.get_task(task_id)

            assert task is not None
            assert task.name == "持久化测试"
            assert task.interval_seconds == 300
        finally:
            import shutil
            shutil.rmtree(storage_dir, ignore_errors=True)

    def test_scheduler_start_stop(self):
        """测试启动/停止调度器"""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as storage_dir:
            storage_path = os.path.join(storage_dir, "tasks.json")
            scheduler = TaskScheduler(storage_path)

            # 启动
            scheduler.start()
            assert scheduler._running is True

            # 停止
            scheduler.stop()
            assert scheduler._running is False


class TestSchedulerIntegration:
    """测试调度器集成"""

    def test_task_execution_callback(self):
        """测试任务执行回调"""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as storage_dir:
            storage_path = os.path.join(storage_dir, "tasks.json")
            scheduler = TaskScheduler(storage_path)

            # 创建任务
            task_id = scheduler.create_interval_task(
                name="回调测试",
                agent_name="developer",
                input="测试",
                interval_seconds=1,  # 1 秒执行一次（用于测试）
            )

            # 记录回调执行
            executed = []

            def callback(task):
                executed.append(task.task_id)

            scheduler.register_callback(task_id, callback)

            # 手动执行一次
            task = scheduler.get_task(task_id)
            scheduler._execute_task(task)

            assert len(executed) == 1
            assert executed[0] == task_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
