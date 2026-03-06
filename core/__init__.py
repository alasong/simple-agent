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

# 增强功能 (阶段 1)
from .memory_enhanced import EnhancedMemory, Experience
from .reasoning_modes import TreeOfThought, ReflectionLoop
from .skill_learning import SkillLibrary, Skill

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
    
    # Workflow
    "Workflow",
    "WorkflowStep",
    "StepResult",
    "ResultType",
    "create_workflow",
    "generate_workflow",
    
    # 增强功能 (阶段 1)
    "EnhancedMemory",
    "Experience",
    "TreeOfThought",
    "ReflectionLoop",
    "SkillLibrary",
    "Skill",
]
