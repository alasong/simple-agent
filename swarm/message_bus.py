"""
消息总线（Message Bus）

Agent 间异步消息传递系统，支持：
- 发布/订阅模式
- 主题路由
- 广播通信
- 事件驱动
"""

import asyncio
from typing import Callable, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import time
import json


@dataclass
class Message:
    """消息"""
    topic: str
    content: Any
    sender: str
    timestamp: float = field(default_factory=time.time)
    message_id: str = ""
    
    def __post_init__(self):
        if not self.message_id:
            import uuid
            self.message_id = str(uuid.uuid4())
    
    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "content": str(self.content)[:500],
            "sender": self.sender,
            "timestamp": self.timestamp,
            "message_id": self.message_id
        }


class MessageBus:
    """Agent 间通信总线"""
    
    def __init__(self):
        self.subscribers: dict[str, list[Callable]] = defaultdict(list)
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._message_history: list[Message] = []
        self._max_history = 100
    
    def subscribe(self, topic: str, callback: Callable):
        """订阅主题
        
        Args:
            topic: 主题名称，支持通配符 "*" 匹配所有
            callback: 回调函数，接收 (message: Message) 参数
        """
        self.subscribers[topic].append(callback)
    
    def unsubscribe(self, topic: str, callback: Callable):
        """取消订阅"""
        if topic in self.subscribers:
            self.subscribers[topic] = [c for c in self.subscribers[topic] if c != callback]
    
    async def publish(self, topic: str, content: Any, sender: str):
        """发布消息"""
        message = Message(topic=topic, content=content, sender=sender)
        await self.message_queue.put(message)
        self._message_history.append(message)
        
        # 限制历史记录
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history:]
    
    async def broadcast(self, content: Any, sender: str):
        """广播消息给所有订阅者"""
        await self.publish("__all__", content, sender)
    
    async def start(self):
        """启动消息处理循环"""
        self._running = True
        self._task = asyncio.create_task(self._process_messages())
    
    async def stop(self):
        """停止消息处理循环"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _process_messages(self):
        """处理消息队列"""
        while self._running:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self._dispatch(message)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[MessageBus] 处理消息失败：{e}")
    
    async def _dispatch(self, message: Message):
        """分发消息给订阅者"""
        callbacks = []
        
        # 精确匹配
        callbacks.extend(self.subscribers.get(message.topic, []))
        
        # 通配符匹配
        callbacks.extend(self.subscribers.get("__all__", []))
        
        # 并行执行所有回调
        async def invoke_callback(callback):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                print(f"[MessageBus] 回调执行失败 ({callback.__name__}): {e}")
        
        await asyncio.gather(*[invoke_callback(cb) for cb in callbacks], return_exceptions=True)
    
    def get_history(self, topic: Optional[str] = None, limit: int = 10) -> list[dict]:
        """获取消息历史"""
        messages = self._message_history
        if topic:
            messages = [m for m in messages if m.topic == topic]
        return [m.to_dict() for m in messages[-limit:]]
    
    def clear_history(self):
        """清空消息历史"""
        self._message_history.clear()
    
    @property
    def queue_size(self) -> int:
        """当前队列大小"""
        return self.message_queue.qsize()
    
    def __repr__(self) -> str:
        return f"<MessageBus queue_size={self.queue_size} subscribers={len(self.subscribers)}>"
