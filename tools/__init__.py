"""
内置工具插件

导入即注册到资源仓库

设计理念:
- 最小化原则：只做 bash 做不到的事
- 环境优先：优先使用系统已有命令
- 不破坏用户习惯：通过 BashTool 调用用户熟悉的工具
"""

# 导入即注册
from .file import ReadFileTool, WriteFileTool
from .check import CheckFileExistsTool, CheckContentTool, CheckPythonSyntaxTool
from .agent_tools import InvokeAgentTool, CreateWorkflowTool, ListAgentsTool
from .web_search_tool import WebSearchTool
from .datetime_tool import DateTimeTool, GetCurrentDateTool
from .supplement import SupplementTool, ExplainReasonTool
from .output_manager import OutputManagerTool

# 系统工具
from .bash_tool import BashTool
from .env_tool import EnvTool
from .http_tool import HttpTool
from .math_tool import CalculatorTool

__all__ = [
    # 文件工具
    "ReadFileTool",
    "WriteFileTool",
    # 检查工具
    "CheckFileExistsTool",
    "CheckContentTool",
    "CheckPythonSyntaxTool",
    # Agent 工具
    "InvokeAgentTool",
    "CreateWorkflowTool",
    "ListAgentsTool",
    # 网络工具
    "WebSearchTool",
    # 时间工具
    "DateTimeTool",
    "GetCurrentDateTool",
    # 分析工具
    "SupplementTool",
    "ExplainReasonTool",
    # 输出工具
    "OutputManagerTool",
    # 系统工具
    "BashTool",
    "EnvTool",
    "HttpTool",
    "CalculatorTool",
]
