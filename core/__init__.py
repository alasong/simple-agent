"""
最小 Agent 框架核心

架构:
    ResourceRepository (资源仓库)
        ├── 工具仓库
        ├── LLM 仓库
        └── Agent 注册表
    
    create_agent (创建 Agent)
        └── 从仓库抽取资源 + 需求 → 新 Agent
    
    Workflow (多 Agent 协作)
        └── 顺序执行多个 Agent
"""

from .tool import BaseTool, ToolResult, ToolRegistry
from .memory import Memory
from .llm import LLMInterface, OpenAILLM
from .agent import Agent, AgentInfo
from .resource import (
    ResourceRepository, repo,
    ToolEntry, LLMEntry,
    tool, register_llm
)
from .factory import (
    create_agent, update_prompt, get_agent, list_agents,
    AgentGenerator
)
from .workflow import Workflow, WorkflowStep, StepResult, ResultType, create_workflow, generate_workflow
from .workflow_generator import WorkflowGenerator

# 模块化组件（架构改进）
from .agent_core import AgentCore
from .agent_serializer import AgentSerializer
from .agent_error_enhancer import AgentErrorEnhancer
from .agent_cloner import AgentCloner
from .container import DIContainer, get_container
from .strategies import (
    ExecutionStrategy,
    ExecutionResult,
    DirectStrategy,
    PlanReflectStrategy,
    TreeOfThoughtStrategy,
    StrategyFactory
)
from .async_adapter import AsyncAgentAdapter

# 调试支持
from .debug import (
    enable_debug,
    disable_debug,
    get_debug_summary,
    print_debug_summary,
    DebugTracker,
    tracker
)

# 增强功能 (阶段 1)
from .memory_enhanced import EnhancedMemory, Experience
from .reasoning_modes import TreeOfThought, ReflectionLoop
from .skill_learning import SkillLibrary, Skill
from .agent_enhanced import EnhancedAgent

__all__ = [
    # 核心组件
    "BaseTool",
    "ToolResult",
    "ToolRegistry",
    "Memory",
    "LLMInterface",
    "OpenAILLM",
    "Agent",
    "AgentInfo",
    
    # 模块化组件
    "AgentCore",
    "AgentSerializer",
    "AgentErrorEnhancer",
    "AgentCloner",
    
    # 依赖注入
    "DIContainer",
    "get_container",
    
    # 策略模式
    "ExecutionStrategy",
    "ExecutionResult",
    "DirectStrategy",
    "PlanReflectStrategy",
    "TreeOfThoughtStrategy",
    "StrategyFactory",
    
    # 异步适配
    "AsyncAgentAdapter",
    
    # 资源仓库
    "ResourceRepository",
    "repo",
    "ToolEntry",
    "LLMEntry",
    "tool",
    "register_llm",
    
    # Agent 创建
    "create_agent",
    "update_prompt",
    "get_agent",
    "list_agents",
    "AgentGenerator",
    "EnhancedAgent",
    
    # Workflow
    "Workflow",
    "WorkflowStep",
    "StepResult",
    "ResultType",
    "create_workflow",
    "generate_workflow",
    "WorkflowGenerator",
    
    # 增强功能 (阶段 1)
    "EnhancedMemory",
    "Experience",
    "TreeOfThought",
    "ReflectionLoop",
    "SkillLibrary",
    "Skill",
    
    # 调试支持
    "enable_debug",
    "disable_debug",
    "get_debug_summary",
    "print_debug_summary",
    "DebugTracker",
    "tracker",
]
