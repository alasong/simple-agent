"""
Agent Serializer - 序列化逻辑

负责 Agent 的序列化和反序列化
"""

import json
import os
from typing import Optional, Dict, Any
from datetime import datetime

from .agent_core import AgentCore
from .tool import ToolRegistry
from .llm import LLMInterface


class AgentSerializer:
    """
    Agent 序列化器
    
    职责:
    - 将 Agent 转换为字典/JSON
    - 从字典/JSON 重建 Agent
    - 从文件加载/保存 Agent
    """
    
    @staticmethod
    def to_dict(agent: AgentCore) -> Dict[str, Any]:
        """
        将 Agent 序列化为字典
        
        Args:
            agent: Agent 实例
        
        Returns:
            字典格式的 Agent 数据
        """
        # 获取工具名称列表
        tool_names = []
        for tool in agent.tool_registry.get_all_tools():
            tool_names.append(tool.__class__.__name__)
        
        return {
            "name": agent.name,
            "version": agent.version,
            "description": agent.description,
            "system_prompt": agent.system_prompt if hasattr(agent, 'system_prompt') else "",
            "tools": tool_names,
            "max_iterations": agent.max_iterations,
            "created_at": agent.created_at or datetime.now().isoformat(),
            "instance_id": agent.instance_id,
            "memory": agent.memory.get_messages()
        }
    
    @staticmethod
    def to_json(agent: AgentCore) -> str:
        """
        将 Agent 序列化为 JSON 字符串
        
        Args:
            agent: Agent 实例
        
        Returns:
            JSON 格式的 Agent 数据
        """
        return json.dumps(AgentSerializer.to_dict(agent), ensure_ascii=False, indent=2)
    
    @staticmethod
    def save(agent: AgentCore, path: str):
        """
        将 Agent 保存到文件
        
        Args:
            agent: Agent 实例
            path: 文件路径
        """
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(AgentSerializer.to_json(agent))
    
    @staticmethod
    def from_dict(
        data: Dict[str, Any], 
        llm: Optional[LLMInterface] = None,
        get_llm_func: Optional[callable] = None,
        get_tool_func: Optional[callable] = None
    ) -> AgentCore:
        """
        从字典反序列化 Agent
        
        Args:
            data: 字典格式的 Agent 数据
            llm: LLM 实例（可选）
            get_llm_func: 获取 LLM 的函数（可选）
            get_tool_func: 获取工具类的函数（可选）
        
        Returns:
            新的 Agent 实例
        """
        # 延迟导入避免循环依赖
        if get_llm_func is None:
            from .resource import repo
            get_llm_func = repo.extract_llm
        
        if get_tool_func is None:
            from .resource import repo
            get_tool_func = repo.get_tool
        
        # LLM
        if llm is None:
            llm = get_llm_func()
        
        # 工具
        from .tool import BaseTool
        tools = []
        for tool_name in data.get("tools", []):
            tool_class = get_tool_func(tool_name)
            if tool_class:
                tools.append(tool_class())
        
        # 创建 Agent
        agent = AgentCore(
            llm=llm,
            tool_registry=ToolRegistry(),
            system_prompt=data.get("system_prompt", ""),
            name=data.get("name", "Agent"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            max_iterations=data.get("max_iterations", 10),
            created_at=data.get("created_at"),
            instance_id=data.get("instance_id")
        )
        
        # 添加工具
        for tool in tools:
            agent.tool_registry.register(tool)
        
        # 恢复记忆
        for msg in data.get("memory", []):
            if msg.get("role") != "system":  # system 已在构造时添加
                agent.memory.messages.append(msg)
        
        return agent
    
    @staticmethod
    def load(
        path: str, 
        llm: Optional[LLMInterface] = None
    ) -> AgentCore:
        """
        从文件加载 Agent
        
        Args:
            path: 文件路径
            llm: LLM 实例（可选）
        
        Returns:
            新的 Agent 实例
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return AgentSerializer.from_dict(data, llm)
