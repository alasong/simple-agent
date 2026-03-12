"""
Agent - 统一的 Agent 实现

Agent 是可部署的实体，支持：
- 序列化/反序列化
- 持久化存储
- 独立运行
- 克隆创建多个副本
- 智能错误恢复
- 沙箱执行环境

沙箱支持：
- 每个任务在一个独立的沙箱目录中执行
- 目录结构：input/, process/temp/, process/cache/, output/, sandbox/
- 任务清单：manifest.json 记录元数据
"""

import json
import os
import traceback
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from datetime import datetime

from .tool import BaseTool, ToolResult, ToolRegistry
from .memory import Memory
from .llm import LLM, OpenAILLM, LLMInterface
from .sandbox import sandbox_manager, Sandbox


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


class Agent:
    """
    Agent - 统一的 Agent 类

    特性：
    - 可序列化为 JSON
    - 可持久化存储
    - 可独立运行
    - 支持克隆创建多个副本
    - 智能错误恢复
    """

    def __init__(
        self,
        llm: Optional[LLMInterface] = None,
        tools: Optional[list[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        name: str = "Agent",
        version: str = "1.0.0",
        description: str = "",
        max_iterations: int = 10,
        created_at: Optional[str] = None,
        instance_id: Optional[str] = None
    ):
        # 核心组件
        self.llm = llm or LLM()
        self.name = name
        self.version = version
        self.description = description
        self.max_iterations = max_iterations
        self.created_at = created_at or datetime.now().isoformat()
        self.instance_id = instance_id

        # 记忆管理
        self.memory = Memory(system_prompt)
        self._system_prompt = system_prompt or ""

        # 工具注册表
        self.tool_registry = ToolRegistry()
        self._tool_names: list[str] = []

        # 注册工具
        if tools:
            for tool in tools:
                self.tool_registry.register(tool)
                self._tool_names.append(tool.__class__.__name__)

        # 工具调用解析器（延迟导入）
        self._parser = None

        # 错误增强器
        self._error_enhancer = AgentErrorEnhancer()

    def _get_parser(self):
        """懒加载工具调用解析器"""
        if self._parser is None:
            from .tool_parser import ToolCallParser
            self._parser = ToolCallParser()
        return self._parser

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
        """获取系统提示词"""
        return self._system_prompt

    def __repr__(self) -> str:
        return f"<Agent {self.name} v{self.version}>"

    # ==================== 工具执行 ====================

    def _execute_tool(self, tool_name: str, arguments: dict) -> ToolResult:
        """执行工具（带异常处理）"""
        tool = self.tool_registry.get(tool_name)
        if not tool:
            return ToolResult(success=False, output="", error=f"未知工具：{tool_name}")

        # 验证参数
        if not isinstance(arguments, dict):
            return ToolResult(success=False, output="", error=f"工具参数必须是字典类型: {tool_name}")

        try:
            return tool.execute(**arguments)
        except TypeError as e:
            # 参数类型错误
            return ToolResult(success=False, output="", error=f"工具参数错误: {str(e)}")
        except Exception as e:
            # 工具执行异常（不中断整个任务）
            return ToolResult(success=False, output="", error=f"工具执行异常: {str(e)}")

    # ==================== 运行主循环 ====================

    def run(
        self,
        user_input: str,
        verbose: bool = True,
        debug: bool = False,
        output_dir: Optional[str] = None,
        enable_self_healing: bool = True,
        enable_sandbox: bool = True
    ) -> str:
        """
        主循环 - 带智能错误恢复和自愈能力，支持沙箱执行环境

        Args:
            user_input: 用户输入
            verbose: 是否打印详细过程
            debug: 是否启用调试跟踪
            output_dir: 输出目录（用于工具执行时保存文件）
            enable_self_healing: 是否启用自愈能力
            enable_sandbox: 是否启用沙箱模式

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

        # 设置全局 verbose 状态和 output_dir
        try:
            from simple_agent.tools.agent_tools import set_verbose
            set_verbose(verbose)
        except ImportError:
            pass

        # 设置文件工具的输出目录
        try:
            from simple_agent.tools.file import set_output_dir as set_file_output_dir
            if output_dir:
                set_file_output_dir(output_dir)
        except ImportError:
            pass

        # 设置沙箱目录
        sandbox = None
        if enable_sandbox:
            task_id = f"task_{int(time.time() * 1000)}"
            sandbox = sandbox_manager.create_sandbox(task_id)
            sandbox.manifest.user_input = user_input
            sandbox.manifest.created_at = datetime.now().isoformat()

            # 设置沙箱目录到执行上下文
            try:
                from simple_agent.core.execution_context import set_sandbox_dir
                set_sandbox_dir(str(sandbox.root))
            except ImportError:
                pass

            # 设置文件工具的沙箱目录
            try:
                from simple_agent.tools.file import set_sandbox_dir as set_file_sandbox_dir
                set_file_sandbox_dir(str(sandbox.root))
            except ImportError:
                pass

            # 设置 BashTool 的 sandbox_dir
            try:
                from simple_agent.tools.bash_tool import _execution_context
                _execution_context.sandbox_dir = str(sandbox.root)
            except ImportError:
                pass

            # 如果没有指定 output_dir，使用沙箱的 output 目录
            if not output_dir:
                output_dir = str(sandbox.output_dir)

        # 设置 BashTool 的输出目录（线程本地存储）
        try:
            from simple_agent.tools.bash_tool import _execution_context
            if output_dir:
                _execution_context.output_dir = os.path.abspath(output_dir)
        except ImportError:
            pass

        # 感知：添加用户输入
        self.memory.add_user(user_input)

        # 自愈相关
        recovery_attempts = 0
        max_recovery_attempts = 3 if enable_self_healing else 1
        original_agent = self if enable_self_healing else None

        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1

            try:
                # 保存断点（用于自愈恢复）
                if enable_self_healing and iteration > 1:
                    self._save_execution_checkpoint(
                        task_id=user_input[:50],
                        iteration=iteration,
                        pending_actions=[]
                    )

                # 推理：调用 LLM
                response = self.llm.chat(
                    messages=self.memory.get_messages(),
                    tools=self.tool_registry.get_openai_tools()
                )

                content = response["content"]
                tool_calls = response["tool_calls"]

                # 重置恢复计数（成功执行后）
                if tool_calls and enable_self_healing:
                    recovery_attempts = 0

                # 如果没有标准工具调用，尝试从 content 中解析
                if not tool_calls and content:
                    tool_calls = self._get_parser().parse(content)

                # 如果没有工具调用，返回结果
                if not tool_calls:
                    self.memory.add_assistant(content)

                    if debug and tracker.enabled and debug_record:
                        tracker.end_agent_execution(
                            debug_record, content, success=True,
                            tool_calls=0, iterations=iteration
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

                    # 如果工具执行失败，检查是否是需要确认的错误
                    if not result.success and result.error and "等待确认" in result.error:
                        if verbose:
                            print(f"[提示] 工具 {tool_name} 需要用户确认，自动重试...")

                        # 尝试用 confirmed_by_user=True 重试
                        arguments_with_confirm = arguments.copy()
                        arguments_with_confirm["confirmed_by_user"] = True
                        result = self._execute_tool(tool_name, arguments_with_confirm)

                        # 如果重试成功，使用成功的结果
                        if result.success:
                            if verbose:
                                print(f"[提示] 工具 {tool_name} 重试成功")
                            self.memory.add_tool_result(
                                tool_call_id=tool_id,
                                name=tool_name,
                                content=result.output
                            )
                            continue  # 继续下一个工具
                        # 如果重试失败，使用实际错误（而不是"等待确认"）
                        # 这样 LLM 知道真正的失败原因

                    # 失败时触发智能恢复
                    if not result.success:
                        if verbose:
                            print(f"[错误] 工具 {tool_name} 执行失败：{result.error}")

                        # 使用错误增强器提供智能应对建议
                        enhanced_error = self._error_enhancer.enhance_with_suggestions(
                            tool_name, arguments, result.error
                        )
                        self.memory.add_tool_result(
                            tool_call_id=tool_id,
                            name=tool_name,
                            content=enhanced_error
                        )
                    else:
                        self.memory.add_tool_result(
                            tool_call_id=tool_id,
                            name=tool_name,
                            content=result.output
                        )

            except Exception as e:
                # 捕获异常并触发自愈机制
                if enable_self_healing and recovery_attempts < max_recovery_attempts:
                    recovery_result = self._handle_exception_with_self_healing(
                        e, user_input, verbose
                    )

                    if recovery_result.success:
                        # 恢复成功，切换新 Agent 继续执行
                        if recovery_result.new_agent and recovery_result.new_agent != self:
                            print(f"[自愈] 切换到新 Agent: {recovery_result.new_agent.name}")
                            self._switch_to_agent(recovery_result.new_agent)
                        recovery_attempts += 1
                        continue  # 继续执行
                    else:
                        # 恢复失败，继续尝试其他策略
                        recovery_attempts += 1
                else:
                    # 自愈失败或已达到最大尝试次数
                    if verbose:
                        print(f"[严重] 自愈机制已用尽，任务终止")
                        if debug:
                            traceback.print_exc()

                    error_msg = f"任务执行失败：{str(e)}"
                    if recovery_attempts > 0:
                        error_msg += f" (已尝试自愈 {recovery_attempts} 次)"

                    if debug and tracker.enabled and debug_record:
                        tracker.end_agent_execution(
                            debug_record, error_msg, success=False,
                            tool_calls=0, iterations=iteration
                        )

                    # 保存沙箱清单（如果启用）
                    if sandbox:
                        sandbox.manifest.status = "failed"
                        sandbox.manifest.completed_at = datetime.now().isoformat()
                        sandbox.manifest.save(str(sandbox.root / "manifest.json"))

                    # 清理执行上下文
                    try:
                        from .execution_context import clear as clear_execution_context
                        clear_execution_context()
                    except ImportError:
                        pass

                    return error_msg

        result_text = f"达到最大迭代次数 ({self.max_iterations})，任务可能未完成"

        if debug and tracker.enabled and debug_record:
            tracker.end_agent_execution(
                debug_record, result_text, success=True,
                tool_calls=0, iterations=iteration
            )

        # 保存沙箱清单（如果启用）
        if sandbox:
            sandbox.manifest.status = "success"
            sandbox.manifest.completed_at = datetime.now().isoformat()
            sandbox.manifest.save(str(sandbox.root / "manifest.json"))

        # 清理执行上下文
        try:
            from .execution_context import clear as clear_execution_context
            clear_execution_context()
        except ImportError:
            pass

        return result_text

    def _handle_exception_with_self_healing(
        self,
        exception: Exception,
        task_description: str,
        verbose: bool
    ) -> Any:
        """处理异常并执行自愈"""
        from .resilience.self_healing import get_coordinator

        coordinator = get_coordinator()
        result = coordinator.handle_exception(
            agent=self,
            exception=exception,
            task_description=task_description
        )

        if verbose:
            print(f"[自愈] 恢复策略：{result.strategy.value}")
            if result.new_agent:
                print(f"[自愈] 新 Agent: {result.new_agent.name}")

        return result

    def _save_execution_checkpoint(
        self,
        task_id: str,
        iteration: int,
        pending_actions: List[Dict]
    ):
        """保存执行断点"""
        from .resilience.self_healing import get_coordinator

        coordinator = get_coordinator()
        coordinator.save_checkpoint(
            task_id=task_id,
            agent=self,
            iteration=iteration,
            memory_messages=list(self.memory.messages),
            pending_actions=pending_actions,
            completed_actions=[]
        )

    def _switch_to_agent(self, new_agent: Any):
        """切换到新 Agent（保留记忆和工具）"""
        # 复制记忆
        for msg in self.memory.messages:
            if msg.get("role") != "system":
                new_agent.memory.messages.append(msg)

        # 复制工具
        for tool in self.tool_registry.get_all_tools():
            if tool.__class__.__name__ not in [
                t.__class__.__name__ for t in new_agent.tool_registry.get_all_tools()
            ]:
                new_agent.tool_registry.register(tool)

        # 更新引用
        self.__dict__.update(new_agent.__dict__)

    # ==================== 序列化 ====================

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "system_prompt": self._system_prompt,
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
    def from_dict(
        cls,
        data: Dict[str, Any],
        llm: Optional[LLMInterface] = None
    ) -> "Agent":
        """从字典反序列化"""
        # 延迟导入避免循环依赖
        if llm is None:
            from .resource import repo
            llm = repo.extract_llm()

        from .resource import repo
        get_tool_func = repo.get_tool

        # 工具
        tools = []
        for tool_name in data.get("tools", []):
            tool_class = get_tool_func(tool_name)
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
            if msg.get("role") != "system":
                agent.memory.messages.append(msg)

        return agent

    @classmethod
    def load(cls, path: str, llm: Optional[LLMInterface] = None) -> "Agent":
        """从文件加载"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data, llm)

    # ==================== 克隆 ====================

    def clone(self, new_instance_id: Optional[str] = None) -> "Agent":
        """
        克隆当前 Agent，创建独立新实例

        Args:
            new_instance_id: 新实例的 ID

        Returns:
            新的 Agent 实例
        """
        # 获取工具列表
        tools = list(self.tool_registry.get_all_tools())

        # 创建新 agent
        new_agent = Agent(
            llm=self.llm,
            tools=tools,
            system_prompt=self._system_prompt,
            name=self.name,
            version=self.version,
            description=self.description,
            max_iterations=self.max_iterations,
            instance_id=new_instance_id
        )

        return new_agent


# ==================== 内部类：错误增强器 ====================

class AgentErrorEnhancer:
    """
    错误增强器

    为工具执行错误提供智能应对建议
    """

    def enhance_with_suggestions(self, tool_name: str, arguments: Dict, error: str) -> str:
        # 检测是否是代码组件名误认为工具
        # 常见的 React/前端组件名模式
        common_component_patterns = [
            "task", "form", "list", "item", "header", "footer", "nav", "sidebar",
            "button", "input", "select", "table", "card", "panel", "container",
            "app", "main", "content", "section", "row", "col", "grid", "flex",
            "modal", "popup", "dropdown", "menu", "tabs", "accordion", "carousel",
            "avatar", "badge", "breadcrumb", "checkbox", "radio", "slider", "switch",
            "alert", "toast", "tooltip", "popover", "dialog", "overlay", "layer",
        ]

        # 检测工具名是否符合代码组件命名模式（大驼峰，常见组件名）
        is_likely_component = (
            tool_name[0].isupper() and  # 大驼峰命名
            any(pattern in tool_name.lower() for pattern in common_component_patterns)
        )

        # 检测是否是变量名或类名（如 personal-todo-app）
        is_likely_variable = (
            tool_name.replace('-', '').replace('_', '').isalnum() and
            ('-' in tool_name or '_' in tool_name or tool_name[0].islower())
        )

        enhanced = f"错误：{error}\n\n"
        enhanced += "⚠️ **重要提示**：不要重复调用同一个工具！这个错误是持久性的，重试不会成功。\n\n"

        if is_likely_component:
            enhanced += f"💡 **检测到代码组件名误认为工具**：\n"
            enhanced += f"   '{tool_name}' 看起来是一个代码组件名（如 React 组件），而不是系统工具。\n"
            enhanced += f"   **请停止调用组件名作为工具！**\n"
            enhanced += f"   - 如果用户要求创建代码组件，直接返回代码，不要调用工具\n"
            enhanced += f"   - 系统允许的工具只有：BashTool, InvokeAgentTool, CreateWorkflowTool, ListAgentsTool, WebSearchTool, ExplainReasonTool, SupplementTool\n"
            enhanced += f"   - 代码组件（如 TaskForm, TaskList, Header, FilterPanel）不是工具！\n"
            enhanced += f"\n💡 **下一步**：\n"
            enhanced += f"   1. 停止尝试调用 '{tool_name}'\n"
            enhanced += f"   2. 直接提供代码实现\n"
            enhanced += f"   3. 如果需要文件写入，使用 WriteFileTool\n"
            enhanced += f"\n---\n\n"
        elif is_likely_variable:
            enhanced += f"💡 **检测到变量/类名误认为工具**：\n"
            enhanced += f"   '{tool_name}' 看起来是一个变量名、类名或项目名，而不是系统工具。\n"
            enhanced += f"   **请停止调用变量名作为工具！**\n"
            enhanced += f"\n💡 **下一步**：\n"
            enhanced += f"   1. 停止尝试调用 '{tool_name}'\n"
            enhanced += f"   2. 理解用户需求，提供实际解决方案\n"
            enhanced += f"\n---\n\n"
        elif tool_name == "WebSearchTool":
            enhanced += self._enhance_web_search_error(arguments, error)
        elif tool_name in ["GetCurrentDateTool", "DateTimeTool"]:
            enhanced += "💡 应对建议：\n"
            enhanced += "1. 使用 BashTool 执行 `date` 命令获取当前日期\n"
            enhanced += "2. 例如：`agent.run('date')`\n"
        else:
            enhanced += "💡 通用应对策略：\n"
            enhanced += "1. 尝试使用其他可用工具完成类似任务\n"
            enhanced += "2. 基于你的知识库提供帮助\n"
            enhanced += "3. 如果任务可以分解，尝试分步骤完成\n"
            enhanced += "4. 诚实地告诉用户限制，并提供替代方案\n"

        return enhanced

    def _enhance_web_search_error(self, arguments: Dict, error: str) -> str:
        query = arguments.get("query", "")

        enhanced = "💡 智能应对建议：\n"

        if "timeout" in error.lower() or "超时" in error or "timed out" in error.lower():
            enhanced += "1. **网络超时** → 立即采取以下替代方案（不要重试）：\n"
            enhanced += "   - **先获取日期**：使用 BashTool 执行 `date` 命令\n"
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

        return enhanced
