"""
Agent 核心

Agent 是可部署的实体，支持：
- 序列化/反序列化
- 持久化存储
- 独立运行
"""

import json
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from .tool import BaseTool, ToolResult, ToolRegistry
from .memory import Memory
from .llm import LLMInterface, OpenAILLM


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


class Agent:
    """
    Agent 实体
    
    特性：
    - 可序列化为 JSON
    - 可持久化存储
    - 可独立部署运行
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
        max_iterations: int = 10,
        created_at: Optional[str] = None,
        instance_id: Optional[str] = None
    ):
        self.llm = llm
        self.name = name
        self.version = version
        self.description = description
        self.max_iterations = max_iterations
        self.created_at = created_at or datetime.now().isoformat()
        self.instance_id = instance_id  # 实例标识，用于区分同一 agent 的不同副本
        self.memory = Memory(system_prompt)
        
        # 注册工具
        self.tool_registry = ToolRegistry()
        self._tool_names: list[str] = []  # 保存工具名称用于序列化
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
    
    @property
    def system_prompt(self) -> str:
        """获取 system prompt"""
        for msg in self.memory.get_messages():
            if msg.get("role") == "system":
                return msg.get("content", "")
        return ""
    
    def __repr__(self) -> str:
        return f"<Agent {self.name} v{self.version}>"
    
    # ==================== 序列化 ====================
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "tools": self._tool_names,
            "max_iterations": self.max_iterations,
            "created_at": self.created_at,
            "instance_id": self.instance_id,
            "memory": self.memory.get_messages()
        }
    
    def to_json(self) -> str:
        """序列化为 JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def save(self, path: str):
        """保存到文件"""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], llm: Optional[LLMInterface] = None) -> "Agent":
        """从字典反序列化"""
        from .resource import repo
        
        # LLM
        if llm is None:
            llm = repo.extract_llm()
        
        # 工具
        tools = []
        for tool_name in data.get("tools", []):
            tool_class = repo.get_tool(tool_name)
            if tool_class:
                tools.append(tool_class())
        
        # 创建 Agent
        agent = cls(
            llm=llm,
            tools=tools,
            system_prompt=data.get("system_prompt", ""),
            name=data.get("name", "Agent"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            max_iterations=data.get("max_iterations", 10),
            created_at=data.get("created_at"),
            instance_id=data.get("instance_id")
        )
        
        # 恢复记忆
        for msg in data.get("memory", []):
            if msg.get("role") != "system":  # system 已在构造时添加
                agent.memory.messages.append(msg)
        
        return agent
    
    @classmethod
    def load(cls, path: str, llm: Optional[LLMInterface] = None) -> "Agent":
        """从文件加载"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data, llm)
    
    def clone(self, new_instance_id: Optional[str] = None) -> "Agent":
        """
        克隆当前 agent，创建一个配置相同但独立的新实例
        
        Args:
            new_instance_id: 新实例的 ID，用于标识
        
        Returns:
            新的 Agent 实例，具有：
            - 相同的配置（name, tools, system_prompt 等）
            - 独立的内存（Memory）
            - 独立的工具注册表
        """
        new_agent = Agent(
            llm=self.llm,
            tools=list(self.tool_registry.get_all_tools()),
            system_prompt=self.system_prompt,
            name=self.name,
            version=self.version,
            description=self.description,
            max_iterations=self.max_iterations,
            instance_id=new_instance_id
        )
        return new_agent
    
    # ==================== 运行 ====================
    
    def add_tool(self, tool: BaseTool):
        """添加工具"""
        self.tool_registry.register(tool)
        self._tool_names.append(tool.__class__.__name__)
    
    def _execute_tool(self, tool_name: str, arguments: dict) -> ToolResult:
        """执行工具"""
        tool = self.tool_registry.get(tool_name)
        if not tool:
            return ToolResult(success=False, output="", error=f"未知工具: {tool_name}")
        return tool.execute(**arguments)
    
    def run(self, user_input: str, verbose: bool = True) -> str:
        """主循环"""
        # 感知：添加用户输入
        self.memory.add_user(user_input)
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            
            # 推理：调用 LLM
            response = self.llm.chat(
                messages=self.memory.get_messages(),
                tools=self.tool_registry.get_openai_tools()
            )
            
            content = response["content"]
            tool_calls = response["tool_calls"]
            
            # 如果没有工具调用，返回结果
            if not tool_calls:
                self.memory.add_assistant(content)
                return content
            
            # 添加助手消息（带工具调用）
            self.memory.add_assistant(content, tool_calls=[
                {"id": tc["id"], "type": "function", "function": {
                    "name": tc["name"],
                    "arguments": json.dumps(tc["arguments"])
                }} for tc in tool_calls
            ])
            
            # 行动：执行所有工具调用
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                arguments = tool_call["arguments"]
                tool_id = tool_call["id"]
                
                result = self._execute_tool(tool_name, arguments)
                
                # 添加工具结果到记忆
                self.memory.add_tool_result(
                    tool_call_id=tool_id,
                    name=tool_name,
                    content=result.output if result.success else f"错误: {result.error}"
                )
        
        return f"达到最大迭代次数 ({self.max_iterations})，任务可能未完成"
