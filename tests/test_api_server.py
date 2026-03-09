"""
API Tests - API 网关测试

运行:
    python -m pytest tests/test_api_server.py -v
"""

import pytest
import time
import threading
import requests
from unittest.mock import patch, MagicMock

# 测试用的 mock 数据
TEST_KEY_VALUE = "test-key-12345"  # 测试用 key，非真实密钥
TEST_TASK_ID = "test-task-001"


class TestAPIModels:
    """测试 Pydantic 数据模型"""

    def test_agent_run_request(self):
        """测试 AgentRunRequest 模型"""
        from core.api_models import AgentRunRequest, TaskStatus

        request = AgentRunRequest(
            agent_name="developer",
            input="分析当前目录",
            config={"timeout": 300, "debug": True}
        )

        assert request.agent_name == "developer"
        assert request.input == "分析当前目录"
        assert request.config["timeout"] == 300
        assert request.config["debug"] is True

    def test_task_status_response(self):
        """测试 TaskStatusResponse 模型"""
        from core.api_models import TaskStatusResponse, TaskStatus
        from datetime import datetime

        response = TaskStatusResponse(
            task_id=TEST_TASK_ID,
            status=TaskStatus.COMPLETED,
            output="测试结果",
            files=["output.txt"],
            duration=45.5
        )

        assert response.task_id == TEST_TASK_ID
        assert response.status == TaskStatus.COMPLETED
        assert response.output == "测试结果"
        assert len(response.files) == 1
        assert response.duration == 45.5

    def test_metrics_response(self):
        """测试 MetricsResponse 模型"""
        from core.api_models import MetricsResponse

        response = MetricsResponse(
            total_tasks=100,
            completed_tasks=95,
            failed_tasks=3,
            success_rate=0.95,
            avg_duration=45.2,
            total_tokens=150000,
            active_agents=2,
            uptime=86400.0
        )

        assert response.total_tasks == 100
        assert response.success_rate == 0.95
        assert response.active_agents == 2


class TestAPIAuth:
    """测试 API 认证"""

    def test_api_key_generation(self):
        """测试 API Key 生成"""
        from core.api_auth import APIAuth
        import tempfile
        import os

        # 使用临时文件存储
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            storage_path = f.name

        try:
            auth = APIAuth(storage_path)
            api_key = auth.generate_key("test-key", rate_limit=100)

            assert api_key.key.startswith("sk-")
            assert api_key.name == "test-key"
            assert api_key.rate_limit == 100
            assert api_key.is_active is True
        finally:
            if os.path.exists(storage_path):
                os.remove(storage_path)

    def test_api_key_validation(self):
        """测试 API Key 验证"""
        from core.api_auth import APIAuth
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            storage_path = f.name

        try:
            auth = APIAuth(storage_path)
            api_key = auth.generate_key("test-key")

            # 验证有效的 key
            is_valid, error = auth.validate_key(api_key.key)
            assert is_valid is True
            assert error is None

            # 验证无效的 key
            is_valid, error = auth.validate_key("sk-invalid")
            assert is_valid is False
            assert "无效" in error
        finally:
            if os.path.exists(storage_path):
                os.remove(storage_path)

    def test_rate_limiter(self):
        """测试速率限制器"""
        from core.api_auth import RateLimiter

        limiter = RateLimiter()
        test_key = "test-rate-limit"  # 测试用标识符

        # 前 5 次请求应该被允许
        for i in range(5):
            assert limiter.is_allowed(test_key, limit=5, window=60) is True

        # 第 6 次请求应该被拒绝
        assert limiter.is_allowed(test_key, limit=5, window=60) is False


class TestUsageTracker:
    """测试用量追踪"""

    def test_task_usage_tracking(self):
        """测试任务用量追踪"""
        from core.usage_tracker import UsageTracker
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            storage_path = f.name

        try:
            tracker = UsageTracker(storage_path)
            task_id = "test-task-001"

            # 开始追踪
            tracker.start_task(task_id, "developer")

            # 更新 token
            tracker.update_tokens(task_id, input_tokens=100, output_tokens=50)

            # 完成任务
            tracker.complete_task(task_id, "completed")

            # 获取用量
            usage = tracker.get_task_usage(task_id)
            assert usage is not None
            assert usage.task_id == task_id
            assert usage.agent_name == "developer"
            assert usage.total_tokens == 150
            assert usage.status == "completed"
        finally:
            if os.path.exists(storage_path):
                os.remove(storage_path)

    def test_total_usage(self):
        """测试总用量统计"""
        from core.usage_tracker import UsageTracker
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            storage_path = f.name

        try:
            tracker = UsageTracker(storage_path)

            # 添加多个任务
            for i in range(5):
                task_id = f"test-task-{i}"
                tracker.start_task(task_id, "developer")
                tracker.update_tokens(task_id, 100, 50)
                tracker.complete_task(task_id, "completed")

            # 获取总用量
            total = tracker.get_total_usage()
            assert total["total_tasks"] >= 5
            assert total["completed_tasks"] >= 5
            assert total["success_rate"] == 1.0
        finally:
            if os.path.exists(storage_path):
                os.remove(storage_path)


class TestSessionStore:
    """测试会话存储"""

    def test_create_and_get_task(self):
        """测试创建和获取任务"""
        from core.session_store import SessionStore
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as storage_dir:
            store = SessionStore(storage_dir)
            task_id = store.create_task(
                task_type="agent",
                agent_name="developer",
                input="测试任务"
            )

            task = store.get_task(task_id)
            assert task is not None
            assert task.agent_name == "developer"
            assert task.input == "测试任务"
            assert task.status.value == "pending"

    def test_update_task_status(self):
        """测试更新任务状态"""
        from core.session_store import SessionStore
        from core.api_models import TaskStatus
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as storage_dir:
            store = SessionStore(storage_dir)
            task_id = store.create_task("agent", agent_name="developer")

            # 更新状态为运行中
            store.update_status(task_id, TaskStatus.RUNNING)
            task = store.get_task(task_id)
            assert task.status == TaskStatus.RUNNING

            # 更新状态为已完成
            store.update_status(task_id, TaskStatus.COMPLETED)
            task = store.get_task(task_id)
            assert task.status == TaskStatus.COMPLETED
            assert task.duration > 0

    def test_list_tasks(self):
        """测试列出任务"""
        from core.session_store import SessionStore
        from core.api_models import TaskStatus
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as storage_dir:
            store = SessionStore(storage_dir)

            # 创建多个任务
            for i in range(5):
                store.create_task("agent", agent_name="developer")

            tasks = store.list_tasks(limit=10)
            assert len(tasks) == 5


class TestDaemonManager:
    """测试守护进程管理"""

    def test_daemon_status(self):
        """测试守护进程状态检查"""
        from core.daemon import DaemonManager

        daemon = DaemonManager(name="test-daemon")
        status = daemon.status()

        assert "name" in status
        assert "running" in status
        assert "pid_file" in status
        assert "log_file" in status

    def test_pid_file_management(self):
        """测试 PID 文件管理"""
        from core.daemon import DaemonManager
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as data_dir:
            daemon = DaemonManager(name="test-daemon")
            daemon._data_dir = data_dir
            daemon._pid_file = os.path.join(data_dir, "test.pid")

            # 初始状态应该是未运行
            assert daemon.is_running() is False
            assert daemon.get_pid() is None


class TestAPIRoutes:
    """测试 API 路由（Mock 测试）"""

    def test_health_endpoint_mock(self):
        """测试健康检查端点（Mock）"""
        from core.api_server import create_app
        from fastapi.testclient import TestClient

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime" in data

    def test_agent_run_endpoint_mock(self):
        """测试 Agent 运行端点（Mock）"""
        # 这个测试比较复杂，因为涉及认证和后台任务
        # 简化为验证端点存在性
        from core.api_server import create_app
        from fastapi.testclient import TestClient

        app = create_app()
        client = TestClient(app)

        # 不带认证应该返回 401
        response = client.post(
            "/api/v1/agent/run",
            json={
                "agent_name": "developer",
                "input": "测试任务"
            }
        )
        assert response.status_code == 401  # 未授权

    def test_task_status_endpoint_mock(self):
        """测试任务状态端点（Mock）"""
        from core.api_server import create_app
        from core.api_models import TaskStatus
        from datetime import datetime
        from fastapi.testclient import TestClient

        # 访问 router 模块中的 _tasks
        import core.api_routes as api_routes

        # 添加一个测试任务
        test_task_id = "test-001"
        api_routes._tasks[test_task_id] = {
            "task_id": test_task_id,
            "type": "agent",
            "agent_name": "developer",
            "input": "测试",
            "status": TaskStatus.COMPLETED,
            "output": "测试结果",
            "files": [],
            "error": None,
            "created_at": datetime.now(),
            "started_at": datetime.now(),
            "completed_at": datetime.now(),
        }

        app = create_app()
        client = TestClient(app)

        response = client.get(f"/api/v1/task/{test_task_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == test_task_id
        assert data["status"] == "completed"
        assert data["output"] == "测试结果"


class TestWebSocketServer:
    """测试 WebSocket 服务器"""

    def test_connection_manager(self):
        """测试连接管理器"""
        from core.websocket_server import ConnectionManager, WebSocketMessage

        manager = ConnectionManager()

        # 初始状态
        assert manager.get_connection_count() == 0
        assert manager.get_subscriber_count("task-001") == 0

    def test_websocket_message(self):
        """测试 WebSocket 消息"""
        from core.websocket_server import WebSocketMessage
        import json

        message = WebSocketMessage(
            type="task_status",
            data={"task_id": "001", "status": "running"}
        )

        json_str = message.to_json()
        parsed = json.loads(json_str)

        assert parsed["type"] == "task_status"
        assert parsed["task_id"] == "001"
        assert "timestamp" in parsed


class TestWebUI:
    """测试 Web UI"""

    def test_webui_app_creation(self):
        """测试 Web UI 应用创建"""
        from webui.app import create_app
        from fastapi.testclient import TestClient

        app = create_app()
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_webui_api_status(self):
        """测试 Web UI API 状态端点"""
        from webui.app import create_app
        from fastapi.testclient import TestClient

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "timestamp" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
