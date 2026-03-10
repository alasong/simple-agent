# 软件开发支持指南

## 概述

Simple Agent 提供完整的软件开发支持，包括：

- **Git Worktree 管理**: 多分支/多项目并行开发
- **开发环境配置**: Python/Node.js 环境自动初始化
- **开发流程自动化**: lint、test、build 一键运行
- **专业 Developer Agent**: 代码生成、重构、审查

## 快速开始

### 1. 创建新的开发任务

```bash
# 使用 CLI 创建软件开发任务
.venv/bin/python cli.py "为新功能创建开发环境"
```

### 2. 使用 Worktree 进行开发

```python
from core.dev import GitWorktreeTool

tool = GitWorktreeTool(repo_path="/path/to/repo")

# 创建新的功能分支
result = tool.create(
    name="feature-login",
    branch="feature/login",
    start_point="main",
    setup_env=True  # 自动创建独立虚拟环境
)

print(result)
# {
#     "success": True,
#     "message": "已创建 worktree: feature-login [环境已初始化]",
#     "worktree": {
#         "name": "feature-login",
#         "path": "/path/to/repo/.worktrees/feature-login",
#         "branch": "feature/login",
#         "env_ready": True
#     }
# }

# 列出所有 worktrees
worktrees = tool.list()

# 删除完成的 worktree
tool.remove("feature-login")
```

### 3. 初始化项目环境

```python
from core.dev import DevEnvironmentTool

# Python 项目
env_tool = DevEnvironmentTool(project_path="/path/to/project")

# 检测环境
info = env_tool.detect()
print(info)

# 初始化 Python 项目
result = env_tool.init_python(
    name="my_project",
    create_venv=True
)

# 初始化 Node.js 项目
result = env_tool.init_node(
    name="my-app",
    typescript=True
)
```

### 4. 运行开发流程

```python
from core.dev import DevWorkflowTool

workflow = DevWorkflowTool(project_path="/path/to/project")

# 运行代码检查
lint_result = workflow.lint()

# 运行测试
test_result = workflow.test(args=["-v", "--tb=short"])

# 运行构建
build_result = workflow.build()

# 运行完整流程
full_result = workflow.full_workflow()
```

---

## Git Worktree 管理

### 什么是 Worktree？

Git Worktree 允许你在同一仓库的多个分支上并行工作，每个 worktree 有自己独立的工作目录和 Git 状态。

### 使用场景

| 场景 | 说明 |
|------|------|
| 多特性开发 | 同时开发多个独立特性 |
| Bug 修复 | 在不中断当前开发的情况下修复紧急 bug |
| 代码审查 | 隔离审查代码，不影响主线开发 |
| 环境隔离 | 每个 worktree 有独立的虚拟环境和依赖 |

### API 参考

```python
from core.dev.git_worktree import GitWorktreeManager

manager = GitWorktreeManager(repo_path="/path/to/repo")

# 创建 worktree
worktree = manager.create_worktree(
    name="feature-xxx",      # worktree 名称（也是目录名）
    branch="feature/xxx",    # 分支名
    start_point="main",      # 起始点（可以是分支名或 commit hash）
    force=False              # 是否强制创建
)

# 列出所有 worktrees
worktrees = manager.list_worktrees()
for wt in worktrees:
    print(f"{wt.path} - {wt.branch} (locked: {wt.is_locked})")

# 获取单个 worktree 信息
wt = manager.get_worktree("feature-xxx")
print(wt.to_dict())

# 删除 worktree
manager.remove_worktree("feature-xxx", force=False)

# 锁定/解锁 worktree（防止误删除）
manager.lock_worktree("feature-xxx")
manager.unlock_worktree("feature-xxx")

# 在 worktree 中运行命令
result = manager.run_in_worktree(
    worktree=wt,
    command=["python", "-m", "pytest"],
    use_venv=True
)
```

### Worktree 目录结构

```
repo/
├── .git/                    # 主仓库
├── .worktrees/              # worktree 目录
│   ├── feature-login/       # worktree 1
│   │   ├── .git             # 链接到主仓库
│   │   ├── .venv/           # 独立虚拟环境
│   │   └── src/             # 源代码
│   └── feature-api/         # worktree 2
│       ├── .git
│       ├── .venv/
│       └── src/
└── main/                    # 主工作目录
```

---

## 开发环境配置

### Python 项目初始化

```python
from core.dev.environment_setup import ProjectInitializer

initializer = ProjectInitializer("/path/to/new/project")

created = initializer.init_python_project(
    name="my_package",
    create_venv=True,        # 创建虚拟环境
    create_structure=True,   # 创建目录结构
    has_tests=True,          # 创建 tests 目录
    has_docs=True            # 创建 docs 目录
)

print(created)
# {
#     "dirs": ["src", "tests", "docs", "examples"],
#     "files": [
#         "src/my_package/__init__.py",
#         "requirements.txt",
#         "pyproject.toml",
#         "README.md"
#     ]
# }
```

### Node.js 项目初始化

```python
initializer = ProjectInitializer("/path/to/new/project")

created = initializer.init_node_project(
    name="my-app",
    typescript=True,         # 使用 TypeScript
    install_deps=True,       # 安装依赖
    create_structure=True    # 创建目录结构
)

print(created)
# {
#     "dirs": ["src", "dist", "test", "src/types", "src/utils"],
#     "files": [
#         "package.json",
#         "tsconfig.json",
#         "src/index.ts"
#     ]
# }
```

### 环境检测

```python
from core.dev.environment_setup import DevEnvironmentSetup

setup = DevEnvironmentSetup("/path/to/project")

# 检测环境
info = setup.detect_environment()

print(f"语言类型：{info.language.value}")
print(f"Python 版本：{info.python_version}")
print(f"Node 版本：{info.node_version}")
print(f"虚拟环境：{info.venv_path}")
print(f"依赖已安装：{info.dependencies_installed}")
print(f"环境就绪：{info.is_ready}")
```

### 环境设置

```python
result = setup.setup(
    create_venv=True,
    install_deps=True,
    language="python",       # 或 "nodejs" 或 "mixed"
    python_version="3.12",   # 指定 Python 版本
    requirements_file="requirements.txt",
    node_install=True        # 运行 npm install
)

if result.success:
    print(f"环境设置完成：{result.message}")
else:
    print(f"环境设置失败：{result.errors}")

for warning in result.warnings:
    print(f"警告：{warning}")
```

### 在项目环境中运行命令

```python
# 自动使用虚拟环境
result = setup.run_command(["python", "--version"])
print(result.stdout)  # Python 3.12.0

# 运行测试
result = setup.run_command(["pytest", "-v"])

# 运行 npm 命令
result = setup.run_command(["npm", "test"])
```

---

## 开发流程自动化

### 运行单一流程

```python
from core.dev.workflow import DevWorkflowRunner

runner = DevWorkflowRunner(
    project_path="/path/to/project",
    venv_path="/path/to/project/.venv"
)

# 代码检查
lint_result = runner.run_lint(
    tool="flake8",    # 或 "pylint", "eslint", 自动检测
    path="src/",
    fix=False         # 是否自动修复
)

# 代码格式化
format_result = runner.run_format(
    tool="black",     # 或 "autopep8", "prettier"
    check_only=False  # 是否仅检查（不修改）
)

# 类型检查
typecheck_result = runner.run_typecheck(
    tool="mypy"       # 或 "pyright", "tsc"
)

# 运行测试
test_result = runner.run_test(
    tool="pytest",    # 或 "unittest", "jest"
    args=["-v", "--tb=short"]
)

# 构建项目
build_result = runner.run_build(
    tool="auto"       # 自动检测构建工具
)
```

### 运行完整流程

```python
# 运行完整开发流程：lint → format → typecheck → test → build
result = runner.run_full_workflow()

print(f"总耗时：{result.total_duration:.2f}秒")
print(f"总结：{result.summary}")

for step_result in result.results:
    print(f"\n{step_result.name}: {step_result.status.value}")
    print(f"  消息：{step_result.message}")
    if step_result.output:
        print(f"  输出：{step_result.output[:200]}...")
```

### 自定义工作流

```python
# 只运行 lint 和 test
result = runner.run_workflow(
    steps=["lint", "test"],
    stop_on_failure=False  # 失败时是否继续
)

# 发布前流程
result = runner.run_workflow(
    steps=["lint", "format", "typecheck", "test", "build"],
    stop_on_failure=True
)
```

### 检查结果状态

```python
from core.dev.workflow import CheckStatus

if result.results[0].status == CheckStatus.PASSED:
    print("✓ 通过")
elif result.results[0].status == CheckStatus.FAILED:
    print("✗ 失败")
    print(f"问题数：{result.results[0].issues_found}")
elif result.results[0].status == CheckStatus.WARNING:
    print("⚠ 警告")
elif result.results[0].status == CheckStatus.SKIPPED:
    print("⊘ 跳过")
```

---

## Developer Agent

### 内置 Software Developer Agent

```yaml
# builtin_agents/configs/software_developer.yaml
name: 软件开发专家
version: 2.0.0
description: 负责复杂软件开发任务，支持多项目并行开发
tools:
  - ReadFileTool
  - WriteFileTool
  - BashTool
  - GitWorktreeTool
  - DevEnvironmentTool
  - DevWorkflowTool
  - CodeReviewTool
```

### 使用示例

```bash
# 使用 Software Developer Agent
.venv/bin/python cli.py "帮我创建一个新用户认证模块，包括登录、注册、密码重置功能"
```

### Agent 开发流程

Software Developer Agent 遵循以下流程：

1. **需求分析**: 理解业务需求，确认技术细节
2. **方案设计**: 设计技术实现方案
3. **环境准备**: 创建 worktree，初始化环境
4. **测试先行**: 编写测试用例
5. **功能实现**: 编写实现代码
6. **质量检查**: 运行 lint、test、build
7. **文档说明**: 编写使用文档

---

## 工具参考

### GitWorktreeTool

```python
from core.dev.tools import GitWorktreeTool

tool = GitWorktreeTool(repo_path="/path/to/repo")

# 创建 worktree
tool.create(name="feature-xxx", branch="feature/xxx", setup_env=True)

# 列出 worktrees
tool.list()

# 获取 worktree 信息
tool.get("feature-xxx")

# 删除 worktree
tool.remove("feature-xxx")

# 切换 worktree
tool.switch("feature-xxx")
```

### DevEnvironmentTool

```python
from core.dev.tools import DevEnvironmentTool

tool = DevEnvironmentTool(project_path="/path/to/project")

# 检测环境
tool.detect()

# 初始化 Python 项目
tool.init_python(name="my_project")

# 初始化 Node.js 项目
tool.init_node(name="my-app")

# 设置环境
tool.setup_env()

# 运行命令
tool.run_command("python --version")
```

### DevWorkflowTool

```python
from core.dev.tools import DevWorkflowTool

tool = DevWorkflowTool(project_path="/path/to/project")

# 代码检查
tool.lint(fix=False)

# 代码格式化
tool.format(check_only=False)

# 类型检查
tool.typecheck()

# 运行测试
tool.test(args=["-v"])

# 构建
tool.build()

# 完整流程
tool.full_workflow()

# 自定义流程
tool.custom_workflow(["lint", "test"])
```

### CodeReviewTool

```python
from core.dev.tools import CodeReviewTool

tool = CodeReviewTool(project_path="/path/to/project")

# 审查文件
tool.review_file("src/module.py")

# 审查分支差异
tool.review_diff(base_branch="main", target_branch="feature/login")

# 运行代码检查
tool.run_linter()
```

---

## 最佳实践

### 1. Worktree 命名规范

```
feature/xxx      # 新功能
bugfix/xxx       # Bug 修复
hotfix/xxx       # 紧急修复
release/v1.0     # 发布分支
experiment/xxx   # 实验性开发
```

### 2. 环境隔离

每个 worktree 使用独立的虚拟环境，避免依赖冲突：

```bash
# worktree 1: feature-login
.venv/  # Django 4.x

# worktree 2: feature-api
.venv/  # FastAPI 0.100+
```

### 3. 开发前检查清单

- [ ] 已创建独立 worktree
- [ ] 虚拟环境已初始化
- [ ] 依赖已安装
- [ ] 测试用例已编写
- [ ] 代码已通过 lint

### 4. CI/CD 集成

在 CI/CD 中使用开发流程工具：

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run lint
        run: python -m core.dev.workflow lint
      - name: Run tests
        run: python -m core.dev.workflow test
      - name: Run build
        run: python -m core.dev.workflow build
```

---

## 故障排查

### Worktree 创建失败

```
错误：worktree 已存在
解决：使用 tool.remove() 删除已存在的 worktree，或使用 force=True
```

### 虚拟环境创建失败

```
错误：python3 命令未找到
解决：安装 Python 3.8+，或指定 python_version 参数
```

### 依赖安装失败

```
错误：requirements.txt 不存在
解决：检查 requirements_file 参数路径是否正确
```

### 工具未找到

```
错误：flake8/pylint 未安装
解决：在虚拟环境中安装：pip install flake8 pylint
```

---

## 示例项目

### Python 全栈项目开发

```python
from core.dev import GitWorktreeTool, DevEnvironmentTool, DevWorkflowTool

# 1. 创建 worktree
wt_tool = GitWorktreeTool(repo_path="/path/to/myproject")
result = wt_tool.create("feature-user-auth", setup_env=True)
worktree_path = result["worktree"]["path"]

# 2. 初始化环境
env_tool = DevEnvironmentTool(worktree_path)
env_tool.init_python("user_auth", create_venv=False)  # worktree 已创建

# 3. 运行开发流程
workflow = DevWorkflowTool(worktree_path)

# 编写代码后运行检查
lint_result = workflow.lint()
if lint_result["success"]:
    print("代码检查通过")

# 运行测试
test_result = workflow.test()
if test_result["success"]:
    print("所有测试通过")

# 构建发布
build_result = workflow.build()
```

---

## 相关文件

- `core/dev/git_worktree.py` - Git Worktree 管理器
- `core/dev/environment_setup.py` - 开发环境配置
- `core/dev/workflow.py` - 开发流程自动化
- `core/dev/tools.py` - Agent 工具封装
- `builtin_agents/configs/software_developer.yaml` - Software Developer Agent 配置
