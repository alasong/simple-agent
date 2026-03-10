"""
Agent 生成器

基于资源仓库创建 Agent:
1. 从仓库抽取工具
2. 从仓库抽取 LLM
3. 可继承已有 Agent
4. 自动生成提示词
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .agent import Agent
from .llm import LLMInterface
from .tool import BaseTool
from .resource import repo, ResourceRepository


class AgentGenerator:
    """Agent 生成器 - 版本管理"""
    
    _agent_versions: Dict[str, int] = {}
    
    def _next_version(self, name: str) -> str:
        """生成下一个版本号"""
        if name not in self._agent_versions:
            self._agent_versions[name] = 0
        self._agent_versions[name] += 1
        return f"1.0.{self._agent_versions[name]}"
    
    def _generate_prompt(self, name: str, description: str, tools: List[BaseTool]) -> str:
        """生成 System Prompt"""
        tools_desc = ", ".join([t.name for t in tools]) if tools else "无"
        
        prompt = f"""为以下 Agent 生成 System Prompt（不超过150字）：

名称: {name}
功能: {description}
工具: {tools_desc}

直接输出 Prompt:"""

        llm = repo.get_llm()
        response = llm.chat([{"role": "user", "content": prompt}])
        return response["content"].strip()


# ==================== 核心函数 ====================

def create_agent(
    description: str,
    name: Optional[str] = None,
    *,
    # 资源抽取
    tools: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    llm: str = "default",
    # 继承
    base: Optional[Agent] = None,
    # 额外配置
    system_prompt: Optional[str] = None,
) -> Agent:
    """
    创建 Agent
    
    从资源仓库抽取资源，结合需求创建新 Agent
    
    Args:
        description: Agent 功能描述
        name: Agent 名称（默认从描述提取）
        
        # 资源抽取
        tools: 指定工具名称列表
        tags: 按标签选择工具
        llm: LLM 名称（默认 "default"）
        
        # 继承
        base: 继承的 Agent，继承其工具和 LLM
        
        # 额外配置
        system_prompt: 自定义提示词（默认自动生成）
    
    Returns:
        Agent 实例
    """
    generator = AgentGenerator()
    
    # 名称
    if not name:
        words = description.split()[:3]
        name = "".join([w.capitalize() for w in words if w]) or "Agent"
    
    # LLM：继承或从仓库抽取
    if base:
        llm_instance = base.llm
    else:
        llm_instance = repo.extract_llm(llm)
    
    # 工具：从仓库抽取
    requirements = {
        "tools": tools or [],
        "tags": tags or [],
        "keywords": [description]
    }
    
    extracted_tools = repo.extract_tools(requirements)
    
    # 继承 base 的工具
    if base:
        inherited = list(base.tool_registry.get_all_tools())
        # 合并（去重）
        existing_names = {t.name for t in extracted_tools}
        for t in inherited:
            if t.name not in existing_names:
                extracted_tools.append(t)
    
    # 版本号
    version = generator._next_version(name)
    
    # 提示词
    if not system_prompt:
        system_prompt = generator._generate_prompt(name, description, extracted_tools)
    
    # 创建 Agent
    agent = Agent(
        llm=llm_instance,
        tools=extracted_tools,
        system_prompt=system_prompt,
        name=name,
        version=version,
        description=description
    )
    
    # 注册到仓库
    repo.register_agent(agent)
    
    return agent


def update_prompt(agent: Agent, description: str) -> Agent:
    """更新 Agent 提示词（创建新版本）"""
    generator = AgentGenerator()
    
    tools = agent.tool_registry.get_all_tools()
    new_prompt = generator._generate_prompt(agent.name, description, tools)
    version = generator._next_version(agent.name)
    
    new_agent = Agent(
        llm=agent.llm,
        tools=tools,
        system_prompt=new_prompt,
        name=agent.name,
        version=version,
        description=description
    )
    
    repo.register_agent(new_agent)
    return new_agent


def get_agent(name: str) -> Optional[Agent]:
    """获取已创建的 Agent"""
    return repo.get_agent(name)


def list_agents() -> Dict[str, Agent]:
    """列出所有 Agent"""
    return repo.list_agents()


# ==================== 便捷导出 ====================

# 从 resource 导出
from .resource import repo, ResourceRepository, tool, register_llm
