"""
内置工具插件

导入即注册到资源仓库

设计理念:
- 最小化原则：只做 bash 做不到的事
- 环境优先：优先使用系统已有命令
- 不破坏用户习惯：通过 BashTool 调用用户熟悉的工具
"""

# 核心工具 (80% 场景)
from .file import ReadFileTool, WriteFileTool
from .bash_tool import BashTool

# Agent 协作工具
from .agent_tools import InvokeAgentTool, CreateWorkflowTool, ListAgentsTool

# 网络工具 (bash 难以处理的)
from .web_search_tool import WebSearchTool
from .http_tool import HttpTool

# 补充工具 (LLM 驱动的解释/补充)
from .supplement import SupplementTool, ExplainReasonTool

__all__ = [
    # 核心工具
    "BashTool",
    "ReadFileTool",
    "WriteFileTool",
    # Agent 工具
    "InvokeAgentTool",
    "CreateWorkflowTool",
    "ListAgentsTool",
    # 网络工具
    "WebSearchTool",
    "HttpTool",
    # 补充工具
    "SupplementTool",
    "ExplainReasonTool",
]
