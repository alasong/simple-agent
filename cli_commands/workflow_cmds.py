"""
工作流管理命令

命令:
- /workflow <文件> [任务描述] - 加载并运行工作流
"""

from typing import List, Dict, Any
from cli_commands import CommandHandler, CommandResult


class WorkflowCommand(CommandHandler):
    """加载并运行工作流"""
    
    @property
    def name(self) -> str:
        return "workflow"
    
    @property
    def description(self) -> str:
        return "加载并运行工作流"
    
    @property
    def usage(self) -> str:
        return "/workflow <工作流文件> [任务描述]"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult.error(
                "请提供工作流文件",
                "用法：/workflow <工作流文件> [任务描述]\n"
                "示例：\n"
                "  /workflow code_review.json\n"
                "  /workflow code_review.json 审查这个文件的代码"
            )
        
        try:
            from core import Workflow
            
            workflow_path = args[0]
            task = " ".join(args[1:]) if len(args) > 1 else None
            
            # 检查工作流文件是否存在
            if not workflow_path.endswith('.json'):
                workflows_dir = context.get('workflows_dir', './workflows')
                workflow_path = os.path.join(workflows_dir, f"{workflow_path}.json")
            
            if not os.path.exists(workflow_path):
                return CommandResult.error(f"工作流文件不存在：{workflow_path}")
            
            # 加载工作流
            workflow = Workflow.load(workflow_path)
            
            result_lines = [
                f"\n已加载工作流：{workflow.name}",
                f"描述：{workflow.description}",
                f"步骤数：{len(workflow.steps)}"
            ]
            
            # 如果没有提供任务描述，提示用户输入
            if not task:
                return CommandResult.ok(
                    "\n".join(result_lines) + "\n\n请提供任务描述",
                    data={"need_input": True, "workflow": workflow}
                )
            
            # 运行工作流
            # Note: 实际执行需要异步处理，这里返回工作流和任务描述
            return CommandResult.ok(
                "\n".join(result_lines),
                data={"workflow": workflow, "task": task, "need_execute": True}
            )
        
        except Exception as e:
            return CommandResult.error("加载工作流失败", str(e))


# 需要导入 os 模块
import os
