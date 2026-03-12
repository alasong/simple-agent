"""
文件操作工具

标签：file, io

沙箱路径支持：
- output:/ - 输出目录（最终产物）
- sandbox:/ - 沙箱环境（代码、配置）
- temp:/ - 临时文件
- cache:/ - 缓存文件
- logs:/ - 日志文件
- input:/ - 输入文件

安全特性：
- 路径验证：防止路径遍历攻击
- 强制输出到 output_dir 目录（如果指定）
- 限制在安全工作目录内
"""

import os
from simple_agent.core import tool, BaseTool, ToolResult
from simple_agent.core.execution_context import _execution_context


# 安全工作目录（默认为当前工作目录）
SAFE_WORKSPACE = os.path.abspath(os.environ.get('SAFE_WORKSPACE', '.'))


def set_output_dir(output_dir: str):
    """设置全局输出目录（所有写操作将优先使用此目录）"""
    _execution_context.output_dir = os.path.abspath(output_dir)


def get_output_dir() -> str:
    """获取全局输出目录"""
    return getattr(_execution_context, 'output_dir', None)


def set_sandbox_dir(sandbox_dir: str):
    """设置沙箱目录"""
    _execution_context.sandbox_dir = os.path.abspath(sandbox_dir)


def get_sandbox_dir() -> str:
    """获取沙箱目录"""
    return getattr(_execution_context, 'sandbox_dir', None)


def validate_path(file_path: str, allow_read_outside: bool = False) -> tuple:
    """
    验证文件路径是否在安全工作目录内

    Args:
        file_path: 文件路径
        allow_read_outside: 是否允许读取安全工作目录外的文件（只读操作）

    Returns:
        (是否有效，错误消息)
    """
    # 规范化路径
    abs_path = os.path.abspath(file_path)

    # 检查是否包含路径遍历模式
    if '..' in file_path:
        return False, "路径包含非法模式：..，不允许访问父目录"

    # 对于只读操作，如果明确允许，可以访问 workspace 外
    if allow_read_outside:
        # 但仍然禁止访问敏感目录
        sensitive_paths = ['/etc', '/usr', '/bin', '/sbin', '/proc', '/sys']
        for sensitive in sensitive_paths:
            if abs_path.startswith(sensitive):
                return False, f"禁止访问系统敏感目录：{sensitive}"
        return True, ""

    # 严格限制在安全工作目录内
    if not abs_path.startswith(SAFE_WORKSPACE):
        return False, f"文件路径必须在工作目录 {SAFE_WORKSPACE} 内"

    return True, ""


def _resolve_sandbox_path(file_path: str, output_dir: str) -> tuple:
    """
    解析沙箱路径（支持特殊前缀）

    支持的特殊前缀：
    - output:/ - 输出目录（最终产物）
    - sandbox:/ - 沙箱环境（代码、配置）
    - temp:/ - 临时文件
    - cache:/ - 缓存文件
    - logs:/ - 日志文件
    - input:/ - 输入文件

    Returns:
        (resolved_path, error_message)
    """
    # 检查沙箱目录
    sandbox_dir = get_sandbox_dir()
    if sandbox_dir:
        prefix_map = {
            "output:/": os.path.join(sandbox_dir, "output"),
            "sandbox:/": os.path.join(sandbox_dir, "sandbox"),
            "temp:/": os.path.join(sandbox_dir, "process", "temp"),
            "cache:/": os.path.join(sandbox_dir, "process", "cache"),
            "logs:/": os.path.join(sandbox_dir, "process", "logs"),
            "input:/": os.path.join(sandbox_dir, "input"),
        }

        for prefix, target_dir in prefix_map.items():
            if file_path.startswith(prefix):
                rel_path = file_path[len(prefix):]
                # 防止路径遍历
                if '..' in rel_path:
                    return None, f"禁止路径遍历: {file_path}"
                resolved = os.path.join(target_dir, rel_path)
                return os.path.abspath(resolved), None

    # 默认输出到 output_dir 或当前目录
    if output_dir:
        filename = os.path.basename(file_path)
        dir_part = os.path.dirname(file_path)
        if dir_part and dir_part != '.':
            safe_dir = os.path.join(output_dir, dir_part)
            os.makedirs(safe_dir, exist_ok=True)
            return os.path.abspath(os.path.join(safe_dir, filename)), None
        else:
            return os.path.abspath(os.path.join(output_dir, filename)), None

    return os.path.abspath(file_path), None


@tool(tags=["file", "io"], description="读取文件内容")
class ReadFileTool(BaseTool):
    """读文件工具"""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "读取指定路径的文件内容"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要读取的文件路径"
                }
            },
            "required": ["file_path"]
        }

    def execute(self, file_path: str) -> ToolResult:
        # 路径验证
        is_valid, error_msg = validate_path(file_path, allow_read_outside=True)
        if not is_valid:
            return ToolResult(success=False, output="", error=error_msg)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return ToolResult(success=True, output=content)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


@tool(tags=["file", "io"], description="写入文件内容")
class WriteFileTool(BaseTool):
    """写文件工具"""

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "将内容写入指定路径的文件"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要写入的文件路径"
                },
                "content": {
                    "type": "string",
                    "description": "要写入的内容"
                }
            },
            "required": ["file_path", "content"]
        }

    def execute(self, file_path: str, content: str) -> ToolResult:
        """
        写入文件（支持沙箱路径）

        Args:
            file_path: 文件路径（可以使用特殊前缀：output:/, sandbox:/, temp:/, cache:/, logs:/, input:/）
            content: 要写入的内容
        """
        # 获取 output_dir（如果 Agent.run 传入了 output_dir）
        output_dir = get_output_dir()
        sandbox_dir = get_sandbox_dir()

        # 如果指定了沙箱目录，使用沙箱路径解析
        if sandbox_dir:
            resolved_path, error = _resolve_sandbox_path(file_path, output_dir)
            if error:
                return ToolResult(success=False, output="", error=error)
            file_path = resolved_path
        elif output_dir:
            # 旧模式：强制将文件写入 output_dir
            filename = os.path.basename(file_path)
            dir_part = os.path.dirname(file_path)
            if dir_part and dir_part != '.':
                # 将子目录添加到 output_dir 下
                safe_dir = os.path.join(output_dir, dir_part)
                os.makedirs(safe_dir, exist_ok=True)
                file_path = os.path.join(safe_dir, filename)
            else:
                file_path = os.path.join(output_dir, filename)
        else:
            # 没有 output_dir，使用原始路径（但需要验证）
            file_path = os.path.abspath(file_path)

        # 限制写入路径必须在 SAFE_WORKSPACE 内（最终写入位置）
        abs_path = os.path.abspath(file_path)
        if not abs_path.startswith(SAFE_WORKSPACE):
            return ToolResult(
                success=False,
                output="",
                error=f"文件路径必须在工作目录 {SAFE_WORKSPACE} 内，收到：{abs_path}"
            )

        try:
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return ToolResult(success=True, output=f"成功写入文件：{file_path}")
        except TypeError as e:
            # 参数类型错误
            return ToolResult(success=False, output="", error=f"文件写入参数类型错误: {e}")
        except Exception as e:
            # 其他异常不中断整个任务
            return ToolResult(success=False, output="", error=f"写入文件失败: {type(e).__name__}: {e}")


# ==================== 注册工具到资源仓库 ====================

from simple_agent.core.resource import repo

repo.register_tool(
    WriteFileTool,
    tags=["file", "io", "write"],
    description="写入文件到指定路径"
)
repo.register_tool(
    ReadFileTool,
    tags=["file", "io", "read"],
    description="读取指定路径的文件内容"
)
