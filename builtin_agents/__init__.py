"""
Builtin Agents - 预定义的专业 Agent

基于统一的 Agent 配置框架，从 YAML 配置文件加载

可用 Agent 通过 list_available_agents() 获取，或查看 config/ 目录。
"""

# 先导入工具模块，确保工具注册到资源仓库
import tools  # noqa: F401

import os
import yaml
from typing import Optional, Dict, List
from pathlib import Path

from core.agent import Agent
from core.llm import OpenAILLM


# 配置目录
CONFIG_DIR = Path(__file__).parent / "configs"

# 缓存已加载的 agent 配置
_agent_configs: Dict[str, dict] = {}


def _load_agent_config(agent_type: str) -> dict:
    """
    加载 agent 配置文件
    
    Args:
        agent_type: agent 类型
        
    Returns:
        配置字典
    """
    # 检查缓存
    if agent_type in _agent_configs:
        return _agent_configs[agent_type]
    
    # 构建配置文件路径（支持 .yaml 和 .yml）
    for ext in [".yaml", ".yml"]:
        config_path = CONFIG_DIR / f"{agent_type}{ext}"
        if config_path.exists():
            break
    else:
        raise ValueError(f"未知的 agent 类型：{agent_type} (配置文件不存在：{CONFIG_DIR}/{agent_type}.yaml)")
    
    # 加载配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 缓存
    _agent_configs[agent_type] = config
    return config


def create_builtin_agent(agent_type: str, llm: Optional[OpenAILLM] = None) -> Agent:
    """
    创建 builtin agent（从配置文件加载）
    
    Args:
        agent_type: agent 类型（developer, reviewer, tester 等）
        llm: LLM 实例（默认使用 OpenAILLM）
    
    Returns:
        Agent 实例
    """
    # 加载配置
    config = _load_agent_config(agent_type)
    
    # 从资源仓库获取工具
    from core.resource import repo
    
    tools = []
    for tool_name in config.get("tools", []):
        tool_class = repo.get_tool(tool_name)
        if tool_class:
            tools.append(tool_class())
        else:
            print(f"[Warning] 未找到工具：{tool_name}")
    
    # 创建 Agent
    # 从统一配置加载默认 max_iterations
    from core.config_loader import get_config
    _config = get_config()
    default_max_iter = _config.get('agent.max_iterations', 10)
    
    agent = Agent(
        llm=llm or OpenAILLM(),
        tools=tools,
        system_prompt=config.get("system_prompt", ""),
        name=config.get("name", f"{agent_type.capitalize()} Agent"),
        version=config.get("version", "1.0.0"),
        description=config.get("description", ""),
        max_iterations=config.get("max_iterations", default_max_iter)
    )
    
    return agent


def get_agent(agent_type: str, llm: Optional[OpenAILLM] = None) -> Agent:
    """
    获取 agent（别名函数）
    
    Args:
        agent_type: agent 类型
        llm: LLM 实例
    
    Returns:
        Agent 实例
    """
    return create_builtin_agent(agent_type, llm)


def list_available_agents() -> List[str]:
    """
    列出所有可用的 agent 类型
    
    Returns:
        agent 类型列表
    """
    if not CONFIG_DIR.exists():
        return []
    
    # 扫描配置文件目录
    agents = []
    for config_file in CONFIG_DIR.glob("*.yaml"):
        agent_type = config_file.stem
        agents.append(agent_type)
    for config_file in CONFIG_DIR.glob("*.yml"):
        agent_type = config_file.stem
        if agent_type not in agents:  # 避免重复
            agents.append(agent_type)
    
    return sorted(agents)


def reload_all_configs():
    """
    重新加载所有配置（用于开发调试）
    
    清除缓存并重新加载配置文件
    """
    _agent_configs.clear()


def get_agent_info(agent_type: str) -> dict:
    """
    获取 agent 信息（不创建实例）
    
    Args:
        agent_type: agent 类型
    
    Returns:
        agent 信息字典
    """
    from core.config_loader import get_config
    _config = get_config()
    default_max_iter = _config.get('agent.max_iterations', 10)
    
    config = _load_agent_config(agent_type)
    return {
        "type": agent_type,
        "name": config.get("name", ""),
        "version": config.get("version", ""),
        "description": config.get("description", ""),
        "tools": config.get("tools", []),
        "max_iterations": config.get("max_iterations", default_max_iter)
    }


# 初始化：加载所有可用 agents
__all__ = [
    "create_builtin_agent",
    "get_agent",
    "list_available_agents",
    "reload_all_configs",
    "get_agent_info"
]
