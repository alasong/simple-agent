"""
Swarm - 群体智能系统

提供多 Agent 协作能力：
- 任务分解和调度
- 共享黑板通信
- 消息总线
- 协作模式
"""

from .orchestrator import SwarmOrchestrator, SwarmResult, Task
from .blackboard import Blackboard, Change
from .message_bus import MessageBus
from .scheduler import TaskScheduler, TaskDecomposer, TaskGraph, TaskStatus
from .collaboration_patterns import (
    PairProgramming,
    SwarmBrainstorming,
    MarketBasedAllocation,
    CodeReviewLoop,
    CollaborationResult,
)
from .scaling import DynamicScaling, AutoScalingOrchestrator, AgentFactory, ScalingMetrics

__all__ = [
    "SwarmOrchestrator",
    "SwarmResult",
    "Task",
    "Blackboard",
    "Change",
    "MessageBus",
    "TaskScheduler",
    "TaskDecomposer",
    "TaskGraph",
    "TaskStatus",
    "PairProgramming",
    "SwarmBrainstorming",
    "MarketBasedAllocation",
    "CodeReviewLoop",
    "CollaborationResult",
    "DynamicScaling",
    "AutoScalingOrchestrator",
    "AgentFactory",
    "ScalingMetrics",
]
