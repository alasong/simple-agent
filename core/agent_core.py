"""
Agent Core - 核心执行逻辑

专注于 Agent 的核心执行流程，不包含序列化、错误增强等附加功能
"""

from typing import Optional
import json

from .tool import BaseTool, ToolResult, ToolRegistry
from .memory import Memory
from .llm import LLMInterface
from .tool_parser import ToolCallParser


class AgentCore:
    """
    Agent 核心执行类
    
    职责:
    - 执行主循环
    - 工具调用解析
    - 工具执行
    
    非职责 (由其他类处理):
    - 序列化 (AgentSerializer)
    - 错误增强 (AgentErrorEnhancer)
    - 克隆 (AgentCloner)
    """
    
    def __init__(
        self,
        llm: LLMInterface,
        tool_registry: Optional[ToolRegistry] = None,
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
        self.created_at = created_at
        self.instance_id = instance_id
        
        # 记忆管理
        self.memory = Memory(system_prompt)
        
        # 工具注册表
        self.tool_registry = tool_registry or ToolRegistry()
        
        # 工具调用解析器
        self.tool_parser = ToolCallParser()
    
    def _execute_tool(self, tool_name: str, arguments: dict) -> ToolResult:
        """执行工具"""
        tool = self.tool_registry.get(tool_name)
        if not tool:
            return ToolResult(success=False, output="", error=f"未知工具：{tool_name}")
        return tool.execute(**arguments)
    
    def run(self, user_input: str, verbose: bool = True, 
            error_enhancer=None, debug: bool = False) -> str:
        """
        主循环 - 核心执行逻辑
        
        Args:
            user_input: 用户输入
            verbose: 是否打印详细过程
            error_enhancer: 可选的错误增强器（AgentErrorEnhancer）
            debug: 是否启用调试跟踪
        
        Returns:
            执行结果
        """
        import time
        from .debug import tracker
        
        # 调试跟踪
        debug_record = None
        if debug and tracker.enabled:
            debug_record = tracker.start_agent_execution(
                self.name, self.version, self.instance_id, user_input
            )
        
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
                
                # 结束调试跟踪
                if debug and tracker.enabled and debug_record:
                    tracker.end_agent_execution(
                        debug_record,
                        content,
                        success=True,
                        tool_calls=0,
                        iterations=iteration
                    )
                
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
                
                # 执行工具
                result = self._execute_tool(tool_name, arguments)
                
                # 失败时触发智能恢复（如果有 error_enhancer）
                if not result.success:
                    if verbose:
                        print(f"[错误] 工具 {tool_name} 执行失败：{result.error}")
                    
                    if error_enhancer:
                        # 使用错误增强器提供智能应对建议
                        enhanced_error = error_enhancer.enhance_with_suggestions(
                            tool_name, arguments, result.error
                        )
                        self.memory.add_tool_result(
                            tool_call_id=tool_id,
                            name=tool_name,
                            content=enhanced_error
                        )
                    else:
                        # 基本错误处理
                        self.memory.add_tool_result(
                            tool_call_id=tool_id,
                            name=tool_name,
                            content=f"错误：{result.error}"
                        )
                else:
                    # 成功则正常添加结果
                    self.memory.add_tool_result(
                        tool_call_id=tool_id,
                        name=tool_name,
                        content=result.output
                    )
        
        result_text = f"达到最大迭代次数 ({self.max_iterations})，任务可能未完成"
        
        # 结束调试跟踪
        if debug and tracker.enabled and debug_record:
            tracker.end_agent_execution(
                debug_record,
                result_text,
                success=True,
                tool_calls=0,
                iterations=iteration
            )
        
        return result_text
