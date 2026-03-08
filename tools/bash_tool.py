"""
BashTool - Shell 命令执行工具

执行系统 shell 命令，支持超时和安全控制
"""

import subprocess
import shlex
from typing import Optional
from core.tool import BaseTool, ToolResult


# 危险命令黑名单
DANGEROUS_COMMANDS = {
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=/dev/zero",
    ":(){ :|:& };:",  # fork bomb
    "chmod -R 777 /",
    "> /dev/sda",
    "mv /* /dev/null",
}

# 需要确认的危险模式
WARNING_PATTERNS = [
    "rm -rf", "rmdir", "del ", "delete",
    "format", "fdisk", "parted",
    "shutdown", "reboot", "init 0", "init 6",
    "iptables", "ufw", "firewall-cmd",
]


def is_dangerous(command: str) -> tuple[bool, str]:
    """检查命令是否危险
    
    Returns:
        (is_dangerous, reason)
    """
    cmd_lower = command.lower().strip()
    
    # 检查黑名单
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous in cmd_lower:
            return True, f"禁止执行危险命令: {dangerous}"
    
    # 检查危险模式
    for pattern in WARNING_PATTERNS:
        if pattern in cmd_lower:
            return True, f"命令包含危险操作 '{pattern}'，请谨慎使用"
    
    return False, ""


class BashTool(BaseTool):
    """Shell 命令执行工具：执行系统命令并返回结果"""
    
    @property
    def name(self) -> str:
        return "bash"
    
    @property
    def description(self) -> str:
        return """执行系统 shell 命令。

使用场景：
- 查看系统信息：uname -a, hostname, whoami
- 文件操作：ls, cat, find, grep, mkdir
- 进程管理：ps, top, kill
- 网络诊断：ping, curl, wget, netstat
- 系统监控：df, free, uptime
- Git 操作：git status, git log
- 包管理：pip list, npm list

注意：
- 不支持交互式命令（如 vim, top, htop）
- 危险命令会被阻止（如 rm -rf /）
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
                "check_danger": {
                    "type": "boolean",
                    "description": "是否检查危险命令，默认 true",
                    "default": True
                }
            },
            "required": ["command"]
        }
    
    def execute(
        self,
        command: str,
        timeout: int = 60,
        check_danger: bool = True,
        **kwargs
    ) -> ToolResult:
        """执行 shell 命令"""
        try:
            # 安全检查
            if check_danger:
                is_danger, reason = is_dangerous(command)
                if is_danger:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"安全限制：{reason}"
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
                output = f"{output}\n\n[返回码: {result.returncode}]"
            
            return ToolResult(
                success=success,
                output=output,
                error=None if success else f"命令执行失败，返回码: {result.returncode}"
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