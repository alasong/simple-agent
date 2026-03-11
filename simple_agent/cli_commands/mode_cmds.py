"""
执行模式管理命令

命令列表:
- /mode - 显示当前执行模式
- /mode auto - 切换到自动模式
- /mode review - 切换到用户评审模式
"""

from typing import List, Dict, Any
from simple_agent.cli_commands import CommandHandler, CommandResult


class ModeCommand(CommandHandler):
    """执行模式管理命令"""

    @property
    def name(self) -> str:
        return "mode"

    @property
    def description(self) -> str:
        return "执行模式管理（自动/用户评审）"

    @property
    def usage(self) -> str:
        return "/mode [auto|review]"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            from simple_agent.core.task_mode import ExecutionMode

            # 获取当前模式
            current_mode = context.get('execution_mode', 'auto')

            if len(args) == 0:
                # 只显示当前模式
                mode_name = "自动模式" if current_mode == "auto" else "用户评审模式"
                return CommandResult.ok(f"当前执行模式：{mode_name} (/mode auto 或 /mode review)")

            elif len(args) == 1:
                new_mode = args[0].lower()
                if new_mode not in ['auto', 'review']:
                    return CommandResult.error(
                        "无效的模式",
                        "用法: /mode auto  或  /mode review"
                    )

                # 设置新模式
                context['execution_mode'] = new_mode

                # 如果有 CLI Coordinator 实例，同步更新
                if 'cli_coordinator' in context:
                    coordinator = context['cli_coordinator']
                    if coordinator and hasattr(coordinator, 'context'):
                        coordinator.context.execution_mode = new_mode

                mode_name = "自动模式" if new_mode == "auto" else "用户评审模式"
                return CommandResult.ok(f"已切换到 {mode_name}")

            else:
                return CommandResult.error(
                    "参数过多",
                    "用法:\n"
                    "  /mode              显示当前模式\n"
                    "  /mode auto         切换到自动模式\n"
                    "  /mode review       切换到用户评审模式"
                )

        except Exception as e:
            return CommandResult.error("模式切换失败", str(e))


class ModeAutoCommand(CommandHandler):
    """自动模式命令（快捷方式）"""

    @property
    def name(self) -> str:
        return "mode auto"

    @property
    def description(self) -> str:
        return "切换到自动执行模式"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        context['execution_mode'] = 'auto'

        if 'cli_coordinator' in context:
            coordinator = context['cli_coordinator']
            if coordinator and hasattr(coordinator, 'context'):
                coordinator.context.execution_mode = 'auto'

        return CommandResult.ok("已切换到自动模式（所有操作将自动执行）")


class ModeReviewCommand(CommandHandler):
    """用户评审模式命令（快捷方式）"""

    @property
    def name(self) -> str:
        return "mode review"

    @property
    def description(self) -> str:
        return "切换到用户评审模式"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        context['execution_mode'] = 'review'

        if 'cli_coordinator' in context:
            coordinator = context['cli_coordinator']
            if coordinator and hasattr(coordinator, 'context'):
                coordinator.context.execution_mode = 'review'

        return CommandResult.ok("已切换到用户评审模式（关键操作将要求确认）")
