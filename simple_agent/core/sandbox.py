"""
沙箱管理器 - 为每个任务提供隔离的执行环境

设计目标：
- 每个任务在一个独立的沙箱目录中执行
- 清晰的目录结构：input/, process/, output/, sandbox/
- 任务清单管理：manifest.json 记录元数据
- 易于清理：临时文件、缓存可单独清理
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ToolCallRecord:
    """工具调用记录"""
    tool: str
    command: str
    duration_ms: int
    success: bool
    output_preview: str = ""


@dataclass
class Manifest:
    """任务清单"""
    task_id: str
    user_input: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "pending"
    input_files: List[str] = field(default_factory=list)
    output_files: List[str] = field(default_factory=list)
    process_files: List[str] = field(default_factory=list)
    tool_calls: List[ToolCallRecord] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    def save(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


class Sandbox:
    """任务沙箱"""

    def __init__(self, base_dir: str, task_id: str):
        self.base_dir = Path(base_dir).resolve()
        self.task_id = task_id
        self.root = self.base_dir / task_id

        # 创建目录结构
        self.input_dir = self.root / "input"
        self.process_dir = self.root / "process"
        self.temp_dir = self.process_dir / "temp"
        self.cache_dir = self.process_dir / "cache"
        self.logs_dir = self.process_dir / "logs"
        self.output_dir = self.root / "output"
        self.sandbox_dir = self.root / "sandbox"

        # 初始化目录
        self._init_dirs()

        # 初始化清单（使用当前时间）
        self.manifest = Manifest(
            task_id=task_id,
            user_input="",
            created_at=datetime.now().isoformat()
        )

    def _init_dirs(self):
        """初始化目录结构"""
        for dir_path in [
            self.input_dir, self.temp_dir, self.cache_dir,
            self.logs_dir, self.output_dir, self.sandbox_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def set_input(self, content: str, filename: str = "input.txt"):
        """设置输入文件"""
        filepath = self.input_dir / filename
        filepath.write_text(content, encoding='utf-8')
        rel_path = str(filepath.relative_to(self.root))
        if rel_path not in self.manifest.input_files:
            self.manifest.input_files.append(rel_path)

    def save_output(self, content: str, filename: str, is_final: bool = True):
        """保存输出文件

        Args:
            content: 文件内容
            filename: 文件名
            is_final: 是否为最终输出
                - True: 保存到 output/ 目录（保留）
                - False: 保存到 temp/ 目录（临时/中间产物）
        """
        if is_final:
            filepath = self.output_dir / filename
        else:
            filepath = self.temp_dir / filename

        filepath.write_text(content, encoding='utf-8')

        rel_path = str(filepath.relative_to(self.root))
        if is_final:
            if rel_path not in self.manifest.output_files:
                self.manifest.output_files.append(rel_path)
        else:
            if rel_path not in self.manifest.process_files:
                self.manifest.process_files.append(rel_path)

    def save_tool_call(self, record: ToolCallRecord):
        """记录工具调用"""
        self.manifest.tool_calls.append(record)

    def save_logs(self, logs: str, filename: str = "execution.log"):
        """保存执行日志"""
        filepath = self.logs_dir / filename
        filepath.write_text(logs, encoding='utf-8')
        rel_path = str(filepath.relative_to(self.root))
        if rel_path not in self.manifest.process_files:
            self.manifest.process_files.append(rel_path)

    def cleanup_temp(self):
        """清理临时文件"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir(exist_ok=True)

    def cleanup_cache(self):
        """清理缓存"""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)

    def cleanup_logs(self):
        """清理日志"""
        if self.logs_dir.exists():
            shutil.rmtree(self.logs_dir)
            self.logs_dir.mkdir(exist_ok=True)

    def cleanup_all(self):
        """清理沙箱（保留输出和 sandbox）"""
        self.cleanup_temp()
        self.cleanup_cache()
        self.cleanup_logs()

    def cleanup_all_including_output(self):
        """彻底清理沙箱（包括 output 和 sandbox）"""
        if self.root.exists():
            shutil.rmtree(self.root)
            self.root.mkdir(parents=True, exist_ok=True)
            self._init_dirs()

    def get_file(self, path: str) -> Optional[str]:
        """获取文件内容（按优先级搜索）

        搜索顺序：output -> sandbox -> input -> temp
        """
        search_paths = [
            self.output_dir / path,
            self.sandbox_dir / path,
            self.input_dir / path,
            self.temp_dir / path,
        ]

        for sp in search_paths:
            if sp.exists():
                return sp.read_text(encoding='utf-8')
        return None

    def list_files(self, recursive: bool = True) -> Dict[str, List[str]]:
        """列出所有文件

        Returns:
            {
                "input": ["input.txt"],
                "output": ["code.py", "report.md"],
                "sandbox": ["config.json"],
                "temp": ["temp.txt"],
                "cache": ["data.cache"],
                "logs": ["execution.log"],
            }
        """
        result = {
            "input": [],
            "output": [],
            "sandbox": [],
            "temp": [],
            "cache": [],
            "logs": [],
        }

        for folder, name in [
            (self.input_dir, "input"),
            (self.output_dir, "output"),
            (self.sandbox_dir, "sandbox"),
            (self.temp_dir, "temp"),
            (self.cache_dir, "cache"),
            (self.logs_dir, "logs"),
        ]:
            if folder.exists():
                if recursive:
                    result[name] = [
                        str(p.relative_to(self.root))
                        for p in folder.rglob('*')
                        if p.is_file()
                    ]
                else:
                    result[name] = [
                        str(p.name)
                        for p in folder.iterdir()
                        if p.is_file()
                    ]

        return result

    def get_file_size(self, path: str) -> int:
        """获取文件大小"""
        filepath = self.root / path
        if filepath.exists():
            return filepath.stat().st_size
        return 0

    def get_total_size(self) -> int:
        """获取沙箱总大小（字节）"""
        total = 0
        for p in self.root.rglob('*'):
            if p.is_file():
                total += p.stat().st_size
        return total


class SandboxManager:
    """沙箱管理器 - 统一管理所有沙箱"""

    def __init__(self, base_dir: str = "./output"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._sandboxes: Dict[str, Sandbox] = {}

    def create_sandbox(self, task_id: str) -> Sandbox:
        """创建新的沙箱

        Args:
            task_id: 任务唯一标识

        Returns:
            新创建的 Sandbox 实例
        """
        sandbox = Sandbox(str(self.base_dir), task_id)
        self._sandboxes[task_id] = sandbox
        return sandbox

    def get_sandbox(self, task_id: str) -> Optional[Sandbox]:
        """获取沙箱

        Args:
            task_id: 任务 ID

        Returns:
            Sandbox 实例，不存在则返回 None
        """
        return self._sandboxes.get(task_id)

    def cleanup_sandbox(self, task_id: str, clear_output: bool = False):
        """清理沙箱

        Args:
            task_id: 任务 ID
            clear_output: 是否清除 output 目录
                - False: 只清理 temp/cache/logs
                - True: 完全删除沙箱目录
        """
        sandbox = self._sandboxes.get(task_id)
        if sandbox:
            if clear_output:
                shutil.rmtree(sandbox.root)
            else:
                sandbox.cleanup_all()
            self._sandboxes.pop(task_id, None)

    def cleanup_old_sandboxes(self, days: int = 7):
        """清理旧沙箱

        Args:
            days: 保留天数，超过此时间的沙箱将被清理
        """
        import time
        now = time.time()
        cutoff = now - days * 86400  # 7天

        for sandbox_dir in self.base_dir.iterdir():
            if sandbox_dir.is_dir():
                # 检查 manifest 的时间
                manifest_path = sandbox_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        manifest = json.loads(manifest_path.read_text())
                        created = datetime.fromisoformat(manifest.get("created_at", ""))
                        if created.timestamp() < cutoff:
                            shutil.rmtree(sandbox_dir)
                            self._sandboxes.pop(sandbox_dir.name, None)
                    except Exception:
                        # 解析失败，使用文件修改时间
                        try:
                            mtime = sandbox_dir.stat().st_mtime
                            if mtime < cutoff:
                                shutil.rmtree(sandbox_dir)
                                self._sandboxes.pop(sandbox_dir.name, None)
                        except Exception:
                            pass
                else:
                    # 没有 manifest，直接清理
                    shutil.rmtree(sandbox_dir)
                    self._sandboxes.pop(sandbox_dir.name, None)

    def list_sandboxes(self) -> List[Dict]:
        """列出所有沙箱

        Returns:
            [
                {
                    "task_id": "task_123",
                    "manifest": {...},
                    "size": 1024,
                },
                ...
            ]
        """
        result = []
        for sandbox_dir in sorted(self.base_dir.iterdir(), key=lambda x: x.name, reverse=True):
            if sandbox_dir.is_dir():
                manifest_path = sandbox_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        manifest = json.loads(manifest_path.read_text())
                        result.append({
                            "task_id": sandbox_dir.name,
                            "manifest": manifest,
                            "size": self._get_dir_size(sandbox_dir),
                        })
                    except Exception:
                        pass
                else:
                    # 没有 manifest，直接添加目录信息
                    result.append({
                        "task_id": sandbox_dir.name,
                        "manifest": None,
                        "size": self._get_dir_size(sandbox_dir),
                    })

        # 按创建时间排序
        result.sort(key=lambda x: x.get("manifest", {}).get("created_at", "") if x.get("manifest") else x["task_id"], reverse=True)
        return result

    def _get_dir_size(self, path: Path) -> int:
        """获取目录大小（字节）"""
        total = 0
        for p in path.rglob('*'):
            if p.is_file():
                total += p.stat().st_size
        return total


# 全局沙箱管理器实例
sandbox_manager = SandboxManager()


# ==================== 路径解析工具 ====================

def parse_sandbox_path(file_path: str, sandbox: Sandbox) -> tuple:
    """解析沙箱路径

    支持的特殊前缀：
    - output:/ - 输出目录（最终产物）
    - sandbox:/ - 沙箱环境（代码、配置）
    - temp:/ - 临时文件
    - cache:/ - 缓存文件
    - logs:/ - 日志文件
    - input:/ - 输入文件

    Args:
        file_path: 文件路径，可以包含特殊前缀
        sandbox: Sandbox 实例

    Returns:
        (target_dir, relative_path, error)
        - target_dir: 目标目录 Path 对象
        - relative_path: 相对路径
        - error: 错误消息， None 表示成功
    """
    # 检查特殊前缀
    prefix_to_dir = {
        "output:/": ("output", sandbox.output_dir),
        "sandbox:/": ("sandbox", sandbox.sandbox_dir),
        "temp:/": ("temp", sandbox.temp_dir),
        "cache:/": ("cache", sandbox.cache_dir),
        "logs:/": ("logs", sandbox.logs_dir),
        "input:/": ("input", sandbox.input_dir),
    }

    for prefix, (target_name, target_dir) in prefix_to_dir.items():
        if file_path.startswith(prefix):
            rel_path = file_path[len(prefix):]
            # 防止路径遍历
            if '..' in rel_path:
                return None, None, f"禁止路径遍历: {file_path}"
            return target_dir, rel_path, None

    # 默认输出到 output/
    target_dir = sandbox.output_dir
    rel_path = file_path

    # 防止路径遍历
    if '..' in rel_path:
        return None, None, f"禁止路径遍历: {file_path}"

    return target_dir, rel_path, None


def get_sandbox_output_dir(sandbox: Sandbox) -> str:
    """获取沙箱的 output 目录路径"""
    return str(sandbox.output_dir)
