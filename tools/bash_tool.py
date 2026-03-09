"""
BashTool - Shell 命令执行工具

执行系统 shell 命令，支持超时和安全控制

设计理念:
- 按人的思路执行：该确认的就确认
- 不是 AI 自动执行，而是辅助人执行
- 安全优先：危险命令需要明确确认
"""

import subprocess
import shlex
from typing import Optional
from core.tool import BaseTool, ToolResult


# 危险命令黑名单（绝对禁止）
DANGEROUS_COMMANDS = {
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=/dev/zero",
    ":(){ :|:& };:",  # fork bomb
    "chmod -R 777 /",
    "> /dev/sda",
    "mv /* /dev/null",
}

# 需要用户确认的危险模式（AI 不应该自动执行）
WARNING_PATTERNS = [
    "rm -rf", "rmdir", "del ", "delete",
    "format", "fdisk", "parted",
    "shutdown", "reboot", "init 0", "init 6",
    "iptables", "ufw", "firewall-cmd",
    "kill -9", "pkill", "killall",
    "curl .* | sh", "wget .* | sh",  # 管道执行远程脚本
    "chmod 777", "chown.*:.*\\s*/",
]

# 只读安全命令（AI 可以自动执行）
SAFE_READONLY_COMMANDS = [
    "ls", "dir", "find", "locate", "which", "whereis",
    "cat", "less", "more", "head", "tail",
    "grep", "egrep", "awk", "sed",
    "pwd", "date", "whoami", "hostname", "uname",
    "ps", "top", "htop", "free", "df", "du",
    "git status", "git log", "git diff", "git branch",
    "pip list", "pip show", "npm list",
    "python --version", "node --version",
    "echo", "printf",
]


def is_dangerous(command: str) -> tuple[bool, str]:
    """检查命令是否危险

    Returns:
        (是否需要用户确认，原因)
        - False + 错误消息：绝对禁止的命令
        - True + 原因：需要用户确认
        - False + "": 安全命令，可直接执行
    """
    cmd_lower = command.lower().strip()

    # 检查黑名单（绝对禁止）
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous in cmd_lower:
            return False, f"禁止执行危险命令：{dangerous}"

    # 检查危险模式（需要用户确认）
    for pattern in WARNING_PATTERNS:
        if pattern in cmd_lower:
            return True, f"命令包含危险操作 '{pattern}'，需要用户确认"

    return False, ""


def is_readonly_safe(command: str) -> bool:
    """检查是否是安全的只读命令"""
    cmd_lower = command.lower().strip()
    for safe in SAFE_READONLY_COMMANDS:
        if cmd_lower.startswith(safe):
            return True
    return False


class BashTool(BaseTool):
    """Shell 命令执行工具：执行系统命令并返回结果

    设计理念:
    - 按人的思路执行：该确认的就确认
    - AI 不应该自动执行危险或有副作用的命令
    - 安全的只读命令可以直接执行
    """

    @property
    def name(self) -> str:
        return "bash"

    @property
    def description(self) -> str:
        return """执行系统 shell 命令。

使用场景:
- 查看系统信息：uname -a, hostname, whoami
- 文件操作：ls, cat, find, grep, mkdir
- 进程管理：ps, top, kill
- 网络诊断：ping, curl, wget, netstat
- 系统监控：df, free, uptime
- Git 操作：git status, git log
- 包管理：pip list, npm list

安全策略:
- 安全的只读命令（ls, cat, git status 等）可直接执行
- 危险命令（rm, kill, shutdown 等）需要用户确认
- 绝对禁止的命令（rm -rf / 等）会被拒绝

注意:
- 不支持交互式命令（如 vim, top, htop）
- 危险命令会被要求确认
- 默认超时 60 秒
"""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的 shell 命令"
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒），默认 60，最大 300",
                    "default": 60,
                    "minimum": 1,
                    "maximum": 300
                },
                "confirmed_by_user": {
                    "type": "boolean",
                    "description": "用户是否已确认危险命令（需要用户明确确认时才为 true）",
                    "default": False
                }
            },
            "required": ["command"]
        }

    def execute(
        self,
        command: str,
        timeout: int = 60,
        confirmed_by_user: bool = False,
        **kwargs
    ) -> ToolResult:
        """执行 shell 命令

        Args:
            command: 要执行的命令
            timeout: 超时时间
            confirmed_by_user: 用户是否已确认危险命令
        """
        try:
            # 安全检查
            need_confirm, reason = is_dangerous(command)

            # 绝对禁止的命令
            if not need_confirm and reason and reason.startswith("禁止"):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"安全限制：{reason}"
                )

            # 需要用户确认的命令
            if need_confirm and not confirmed_by_user:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"等待确认：{reason}\n\n请向用户展示此命令并获取确认后，设置 confirmed_by_user=true 重新调用。"
                )

            # 限制超时时间
            timeout = min(max(timeout, 1), 300)

            # 执行命令
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=kwargs.get("cwd")  # 支持指定工作目录
            )

            # 构建输出
            output_parts = []

            if result.stdout:
                output_parts.append(f"[输出]\n{result.stdout.strip()}")

            if result.stderr:
                output_parts.append(f"[错误]\n{result.stderr.strip()}")

            output = "\n".join(output_parts) if output_parts else "命令执行成功（无输出）"

            # 根据返回码判断成功
            success = result.returncode == 0

            if not success:
                output = f"{output}\n\n[返回码：{result.returncode}]"

            return ToolResult(
                success=success,
                output=output,
                error=None if success else f"命令执行失败，返回码：{result.returncode}"
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"命令执行超时（超过 {timeout} 秒）"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"执行命令失败：{e}"
            )


# 注册工具到资源仓库
from core.resource import repo
repo.register_tool(
    BashTool,
    tags=["system", "shell", "command", "execute"],
    description="执行系统 shell 命令"
)
