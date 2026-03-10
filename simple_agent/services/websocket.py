"""
WebSocket Server - WebSocket 实时推送

支持:
- 任务进度实时推送
- 客户端连接管理
- 广播消息
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Set, Any, Optional
from dataclasses import dataclass

from fastapi import WebSocket, WebSocketDisconnect, Query


@dataclass
class WebSocketMessage:
    """WebSocket 消息"""
    type: str  # "task_status", "progress", "log", "error"
    data: Dict[str, Any]
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps({
            "type": self.type,
            "timestamp": self.timestamp,
            **self.data
        })


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # task_id -> set of websockets
        self._task_subscriptions: Dict[str, Set[WebSocket]] = {}
        # all connected websockets
        self._active_connections: Set[WebSocket] = set()
        # websocket -> subscribed task_ids
        self._client_subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket, task_id: Optional[str] = None):
        """
        接受 WebSocket 连接

        Args:
            websocket: WebSocket 实例
            task_id: 可选的任务 ID，如果提供则自动订阅该任务
        """
        await websocket.accept()
        self._active_connections.add(websocket)
        self._client_subscriptions[websocket] = set()

        if task_id:
            await self.subscribe_to_task(websocket, task_id)

    def disconnect(self, websocket: WebSocket):
        """断开 WebSocket 连接"""
        self._active_connections.discard(websocket)

        # 清理订阅
        if websocket in self._client_subscriptions:
            for task_id in self._client_subscriptions[websocket]:
                if task_id in self._task_subscriptions:
                    self._task_subscriptions[task_id].discard(websocket)
            del self._client_subscriptions[websocket]

    async def subscribe_to_task(self, websocket: WebSocket, task_id: str):
        """订阅任务"""
        if task_id not in self._task_subscriptions:
            self._task_subscriptions[task_id] = set()
        self._task_subscriptions[task_id].add(websocket)
        self._client_subscriptions[websocket].add(task_id)

        # 发送确认消息
        await self.send_personal_message(
            websocket,
            WebSocketMessage(
                type="subscribed",
                data={"task_id": task_id}
            )
        )

    async def unsubscribe_from_task(self, websocket: WebSocket, task_id: str):
        """取消订阅任务"""
        if task_id in self._task_subscriptions:
            self._task_subscriptions[task_id].discard(websocket)
        if websocket in self._client_subscriptions:
            self._client_subscriptions[websocket].discard(task_id)

    async def send_personal_message(self, websocket: WebSocket, message: WebSocketMessage):
        """发送个人消息"""
        try:
            await websocket.send_text(message.to_json())
        except Exception as e:
            print(f"[WebSocket] 发送消息失败：{e}")

    async def broadcast_to_task(self, task_id: str, message: WebSocketMessage):
        """
        广播消息到订阅了指定任务的所有客户端

        Args:
            task_id: 任务 ID
            message: 消息
        """
        if task_id in self._task_subscriptions:
            # 复制到列表，避免迭代时修改
            websockets = list(self._task_subscriptions[task_id])
            for websocket in websockets:
                try:
                    await self.send_personal_message(websocket, message)
                except Exception:
                    # 发送失败，移除连接
                    self.disconnect(websocket)

    async def broadcast_task_status(self, task_id: str, status: str, **kwargs):
        """广播任务状态"""
        message = WebSocketMessage(
            type="task_status",
            data={
                "task_id": task_id,
                "status": status,
                **kwargs
            }
        )
        await self.broadcast_to_task(task_id, message)

    async def broadcast_progress(
        self,
        task_id: str,
        progress: float,
        message: Optional[str] = None,
        step: Optional[str] = None
    ):
        """广播任务进度"""
        message_obj = WebSocketMessage(
            type="progress",
            data={
                "task_id": task_id,
                "progress": progress,
                "message": message,
                "step": step
            }
        )
        await self.broadcast_to_task(task_id, message_obj)

    async def broadcast_log(self, task_id: str, log: str, level: str = "info"):
        """广播日志"""
        message = WebSocketMessage(
            type="log",
            data={
                "task_id": task_id,
                "log": log,
                "level": level
            }
        )
        await self.broadcast_to_task(task_id, message)

    def get_connection_count(self) -> int:
        """获取连接数"""
        return len(self._active_connections)

    def get_subscriber_count(self, task_id: str) -> int:
        """获取任务订阅数"""
        return len(self._task_subscriptions.get(task_id, set()))


# 全局管理器
_manager: Optional[ConnectionManager] = None


def get_manager() -> ConnectionManager:
    """获取全局管理器"""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


# WebSocket 路由助手
async def websocket_endpoint(
    websocket: WebSocket,
    task_id: Optional[str] = Query(None, description="任务 ID")
):
    """
    WebSocket 端点

    用法:
        ws://localhost:8000/ws
        ws://localhost:8000/ws?task_id=xxx
    """
    manager = get_manager()
    await manager.connect(websocket, task_id)

    try:
        while True:
            # 接收客户端消息（心跳、订阅控制等）
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "subscribe":
                    # 订阅任务
                    new_task_id = message.get("task_id")
                    if new_task_id:
                        await manager.subscribe_to_task(websocket, new_task_id)

                elif msg_type == "unsubscribe":
                    # 取消订阅
                    old_task_id = message.get("task_id")
                    if old_task_id:
                        await manager.unsubscribe_from_task(websocket, old_task_id)

                elif msg_type == "ping":
                    # 心跳
                    await manager.send_personal_message(
                        websocket,
                        WebSocketMessage(type="pong", data={})
                    )

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"[WebSocket] 异常：{e}")
        manager.disconnect(websocket)
