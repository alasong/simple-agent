"""
Git Worktree Manager - 多项目开发支持

支持：
1. 创建/删除 worktree
2. 独立虚拟环境管理
3. 分支隔离
4. 项目上下文切换
"""

import os
import subprocess
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import shutil


@dataclass
class WorktreeInfo:
    """Worktree 信息"""
    path: str
    branch: str
    head: str
    is_locked: bool = False
    created_at: Optional[str] = None

    @property
    def env_dir(self) -> str:
        """虚拟环境路径"""
        return os.path.join(self.path, ".venv")

    @property
    def is_venv_created(self) -> bool:
        """是否已创建虚拟环境"""
        return os.path.exists(self.env_dir)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "branch": self.branch,
            "head": self.head,
            "is_locked": self.is_locked,
            "created_at": self.created_at,
            "is_venv_created": self.is_venv_created
        }


class GitWorktreeManager:
    """
    Git Worktree 管理器

    使用示例:
    ```python
    manager = GitWorktreeManager(repo_path="/path/to/repo")

    # 创建新的 worktree
    worktree = manager.create_worktree(
        name="feature-xxx",
        branch="feature/new-feature",
        start_point="main"
    )

    # 初始化独立环境
    manager.setup_environment(worktree, python_version="3.12")

    # 列出所有 worktrees
    worktrees = manager.list_worktrees()

    # 切换到 worktree
    manager.checkout(worktree.path)

    # 删除 worktree
    manager.remove_worktree("feature-xxx")
    ```
    """

    def __init__(self, repo_path: Optional[str] = None):
        """
        初始化 worktree 管理器

        Args:
            repo_path: Git 仓库路径，默认为当前目录
        """
        self.repo_path = repo_path or os.getcwd()
        self._validate_git_repo()

    def _validate_git_repo(self):
        """验证是否为 git 仓库"""
        git_dir = os.path.join(self.repo_path, ".git")
        if not os.path.exists(git_dir):
            raise ValueError(f"{self.repo_path} 不是 git 仓库")

    def _run_git(self, args: List[str], capture: bool = True) -> subprocess.CompletedProcess:
        """运行 git 命令"""
        cmd = ["git"] + args
        kwargs = {
            "cwd": self.repo_path,
            "capture_output": capture,
            "text": True
        }
        try:
            return subprocess.run(cmd, **kwargs)
        except FileNotFoundError:
            raise RuntimeError("git 命令未安装，请先安装 git")

    def create_worktree(
        self,
        name: str,
        branch: Optional[str] = None,
        start_point: str = "HEAD",
        force: bool = False
    ) -> WorktreeInfo:
        """
        创建新的 worktree

        Args:
            name: worktree 名称（也是目录名和分支名）
            branch: 分支名，默认为 name
            start_point: 起始点（分支/提交），默认为 HEAD
            force: 是否强制创建

        Returns:
            WorktreeInfo: 创建的 worktree 信息
        """
        branch = branch or name
        worktree_path = os.path.join(self.repo_path, ".worktrees", name)

        # 创建 .worktrees 目录
        os.makedirs(os.path.dirname(worktree_path), exist_ok=True)

        # 构建命令
        args = ["worktree", "add"]
        if force:
            args.append("-f")
        args.extend(["-b", branch, worktree_path, start_point])

        result = self._run_git(args)
        if result.returncode != 0:
            raise RuntimeError(f"创建 worktree 失败：{result.stderr}")

        # 记录创建时间
        created_at = datetime.now().isoformat()
        metadata_file = os.path.join(worktree_path, ".worktree_meta.json")
        with open(metadata_file, "w") as f:
            json.dump({
                "name": name,
                "branch": branch,
                "created_at": created_at,
                "parent_repo": self.repo_path
            }, f, indent=2)

        return WorktreeInfo(
            path=worktree_path,
            branch=branch,
            head=start_point,
            created_at=created_at
        )

    def remove_worktree(self, name: str, force: bool = False) -> bool:
        """
        删除 worktree

        Args:
            name: worktree 名称
            force: 是否强制删除

        Returns:
            bool: 是否成功删除
        """
        worktree_path = os.path.join(self.repo_path, ".worktrees", name)

        if not os.path.exists(worktree_path):
            # 尝试作为路径直接删除
            if not os.path.exists(name):
                raise ValueError(f"Worktree '{name}' 不存在")
            worktree_path = name

        # 先删除虚拟环境（如果存在）
        env_dir = os.path.join(worktree_path, ".venv")
        if os.path.exists(env_dir):
            shutil.rmtree(env_dir)

        # 删除 worktree
        args = ["worktree", "remove"]
        if force:
            args.append("-f")
        args.append(worktree_path)

        result = self._run_git(args)
        if result.returncode != 0:
            # 如果 git 命令失败，尝试直接删除目录
            if force:
                shutil.rmtree(worktree_path, ignore_errors=True)
                return True
            raise RuntimeError(f"删除 worktree 失败：{result.stderr}")

        return True

    def list_worktrees(self) -> List[WorktreeInfo]:
        """
        列出所有 worktrees

        Returns:
            List[WorktreeInfo]: worktree 列表
        """
        result = self._run_git(["worktree", "list", "--porcelain"])
        if result.returncode != 0:
            raise RuntimeError(f"列出 worktree 失败：{result.stderr}")

        worktrees = []
        current_worktree = None

        for line in result.stdout.split("\n"):
            line = line.strip()
            if not line:
                if current_worktree:
                    worktrees.append(current_worktree)
                    current_worktree = None
                continue

            if line.startswith("worktree "):
                path = line.split(" ", 1)[1]
                current_worktree = WorktreeInfo(
                    path=path,
                    branch="",
                    head=""
                )
            elif line.startswith("HEAD ") and current_worktree:
                current_worktree.head = line.split(" ", 1)[1]
            elif line.startswith("branch ") and current_worktree:
                branch_ref = line.split(" ", 1)[1]
                current_worktree.branch = branch_ref.replace("refs/heads/", "")
            elif line.startswith("locked ") and current_worktree:
                current_worktree.is_locked = True

        return worktrees

    def get_worktree(self, name: str) -> Optional[WorktreeInfo]:
        """
        获取指定 worktree 信息

        Args:
            name: worktree 名称或路径

        Returns:
            Optional[WorktreeInfo]: worktree 信息，不存在则返回 None
        """
        worktrees = self.list_worktrees()
        for wt in worktrees:
            # 按名称匹配（目录名）
            if os.path.basename(wt.path) == name or wt.path == name:
                return wt
        return None

    def checkout(self, worktree_path: str) -> bool:
        """
        切换到 worktree

        Args:
            worktree_path: worktree 路径

        Returns:
            bool: 是否成功切换
        """
        if not os.path.exists(worktree_path):
            raise ValueError(f"Worktree '{worktree_path}' 不存在")

        # 在 worktree 目录中运行 git 命令
        cmd = ["git", "checkout", "."]
        result = subprocess.run(
            cmd,
            cwd=worktree_path,
            capture_output=True,
            text=True
        )
        return result.returncode == 0

    def setup_environment(
        self,
        worktree: WorktreeInfo,
        python_version: Optional[str] = None,
        install_deps: bool = True,
        requirements_file: Optional[str] = None
    ) -> bool:
        """
        为 worktree 创建独立的虚拟环境

        Args:
            worktree: worktree 信息
            python_version: Python 版本，如 "3.12"
            install_deps: 是否安装依赖
            requirements_file: requirements 文件路径，默认为 "<worktree>/requirements.txt"

        Returns:
            bool: 是否成功创建
        """
        env_dir = worktree.env_dir

        # 创建虚拟环境
        if python_version:
            # 尝试使用指定版本的 python
            python_cmd = f"python{python_version}"
        else:
            python_cmd = "python3"

        cmd = [python_cmd, "-m", "venv", env_dir]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # 尝试使用 python
            cmd = ["python", "-m", "venv", env_dir]
            result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"创建虚拟环境失败：{result.stderr}")

        # 安装依赖
        if install_deps:
            if requirements_file is None:
                requirements_file = os.path.join(worktree.path, "requirements.txt")

            if os.path.exists(requirements_file):
                pip_path = os.path.join(env_dir, "bin", "pip")
                if not os.path.exists(pip_path):
                    pip_path = os.path.join(env_dir, "Scripts", "pip")  # Windows

                subprocess.run(
                    [pip_path, "install", "-r", requirements_file],
                    capture_output=True
                )

        return True

    def run_in_worktree(
        self,
        worktree: WorktreeInfo,
        command: List[str],
        use_venv: bool = True
    ) -> subprocess.CompletedProcess:
        """
        在 worktree 中运行命令

        Args:
            worktree: worktree 信息
            command: 命令和参数
            use_venv: 是否使用虚拟环境

        Returns:
            subprocess.CompletedProcess: 执行结果
        """
        env = os.environ.copy()

        if use_venv and worktree.is_venv_created:
            # 激活虚拟环境
            venv_bin = os.path.join(worktree.env_dir, "bin")
            if os.path.exists(venv_bin):
                env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"

        return subprocess.run(
            command,
            cwd=worktree.path,
            env=env,
            capture_output=True,
            text=True
        )

    def get_status(self) -> Dict[str, Any]:
        """
        获取所有 worktrees 的状态

        Returns:
            Dict: 状态信息
        """
        worktrees = self.list_worktrees()

        return {
            "repo_path": self.repo_path,
            "total_worktrees": len(worktrees),
            "worktrees": [wt.to_dict() for wt in worktrees]
        }

    def lock_worktree(self, name: str) -> bool:
        """
        锁定 worktree（防止被删除）

        Args:
            name: worktree 名称

        Returns:
            bool: 是否成功锁定
        """
        worktree_path = os.path.join(self.repo_path, ".worktrees", name)
        if not os.path.exists(worktree_path):
            worktree_path = name

        result = self._run_git(["worktree", "lock", worktree_path])
        return result.returncode == 0

    def unlock_worktree(self, name: str) -> bool:
        """
        解锁 worktree

        Args:
            name: worktree 名称

        Returns:
            bool: 是否成功解锁
        """
        worktree_path = os.path.join(self.repo_path, ".worktrees", name)
        if not os.path.exists(worktree_path):
            worktree_path = name

        result = self._run_git(["worktree", "unlock", worktree_path])
        return result.returncode == 0


# ==================== Global Instance ====================

_manager: Optional[GitWorktreeManager] = None


def get_worktree_manager(repo_path: Optional[str] = None) -> GitWorktreeManager:
    """获取 worktree 管理器（单例）"""
    global _manager
    if _manager is None or (repo_path and _manager.repo_path != repo_path):
        _manager = GitWorktreeManager(repo_path)
    return _manager


def reset_worktree_manager():
    """重置管理器（用于测试）"""
    global _manager
    _manager = None
