"""
Development Workflow Automation - 开发流程自动化

支持：
1. 代码检查 (lint)
2. 代码格式化 (format)
3. 类型检查 (type check)
4. 测试运行 (test)
5. 构建 (build)
6. 代码审查 (code review)
"""

import os
import subprocess
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time


class CheckStatus(Enum):
    """检查结果状态"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class CheckResult:
    """检查结果"""
    name: str
    status: CheckStatus
    message: str
    duration: float = 0.0
    output: str = ""
    errors: str = ""
    files_checked: int = 0
    issues_found: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "duration": self.duration,
            "files_checked": self.files_checked,
            "issues_found": self.issues_found,
            "output": self.output[:500] if len(self.output) > 500 else self.output
        }


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    success: bool
    results: List[CheckResult] = field(default_factory=list)
    total_duration: float = 0.0
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "total_duration": self.total_duration,
            "summary": self.summary,
            "results": [r.to_dict() for r in self.results]
        }


class DevWorkflowRunner:
    """
    开发流程运行器

    支持的工作流：
    - lint: 代码检查
    - format: 代码格式化
    - typecheck: 类型检查
    - test: 运行测试
    - build: 构建项目
    - review: 代码审查

    使用示例:
    ```python
    runner = DevWorkflowRunner(project_path="/path/to/project")

    # 运行单一流程
    result = runner.run_lint()

    # 运行完整流程
    result = runner.run_full_workflow()

    # 自定义流程
    result = runner.run_workflow(["lint", "test", "build"])
    ```
    """

    def __init__(
        self,
        project_path: str,
        venv_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化运行器

        Args:
            project_path: 项目路径
            venv_path: 虚拟环境路径
            config: 配置选项
        """
        self.project_path = os.path.abspath(project_path)
        self.venv_path = venv_path or os.path.join(self.project_path, ".venv")
        self.config = config or {}

        # 工具配置
        self.tools_config = self.config.get("tools", {})

    def _get_env(self) -> Dict[str, str]:
        """获取环境变量（包含虚拟环境）"""
        env = os.environ.copy()

        # 添加虚拟环境到 PATH
        if os.path.exists(self.venv_path):
            bin_dir = os.path.join(self.venv_path, "bin")
            if os.path.exists(bin_dir):
                env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
            else:
                bin_dir = os.path.join(self.venv_path, "Scripts")
                if os.path.exists(bin_dir):
                    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"

        # 添加 node_modules/.bin
        node_bin = os.path.join(self.project_path, "node_modules", ".bin")
        if os.path.exists(node_bin):
            env["PATH"] = f"{node_bin}:{env.get('PATH', '')}"

        # 设置 PYTHONPATH
        src_dir = os.path.join(self.project_path, "src")
        if os.path.exists(src_dir):
            env["PYTHONPATH"] = f"{src_dir}:{env.get('PYTHONPATH', '')}"

        return env

    def _run_command(
        self,
        cmd: List[str],
        cwd: Optional[str] = None,
        timeout: int = 300
    ) -> Tuple[int, str, str]:
        """
        运行命令

        Returns:
            Tuple: (returncode, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_path,
                env=self._get_env(),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"命令超时（>{timeout}s）"
        except FileNotFoundError as e:
            return -127, "", f"命令未找到：{cmd[0]}"

    def _check_tool_installed(self, tool_name: str, install_cmd: Optional[str] = None) -> bool:
        """检查工具是否已安装"""
        returncode, _, _ = self._run_command(["which", tool_name])
        if returncode == 0:
            return True

        # 尝试在虚拟环境中查找
        if os.path.exists(self.venv_path):
            tool_path = os.path.join(self.venv_path, "bin", tool_name)
            if os.path.exists(tool_path):
                return True
            tool_path = os.path.join(self.venv_path, "Scripts", tool_name)
            if os.path.exists(tool_path):
                return True

        return False

    def run_lint(
        self,
        tool: Optional[str] = None,
        path: Optional[str] = None,
        fix: bool = False
    ) -> CheckResult:
        """
        运行代码检查

        Args:
            tool: 检查工具 (flake8, pylint, eslint)，自动检测
            path: 检查路径，默认为项目根目录
            fix: 是否自动修复

        Returns:
            CheckResult: 检查结果
        """
        start_time = time.time()
        path = path or self.project_path

        # 自动检测工具
        if tool is None:
            if self._check_tool_installed("flake8"):
                tool = "flake8"
            elif self._check_tool_installed("pylint"):
                tool = "pylint"
            elif self._check_tool_installed("eslint"):
                tool = "eslint"
            else:
                return CheckResult(
                    name="lint",
                    status=CheckStatus.SKIPPED,
                    message="未找到 lint 工具（flake8/pylint/eslint）",
                    duration=time.time() - start_time
                )

        # 构建命令
        if tool == "flake8":
            cmd = ["flake8", "--count", "--show-source", "--statistics"]
        elif tool == "pylint":
            cmd = ["pylint"]
        elif tool == "eslint":
            cmd = ["eslint", "--format", "stylish"]
        else:
            cmd = [tool]

        if fix:
            if tool == "flake8":
                pass  # flake8 不支持自动修复
            elif tool == "pylint":
                pass
            elif tool == "eslint":
                cmd.append("--fix")

        cmd.append(path)

        # 运行
        returncode, stdout, stderr = self._run_command(cmd)

        # 解析结果
        duration = time.time() - start_time
        if returncode == 0:
            status = CheckStatus.PASSED
            message = "代码检查通过"
        elif returncode > 0:
            status = CheckStatus.FAILED
            message = f"发现代码问题"
        else:
            status = CheckStatus.FAILED
            message = f"检查失败：{stderr[:100]}"

        # 统计问题数
        issues_found = stdout.count("\n") if stdout else 0

        return CheckResult(
            name=f"lint ({tool})",
            status=status,
            message=message,
            duration=duration,
            output=stdout,
            errors=stderr,
            issues_found=issues_found
        )

    def run_format(
        self,
        tool: Optional[str] = None,
        path: Optional[str] = None,
        check_only: bool = False
    ) -> CheckResult:
        """
        运行代码格式化

        Args:
            tool: 格式化工具 (black, autopep8, prettier)，自动检测
            path: 格式化路径
            check_only: 是否仅检查（不修改）

        Returns:
            CheckResult: 检查结果
        """
        start_time = time.time()
        path = path or self.project_path

        # 自动检测工具
        if tool is None:
            if self._check_tool_installed("black"):
                tool = "black"
            elif self._check_tool_installed("autopep8"):
                tool = "autopep8"
            elif self._check_tool_installed("prettier"):
                tool = "prettier"
            else:
                return CheckResult(
                    name="format",
                    status=CheckStatus.SKIPPED,
                    message="未找到格式化工具（black/autopep8/prettier）",
                    duration=time.time() - start_time
                )

        # 构建命令
        if tool == "black":
            cmd = ["black"]
            if check_only:
                cmd.extend(["--check", "--diff"])
        elif tool == "autopep8":
            cmd = ["autopep8"]
            if check_only:
                cmd.append("--diff")
        elif tool == "prettier":
            cmd = ["prettier", "--write" if not check_only else "--check"]
        else:
            cmd = [tool]

        cmd.append(path)

        # 运行
        returncode, stdout, stderr = self._run_command(cmd)

        duration = time.time() - start_time
        if returncode == 0:
            status = CheckStatus.PASSED
            message = "代码格式化完成" if not check_only else "代码格式正确"
        else:
            status = CheckStatus.FAILED
            message = "代码需要格式化" if check_only else "格式化失败"

        return CheckResult(
            name=f"format ({tool})",
            status=status,
            message=message,
            duration=duration,
            output=stdout,
            errors=stderr
        )

    def run_typecheck(
        self,
        tool: Optional[str] = None,
        path: Optional[str] = None
    ) -> CheckResult:
        """
        运行类型检查

        Args:
            tool: 类型检查工具 (mypy, pyright, tsc)，自动检测
            path: 检查路径

        Returns:
            CheckResult: 检查结果
        """
        start_time = time.time()
        path = path or self.project_path

        # 自动检测工具
        if tool is None:
            if self._check_tool_installed("mypy"):
                tool = "mypy"
            elif self._check_tool_installed("pyright"):
                tool = "pyright"
            elif self._check_tool_installed("tsc"):
                tool = "tsc"
            else:
                return CheckResult(
                    name="typecheck",
                    status=CheckStatus.SKIPPED,
                    message="未找到类型检查工具（mypy/pyright/tsc）",
                    duration=time.time() - start_time
                )

        # 构建命令
        if tool == "mypy":
            cmd = ["mypy", "--pretty", "--show-error-codes"]
        elif tool == "pyright":
            cmd = ["pyright"]
        elif tool == "tsc":
            cmd = ["tsc", "--noEmit"]
        else:
            cmd = [tool]

        # 检查是否有配置文件
        if tool == "mypy" and os.path.exists(os.path.join(path, "mypy.ini")):
            pass  # 使用配置文件
        elif tool == "mypy" and os.path.exists(os.path.join(path, "pyproject.toml")):
            pass  # 使用 pyproject.toml
        else:
            cmd.append(path)

        # 运行
        returncode, stdout, stderr = self._run_command(cmd, timeout=600)

        duration = time.time() - start_time
        if returncode == 0:
            status = CheckStatus.PASSED
            message = "类型检查通过"
        else:
            status = CheckStatus.FAILED
            message = "发现类型错误"

        return CheckResult(
            name=f"typecheck ({tool})",
            status=status,
            message=message,
            duration=duration,
            output=stdout,
            errors=stderr
        )

    def run_test(
        self,
        tool: Optional[str] = None,
        path: Optional[str] = None,
        args: Optional[List[str]] = None
    ) -> CheckResult:
        """
        运行测试

        Args:
            tool: 测试工具 (pytest, unittest, jest)，自动检测
            path: 测试路径
            args: 额外参数

        Returns:
            CheckResult: 检查结果
        """
        start_time = time.time()
        path = path or os.path.join(self.project_path, "tests")
        args = args or []

        # 自动检测工具
        if tool is None:
            # 检查项目类型
            if os.path.exists(os.path.join(self.project_path, "package.json")):
                # Node.js 项目
                if self._check_tool_installed("jest"):
                    tool = "jest"
                else:
                    tool = "npm"
                    args = ["test"]
            else:
                # Python 项目
                if self._check_tool_installed("pytest"):
                    tool = "pytest"
                elif self._check_tool_installed("unittest"):
                    tool = "python"
                    args = ["-m", "unittest"]
                else:
                    return CheckResult(
                        name="test",
                        status=CheckStatus.SKIPPED,
                        message="未找到测试工具（pytest/unittest/jest）",
                        duration=time.time() - start_time
                    )

        # 构建命令
        if tool == "pytest":
            cmd = ["pytest", "-v", "--tb=short"]
        elif tool == "python":  # unittest
            cmd = ["python", "-m", "unittest", "discover"]
        elif tool == "jest":
            cmd = ["jest"]
        elif tool == "npm":
            cmd = ["npm"]
        else:
            cmd = [tool]

        cmd.extend(args)

        if tool not in ["npm", "python"]:
            if os.path.exists(path):
                cmd.append(path)

        # 运行
        returncode, stdout, stderr = self._run_command(cmd, timeout=600)

        duration = time.time() - start_time
        if returncode == 0:
            status = CheckStatus.PASSED
            message = "所有测试通过"
        else:
            status = CheckStatus.FAILED
            message = "测试失败"

        return CheckResult(
            name=f"test ({tool or 'auto'})",
            status=status,
            message=message,
            duration=duration,
            output=stdout,
            errors=stderr
        )

    def run_build(
        self,
        tool: Optional[str] = None,
        args: Optional[List[str]] = None
    ) -> CheckResult:
        """
        运行构建

        Args:
            tool: 构建工具 (setuptools, poetry, npm, webpack)，自动检测
            args: 额外参数

        Returns:
            CheckResult: 检查结果
        """
        start_time = time.time()
        args = args or []

        # 自动检测工具
        if tool is None:
            if os.path.exists(os.path.join(self.project_path, "package.json")):
                # 检查是否有 build 脚本
                try:
                    with open(os.path.join(self.project_path, "package.json")) as f:
                        pkg = json.load(f)
                        if "build" in pkg.get("scripts", {}):
                            tool = "npm"
                            args = ["run", "build"]
                        elif os.path.exists(os.path.join(self.project_path, "webpack.config.js")):
                            tool = "webpack"
                        else:
                            tool = "tsc"  # TypeScript 项目
                except Exception:
                    tool = "npm"
            elif os.path.exists(os.path.join(self.project_path, "pyproject.toml")):
                tool = "python"
                args = ["-m", "build"]
            elif os.path.exists(os.path.join(self.project_path, "setup.py")):
                tool = "python"
                args = ["setup.py", "sdist", "bdist_wheel"]
            else:
                return CheckResult(
                    name="build",
                    status=CheckStatus.SKIPPED,
                    message="未找到构建配置（setup.py/pyproject.toml/package.json）",
                    duration=time.time() - start_time
                )

        # 构建命令
        if tool == "python":
            cmd = ["python"] + args
        elif tool == "npm":
            cmd = ["npm"] + args
        elif tool == "webpack":
            cmd = ["webpack"]
        elif tool == "tsc":
            cmd = ["tsc"]
        else:
            cmd = [tool]

        # 运行
        returncode, stdout, stderr = self._run_command(cmd, timeout=600)

        duration = time.time() - start_time
        if returncode == 0:
            status = CheckStatus.PASSED
            message = "构建成功"
        else:
            status = CheckStatus.FAILED
            message = "构建失败"

        return CheckResult(
            name=f"build ({tool})",
            status=status,
            message=message,
            duration=duration,
            output=stdout,
            errors=stderr
        )

    def run_workflow(
        self,
        steps: List[str],
        stop_on_failure: bool = True
    ) -> WorkflowResult:
        """
        运行自定义工作流

        Args:
            steps: 步骤列表 ["lint", "test", "build"]
            stop_on_failure: 失败时是否停止

        Returns:
            WorkflowResult: 工作流结果
        """
        start_time = time.time()
        results = []
        success = True

        step_methods = {
            "lint": self.run_lint,
            "format": self.run_format,
            "typecheck": self.run_typecheck,
            "test": self.run_test,
            "build": self.run_build
        }

        for step in steps:
            if step not in step_methods:
                results.append(CheckResult(
                    name=step,
                    status=CheckStatus.SKIPPED,
                    message=f"未知步骤：{step}"
                ))
                continue

            result = step_methods[step]()
            results.append(result)

            if result.status == CheckStatus.FAILED and stop_on_failure:
                success = False
                break

        total_duration = time.time() - start_time

        # 生成总结
        passed = sum(1 for r in results if r.status == CheckStatus.PASSED)
        failed = sum(1 for r in results if r.status == CheckStatus.FAILED)
        skipped = sum(1 for r in results if r.status == CheckStatus.SKIPPED)

        summary = f"完成 {passed}/{len(results)} 个步骤"
        if failed > 0:
            summary += f", {failed} 个失败"
        if skipped > 0:
            summary += f", {skipped} 个跳过"

        return WorkflowResult(
            success=success,
            results=results,
            total_duration=total_duration,
            summary=summary
        )

    def run_full_workflow(self) -> WorkflowResult:
        """
        运行完整开发流程

        流程：lint → format (check) → typecheck → test → build

        Returns:
            WorkflowResult: 工作流结果
        """
        return self.run_workflow(
            ["lint", "format", "typecheck", "test", "build"],
            stop_on_failure=False
        )


# ==================== Factory Function ====================

def get_workflow_runner(
    project_path: str,
    venv_path: Optional[str] = None,
    config: Optional[Dict] = None
) -> DevWorkflowRunner:
    """获取开发流程运行器"""
    return DevWorkflowRunner(project_path, venv_path, config)
