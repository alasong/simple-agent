"""
Development Tools - 开发工具集

提供完整的软件开发支持：
1. Git Worktree 管理 - 多项目并行开发
2. 开发环境配置 - Python/Node.js 环境初始化
3. 开发流程自动化 - lint/test/build 一键运行
4. Agent 工具封装 - 供 Agent 调用的高级工具

使用示例:
```python
from core.dev import (
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
