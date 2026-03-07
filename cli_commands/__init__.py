"""
CLI 命令处理模块

将 CLI 命令按功能模块化，便于维护和扩展。

模块划分:
- session_cmds: 会话管理命令
- agent_cmds: Agent 管理命令
- workflow_cmds: 工作流命令
- debug_cmds: 调试命令
- task_cmds: 任务管理命令
"""

from typing import Dict, Type, List, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class CommandResult:
    """命令执行结果"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    
    @classmethod
    def ok(cls, message: str, data: Optional[Any] = None) -> 'CommandResult':
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def error(cls, message: str, error: Optional[str] = None) -> 'CommandResult':
        return cls(success=False, message=message, error=error)


class CommandHandler(ABC):
    """命令处理器基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """命令名称"""
        pass
    
    @property
    def description(self) -> str:
        """命令描述"""
        return ""
    
    @property
    def usage(self) -> str:
        """使用说明"""
        return f"/{self.name}"
    
    @abstractmethod
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        """执行命令
        
        Args:
            args: 命令参数列表
            context: 执行上下文（包含 agent、session 等）
        
        Returns:
            CommandResult: 执行结果
        """
        pass
    
    def parse_args(self, args: List[str]) -> Dict[str, Any]:
        """解析命令参数（可选覆写）
        
        默认实现：简单分割参数
        """
        return {"args": args}


# 延迟导入各命令模块，避免循环依赖
def get_session_commands() -> List[CommandHandler]:
    """获取会话管理命令"""
    from .session_cmds import SessionCommand, SessionListCommand, SessionNewCommand, SessionDelCommand
    return [
        SessionCommand(),
        SessionListCommand(),
        SessionNewCommand(),
        SessionDelCommand()
    ]


def get_agent_commands() -> List[CommandHandler]:
    """获取 Agent 管理命令"""
    from .agent_cmds import AgentNewCommand, AgentUpdateCommand, AgentSwitchCommand, \
                           AgentListCommand, AgentInfoCommand, AgentSaveCommand, AgentLoadCommand
    return [
        AgentNewCommand(),
        AgentUpdateCommand(),
        AgentSwitchCommand(),
        AgentListCommand(),
        AgentInfoCommand(),
        AgentSaveCommand(),
        AgentLoadCommand()
    ]


def get_workflow_commands() -> List[CommandHandler]:
    """获取工作流命令"""
    from .workflow_cmds import WorkflowCommand
    return [WorkflowCommand()]


def get_debug_commands() -> List[CommandHandler]:
    """获取调试命令"""
    from .debug_cmds import DebugCommand, DebugSummaryCommand, DebugStatsCommand
    return [
        DebugCommand(),
        DebugSummaryCommand(),
        DebugStatsCommand()
    ]


def get_task_commands() -> List[CommandHandler]:
    """获取任务管理命令"""
    from .task_cmds import BgCommand, TasksCommand, ResultCommand, CancelCommand, TaskStatsCommand
    return [
        BgCommand(),
        TasksCommand(),
        ResultCommand(),
        CancelCommand(),
        TaskStatsCommand()
    ]


def get_all_commands() -> List[CommandHandler]:
    """获取所有命令"""
    commands = []
    commands.extend(get_session_commands())
    commands.extend(get_agent_commands())
    commands.extend(get_workflow_commands())
    commands.extend(get_debug_commands())
    commands.extend(get_task_commands())
    return commands


__all__ = [
    'CommandResult',
    'CommandHandler',
    'get_all_commands',
    'get_session_commands',
    'get_agent_commands',
    'get_workflow_commands',
    'get_debug_commands',
    'get_task_commands',
]
