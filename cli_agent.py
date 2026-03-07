"""
CLI Agent - 统一的用户交互入口

职责:
1. 接收用户输入
2. 判断简单/复杂任务
3. 简单任务：直接回答
4. 复杂任务：委托给 Planner Agent 处理
5. 支持输出保存到文件

配置驱动：从 builtin_agents/configs/cli.json 加载
支持会话记忆：保持多轮对话上下文
"""

import asyncio
import os
import time
from datetime import datetime
from typing import Optional, Any

# 先导入工具模块，确保工具注册到资源仓库
import tools  # noqa: F401

from core.llm import OpenAILLM
from core.config_loader import get_config
from core.task_queue import TaskQueue
from core.task_handle import TaskHandle

# 导入提示词配置，避免硬编码
from configs.cli_prompts import PromptTemplates, WeekdayConfig


class CLIAgent:
    """
    CLI 入口 Agent
    
    只做入口判断，不处理复杂逻辑
    自身从配置文件加载
    """
    
    def __init__(self, llm: Optional[OpenAILLM] = None, max_concurrent: int = 3, instance_id: Optional[str] = None):
        self.llm = llm or OpenAILLM()
        self._agent = None  # CLI Agent 实例
        self._planner = None  # Planner Agent，延迟加载
        self._config = get_config()
        # 实例 ID - 用于输出隔离
        self.instance_id = instance_id
        # 任务队列 - 支持后台执行
        self.task_queue = TaskQueue(max_concurrent=max_concurrent)
        self._task_counter = 0
        self._queue_started = False
        # Note: CLIAgent delegates to self.agent and self.planner for execution
        # Memory is managed by those agents, not here
    
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
        max_iter = self._config.get('agent.cli_max_iterations', 5)
        return Agent(
            llm=self.llm,
            name="CLI Agent",
            description="用户交互入口",
            system_prompt="你是 CLI Agent，负责判断任务复杂度并分发。",
            max_iterations=max_iter
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
        max_iter = self._config.get('agent.planner_max_iterations', 15)
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
            max_iterations=max_iter
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
            return self._handle_simple_task(user_input, verbose, output_dir, isolate_by_instance)
        else:
            # 3. 复杂任务：委托给 Planner Agent
            return self._handle_complex_task(user_input, verbose, output_dir, isolate_by_instance)
    
    def _handle_simple_task(self, user_input: str, verbose: bool = True, 
                           output_dir: Optional[str] = None,
                           isolate_by_instance: bool = False) -> Any:
        """处理简单任务"""
        if verbose:
            print(f"\n[CLI Agent] 使用 CLI Agent 处理简单任务...")
        
        # 检测是否需要实时信息（使用配置中的关键词）
        enhanced_input = user_input
        
        # 日期查询：直接从系统获取当前日期（避免 LLM 编造）
        if any(kw in user_input for kw in PromptTemplates.get_date_keywords()):
            if verbose:
                print("[CLI Agent] 检测到日期查询，获取系统当前日期...")
            
            # 直接从系统获取日期，避免 LLM 编造
            now = datetime.now()
            weekday_str = WeekdayConfig.get_weekday(now.weekday())
            current_date_str = f"{now.year}年{now.month}月{now.day}日，{weekday_str}"
            
            if verbose:
                print(PromptTemplates.get_log_current_date(current_date_str))
            
            # 将准确日期注入到提示词
            enhanced_input = f"{user_input}（当前准确日期：{current_date_str}）"
        
        # 天气查询：直接从系统获取当前日期（更可靠，避免 LLM 编造）
        elif any(kw in user_input for kw in PromptTemplates.get_weather_keywords()):
            if verbose:
                print(PromptTemplates.get_log_weather_detection())
            
            # 直接从系统获取日期，避免 LLM 编造
            now = datetime.now()
            weekday_str = WeekdayConfig.get_weekday(now.weekday())
            current_date_str = f"{now.year}年{now.month}月{now.day}日，{weekday_str}"
            
            if verbose:
                print(PromptTemplates.get_log_current_date(current_date_str))
            
            # 将准确日期注入到提示词
            prompt_suffix = PromptTemplates.get_weather_prompt(current_date_str)
            enhanced_input = f"{user_input}{prompt_suffix}"
        
        # 实时信息查询
        elif any(kw in user_input for kw in PromptTemplates.get_realtime_keywords()):
            enhanced_input = f"{user_input}{PromptTemplates.get_realtime_prompt_template()}"
        
        result = self.agent.run(enhanced_input, verbose=verbose)
        
        # 保存输出到文件，并获取保存的路径
        saved_path = None
        if output_dir:
            saved_path = self._save_output(output_dir, result, user_input, isolate_by_instance)
        
        if verbose:
            print(f"\n[CLI Agent] 任务完成")
        
        # 返回结果和保存路径
        return result, saved_path
    
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
        
        # 保存输出到文件，并获取保存的路径
        saved_path = None
        if output_dir:
            saved_path = self._save_output(output_dir, result, user_input, isolate_by_instance)
        
        if verbose:
            print(f"\n[CLI Agent] 复杂任务处理完成")
        
        # 返回结果和保存路径
        return result, saved_path
    
    def _save_output(self, output_dir: str, result: Any, user_input: str,
                    isolate_by_instance: bool = False) -> Optional[str]:
        """保存输出到文件
        
        Returns:
            保存的文件路径，如果未保存则返回 None
        """
        # 测试环境防护：检测是否在测试环境中运行
        def is_test_environment():
            """检测是否在测试环境中运行"""
            import sys
            # 检查是否在 pytest 或 unittest 中运行
            if any(mod.startswith('pytest') or mod.startswith('unittest') for mod in sys.modules):
                return True
            # 检查环境变量
            if os.environ.get('TESTING') or os.environ.get('PYTEST_CURRENT_TEST'):
                return True
            return False
        
        # 在测试环境中跳过文件保存
        if is_test_environment():
            if os.environ.get('DEBUG_SAVE_OUTPUT'):
                # 如果显式要求保存，则继续
                pass
            else:
                # 否则跳过保存，避免污染文件系统
                return None
        
        try:
            # 创建输出目录
            if isolate_by_instance and hasattr(self.agent, 'instance_id') and self.agent.instance_id:
                # 按实例 ID 隔离
                output_path = os.path.join(output_dir, self.agent.instance_id)
            else:
                # 使用任务前缀作为目录名
                task_prefix = user_input[:20].replace('/', '_').replace('\\', '_').replace(' ', '_')
                output_path = os.path.join(output_dir, task_prefix)
            
            os.makedirs(output_path, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(output_path, f'result_{timestamp}.txt')
            
            # 保存结果
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# 任务输入\n{user_input}\n\n")
                f.write(f"# 执行时间\n{datetime.now().isoformat()}\n\n")
                f.write(f"# 执行结果\n{result}\n")
            
            print(f"\n[输出] 已保存到：{output_file}")
            
            # 返回保存的目录路径，用于在 cli.py 中显示
            return output_path
        
        except Exception as e:
            print(f"\n[警告] 保存输出失败：{e}")
            return None
    
    async def _ensure_queue_started(self):
        """确保任务队列已启动"""
        if not self._queue_started:
            await self.task_queue.start()
            self._queue_started = True
    
    async def execute_async(
        self,
        user_input: str,
        verbose: bool = True,
        output_dir: Optional[str] = None,
        isolate_by_instance: bool = False
    ) -> TaskHandle:
        """
        异步执行任务（后台执行，立即返回）
        
        Args:
            user_input: 用户输入
            verbose: 是否打印详细过程
            output_dir: 输出目录
            isolate_by_instance: 是否按实例隔离
        
        Returns:
            TaskHandle 对象，用于跟踪任务状态
        """
        # 确保队列已启动
        await self._ensure_queue_started()
        
        # 生成任务 ID
        self._task_counter += 1
        task_id = f"task_{self._task_counter}_{int(time.time() * 1000)}"
        
        # 创建执行协程
        async def task_coro():
            """任务执行包装器"""
            loop = asyncio.get_event_loop()
            
            # 在线程池中执行同步的 execute 方法
            def execute_task():
                return self.execute(
                    user_input,
                    verbose=verbose,
                    output_dir=output_dir,
                    isolate_by_instance=isolate_by_instance
                )
            
            return await loop.run_in_executor(None, execute_task)
        
        # 提交到任务队列
        handle = await self.task_queue.submit(
            task_id=task_id,
            input_text=user_input,
            coro=task_coro()
        )
        
        if verbose:
            print(f"\n[CLI Agent] ✓ 任务已提交到后台执行：{task_id}")
            print(f"[CLI Agent] 使用 /tasks 查看状态，/result {task_id} 查看结果")
        
        return handle
    
    def execute_background(
        self,
        user_input: str,
        verbose: bool = True,
        output_dir: Optional[str] = None,
        isolate_by_instance: bool = False
    ) -> TaskHandle:
        """
        同步方式提交后台任务（兼容接口）
        
        Args:
            user_input: 用户输入
            verbose: 是否打印详细过程
            output_dir: 输出目录
            isolate_by_instance: 是否按实例隔离
        
        Returns:
            TaskHandle 对象
        """
        # 创建新的事件循环来运行异步方法
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行（如在 Jupyter 中），创建 task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = loop.run_in_executor(
                        executor,
                        lambda: asyncio.run(self.execute_async(
                            user_input, verbose, output_dir, isolate_by_instance
                        ))
                    )
                    return asyncio.run_coroutine_threadsafe(future, loop).result()
            else:
                return loop.run_until_complete(self.execute_async(
                    user_input, verbose, output_dir, isolate_by_instance
                ))
        except RuntimeError:
            # 没有事件循环，创建新的
            return asyncio.run(self.execute_async(
                user_input, verbose, output_dir, isolate_by_instance
            ))

