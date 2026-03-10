"""
会话管理命令

命令列表:
- /sessions - 列出所有会话
- /session - 显示当前会话
- /session <名称> - 切换会话
- /session new <名称> - 创建新会话
- /session del <名称> - 删除会话
- /clear - 清空当前会话记忆
"""

from typing import List, Dict, Any
from simple_agent.cli_commands import CommandHandler, CommandResult


class SessionListCommand(CommandHandler):
    """列出所有会话"""
    
    @property
    def name(self) -> str:
        return "sessions"
    
    @property
    def description(self) -> str:
        return "列出所有保存的会话"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            from simple_agent.core.session import list_sessions, get_session_info
            
            sessions = list_sessions()
            if not sessions:
                return CommandResult.ok("暂无保存的会话")
            
            lines = [f"\n{'='*60}"]
            lines.append(f"会话列表 ({len(sessions)} 个):")
            
            for s in sessions:
                info = get_session_info(s)
                if info:
                    agent_name = info.get('agent_name', 'Unknown')
                    msg_count = info.get('message_count', 0)
                    updated = info.get('updated_at', '')
                    lines.append(f"  - {s} (Agent: {agent_name}, 消息：{msg_count}, 更新：{updated})")
                else:
                    lines.append(f"  - {s}")
            
            lines.append(f"{'='*60}")
            return CommandResult.ok("\n".join(lines))
        
        except Exception as e:
            return CommandResult.error("获取会话列表失败", str(e))


class SessionCommand(CommandHandler):
    """会话管理命令（主命令）"""
    
    @property
    def name(self) -> str:
        return "session"
    
    @property
    def description(self) -> str:
        return "会话管理（显示/切换/创建/删除）"
    
    @property
    def usage(self) -> str:
        return "/session [new|del] <名称>"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            from simple_agent.core.session import switch_session, get_current_session, get_session_manager
            
            agent = context.get('current_agent') or context.get('cli_agent', {}).get('agent')
            
            if len(args) == 0:
                # 只显示当前会话
                current = get_current_session()
                return CommandResult.ok(f"当前会话：{current or 'default'}")
            
            elif len(args) == 1:
                # /session <name> - 切换会话
                if not agent:
                    return CommandResult.error("暂无 Agent")
                elif switch_session(args[0], agent):
                    return CommandResult.ok(f"已切换到会话：{args[0]}")
                else:
                    return CommandResult.error(f"切换会话失败：{args[0]}")
            
            elif args[0] == "new" and len(args) >= 2:
                # /session new <name> - 创建新会话
                if not agent:
                    return CommandResult.error("暂无 Agent")
                elif switch_session(args[1], agent):
                    return CommandResult.ok(f"已创建并切换到新会话：{args[1]}")
                else:
                    return CommandResult.error(f"创建会话失败：{args[1]}")
            
            elif args[0] == "del" and len(args) >= 2:
                # /session del <name> - 删除会话
                manager = get_session_manager()
                if manager.delete(args[1]):
                    return CommandResult.ok(f"已删除会话：{args[1]}")
                else:
                    return CommandResult.error(f"会话不存在：{args[1]}")
            
            else:
                return CommandResult.error(
                    "用法错误",
                    "用法:\n"
                    "  /session              显示当前会话\n"
                    "  /session <名称>        切换会话\n"
                    "  /session new <名称>    创建新会话\n"
                    "  /session del <名称>    删除会话"
                )
        
        except Exception as e:
            return CommandResult.error("会话管理失败", str(e))


class SessionNewCommand(CommandHandler):
    """创建新会话（快捷命令）"""
    
    @property
    def name(self) -> str:
        return "session new"
    
    @property
    def description(self) -> str:
        return "创建新会话"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult.error("请提供会话名称", "用法：/session new <名称>")
        
        try:
            from simple_agent.core.session import switch_session
            
            agent = context.get('current_agent') or context.get('cli_agent', {}).get('agent')
            if not agent:
                return CommandResult.error("暂无 Agent")
            
            session_name = args[0]
            if switch_session(session_name, agent):
                return CommandResult.ok(f"已创建并切换到新会话：{session_name}")
            else:
                return CommandResult.error(f"创建会话失败：{session_name}")
        
        except Exception as e:
            return CommandResult.error("创建会话失败", str(e))


class SessionDelCommand(CommandHandler):
    """删除会话（快捷命令）"""
    
    @property
    def name(self) -> str:
        return "session del"
    
    @property
    def description(self) -> str:
        return "删除会话"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult.error("请提供会话名称", "用法：/session del <名称>")
        
        try:
            from simple_agent.core.session import get_session_manager
            
            manager = get_session_manager()
            if manager.delete(args[0]):
                return CommandResult.ok(f"已删除会话：{args[0]}")
            else:
                return CommandResult.error(f"会话不存在：{args[0]}")
        
        except Exception as e:
            return CommandResult.error("删除会话失败", str(e))


class ClearCommand(CommandHandler):
    """清空当前会话记忆"""
    
    @property
    def name(self) -> str:
        return "clear"
    
    @property
    def description(self) -> str:
        return "清空当前会话的记忆"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            agent = context.get('current_agent')
            cli_agent = context.get('cli_agent')
            
            if agent:
                agent.memory.clear()
                return CommandResult.ok(f"{agent.name} 记忆已清空")
            elif cli_agent:
                cli_agent.clear_memory()
                return CommandResult.ok("CLI Agent 记忆已清空")
            else:
                return CommandResult.error("暂无 Agent")
        
        except Exception as e:
            return CommandResult.error("清空记忆失败", str(e))
