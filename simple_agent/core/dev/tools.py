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
import json

from simple_agent.core.tool import BaseTool, ToolResult

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


# ==================== GitWorktreeTool ====================

class GitWorktreeTool(BaseTool):
    """
    Git Worktree 工具（Agent 调用版本）

    Agent 可调用此工具管理多项目开发环境
    """

    @property
    def name(self) -> str:
        return "GitWorktreeTool"

    @property
    def description(self) -> str:
        return "管理 Git Worktree，支持多分支并行开发"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "remove", "list", "get", "switch"],
                    "description": "操作类型"
                },
                "name": {
                    "type": "string",
                    "description": "worktree 名称（create/get/remove/switch 需要）"
                },
                "branch": {
                    "type": "string",
                    "description": "分支名（create 时可选）"
                }
            },
            "required": ["action"]
        }

    def execute(self, action: str = "list", name: Optional[str] = None,
                branch: Optional[str] = None, **kwargs) -> ToolResult:
        """执行 Git Worktree 操作"""
        impl = _GitWorktreeToolImpl()

        try:
            if action == "create":
                result = impl.create(name or "worktree", branch=branch)
            elif action == "remove":
                result = impl.remove(name, force=kwargs.get('force', False))
            elif action == "list":
                result = impl.list()
            elif action == "get":
                result = impl.get(name)
            elif action == "switch":
                result = impl.switch(name)
            else:
                return ToolResult(success=False, output="", error=f"未知操作：{action}")

            return ToolResult(
                success=result.get("success", False),
                output=json.dumps(result, ensure_ascii=False, indent=2)
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class _GitWorktreeToolImpl:
    """Git Worktree 内部实现类"""

    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path or os.getcwd()
        self._manager = None

    @property
    def manager(self):
        if self._manager is None:
            self._manager = get_worktree_manager(self.repo_path)
        return self._manager

    def create(self, name: str, branch: Optional[str] = None, start_point: str = "HEAD", setup_env: bool = True) -> Dict[str, Any]:
        try:
            worktree = self.manager.create_worktree(name, branch, start_point)
            result = {
                "success": True,
                "message": f"已创建 worktree: {name}",
                "worktree": {"name": name, "path": worktree.path, "branch": worktree.branch}
            }
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
            return {"success": False, "message": f"创建 worktree 失败：{e}", "error": str(e)}

    def remove(self, name: str, force: bool = False) -> Dict[str, Any]:
        try:
            self.manager.remove_worktree(name, force)
            return {"success": True, "message": f"已删除 worktree: {name}"}
        except Exception as e:
            return {"success": False, "message": f"删除 worktree 失败：{e}", "error": str(e)}

    def list(self) -> Dict[str, Any]:
        try:
            worktrees = self.manager.list_worktrees()
            return {"success": True, "count": len(worktrees), "worktrees": [wt.to_dict() for wt in worktrees]}
        except Exception as e:
            return {"success": False, "message": f"列出 worktree 失败：{e}", "error": str(e)}

    def get(self, name: str) -> Dict[str, Any]:
        try:
            worktree = self.manager.get_worktree(name)
            if worktree:
                return {"success": True, "worktree": worktree.to_dict()}
            return {"success": False, "message": f"Worktree '{name}' 不存在"}
        except Exception as e:
            return {"success": False, "message": f"获取 worktree 失败：{e}", "error": str(e)}

    def switch(self, name: str) -> Dict[str, Any]:
        try:
            worktree = self.manager.get_worktree(name)
            if not worktree:
                return {"success": False, "message": f"Worktree '{name}' 不存在"}
            return {"success": True, "message": f"Worktree '{name}' 路径：{worktree.path}", "path": worktree.path, "branch": worktree.branch}
        except Exception as e:
            return {"success": False, "message": f"切换 worktree 失败：{e}", "error": str(e)}


# ==================== DevEnvironmentTool ====================

class DevEnvironmentTool(BaseTool):
    """开发环境设置工具（Agent 调用版本）"""

    @property
    def name(self) -> str:
        return "DevEnvironmentTool"

    @property
    def description(self) -> str:
        return "开发环境配置工具，支持 Python/Node.js 项目初始化"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["detect", "init_python", "init_node", "setup_env"],
                    "description": "操作类型"
                },
                "name": {"type": "string", "description": "项目名称"},
                "create_venv": {"type": "boolean", "description": "是否创建虚拟环境"}
            },
            "required": ["action"]
        }

    def execute(self, action: str = "detect", name: Optional[str] = None,
                create_venv: bool = True, **kwargs) -> ToolResult:
        """执行开发环境操作"""
        impl = _DevEnvironmentToolImpl()

        try:
            if action == "detect":
                result = impl.detect()
            elif action == "init_python":
                result = impl.init_python(name or "my_project", create_venv)
            elif action == "init_node":
                result = impl.init_node(name or "my_node_project")
            elif action == "setup_env":
                result = impl.setup_env()
            else:
                return ToolResult(success=False, output="", error=f"未知操作：{action}")

            return ToolResult(
                success=result.get("success", False),
                output=json.dumps(result, ensure_ascii=False, indent=2)
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class _DevEnvironmentToolImpl:
    """开发环境内部实现类"""

    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path or os.getcwd()
        self._setup = None

    @property
    def setup(self):
        if self._setup is None:
            self._setup = get_environment_setup(self.project_path)
        return self._setup

    def detect(self) -> Dict[str, Any]:
        try:
            info = self.setup.detect_environment()
            return {"success": True, "environment": info.to_dict()}
        except Exception as e:
            return {"success": False, "message": f"环境检测失败：{e}", "error": str(e)}

    def init_python(self, name: str, create_venv: bool = True) -> Dict[str, Any]:
        try:
            from .environment_setup import ProjectInitializer
            initializer = ProjectInitializer(self.project_path)
            created = initializer.init_python_project(name, create_venv=create_venv)
            return {"success": True, "message": f"已初始化 Python 项目：{name}", "created": created}
        except Exception as e:
            return {"success": False, "message": f"初始化 Python 项目失败：{e}", "error": str(e)}

    def init_node(self, name: str, typescript: bool = True) -> Dict[str, Any]:
        try:
            from .environment_setup import ProjectInitializer
            initializer = ProjectInitializer(self.project_path)
            created = initializer.init_node_project(name, typescript=typescript)
            return {"success": True, "message": f"已初始化 Node.js 项目：{name}", "created": created}
        except Exception as e:
            return {"success": False, "message": f"初始化 Node.js 项目失败：{e}", "error": str(e)}

    def setup_env(self) -> Dict[str, Any]:
        try:
            result = self.setup.setup(create_venv=True, install_deps=True)
            return {"success": result.success, "message": result.message}
        except Exception as e:
            return {"success": False, "message": f"环境设置失败：{e}", "error": str(e)}


# ==================== DevWorkflowTool ====================

class DevWorkflowTool(BaseTool):
    """开发流程工具（Agent 调用版本）"""

    @property
    def name(self) -> str:
        return "DevWorkflowTool"

    @property
    def description(self) -> str:
        return "开发流程自动化工具，支持 lint/test/build"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["lint", "test", "build", "format", "full_workflow"],
                    "description": "操作类型"
                }
            },
            "required": ["action"]
        }

    def execute(self, action: str = "lint", **kwargs) -> ToolResult:
        """执行开发流程操作"""
        impl = _DevWorkflowToolImpl()

        try:
            if action == "lint":
                result = impl.lint()
            elif action == "test":
                result = impl.test()
            elif action == "build":
                result = impl.build()
            elif action == "format":
                result = impl.format()
            elif action == "full_workflow":
                result = impl.full_workflow()
            else:
                return ToolResult(success=False, output="", error=f"未知操作：{action}")

            return ToolResult(
                success=result.get("success", False),
                output=json.dumps(result, ensure_ascii=False, indent=2)
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class _DevWorkflowToolImpl:
    """开发流程内部实现类"""

    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path or os.getcwd()
        self._runner = None

    @property
    def runner(self):
        if self._runner is None:
            venv_path = os.path.join(self.project_path, ".venv")
            self._runner = get_workflow_runner(self.project_path, venv_path)
        return self._runner

    def lint(self) -> Dict[str, Any]:
        try:
            result = self.runner.run_lint()
            return {"success": result.status.value == "passed", "status": result.status.value, "output": result.output}
        except Exception as e:
            return {"success": False, "message": f"代码检查失败：{e}", "error": str(e)}

    def test(self) -> Dict[str, Any]:
        try:
            result = self.runner.run_test()
            return {"success": result.status.value == "passed", "status": result.status.value, "output": result.output}
        except Exception as e:
            return {"success": False, "message": f"测试失败：{e}", "error": str(e)}

    def build(self) -> Dict[str, Any]:
        try:
            result = self.runner.run_build()
            return {"success": result.status.value == "passed", "status": result.status.value, "output": result.output}
        except Exception as e:
            return {"success": False, "message": f"构建失败：{e}", "error": str(e)}

    def format(self) -> Dict[str, Any]:
        try:
            result = self.runner.run_format()
            return {"success": result.status.value == "passed", "status": result.status.value, "output": result.output}
        except Exception as e:
            return {"success": False, "message": f"格式化失败：{e}", "error": str(e)}

    def full_workflow(self) -> Dict[str, Any]:
        try:
            result = self.runner.run_full_workflow()
            return {"success": result.success, "summary": result.summary}
        except Exception as e:
            return {"success": False, "message": f"工作流失败：{e}", "error": str(e)}


# ==================== CodeReviewTool ====================

class CodeReviewTool(BaseTool):
    """代码审查工具（Agent 调用版本）"""

    @property
    def name(self) -> str:
        return "CodeReviewTool"

    @property
    def description(self) -> str:
        return "代码审查工具，支持文件审查和 diff 审查"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["review_file", "review_diff", "run_linter"],
                    "description": "审查操作类型"
                },
                "file_path": {"type": "string", "description": "文件路径（review_file 需要）"},
                "base_branch": {"type": "string", "description": "基础分支（review_diff 需要）"},
                "target_branch": {"type": "string", "description": "目标分支（review_diff 需要）"}
            },
            "required": ["action"]
        }

    def execute(self, action: str = "review_file", file_path: Optional[str] = None,
                base_branch: Optional[str] = None, target_branch: Optional[str] = None, **kwargs) -> ToolResult:
        """执行代码审查操作"""
        impl = _CodeReviewToolImpl()

        try:
            if action == "review_file":
                if not file_path:
                    return ToolResult(success=False, output="", error="review_file 需要指定 file_path")
                result = impl.review_file(file_path)
            elif action == "review_diff":
                if not base_branch or not target_branch:
                    return ToolResult(success=False, output="", error="review_diff 需要指定 base_branch 和 target_branch")
                result = impl.review_diff(base_branch, target_branch)
            elif action == "run_linter":
                result = impl.run_linter()
            else:
                return ToolResult(success=False, output="", error=f"未知操作：{action}")

            return ToolResult(
                success=result.get("success", False),
                output=json.dumps(result, ensure_ascii=False, indent=2)
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class _CodeReviewToolImpl:
    """代码审查内部实现类"""

    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path or os.getcwd()

    def review_file(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {"success": False, "message": f"文件不存在：{file_path}"}
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        checklist = ["代码规范", "错误处理", "注释", "性能", "安全"]
        return {"success": True, "file": file_path, "content": content[:10000], "checklist": checklist}

    def review_diff(self, base_branch: str, target_branch: str) -> Dict[str, Any]:
        import subprocess
        try:
            result = subprocess.run(["git", "diff", f"{base_branch}..{target_branch}"],
                                    cwd=self.project_path, capture_output=True, text=True)
            if result.returncode != 0:
                return {"success": False, "message": f"获取 diff 失败：{result.stderr}"}
            return {"success": True, "base_branch": base_branch, "target_branch": target_branch, "diff": result.stdout[:10000]}
        except Exception as e:
            return {"success": False, "message": f"审查差异失败：{e}", "error": str(e)}

    def run_linter(self) -> Dict[str, Any]:
        workflow = _DevWorkflowToolImpl(self.project_path)
        return workflow.lint()


# ==================== 旧版兼容类（保留向后兼容） ====================

class GitWorktreeToolLegacy:
    """旧版 GitWorktreeTool（保留向后兼容）"""
    name = "GitWorktreeTool"
    description = "Git Worktree 管理工具"
    # 推荐使用新的 GitWorktreeTool 类

class DevEnvironmentToolLegacy:
    """旧版 DevEnvironmentTool（保留向后兼容）"""
    name = "DevEnvironmentTool"
    description = "开发环境配置工具"

class DevWorkflowToolLegacy:
    """旧版 DevWorkflowTool（保留向后兼容）"""
    name = "DevWorkflowTool"
    description = "开发流程自动化工具"

class CodeReviewToolLegacy:
    """旧版 CodeReviewTool（保留向后兼容）"""
    name = "CodeReviewTool"
    description = "代码审查工具"
