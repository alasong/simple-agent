"""
Self-Healing Coordinator - 自愈协调器

支持 Agent 执行异常的：
1. 异常定位和诊断
2. 自动重新生成失败的 Agent
3. 继续执行未完成的任务

架构:
┌─────────────────────────────────────────────────────────┐
│           SelfHealingCoordinator                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │  ExceptionDiagnoser                               │  │
│  │  - 异常类型识别                                   │  │
│  │  - 根本原因分析                                   │  │
│  │  - 影响范围评估                                   │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  AgentRegenerator                                 │  │
│  │  - 重新生成失败的 Agent                           │  │
│  │  - 调整配置参数                                   │  │
│  │  - 切换备用 Agent                                 │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  TaskResumer                                      │  │
│  │  - 保存执行断点                                   │  │
│  │  - 恢复未完成的任务                               │  │
│  │  - 合并多次执行结果                               │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
"""

import json
import time
import traceback
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ExceptionType(Enum):
    """异常类型"""
    LLM_ERROR = "llm_error"              # LLM 调用失败
    TOOL_ERROR = "tool_error"            # 工具执行失败
    MEMORY_ERROR = "memory_error"        # 记忆管理失败
    NETWORK_ERROR = "network_error"      # 网络错误
    TIMEOUT_ERROR = "timeout_error"      # 超时错误
    AGENT_CRASH = "agent_crash"          # Agent 崩溃
    UNKNOWN = "unknown"                  # 未知错误


class RecoveryStrategy(Enum):
    """恢复策略"""
    RETRY = "retry"                      # 重试
    REGENERATE_AGENT = "regenerate"      # 重新生成 Agent
    SWITCH_AGENT = "switch"              # 切换 Agent
    DECOMPOSE_TASK = "decompose"         # 分解任务
    SKIP_STEP = "skip"                   # 跳过当前步骤
    ROLLBACK = "rollback"                # 回滚到上一个稳定状态


@dataclass
class ExceptionReport:
    """异常报告"""
    exception_type: ExceptionType
    error_message: str
    stack_trace: str
    agent_name: str
    task_description: str
    timestamp: str
    context: Dict[str, Any] = field(default_factory=dict)
    recovery_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "exception_type": self.exception_type.value,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "agent_name": self.agent_name,
            "task_description": self.task_description,
            "timestamp": self.timestamp,
            "context": self.context,
            "recovery_suggestions": self.recovery_suggestions
        }


@dataclass
class RecoveryResult:
    """恢复结果"""
    success: bool
    strategy: RecoveryStrategy
    new_agent: Optional[Any] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
    attempts: int = 0
    execution_time: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "strategy": self.strategy.value,
            "new_agent": self.new_agent.name if self.new_agent else None,
            "result": self.result,
            "error_message": self.error_message,
            "attempts": self.attempts,
            "execution_time": round(self.execution_time, 2)
        }


@dataclass
class ExecutionCheckpoint:
    """执行断点"""
    task_id: str
    agent_name: str
    iteration: int
    memory_messages: List[Dict]
    pending_actions: List[Dict]
    completed_actions: List[Dict]
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "iteration": self.iteration,
            "memory_messages": self.memory_messages,
            "pending_actions": self.pending_actions,
            "completed_actions": self.completed_actions,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionCheckpoint":
        return cls(
            task_id=data["task_id"],
            agent_name=data["agent_name"],
            iteration=data["iteration"],
            memory_messages=data["memory_messages"],
            pending_actions=data["pending_actions"],
            completed_actions=data["completed_actions"],
            timestamp=data["timestamp"]
        )


class ExceptionDiagnoser:
    """异常诊断器"""

    # 异常类型映射
    EXCEPTION_MAPPINGS = {
        "ConnectionError": ExceptionType.NETWORK_ERROR,
        "TimeoutError": ExceptionType.TIMEOUT_ERROR,
        "TimeoutException": ExceptionType.TIMEOUT_ERROR,
        "requests.exceptions.RequestException": ExceptionType.NETWORK_ERROR,
        "requests.exceptions.Timeout": ExceptionType.TIMEOUT_ERROR,
        "openai.APIError": ExceptionType.LLM_ERROR,
        "openai.APIConnectionError": ExceptionType.NETWORK_ERROR,
    }

    def diagnose(self, exception: Exception, context: Dict[str, Any]) -> ExceptionReport:
        """诊断异常"""
        # 识别异常类型
        exception_type = self._identify_exception_type(exception)

        # 获取堆栈跟踪
        stack_trace = traceback.format_exc()

        # 分析根本原因
        root_cause = self._analyze_root_cause(exception_type, exception, context)

        # 生成恢复建议
        recovery_suggestions = self._generate_recovery_suggestions(exception_type, root_cause, context)

        return ExceptionReport(
            exception_type=exception_type,
            error_message=str(exception),
            stack_trace=stack_trace,
            agent_name=context.get("agent_name", "Unknown"),
            task_description=context.get("task_description", ""),
            timestamp=datetime.now().isoformat(),
            context=context,
            recovery_suggestions=recovery_suggestions
        )

    def _identify_exception_type(self, exception: Exception) -> ExceptionType:
        """识别异常类型"""
        exception_class = exception.__class__.__name__
        module = exception.__class__.__module__

        # 检查映射
        for key, exc_type in self.EXCEPTION_MAPPINGS.items():
            if key in exception_class or f"{module}.{exception_class}" == key:
                return exc_type

        # 默认判断
        if "network" in str(exception).lower() or "connection" in str(exception).lower():
            return ExceptionType.NETWORK_ERROR
        elif "timeout" in str(exception).lower() or "timed out" in str(exception).lower():
            return ExceptionType.TIMEOUT_ERROR
        elif "llm" in str(exception).lower() or "openai" in str(exception).lower():
            return ExceptionType.LLM_ERROR
        elif "tool" in str(exception).lower():
            return ExceptionType.TOOL_ERROR

        return ExceptionType.UNKNOWN

    def _analyze_root_cause(
        self,
        exception_type: ExceptionType,
        exception: Exception,
        context: Dict[str, Any]
    ) -> str:
        """分析根本原因"""
        if exception_type == ExceptionType.NETWORK_ERROR:
            return "网络连接问题，可能是 API 服务不可用或防火墙阻止"
        elif exception_type == ExceptionType.TIMEOUT_ERROR:
            return "请求超时，可能是服务负载过高或网络延迟"
        elif exception_type == ExceptionType.LLM_ERROR:
            return "LLM API 调用失败，可能是配额不足或服务异常"
        elif exception_type == ExceptionType.TOOL_ERROR:
            tool_name = context.get("failed_tool", "Unknown")
            return f"工具 {tool_name} 执行失败，可能是参数错误或环境不满足"
        elif exception_type == ExceptionType.AGENT_CRASH:
            return "Agent 进程崩溃，可能是内存溢出或严重错误"
        return f"未知错误：{str(exception)}"

    def _generate_recovery_suggestions(
        self,
        exception_type: ExceptionType,
        root_cause: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """生成恢复建议"""
        suggestions = []

        if exception_type == ExceptionType.NETWORK_ERROR:
            suggestions.extend([
                "检查网络连接是否正常",
                "尝试切换到备用 API 端点",
                "使用本地缓存的数据"
            ])
        elif exception_type == ExceptionType.TIMEOUT_ERROR:
            suggestions.extend([
                "增加超时时间",
                "减小任务复杂度",
                "分批处理大数据"
            ])
        elif exception_type == ExceptionType.LLM_ERROR:
            suggestions.extend([
                "检查 API 配额是否充足",
                "切换到备用 LLM 服务",
                "简化提示词减少 token 消耗"
            ])
        elif exception_type == ExceptionType.TOOL_ERROR:
            suggestions.extend([
                "检查工具参数是否正确",
                "确认工具依赖的环境",
                "尝试替代工具完成相同功能"
            ])
        elif exception_type == ExceptionType.AGENT_CRASH:
            suggestions.extend([
                "重新生成 Agent 实例",
                "清理内存释放资源",
                "分解任务为更小的子任务"
            ])

        return suggestions


class AgentRegenerator:
    """Agent 重新生成器"""

    def __init__(self):
        self._agent_history: Dict[str, List[Dict]] = {}  # Agent 历史配置
        self._failure_count: Dict[str, int] = {}  # 失败计数

    def regenerate(
        self,
        failed_agent: Any,
        exception_report: ExceptionReport
    ) -> Any:
        """
        重新生成 Agent

        Args:
            failed_agent: 失败的 Agent
            exception_report: 异常报告

        Returns:
            新生成的 Agent
        """
        agent_name = failed_agent.name
        agent_key = f"{agent_name}_{failed_agent.instance_id or 'default'}"

        # 记录失败历史
        if agent_key not in self._failure_count:
            self._failure_count[agent_key] = 0
        self._failure_count[agent_key] += 1

        failure_count = self._failure_count[agent_key]

        # 根据失败次数选择策略
        if failure_count == 1:
            # 第一次失败：保持配置重试
            return self._clone_agent(failed_agent)
        elif failure_count == 2:
            # 第二次失败：调整配置（增加迭代次数）
            return self._regenerate_with_adjusted_config(failed_agent)
        else:
            # 多次失败：切换到备用 Agent
            return self._switch_to_backup_agent(failed_agent)

    def _clone_agent(self, original: Any) -> Any:
        """克隆 Agent"""
        return original.clone()

    def _regenerate_with_adjusted_config(self, original: Any) -> Any:
        """调整配置后重新生成"""
        from core.agent import Agent

        # 增加迭代次数
        new_max_iterations = min(original.max_iterations + 5, 30)

        new_agent = Agent(
            llm=original.llm,
            system_prompt=original.system_prompt,
            name=original.name,
            version=original.version,
            description=original.description,
            max_iterations=new_max_iterations,
            instance_id=f"{original.instance_id}_v2" if original.instance_id else "v2"
        )

        # 复制工具
        for tool in original.tool_registry.get_all_tools():
            new_agent.tool_registry.register(tool)

        return new_agent

    def _switch_to_backup_agent(self, failed_agent: Any) -> Any:
        """切换到备用 Agent"""
        from builtin_agents import get_agent

        # 尝试获取同类型的备用 Agent
        backup_names = {
            "planner": ["developer", "architect"],
            "developer": ["planner", "architect"],
            "architect": ["developer", "planner"],
            "reviewer": ["developer", "tester"],
            "tester": ["developer", "reviewer"],
        }

        agent_name = failed_agent.name.lower()
        backup_list = backup_names.get(agent_name, [])

        for backup_name in backup_list:
            try:
                backup = get_agent(backup_name)
                print(f"[自愈] 切换到备用 Agent: {backup_name}")
                return backup
            except (ImportError, ValueError):
                continue

        # 没有可用备用，返回新的同类型 Agent
        print(f"[自愈] 重新创建 {agent_name} Agent")
        return failed_agent.clone()


class TaskResumer:
    """任务恢复器"""

    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        self._checkpoints: Dict[str, ExecutionCheckpoint] = {}

    def save_checkpoint(
        self,
        task_id: str,
        agent: Any,
        iteration: int,
        memory_messages: List[Dict],
        pending_actions: List[Dict],
        completed_actions: List[Dict]
    ):
        """保存执行断点"""
        checkpoint = ExecutionCheckpoint(
            task_id=task_id,
            agent_name=agent.name,
            iteration=iteration,
            memory_messages=memory_messages,
            pending_actions=pending_actions,
            completed_actions=completed_actions,
            timestamp=datetime.now().isoformat()
        )

        self._checkpoints[task_id] = checkpoint

        # 持久化到文件
        try:
            import os
            os.makedirs(self.checkpoint_dir, exist_ok=True)
            checkpoint_path = os.path.join(self.checkpoint_dir, f"{task_id}.json")
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[TaskResumer] 保存断点失败：{e}")

    def load_checkpoint(self, task_id: str) -> Optional[ExecutionCheckpoint]:
        """加载执行断点"""
        # 先检查内存
        if task_id in self._checkpoints:
            return self._checkpoints[task_id]

        # 再检查文件
        try:
            import os
            checkpoint_path = os.path.join(self.checkpoint_dir, f"{task_id}.json")
            if os.path.exists(checkpoint_path):
                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                checkpoint = ExecutionCheckpoint.from_dict(data)
                self._checkpoints[task_id] = checkpoint
                return checkpoint
        except Exception as e:
            print(f"[TaskResumer] 加载断点失败：{e}")

        return None

    def clear_checkpoint(self, task_id: str):
        """清除执行断点"""
        if task_id in self._checkpoints:
            del self._checkpoints[task_id]

        try:
            import os
            checkpoint_path = os.path.join(self.checkpoint_dir, f"{task_id}.json")
            if os.path.exists(checkpoint_path):
                os.remove(checkpoint_path)
        except Exception:
            pass

    def restore_and_resume(
        self,
        checkpoint: ExecutionCheckpoint,
        new_agent: Any
    ) -> Dict[str, Any]:
        """恢复断点并准备继续执行"""
        # 恢复记忆
        for msg in checkpoint.memory_messages:
            if msg.get("role") != "system":
                new_agent.memory.messages.append(msg)

        return {
            "task_id": checkpoint.task_id,
            "iteration": checkpoint.iteration,
            "pending_actions": checkpoint.pending_actions,
            "completed_actions": checkpoint.completed_actions
        }


class SelfHealingCoordinator:
    """自愈协调器"""

    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        self.diagnoser = ExceptionDiagnoser()
        self.regenerator = AgentRegenerator()
        self.resumer = TaskResumer(checkpoint_dir=checkpoint_dir)
        self._max_recovery_attempts = 3

    def handle_exception(
        self,
        agent: Any,
        exception: Exception,
        task_description: str,
        context: Optional[Dict] = None
    ) -> RecoveryResult:
        """
        处理异常，执行自愈流程

        Args:
            agent: 失败的 Agent
            exception: 异常对象
            task_description: 任务描述
            context: 额外上下文

        Returns:
            恢复结果
        """
        start_time = time.time()

        # 1. 诊断异常
        ctx = context or {}
        ctx["agent_name"] = agent.name
        ctx["task_description"] = task_description
        report = self.diagnoser.diagnose(exception, ctx)

        print(f"\n[自愈协调器] 异常诊断完成:")
        print(f"  类型：{report.exception_type.value}")
        print(f"  原因：{self._truncate(report.error_message, 100)}")

        # 2. 根据异常类型选择恢复策略
        strategy = self._select_recovery_strategy(report)

        # 3. 执行恢复
        result = self._execute_recovery(agent, report, strategy, task_description)
        result.execution_time = time.time() - start_time

        return result

    def _select_recovery_strategy(self, report: ExceptionReport) -> RecoveryStrategy:
        """选择恢复策略"""
        exc_type = report.exception_type

        if exc_type == ExceptionType.TIMEOUT_ERROR:
            return RecoveryStrategy.RETRY
        elif exc_type == ExceptionType.NETWORK_ERROR:
            return RecoveryStrategy.RETRY
        elif exc_type == ExceptionType.LLM_ERROR:
            return RecoveryStrategy.SWITCH_AGENT
        elif exc_type == ExceptionType.AGENT_CRASH:
            return RecoveryStrategy.REGENERATE_AGENT
        elif exc_type == ExceptionType.TOOL_ERROR:
            # 如果是持久性错误，跳过该步骤
            if "persistence" in report.error_message.lower() or "持久性" in report.error_message.lower():
                return RecoveryStrategy.SKIP_STEP
            return RecoveryStrategy.RETRY
        else:
            return RecoveryStrategy.REGENERATE_AGENT

    def _execute_recovery(
        self,
        agent: Any,
        report: ExceptionReport,
        strategy: RecoveryStrategy,
        task_description: str
    ) -> RecoveryResult:
        """执行恢复"""
        attempts = 0

        if strategy == RecoveryStrategy.RETRY:
            # 重试：直接使用原 Agent
            print(f"[自愈] 策略：重试")
            return RecoveryResult(
                success=True,
                strategy=strategy,
                new_agent=agent,
                attempts=1
            )

        elif strategy == RecoveryStrategy.REGENERATE_AGENT:
            # 重新生成 Agent
            print(f"[自愈] 策略：重新生成 Agent")
            new_agent = self.regenerator.regenerate(agent, report)
            return RecoveryResult(
                success=True,
                strategy=strategy,
                new_agent=new_agent,
                attempts=1
            )

        elif strategy == RecoveryStrategy.SWITCH_AGENT:
            # 切换备用 Agent
            print(f"[自愈] 策略：切换备用 Agent")
            backup_agent = self.regenerator._switch_to_backup_agent(agent)
            return RecoveryResult(
                success=True,
                strategy=strategy,
                new_agent=backup_agent,
                attempts=1
            )

        elif strategy == RecoveryStrategy.DECOMPOSE_TASK:
            # 分解任务（需要外部处理）
            print(f"[自愈] 策略：分解任务")
            return RecoveryResult(
                success=False,  # 需要外部处理
                strategy=strategy,
                error_message="任务过于复杂，需要分解为子任务",
                attempts=1
            )

        elif strategy == RecoveryStrategy.SKIP_STEP:
            # 跳过当前步骤
            print(f"[自愈] 策略：跳过当前步骤")
            return RecoveryResult(
                success=True,
                strategy=strategy,
                new_agent=agent,
                attempts=1
            )

        else:
            return RecoveryResult(
                success=False,
                strategy=strategy,
                error_message="无法执行恢复",
                attempts=1
            )

    def resume_from_checkpoint(
        self,
        task_id: str,
        new_agent: Any
    ) -> Optional[Dict[str, Any]]:
        """从断点恢复任务"""
        checkpoint = self.resumer.load_checkpoint(task_id)
        if checkpoint:
            print(f"[自愈] 从断点恢复：{task_id} (迭代 {checkpoint.iteration})")
            return self.resumer.restore_and_resume(checkpoint, new_agent)
        return None

    def save_checkpoint(
        self,
        task_id: str,
        agent: Any,
        iteration: int,
        memory_messages: List[Dict],
        pending_actions: List[Dict] = None,
        completed_actions: List[Dict] = None
    ):
        """保存执行断点"""
        self.resumer.save_checkpoint(
            task_id=task_id,
            agent=agent,
            iteration=iteration,
            memory_messages=memory_messages,
            pending_actions=pending_actions or [],
            completed_actions=completed_actions or []
        )

    def _truncate(self, text: str, max_len: int) -> str:
        """截断文本"""
        if len(text) > max_len:
            return text[:max_len] + "..."
        return text


# 全局协调器实例
_coordinator: Optional[SelfHealingCoordinator] = None


def get_coordinator(checkpoint_dir: str = "./checkpoints") -> SelfHealingCoordinator:
    """获取自愈协调器实例"""
    global _coordinator
    if _coordinator is None:
        _coordinator = SelfHealingCoordinator(checkpoint_dir=checkpoint_dir)
    return _coordinator
