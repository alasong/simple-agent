"""
内置工具插件

导入即注册到资源仓库
"""

# 导入即注册
from .file import ReadFileTool, WriteFileTool
from .check import CheckFileExistsTool, CheckContentTool, CheckPythonSyntaxTool
from .agent_tools import InvokeAgentTool, CreateWorkflowTool, ListAgentsTool
from .web_search_tool import WebSearchTool

__all__ = [
    "ReadFileTool",
    "WriteFileTool",
    "CheckFileExistsTool",
    "CheckContentTool",
    "CheckPythonSyntaxTool",
    "InvokeAgentTool",
    "CreateWorkflowTool",
    "ListAgentsTool",
    "WebSearchTool",
]
