"""
Agent 协作工具

支持 Agent 之间的协作：
- InvokeAgentTool: 调用其他 Agent 执行子任务
- CreateWorkflowTool: 创建工作流并执行（支持并行）
- ListAgentsTool: 列出可用的 Agent 类型
"""

import threading
from typing import Optional, Dict, Any

from simple_agent.core.tool import BaseTool, ToolResult
from simple_agent.core.resource import repo

# 全局执行上下文（线程本地存储）
_execution_context = threading.local()


def set_verbose(verbose: bool):
    """设置全局 verbose 状态"""
    _execution_context.verbose = verbose


def get_verbose() -> bool:
    """获取全局 verbose 状态"""
    return getattr(_execution_context, 'verbose', True)


def set_output_dir(output_dir: Optional[str]):
    """设置全局输出目录"""
    _execution_context.output_dir = output_dir


def get_output_dir() -> str:
    """获取全局输出目录（如果未设置，返回 None）"""
    return getattr(_execution_context, 'output_dir', None)


# ==================== 工具定义 ====================

class InvokeAgentTool(BaseTool):
    """调用其他 Agent 执行子任务"""

    @property
    def name(self) -> str:
        return "InvokeAgentTool"

    @property
    def description(self) -> str:
        return "调用指定的专业 Agent 执行子任务。适用于需要将任务分解给专业 Agent 的场景。**支持并行调用多个 Agent**。"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Agent 名称 (SoftwareDeveloper, developer, reviewer, tester, architect, documenter, deployer 等)"
                },
                "agent_type": {
                    "type": "string",
                    "description": "Agent 类型 (同上，兼容旧参数)"
                },
                "task": {
                    "type": "string",
                    "description": "要执行的子任务描述"
                },
                "task_description": {
                    "type": "string",
                    "description": "任务描述 (兼容旧参数)"
                },
                "parameters": {
                    "type": "object",
                    "description": "额外的参数配置"
                },
                "interactive": {
                    "type": "boolean",
                    "description": "是否启用交互模式，在关键步骤询问用户"
                }
            },
            "required": []
        }

    def execute(self, agent_name: Optional[str] = None, agent_type: Optional[str] = None,
                task: Optional[str] = None, task_description: Optional[str] = None,
                parameters: Optional[dict] = None, interactive: bool = False, **kwargs) -> ToolResult:
        """
        调用其他 Agent

        Args:
            agent_name: Agent 名称（优先使用）
            agent_type: Agent 类型（兼容旧参数）
            task: 子任务描述（优先使用）
            task_description: 任务描述（兼容旧参数）
            parameters: 额外参数配置
            interactive: 是否启用交互模式
        """
        # 兼容不同参数命名
        target_agent = agent_name or agent_type
        target_task = task or task_description

        if not target_agent or not target_task:
            return ToolResult(
                success=False,
                output="",
                error="需要指定 agent_name(或 agent_type) 和 task(或 task_description)"
            )

        # 使用全局 verbose 设置（必须在交互模式之前）
        verbose = get_verbose()

        try:
            from simple_agent.core.agent_manager import get_agent

            # Agent 名称转换：支持驼峰命名和蛇形命名
            # 例如：SoftwareDeveloper -> software_developer
            def convert_agent_name(name: str) -> str:
                """将驼峰命名转换为蛇形命名"""
                import re
                # 如果已经包含下划线，可能是蛇形命名，直接返回
                if '_' in name:
                    return name.lower()
                # 驼峰转蛇形
                return re.sub(r'([A-Z])', r'_\1', name).lower().lstrip('_')

            # 尝试直接获取
            try:
                agent = get_agent(target_agent)
            except ValueError:
                # 转换名称后再尝试（驼峰->蛇形）
                converted_name = convert_agent_name(target_agent)
                agent = get_agent(converted_name)
                if verbose:
                    print(f"[InvokeAgent] Agent 名称转换: {target_agent} -> {converted_name}")

            # 交互模式提示
            if interactive and verbose:
                print(f"\n[交互确认] 准备调用 {target_agent} Agent")
                print(f"任务：{target_task[:100]}...")
                try:
                    confirm = input("是否继续？(Y/n): ").strip().lower()
                    if confirm in ('n', 'no'):
                        return ToolResult(success=False, output="", error="用户取消操作")
                except:
                    pass

            if verbose:
                print(f"\n[InvokeAgent] 调用 {target_agent} Agent...")
                print(f"[InvokeAgent] 任务：{target_task}")

            result = agent.run(target_task, verbose=verbose)

            if verbose:
                print(f"\n[InvokeAgent] {target_agent} Agent 完成")

            return ToolResult(
                success=True,
                output=result,
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"调用 Agent 失败：{e}"
            )


class CreateWorkflowTool(BaseTool):
    """创建工作流并执行（支持并行）"""

    @property
    def name(self) -> str:
        return "CreateWorkflowTool"

    @property
    def description(self) -> str:
        return "根据任务描述创建工作流并执行。**支持并行执行多个 Agent**，适用于多步骤复杂任务。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "任务描述，工作流将基于此描述自动生成"
                },
                "steps": {
                    "type": "array",
                    "description": "可选的步骤配置列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "步骤名称"},
                            "agent_type": {"type": "string", "description": "使用的 Agent 类型"},
                            "description": {"type": "string", "description": "该步骤的任务描述"},
                            "parallel": {"type": "boolean", "description": "是否与上一步并行执行（默认 false）"}
                        },
                        "required": ["name", "agent_type", "description"]
                    }
                },
                "parallel": {
                    "type": "boolean",
                    "description": "是否启用并行执行模式（默认 true，适用于步骤之间无依赖的情况）"
                }
            },
            "required": ["task_description"]
        }

    def execute(self, task_description: str, steps: Optional[list] = None, parallel: bool = True, **kwargs) -> ToolResult:
        """创建并执行工作流"""
        try:
            # 修复导入路径
            from simple_agent.swarm.scheduler.workflow import Workflow, generate_workflow
            from simple_agent.swarm.scheduler.workflow_parallel import ParallelWorkflow, create_parallel_workflow
            from simple_agent.core.agent_manager import get_agent

            verbose = get_verbose()
            output_dir = get_output_dir()

            if verbose:
                print(f"\n[CreateWorkflow] 创建工作流...")
                print(f"[CreateWorkflow] 任务：{task_description}")
                print(f"[CreateWorkflow] 并行模式：{parallel}")
                if output_dir:
                    print(f"[CreateWorkflow] 输出目录：{output_dir}")

            if steps:
                # 有指定步骤，判断是否启用并行
                if parallel:
                    # 创建并行工作流
                    workflow = create_parallel_workflow(max_concurrent=5, default_timeout=300.0)
                    for i, step_config in enumerate(steps):
                        try:
                            agent = get_agent(step_config["agent_type"])
                        except (ImportError, ValueError):
                            agent = create_agent(description=step_config["description"], tags=[])

                        workflow.add_task(
                            name=step_config["name"],
                            agent=agent,
                            instance_id=f"step_{i}",
                            task_input=step_config["description"]
                        )

                    if verbose:
                        print(f"\n[CreateWorkflow] 执行并行工作流，{len(workflow.tasks)} 个任务...")

                    import asyncio
                    results = asyncio.run(workflow.execute(task_description, verbose=verbose, output_dir=output_dir))

                    # 合并结果
                    result_parts = []
                    for task_id, result in results.items():
                        if result.success:
                            result_parts.append(f"[{task_id}] {result.result.result if result.result else '完成'}")
                        else:
                            result_parts.append(f"[{task_id}] 失败：{result.error}")
                    result = "\n\n".join(result_parts)
                else:
                    # 创建顺序工作流
                    workflow = Workflow(name="动态工作流", description=task_description)
                    for i, step_config in enumerate(steps):
                        try:
                            agent = get_agent(step_config["agent_type"])
                        except (ImportError, ValueError):
                            agent = create_agent(description=step_config["description"], tags=[])

                        workflow.add_step(
                            name=step_config["name"],
                            agent=agent,
                            output_key=f"step_{i}"
                        )

                    if verbose:
                        print(f"\n[CreateWorkflow] 执行顺序工作流，{len(workflow.steps)} 个步骤...")

                    context = workflow.run(task_description, verbose=verbose, output_dir=output_dir)
                    result = context.get("_last_output", "工作流执行完成")
            else:
                # 无指定步骤，使用默认顺序工作流
                workflow = generate_workflow(task_description, verbose=verbose)

                if verbose:
                    print(f"\n[CreateWorkflow] 执行工作流，{len(workflow.steps)} 个步骤...")

                context = workflow.run(task_description, verbose=verbose, output_dir=output_dir)
                result = context.get("_last_output", "工作流执行完成")

            if verbose:
                print(f"\n[CreateWorkflow] 工作流完成")

            return ToolResult(
                success=True,
                output=result,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"创建工作流失败：{e}"
            )


class ListAgentsTool(BaseTool):
    """列出所有可用的 Agent 类型"""
    
    @property
    def name(self) -> str:
        return "ListAgentsTool"
    
    @property
    def description(self) -> str:
        return "列出所有可用的专业 Agent 类型及其功能描述。在不确定使用哪种 Agent 时使用。"
    
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}
    
    def execute(self, **kwargs) -> ToolResult:
        """列出所有可用的 Agent"""
        try:
            from simple_agent.core.agent_manager import list_all_agents, get_agent_info
            
            agents = list_all_agents()
            if not agents:
                return ToolResult(success=True, output="没有可用的 agents")
            
            result_lines = ["可用的 Agent 类型:"]
            for agent_type in agents:
                info = get_agent_info(agent_type)
                source_tag = " [custom]" if info.get("source") == "custom" else ""
                result_lines.append(f"  - {agent_type}{source_tag}: {info['name']} - {info['description']}")
            
            return ToolResult(
                success=True,
                output="\n".join(result_lines),
            )
            
        except ImportError:
            return ToolResult(success=True, output="Agent 管理模块未实现")
        except Exception as e:
            return ToolResult(success=False, output="", error=f"列出 Agent 失败：{e}")


# ==================== 注册工具到资源仓库 ====================

repo.register_tool(InvokeAgentTool, tags=["agent", "coordination"], description="调用其他 Agent 执行子任务")
repo.register_tool(CreateWorkflowTool, tags=["agent", "workflow"], description="创建工作流并执行")
repo.register_tool(ListAgentsTool, tags=["agent", "info"], description="列出可用的 Agent 类型")
