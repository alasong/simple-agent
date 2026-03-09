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

from .api_models import (
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
)
from .api_auth import get_auth, APIAuth
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
        from core.llm import OpenAILLM

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
        from core.workflow import Workflow, WorkflowStep
        from builtin_agents import create_builtin_agent
        from core.llm import OpenAILLM

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
