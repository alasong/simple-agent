"""
守护进程命令

支持在交互模式下管理 API 守护进程：
/start      启动 API 守护进程
/stop       停止 API 守护进程
/restart    重启 API 守护进程
/status     查看守护进程状态
/logs       查看日志
/install-service  生成 systemd/launchd 服务配置
"""

import os
from typing import List, Dict, Any
from .__init__ import CommandHandler, CommandResult

try:
    from core.rich_output import print_info
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class StartDaemonCommand(CommandHandler):
    """启动守护进程"""

    @property
    def name(self) -> str:
        return "start"

    @property
    def description(self) -> str:
        return "启动 API 守护进程"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            from core.daemon import get_daemon
            daemon = get_daemon()
            success, msg = daemon.start()

            if success:
                result = CommandResult.ok(msg)
                if RICH_AVAILABLE:
                    print_info("API 服务已在后台运行")
                    print_info("访问 http://localhost:8000/docs 查看 API 文档")
                return result
            else:
                return CommandResult.error(msg)
        except ImportError as e:
            return CommandResult.error(f"无法导入守护进程模块：{e}")


class StopDaemonCommand(CommandHandler):
    """停止守护进程"""

    @property
    def name(self) -> str:
        return "stop"

    @property
    def description(self) -> str:
        return "停止 API 守护进程"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            from core.daemon import get_daemon
            daemon = get_daemon()
            success, msg = daemon.stop()

            if success:
                return CommandResult.ok(msg)
            else:
                return CommandResult.error(msg)
        except ImportError as e:
            return CommandResult.error(f"无法导入守护进程模块：{e}")


class RestartDaemonCommand(CommandHandler):
    """重启守护进程"""

    @property
    def name(self) -> str:
        return "restart"

    @property
    def description(self) -> str:
        return "重启 API 守护进程"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            from core.daemon import get_daemon
            daemon = get_daemon()
            success, msg = daemon.restart()

            if success:
                return CommandResult.ok(msg)
            else:
                return CommandResult.error(msg)
        except ImportError as e:
            return CommandResult.error(f"无法导入守护进程模块：{e}")


class StatusDaemonCommand(CommandHandler):
    """查看守护进程状态"""

    @property
    def name(self) -> str:
        return "status"

    @property
    def description(self) -> str:
        return "查看守护进程状态"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            from core.daemon import get_daemon
            daemon = get_daemon()
            status = daemon.status()

            lines = [
                f"{'='*50}",
                f"守护进程：{status['name']}",
                f"运行状态：{'运行中' if status['running'] else '已停止'}",
            ]

            if status.get('pid'):
                lines.append(f"PID: {status['pid']}")
            lines.append(f"PID 文件：{status['pid_file']}")
            lines.append(f"日志文件：{status['log_file']}")

            if status['running'] and 'create_time' in status:
                lines.append(f"启动时间：{status['create_time']}")
            if status['running'] and 'cpu_percent' in status:
                lines.append(f"CPU: {status['cpu_percent']:.1f}%")
                lines.append(f"内存：{status['memory_percent']:.1f}%")

            lines.append(f"{'='*50}")

            return CommandResult.ok("\n".join(lines))
        except ImportError as e:
            return CommandResult.error(f"无法导入守护进程模块：{e}")


class LogsDaemonCommand(CommandHandler):
    """查看守护进程日志"""

    @property
    def name(self) -> str:
        return "logs"

    @property
    def description(self) -> str:
        return "查看守护进程日志"

    def parse_args(self, args: List[str]) -> Dict[str, Any]:
        lines = 50
        if args and args[0].isdigit():
            lines = int(args[0])
        return {"lines": lines}

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            from core.daemon import get_daemon
            daemon = get_daemon()
            parsed = self.parse_args(args)
            lines = parsed.get("lines", 50)

            logs = daemon.logs(lines=lines)

            output = [
                f"{'='*50}",
                f"最近 {lines} 行日志:",
                f"{'='*50}",
                logs,
            ]

            return CommandResult.ok("\n".join(output))
        except ImportError as e:
            return CommandResult.error(f"无法导入守护进程模块：{e}")


class InstallServiceCommand(CommandHandler):
    """生成系统服务配置"""

    @property
    def name(self) -> str:
        return "install-service"

    @property
    def description(self) -> str:
        return "生成 systemd/launchd 服务配置"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            from core.daemon import generate_systemd_service, generate_launchd_plist
            import platform

            system = platform.system()

            if system == "Linux":
                service_content = generate_systemd_service()
                service_file = "/etc/systemd/system/simple-agent.service"

                output = [
                    f"{'='*50}",
                    "systemd 服务配置:",
                    f"{'='*50}",
                    service_content,
                    f"\n安装步骤:",
                    f"1. sudo tee {service_file} << 'EOF'",
                    service_content,
                    "EOF",
                    "2. sudo systemctl daemon-reload",
                    "3. sudo systemctl enable simple-agent",
                    "4. sudo systemctl start simple-agent",
                ]

            elif system == "Darwin":  # macOS
                plist_content = generate_launchd_plist()
                home = os.path.expanduser("~")
                plist_file = os.path.join(home, "Library", "LaunchAgents", "simple-agent.plist")

                output = [
                    f"{'='*50}",
                    "launchd 服务配置:",
                    f"{'='*50}",
                    plist_content,
                    f"\n安装步骤:",
                    f"1. mkdir -p ~/Library/LaunchAgents",
                    f"2. 保存配置到：{plist_file}",
                    "3. launchctl load -w ~/Library/LaunchAgents/simple-agent.plist",
                ]
            else:
                output = [f"不支持的操作系统：{system}"]

            return CommandResult.ok("\n".join(output))
        except ImportError as e:
            return CommandResult.error(f"无法导入守护进程模块：{e}")
        except NameError:
            # os 模块未导入
            import os
            return self.execute(args, context)


def get_daemon_commands() -> List[CommandHandler]:
    """获取守护进程命令列表"""
    return [
        StartDaemonCommand(),
        StopDaemonCommand(),
        RestartDaemonCommand(),
        StatusDaemonCommand(),
        LogsDaemonCommand(),
        InstallServiceCommand(),
    ]
