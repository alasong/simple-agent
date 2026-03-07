"""
共享黑板（Blackboard）

所有 Agent 可读写的共享信息空间，支持：
- 数据共享
- 状态同步
- 历史记录追踪
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from collections import OrderedDict


@dataclass
class Change:
    """黑板变更"""
    key: str
    value: Any
    agent_id: str
    timestamp: float
    task_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": str(self.value)[:200],  # 限制长度便于显示
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "task_id": self.task_id
        }


class Blackboard:
    """共享黑板 - 所有 Agent 可读写"""
    
    def __init__(self, max_history: int = 100):
        self.data: dict[str, Any] = {}
        self.history: list[Change] = []
        self.max_history = max_history
        self._lock = asyncio.Lock()
        self._subscribers: dict[str, list[callable]] = {}
    
    def write(self, key: str, value: Any, agent_id: str, task_id: Optional[str] = None):
        """写入数据"""
        change = Change(
            key=key,
            value=value,
            agent_id=agent_id,
            timestamp=time.time(),
            task_id=task_id
        )
        
        self.data[key] = value
        self.history.append(change)
        
        # 限制历史记录长度
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def read(self, key: str) -> Any:
        """读取数据"""
        return self.data.get(key)
    
    def get(self, key: str, default: Any = None) -> Any:
        """读取数据（带默认值）"""
        return self.data.get(key, default)
    
    def get_all(self) -> dict[str, Any]:
        """获取所有数据"""
        return self.data.copy()
    
    def get_context(self, task: 'Task') -> str:
        """为任务准备上下文"""
        if not task or not task.dependencies:
            return ""
        
        relevant = []
        for dep in task.dependencies:
            if dep in self.data:
                value = self.data[dep]
                relevant.append(f"{dep}: {str(value)[:200]}")
        
        if not relevant:
            return ""
        
        return "依赖任务结果:\n" + "\n".join(relevant)
    
    def update(self, task_id: str, result: str, agent_id: str):
        """更新任务结果"""
        self.write(task_id, result, agent_id, task_id)
    
    def get_history(self, key: Optional[str] = None, limit: int = 10) -> list[dict]:
        """获取变更历史"""
        changes = self.history
        if key:
            changes = [c for c in changes if c.key == key]
        
        return [c.to_dict() for c in changes[-limit:]]
    
    def clear(self):
        """清空黑板"""
        self.data.clear()
        self.history.clear()
    
    def subscribe(self, key: str, callback: callable):
        """订阅某个键的变化"""
        if key not in self._subscribers:
            self._subscribers[key] = []
        self._subscribers[key].append(callback)
    
    async def notify_subscribers(self, key: str, value: Any):
        """通知订阅者"""
        for callback in self._subscribers.get(key, []):
            if asyncio.iscoroutinefunction(callback):
                await callback(key, value)
            else:
                callback(key, value)
    
    def __repr__(self) -> str:
        return f"<Blackboard data_keys={list(self.data.keys())} history_len={len(self.history)}>"
