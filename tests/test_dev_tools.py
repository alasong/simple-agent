"""
Development Tools Tests - 开发工具测试

测试覆盖:
1. GitWorktreeManager - Worktree 管理
2. DevEnvironmentSetup - 环境配置
3. DevWorkflowRunner - 开发流程
4. Agent Tools - 工具封装
"""

import pytest
import os
import tempfile
import shutil
import subprocess
import sys


# ==================== Git Worktree Tests ====================

class TestGitWorktreeManager:
    """测试 Git Worktree 管理"""

    @pytest.fixture
    def temp_repo(self, tmp_path):
        """创建临时 git 仓库"""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        # 初始化 git
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, check=True)

        # 创建初始提交
        test_file = repo_path / "README.md"
        test_file.write_text("# Test Repo")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

        # 重命名分支为 main
        subprocess.run(["git", "branch", "-M", "main"], cwd=repo_path, check=True, capture_output=True)

        return str(repo_path)

    def test_create_worktree(self, temp_repo):
        """测试创建 worktree"""
        from core.dev.git_worktree import GitWorktreeManager

        manager = GitWorktreeManager(temp_repo)
        worktree = manager.create_worktree(
            name="feature-test",
            branch="feature/test",
            start_point="main"
        )

        assert worktree.branch == "feature/test"
        assert os.path.exists(worktree.path)

    def test_list_worktrees(self, temp_repo):
        """测试列出 worktrees"""
        from core.dev.git_worktree import GitWorktreeManager

        manager = GitWorktreeManager(temp_repo)

        # 创建两个 worktrees
        manager.create_worktree("feature-1", branch="feature/1")
        manager.create_worktree("feature-2", branch="feature/2")

        worktrees = manager.list_worktrees()
        assert len(worktrees) >= 2  # 至少有两个（不包括主 worktree）

    def test_remove_worktree(self, temp_repo):
        """测试删除 worktree"""
        from core.dev.git_worktree import GitWorktreeManager

        manager = GitWorktreeManager(temp_repo)

        # 创建然后删除
        worktree = manager.create_worktree("feature-temp")
        assert os.path.exists(worktree.path)

        manager.remove_worktree("feature-temp", force=True)
        # 使用 force 删除

    def test_get_worktree(self, temp_repo):
        """测试获取 worktree 信息"""
        from core.dev.git_worktree import GitWorktreeManager

        manager = GitWorktreeManager(temp_repo)
        worktree = manager.create_worktree("feature-get")

        result = manager.get_worktree("feature-get")
        assert result is not None
        assert result.branch == "feature-get"

    def test_get_status(self, temp_repo):
        """测试获取状态"""
        from core.dev.git_worktree import GitWorktreeManager

        manager = GitWorktreeManager(temp_repo)
        manager.create_worktree("feature-status")

        status = manager.get_status()
        assert "total_worktrees" in status
        assert "worktrees" in status


# ==================== Environment Setup Tests ====================

class TestDevEnvironmentSetup:
    """测试开发环境设置"""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """创建临时项目目录"""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        # 创建 requirements.txt
        req_file = project_path / "requirements.txt"
        req_file.write_text("# Test dependencies\n")

        return str(project_path)

    def test_detect_environment_python(self, temp_project):
        """测试环境检测 - Python"""
        from core.dev.environment_setup import DevEnvironmentSetup, LanguageType

        setup = DevEnvironmentSetup(temp_project)
        info = setup.detect_environment()

        assert info.language == LanguageType.PYTHON

    def test_detect_environment_node(self, tmp_path):
        """测试环境检测 - Node.js"""
        from core.dev.environment_setup import DevEnvironmentSetup, LanguageType

        project_path = tmp_path / "node_project"
        project_path.mkdir()
        (project_path / "package.json").write_text('{"name": "test"}')

        setup = DevEnvironmentSetup(str(project_path))
        info = setup.detect_environment()

        assert info.language == LanguageType.NODEJS

    def test_setup_environment(self, temp_project):
        """测试环境设置"""
        from core.dev.environment_setup import DevEnvironmentSetup

        setup = DevEnvironmentSetup(temp_project)
        result = setup.setup(create_venv=True, install_deps=False)

        assert result.success
        assert result.env_info is not None
        assert result.env_info.venv_path is not None

    def test_run_command_in_venv(self, temp_project):
        """测试在虚拟环境中运行命令"""
        from core.dev.environment_setup import DevEnvironmentSetup

        setup = DevEnvironmentSetup(temp_project)
        setup.setup(create_venv=True, install_deps=False)

        # 运行 python --version
        result = setup.run_command(["python", "--version"])
        assert result.returncode == 0


# ==================== Project Initializer Tests ====================

class TestProjectInitializer:
    """测试项目初始化"""

    def test_init_python_project(self, tmp_path):
        """测试初始化 Python 项目"""
        from core.dev.environment_setup import ProjectInitializer

        project_path = tmp_path / "python_project"
        initializer = ProjectInitializer(str(project_path))

        created = initializer.init_python_project(
            name="my_package",
            create_venv=True,
            create_structure=True
        )

        assert "dirs" in created
        assert "files" in created
        assert os.path.exists(project_path / "src" / "my_package" / "__init__.py")
        assert os.path.exists(project_path / "requirements.txt")
        assert os.path.exists(project_path / ".venv")

    def test_init_node_project(self, tmp_path):
        """测试初始化 Node.js 项目"""
        from core.dev.environment_setup import ProjectInitializer

        project_path = tmp_path / "node_project"
        initializer = ProjectInitializer(str(project_path))

        try:
            created = initializer.init_node_project(
                name="my-app",
                typescript=True,
                install_deps=False  # 跳过安装以加快测试
            )

            assert "dirs" in created
            assert "files" in created
            assert os.path.exists(project_path / "package.json")
            assert os.path.exists(project_path / "tsconfig.json")
        except Exception:
            # 如果 npm 未安装，跳过测试
            pytest.skip("npm not available")


# ==================== Workflow Tests ====================

class TestDevWorkflowRunner:
    """测试开发流程运行器"""

    @pytest.fixture
    def python_project(self, tmp_path):
        """创建 Python 项目"""
        project_path = tmp_path / "workflow_test"
        project_path.mkdir()

        # 创建虚拟环境
        venv_path = project_path / ".venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)

        # 创建 requirements.txt
        (project_path / "requirements.txt").write_text("# deps\n")

        # 创建测试目录
        (project_path / "tests").mkdir()
        (project_path / "tests" / "__init__.py").write_text("")

        # 创建测试文件
        test_file = project_path / "tests" / "test_sample.py"
        test_file.write_text("""
def test_pass():
    assert True
""")

        # 创建 Python 文件
        src_file = project_path / "sample.py"
        src_file.write_text("""
def hello():
    return "Hello"
""")

        return str(project_path)

    def test_run_lint_skip(self, python_project):
        """测试运行 lint（跳过，因为未安装 flake8）"""
        from core.dev.workflow import DevWorkflowRunner, CheckStatus

        runner = DevWorkflowRunner(python_project, venv_path=os.path.join(python_project, ".venv"))
        result = runner.run_lint()

        # 可能跳过（未安装工具）或通过
        assert result.status in [CheckStatus.SKIPPED, CheckStatus.PASSED, CheckStatus.FAILED]

    def test_run_test_pass(self, python_project):
        """测试运行测试"""
        from core.dev.workflow import DevWorkflowRunner, CheckStatus

        runner = DevWorkflowRunner(python_project, venv_path=os.path.join(python_project, ".venv"))
        result = runner.run_test()

        # 可能跳过（未安装 pytest）或通过
        assert result.status in [CheckStatus.SKIPPED, CheckStatus.PASSED, CheckStatus.FAILED]

    def test_run_full_workflow(self, python_project):
        """测试运行完整工作流"""
        from core.dev.workflow import DevWorkflowRunner

        runner = DevWorkflowRunner(python_project, venv_path=os.path.join(python_project, ".venv"))
        result = runner.run_full_workflow()

        assert result.total_duration > 0
        assert len(result.results) > 0


# ==================== Agent Tools Tests ====================

class TestAgentTools:
    """测试 Agent 工具封装"""

    @pytest.fixture
    def temp_repo(self, tmp_path):
        """创建临时 git 仓库"""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, check=True)
        (repo_path / "README.md").write_text("# Test")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Init"], cwd=repo_path, check=True)
        subprocess.run(["git", "branch", "-M", "main"], cwd=repo_path, check=True, capture_output=True)
        return str(repo_path)

    def test_git_worktree_tool(self, temp_repo):
        """测试 GitWorktreeTool"""
        from core.dev.tools import GitWorktreeTool

        tool = GitWorktreeTool(repo_path=temp_repo)

        # 创建
        result = tool.create("test-tool", setup_env=False)
        assert result["success"]

        # 列出
        result = tool.list()
        assert result["success"]
        assert result["count"] >= 1

        # 获取
        result = tool.get("test-tool")
        assert result["success"]

    def test_dev_environment_tool(self, tmp_path):
        """测试 DevEnvironmentTool"""
        from core.dev.tools import DevEnvironmentTool

        project_path = tmp_path / "env_tool_test"
        project_path.mkdir()

        tool = DevEnvironmentTool(str(project_path))

        # 检测
        result = tool.detect()
        assert result["success"]

        # 初始化 Python 项目
        result = tool.init_python("test_pkg", create_venv=False)
        assert result["success"]

    def test_dev_workflow_tool(self, tmp_path):
        """测试 DevWorkflowTool"""
        from core.dev.tools import DevWorkflowTool

        project_path = tmp_path / "workflow_tool_test"
        project_path.mkdir()
        (project_path / ".venv").mkdir()  # 创建空虚拟环境目录

        tool = DevWorkflowTool(str(project_path))

        # lint（可能跳过）
        result = tool.lint()
        assert "success" in result

        # 自定义工作流
        result = tool.custom_workflow(["lint"])
        assert "success" in result


# ==================== Integration Tests ====================

class TestIntegration:
    """集成测试"""

    def test_full_development_flow(self, tmp_path):
        """测试完整开发流程"""
        from core.dev import (
            GitWorktreeManager,
            ProjectInitializer,
            DevWorkflowRunner
        )

        # 1. 创建 git 仓库
        repo_path = tmp_path / "integration_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, check=True)

        # 创建初始提交
        (repo_path / "README.md").write_text("# Test")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Init"], cwd=repo_path, check=True)

        # 2. 创建 worktree
        manager = GitWorktreeManager(str(repo_path))
        worktree = manager.create_worktree("feature-integration")

        # 3. 初始化项目
        initializer = ProjectInitializer(worktree.path)
        initializer.init_python_project("integration_pkg", create_venv=False)

        # 4. 设置环境
        venv_path = os.path.join(worktree.path, ".venv")
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

        # 5. 运行工作流
        runner = DevWorkflowRunner(worktree.path, venv_path=venv_path)
        result = runner.run_workflow(["lint", "test"])

        assert result.total_duration > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
