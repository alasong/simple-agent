"""
Agent 协作工具

支持 Agent 之间的协作：
- InvokeAgentTool: 调用其他 Agent 执行子任务
- CreateWorkflowTool: 创建工作流并执行
- ListAgentsTool: 列出可用的 Agent 类型
"""

import threading
from typing import Optional, Dict, Any

from core.tool import BaseTool, ToolResult
from core.resource import repo

# 全局执行上下文（线程本地存储）
_execution_context = threading.local()


def set_verbose(verbose: bool):
    """设置全局 verbose 状态"""
    _execution_context.verbose = verbose


def get_verbose() -> bool:
    """获取全局 verbose 状态"""
    return getattr(_execution_context, 'verbose', True)


# ==================== 工具定义 ====================

class InvokeAgentTool(BaseTool):
    """调用其他 Agent 执行子任务"""
    
    @property
    def name(self) -> str:
        return "InvokeAgentTool"
    
    @property
    def description(self) -> str:
        return "调用指定的专业 Agent 执行子任务。适用于需要将任务分解给专业 Agent 的场景。"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "agent_type": {
                    "type": "string",
                    "description": "Agent 类型 (developer, reviewer, tester, architect, documenter, deployer)"
                },
                "task": {
                    "type": "string",
                    "description": "要执行的子任务描述"
                }
            },
            "required": ["agent_type", "task"]
        }
    
    def execute(self, agent_type: str, task: str, **kwargs) -> ToolResult:
        """
        调用其他 Agent
        
        Args:
            agent_type: Agent 类型
            task: 子任务描述
        """
        try:
            from core.agent_manager import get_agent
            agent = get_agent(agent_type)
            
            # 使用全局 verbose 设置
            verbose = get_verbose()
            if verbose:
                print(f"\n[InvokeAgent] 调用 {agent_type} Agent...")
                print(f"[InvokeAgent] 任务：{task}")
            
            result = agent.run(task, verbose=verbose)
            
            if verbose:
                print(f"\n[InvokeAgent] {agent_type} Agent 完成")
            
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
    """创建工作流并执行"""
    
    @property
    def name(self) -> str:
        return "CreateWorkflowTool"
    
    @property
    def description(self) -> str:
        return "根据任务描述自动创建工作流，并按顺序执行多个 Agent。适用于多步骤复杂任务。"
    
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
                            "description": {"type": "string", "description": "该步骤的任务描述"}
                        },
                        "required": ["name", "agent_type", "description"]
                    }
                }
            },
            "required": ["task_description"]
        }
    
    def execute(self, task_description: str, steps: Optional[list] = None, **kwargs) -> ToolResult:
        """创建并执行工作流"""
        try:
            from core.workflow import Workflow, generate_workflow
            from core.factory import create_agent
            from core.agent_manager import get_agent
            
            verbose = get_verbose()
            
            if verbose:
                print(f"\n[CreateWorkflow] 创建工作流...")
                print(f"[CreateWorkflow] 任务：{task_description}")
            
            if steps:
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
            else:
                workflow = generate_workflow(task_description, verbose=verbose)
            
            if verbose:
                print(f"\n[CreateWorkflow] 执行工作流，{len(workflow.steps)} 个步骤...")
            
            # 执行工作流时传递 verbose
            context = workflow.run(task_description, verbose=verbose)
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
            from core.agent_manager import list_all_agents, get_agent_info
            
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
