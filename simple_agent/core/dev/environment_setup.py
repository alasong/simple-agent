"""
Development Environment Setup - 开发环境配置工具

支持：
1. Python 虚拟环境创建
2. Node.js 环境检测
3. 依赖安装
4. 环境检测
5. 项目初始化
"""

import os
import sys
import json
import subprocess
import shutil
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum


class LanguageType(Enum):
    """编程语言类型"""
    PYTHON = "python"
    NODEJS = "nodejs"
    MIXED = "mixed"


@dataclass
class EnvironmentInfo:
    """环境信息"""
    project_path: str
    language: LanguageType
    python_version: Optional[str] = None
    node_version: Optional[str] = None
    venv_path: Optional[str] = None
    node_modules_path: Optional[str] = None
    dependencies_installed: bool = False
    is_ready: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "language": self.language.value,
            "python_version": self.python_version,
            "node_version": self.node_version,
            "venv_path": self.venv_path,
            "node_modules_path": self.node_modules_path,
            "dependencies_installed": self.dependencies_installed,
            "is_ready": self.is_ready
        }


@dataclass
class SetupResult:
    """环境设置结果"""
    success: bool
    message: str
    env_info: Optional[EnvironmentInfo] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class DevEnvironmentSetup:
    """
    开发环境设置工具

    使用示例:
    ```python
    setup = DevEnvironmentSetup("/path/to/project")

    # 检测环境
    info = setup.detect_environment()

    # 创建环境
    result = setup.setup(
        create_venv=True,
        install_deps=True,
        language=LanguageType.PYTHON
    )

    # 运行命令
    setup.run_command(["python", "--version"])
    setup.run_command(["npm", "test"], use_node_venv=True)
    ```
    """

    def __init__(self, project_path: str):
        """
        初始化环境设置

        Args:
            project_path: 项目路径
        """
        self.project_path = os.path.abspath(project_path)

    def _run_command(
        self,
        cmd: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict] = None,
        capture: bool = True
    ) -> subprocess.CompletedProcess:
        """运行命令"""
        kwargs = {
            "cwd": cwd or self.project_path,
            "capture_output": capture,
            "text": True
        }
        if env:
            kwargs["env"] = env
        try:
            return subprocess.run(cmd, **kwargs)
        except FileNotFoundError as e:
            raise RuntimeError(f"命令未找到：{cmd[0]}") from e

    def detect_environment(self) -> EnvironmentInfo:
        """
        检测项目环境

        Returns:
            EnvironmentInfo: 环境信息
        """
        info = EnvironmentInfo(
            project_path=self.project_path,
            language=LanguageType.PYTHON
        )

        # 检测 Python
        python_version = self._detect_python()
        if python_version:
            info.python_version = python_version

        # 检测 Node.js
        node_version = self._detect_nodejs()
        if node_version:
            info.node_version = node_version

        # 判断项目类型
        has_python = os.path.exists(os.path.join(self.project_path, "requirements.txt")) or \
                     os.path.exists(os.path.join(self.project_path, "pyproject.toml")) or \
                     os.path.exists(os.path.join(self.project_path, "setup.py"))
        has_node = os.path.exists(os.path.join(self.project_path, "package.json"))

        if has_python and has_node:
            info.language = LanguageType.MIXED
        elif has_node:
            info.language = LanguageType.NODEJS
        else:
            info.language = LanguageType.PYTHON

        # 检测虚拟环境
        venv_paths = [".venv", "venv", "env", ".env"]
        for venv in venv_paths:
            path = os.path.join(self.project_path, venv)
            if os.path.exists(path):
                info.venv_path = path
                break

        # 检测 node_modules
        node_modules = os.path.join(self.project_path, "node_modules")
        if os.path.exists(node_modules):
            info.node_modules_path = node_modules

        # 检查依赖是否已安装
        if info.venv_path:
            info.dependencies_installed = self._check_python_deps(info.venv_path)
        if info.node_modules_path:
            info.dependencies_installed = info.dependencies_installed or True

        # 判断是否就绪
        info.is_ready = (
            (info.language == LanguageType.PYTHON and info.venv_path and info.dependencies_installed) or
            (info.language == LanguageType.NODEJS and info.node_modules_path) or
            (info.language == LanguageType.MIXED and info.venv_path and info.node_modules_path)
        )

        return info

    def _detect_python(self) -> Optional[str]:
        """检测 Python 版本"""
        for cmd in ["python3", "python"]:
            try:
                result = self._run_command([cmd, "--version"])
                if result.returncode == 0:
                    # 解析版本号
                    version = result.stderr.strip() or result.stdout.strip()
                    return version.replace("Python ", "")
            except Exception:
                continue
        return None

    def _detect_nodejs(self) -> Optional[str]:
        """检测 Node.js 版本"""
        try:
            result = self._run_command(["node", "--version"])
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _check_python_deps(self, venv_path: str) -> bool:
        """检查 Python 依赖是否已安装"""
        pip_path = os.path.join(venv_path, "bin", "pip")
        if not os.path.exists(pip_path):
            pip_path = os.path.join(venv_path, "Scripts", "pip")  # Windows

        if not os.path.exists(pip_path):
            return False

        # 检查是否有已安装的包
        result = self._run_command([pip_path, "list"])
        return result.returncode == 0 and len(result.stdout.strip()) > 0

    def setup(
        self,
        create_venv: bool = True,
        install_deps: bool = True,
        language: Optional[LanguageType] = None,
        python_version: Optional[str] = None,
        requirements_file: Optional[str] = None,
        node_install: bool = True
    ) -> SetupResult:
        """
        设置开发环境

        Args:
            create_venv: 是否创建虚拟环境
            install_deps: 是否安装依赖
            language: 语言类型，自动检测则为 None
            python_version: Python 版本
            requirements_file: requirements 文件路径
            node_install: 是否运行 npm install

        Returns:
            SetupResult: 设置结果
        """
        result = SetupResult(success=True, message="环境设置完成")

        # 检测当前环境
        env_info = self.detect_environment()
        if language is None:
            language = env_info.language

        warnings = []
        errors = []

        # 设置 Python 环境
        if language in [LanguageType.PYTHON, LanguageType.MIXED]:
            self._setup_python(
                result,
                create_venv=create_venv,
                install_deps=install_deps,
                python_version=python_version,
                requirements_file=requirements_file
            )

        # 设置 Node.js 环境
        if language in [LanguageType.NODEJS, LanguageType.MIXED]:
            self._setup_node(result, install=node_install)

        result.warnings = warnings
        result.errors = errors

        if errors:
            result.success = False
            result.message = "环境设置失败：" + "; ".join(errors)
        else:
            # 重新检测环境
            result.env_info = self.detect_environment()
            result.message = f"环境设置完成 - {result.env_info.language.value}"

        return result

    def _setup_python(
        self,
        result: SetupResult,
        create_venv: bool,
        install_deps: bool,
        python_version: Optional[str],
        requirements_file: Optional[str]
    ):
        """设置 Python 环境"""
        venv_path = os.path.join(self.project_path, ".venv")

        # 创建虚拟环境
        if create_venv and not os.path.exists(venv_path):
            try:
                if python_version:
                    python_cmd = f"python{python_version}"
                else:
                    python_cmd = "python3"

                # 检查 Python 是否可用
                check_result = self._run_command([python_cmd, "--version"])
                if check_result.returncode != 0:
                    python_cmd = "python"

                cmd = [python_cmd, "-m", "venv", venv_path]
                self._run_command(cmd)
                result.message += " [虚拟环境已创建]"
            except Exception as e:
                result.errors.append(f"创建虚拟环境失败：{e}")
                result.success = False
                return

        # 安装依赖
        if install_deps:
            pip_path = os.path.join(venv_path, "bin", "pip")
            if not os.path.exists(pip_path):
                pip_path = os.path.join(venv_path, "Scripts", "pip")

            if os.path.exists(pip_path):
                # 升级 pip
                self._run_command([pip_path, "install", "--upgrade", "pip"])

                # 安装 requirements
                req_file = requirements_file or os.path.join(self.project_path, "requirements.txt")
                if os.path.exists(req_file):
                    install_result = self._run_command([pip_path, "install", "-r", req_file])
                    if install_result.returncode != 0:
                        result.warnings.append(f"部分依赖安装失败：{install_result.stderr[:100]}")
                else:
                    result.warnings.append(f"未找到 requirements 文件：{req_file}")
            else:
                result.warnings.append("pip 未找到，跳过依赖安装")

    def _setup_node(self, result: SetupResult, install: bool = True):
        """设置 Node.js 环境"""
        # 检查 node 是否安装
        node_result = self._run_command(["node", "--version"])
        if node_result.returncode != 0:
            result.warnings.append("Node.js 未安装，跳过设置")
            return

        # 检查 npm
        npm_result = self._run_command(["npm", "--version"])
        if npm_result.returncode != 0:
            result.warnings.append("npm 未找到")
            return

        # 运行 npm install
        if install:
            package_json = os.path.join(self.project_path, "package.json")
            if os.path.exists(package_json):
                install_result = self._run_command(["npm", "install"])
                if install_result.returncode != 0:
                    result.warnings.append(f"npm install 失败：{install_result.stderr[:100]}")
            else:
                result.warnings.append("未找到 package.json")

    def run_command(
        self,
        command: List[str],
        use_venv: bool = True,
        use_node_venv: bool = True,
        cwd: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        """
        在 project 环境中运行命令

        Args:
            command: 命令和参数
            use_venv: 是否使用 Python 虚拟环境
            use_node_venv: 是否使用 node_modules/.bin
            cwd: 工作目录

        Returns:
            subprocess.CompletedProcess: 执行结果
        """
        env = os.environ.copy()
        paths = []

        # 添加虚拟环境 bin 目录
        if use_venv:
            venv_bin = os.path.join(self.project_path, ".venv", "bin")
            if os.path.exists(venv_bin):
                paths.append(venv_bin)
            else:
                venv_bin = os.path.join(self.project_path, ".venv", "Scripts")
                if os.path.exists(venv_bin):
                    paths.append(venv_bin)

        # 添加 node_modules/.bin
        if use_node_venv:
            node_bin = os.path.join(self.project_path, "node_modules", ".bin")
            if os.path.exists(node_bin):
                paths.append(node_bin)

        if paths:
            current_path = env.get("PATH", "")
            env["PATH"] = ":".join(paths) + ":" + current_path

        return self._run_command(command, cwd=cwd or self.project_path, env=env)

    def get_env_script(self) -> str:
        """
        获取环境激活脚本

        Returns:
            str: 激活脚本内容
        """
        env_info = self.detect_environment()
        lines = ["#!/bin/bash", "# Environment activation script", ""]

        if env_info.venv_path:
            activate_script = os.path.join(env_info.venv_path, "bin", "activate")
            if os.path.exists(activate_script):
                lines.append(f"# Activate Python virtual environment")
                lines.append(f"source {activate_script}")
                lines.append("")

        if env_info.node_modules_path:
            lines.append("# Add node_modules/.bin to PATH")
            lines.append(f"export PATH=\"$PWD/node_modules/.bin:$PATH\"")
            lines.append("")

        return "\n".join(lines)


# ==================== 项目初始化 ====================

class ProjectInitializer:
    """
    项目初始化工具

    使用示例:
    ```python
    initializer = ProjectInitializer("/path/to/new/project")

    # 初始化 Python 项目
    initializer.init_python_project(
        name="my_project",
        create_venv=True,
        create_structure=True
    )

    # 初始化 Node.js 项目
    initializer.init_node_project(
        name="my-app",
        typescript=True,
        install_deps=True
    )
    ```
    """

    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)

    def init_python_project(
        self,
        name: str,
        create_venv: bool = True,
        create_structure: bool = True,
        has_tests: bool = True,
        has_docs: bool = True
    ) -> Dict[str, Any]:
        """
        初始化 Python 项目

        Args:
            name: 项目名称
            create_venv: 是否创建虚拟环境
            create_structure: 是否创建目录结构
            has_tests: 是否创建测试目录
            has_docs: 是否创建文档目录

        Returns:
            Dict: 创建的文件和目录
        """
        os.makedirs(self.project_path, exist_ok=True)

        created = {"dirs": [], "files": []}

        # 创建目录结构
        if create_structure:
            dirs = ["src", "tests", "docs"]
            if has_tests:
                dirs.append("tests")
            if has_docs:
                dirs.extend(["docs", "examples"])

            for d in dirs:
                dir_path = os.path.join(self.project_path, d)
                os.makedirs(dir_path, exist_ok=True)
                created["dirs"].append(d)

            # 创建 __init__.py
            src_path = os.path.join(self.project_path, "src", name)
            os.makedirs(src_path, exist_ok=True)
            with open(os.path.join(src_path, "__init__.py"), "w") as f:
                f.write(f'"""{name} - Auto-generated project."""\n\n__version__ = "0.1.0"\n')
            created["files"].append(f"src/{name}/__init__.py")

        # 创建 requirements.txt
        req_file = os.path.join(self.project_path, "requirements.txt")
        with open(req_file, "w") as f:
            f.write("# Project dependencies\n")
            f.write("# Add your dependencies here\n")
        created["files"].append("requirements.txt")

        # 创建 pyproject.toml
        pyproject = os.path.join(self.project_path, "pyproject.toml")
        with open(pyproject, "w") as f:
            f.write(f"""[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "0.1.0"
description = "Auto-generated Python project"
requires-python = ">=3.8"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
""")
        created["files"].append("pyproject.toml")

        # 创建 README.md
        readme = os.path.join(self.project_path, "README.md")
        with open(readme, "w") as f:
            f.write(f"# {name}\n\n")
            f.write(f"## Setup\n\n")
            f.write("```bash\n")
            f.write("# Create virtual environment\n")
            f.write("python3 -m venv .venv\n")
            f.write("source .venv/bin/activate\n\n")
            f.write("# Install dependencies\n")
            f.write("pip install -r requirements.txt\n")
            f.write("```\n\n")
            f.write("## Usage\n\n")
            f.write("```python\n")
            f.write(f"from {name} import *\n")
            f.write("```\n")
        created["files"].append("README.md")

        # 创建虚拟环境
        if create_venv:
            setup = DevEnvironmentSetup(self.project_path)
            setup.setup(create_venv=True, install_deps=False)

        return created

    def init_node_project(
        self,
        name: str,
        typescript: bool = True,
        install_deps: bool = True,
        create_structure: bool = True
    ) -> Dict[str, Any]:
        """
        初始化 Node.js 项目

        Args:
            name: 项目名称
            typescript: 是否使用 TypeScript
            install_deps: 是否安装依赖
            create_structure: 是否创建目录结构

        Returns:
            Dict: 创建的文件和目录
        """
        os.makedirs(self.project_path, exist_ok=True)

        created = {"dirs": [], "files": []}

        # 运行 npm init
        result = subprocess.run(
            ["npm", "init", "-y"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            created["files"].append("package.json")

        # 创建目录结构
        if create_structure:
            dirs = ["src", "dist", "test"]
            if typescript:
                dirs.extend(["src/types", "src/utils"])

            for d in dirs:
                dir_path = os.path.join(self.project_path, d)
                os.makedirs(dir_path, exist_ok=True)
                created["dirs"].append(d)

        # 创建 tsconfig.json
        if typescript:
            tsconfig = os.path.join(self.project_path, "tsconfig.json")
            with open(tsconfig, "w") as f:
                f.write("""{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "declaration": true,
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": false,
    "inlineSourceMap": true,
    "inlineSources": true,
    "experimentalDecorators": true,
    "strictPropertyInitialization": false,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "test"]
}
""")
            created["files"].append("tsconfig.json")

        # 安装依赖
        if install_deps and typescript:
            subprocess.run(
                ["npm", "install", "--save-dev", "typescript", "@types/node"],
                cwd=self.project_path,
                capture_output=True
            )

        # 创建 src/index.ts
        if typescript:
            index_file = os.path.join(self.project_path, "src", "index.ts")
            with open(index_file, "w") as f:
                f.write(f'/**\n * {name}\n */\n\n')
                f.write('export function hello(): string {\n')
                f.write('  return "Hello, World!";\n')
                f.write('}\n')
            created["files"].append("src/index.ts")

        return created


# ==================== Factory Functions ====================

def get_environment_setup(project_path: str) -> DevEnvironmentSetup:
    """获取环境设置工具"""
    return DevEnvironmentSetup(project_path)


def get_project_initializer(project_path: str) -> ProjectInitializer:
    """获取项目初始化工具"""
    return ProjectInitializer(project_path)
