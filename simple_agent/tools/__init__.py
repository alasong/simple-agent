"""
内置工具插件 - 插件型按需加载

导入即注册到资源仓库

设计理念:
- 最小化原则：只做 bash 做不到的事
- 环境优先：优先使用系统已有命令
- 不破坏用户习惯：通过 BashTool 调用用户熟悉的工具
- 按需加载：只导入常用工具，其他工具使用时自动发现

常用工具（默认导入）:
- BashTool: 执行 shell 命令
- ReadFileTool: 读取文件
- WriteFileTool: 写入文件

其他工具（按需加载）:
- Agent 工具：InvokeAgentTool, CreateWorkflowTool, ListAgentsTool
- 网络工具：WebSearchTool, HttpTool
- 补充工具：SupplementTool, ExplainReasonTool
- 推理工具：TreeOfThoughtTool, IterativeOptimizerTool, SwarmVotingTool, MultiPathOptimizerTool
"""

# 核心工具 (80% 场景) - 默认导入
from .file import ReadFileTool, WriteFileTool
from .bash_tool import BashTool

__all__ = [
    # 核心工具 - 默认导入
    "BashTool",
    "ReadFileTool",
    "WriteFileTool",
]

# 注意：其他工具不再显式导出，改为通过 ToolRegistry 按需加载
# 使用方式：
#   from simple_agent.core.tool_registry import get_tool
#   tool = get_tool("WebSearchTool")

