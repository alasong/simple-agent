"""
CLI Agent - 统一的用户交互入口

职责:
1. 接收用户输入
2. 判断简单/复杂任务
3. 简单任务：直接回答
4. 复杂任务：委托给 Planner Agent 处理

配置驱动：从 builtin_agents/configs/cli.json 加载
支持会话记忆：保持多轮对话上下文
"""

from typing import Optional, Any

# 先导入工具模块，确保工具注册到资源仓库
import tools  # noqa: F401

from core.llm import OpenAILLM


class CLIAgent:
    """
    CLI 入口 Agent
    
    只做入口判断，不处理复杂逻辑
    自身从配置文件加载
    """
    
    def __init__(self, llm: Optional[OpenAILLM] = None):
        self.llm = llm or OpenAILLM()
        self._agent = None  # CLI Agent 实例
        self._planner = None  # Planner Agent，延迟加载
    
    def _init_session_memory(self):
        """初始化会话记忆"""
        self.memory = create_memory(self.session_id)
        # 设置系统提示词到记忆
        if self.memory:
            self.memory.set_system_prompt(
                "你是 CLI Agent，是用户与系统交互的入口。"
                "请结合对话历史理解用户意图，保持上下文连贯性。"
            )
    
    @property
    def agent(self):
        """获取 CLI Agent 实例（延迟加载）"""
        if self._agent is None:
            try:
                from builtin_agents import get_agent
                self._agent = get_agent("cli")
            except (ImportError, ValueError):
                # 配置不存在时，创建临时的
                self._agent = self._create_fallback_agent()
        return self._agent
    
    def _create_fallback_agent(self):
        """创建临时 CLI Agent（当配置不存在时）"""
        from core.agent import Agent
        return Agent(
            llm=self.llm,
            name="CLI Agent",
            description="用户交互入口",
            system_prompt="你是 CLI Agent，负责判断任务复杂度并分发。",
            max_iterations=5
        )
    
    def _get_planner(self):
        """获取 Planner Agent"""
        if self._planner is None:
            try:
                from builtin_agents import get_agent
                self._planner = get_agent("planner")
            except (ImportError, ValueError):
                self._planner = self._create_fallback_planner()
        return self._planner
    
    def _create_fallback_planner(self):
        """创建临时 Planner Agent"""
        from core.agent import Agent
        return Agent(
            llm=self.llm,
            name="Planner Agent",
            description="任务规划师",
            system_prompt="""你是任务规划师，负责：
1. 分析复杂任务并分解为子任务
2. 创建和编排工作流
3. 调用专业 Agents 执行子任务
4. 合并结果并返回

你拥有的工具：
- InvokeAgentTool: 调用其他 Agent
- CreateWorkflowTool: 创建工作流
- ListAgentsTool: 查看可用的 Agent 列表""",
            max_iterations=15
        )
    
    def _is_complex_task(self, user_input: str) -> bool:
        """判断是否为复杂任务"""
        complex_indicators = [
            "多个", "流程", "工作流", "分解", "规划", "设计",
            "先", "然后", "再", "最后", "步骤", "阶段",
            "项目", "并行", "同时", "审查", "测试", "部署",
            "架构", "文档", "CI/CD",
            "分析", "研究", "调研", "趋势", "方案", "计划"
        ]
        
        simple_indicators = [
            "什么是", "为什么", "怎么", "如何", "解释", "说明",
            "帮我写", "写一个", "函数", "代码",
            "翻译", "计算", "转换"
        ]
        
        # 检查是否有明显的复杂任务关键词
        for indicator in complex_indicators:
            if indicator in user_input:
                # 但如果同时有简单关键词且任务很短，仍算简单
                has_simple = any(s in user_input for s in simple_indicators)
                if has_simple and len(user_input) < 30:
                    continue
                return True
        
        # 检查是否是明显的简单任务
        for indicator in simple_indicators:
            if indicator in user_input:
                if len(user_input) < 40:
                    return False
        
        # 默认：超过一定长度或有多个逗号分隔的任务算复杂
        if len(user_input) > 80 or user_input.count(",") >= 2 or user_input.count(",") >= 2:
            return True
        
        return False
    
    def execute(self, user_input: str, verbose: bool = True, 
                output_dir: Optional[str] = None, isolate_by_instance: bool = False) -> Any:
        """
        执行任务
        
        Args:
            user_input: 用户输入
            verbose: 是否打印详细过程
            output_dir: 输出目录
            isolate_by_instance: 是否按实例隔离
        
        Returns:
            执行结果
        """
        # 1. 判断任务复杂度
        is_complex = self._is_complex_task(user_input)
        
        if verbose:
            print(f"\n[CLI Agent] 任务复杂度：{'复杂' if is_complex else '简单'}")
        
        if not is_complex:
            # 2. 简单任务：使用 CLI Agent 直接回答
            return self._handle_simple_task(user_input, verbose)
        else:
            # 3. 复杂任务：委托给 Planner Agent
            return self._handle_complex_task(user_input, verbose, output_dir, isolate_by_instance)
    
    def _handle_simple_task(self, user_input: str, verbose: bool = True) -> Any:
        """处理简单任务"""
        if verbose:
            print(f"\n[CLI Agent] 使用 CLI Agent 处理简单任务...")
        
        # 检测是否需要实时信息
        date_keywords = ["今天", "日期", "几号", "星期", "时间", "现在几点"]
        realtime_keywords = [
            "新闻", "头条", "最新", "股价", "比分", "排名", "热搜", "疫情"
        ]
        weather_keywords = ["天气", "气温", "下雨", "刮风", "雾霾", "空气质量"]
        
        # 如果查询包含日期关键词，使用 GetCurrentDateTool
        enhanced_input = user_input
        if any(kw in user_input for kw in date_keywords):
            enhanced_input = f"{user_input}（请使用 GetCurrentDateTool 获取当前日期）"
        elif any(kw in user_input for kw in weather_keywords):
            enhanced_input = f"{user_input}（请使用 WebSearchTool 搜索，设置 fetch_content=true 获取详细天气信息）"
        elif any(kw in user_input for kw in realtime_keywords):
            enhanced_input = f"{user_input}（请使用 WebSearchTool 搜索获取最新信息）"
        
        result = self.agent.run(enhanced_input, verbose=verbose)
        
        if verbose:
            print(f"\n[CLI Agent] 任务完成")
        
        return result
    
    def _handle_complex_task(self, user_input: str, verbose: bool = True,
                             output_dir: Optional[str] = None,
                             isolate_by_instance: bool = False) -> Any:
        """处理复杂任务 - 委托给 Planner Agent"""
        planner = self._get_planner()
        
        if verbose:
            print(f"\n[CLI Agent] 委托给 Planner Agent 进行任务分解...")
            print(f"[CLI Agent] Planner: {planner.name}")
        
        # Planner Agent 负责处理复杂任务
        result = planner.run(user_input, verbose=verbose)
        
        if verbose:
            print(f"\n[CLI Agent] 复杂任务处理完成")
        
        return result

