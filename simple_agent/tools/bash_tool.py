"""
BashTool - Shell 命令执行工具

执行系统 shell 命令，支持超时和安全控制

设计理念:
- 按人的思路执行：该确认的就确认
- 不是 AI 自动执行，而是辅助人执行
- 安全优先：危险命令需要明确确认
- 深度防护：集成多层安全审计机制
"""

import subprocess
import shlex
import os
from typing import Optional
from simple_agent.core.tool import BaseTool, ToolResult
from simple_agent.core.execution_context import _execution_context

# 集成任务执行模式
try:
    from simple_agent.core.task_mode import (
        get_execution_mode,
        ExecutionMode,
        check_and_request_confirmation,
    )
    TASK_MODE_ENABLED = True
except ImportError:
    TASK_MODE_ENABLED = False

# 集成深度安全防护模块
try:
    from simple_agent.core.script_security import (
        SecurityAuditor,
        SecurityLevel,
        PermissionLevel,
        quick_audit,
    )
    DEEP_SECURITY_ENABLED = True
except ImportError:
    DEEP_SECURITY_ENABLED = False


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
    # 首先使用深度安全审计（如果启用）
    if DEEP_SECURITY_ENABLED:
        audit_result = quick_audit(command)
        if not audit_result.allowed:
            # 根据安全级别返回
            if audit_result.security_level == SecurityLevel.BLOCKED:
                return False, f"禁止执行危险命令：{audit_result.risk_reasons[0] if audit_result.risk_reasons else '安全策略阻止'}"
            elif audit_result.security_level in [SecurityLevel.MEDIUM_RISK, SecurityLevel.HIGH_RISK]:
                return True, f"需要确认：{audit_result.risk_reasons[0] if audit_result.risk_reasons else '危险操作'}"

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

沙箱支持:
- 命令在沙箱目录中执行（如果启用）
- 沙箱目录结构：output/, process/temp/, process/cache/, sandbox/

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
                },
                "mode": {
                    "type": "string",
                    "enum": ["auto", "review"],
                    "description": "执行模式：'auto' 自动执行，'review' 用户评审",
                    "default": "auto"
                }
            },
            "required": ["command"]
        }

    def execute(
        self,
        command: str,
        timeout: int = 60,
        confirmed_by_user: bool = False,
        cwd: Optional[str] = None,
        use_sandbox: bool = True,
        mode: Optional[str] = None,  # "auto" or "review"
        **kwargs
    ) -> ToolResult:
        """执行 shell 命令（带完整异常处理）"""
        try:
            # 验证输入参数
            if not isinstance(command, str):
                return ToolResult(
                    success=False,
                    output="",
                    error="command 参数必须是字符串类型"
                )

            if not command or not command.strip():
                return ToolResult(
                    success=False,
                    output="",
                    error="command 参数不能为空"
                )

            # 限制超时时间
            timeout = min(max(int(timeout), 1), 300)
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
                # 检查执行模式
                current_mode = get_execution_mode()
                if mode == "auto" or (mode is None and current_mode == ExecutionMode.AUTO):
                    # 自动模式下，直接执行（安全检查已通过）
                    pass
                else:
                    # REVIEW 模式或默认模式，检查是否可以自动批准
                    should_proceed, error_msg = check_and_request_confirmation(
                        command,
                        message=f"检测到需要确认的命令: {reason}"
                    )
                    if not should_proceed:
                        return ToolResult(
                            success=False,
                            output="",
                            error=f"操作被用户拒绝：{error_msg}"
                        )

            # 限制超时时间
            timeout = min(max(timeout, 1), 300)

            # 默认工作目录：优先使用沙箱目录
            if cwd is None:
                # 尝试从执行上下文获取沙箱目录
                sandbox_dir = getattr(_execution_context, 'sandbox_dir', None)
                if sandbox_dir and use_sandbox:
                    cwd = sandbox_dir
                else:
                    # 回退到 output_dir
                    cwd = getattr(_execution_context, 'output_dir', None)
                    if cwd is None:
                        cwd = kwargs.get("cwd", '.')

            # 确保工作目录存在
            try:
                os.makedirs(cwd, exist_ok=True)
            except Exception:
                pass  # 如果无法创建目录，继续使用默认目录

            # 执行命令
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
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
            # 捕获所有异常，不中断整个任务
            return ToolResult(
                success=False,
                output="",
                error=f"执行命令失败：{type(e).__name__}: {e}"
            )


# 注册工具到资源仓库
from simple_agent.core.resource import repo
repo.register_tool(
    BashTool,
    tags=["system", "shell", "command", "execute"],
    description="执行系统 shell 命令"
)
