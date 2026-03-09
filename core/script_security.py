"""
Script Security - 深度脚本防护系统

多层安全防护机制：
1. 命令黑名单/白名单
2. 代码模式静态分析
3. 沙箱执行环境
4. 权限分级控制
5. 运行时监控
6. 审计日志

使用示例:
    from core.script_security import SecurityAuditor, SandboxExecutor

    # 安全审计
    auditor = SecurityAuditor()
    result = auditor.audit_command("rm -rf /tmp/test")
    if result.allowed:
        execute_command(...)

    # 沙箱执行
    executor = SandboxExecutor(allowed_dirs=["/tmp"], timeout=30)
    result = executor.execute("python script.py")
"""

import os
import re
import ast
import subprocess
import tempfile
import shutil
import hashlib
import logging
import traceback
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set, Tuple
from enum import Enum
from datetime import datetime
import json
import stat
import pwd
import grp


# ============================================================================
# 日志配置
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# 安全级别枚举
# ============================================================================

class SecurityLevel(Enum):
    """安全级别"""
    SAFE = "safe"              # 安全，可直接执行
    LOW_RISK = "low_risk"      # 低风险，记录日志
    MEDIUM_RISK = "medium_risk" # 中风险，需要确认
    HIGH_RISK = "high_risk"    # 高风险，需要管理员确认
    BLOCKED = "blocked"        # 禁止执行


class PermissionLevel(Enum):
    """权限级别"""
    GUEST = "guest"            # 访客：只读命令
    USER = "user"              # 用户：常规操作
    DEVELOPER = "developer"    # 开发者：构建/测试
    ADMIN = "admin"            # 管理员：系统操作
    ROOT = "root"              # 根权限：所有操作


# ============================================================================
# 安全配置数据
# ============================================================================

@dataclass
class SecurityConfig:
    """安全配置"""
    # 超时配置
    default_timeout: int = 60
    max_timeout: int = 300

    # 文件大小限制（字节）
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_output_size: int = 10 * 1024 * 1024  # 10MB

    # 目录限制
    allowed_base_dirs: List[str] = field(default_factory=lambda: ["/tmp", "/home"])
    forbidden_paths: Set[str] = field(default_factory=lambda: {
        "/etc/passwd", "/etc/shadow", "/etc/sudoers",
        "/root", "/boot", "/proc", "/sys",
    })

    # 命令限制
    max_command_length: int = 4096

    # 审计配置
    enable_audit_log: bool = True
    audit_log_path: str = "./.security/audit.log"

    # 沙箱配置
    sandbox_enabled: bool = True
    sandbox_user: Optional[str] = None


# ============================================================================
# 命令黑名单和模式
# ============================================================================

# 绝对禁止的命令（系统破坏性）
CRITICAL_BLOCKED_COMMANDS = [
    "rm -rf /",
    "rm -rf /*",
    "rm -rf /root",
    "rm -rf /home",
    "rm -rf /etc",
    "rm -rf /var",
    "rm -rf /usr",
    "rm -rf /bin",
    "rm -rf /sbin",
    "rm -rf /lib",
    "mkfs",
    "mkfs.",
    "dd if=/dev/zero",
    ":(){ :|:& };:",  # Fork bomb
    "chmod -R 777 /",
    "chown -R",
    "> /dev/sda",
    "mv /* /dev/null",
    "cp /* /dev/null",
    "shutdown -h now",
    "init 0",
    "reboot -f",
    "echo.*> /etc/",
]

# 危险命令模式
DANGEROUS_PATTERNS = [
    (r"rm\s+(-[rf]+\s+)?/", "删除根目录文件"),
    (r"rm\s+-rf\s+\*", "递归强制删除所有文件"),
    (r"dd\s+.*of=/dev/", "直接写入设备"),
    (r">\s*/dev/sd[a-z]", "重定向到磁盘设备"),
    (r"chmod\s+(-R\s+)?777", "设置全局可执行权限"),
    (r"chown\s+.*:.*\s+/", "修改根目录所有者"),
    (r"curl\s+.*\|\s*(ba)?sh", "执行远程脚本"),
    (r"wget\s+.*\|\s*(ba)?sh", "执行远程脚本"),
    (r"python.*-c.*eval", "Python 执行动态代码"),
    (r"python.*-c.*exec", "Python 执行动态代码"),
    (r"base64\s+-d\s+.*\|\s*(ba)?sh", "解码并执行"),
    (r"sudo\s+rm", "使用 sudo 删除"),
    (r"sudo\s+chmod", "使用 sudo 修改权限"),
    (r"sudo\s+chown", "使用 sudo 修改所有者"),
    (r"iptables\s+-F", "清空防火墙规则"),
    (r"ufw\s+disable", "禁用防火墙"),
    (r"systemctl\s+stop\s+firewalld", "停止防火墙"),
    (r"setenforce\s+0", "禁用 SELinux"),
    (r"userdel\s+-r", "删除用户"),
    (r"passwd\s+-d", "删除密码"),
    (r"kill\s+-9\s+-?1", "杀死所有进程"),
    (r"pkill\s+-9.*-f.*", "强制杀死进程"),
    (r"killall\s+-9", "强制杀死所有匹配进程"),
    (r"export\s+.*=.*;.*rm", "环境变量后接删除"),
    (r"mkfifo.*mknod", "创建特殊文件"),
    (r"nmap\s+-", "网络扫描"),
    (r"hydra\s+", "密码爆破"),
    (r"john\s+", "密码破解"),
]

# 只读安全命令（可直接执行）
SAFE_READONLY_COMMANDS = [
    "ls", "dir", "vdir", "find", "locate", "which", "whereis", "whatis",
    "cat", "less", "more", "head", "tail", "nl", "bat",
    "pwd", "cd", "pushd", "popd", "dirs",
    "date", "time", "uptime", "hostname", "uname", "whoami",
    "ps", "top", "htop", "free", "df", "du", "vmstat", "iostat",
    "grep", "egrep", "fgrep", "awk", "sed", "cut", "sort", "uniq",
    "wc", "diff", "patch", "cmp", "comm",
    "git status", "git log", "git diff", "git branch", "git show",
    "git blame", "git reflog", "git remote -v",
    "pip list", "pip show", "pip freeze", "npm list", "yarn list",
    "echo", "printf", "printenv", "env",
    "man", "info", "help", "type", "compgen",
    "file", "stat", "tree",
    "id", "groups", "who", "w", "last",
    "uname -a", "hostnamectl", "timedatectl",
    "python --version", "python3 --version", "node --version",
    "java -version", "go version", "rustc --version",
]

# 需要确认的命令模式
REQUIRE_CONFIRM_PATTERNS = [
    (r"rm\s", "删除文件操作"),
    (r"rmdir\s", "删除目录操作"),
    (r"unlink\s", "删除文件/链接"),
    (r"mv\s", "移动/重命名文件"),
    (r"cp\s+-[a-z]*r", "递归复制"),
    (r"scp\s", "远程复制"),
    (r"rsync\s", "文件同步"),
    (r">\s*", "重定向输出（可能覆盖文件）"),
    (r">>\s*", "追加输出"),
    (r"chmod\s", "修改文件权限"),
    (r"chown\s", "修改文件所有者"),
    (r"chgrp\s", "修改文件组"),
    (r"touch\s", "创建/修改文件时间"),
    (r"mkdir\s", "创建目录"),
    (r"ln\s", "创建链接"),
    (r"tar\s", "归档/解包"),
    (r"zip\s", "压缩文件"),
    (r"gzip\s", "压缩文件"),
    (r"kill\s", "发送信号到进程"),
    (r"killall\s", "杀死进程"),
    (r"pkill\s", "按名称杀死进程"),
    (r"systemctl\s+(start|stop|restart|enable|disable)", "系统服务管理"),
    (r"service\s+(start|stop|restart)", "系统服务管理"),
    (r"sudo\s", "提权操作"),
    (r"su\s+", "切换用户"),
    (r"apt\s+(install|remove|purge)", "包管理操作"),
    (r"apt-get\s+(install|remove|purge)", "包管理操作"),
    (r"yum\s+(install|remove)", "包管理操作"),
    (r"dnf\s+(install|remove)", "包管理操作"),
    (r"pip\s+install", "安装包"),
    (r"pip\s+uninstall", "卸载包"),
    (r"npm\s+(install|uninstall)", "包管理操作"),
    (r"curl\s+-[a-z]*O", "下载文件"),
    (r"wget\s+", "下载文件"),
    (r"docker\s+(rm|rmi,run,stop,start)", "Docker 容器操作"),
    (r"git\s+(reset\s+--hard|checkout\s+--|clean\s+-fd)", "Git 危险操作"),
]


# ============================================================================
# 审计日志
# ============================================================================

@dataclass
class AuditEntry:
    """审计日志条目"""
    timestamp: str
    command: str
    user: str
    security_level: str
    permission_level: str
    result: str  # allowed, denied, confirmed
    risk_reasons: List[str]
    execution_time: Optional[float] = None
    output_hash: Optional[str] = None
    error: Optional[str] = None


class AuditLogger:
    """审计日志记录器"""

    def __init__(self, log_path: str):
        self.log_path = log_path
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        """确保日志目录存在"""
        log_dir = os.path.dirname(self.log_path)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)

    def log(self, entry: AuditEntry):
        """记录审计日志"""
        log_line = json.dumps({
            "timestamp": entry.timestamp,
            "command": entry.command,
            "user": entry.user,
            "security_level": entry.security_level,
            "permission_level": entry.permission_level,
            "result": entry.result,
            "risk_reasons": entry.risk_reasons,
            "execution_time": entry.execution_time,
            "output_hash": entry.output_hash,
            "error": entry.error,
        }, ensure_ascii=False)

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        except Exception as e:
            logger.error(f"写入审计日志失败：{e}")

    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """获取最近的日志"""
        entries = []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            return []

        return entries[-limit:]


# ============================================================================
# 安全审计器
# ============================================================================

@dataclass
class AuditResult:
    """审计结果"""
    allowed: bool
    security_level: SecurityLevel
    risk_reasons: List[str]
    required_permission: PermissionLevel
    message: str

    @classmethod
    def allow(cls, level: SecurityLevel = SecurityLevel.SAFE) -> "AuditResult":
        return cls(
            allowed=True,
            security_level=level,
            risk_reasons=[],
            required_permission=PermissionLevel.USER,
            message="命令安全检查通过"
        )

    @classmethod
    def deny(cls, reasons: List[str], level: SecurityLevel = SecurityLevel.BLOCKED) -> "AuditResult":
        return cls(
            allowed=False,
            security_level=level,
            risk_reasons=reasons,
            required_permission=PermissionLevel.ROOT,
            message="命令被安全策略阻止：" + "; ".join(reasons)
        )

    @classmethod
    def require_confirm(cls, reasons: List[str], level: SecurityLevel = SecurityLevel.MEDIUM_RISK) -> "AuditResult":
        return cls(
            allowed=False,
            security_level=level,
            risk_reasons=reasons,
            required_permission=PermissionLevel.DEVELOPER,
            message="命令需要确认：" + "; ".join(reasons)
        )


class SecurityAuditor:
    """安全审计器"""

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式"""
        self._dangerous_regexes = [
            (re.compile(pattern, re.IGNORECASE), reason)
            for pattern, reason in DANGEROUS_PATTERNS
        ]
        self._confirm_regexes = [
            (re.compile(pattern, re.IGNORECASE), reason)
            for pattern, reason in REQUIRE_CONFIRM_PATTERNS
        ]

    def audit_command(self, command: str,
                      permission: PermissionLevel = PermissionLevel.USER) -> AuditResult:
        """审计命令安全性"""

        # 1. 检查命令长度
        if len(command) > self.config.max_command_length:
            return AuditResult.deny(
                [f"命令长度超出限制 ({len(command)} > {self.config.max_command_length})"]
            )

        cmd_stripped = command.strip().lower()

        # 2. 检查绝对禁止的命令
        for blocked in CRITICAL_BLOCKED_COMMANDS:
            if blocked.lower() in cmd_stripped:
                return AuditResult.deny(
                    [f"包含禁止命令：{blocked}"],
                    SecurityLevel.BLOCKED
                )

        # 3. 检查危险模式
        for regex, reason in self._dangerous_regexes:
            if regex.search(command):
                return AuditResult.deny(
                    [f"危险操作：{reason}"],
                    SecurityLevel.BLOCKED
                )

        # 4. 检查是否需要确认
        require_confirm_reasons = []
        risk_level = SecurityLevel.SAFE

        for regex, reason in self._confirm_regexes:
            if regex.search(command):
                require_confirm_reasons.append(reason)
                risk_level = SecurityLevel.MEDIUM_RISK

        # 5. 检查是否是只读安全命令
        if not require_confirm_reasons:
            for safe_cmd in SAFE_READONLY_COMMANDS:
                if cmd_stripped.startswith(safe_cmd):
                    return AuditResult.allow(SecurityLevel.SAFE)

        # 6. 根据权限级别判断
        if require_confirm_reasons:
            if permission in [PermissionLevel.ADMIN, PermissionLevel.ROOT]:
                return AuditResult.allow(SecurityLevel.LOW_RISK)
            elif permission == PermissionLevel.DEVELOPER:
                return AuditResult.require_confirm(
                    require_confirm_reasons,
                    SecurityLevel.LOW_RISK
                )
            else:
                return AuditResult.require_confirm(
                    require_confirm_reasons,
                    risk_level
                )

        # 7. 默认允许
        return AuditResult.allow(SecurityLevel.LOW_RISK)

    def audit_script(self, script_content: str, filename: str = "<script>") -> List[Dict]:
        """审计脚本内容（静态分析）"""
        issues = []
        lines = script_content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # 跳过注释和空行
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # 审计每一行命令
            result = self.audit_command(stripped)
            if not result.allowed:
                issues.append({
                    "file": filename,
                    "line": line_num,
                    "command": stripped[:100],
                    "security_level": result.security_level.value,
                    "reasons": result.risk_reasons,
                    "message": result.message
                })

        return issues

    def audit_python_code(self, code: str, filename: str = "<code>") -> List[Dict]:
        """审计 Python 代码"""
        issues = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [{
                "file": filename,
                "line": e.lineno or 0,
                "severity": "critical",
                "category": "syntax",
                "message": f"语法错误：{e.msg}"
            }]

        lines = code.split("\n")

        # AST 分析
        for node in ast.walk(tree):
            # 检查危险函数调用
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in ["eval", "exec", "compile", "open", "__import__"]:
                    issues.append({
                        "file": filename,
                        "line": node.lineno,
                        "severity": "critical",
                        "category": "security",
                        "message": f"使用危险函数：{func_name}()",
                        "code": lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                    })

            # 检查 subprocess 调用
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ["system", "popen", "call", "run", "check_output"]:
                        # 检查是否使用 shell=True
                        for keyword in node.keywords:
                            if keyword.arg == "shell":
                                if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                                    issues.append({
                                        "file": filename,
                                        "line": node.lineno,
                                        "severity": "warning",
                                        "category": "security",
                                        "message": "subprocess 使用 shell=True 可能存在注入风险",
                                        "code": lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                                    })

        # 正则模式检查
        security_patterns = [
            (r'eval\s*\(', 'eval() 代码注入风险'),
            (r'exec\s*\(', 'exec() 代码注入风险'),
            (r'os\.system\s*\(', 'os.system() 命令注入风险'),
            (r'pickle\.load', 'pickle 反序列化风险'),
            (r'yaml\.load\s*\([^)]*\)(?!.*Loader)', 'yaml.load() 无 Loader 风险'),
            (r'md5\s*\(|sha1\s*\(', '弱哈希算法'),
            (r'random\.(random|randint|choice)', '非加密安全随机'),
            (r'password\s*=\s*["\'][^"\']+["\']', '硬编码密码'),
            (r'secret\s*=\s*["\'][^"\']+["\']', '硬编码密钥'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', '硬编码 API 密钥'),
            (r'token\s*=\s*["\'][^"\']+["\']', '硬编码 Token'),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, message in security_patterns:
                if re.search(pattern, line):
                    issues.append({
                        "file": filename,
                        "line": i,
                        "severity": "critical" if "密码" in message or "密钥" in message else "warning",
                        "category": "security",
                        "message": message,
                        "code": line.strip()
                    })

        return issues


# ============================================================================
# 沙箱执行器
# ============================================================================

@dataclass
class SandboxResult:
    """沙箱执行结果"""
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0
    execution_time: float = 0.0
    security_violations: List[str] = field(default_factory=list)


class SandboxExecutor:
    """沙箱执行器"""

    def __init__(self,
                 allowed_dirs: Optional[List[str]] = None,
                 allowed_network: bool = False,
                 timeout: int = 60,
                 max_memory_mb: int = 512,
                 user: Optional[str] = None):
        self.allowed_dirs = allowed_dirs or [tempfile.gettempdir()]
        self.allowed_network = allowed_network
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb
        self.user = user
        self._audit_logger: Optional[AuditLogger] = None

    def set_audit_logger(self, logger: AuditLogger):
        """设置审计日志器"""
        self._audit_logger = logger

    def execute(self, command: str,
                auditor: Optional[SecurityAuditor] = None) -> SandboxResult:
        """在沙箱中执行命令"""
        start_time = datetime.now()
        security_violations = []

        # 1. 安全审计
        if auditor:
            audit_result = auditor.audit_command(command)
            if not audit_result.allowed:
                return SandboxResult(
                    success=False,
                    output="",
                    error=audit_result.message,
                    security_violations=audit_result.risk_reasons
                )

        # 2. 构建受限环境
        env = self._build_restricted_env()

        # 3. 执行命令
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                env=env,
                cwd=self.allowed_dirs[0] if self.allowed_dirs else None,
                preexec_fn=self._preexec_fn if hasattr(self, '_preexec_fn') else None,
            )

            try:
                stdout, stderr = process.communicate(
                    timeout=self.timeout,
                    input=b""
                )

                # 限制输出大小
                stdout = self._truncate_output(stdout)
                stderr = self._truncate_output(stderr)

                execution_time = (datetime.now() - start_time).total_seconds()

                # 记录审计日志
                if self._audit_logger:
                    entry = AuditEntry(
                        timestamp=datetime.now().isoformat(),
                        command=command[:500],
                        user=self.user or os.environ.get("USER", "unknown"),
                        security_level="executed",
                        permission_level="user",
                        result="completed" if process.returncode == 0 else "failed",
                        risk_reasons=security_violations,
                        execution_time=execution_time,
                        output_hash=hashlib.sha256(stdout).hexdigest()[:16] if stdout else None,
                        error=stderr.decode()[:200] if stderr and process.returncode != 0 else None
                    )
                    self._audit_logger.log(entry)

                return SandboxResult(
                    success=process.returncode == 0,
                    output=stdout.decode() if stdout else "",
                    error=stderr.decode() if stderr and process.returncode != 0 else None,
                    exit_code=process.returncode,
                    execution_time=execution_time,
                    security_violations=security_violations
                )

            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                return SandboxResult(
                    success=False,
                    output="",
                    error=f"命令执行超时（超过 {self.timeout} 秒）",
                    execution_time=self.timeout,
                    security_violations=["timeout_exceeded"]
                )

        except Exception as e:
            return SandboxResult(
                success=False,
                output="",
                error=f"执行失败：{e}",
                security_violations=[str(e)]
            )

    def _build_restricted_env(self) -> Dict[str, str]:
        """构建受限环境变量"""
        env = os.environ.copy()

        # 移除敏感变量
        sensitive_vars = ["AWS_SECRET_ACCESS_KEY", "PRIVATE_KEY", "PASSWORD"]
        for var in sensitive_vars:
            env.pop(var, None)

        # 设置受限 PATH
        env["PATH"] = "/usr/local/bin:/usr/bin:/bin"

        return env

    def _truncate_output(self, data: bytes, max_size: int = 10 * 1024 * 1024) -> bytes:
        """截断输出"""
        if len(data) > max_size:
            return data[:max_size] + b"\n... [output truncated]"
        return data

    def execute_script_file(self, script_path: str,
                            auditor: Optional[SecurityAuditor] = None) -> SandboxResult:
        """执行脚本文件"""
        # 检查文件是否存在
        if not os.path.exists(script_path):
            return SandboxResult(
                success=False,
                output="",
                error=f"脚本文件不存在：{script_path}"
            )

        # 读取并审计脚本内容
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return SandboxResult(
                success=False,
                output="",
                error=f"读取脚本失败：{e}"
            )

        # 审计脚本
        if auditor:
            issues = auditor.audit_script(content, script_path)
            critical_issues = [i for i in issues if i.get("security_level") == "blocked"]
            if critical_issues:
                return SandboxResult(
                    success=False,
                    output="",
                    error="脚本包含禁止的命令:\n" + "\n".join(
                        f"  行 {i['line']}: {i['message']}" for i in critical_issues
                    ),
                    security_violations=[i["message"] for i in critical_issues]
                )

        # 确定解释器
        interpreter = self._detect_interpreter(script_path, content)
        command = f"{interpreter} {script_path}"

        return self.execute(command, auditor)

    def _detect_interpreter(self, path: str, content: str) -> str:
        """检测脚本解释器"""
        # 检查 shebang
        lines = content.split("\n")
        if lines and lines[0].startswith("#!"):
            shebang = lines[0][2:].strip()
            return shebang.split()[0]  # 返回解释器路径

        # 根据扩展名判断
        ext = Path(path).suffix.lower()
        interpreters = {
            ".py": "python3",
            ".sh": "bash",
            ".js": "node",
            ".rb": "ruby",
            ".pl": "perl",
        }
        return interpreters.get(ext, "bash")


# ============================================================================
# Python 代码沙箱
# ============================================================================

class PythonSandbox:
    """Python 代码沙箱"""

    # 允许的全局函数
    SAFE_GLOBALS = {
        "__builtins__": {
            # 基础函数
            "abs", "all", "any", "ascii", "bin", "bool", "bytes",
            "callable", "chr", "classmethod", "complex",
            "dict", "dir", "divmod", "enumerate", "eval", "exec", "exit",
            "filter", "float", "format", "frozenset",
            "getattr", "hasattr", "hash", "help", "hex", "id", "int",
            "isinstance", "issubclass", "iter", "len", "list", "locals",
            "map", "max", "min", "next", "object", "oct", "ord", "pow",
            "print", "property", "range", "repr", "reversed", "round",
            "set", "setattr", "slice", "sorted", "str", "sum", "super",
            "tuple", "type", "vars", "zip",
            # 常量
            "True", "False", "None",
        }
    }

    # 禁止的模块
    FORBIDDEN_MODULES = {
        "os", "sys", "subprocess", "shutil", "socket",
        "http", "urllib", "requests", "ftplib", "smtplib",
        "pickle", "marshal", "ctypes", "importlib",
        "__import__", "eval", "exec", "compile",
        "open", "file", "io",
        "crypt", "pwd", "grp", "spwd",
        "fcntl", "resource", "termios", "tty",
    }

    def __init__(self, safe_mode: bool = True):
        self.safe_mode = safe_mode
        self._executed_modules: Set[str] = set()

    def execute(self, code: str,
                local_vars: Optional[Dict] = None) -> Tuple[Any, str]:
        """执行 Python 代码（安全模式）"""
        output_capture = []

        # 安全检查
        issues = self._security_check(code)
        if issues:
            raise SecurityError("代码安全检查失败:\n" + "\n".join(issues))

        # 创建受限的 globals
        safe_globals = self._create_safe_globals()
        safe_globals["print"] = lambda *args: output_capture.append(" ".join(map(str, args)))

        # 执行代码
        local_vars = local_vars or {}
        try:
            exec(compile(code, "<sandbox>", "exec"), safe_globals, local_vars)
            return local_vars, "\n".join(output_capture)
        except Exception as e:
            raise ExecutionError(f"代码执行失败：{e}")

    def _security_check(self, code: str) -> List[str]:
        """代码安全检查"""
        issues = []

        # 检查禁止的模块导入
        for module in self.FORBIDDEN_MODULES:
            if re.search(rf'\bimport\s+{module}\b', code):
                issues.append(f"禁止导入模块：{module}")
            if re.search(rf'\bfrom\s+{module}\b', code):
                issues.append(f"禁止从模块导入：{module}")

        # 检查危险函数
        dangerous_funcs = ["eval(", "exec(", "compile(", "open(", "__import__("]
        for func in dangerous_funcs:
            if func in code:
                issues.append(f"禁止使用函数：{func}")

        return issues

    def _create_safe_globals(self) -> Dict:
        """创建安全的 globals 字典"""
        return {
            "__builtins__": self.SAFE_GLOBALS["__builtins__"],
        }


# ============================================================================
# 自定义异常
# ============================================================================

class SecurityError(Exception):
    """安全异常"""
    pass


class ExecutionError(Exception):
    """执行异常"""
    pass


class SandboxEscapeError(Exception):
    """沙箱逃逸尝试"""
    pass


# ============================================================================
# 工具函数
# ============================================================================

def quick_audit(command: str) -> AuditResult:
    """快速审计命令"""
    auditor = SecurityAuditor()
    return auditor.audit_command(command)


def safe_execute(command: str, timeout: int = 30) -> SandboxResult:
    """安全执行命令"""
    auditor = SecurityAuditor()
    executor = SandboxExecutor(timeout=timeout)
    return executor.execute(command, auditor)


def audit_file(file_path: str) -> List[Dict]:
    """审计文件安全性"""
    auditor = SecurityAuditor()

    # 检查文件类型
    ext = Path(file_path).suffix.lower()

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if ext == ".py":
        return auditor.audit_python_code(content, file_path)
    else:
        return auditor.audit_script(content, file_path)


# ============================================================================
# 主函数（命令行工具）
# ============================================================================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="脚本安全审计工具")
    parser.add_argument("action", choices=["audit", "execute", "check"],
                       help="操作类型")
    parser.add_argument("target", help="目标（命令或文件路径）")
    parser.add_argument("--timeout", type=int, default=60,
                       help="执行超时（秒）")
    parser.add_argument("--json", action="store_true",
                       help="输出 JSON 格式")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="详细输出")

    args = parser.parse_args()

    if args.action == "audit":
        # 审计文件
        if not os.path.exists(args.target):
            print(f"错误：文件不存在：{args.target}")
            return 1

        issues = audit_file(args.target)

        if args.json:
            print(json.dumps(issues, ensure_ascii=False, indent=2))
        else:
            if not issues:
                print("✓ 安全检查通过")
            else:
                print(f"发现 {len(issues)} 个问题:")
                for issue in issues:
                    severity = issue.get("severity", "warning")
                    icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(severity, "⚪")
                    print(f"  {icon} 行 {issue.get('line', '?')}: {issue.get('message')}")
                return 1

    elif args.action == "execute":
        # 安全执行命令
        result = safe_execute(args.target, timeout=args.timeout)

        if result.success:
            print(result.output)
        else:
            print(f"执行失败：{result.error}", file=sys.stderr)
            if result.security_violations:
                print(f"安全违规：{result.security_violations}", file=sys.stderr)
            return 1

    elif args.action == "check":
        # 快速检查命令
        audit_result = quick_audit(args.target)

        if args.json:
            print(json.dumps({
                "allowed": audit_result.allowed,
                "security_level": audit_result.security_level.value,
                "required_permission": audit_result.required_permission.value,
                "risk_reasons": audit_result.risk_reasons,
                "message": audit_result.message
            }, ensure_ascii=False))
        else:
            if audit_result.allowed:
                print(f"✓ 命令安全级别：{audit_result.security_level.value}")
            else:
                print(f"✗ {audit_result.message}")
                return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
