"""
任务追踪和 Session 交互命令

命令列表:
- /tasks status <task_id> - 查看任务详细状态
- /tasks running - 查看正在执行的任务
- /tasks list - 列出所有任务
- /session continue <task_id> - 在 session 中继续交互
- /session history <task_id> - 查看 session 历史
- /session end <task_id> - 结束 session
"""

from typing import List, Dict, Any
from simple_agent.cli_commands import CommandHandler, CommandResult


class TaskStatusCommand(CommandHandler):
    """查看任务详细状态"""

    @property
    def name(self) -> str:
        return "tasks status"

    @property
    def description(self) -> str:
        return "查看任务详细状态"

    @property
    def usage(self) -> str:
        return "/tasks status <task_id>"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult.error(
                "请提供任务 ID",
                "用法：/tasks status <task_id>\n示例：/tasks status task_123"
            )

        try:
            cli_agent = context.get('cli_agent')
            if not cli_agent:
                return CommandResult.error("CLI Agent 未初始化")

            task_id = args[0]
            cli_agent.print_task_status(task_id)

            return CommandResult.ok(f"✓ 已打印任务 {task_id} 的详细状态")

        except Exception as e:
            import traceback
            return CommandResult.error("获取任务状态失败", f"{e}\n{traceback.format_exc()}")


class TaskRunningCommand(CommandHandler):
    """查看正在执行的任务"""

    @property
    def name(self) -> str:
        return "tasks running"

    @property
    def description(self) -> str:
        return "查看正在执行的任务列表"

    @property
    def usage(self) -> str:
        return "/tasks running"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            cli_agent = context.get('cli_agent')
            if not cli_agent:
                return CommandResult.error("CLI Agent 未初始化")

            cli_agent.print_running_tasks()
            return CommandResult.ok("✓ 已打印正在执行的任务")

        except Exception as e:
            import traceback
            return CommandResult.error("获取任务列表失败", f"{e}\n{traceback.format_exc()}")


class TaskListCommand(CommandHandler):
    """列出所有任务"""

    @property
    def name(self) -> str:
        return "tasks list"

    @property
    def description(self) -> str:
        return "列出所有任务（按状态分组）"

    @property
    def usage(self) -> str:
        return "/tasks list"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            cli_agent = context.get('cli_agent')
            if not cli_agent:
                return CommandResult.error("CLI Agent 未初始化")

            cli_agent.print_all_tasks()
            return CommandResult.ok("✓ 已打印所有任务")

        except Exception as e:
            import traceback
            return CommandResult.error("获取任务列表失败", f"{e}\n{traceback.format_exc()}")


class SessionContinueCommand(CommandHandler):
    """在 session 中继续交互"""

    @property
    def name(self) -> str:
        return "session continue"

    @property
    def description(self) -> str:
        return "在现有 session 中继续对话（对于等待确认的任务，会自动执行）"

    @property
    def usage(self) -> str:
        return "/session continue <task_id> <消息>"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        if len(args) < 2:
            return CommandResult.error(
                "请提供 task_id 和消息",
                "用法：/session continue <task_id> <消息>\n示例：/session continue task_123 确认执行"
            )

        try:
            cli_agent = context.get('cli_agent')
            if not cli_agent:
                return CommandResult.error("CLI Agent 未初始化")

            task_id = args[0]
            message = " ".join(args[1:])

            # 尝试先执行等待确认的任务（如果有）
            # 检查任务是否处于 CONFIRMING 状态
            from simple_agent.core.task_handle import TaskStatusEnum
            handle = None
            if hasattr(cli_agent, 'task_queue') and hasattr(cli_agent.task_queue, '_tasks'):
                handle = cli_agent.task_queue._tasks.get(task_id)

            if handle and handle.status.status == TaskStatusEnum.CONFIRMING:
                # 任务等待确认，执行它
                result = cli_agent.continue_session_and_execute(task_id, message)
                return CommandResult.ok(
                    f"✓ 任务已执行: {task_id}",
                    data={"result": result}
                )

            # 正常的 session 继续
            result = cli_agent.continue_session(task_id, message)

            return CommandResult.ok(
                f"✓ Session 继续成功: {task_id}",
                data={"result": result}
            )

        except ValueError as e:
            return CommandResult.error("Session 不存在", str(e))
        except Exception as e:
            import traceback
            return CommandResult.error("继续 Session 失败", f"{e}\n{traceback.format_exc()}")


class SessionHistoryCommand(CommandHandler):
    """查看 Session 历史"""

    @property
    def name(self) -> str:
        return "session history"

    @property
    def description(self) -> str:
        return "查看 Session 交互历史"

    @property
    def usage(self) -> str:
        return "/session history <task_id>"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult.error(
                "请提供 task_id",
                "用法：/session history <task_id>\n示例：/session history task_123"
            )

        try:
            cli_agent = context.get('cli_agent')
            if not cli_agent:
                return CommandResult.error("CLI Agent 未初始化")

            task_id = args[0]
            history = cli_agent.get_session_history(task_id)

            if not history:
                return CommandResult.ok(f"Session {task_id} 没有历史记录")

            lines = [f"\n{'='*60}"]
            lines.append(f"Session 历史 ({task_id})")
            lines.append(f"{'='*60}")

            for i, msg in enumerate(history):
                role = "用户" if msg.get("role") == "user" else "助手"
                content = msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else ""
                lines.append(f"  [{i+1}] {role}：{content}")

            lines.append(f"{'='*60}")
            lines.append(f"共 {len(history)} 条消息")

            return CommandResult.ok("\n".join(lines))

        except Exception as e:
            import traceback
            return CommandResult.error("获取 Session 历史失败", f"{e}\n{traceback.format_exc()}")


class SessionEndCommand(CommandHandler):
    """结束 Session"""

    @property
    def name(self) -> str:
        return "session end"

    @property
    def description(self) -> str:
        return "结束指定的 Session"

    @property
    def usage(self) -> str:
        return "/session end <task_id>"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult.error(
                "请提供 task_id",
                "用法：/session end <task_id>\n示例：/session end task_123"
            )

        try:
            cli_agent = context.get('cli_agent')
            if not cli_agent:
                return CommandResult.error("CLI Agent 未初始化")

            task_id = args[0]
            cli_agent.end_session(task_id)

            return CommandResult.ok(f"✓ 已结束 Session: {task_id}")

        except Exception as e:
            import traceback
            return CommandResult.error("结束 Session 失败", f"{e}\n{traceback.format_exc()}")


# 导出函数
def get_tracking_commands() -> List[CommandHandler]:
    """获取任务追踪命令"""
    return [
        TaskStatusCommand(),
        TaskRunningCommand(),
        TaskListCommand(),
        SessionContinueCommand(),
        SessionHistoryCommand(),
        SessionEndCommand(),
    ]
