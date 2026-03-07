"""
Agent 核心 - Facade 模式

Agent 是可部署的实体，支持：
- 序列化/反序列化
- 持久化存储
- 独立运行

使用 Facade 模式组合以下模块：
- AgentCore: 核心执行逻辑
- AgentSerializer: 序列化逻辑
- AgentErrorEnhancer: 错误增强逻辑
- AgentCloner: 克隆逻辑
"""

import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from .tool import BaseTool, ToolResult, ToolRegistry
from .memory import Memory
from .llm import LLMInterface, OpenAILLM
from .agent_core import AgentCore
from .agent_serializer import AgentSerializer
from .agent_error_enhancer import AgentErrorEnhancer
from .agent_cloner import AgentCloner


@dataclass
class AgentInfo:
    """Agent 元信息"""
    name: str
    version: str
    description: str = ""
    created_at: str = ""
    tools: list = None
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class AgentConfig:
    """Agent 配置（用于序列化）"""
    name: str
    version: str
    description: str
    system_prompt: str
    tools: list  # 工具名称列表
    max_iterations: int
    created_at: str
    memory: list  # 对话历史


class Agent(AgentCore):
    """
    Agent Facade
    
    组合核心模块，提供统一的接口
    
    特性：
    - 可序列化为 JSON
    - 可持久化存储
    - 可独立运行
    - 支持克隆创建多个副本
    """
    
    def __init__(
        self,
        llm: LLMInterface,
        tools: Optional[list[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        name: str = "Agent",
        version: str = "1.0.0",
        description: str = "",
        max_iterations: int = None,
        created_at: Optional[str] = None,
        instance_id: Optional[str] = None
    ):
        # 初始化核心组件
        super().__init__(
            llm=llm,
            tool_registry=ToolRegistry(),
            system_prompt=system_prompt,
            name=name,
            version=version,
            description=description,
            max_iterations=max_iterations or 10,
            created_at=created_at,
            instance_id=instance_id
        )
        
        # 组合模块
        self._serializer = AgentSerializer()
        self._error_enhancer = AgentErrorEnhancer()
        
        # 注册工具
        self._tool_names: list[str] = []
        if tools:
            for tool in tools:
                self.tool_registry.register(tool)
                self._tool_names.append(tool.__class__.__name__)
    
    @property
    def info(self) -> AgentInfo:
        """获取 Agent 信息"""
        return AgentInfo(
            name=self.name,
            version=self.version,
            description=self.description,
            created_at=self.created_at,
            tools=self._tool_names
        )
    
    def __repr__(self) -> str:
        return f"<Agent {self.name} v{self.version}>"
    
    # ==================== 序列化（委托给 AgentSerializer）====================
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return self._serializer.to_dict(self)
    
    def to_json(self) -> str:
        """序列化为 JSON"""
        return self._serializer.to_json(self)
    
    def save(self, path: str):
        """保存到文件"""
        self._serializer.save(self, path)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], llm: Optional[LLMInterface] = None) -> "Agent":
        """从字典反序列化"""
        return AgentSerializer.from_dict(data, llm)
    
    @classmethod
    def load(cls, path: str, llm: Optional[LLMInterface] = None) -> "Agent":
        """从文件加载"""
        return AgentSerializer.load(path, llm)
    
    # ==================== 克隆（委托给 AgentCloner）====================
    
    def clone(self, new_instance_id: Optional[str] = None) -> "Agent":
        """克隆当前 agent，创建独立新实例"""
        return AgentCloner.clone(self, new_instance_id)
    
    # ==================== 运行（委托给 AgentCore，添加错误增强）====================
    
    def run(self, user_input: str, verbose: bool = True, debug: bool = False) -> str:
        """主循环（带智能错误恢复）"""
        # 委托给父类，传入 error_enhancer 实现智能错误恢复
        return super().run(
            user_input=user_input,
            verbose=verbose,
            debug=debug,
            error_enhancer=self._error_enhancer
        )
