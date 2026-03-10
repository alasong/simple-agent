"""
Simple Agent - 多 Agent 协作系统

一个支持群体智能、任务自动分解、智能调度和多种协作模式的 Agent 系统。
"""

__version__ = "1.0.0"

# 核心组件
from simple_agent.core import (
    Agent,
    BaseTool,
    ToolResult,
    Memory,
    LLM,
    OpenAILLM,
    create_agent,
    get_agent,
)

# 群体智能
from simple_agent.swarm import (
    SwarmOrchestrator,
    TaskScheduler,
    Blackboard,
)

# 服务
from simple_agent.services import (
    create_app,
    get_scheduler,
)

__all__ = [
    # Core
    "Agent",
    "BaseTool",
    "ToolResult",
    "Memory",
    "LLM",
    "OpenAILLM",
    "create_agent",
    "get_agent",
    # Swarm
    "SwarmOrchestrator",
    "TaskScheduler",
    "Blackboard",
    # Services
    "create_app",
    "get_scheduler",
]
