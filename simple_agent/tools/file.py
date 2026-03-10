"""
文件操作工具

标签：file, io

安全特性：
- 路径验证：防止路径遍历攻击
- 限制在安全工作目录内
"""

import os
from simple_agent.core import tool, BaseTool, ToolResult


# 安全工作目录（默认为当前工作目录）
SAFE_WORKSPACE = os.path.abspath(os.environ.get('SAFE_WORKSPACE', '.'))


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
        # 路径验证（写操作必须在工作区内）
        is_valid, error_msg = validate_path(file_path, allow_read_outside=False)
        if not is_valid:
            return ToolResult(success=False, output="", error=error_msg)
        
        try:
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return ToolResult(success=True, output=f"成功写入文件：{file_path}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
