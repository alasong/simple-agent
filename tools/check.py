"""
检查工具

标签: check, review, code
"""

import os
import re
from core import tool, BaseTool, ToolResult


@tool(tags=["check", "review"], description="检查文件是否存在")
class CheckFileExistsTool(BaseTool):
    """检查文件是否存在"""
    
    @property
    def name(self) -> str:
        return "check_file_exists"
    
    @property
    def description(self) -> str:
        return "检查指定路径的文件是否存在"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要检查的文件路径"
                }
            },
            "required": ["file_path"]
        }
    
    def execute(self, file_path: str) -> ToolResult:
        exists = os.path.exists(file_path)
        if exists:
            size = os.path.getsize(file_path)
            return ToolResult(success=True, output=f"文件存在: {file_path} (大小: {size} 字节)")
        else:
            return ToolResult(success=False, output=f"文件不存在: {file_path}")


@tool(tags=["check", "review", "code"], description="检查文件内容")
class CheckContentTool(BaseTool):
    """检查文件内容是否包含特定文本"""
    
    @property
    def name(self) -> str:
        return "check_content"
    
    @property
    def description(self) -> str:
        return "检查文件内容是否包含指定文本或匹配正则表达式"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要检查的文件路径"
                },
                "pattern": {
                    "type": "string",
                    "description": "要匹配的文本或正则表达式"
                },
                "is_regex": {
                    "type": "boolean",
                    "description": "是否使用正则表达式匹配"
                }
            },
            "required": ["file_path", "pattern"]
        }
    
    def execute(self, file_path: str, pattern: str, is_regex: bool = False) -> ToolResult:
        if not os.path.exists(file_path):
            return ToolResult(success=False, output=f"文件不存在: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if is_regex:
                matches = re.findall(pattern, content)
                return ToolResult(
                    success=len(matches) > 0,
                    output=f"找到 {len(matches)} 个匹配" if matches else "未找到匹配"
                )
            else:
                count = content.count(pattern)
                return ToolResult(
                    success=count > 0,
                    output=f"找到 {count} 处匹配: '{pattern}'" if count else f"未找到: '{pattern}'"
                )
        except Exception as e:
            return ToolResult(success=False, output=f"读取文件失败: {str(e)}")


@tool(tags=["check", "review", "code"], description="检查Python语法")
class CheckPythonSyntaxTool(BaseTool):
    """检查 Python 语法"""
    
    @property
    def name(self) -> str:
        return "check_python_syntax"
    
    @property
    def description(self) -> str:
        return "检查 Python 文件的语法是否正确"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要检查的 Python 文件路径"
                }
            },
            "required": ["file_path"]
        }
    
    def execute(self, file_path: str) -> ToolResult:
        if not os.path.exists(file_path):
            return ToolResult(success=False, output=f"文件不存在: {file_path}")
        
        if not file_path.endswith('.py'):
            return ToolResult(success=False, output=f"不是 Python 文件: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            compile(code, file_path, 'exec')
            return ToolResult(success=True, output=f"Python 语法正确: {file_path}")
        except SyntaxError as e:
            return ToolResult(success=False, output=f"语法错误 (行 {e.lineno}): {e.msg}")
        except Exception as e:
            return ToolResult(success=False, output=f"检查失败: {str(e)}")
