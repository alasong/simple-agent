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
        """执行工具"""
        pass
    
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
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)
    
    def get_all_tools(self) -> list[BaseTool]:
        """获取所有工具"""
        return list(self._tools.values())
    
    def get_openai_tools(self) -> list[dict]:
        """获取 OpenAI 格式的工具列表"""
        return [tool.to_openai_tool() for tool in self._tools.values()]
