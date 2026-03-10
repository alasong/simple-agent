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

上下文注入：在任务判断和执行前注入时间、地点等基本信息
"""

import asyncio
import os
import time
from datetime import datetime
from typing import Optional, Any, Dict

from core.llm import OpenAILLM
from core.config_loader import get_config
from core.task_queue import TaskQueue
from core.task_handle import TaskHandle

# 导入提示词配置，避免硬编码
from configs.cli_prompts import PromptTemplates, WeekdayConfig


class ContextInjectorConfig:
    """
    上下文注入器配置 - 从配置文件加载关键词

    避免在代码中硬编码关键词列表
    """

    # 默认关键词（当 YAML 配置不可用时）
    _default_time_keywords = ["今天", "日期", "时间", "星期", "放假", "开学", "暑假", "寒假", "安排", "时刻", "几点"]
    _default_location_keywords = ["天气", "位置", "地点", "哪里", "在哪", "北京", "上海", "广州", "深圳", "杭州"]
    _default_season_keywords = ["季节", "气候", "温度", "冷热", "穿衣"]

    _time_keywords: list = None
    _location_keywords: list = None
    _season_keywords: list = None

    @classmethod
    def _load_keywords(cls) -> None:
        """从 YAML 加载关键词"""
        if cls._time_keywords is not None:
            return  # 已加载

        try:
            import yaml
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'configs',
                'cli_keywords.yaml'
            )

            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}

                    # 合并默认值和配置值
                    if 'date_keywords' in config:
                        cls._time_keywords = list(set(cls._default_time_keywords + config['date_keywords']))
                    if 'weather_keywords' in config:
                        cls._location_keywords = list(set(cls._default_location_keywords + config['weather_keywords']))
                    if 'realtime_keywords' in config:
                        cls._season_keywords = list(set(cls._default_season_keywords + config['realtime_keywords']))
        except Exception:
            pass  # 使用默认值

        # 确保有值
        if cls._time_keywords is None:
            cls._time_keywords = cls._default_time_keywords
        if cls._location_keywords is None:
            cls._location_keywords = cls._default_location_keywords
        if cls._season_keywords is None:
            cls._season_keywords = cls._default_season_keywords

    @classmethod
    def get_time_keywords(cls) -> list:
        """获取时间相关关键词"""
        cls._load_keywords()
        return cls._time_keywords

    @classmethod
    def get_location_keywords(cls) -> list:
        """获取地点相关关键词"""
        cls._load_keywords()
        return cls._location_keywords

    @classmethod
    def get_season_keywords(cls) -> list:
        """获取季节相关关键词"""
        cls._load_keywords()
        return cls._season_keywords


class ContextInjector:
    """
    上下文注入器 - 在任务执行前注入基本信息

    注入的信息包括:
    - 时间上下文：当前日期、时间、星期、季节
    - 地点上下文：用户位置（如果有）
    - 任务分类：时间相关/地点相关/政策相关等
    """

    @staticmethod
    def get_time_context() -> Dict[str, Any]:
        """获取时间上下文"""
        now = datetime.now()
        weekday_str = WeekdayConfig.get_weekday(now.weekday())

        # 判断季节
        month = now.month
        if month in [3, 4, 5]:
            season = "春季"
        elif month in [6, 7, 8]:
            season = "夏季"
        elif month in [9, 10, 11]:
            season = "秋季"
        else:
            season = "冬季"

        # 判断学期状态（针对学校相关查询）
        if month in [2, 3, 4, 5, 6, 7]:
            semester = "下学期（春季学期）"
        elif month in [8, 9, 10, 11, 12, 1]:
            semester = "上学期（秋季学期）"
        else:
            semester = "未知"

        # 判断暑假/寒假期间
        is_summer_vacation = month in [7, 8]
        is_winter_vacation = month in [1, 2]

        return {
            "date": now.strftime("%Y 年%m 月%d 日"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": weekday_str,
            "season": season,
            "semester": semester,
            "is_summer_vacation": is_summer_vacation,
            "is_winter_vacation": is_winter_vacation,
            "month": month,
        }

    @staticmethod
    def build_context_string(user_input: str, verbose: bool = True) -> str:
        """
        构建上下文注入字符串

        Args:
            user_input: 用户输入
            verbose: 是否打印日志

        Returns:
            上下文注入字符串
        """
        time_ctx = ContextInjector.get_time_context()

        # 检测用户输入类型，决定注入哪些上下文
        context_parts = []

        # 时间相关查询：注入详细时间信息（使用配置关键词）
        time_keywords = ContextInjectorConfig.get_time_keywords()
        if any(kw in user_input for kw in time_keywords):
            context_parts.append(
                f"[当前时间信息] {time_ctx['date']}，{time_ctx['weekday']}，{time_ctx['time']}，"
                f"当前是{time_ctx['season']}{time_ctx['semester']}"
            )
            if time_ctx['is_summer_vacation']:
                context_parts.append("[当前状态] 正值暑假期间")
            elif time_ctx['is_winter_vacation']:
                context_parts.append("[当前状态] 正值寒假期间")

        # 地点相关查询：注入位置信息（如果有）
        location_keywords = ContextInjectorConfig.get_location_keywords()
        if any(kw in user_input for kw in location_keywords):
            # 可以尝试获取用户位置
            try:
                # 这里可以添加位置检测逻辑
                pass
            except Exception:
                pass

        # 季节/气候相关查询：注入季节信息
        season_keywords = ContextInjectorConfig.get_season_keywords()
        if any(kw in user_input for kw in season_keywords):
            context_parts.append(f"[当前季节] {time_ctx['season']}，{time_ctx['semester']}")

        if context_parts:
            return "\n".join(context_parts)
        return ""

    @staticmethod
    def inject_context(user_input: str, verbose: bool = True) -> str:
        """
        将上下文注入到用户输入中

        Args:
            user_input: 用户输入
            verbose: 是否打印日志

        Returns:
            注入上下文后的用户输入
        """
        context = ContextInjector.build_context_string(user_input, verbose)

        if context:
            if verbose:
                print(f"\n[上下文注入] 已注入:\n{context}")
            return f"{context}\n\n用户问题：{user_input}"

        return user_input

# 注意：不再需要 import tools 副作用导入
# 常用工具（BashTool, ReadFileTool, WriteFileTool）已默认导出
# 其他工具通过 ToolRegistry 按需加载


class TaskComplexityConfig:
    """
    任务复杂度判断配置 - 从配置文件加载模式列表

    避免在代码中硬编码判断模式
    """

    # 默认模式（当 YAML 配置不可用时）
    _default_simple_patterns = [
        "你好", "您好", "hello", "hi",  # 问候
        "谢谢", "感谢", "bye", "再见",  # 礼貌用语
        "你是谁", "你能做什么", "介绍下",  # 基础问答
    ]

    _default_complex_patterns = [
        "工作流", "CI/CD", "部署流程", "测试流程",
    ]

    _default_complexity_judge_prompt = """你是一个任务复杂度分类器。请判断以下用户输入是否需要多步规划和复杂推理：

用户输入：{user_input}

判断标准：
- 简单任务：单一问题、概念解释、代码片段、翻译、计算、**信息查询**（如天气、新闻、时间、政策、安排等）
- 复杂任务：需要多步骤、多工具协作、系统设计、流程规划、分析研究、项目执行

注意：用户查询类问题（如"xxx 安排"、"xxx 时间"、"xxx 政策"）通常是简单信息查询，不是复杂任务。

请只回答一个词：simple 或 complex"""

    _simple_patterns: list = None
    _complex_patterns: list = None
    _complexity_judge_prompt: str = None

    @classmethod
    def _load_patterns(cls) -> None:
        """从 YAML 加载模式列表"""
        if cls._simple_patterns is not None:
            return  # 已加载

        try:
            import yaml
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'configs',
                'cli_keywords.yaml'
            )

            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}

                    # 加载任务复杂度判断模式
                    if 'task_complexity' in config:
                        task_config = config['task_complexity']
                        if 'simple_patterns' in task_config:
                            cls._simple_patterns = list(set(cls._default_simple_patterns + task_config['simple_patterns']))
                        if 'complex_patterns' in task_config:
                            cls._complex_patterns = list(set(cls._default_complex_patterns + task_config['complex_patterns']))

                    # 加载 LLM 复杂度判断提示词
                    if 'llm_prompts' in config:
                        prompt_config = config['llm_prompts']
                        if 'complexity_judge' in prompt_config:
                            cls._complexity_judge_prompt = prompt_config['complexity_judge']
        except Exception:
            pass  # 使用默认值

        # 确保有值
        if cls._simple_patterns is None:
            cls._simple_patterns = cls._default_simple_patterns
        if cls._complex_patterns is None:
            cls._complex_patterns = cls._default_complex_patterns
        if cls._complexity_judge_prompt is None:
            cls._complexity_judge_prompt = cls._default_complexity_judge_prompt

    @classmethod
    def get_simple_patterns(cls) -> list:
        """获取简单任务模式"""
        cls._load_patterns()
        return cls._simple_patterns

    @classmethod
    def get_complex_patterns(cls) -> list:
        """获取复杂任务模式"""
        cls._load_patterns()
        return cls._complex_patterns

    @classmethod
    def get_complexity_judge_prompt(cls) -> str:
        """获取复杂度判断提示词"""
        cls._load_patterns()
        return cls._complexity_judge_prompt


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
        第二级：LLM 语义判断（不确定的任务，注入上下文）
        """
        # ========== 第一级：快速规则过滤 ==========

        # 空输入或极短输入视为简单任务
        if not user_input or len(user_input.strip()) < 5:
            if verbose:
                print("[CLI Agent] 任务判断：极短输入 -> 简单任务")
            return False

        # 明显的简单任务模式（直接返回，不调用 LLM）
        # 从配置加载，避免硬编码
        simple_patterns = TaskComplexityConfig.get_simple_patterns()

        for pattern in simple_patterns:
            if pattern in user_input.lower():
                if verbose:
                    print(f"[CLI Agent] 任务判断：匹配简单模式 '{pattern}' -> 简单任务")
                return False

        # 明显的复杂任务模式（多步骤、多条件）
        # 从配置加载，避免硬编码
        complex_patterns = TaskComplexityConfig.get_complex_patterns()

        for pattern in complex_patterns:
            if pattern in user_input:
                if verbose:
                    print(f"[CLI Agent] 任务判断：匹配复杂模式 '{pattern}' -> 复杂任务")
                return True

        # ========== 第二级：LLM 语义判断（注入上下文） ==========

        if verbose:
            print("[CLI Agent] 任务判断：规则无法确定，使用 LLM 判断...")

        # 注入上下文后让 LLM 判断
        enhanced_input = ContextInjector.inject_context(user_input, verbose)
        return self._llm_judge_complexity(enhanced_input, verbose)
    
    def _llm_judge_complexity(self, user_input: str, verbose: bool = True) -> bool:
        """
        使用 LLM 判断任务复杂度

        Returns:
            True: 复杂任务（需要规划）
            False: 简单任务（直接处理）
        """
        # 从配置加载提示词，避免硬编码
        prompt_template = TaskComplexityConfig.get_complexity_judge_prompt()
        prompt = prompt_template.format(user_input=user_input)

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

        # 注入上下文后委托给 Planner
        enhanced_input = ContextInjector.inject_context(user_input, verbose)

        # Planner Agent 负责处理复杂任务（注入上下文后的输入）
        result = planner.run(enhanced_input, verbose=verbose)

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

