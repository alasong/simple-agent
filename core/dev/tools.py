"""
Development Tools for Agents - Agent 开发工具封装

提供 Agent 可调用的开发工具：
1. GitWorktreeTool - Worktree 管理
2. DevEnvironmentTool - 环境设置
3. DevWorkflowTool - 开发流程
4. CodeReviewTool - 代码审查
"""

from typing import Optional, Dict, Any, List
import os
import sys

# 延迟导入，避免循环依赖
def get_worktree_manager(repo_path: Optional[str] = None):
    from .git_worktree import get_worktree_manager as _get_manager
    return _get_manager(repo_path)


def get_environment_setup(project_path: str):
    from .environment_setup import get_environment_setup as _get_setup
    return _get_setup(project_path)


def get_workflow_runner(project_path: str, venv_path: Optional[str] = None, config: Optional[Dict] = None):
    from .workflow import get_workflow_runner as _get_runner
    return _get_runner(project_path, venv_path, config)


class GitWorktreeTool:
    """
    Git Worktree 工具

    Agent 可调用此工具管理多项目开发环境

    使用示例 (Agent 调用):
    ```python
    tool = GitWorktreeTool()

    # 创建新的开发分支
    result = tool.create("feature-login", branch="feature/login")

    # 列出所有 worktrees
    worktrees = tool.list()

    # 删除 worktree
    tool.remove("feature-login")
    ```
    """

    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path or os.getcwd()
        self._manager = None

    @property
    def manager(self):
        if self._manager is None:
            self._manager = get_worktree_manager(self.repo_path)
        return self._manager

    def create(
        self,
        name: str,
        branch: Optional[str] = None,
        start_point: str = "HEAD",
        setup_env: bool = True
    ) -> Dict[str, Any]:
        """
        创建新的 worktree

        Args:
            name: worktree 名称
            branch: 分支名
            start_point: 起始点
            setup_env: 是否设置环境

        Returns:
            Dict: 创建结果
        """
        try:
            worktree = self.manager.create_worktree(name, branch, start_point)

            result = {
                "success": True,
                "message": f"已创建 worktree: {name}",
                "worktree": {
                    "name": name,
                    "path": worktree.path,
                    "branch": worktree.branch
                }
            }

            # 设置独立环境
            if setup_env:
                try:
                    self.manager.setup_environment(worktree)
                    result["message"] += " [环境已初始化]"
                    result["worktree"]["env_ready"] = True
                except Exception as e:
                    result["message"] += f" [环境创建失败：{e}]"
                    result["worktree"]["env_ready"] = False

            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"创建 worktree 失败：{e}",
                "error": str(e)
            }

    def remove(self, name: str, force: bool = False) -> Dict[str, Any]:
        """删除 worktree"""
        try:
            self.manager.remove_worktree(name, force)
            return {
                "success": True,
                "message": f"已删除 worktree: {name}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"删除 worktree 失败：{e}",
                "error": str(e)
            }

    def list(self) -> Dict[str, Any]:
        """列出所有 worktrees"""
        try:
            worktrees = self.manager.list_worktrees()
            return {
                "success": True,
                "count": len(worktrees),
                "worktrees": [wt.to_dict() for wt in worktrees]
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"列出 worktree 失败：{e}",
                "error": str(e)
            }

    def get(self, name: str) -> Dict[str, Any]:
        """获取 worktree 信息"""
        try:
            worktree = self.manager.get_worktree(name)
            if worktree:
                return {
                    "success": True,
                    "worktree": worktree.to_dict()
                }
            else:
                return {
                    "success": False,
                    "message": f"Worktree '{name}' 不存在"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取 worktree 失败：{e}",
                "error": str(e)
            }

    def switch(self, name: str) -> Dict[str, Any]:
        """切换到 worktree 目录"""
        try:
            worktree = self.manager.get_worktree(name)
            if not worktree:
                return {
                    "success": False,
                    "message": f"Worktree '{name}' 不存在"
                }

            # 返回工作目录信息，供 Agent 参考
            return {
                "success": True,
                "message": f"Worktree '{name}' 路径：{worktree.path}",
                "path": worktree.path,
                "branch": worktree.branch
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"切换 worktree 失败：{e}",
                "error": str(e)
            }


class DevEnvironmentTool:
    """
    开发环境设置工具

    Agent 可调用此工具初始化项目环境
    """

    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path or os.getcwd()
        self._setup = None

    @property
    def setup(self):
        if self._setup is None:
            self._setup = get_environment_setup(self.project_path)
        return self._setup

    def detect(self) -> Dict[str, Any]:
        """检测项目环境"""
        try:
            info = self.setup.detect_environment()
            return {
                "success": True,
                "environment": info.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"环境检测失败：{e}",
                "error": str(e)
            }

    def init_python(self, name: str, create_venv: bool = True) -> Dict[str, Any]:
        """初始化 Python 项目"""
        try:
            from .environment_setup import ProjectInitializer
            initializer = ProjectInitializer(self.project_path)
            created = initializer.init_python_project(name, create_venv=create_venv)
            return {
                "success": True,
                "message": f"已初始化 Python 项目：{name}",
                "created": created
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"初始化 Python 项目失败：{e}",
                "error": str(e)
            }

    def init_node(self, name: str, typescript: bool = True) -> Dict[str, Any]:
        """初始化 Node.js 项目"""
        try:
            from .environment_setup import ProjectInitializer
            initializer = ProjectInitializer(self.project_path)
            created = initializer.init_node_project(name, typescript=typescript)
            return {
                "success": True,
                "message": f"已初始化 Node.js 项目：{name}",
                "created": created
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"初始化 Node.js 项目失败：{e}",
                "error": str(e)
            }

    def setup_env(self, language: Optional[str] = None) -> Dict[str, Any]:
        """设置开发环境"""
        try:
            from .environment_setup import LanguageType
            lang = LanguageType(language) if language else None
            result = self.setup.setup(create_venv=True, install_deps=True, language=lang)

            return {
                "success": result.success,
                "message": result.message,
                "warnings": result.warnings,
                "errors": result.errors,
                "environment": result.env_info.to_dict() if result.env_info else None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"环境设置失败：{e}",
                "error": str(e)
            }

    def run_command(self, command: str) -> Dict[str, Any]:
        """在项目环境中运行命令"""
        try:
            import subprocess
            result = self.setup.run_command(command.split())
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"命令执行失败：{e}",
                "error": str(e)
            }


class DevWorkflowTool:
    """
    开发流程工具

    Agent 可调用此工具运行 lint、test、build 等流程
    """

    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path or os.getcwd()
        self._runner = None

    @property
    def runner(self):
        if self._runner is None:
            venv_path = os.path.join(self.project_path, ".venv")
            self._runner = get_workflow_runner(self.project_path, venv_path)
        return self._runner

    def lint(self, path: Optional[str] = None, fix: bool = False) -> Dict[str, Any]:
        """运行代码检查"""
        try:
            result = self.runner.run_lint(path=path, fix=fix)
            return {
                "success": result.status.value == "passed",
                "status": result.status.value,
                "message": result.message,
                "output": result.output,
                "issues_found": result.issues_found
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"代码检查失败：{e}",
                "error": str(e)
            }

    def format(self, check_only: bool = False) -> Dict[str, Any]:
        """运行代码格式化"""
        try:
            result = self.runner.run_format(check_only=check_only)
            return {
                "success": result.status.value == "passed",
                "status": result.status.value,
                "message": result.message,
                "output": result.output
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"代码格式化失败：{e}",
                "error": str(e)
            }

    def typecheck(self) -> Dict[str, Any]:
        """运行类型检查"""
        try:
            result = self.runner.run_typecheck()
            return {
                "success": result.status.value == "passed",
                "status": result.status.value,
                "message": result.message,
                "output": result.output
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"类型检查失败：{e}",
                "error": str(e)
            }

    def test(self, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """运行测试"""
        try:
            result = self.runner.run_test(args=args)
            return {
                "success": result.status.value == "passed",
                "status": result.status.value,
                "message": result.message,
                "output": result.output
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"测试失败：{e}",
                "error": str(e)
            }

    def build(self) -> Dict[str, Any]:
        """运行构建"""
        try:
            result = self.runner.run_build()
            return {
                "success": result.status.value == "passed",
                "status": result.status.value,
                "message": result.message,
                "output": result.output
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"构建失败：{e}",
                "error": str(e)
            }

    def full_workflow(self) -> Dict[str, Any]:
        """运行完整开发流程"""
        try:
            result = self.runner.run_full_workflow()
            return {
                "success": result.success,
                "summary": result.summary,
                "total_duration": result.total_duration,
                "results": [r.to_dict() for r in result.results]
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"工作流执行失败：{e}",
                "error": str(e)
            }

    def custom_workflow(self, steps: List[str]) -> Dict[str, Any]:
        """运行自定义工作流"""
        try:
            result = self.runner.run_workflow(steps)
            return {
                "success": result.success,
                "summary": result.summary,
                "total_duration": result.total_duration,
                "results": [r.to_dict() for r in result.results]
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"工作流执行失败：{e}",
                "error": str(e)
            }


class CodeReviewTool:
    """
    代码审查工具

    Agent 可调用此工具进行代码审查
    """

    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path or os.getcwd()

    def review_file(
        self,
        file_path: str,
        checklist: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        审查单个文件

        Args:
            file_path: 文件路径
            checklist: 检查清单

        Returns:
            Dict: 审查结果
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"文件不存在：{file_path}"
            }

        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 默认检查清单
        if checklist is None:
            checklist = [
                "代码是否遵循命名规范",
                "是否有适当的错误处理",
                "是否有必要的注释",
                "是否有潜在的性能问题",
                "是否有安全隐患"
            ]

        # 返回文件内容供 Agent 审查
        return {
            "success": True,
            "file": file_path,
            "content": content,
            "checklist": checklist,
            "message": "请审查以上代码内容"
        }

    def review_diff(
        self,
        base_branch: str,
        target_branch: str
    ) -> Dict[str, Any]:
        """
        审查分支差异

        Args:
            base_branch: 基础分支
            target_branch: 目标分支

        Returns:
            Dict: 审查结果
        """
        import subprocess

        try:
            result = subprocess.run(
                ["git", "diff", f"{base_branch}..{target_branch}"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"获取 diff 失败：{result.stderr}"
                }

            return {
                "success": True,
                "base_branch": base_branch,
                "target_branch": target_branch,
                "diff": result.stdout,
                "message": "请审查以上代码变更"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"审查差异失败：{e}",
                "error": str(e)
            }

    def run_linter(self, path: Optional[str] = None) -> Dict[str, Any]:
        """运行代码检查工具进行审查"""
        workflow = DevWorkflowTool(self.project_path)
        return workflow.lint(path=path)
