"""
Custom Agents - 用户自定义 Agent

支持加载用户自定义的 Agent 配置，扩展系统能力
"""

import os
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, List

from core.agent import Agent
from core.llm import OpenAILLM
from core.resource import repo


def get_custom_agents_dir() -> Path:
    """获取自定义 Agent 配置目录"""
    # 优先使用环境变量
    env_dir = os.environ.get("CUSTOM_AGENTS_DIR")
    if env_dir:
        return Path(env_dir)
    
    # 默认在项目目录
    return Path(__file__).parent


def list_custom_agents() -> List[str]:
    """列出所有可用的自定义 Agent"""
    configs_dir = get_custom_agents_dir() / "configs"
    if not configs_dir.exists():
        return []
    
    agents = []
    # 支持 .yaml, .yml 和 .json 格式
    for ext in ["*.yaml", "*.yml", "*.json"]:
        for config_file in configs_dir.glob(ext):
            agent_type = config_file.stem
            if agent_type not in agents:
                agents.append(agent_type)
    
    return sorted(agents)


def get_custom_agent_config(agent_type: str) -> Optional[Dict]:
    """获取自定义 Agent 的配置"""
    configs_dir = get_custom_agents_dir() / "configs"
    
    # 尝试多种格式：.yaml, .yml, .json
    for ext in [".yaml", ".yml", ".json"]:
        config_file = configs_dir / f"{agent_type}{ext}"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                if ext == ".json":
                    return json.load(f)
                else:
                    return yaml.safe_load(f)
    
    return None


def load_custom_agent(agent_type: str) -> Optional[Agent]:
    """加载自定义 Agent"""
    config = get_custom_agent_config(agent_type)
    if not config:
        return None
    
    # 检查 LLM 配置
    llm = OpenAILLM()
    if not llm.is_available():
        print("[Warning] LLM 不可用，无法创建 Agent")
        return None
    
    # 加载工具
    tools = []
    for tool_name in config.get("tools", []):
        try:
            tool_class = repo.get_tool(tool_name)
            if tool_class:
                tools.append(tool_class())
        except Exception as e:
            print(f"[Warning] 加载工具失败：{tool_name}, {e}")
    
    # 创建 Agent
    agent = Agent(
        name=config.get("name", agent_type),
        llm=llm,
        system_prompt=config.get("system_prompt", ""),
        description=config.get("description", ""),
        tools=tools,
        max_iterations=config.get("max_iterations", 10)
    )
    
    return agent
