"""
调试命令

命令列表:
- /debug [on|off] - 切换调试模式
- /debug summary - 显示调试摘要
- /debug stats - 显示详细统计信息
"""

from typing import List, Dict, Any
from simple_agent.cli_commands import CommandHandler, CommandResult


class DebugCommand(CommandHandler):
    """切换调试模式"""
    
    @property
    def name(self) -> str:
        return "debug"
    
    @property
    def description(self) -> str:
        return "切换调试模式或显示调试信息"
    
    @property
    def usage(self) -> str:
        return "/debug [on|off|summary|stats]"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            # 检查调试模块是否可用
            try:
                from core import enable_debug, disable_debug, get_debug_summary, print_debug_summary, tracker
                DEBUG_AVAILABLE = True
            except ImportError:
                DEBUG_AVAILABLE = False
            
            if not args:
                # 切换模式
                debug_mode = context.get('debug_mode', True)
                debug_mode = not debug_mode
                context['debug_mode'] = debug_mode
                
                lines = [f"调试模式：{'已开启' if debug_mode else '已关闭'}"]
                if debug_mode:
                    output_dir = context.get('output_dir', './output/cli')
                    lines.append(f"输出目录：{output_dir}")
                    if DEBUG_AVAILABLE:
                        enable_debug(verbose=True)
                        lines.append(f"调试跟踪器：已启用 (verbose=True)")
                
                return CommandResult.ok("\n".join(lines))
            
            subcommand = args[0].lower()
            
            if subcommand in ["on", "off", "true", "1", "false", "0"]:
                # 显式开关
                debug_mode = subcommand in ["on", "true", "1"]
                context['debug_mode'] = debug_mode
                
                lines = [f"调试模式：{'已开启' if debug_mode else '已关闭'}"]
                if debug_mode:
                    output_dir = context.get('output_dir', './output/cli')
                    lines.append(f"输出目录：{output_dir}")
                    if DEBUG_AVAILABLE:
                        enable_debug(verbose=True)
                        lines.append(f"调试跟踪器：已启用")
                else:
                    if DEBUG_AVAILABLE:
                        disable_debug()
                        lines.append(f"调试跟踪器：已禁用")
                
                return CommandResult.ok("\n".join(lines))
            
            elif subcommand == "summary":
                if not DEBUG_AVAILABLE:
                    return CommandResult.error("调试模块不可用")
                
                lines = [f"\n{'='*60}"]
                lines.append("调试执行摘要")
                lines.append(f"{'='*60}")
                
                # 获取调试摘要
                summary = get_debug_summary()
                lines.append(summary)
                
                return CommandResult.ok("\n".join(lines))
            
            elif subcommand == "stats":
                if not DEBUG_AVAILABLE:
                    return CommandResult.error("调试模块不可用")
                
                lines = [f"\n{'='*60}"]
                lines.append("详细统计信息")
                lines.append(f"{'='*60}")
                
                # Agent 统计
                agent_stats = tracker.get_agent_stats()
                if agent_stats and agent_stats.get('count', 0) > 0:
                    lines.append(f"\n📊 Agent 执行统计:")
                    lines.append(f"  总执行次数：{agent_stats.get('count', 0)}")
                    lines.append(f"  成功：{agent_stats.get('successful', 0)}")
                    lines.append(f"  失败：{agent_stats.get('failed', 0)}")
                    if agent_stats.get('count', 0) > 0:
                        lines.append(f"  成功率：{agent_stats.get('success_rate', 0):.1%}")
                        lines.append(f"  平均耗时：{agent_stats.get('avg_duration', 0):.3f}秒")
                    
                    # 按 Agent 分类统计
                    if 'by_agent' in agent_stats and agent_stats['by_agent']:
                        lines.append(f"\n  按 Agent 分类:")
                        for agent_name, stats in agent_stats['by_agent'].items():
                            lines.append(f"    - {agent_name}:")
                            lines.append(f"        执行：{stats.get('count', 0)} 次")
                            lines.append(f"        平均耗时：{stats.get('avg_duration', 0):.3f}秒")
                            lines.append(f"        工具调用：{stats.get('total_tool_calls', 0)} 次")
                else:
                    lines.append("\n暂无 Agent 执行记录")
                
                # Workflow 统计
                workflow_stats = tracker.get_workflow_stats()
                if workflow_stats and workflow_stats.get('count', 0) > 0:
                    lines.append(f"\n📊 Workflow 执行统计:")
                    lines.append(f"  总执行次数：{workflow_stats.get('count', 0)}")
                    lines.append(f"  成功：{workflow_stats.get('successful', 0)}")
                    lines.append(f"  失败：{workflow_stats.get('failed', 0)}")
                    if workflow_stats.get('count', 0) > 0:
                        lines.append(f"  成功率：{workflow_stats.get('success_rate', 0):.1%}")
                        lines.append(f"  平均耗时：{workflow_stats.get('avg_duration', 0):.3f}秒")
                        lines.append(f"  总步骤数：{workflow_stats.get('total_steps', 0)}")
                        lines.append(f"  步骤成功率：{workflow_stats.get('step_success_rate', 0):.1%}")
                    
                    # 按 Workflow 分类统计
                    if 'by_workflow' in workflow_stats and workflow_stats['by_workflow']:
                        lines.append(f"\n  按 Workflow 分类:")
                        for workflow_name, stats in workflow_stats['by_workflow'].items():
                            lines.append(f"    - {workflow_name}:")
                            lines.append(f"        执行：{stats.get('count', 0)} 次")
                            lines.append(f"        平均步骤：{stats.get('avg_steps', 0):.1f}")
                            lines.append(f"        平均耗时：{stats.get('avg_duration', 0):.3f}秒")
                else:
                    lines.append("\n暂无 Workflow 执行记录")
                
                lines.append(f"\n{'='*60}")
                return CommandResult.ok("\n".join(lines))
            
            else:
                # 未知子命令，切换模式
                debug_mode = context.get('debug_mode', True)
                debug_mode = not debug_mode
                context['debug_mode'] = debug_mode
                
                lines = [f"调试模式：{'已开启' if debug_mode else '已关闭'}"]
                if debug_mode:
                    output_dir = context.get('output_dir', './output/cli')
                    lines.append(f"输出目录：{output_dir}")
                    if DEBUG_AVAILABLE:
                        enable_debug(verbose=True)
                        lines.append(f"调试跟踪器：已启用 (verbose=True)")
                else:
                    if DEBUG_AVAILABLE:
                        disable_debug()
                        lines.append(f"调试跟踪器：已禁用")
                
                return CommandResult.ok("\n".join(lines))
        
        except Exception as e:
            return CommandResult.error("调试命令执行失败", str(e))


class DebugSummaryCommand(CommandHandler):
    """显示调试摘要（快捷命令）"""
    
    @property
    def name(self) -> str:
        return "debug summary"
    
    @property
    def description(self) -> str:
        return "显示调试执行摘要"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        # 委托给 DebugCommand 处理
        debug_cmd = DebugCommand()
        return debug_cmd.execute(["summary"], context)


class DebugStatsCommand(CommandHandler):
    """显示详细统计（快捷命令）"""
    
    @property
    def name(self) -> str:
        return "debug stats"
    
    @property
    def description(self) -> str:
        return "显示详细统计信息"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        # 委托给 DebugCommand 处理
        debug_cmd = DebugCommand()
        return debug_cmd.execute(["stats"], context)
