"""
工具系统核心
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: str
    error: Optional[str] = None


class BaseTool(ABC):
    """工具抽象基类 - 所有工具必须继承此类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> dict:
        """JSON Schema 格式的参数定义"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """执行工具 - 所有工具实现必须包含异常处理"""
        pass

    def _validate_arguments(self, kwargs: dict) -> tuple[bool, Optional[str]]:
        """
        验证工具参数（可被子类重写）

        Returns:
            (是否通过, 错误消息)
        """
        if not isinstance(kwargs, dict):
            return False, "参数必须是字典类型"
        return True, None
    
    def to_openai_tool(self) -> dict:
        """转换为 OpenAI tool 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """注册工具"""
        # 兼容不具有 name 属性的工具
        if hasattr(tool, 'name'):
            self._tools[tool.name] = tool
        else:
            # 使用类名作为工具名
            tool_name = tool.__class__.__name__
            self._tools[tool_name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)

    def get_all_tools(self) -> list[BaseTool]:
        """获取所有工具"""
        return list(self._tools.values())

    def get_openai_tools(self) -> list[dict]:
        """获取 OpenAI 格式的工具列表"""
        result = []
        for tool in self._tools.values():
            try:
                # 如果工具有 to_openai_tool 方法，直接调用
                if hasattr(tool, 'to_openai_tool') and callable(tool.to_openai_tool):
                    result.append(tool.to_openai_tool())
                # 否则尝试手动构建
                elif hasattr(tool, 'name') and hasattr(tool, 'description'):
                    result.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": getattr(tool, 'parameters', {"type": "object", "properties": {}})
                        }
                    })
                # 完全没有必要属性的工具，跳过
            except Exception:
                # 跳过无法转换为 OpenAI 格式的工具
                pass
        return result
