"""
API Models - Pydantic 数据模型

定义 API 请求/响应的数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRunRequest(BaseModel):
    """Agent 运行请求"""
    agent_name: str = Field(..., description="Agent 名称，如 'developer', 'tester'")
    input: str = Field(..., description="输入内容/任务描述")
    config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="配置选项，如 {'timeout': 300, 'debug': True}"
    )
    instance_id: Optional[str] = Field(
        None,
        description="实例 ID，用于区分同一 Agent 的多个副本"
    )


class AgentRunResponse(BaseModel):
    """Agent 运行响应"""
    task_id: str = Field(..., description="任务 ID")
    status: TaskStatus = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")
    created_at: datetime = Field(default_factory=datetime.now)


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str = Field(..., description="任务 ID")
    status: TaskStatus = Field(..., description="任务状态")
    output: Optional[str] = Field(None, description="输出内容")
    files: Optional[List[str]] = Field(None, description="生成的文件列表")
    error: Optional[str] = Field(None, description="错误信息（如果失败）")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    duration: Optional[float] = Field(None, description="执行时长（秒）")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class WorkflowExecuteRequest(BaseModel):
    """Workflow 执行请求"""
    workflow_name: Optional[str] = Field(
        None,
        description="Workflow 名称（用于预定义 workflow）"
    )
    steps: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Workflow 步骤定义（动态创建时使用）"
    )
    inputs: Dict[str, Any] = Field(
        ...,
        description="输入数据"
    )
    config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="配置选项"
    )


class WorkflowExecuteResponse(BaseModel):
    """Workflow 执行响应"""
    task_id: str = Field(..., description="任务 ID")
    status: TaskStatus = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")
    created_at: datetime = Field(default_factory=datetime.now)


class TaskProgress(BaseModel):
    """任务进度（用于 WebSocket 推送）"""
    task_id: str = Field(..., description="任务 ID")
    status: TaskStatus = Field(..., description="当前状态")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="进度百分比 0-1")
    message: Optional[str] = Field(None, description="进度消息")
    step: Optional[str] = Field(None, description="当前步骤名称")
    timestamp: datetime = Field(default_factory=datetime.now)


class MetricsResponse(BaseModel):
    """系统指标响应"""
    total_tasks: int = Field(..., description="总任务数")
    completed_tasks: int = Field(..., description="已完成任务数")
    failed_tasks: int = Field(..., description="失败任务数")
    success_rate: float = Field(..., description="成功率 0-1")
    avg_duration: float = Field(..., description="平均执行时长（秒）")
    total_tokens: int = Field(..., description="总 token 消耗")
    active_agents: int = Field(..., description="活跃 Agent 数量")
    uptime: float = Field(..., description="运行时长（秒）")


class AgentInfo(BaseModel):
    """Agent 信息"""
    name: str = Field(..., description="Agent 名称")
    description: str = Field(..., description="Agent 描述")
    version: str = Field(..., description="版本号")
    tools: List[str] = Field(default_factory=list, description="工具列表")
    skills: List[str] = Field(default_factory=list, description="技能标签")


class AgentListResponse(BaseModel):
    """Agent 列表响应"""
    agents: List[AgentInfo] = Field(..., description="Agent 列表")
    total: int = Field(..., description="总数")


class WorkflowInfo(BaseModel):
    """Workflow 信息"""
    name: str = Field(..., description="Workflow 名称")
    description: str = Field(..., description="Workflow 描述")
    steps: List[str] = Field(default_factory=list, description="步骤名称列表")


class WorkflowListResponse(BaseModel):
    """Workflow 列表响应"""
    workflows: List[WorkflowInfo] = Field(..., description="Workflow 列表")
    total: int = Field(..., description="总数")


class APIError(BaseModel):
    """API 错误响应"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细错误信息")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="健康状态")
    version: str = Field(..., description="服务版本")
    uptime: float = Field(..., description="运行时长（秒）")
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# 定时任务相关模型
# ============================================================================

class ScheduleType(str, Enum):
    """调度类型"""
    ONCE = "once"
    INTERVAL = "interval"
    CRON = "cron"


class CreateScheduledTaskRequest(BaseModel):
    """创建定时任务请求"""
    name: str = Field(..., description="任务名称")
    schedule_type: ScheduleType = Field(..., description="调度类型")
    agent_name: str = Field(..., description="Agent 名称")
    input: str = Field(..., description="任务输入")

    # 调度配置（根据类型选择）
    run_at: Optional[str] = Field(None, description="一次性执行时间 (ISO 格式)")
    interval_seconds: Optional[int] = Field(None, ge=1, description="间隔秒数")
    cron_expression: Optional[str] = Field(None, description="Cron 表达式")

    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="配置选项")
    description: Optional[str] = Field(None, description="任务描述")


class ScheduledTaskInfo(BaseModel):
    """定时任务信息"""
    task_id: str = Field(..., description="任务 ID")
    name: str = Field(..., description="任务名称")
    schedule_type: ScheduleType = Field(..., description="调度类型")
    agent_name: str = Field(..., description="Agent 名称")
    enabled: bool = Field(..., description="是否启用")
    last_run: Optional[str] = Field(None, description="最后执行时间")
    next_run: Optional[str] = Field(None, description="下次执行时间")
    total_runs: int = Field(..., description="执行次数")
    failed_runs: int = Field(..., description="失败次数")
    cron_expression: Optional[str] = Field(None, description="Cron 表达式")
    interval_seconds: Optional[int] = Field(None, description="间隔秒数")
    created_at: str = Field(..., description="创建时间")


class ScheduledTaskListResponse(BaseModel):
    """定时任务列表响应"""
    tasks: List[ScheduledTaskInfo] = Field(..., description="任务列表")
    total: int = Field(..., description="总数")
