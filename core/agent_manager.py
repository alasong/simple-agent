"""
Agent Manager - 统一管理 builtin 和 custom agents

提供统一的接口来发现、加载和管理所有可用的 Agent
"""

from typing import Optional, Dict, List
from core.agent import Agent
from core.llm import OpenAILLM


def get_agent(agent_type: str, llm: Optional[OpenAILLM] = None) -> Agent:
    """
    获取 Agent（优先 builtin，然后 custom）
    
    Args:
        agent_type: agent 类型
        llm: LLM 实例
    
    Returns:
        Agent 实例
    
    Raises:
        ValueError: Agent 不存在
    """
    # 先尝试 builtin agents
    try:
        from builtin_agents import get_agent as get_builtin
        return get_builtin(agent_type, llm)
    except ValueError:
        pass  # builtin 中没有，继续尝试 custom
    
    # 尝试 custom agents
    try:
        from custom_agents import load_custom_agent
        agent = load_custom_agent(agent_type)
        if agent:
            return agent
    except Exception as e:
        print(f"[Warning] 加载自定义 Agent 失败：{e}")
    
    raise ValueError(f"未知的 Agent 类型：{agent_type}")


def list_all_agents() -> List[str]:
    """
    列出所有可用的 Agent（builtin + custom）
    
    Returns:
        agent 类型列表
    """
    agents = set()
    
    # 获取 builtin agents
    try:
        from builtin_agents import list_available_agents
        agents.update(list_available_agents())
    except Exception:
        pass
    
    # 获取 custom agents
    try:
        from custom_agents import list_custom_agents
        agents.update(list_custom_agents())
    except Exception:
        pass
    
    return sorted(list(agents))


def get_agent_info(agent_type: str) -> dict:
    """
    获取 Agent 信息（不创建实例）
    
    Args:
        agent_type: agent 类型
    
    Returns:
        agent 信息字典
    """
    # 先尝试 builtin
    try:
        from builtin_agents import get_agent_info
        return get_agent_info(agent_type)
    except ValueError:
        pass
    
    # 尝试 custom
    try:
        from custom_agents import get_custom_agent_config
        config = get_custom_agent_config(agent_type)
        if config:
            return {
                "type": agent_type,
                "name": config.get("name", ""),
                "version": config.get("version", ""),
                "description": config.get("description", ""),
                "tools": config.get("tools", []),
                "max_iterations": config.get("max_iterations", 10),
                "source": "custom"
            }
    except Exception:
        pass
    
    return {
        "type": agent_type,
        "name": agent_type,
        "description": "未知 Agent",
        "source": "unknown"
    }


def reload_all_agents():
    """重新加载所有 Agent 配置"""
    try:
        from builtin_agents import reload_all_configs
        reload_all_configs()
    except Exception:
        pass
    
    # custom agents 不缓存，无需 reload


__all__ = [
    "get_agent",
    "list_all_agents",
    "get_agent_info",
    "reload_all_agents"
]
