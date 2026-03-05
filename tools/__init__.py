"""
内置工具插件

导入即注册到资源仓库
"""

# 导入即注册
from .file import ReadFileTool, WriteFileTool
from .check import CheckFileExistsTool, CheckContentTool, CheckPythonSyntaxTool

__all__ = [
    "ReadFileTool",
    "WriteFileTool",
    "CheckFileExistsTool",
    "CheckContentTool",
    "CheckPythonSyntaxTool",
]
