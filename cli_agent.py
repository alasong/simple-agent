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
    
    def _is_complex_task(self, user_input: str, verbose: bool = True) -> bool:
        """
        判断是否为复杂任务 - 采用两级判断策略
        
        第一级：快速规则过滤（明显的简单任务）
        第二级：LLM 语义判断（不确定的任务）
        """
        # ========== 第一级：快速规则过滤 ==========
        
        # 空输入或极短输入视为简单任务
        if not user_input or len(user_input.strip()) < 5:
            if verbose:
                print("[CLI Agent] 任务判断：极短输入 -> 简单任务")
            return False
        
        # 明显的简单任务模式（直接返回，不调用 LLM）
        simple_patterns = [
            "你好", "您好", "hello", "hi",  # 问候
            "谢谢", "感谢", "bye", "再见",  # 礼貌用语
            "你是谁", "你能做什么", "介绍下",  # 基础问答
        ]
        
        for pattern in simple_patterns:
            if pattern in user_input.lower():
                if verbose:
                    print(f"[CLI Agent] 任务判断：匹配简单模式 '{pattern}' -> 简单任务")
                return False
        
        # 明显的复杂任务模式（多步骤、多条件）
        complex_patterns = [
            "工作流", "CI/CD", "部署流程", "测试流程",
        ]
        
        for pattern in complex_patterns:
            if pattern in user_input:
                if verbose:
                    print(f"[CLI Agent] 任务判断：匹配复杂模式 '{pattern}' -> 复杂任务")
                return True
        
        # ========== 第二级：LLM 语义判断 ==========
        
        if verbose:
            print("[CLI Agent] 任务判断：规则无法确定，使用 LLM 判断...")
        
        return self._llm_judge_complexity(user_input, verbose)
    
    def _llm_judge_complexity(self, user_input: str, verbose: bool = True) -> bool:
        """
        使用 LLM 判断任务复杂度
        
        Returns:
            True: 复杂任务（需要规划）
            False: 简单任务（直接处理）
        """
        prompt = f"""你是一个任务复杂度分类器。请判断以下用户输入是否需要多步规划和复杂推理：

用户输入：{user_input}

判断标准：
- 简单任务：单一问题、概念解释、代码片段、翻译、计算、信息查询
- 复杂任务：需要多步骤、多工具协作、系统设计、流程规划、分析研究

请只回答一个词：simple 或 complex"""

        try:
            # 构建消息格式用于 LLM 调用
            messages = [
                {"role": "user", "content": prompt}
            ]
            response = self.llm.chat(messages)
            result = (response.get("content") or "").strip().lower()
            
            # 解析结果
            is_complex = "complex" in result
            
            if verbose:
                reason = "复杂任务" if is_complex else "简单任务"
                print(f"[CLI Agent] LLM 判断结果：{reason} (原始响应：{result})")
            
            return is_complex
            
        except Exception as e:
            # LLM 判断失败时，降级使用长度启发式
            if verbose:
                print(f"[CLI Agent] LLM 判断失败：{e}，降级使用规则判断")
            
            # 降级规则
            if len(user_input) > 100:
                return True
            if user_input.count(",") >= 2 or user_input.count(";") >= 2:
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
        # 1. 判断任务复杂度（LLM 判断会在内部打印详情）
        is_complex = self._is_complex_task(user_input, verbose)
        
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

