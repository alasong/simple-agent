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
import threading
import time
from datetime import datetime
from typing import Optional, Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum

from simple_agent.core.llm import OpenAILLM
from simple_agent.core.config_loader import get_config
from simple_agent.core.task_queue import TaskQueue
from simple_agent.core.task_handle import TaskHandle
from simple_agent.core.strategy_router import StrategyRouter, create_router


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    user_input: str
    status: TaskStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    verbose: bool = True
    output_dir: Optional[str] = None
    interactive: bool = False

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
            # cli_agent.py 和 configs 目录同级
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
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

    使用 StrategyRouter 统一决策系统来判断任务复杂度和选择执行策略
    自身从配置文件加载
    """

    def __init__(
        self,
        llm: Optional[OpenAILLM] = None,
        max_concurrent: int = 3,
        instance_id: Optional[str] = None,
        agent_pool: Optional[List[Any]] = None
    ):
        self.llm = llm or OpenAILLM()
        self._agent = None  # CLI Agent 实例
        self._planner = None  # Planner Agent，延迟加载
        self._config = get_config()
        self.agent_pool = agent_pool or []
        # 实例 ID - 用于输出隔离
        self.instance_id = instance_id
        # 任务队列 - 支持后台执行
        self.task_queue = TaskQueue(max_concurrent=max_concurrent)
        self._task_counter = 0
        self._queue_started = False
        # Session 管理 - 支持多轮交互
        self._session_memory: Dict[str, List[Dict]] = {}  # task_id -> messages
        self._current_session: Optional[str] = None  # 当前会话的 task_id
        # 任务追踪 - 支持查看正在执行的任务
        self._tasks: Dict[str, TaskInfo] = {}
        self._tasks_lock = threading.Lock()
        # StrategyRouter - 统一决策系统
        self.strategy_router = create_router(
            agent_pool=self.agent_pool,
            llm=self.llm
        )
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

            # 注册 Agent 到注册中心
            self._register_agent(self._agent, "cli")
        return self._agent
    
    def _create_fallback_agent(self):
        """创建临时 CLI Agent（当配置不存在时）"""
        from simple_agent.core.agent import Agent
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
                from simple_agent.builtin_agents import get_agent
                self._planner = get_agent("planner")
            except (ImportError, ValueError):
                self._planner = self._create_fallback_planner()

            # 注册 Agent 到注册中心
            self._register_agent(self._planner, "planner")
        return self._planner

    def _register_agent(self, agent, agent_type: str):
        """注册 Agent 到注册中心"""
        try:
            from simple_agent.core.agent_registry import get_agent_registry, AgentSource
            registry = get_agent_registry()
            registry.register(agent, source=AgentSource.CLI)
        except Exception:
            pass  # 注册失败不影响主流程

    # ==================== 任务追踪 ====================

    def _create_task_info(self, task_id: str, user_input: str, verbose: bool,
                         output_dir: Optional[str], interactive: bool) -> TaskInfo:
        """创建任务信息"""
        return TaskInfo(
            task_id=task_id,
            user_input=user_input,
            status=TaskStatus.PENDING,
            created_at=datetime.now().isoformat(),
            verbose=verbose,
            output_dir=output_dir,
            interactive=interactive
        )

    def _update_task_status(self, task_id: str, status: TaskStatus, **kwargs):
        """更新任务状态"""
        with self._tasks_lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                if status == TaskStatus.RUNNING and not task.started_at:
                    task.started_at = datetime.now().isoformat()
                elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                    task.completed_at = datetime.now().isoformat()
                task.status = status
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)

    def _save_task_info(self, task_info: TaskInfo):
        """保存任务信息"""
        with self._tasks_lock:
            self._tasks[task_info.task_id] = task_info

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务信息"""
        with self._tasks_lock:
            return self._tasks.get(task_id)

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[TaskInfo]:
        """列出任务，可按状态过滤"""
        with self._tasks_lock:
            if status:
                return [t for t in self._tasks.values() if t.status == status]
            return list(self._tasks.values())

    def get_running_tasks(self) -> List[TaskInfo]:
        """获取正在执行的任务"""
        return self.list_tasks(status=TaskStatus.RUNNING)

    def get_pending_tasks(self) -> List[TaskInfo]:
        """获取待执行的任务"""
        return self.list_tasks(status=TaskStatus.PENDING)

    # ==================== Session 管理 ====================

    def create_session(self, task_id: str, user_input: str) -> str:
        """
        创建新的 session

        Args:
            task_id: 任务 ID
            user_input: 初始输入

        Returns:
            session ID（与 task_id 相同）
        """
        self._session_memory[task_id] = [
            {"role": "user", "content": user_input}
        ]
        self._current_session = task_id
        return task_id

    def continue_session(self, task_id: str, user_input: str) -> str:
        """
        在现有 session 中继续交互

        Args:
            task_id: 任务 ID（session ID）
            user_input: 新的用户输入

        Returns:
            Agent 的响应
        """
        if task_id not in self._session_memory:
            raise ValueError(f"Session {task_id} 不存在")

        # 添加用户消息到 session 记忆
        self._session_memory[task_id].append({"role": "user", "content": user_input})
        self._current_session = task_id

        # 获取用于继续对话的输入（包含完整上下文）
        session_messages = self._session_memory[task_id]

        # 使用 Agent 继续对话
        agent = self._get_active_agent_for_session(task_id)

        # 调用 Agent 的 run 方法（使用 session 记忆）
        # 通过注入上下文的方式继续对话
        if hasattr(agent, 'memory'):
            # 将 session 消息恢复到 agent 记忆
            for msg in session_messages:
                if msg["role"] == "user":
                    agent.memory.add_user(msg["content"])
                elif msg["role"] == "assistant":
                    agent.memory.add_assistant(msg["content"])

        # 获取 Agent 的响应
        response = agent.run(user_input, verbose=self._get_verbose_for_session(task_id))

        # 保存助手响应到 session
        self._session_memory[task_id].append({"role": "assistant", "content": response})

        return response

    def continue_session_and_execute(self, task_id: str, user_input: str) -> Any:
        """
        在 session 中继续交互并执行任务（用于确认等待的任务）

        Args:
            task_id: 任务 ID
            user_input: 用户输入

        Returns:
            执行结果
        """
        if task_id not in self._session_memory:
            raise ValueError(f"Session {task_id} 不存在")

        # 检查任务是否等待确认
        from simple_agent.core.task_handle import TaskStatusEnum
        handle = self.task_queue._tasks.get(task_id)
        if handle and handle.status.status == TaskStatusEnum.CONFIRMING:
            # 任务等待确认，执行它
            async def execute_confirmed_task():
                return self.execute(
                    self._session_memory[task_id][0]["content"],  # 原始任务
                    verbose=True,
                    session_id=task_id,
                    create_session=False,
                    interactive=False  # 已确认，不再需要交互
                )

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    result = asyncio.run_coroutine_threadsafe(execute_confirmed_task(), loop).result()
                else:
                    result = loop.run_until_complete(execute_confirmed_task())
            except Exception as e:
                import traceback
                return f"[执行失败] {e}\n{traceback.format_exc()}"

            return result

        # 正常的 session 继续
        return self.continue_session(task_id, user_input)

    def _get_active_agent_for_session(self, task_id: str):
        """获取 session 关联的 Agent"""
        # 默认使用 CLI Agent
        return self.agent

    def _get_verbose_for_session(self, task_id: str) -> bool:
        """获取 session 的 verbose 设置"""
        with self._tasks_lock:
            task = self._tasks.get(task_id)
            return task.verbose if task else True

    def get_session_history(self, task_id: str) -> List[Dict]:
        """获取 session 的历史消息"""
        return self._session_memory.get(task_id, [])

    def end_session(self, task_id: str):
        """结束 session"""
        if task_id in self._session_memory:
            del self._session_memory[task_id]
        if self._current_session == task_id:
            self._current_session = None

    def print_task_status(self, task_id: str):
        """打印任务状态"""
        task = self.get_task(task_id)
        if not task:
            print(f"[任务 {task_id}] 不存在")
            return

        print(f"\n{'='*60}")
        print(f"[任务 {task_id}] 状态")
        print(f"{'='*60}")
        print(f"状态: {task.status.value}")
        print(f"创建时间: {task.created_at}")
        if task.started_at:
            print(f"开始时间: {task.started_at}")
        if task.completed_at:
            print(f"完成时间: {task.completed_at}")
        print(f"交互模式: {task.interactive}")
        print(f"输出目录: {task.output_dir}")
        print(f"输入: {task.user_input[:100]}{'...' if len(task.user_input) > 100 else ''}")
        if task.result:
            print(f"结果: {task.result[:100]}{'...' if len(task.result) > 100 else ''}")
        if task.error:
            print(f"错误: {task.error}")
        print(f"{'='*60}")

    def print_running_tasks(self):
        """打印正在执行的任务"""
        tasks = self.get_running_tasks()
        if not tasks:
            print("[任务] 没有正在执行的任务")
            return

        print(f"\n{'='*60}")
        print(f"[任务] 正在执行的任务 ({len(tasks)} 个)")
        print(f"{'='*60}")
        for task in tasks:
            print(f"  • {task.task_id}: {task.user_input[:50]}...")
        print(f"{'='*60}")

    def print_all_tasks(self):
        """打印所有任务"""
        tasks = self.list_tasks()
        if not tasks:
            print("[任务] 没有任务记录")
            return

        print(f"\n{'='*60}")
        print(f"[任务] 任务列表 ({len(tasks)} 个)")
        print(f"{'='*60}")

        # 按状态分组
        by_status = {}
        for task in tasks:
            status = task.status.value
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(task)

        for status, status_tasks in by_status.items():
            print(f"\n[{status.upper()}] ({len(status_tasks)} 个)")
            for task in status_tasks:
                print(f"  • {task.task_id}: {task.user_input[:50]}...")

        print(f"{'='*60}")

    def _create_fallback_planner(self):
        """创建临时 Planner Agent"""
        from simple_agent.core.agent import Agent
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

## 软件开发任务特别处理

当用户请求开发软件、应用、系统、网站等时（关键词：开发、创建、实现、构建 + 软件/系统/网站/应用等），
**必须使用 SoftwareDeveloper Agent** 来执行任务。

SoftwareDeveloper Agent 会自动：
- 创建项目结构和环境
- 编写代码和测试
- 运行测试并生成报告
- 编写文档

## 你拥有的工具：
- InvokeAgentTool: 调用其他 Agent（如 SoftwareDeveloper, Tester, Documenter 等）
- CreateWorkflowTool: 创建工作流
- ListAgentsTool: 查看可用的 Agent 列表
- DevWorkflowTool: 软件开发工作流（代码检查、测试、构建）
""",
            max_iterations=max_iter
        )
    
    def _is_complex_task(self, user_input: str, verbose: bool = True) -> bool:
        """
        判断是否为复杂任务 - 使用 StrategyRouter 进行统一决策

        Returns:
            True: 复杂任务（需要规划）
            False: 简单任务（直接处理）
        """
        # 使用 StrategyRouter 进行路由决策
        import asyncio

        try:
            # Run the async route function sync
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.strategy_router.route(user_input))
            finally:
                loop.close()

            # 使用复杂度阈值判断
            complexity = result.complexity_estimate
            is_complex = complexity > 0.5

            if verbose:
                # 只打印关键信息
                strategy_used = result.strategy.value if hasattr(result, 'strategy') else "unknown"
                print(f"[CLI Agent] 策略路由: 复杂度={complexity:.2f}, 建议策略={strategy_used}")

            return is_complex

        except Exception as e:
            # StrategyRouter 失败时，降级到原有逻辑
            if verbose:
                print(f"[CLI Agent] 策略路由失败：{e}，降级使用规则判断")

            # 降级规则（原始逻辑）
            if not user_input or len(user_input.strip()) < 5:
                return False

            complex_patterns = TaskComplexityConfig.get_complex_patterns()
            for pattern in complex_patterns:
                if pattern in user_input:
                    return True

            # 长度启发式
            if len(user_input) > 100:
                return True
            if user_input.count(",") >= 2 or user_input.count(";") >= 2:
                return True
            return False
    
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
                output_dir: Optional[str] = None, isolate_by_instance: bool = False,
                interactive: bool = False, session_id: Optional[str] = None,
                create_session: bool = True) -> Any:
        """
        执行任务

        Args:
            user_input: 用户输入
            verbose: 是否打印详细过程
            output_dir: 输出目录
            isolate_by_instance: 是否按实例隔离
            interactive: 是否启用交互模式（关键步骤询问用户）
            session_id: 任务 session ID（用于Continuation对话）
            create_session: 是否创建新 session

        Returns:
            执行结果
        """
        # 生成 task_id
        self._task_counter += 1
        task_id = f"task_{self._task_counter}_{int(time.time() * 1000)}"

        # 如果提供了 session_id，使用它作为 task_id
        if session_id:
            task_id = session_id
            # 在 session 中继续对话
            if not create_session:
                try:
                    return self.continue_session(task_id, user_input)
                except ValueError as e:
                    # Session 不存在，创建新的
                    if verbose:
                        print(f"[Session] {e}，创建新的 session")
                    self.create_session(task_id, user_input)

        # 创建任务信息
        task_info = self._create_task_info(task_id, user_input, verbose, output_dir, interactive)
        self._save_task_info(task_info)

        # 交互模式：确认执行任务
        if interactive and verbose:
            print(f"\n{'='*60}")
            print("[交互确认] 准备执行任务")
            print(f"任务：{user_input[:80]}{'...' if len(user_input) > 80 else ''}")
            print(f"{'='*60}")
            try:
                confirm = input("是否继续执行？(Y/n): ").strip().lower()
                if confirm in ('n', 'no'):
                    self._update_task_status(task_id, TaskStatus.CANCELLED)
                    return "[用户取消] 任务已取消"
            except EOFError:
                # 非交互模式，继续执行
                pass

        # 1. 判断任务复杂度（LLM 判断会在内部打印详情）
        is_complex = self._is_complex_task(user_input, verbose)

        if verbose:
            print(f"\n[CLI Agent] 任务复杂度：{'复杂' if is_complex else '简单'}")

        self._update_task_status(task_id, TaskStatus.RUNNING)

        if not is_complex:
            # 2. 简单任务：使用 CLI Agent 直接回答
            try:
                result = self._handle_simple_task(user_input, verbose, output_dir, isolate_by_instance, interactive, task_id)
                self._update_task_status(task_id, TaskStatus.COMPLETED, result=str(result))
                return result
            except Exception as e:
                self._update_task_status(task_id, TaskStatus.FAILED, error=str(e))
                raise
        else:
            # 3. 复杂任务：委托给 Planner Agent
            try:
                result = self._handle_complex_task(user_input, verbose, output_dir, isolate_by_instance, interactive, task_id)
                self._update_task_status(task_id, TaskStatus.COMPLETED, result=str(result))
                return result
            except Exception as e:
                self._update_task_status(task_id, TaskStatus.FAILED, error=str(e))
                raise
    
    def _handle_simple_task(self, user_input: str, verbose: bool = True,
                           output_dir: Optional[str] = None,
                           isolate_by_instance: bool = False,
                           interactive: bool = False,
                           task_id: Optional[str] = None) -> Any:
        """处理简单任务"""
        # 任务开始时更新状态（如果提供了 task_id）
        if task_id:
            self._update_task_status(task_id, TaskStatus.RUNNING)

        # 交互模式：确认简单任务执行
        if interactive and verbose:
            print(f"\n{'='*60}")
            print("[交互确认] 准备执行简单任务")
            print(f"任务：{user_input[:60]}{'...' if len(user_input) > 60 else ''}")
            print(f"{'='*60}")
            try:
                confirm = input("是否继续执行？(Y/n): ").strip().lower()
                if confirm in ('n', 'no'):
                    if task_id:
                        self._update_task_status(task_id, TaskStatus.CANCELLED)
                    return "[用户取消] 任务已取消"
            except EOFError:
                pass

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

        result = self.agent.run(enhanced_input, verbose=verbose, output_dir=output_dir)

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
                             isolate_by_instance: bool = False,
                             interactive: bool = False,
                             task_id: Optional[str] = None) -> Any:
        """处理复杂任务 - 委托给 Planner Agent"""
        # 任务开始时更新状态（如果提供了 task_id）
        if task_id:
            self._update_task_status(task_id, TaskStatus.RUNNING)

        # 交互模式：确认复杂任务执行
        if interactive and verbose:
            print(f"\n{'='*60}")
            print("[交互确认] 准备执行复杂任务")
            print(f"任务：{user_input[:60]}{'...' if len(user_input) > 60 else ''}")
            print("说明：复杂任务将由 Planner Agent 进行任务分解和规划")
            print(f"{'='*60}")
            try:
                confirm = input("是否继续执行？(Y/n): ").strip().lower()
                if confirm in ('n', 'no'):
                    if task_id:
                        self._update_task_status(task_id, TaskStatus.CANCELLED)
                    return "[用户取消] 任务已取消"
            except EOFError:
                pass

        planner = self._get_planner()

        if verbose:
            print(f"\n[CLI Agent] 委托给 Planner Agent 进行任务分解...")
            print(f"[CLI Agent] Planner: {planner.name}")

        # 注入上下文后委托给 Planner
        enhanced_input = ContextInjector.inject_context(user_input, verbose)

        # Planner Agent 负责处理复杂任务（注入上下文后的输入）
        result = planner.run(enhanced_input, verbose=verbose, output_dir=output_dir)

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

        # 检测测试环境
        is_testing = is_test_environment()

        # Debug 模式下显示质量评估（即使在测试环境中也显示）
        if os.environ.get('DEBUG'):
            self._show_quality_assessment(result, user_input)

        # 在测试环境中跳过文件保存（除非显式要求）
        if is_testing:
            if os.environ.get('DEBUG_SAVE_OUTPUT'):
                # 如果显式要求保存，则继续
                pass
            else:
                # 否则跳过保存，避免污染文件系统
                return None

        try:
            # 直接使用 output_dir 作为输出路径
            # 注意：output_dir 已由 CLI Coordinator 生成为任务专属路径
            # 不需要再创建额外的子目录
            output_path = output_dir

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

    def _show_quality_assessment(self, result: str, user_input: str):
        """
        Phase 6: 显示质量评估结果（debug 模式）

        Args:
            result: Agent 输出内容
            user_input: 用户输入
        """
        try:
            from simple_agent.swarm.quality.checker import create_checker
            from simple_agent.swarm.quality.evaluator import FeedbackEvaluator

            print("\n" + "=" * 60)
            print("[质量评估]")
            print("=" * 60)

            # 1. 质量检查
            checker = create_checker("general")
            report = checker.check(result)

            print(f"检查类型：{report.checklist_type}")
            print(f"通过项：{report.passed}/{report.total}")
            print(f"通过率：{report.pass_rate:.1%}")

            if report.failed_items:
                print(f"\n未通过检查项:")
                for item in report.failed_items:
                    print(f"  ❌ {item}")

            if report.suggestions:
                print(f"\n改进建议:")
                for sug in report.suggestions:
                    print(f"  💡 {sug}")

            # 2. 输出质量评级（严格标准）
            # 有实质性内容缺失的，全部评为"需要改进"
            print("\n质量评级:", end=" ")

            # 检查是否有实质性内容缺失
            has_substance_issues = any(
                "具体" in item or "示例" in item or "步骤" in item or "数据" in item
                for item in report.failed_items
            )

            # 检查是否需要实时数据但未能获取
            needs_realtime = any(
                kw in user_input.lower()
                for kw in ["当前", "今日", "现在", "最新", "实时", "热点", "行情", "股市", "股票"]
            )

            # 检查是否输出缺乏具体内容
            lacks_content = len(result) < 300 or "无法获取" in result or "网络连接" in result

            # 信息查询类任务：检查是否包含具体数据（而非步骤/示例）
            is_info_query = any(
                kw in user_input.lower()
                for kw in ["什么", "哪些", "情况", "状态", "信息", "数据", "热点", "行情"]
            )

            # 对于信息查询类任务，实质性内容指的是具体数据而非步骤
            if is_info_query:
                # 只关心数据/信息相关的缺失，不关心步骤/示例
                has_substance_issues = any(
                    "数据" in item or "信息" in item
                    for item in report.failed_items
                )
            else:
                has_substance_issues = any(
                    "具体" in item or "示例" in item or "步骤" in item or "数据" in item
                    for item in report.failed_items
                )

            if needs_realtime and lacks_content:
                print("⭐⭐ 需要改进（未获取到实时数据）")
                print("\n⚠️  警示：该问题需要实时数据，但网络获取失败")
                print("建议：1. 检查网络连接 2. 配置搜索 API 3. 使用代理")
            elif report.pass_rate >= 0.9 and not has_substance_issues:
                print("⭐⭐⭐⭐⭐ 优秀")
            elif report.pass_rate >= 0.85 and not has_substance_issues:
                print("⭐⭐⭐⭐ 良好")
            elif report.pass_rate >= 0.7:
                print("⭐⭐⭐ 合格（但有实质性内容缺失）")
            else:
                print("⭐⭐ 需要改进")

            if has_substance_issues and not (needs_realtime and lacks_content):
                print("\n⚠️  警示：回答缺乏实质性内容，建议重新获取真实数据")

            print("=" * 60)

        except Exception as e:
            print(f"\n[质量评估] 评估失败：{e}")

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
        isolate_by_instance: bool = False,
        session_id: Optional[str] = None,
        create_session: bool = True,
        interactive: bool = False
    ) -> TaskHandle:
        """
        异步执行任务（后台执行，立即返回）

        Args:
            user_input: 用户输入
            verbose: 是否打印详细过程
            output_dir: 输出目录
            isolate_by_instance: 是否按实例隔离
            session_id: 任务 session ID（用于继续对话）
            create_session: 是否创建新 session
            interactive: 是否为交互式任务（需要用户确认）

        Returns:
            TaskHandle 对象，用于跟踪任务状态
        """
        from simple_agent.core.task_handle import TaskStatusEnum

        # 确保队列已启动
        await self._ensure_queue_started()

        # 生成任务 ID
        self._task_counter += 1
        task_id = f"task_{self._task_counter}_{int(time.time() * 1000)}"

        # 如果提供了 session_id，使用它作为 task_id
        if session_id:
            task_id = session_id

        # 如果是交互式任务，先创建 session，设置为 CONFIRMING 状态
        if interactive:
            self.create_session(task_id, user_input)

            # 创建 TaskHandle 并设置为 CONFIRMING 状态
            handle = await self.task_queue.submit(
                task_id=task_id,
                input_text=user_input,
                coro=None,  # 暂时不执行
                interactive=True
            )

            # 设置状态为等待确认
            await handle.update_status(
                TaskStatusEnum.CONFIRMING,
                progress="等待用户确认"
            )

            if verbose:
                print(f"\n{'='*60}")
                print("[交互式后台任务] 任务已创建，等待用户确认")
                print(f"任务 ID: {task_id}")
                print(f"任务描述: {user_input[:60]}{'...' if len(user_input) > 60 else ''}")
                print(f"{'='*60}")
                print("使用以下命令确认并执行：")
                print(f"  /session continue {task_id} 确认执行")
                print("或取消任务：")
                print(f"  /cancel {task_id}")
            return handle

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
                    isolate_by_instance=isolate_by_instance,
                    session_id=session_id,
                    create_session=create_session,
                    interactive=False  # 后台任务不进行交互确认
                )

            return await loop.run_in_executor(None, execute_task)

        # 提交到任务队列
        handle = await self.task_queue.submit(
            task_id=task_id,
            input_text=user_input,
            coro=task_coro(),
            interactive=False
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

