"""
Development Tools - 开发工具集

提供完整的软件开发支持：
1. Git Worktree 管理 - 多项目并行开发
2. 开发环境配置 - Python/Node.js 环境初始化
3. 开发流程自动化 - lint/test/build 一键运行
4. Agent 工具封装 - 供 Agent 调用的高级工具

使用示例:
```python
from simple_agent.core.dev import (
    GitWorktreeTool,
    DevEnvironmentTool,
    DevWorkflowTool,
    CodeReviewTool
)

# Git Worktree 管理
wt = GitWorktreeTool(repo_path="/path/to/repo")
wt.create("feature-login", setup_env=True)

# 环境配置
env = DevEnvironmentTool(project_path="/path/to/project")
env.init_python("my_project")

# 开发流程
workflow = DevWorkflowTool("/path/to/project")
workflow.full_workflow()  # lint -> test -> build
```
"""

from .git_worktree import (
    GitWorktreeManager,
    WorktreeInfo,
    get_worktree_manager,
    reset_worktree_manager
)

from .environment_setup import (
    DevEnvironmentSetup,
    ProjectInitializer,
    EnvironmentInfo,
    SetupResult,
    LanguageType,
    get_environment_setup,
    get_project_initializer
)

from .workflow import (
    DevWorkflowRunner,
    WorkflowResult,
    CheckResult,
    CheckStatus,
    get_workflow_runner
)

from .tools import (
    GitWorktreeTool,
    DevEnvironmentTool,
    DevWorkflowTool,
    CodeReviewTool
)

# 注册开发工具到资源仓库（供 Agent 使用）
try:
    from simple_agent.core.resource import repo

    # 注册 GitWorktreeTool
    repo.register_tool(GitWorktreeTool, tags=["dev", "git"], description="Git Worktree 管理")

    # 注册 DevEnvironmentTool
    repo.register_tool(DevEnvironmentTool, tags=["dev", "environment"], description="开发环境配置")

    # 注册 DevWorkflowTool
    repo.register_tool(DevWorkflowTool, tags=["dev", "workflow"], description="开发流程自动化")

    # 注册 CodeReviewTool
    repo.register_tool(CodeReviewTool, tags=["dev", "review"], description="代码审查")

except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"注册开发工具失败：{e}")

__all__ = [
    # Git Worktree
    "GitWorktreeManager",
    "WorktreeInfo",
    "get_worktree_manager",
    "reset_worktree_manager",

    # Environment Setup
    "DevEnvironmentSetup",
    "ProjectInitializer",
    "EnvironmentInfo",
    "SetupResult",
    "LanguageType",
    "get_environment_setup",
    "get_project_initializer",

    # Workflow
    "DevWorkflowRunner",
    "WorkflowResult",
    "CheckResult",
    "CheckStatus",
    "get_workflow_runner",

    # Agent Tools
    "GitWorktreeTool",
    "DevEnvironmentTool",
    "DevWorkflowTool",
    "CodeReviewTool",
]
