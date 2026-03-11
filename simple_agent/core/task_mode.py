"""
任务执行模式配置

支持两种执行模式：
1. 完全自动 (AUTO) - 所有操作由 Agent 自动完成，无需用户确认
2. Step-by-step (REVIEW) - 关键节点需要用户评审确认

用户评审点：
- 任务开始（可选）
- 危险命令执行前
- 重要文件修改
- 任务完成汇总
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
import threading


class ExecutionMode(Enum):
    """执行模式"""
    AUTO = "auto"          # 完全自动模式
    REVIEW = "review"      # 用户评审模式（step-by-step）


class ReviewPoint(Enum):
    """用户评审点类型"""
    TASK_START = "task_start"              # 任务开始
    DANGEROUS_COMMAND = "dangerous_command" # 危险命令
    FILE_MODIFIED = "file_modified"        # 重要文件修改
    TASK_STAGE_COMPLETE = "task_stage_complete" # 阶段完成
    TASK_FINAL = "task_final"              # 任务完成


@dataclass
class ReviewRequest:
    """评审请求"""
    point: ReviewPoint
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "point": self.point.value,
            "message": self.message,
            "details": self.details,
            "context": self.context,
        }


@dataclass
class ReviewResponse:
    """评审响应"""
    approved: bool
    feedback: Optional[str] = None
    modified_request: Optional[Dict] = None  # 修改后的请求（如调整参数）


class ReviewCallback:
    """评审回调接口"""

    def __init__(self):
        self._callbacks: Dict[ReviewPoint, List[Callable]] = {}
        self._global_callback: Optional[Callable] = None

    def register(self, point: ReviewPoint, callback: Callable[[ReviewRequest], ReviewResponse]):
        """注册评审回调"""
        if point not in self._callbacks:
            self._callbacks[point] = []
        self._callbacks[point].append(callback)

    def set_global(self, callback: Callable[[ReviewRequest], ReviewResponse]):
        """设置全局回调（处理所有未注册的评审点）"""
        self._global_callback = callback

    def request(self, request: ReviewRequest) -> ReviewResponse:
        """发起评审请求"""
        # 优先调用特定评审点的回调
        callbacks = self._callbacks.get(request.point, [])

        # 如果没有特定回调，使用全局回调
        if not callbacks and self._global_callback:
            callbacks = [self._global_callback]

        # 执行所有回调（第一个回调决定结果）
        for callback in callbacks:
            response = callback(request)
            if response:
                return response

        # 默认拒绝（安全优先）
        return ReviewResponse(approved=False, feedback="未配置评审回调")


# 线程本地存储的执行上下文
_task_mode_context = threading.local()


def set_execution_mode(mode: ExecutionMode):
    """设置执行模式"""
    _task_mode_context.mode = mode


def get_execution_mode() -> ExecutionMode:
    """获取执行模式"""
    return getattr(_task_mode_context, 'mode', ExecutionMode.AUTO)


def set_review_callback(callback: ReviewCallback):
    """设置评审回调"""
    _task_mode_context.review_callback = callback


def get_review_callback() -> Optional[ReviewCallback]:
    """获取评审回调"""
    return getattr(_task_mode_context, 'review_callback', None)


def request_review(point: ReviewPoint, message: str,
                   details: Optional[Dict] = None,
                   context: Optional[Dict] = None) -> ReviewResponse:
    """请求用户评审

    Returns:
        ReviewResponse - 包含批准/拒绝结果
    """
    mode = get_execution_mode()

    # 自动模式下，直接批准
    if mode == ExecutionMode.AUTO:
        return ReviewResponse(approved=True)

    # REVIEW 模式下，请求评审
    callback = get_review_callback()
    if not callback:
        # 如果没有回调，默认拒绝
        return ReviewResponse(approved=False, feedback="未配置评审回调")

    request = ReviewRequest(
        point=point,
        message=message,
        details=details or {},
        context=context or {},
    )

    return callback.request(request)


# ============================================================================
# 内置评审策略
# ============================================================================

class ApproveAllCallback(ReviewCallback):
    """批准所有请求（完全自动模式的默认策略）"""

    def request(self, request: ReviewRequest) -> ReviewResponse:
        return ReviewResponse(approved=True)


class RejectAllCallback(ReviewCallback):
    """拒绝所有请求（安全优先）"""

    def request(self, request: ReviewRequest) -> ReviewResponse:
        return ReviewResponse(approved=False, feedback="安全策略：默认拒绝")


class TerminalCallback(ReviewCallback):
    """终端交互回调（step-by-step 模式）"""

    def request(self, request: ReviewRequest) -> ReviewResponse:
        import sys

        # 格式化请求
        print("\n" + "=" * 60)
        print(f"[评审请求] {request.point.value}")
        print("=" * 60)
        print(f"说明: {request.message}")

        if request.details:
            print("\n详细信息:")
            for key, value in request.details.items():
                print(f"  {key}: {value}")

        if request.context:
            print("\n上下文:")
            for key, value in request.context.items():
                print(f"  {key}: {value}")

        print("\n" + "-" * 60)

        # 等待用户输入
        while True:
            try:
                response = input("是否批准？(y/n/skip): ").strip().lower()

                if response in ('y', 'yes', '是'):
                    return ReviewResponse(approved=True)
                elif response in ('n', 'no', '否'):
                    return ReviewResponse(approved=False)
                elif response in ('s', 'skip', '跳过'):
                    # 返回批准但标记为跳过
                    return ReviewResponse(
                        approved=True,
                        feedback="用户选择跳过",
                        modified_request={"skip": True}
                    )
                else:
                    print("请输入 y/n/skip")
            except EOFError:
                # 非交互模式，默认拒绝
                return ReviewResponse(approved=False, feedback="非交互模式，默认拒绝")


def create_terminal_review_callback() -> ReviewCallback:
    """创建终端交互回调"""
    callback = TerminalCallback()

    # 注册通用处理器
    callback.set_global(callback.request)

    return callback


def create_auto_review_callback() -> ReviewCallback:
    """创建自动批准回调"""
    return ApproveAllCallback()


# ============================================================================
# 工具执行集成
# ============================================================================

def should_confirm_command(command: str) -> bool:
    """判断命令是否需要确认（基于安全级别）"""
    # 这里可以集成 script_security 的审计
    from simple_agent.core.script_security import quick_audit, SecurityLevel

    try:
        result = quick_audit(command)
        return result.security_level in [SecurityLevel.MEDIUM_RISK, SecurityLevel.HIGH_RISK]
    except Exception:
        # 如果审计失败，默认需要确认（安全优先）
        return True


def get_review_point_for_command(command: str) -> ReviewPoint:
    """获取命令对应的评审点"""
    # 根据命令特征判断评审点
    if "rm -rf" in command or "rm -r" in command:
        return ReviewPoint.DANGEROUS_COMMAND
    elif "chmod" in command or "chown" in command:
        return ReviewPoint.DANGEROUS_COMMAND
    elif "sudo" in command:
        return ReviewPoint.DANGEROUS_COMMAND
    elif command.startswith("git reset") or "git clean" in command:
        return ReviewPoint.DANGEROUS_COMMAND
    else:
        return ReviewPoint.DANGEROUS_COMMAND  # 默认使用危险命令评审点


def check_and_request_confirmation(
    command: str,
    point: Optional[ReviewPoint] = None,
    message: Optional[str] = None,
    details: Optional[Dict] = None,
    mode: Optional[str] = None  # "auto" or "review"
) -> tuple[bool, Optional[str]]:
    """
    检查是否需要确认，并发起评审请求

    Args:
        command: 要执行的命令
        point: 评审点
        message: 评审消息
        details: 详细信息
        mode: 执行模式 ("auto" 或 "review")，覆盖全局设置

    Returns:
        (should_proceed, error_message)
    """
    # 如果指定了 mode 参数，使用它
    if mode == "auto":
        return True, None

    # 检查执行模式
    current_mode = get_execution_mode()
    if current_mode == ExecutionMode.AUTO:
        return True, None

    # 确定评审点和消息
    review_point = point or get_review_point_for_command(command)
    review_message = message or f"即将执行命令: {command[:100]}..."

    # 请求评审
    response = request_review(
        point=review_point,
        message=review_message,
        details=details or {"command": command[:500]},
        context={"mode": mode.value},
    )

    if response.approved:
        return True, None
    else:
        error = response.feedback or f"操作被用户拒绝: {command}"
        return False, error


# ============================================================================
# 上下文管理器
# ============================================================================

class ExecutionModeContext:
    """执行模式上下文管理器"""

    def __init__(self, mode: ExecutionMode, review_callback: Optional[ReviewCallback] = None):
        self.mode = mode
        self.review_callback = review_callback
        self._old_mode: Optional[ExecutionMode] = None
        self._old_callback: Optional[ReviewCallback] = None

    def __enter__(self):
        # 保存旧值
        self._old_mode = get_execution_mode()
        self._old_callback = get_review_callback()

        # 设置新模式
        set_execution_mode(self.mode)
        if self.review_callback:
            set_review_callback(self.review_callback)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复旧值
        if self._old_mode is not None:
            set_execution_mode(self._old_mode)
        if self._old_callback is not None:
            set_review_callback(self._old_callback)
        elif hasattr(_task_mode_context, 'review_callback'):
            delattr(_task_mode_context, 'review_callback')


def with_mode(mode: ExecutionMode, callback: ReviewCallback = None):
    """装饰器：为函数设置执行模式"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with ExecutionModeContext(mode, callback):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# Agent 集成
# ============================================================================

def agent_run_with_mode(
    agent,
    user_input: str,
    mode: ExecutionMode = ExecutionMode.AUTO,
    review_callback: Optional[ReviewCallback] = None,
    **kwargs
) -> str:
    """
    使用指定模式运行 Agent

    Args:
        agent: Agent 实例
        user_input: 用户输入
        mode: 执行模式
        review_callback: 评审回调
        **kwargs: 其他参数传递给 agent.run()

    Returns:
        执行结果
    """
    callback = review_callback

    # 根据模式设置默认回调
    if mode == ExecutionMode.AUTO and callback is None:
        callback = create_auto_review_callback()
    elif mode == ExecutionMode.REVIEW and callback is None:
        callback = create_terminal_review_callback()

    with ExecutionModeContext(mode, callback):
        return agent.run(user_input, **kwargs)
