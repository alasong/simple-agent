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
from .tool_parser import ToolCallParser


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
        # 从配置加载默认值
        from .config_loader import get_config
        _config = get_config()
        default_max_iter = _config.get('agent.max_iterations', 10)
        
        self.llm = llm
        self.name = name
        self.version = version
        self.description = description
        self.max_iterations = max_iterations if max_iterations is not None else default_max_iter
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
        
        # 工具调用解析器
        self.tool_parser = ToolCallParser()
    
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
            return ToolResult(success=False, output="", error=f"未知工具：{tool_name}")
        return tool.execute(**arguments)
    
    def _enhance_error_with_suggestions(self, tool_name: str, arguments: dict, error: str) -> str:
        """
        增强错误信息，提供智能应对建议
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            error: 原始错误信息
            
        Returns:
            增强后的错误信息，包含替代方案建议
        """
        enhanced = f"错误：{error}\n\n"
        enhanced += "⚠️ **重要提示**：不要重复调用同一个工具！这个错误是持久性的，重试不会成功。\n\n"
        
        # 针对 WebSearchTool 的特殊处理
        if tool_name == "WebSearchTool":
            query = arguments.get("query", "")
            fetch_content = arguments.get("fetch_content", False)
            
            enhanced += "💡 智能应对建议：\n"
            
            if "timeout" in error.lower() or "超时" in error or "timed out" in error.lower():
                enhanced += "1. **网络超时** → 立即采取以下替代方案（不要重试）：\n"
                enhanced += "   - **先获取日期**：使用 GetCurrentDateTool 确定今天的日期\n"
                enhanced += "   - 换一个搜索词或更具体的网站\n"
                enhanced += "   - 使用 fetch_content=false 先获取搜索结果列表\n"
                enhanced += "   - 换一个信息源（如直接访问目标网站）\n"
                enhanced += "   - 基于你的知识提供背景信息\n"
            elif "connection" in error.lower() or "连接" in error:
                enhanced += "1. **连接失败** → 尝试：\n"
                enhanced += "   - 换一个网站或搜索引擎\n"
                enhanced += "   - 使用你已有的知识库回答\n"
                enhanced += "   - 建议用户通过其他渠道获取\n"
            else:
                enhanced += "1. **搜索失败** → 尝试：\n"
                enhanced += "   - 换一种搜索方式或关键词\n"
                enhanced += "   - 直接访问相关专业网站\n"
                enhanced += "   - 基于已有知识提供帮助\n"
            
            enhanced += f"\n2. **替代方案示例**：\n"
            enhanced += f"   - 如果查询'{query}'失败，可以尝试：\n"
            
            # 根据查询类型提供具体建议
            if "天气" in query:
                enhanced += "     * 换一个天气网站（中国天气网、AccuWeather）\n"
                enhanced += "     * 先搜索'中国天气网 北京'找到 URL，再提取内容\n"
                enhanced += "     * 提供北京气候的一般知识\n"
            elif "新闻" in query or "最新" in query:
                enhanced += "     * 换搜索引擎或平台（微博、知乎、头条）\n"
                enhanced += "     * 搜索相关话题的历史背景\n"
                enhanced += "     * 解释如何追踪这类信息\n"
            elif "股价" in query or "股票" in query:
                enhanced += "     * 换财经网站（新浪财经、东方财富、雪球）\n"
                enhanced += "     * 提供股票分析方法\n"
                enhanced += "     * 解释基本面分析框架\n"
            else:
                enhanced += "     * 换一种表述或更具体的关键词\n"
                enhanced += "     * 访问相关领域的专业网站\n"
                enhanced += "     * 基于你的知识库提供相关信息\n"
            
            enhanced += "\n3. **最后的选择**：如果所有尝试都失败，诚实地告诉用户，并提供：\n"
            enhanced += "   - 你无法获取实时数据的原因\n"
            enhanced += "   - 用户可以自行访问的可靠来源\n"
            enhanced += "   - 你能够提供的背景知识或分析框架\n"
        
        # 针对 GetCurrentDateTool
        elif tool_name == "GetCurrentDateTool":
            enhanced += "💡 应对建议：\n"
            enhanced += "1. 如果日期工具失败，可以直接使用系统日期或用户提供的时间\n"
            enhanced += "2. 对于日期相关的查询，可以基于相对时间（如'今天'、'明天'）来回答\n"
        
        # 通用工具失败处理
        else:
            enhanced += "💡 通用应对策略：\n"
            enhanced += "1. 尝试使用其他可用工具完成类似任务\n"
            enhanced += "2. 基于你的知识库提供帮助\n"
            enhanced += "3. 如果任务可以分解，尝试分步骤完成\n"
            enhanced += "4. 诚实地告诉用户限制，并提供替代方案\n"
        
        return enhanced
    
    def run(self, user_input: str, verbose: bool = True) -> str:
        """主循环"""
        # 设置全局 verbose 状态（供工具使用）
        try:
            from tools.agent_tools import set_verbose
            set_verbose(verbose)
        except ImportError:
            pass
        
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
            
            # 如果 LLM 没有返回标准工具调用，尝试从 content 中解析
            if not tool_calls and content:
                tool_calls = self.tool_parser.parse(content)
            
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
            
            # 行动：执行所有工具调用（带智能失败恢复）
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                arguments = tool_call["arguments"]
                tool_id = tool_call["id"]
                
                # 执行工具
                result = self._execute_tool(tool_name, arguments)
                
                # 失败时触发智能恢复
                if not result.success:
                    if verbose:
                        print(f"[错误] 工具 {tool_name} 执行失败：{result.error}")
                    
                    # 在错误信息中附加智能应对建议，引导 LLM 采取替代方案
                    enhanced_error = self._enhance_error_with_suggestions(
                        tool_name, arguments, result.error
                    )
                    
                    # 添加增强后的错误信息到记忆
                    self.memory.add_tool_result(
                        tool_call_id=tool_id,
                        name=tool_name,
                        content=enhanced_error
                    )
                else:
                    # 成功则正常添加结果
                    self.memory.add_tool_result(
                        tool_call_id=tool_id,
                        name=tool_name,
                        content=result.output
                    )
        
        return f"达到最大迭代次数 ({self.max_iterations})，任务可能未完成"
