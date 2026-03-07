"""
Agent Cloner - Agent 克隆逻辑

负责创建 Agent 的独立副本
"""

from typing import Optional
from .agent_core import AgentCore
from .tool import ToolRegistry


class AgentCloner:
    """
    Agent 克隆器
    
    职责:
    - 创建 Agent 的独立副本
    - 确保新实例与原始实例配置相同但状态独立
    """
    
    @staticmethod
    def clone(agent: AgentCore, new_instance_id: Optional[str] = None) -> AgentCore:
        """
        克隆 Agent，创建一个配置相同但独立的新实例
        
        Args:
            agent: 原始 Agent 实例
            new_instance_id: 新实例的 ID，用于标识
        
        Returns:
            新的 Agent 实例，具有：
            - 相同的配置（name, tools, system_prompt 等）
            - 独立的内存（Memory）
            - 独立的工具注册表
        """
        # 获取原始 agent 的工具列表
        tools = list(agent.tool_registry.get_all_tools())
        
        # 获取 system prompt
        system_prompt = ""
        for msg in agent.memory.get_messages():
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
                break
        
        # 创建新 agent
        new_agent = AgentCore(
            llm=agent.llm,
            tool_registry=ToolRegistry(),
            system_prompt=system_prompt,
            name=agent.name,
            version=agent.version,
            description=agent.description,
            max_iterations=agent.max_iterations,
            instance_id=new_instance_id
        )
        
        # 添加工具到新 agent
        for tool in tools:
            new_agent.tool_registry.register(tool)
        
        return new_agent
