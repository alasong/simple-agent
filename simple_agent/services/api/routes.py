"""
API Routes - API 路由定义

定义所有 HTTP API 端点
"""

import asyncio
import threading
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from .models import (
    TaskStatus,
    AgentRunRequest,
    AgentRunResponse,
    TaskStatusResponse,
    WorkflowExecuteRequest,
    WorkflowExecuteResponse,
    MetricsResponse,
    AgentListResponse,
    AgentInfo,
    WorkflowListResponse,
    WorkflowInfo,
    APIError,
    HealthResponse,
    ScheduleType,
    CreateScheduledTaskRequest,
    ScheduledTaskInfo,
    ScheduledTaskListResponse,
)
from .auth import get_auth, APIAuth
from .usage_tracker import get_tracker


# 路由器
router = APIRouter(prefix="/api/v1")

# 任务存储（生产环境应使用 Redis/数据库）
_tasks: Dict[str, Dict[str, Any]] = {}

# 服务启动时间
_start_time = datetime.now()


# ============================================================================
# 依赖注入
# ============================================================================

def verify_api_key(x_api_key: str = Query(None, alias="X-API-Key")):
    """验证 API Key"""
    auth = get_auth()
    is_valid, error_msg = auth.validate_key(x_api_key)
    if not is_valid:
        raise HTTPException(status_code=401, detail=error_msg)
    return x_api_key


def get_task(task_id: str) -> Dict[str, Any]:
    """获取任务"""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail=f"任务不存在：{task_id}")
    return _tasks[task_id]


# ============================================================================
# 健康检查
# ============================================================================

@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """健康检查"""
    uptime = (datetime.now() - _start_time).total_seconds()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime=uptime
    )


# ============================================================================
# Agent 相关
# ============================================================================

@router.post(
    "/agent/run",
    response_model=AgentRunResponse,
    tags=["Agent"]
)
async def run_agent(
    request: AgentRunRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    运行单个 Agent

    - **agent_name**: Agent 名称（如 developer, tester）
    - **input**: 输入内容/任务描述
    - **config**: 可选配置（timeout, debug 等）
    """
    task_id = str(uuid.uuid4())

    # 创建任务记录
    _tasks[task_id] = {
        "task_id": task_id,
        "type": "agent",
        "agent_name": request.agent_name,
        "input": request.input,
        "config": request.config,
        "instance_id": request.instance_id,
        "status": TaskStatus.PENDING,
        "output": None,
        "files": [],
        "error": None,
        "created_at": datetime.now(),
        "started_at": None,
        "completed_at": None,
    }

    # 启动后台任务
    background_tasks.add_task(_execute_agent_task, task_id)

    return AgentRunResponse(
        task_id=task_id,
        status=TaskStatus.RUNNING,
        message="任务已提交，正在处理中"
    )


@router.get(
    "/agent/list",
    response_model=AgentListResponse,
    tags=["Agent"]
)
async def list_agents(
    api_key: str = Depends(verify_api_key)
):
    """列出所有可用的 Agent"""
    try:
        from builtin_agents import list_available_agents, get_agent_info
        available = list_available_agents()
        agents = []
        for agent_type in available:
            try:
                info = get_agent_info(agent_type)
                agents.append(AgentInfo(
                    name=agent_type,
                    description=info.get("description", ""),
                    version=info.get("version", "1.0.0"),
                    tools=info.get("tools", []),
                    skills=[]  # 可以从配置中读取
                ))
            except Exception as e:
                print(f"[API] 获取 Agent 信息失败 {agent_type}: {e}")

        return AgentListResponse(agents=agents, total=len(agents))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Workflow 相关
# ============================================================================

@router.post(
    "/workflow/execute",
    response_model=WorkflowExecuteResponse,
    tags=["Workflow"]
)
async def execute_workflow(
    request: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    执行 Workflow

    - **workflow_name**: 预定义 Workflow 名称（可选）
    - **steps**: 动态定义 Workflow 步骤（可选）
    - **inputs**: 输入数据
    - **config**: 可选配置
    """
    task_id = str(uuid.uuid4())

    # 创建任务记录
    _tasks[task_id] = {
        "task_id": task_id,
        "type": "workflow",
        "workflow_name": request.workflow_name,
        "steps": request.steps,
        "inputs": request.inputs,
        "config": request.config,
        "status": TaskStatus.PENDING,
        "output": None,
        "files": [],
        "error": None,
        "created_at": datetime.now(),
        "started_at": None,
        "completed_at": None,
    }

    # 启动后台任务
    background_tasks.add_task(_execute_workflow_task, task_id)

    return WorkflowExecuteResponse(
        task_id=task_id,
        status=TaskStatus.RUNNING,
        message="Workflow 任务已提交，正在处理中"
    )


@router.get(
    "/workflow/list",
    response_model=WorkflowListResponse,
    tags=["Workflow"]
)
async def list_workflows(
    api_key: str = Depends(verify_api_key)
):
    """列出所有可用的 Workflow"""
    # TODO: 实现 Workflow 列表
    # 目前返回空列表，后续可以支持预定义 Workflow
    return WorkflowListResponse(workflows=[], total=0)


# ============================================================================
# 任务状态
# ============================================================================

@router.get(
    "/task/{task_id}/status",
    response_model=TaskStatusResponse,
    tags=["Tasks"]
)
async def get_task_status(
    task_id: str,
    task: Dict = Depends(get_task)
):
    """获取任务状态"""
    return TaskStatusResponse(
        task_id=task["task_id"],
        status=task["status"],
        output=task.get("output"),
        files=task.get("files"),
        error=task.get("error"),
        created_at=task.get("created_at"),
        started_at=task.get("started_at"),
        completed_at=task.get("completed_at"),
        duration=(
            (task["completed_at"] - task["started_at"]).total_seconds()
            if task.get("started_at") and task.get("completed_at")
            else None
        ),
        metadata={
            "type": task.get("type"),
            "agent_name": task.get("agent_name"),
            "workflow_name": task.get("workflow_name"),
        }
    )


@router.delete(
    "/task/{task_id}",
    tags=["Tasks"]
)
async def cancel_task(
    task_id: str,
    task: Dict = Depends(get_task)
):
    """取消任务"""
    if task["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        return {"message": f"任务已是终态：{task['status']}"}

    task["status"] = TaskStatus.CANCELLED
    task["completed_at"] = datetime.now()

    return {"message": "任务已取消"}


# ============================================================================
# 指标和统计
# ============================================================================

@router.get(
    "/metrics",
    response_model=MetricsResponse,
    tags=["Metrics"]
)
async def get_metrics(
    api_key: str = Depends(verify_api_key)
):
    """获取系统指标"""
    tracker = get_tracker()
    usage = tracker.get_total_usage()

    # 计算活跃 Agent 数量
    active_agents = len([
        t for t in _tasks.values()
        if t["status"] == TaskStatus.RUNNING
    ])

    return MetricsResponse(
        total_tasks=usage["total_tasks"],
        completed_tasks=usage["completed_tasks"],
        failed_tasks=usage["failed_tasks"],
        success_rate=usage["success_rate"],
        avg_duration=usage["avg_duration"],
        total_tokens=usage["total_tokens"],
        active_agents=active_agents,
        uptime=tracker.get_uptime()
    )


@router.get(
    "/usage/daily",
    tags=["Metrics"]
)
async def get_daily_usage(
    days: int = Query(default=7, ge=1, le=30),
    api_key: str = Depends(verify_api_key)
):
    """获取每日用量统计"""
    tracker = get_tracker()
    return {"daily_usage": tracker.get_daily_usage(days)}


# ============================================================================
# 定时任务相关
# ============================================================================

@router.post(
    "/schedule",
    tags=["Scheduled Tasks"],
)
async def create_scheduled_task(
    request: CreateScheduledTaskRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    创建定时任务

    - **schedule_type**: 调度类型 (once/interval/cron)
    - **run_at**: 一次性执行时间 (ISO 格式，如 "2026-03-10T10:00:00")
    - **interval_seconds**: 间隔秒数（如 3600 表示每小时）
    - **cron_expression**: Cron 表达式（如 "*/5 * * * *" 表示每 5 分钟）
    """
    from simple_agent.services.task_scheduler import get_scheduler

    scheduler = get_scheduler()

    # 根据调度类型创建任务
    if request.schedule_type == ScheduleType.ONCE:
        if not request.run_at:
            raise HTTPException(status_code=400, detail="ONCE 类型需要 run_at 参数")
        run_at = datetime.fromisoformat(request.run_at)
        task_id = scheduler.create_once_task(
            name=request.name,
            agent_name=request.agent_name,
            input=request.input,
            run_at=run_at,
            config=request.config,
            description=request.description,
            created_by=api_key,
        )
    elif request.schedule_type == ScheduleType.INTERVAL:
        if not request.interval_seconds:
            raise HTTPException(status_code=400, detail="INTERVAL 类型需要 interval_seconds 参数")
        task_id = scheduler.create_interval_task(
            name=request.name,
            agent_name=request.agent_name,
            input=request.input,
            interval_seconds=request.interval_seconds,
            config=request.config,
            description=request.description,
            created_by=api_key,
        )
    elif request.schedule_type == ScheduleType.CRON:
        if not request.cron_expression:
            raise HTTPException(status_code=400, detail="CRON 类型需要 cron_expression 参数")
        task_id = scheduler.create_cron_task(
            name=request.name,
            agent_name=request.agent_name,
            input=request.input,
            cron_expression=request.cron_expression,
            config=request.config,
            description=request.description,
            created_by=api_key,
        )
    else:
        raise HTTPException(status_code=400, detail=f"未知的调度类型：{request.schedule_type}")

    return {"task_id": task_id, "message": "定时任务已创建"}


@router.get(
    "/schedule",
    response_model=ScheduledTaskListResponse,
    tags=["Scheduled Tasks"],
)
async def list_scheduled_tasks(
    enabled_only: bool = Query(default=False, description="是否只显示启用的任务"),
    api_key: str = Depends(verify_api_key)
):
    """列出所有定时任务"""
    from simple_agent.services.task_scheduler import get_scheduler

    scheduler = get_scheduler()
    tasks = scheduler.list_tasks(enabled_only=enabled_only)

    task_list = [
        ScheduledTaskInfo(
            task_id=task.task_id,
            name=task.name,
            schedule_type=task.schedule_type,
            agent_name=task.agent_name,
            enabled=task.enabled,
            last_run=task.last_run.isoformat() if task.last_run else None,
            next_run=task.next_run.isoformat() if task.next_run else None,
            total_runs=task.total_runs,
            failed_runs=task.failed_runs,
            cron_expression=task.cron_expression,
            interval_seconds=task.interval_seconds,
            created_at=task.created_at.isoformat(),
        )
        for task in tasks
    ]

    return ScheduledTaskListResponse(tasks=task_list, total=len(task_list))


@router.get(
    "/schedule/{task_id}",
    tags=["Scheduled Tasks"],
)
async def get_scheduled_task(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """获取定时任务详情"""
    from simple_agent.services.task_scheduler import get_scheduler

    scheduler = get_scheduler()
    task = scheduler.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {
        "task_id": task.task_id,
        "name": task.name,
        "schedule_type": task.schedule_type.value,
        "agent_name": task.agent_name,
        "input": task.input,
        "enabled": task.enabled,
        "last_run": task.last_run.isoformat() if task.last_run else None,
        "next_run": task.next_run.isoformat() if task.next_run else None,
        "total_runs": task.total_runs,
        "failed_runs": task.failed_runs,
        "cron_expression": task.cron_expression,
        "interval_seconds": task.interval_seconds,
        "created_at": task.created_at.isoformat(),
        "description": task.description,
    }


@router.post(
    "/schedule/{task_id}/enable",
    tags=["Scheduled Tasks"],
)
async def enable_scheduled_task(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """启用定时任务"""
    from simple_agent.services.task_scheduler import get_scheduler

    scheduler = get_scheduler()
    if not scheduler.enable_task(task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"message": "任务已启用"}


@router.post(
    "/schedule/{task_id}/disable",
    tags=["Scheduled Tasks"],
)
async def disable_scheduled_task(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """禁用定时任务"""
    from simple_agent.services.task_scheduler import get_scheduler

    scheduler = get_scheduler()
    if not scheduler.disable_task(task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"message": "任务已禁用"}


@router.delete(
    "/schedule/{task_id}",
    tags=["Scheduled Tasks"],
)
async def delete_scheduled_task(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """删除定时任务"""
    from simple_agent.services.task_scheduler import get_scheduler

    scheduler = get_scheduler()
    if not scheduler.delete_task(task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"message": "任务已删除"}


# ============================================================================
# 定时任务执行回调
# ============================================================================

def _execute_scheduled_task(scheduled_task):
    """执行定时任务（回调函数）"""
    from simple_agent.services.task_scheduler import get_scheduler

    # 创建一个普通任务来执行
    task_id = str(uuid.uuid4())

    _tasks[task_id] = {
        "task_id": task_id,
        "type": "agent",
        "agent_name": scheduled_task.agent_name,
        "input": scheduled_task.input,
        "config": scheduled_task.config,
        "status": TaskStatus.PENDING,
        "output": None,
        "files": [],
        "error": None,
        "created_at": datetime.now(),
        "started_at": None,
        "completed_at": None,
        "scheduled_task_id": scheduled_task.task_id,  # 关联定时任务 ID
    }

    # 执行任务
    _execute_agent_task(task_id)

    print(f"[定时任务] {scheduled_task.name} 执行完成，状态：{_tasks[task_id]['status']}")


# ============================================================================
# 任务执行器
# ============================================================================

def _execute_agent_task(task_id: str):
    """后台执行 Agent 任务"""
    task = _tasks.get(task_id)
    if not task:
        return

    try:
        # 更新状态
        task["status"] = TaskStatus.RUNNING
        task["started_at"] = datetime.now()

        # 启动用量追踪
        tracker = get_tracker()
        tracker.start_task(task_id, task["agent_name"])

        # 创建并执行 Agent
        from builtin_agents import create_builtin_agent
        from simple_agent.core.llm import OpenAILLM

        agent = create_builtin_agent(task["agent_name"], OpenAILLM())

        # 执行任务（同步调用，在后台线程中运行）
        config = task.get("config", {})
        verbose = config.get("verbose", True)
        debug = config.get("debug", False)
        timeout = config.get("timeout", 300)

        # 在独立线程中执行，支持超时
        result = _run_agent_with_timeout(agent, task["input"], verbose, debug, timeout)

        # 更新任务状态
        task["output"] = result
        task["status"] = TaskStatus.COMPLETED
        task["completed_at"] = datetime.now()

        # 更新用量追踪
        tracker.complete_task(task_id, "completed")

    except TimeoutError as e:
        task["status"] = TaskStatus.FAILED
        task["error"] = f"任务执行超时：{str(e)}"
        task["completed_at"] = datetime.now()
        tracker.complete_task(task_id, "failed")

    except Exception as e:
        task["status"] = TaskStatus.FAILED
        task["error"] = str(e)
        task["completed_at"] = datetime.now()
        tracker.complete_task(task_id, "failed")


def _execute_workflow_task(task_id: str):
    """后台执行 Workflow 任务"""
    task = _tasks.get(task_id)
    if not task:
        return

    try:
        # 更新状态
        task["status"] = TaskStatus.RUNNING
        task["started_at"] = datetime.now()

        # 启动用量追踪
        tracker = get_tracker()
        tracker.start_task(task_id, task.get("workflow_name", "workflow"))

        # 执行 Workflow
        from simple_agent.swarm.scheduler.workflow import Workflow, WorkflowStep
        from simple_agent.builtin_agents import create_builtin_agent
        from simple_agent.core.llm import OpenAILLM

        inputs = task.get("inputs", {})
        steps_config = task.get("steps", [])

        # 动态创建 Workflow
        workflow = Workflow()

        for step_config in steps_config:
            agent_name = step_config.get("agent_name")
            step_name = step_config.get("name", agent_name)
            input_key = step_config.get("input_key")
            output_key = step_config.get("output_key")

            agent = create_builtin_agent(agent_name, OpenAILLM())
            step = WorkflowStep(
                name=step_name,
                agent=agent,
                input_key=input_key,
                output_key=output_key,
            )
            workflow.add_step(step)

        # 执行 Workflow
        config = task.get("config", {})
        verbose = config.get("verbose", True)
        debug = config.get("debug", False)

        result = workflow.run(
            inputs.get("input", ""),
            verbose=verbose,
            debug=debug,
        )

        # 更新任务状态
        task["output"] = result.get("_last_output", "")
        task["status"] = TaskStatus.COMPLETED
        task["completed_at"] = datetime.now()

        # 更新用量追踪
        tracker.complete_task(task_id, "completed")

    except Exception as e:
        task["status"] = TaskStatus.FAILED
        task["error"] = str(e)
        task["completed_at"] = datetime.now()
        tracker = get_tracker()
        tracker.complete_task(task_id, "failed")


def _run_agent_with_timeout(agent, input_text: str, verbose: bool, debug: bool, timeout: int) -> str:
    """带超时的 Agent 执行"""
    result_container = {"result": None, "error": None}

    def target():
        try:
            result_container["result"] = agent.run(input_text, verbose=verbose, debug=debug)
        except Exception as e:
            result_container["error"] = e

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        raise TimeoutError(f"Agent 执行超时（{timeout}秒）")

    if result_container["error"]:
        raise result_container["error"]

    return result_container["result"]
