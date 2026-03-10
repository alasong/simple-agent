"""
Services Layer - 本地服务化平台

包含:
- API 服务 (FastAPI)
- 守护进程管理
- WebSocket 实时推送
- 会话持久化存储
- 定时任务调度器
"""

# API 服务
from simple_agent.services.api import (
    create_app,
    get_app,
    app,
    get_auth,
    init_auth,
    APIAuth,
    get_tracker,
    init_tracker,
)

# 定时任务调度器
from simple_agent.services.task_scheduler import (
    get_scheduler,
    init_scheduler,
    TaskScheduler,
    ScheduledTask,
    ScheduleType,
)

# 守护进程
from simple_agent.services.daemon import (
    get_daemon,
    init_daemon,
    DaemonManager,
)

# WebSocket
from simple_agent.services.websocket import (
    ConnectionManager,
    WebSocketMessage,
)

# 会话存储
from simple_agent.services.session_store import (
    get_store,
    init_store,
    SessionStore,
)

__all__ = [
    # API
    "create_app",
    "get_app",
    "app",
    "get_auth",
    "init_auth",
    "APIAuth",
    "get_tracker",
    "init_tracker",
    # Scheduler
    "get_scheduler",
    "init_scheduler",
    "TaskScheduler",
    "ScheduledTask",
    "ScheduleType",
    # Daemon
    "get_daemon",
    "init_daemon",
    "DaemonManager",
    # WebSocket
    "ConnectionManager",
    "WebSocketMessage",
    # Session
    "get_store",
    "init_store",
    "SessionStore",
]
