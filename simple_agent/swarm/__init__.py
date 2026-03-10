"""
Swarm - 群体智能系统

提供多 Agent 协作能力：
- 任务分解和调度
- 共享黑板通信
- 消息总线
- 协作模式
"""

from .orchestrator import SwarmOrchestrator, SwarmResult, SwarmOrchestratorBuilder
from .blackboard import Blackboard, Change
from .message_bus import MessageBus
from .task_scheduler import Task, TaskScheduler, TaskDecomposer, TaskGraph, TaskStatus, TaskSchedulerV2
from .collaboration_patterns import (
    PairProgramming,
    SwarmBrainstorming,
    MarketBasedAllocation,
    CodeReviewLoop,
    CollaborationResult,
)
from .scaling import DynamicScaling, AutoScalingOrchestrator, AgentFactory, ScalingMetrics
from .scheduler.workflow import Workflow, WorkflowStep
from .scheduler.workflow_parallel import ParallelWorkflow, ParallelStep, create_parallel_workflow

__all__ = [
    "SwarmOrchestrator",
    "SwarmResult",
    "SwarmOrchestratorBuilder",
    "Task",
    "Blackboard",
    "Change",
    "MessageBus",
    "TaskScheduler",
    "TaskSchedulerV2",
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
