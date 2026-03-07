"""
Workflow Generator - 自动生成工作流

负责根据描述自动生成 Workflow
"""

import json
from typing import Optional, List, Dict
from .workflow import Workflow, WorkflowStep, ResultType
from .agent import Agent
from .factory import create_agent


class WorkflowGenerator:
    """
    工作流生成器
    
    职责:
    - 解析工作流描述
    - 生成步骤配置
    - 创建 Workflow 实例
    """
    
    @classmethod
    def from_description(
        cls, 
        description: str, 
        verbose: bool = True
    ) -> Workflow:
        """
        根据描述生成 Workflow
        
        Args:
            description: 工作流描述
            verbose: 是否打印详细过程
        
        Returns:
            Workflow 实例
        """
        from .resource import repo
        
        # 获取 LLM
        llm = repo.extract_llm()
        
        # 生成工作流定义
        prompt = f"""分析以下任务描述，生成一个多步骤工作流。

任务描述：{description}

请输出 JSON 格式的工作流定义：
{{
    "name": "工作流名称",
    "description": "工作流描述",
    "steps": [
        {{
            "name": "步骤名称",
            "agent_description": "Agent 功能描述（用于自动创建 Agent）",
            "tools": ["工具标签，如 file/check/code"]
        }}
    ]
}}

要求：
1. 将任务分解为 2-5 个清晰的步骤
2. 每个步骤对应一个 Agent
3. tools 根据步骤功能选择：file(文件操作), check(检查), code(代码相关)
4. 只输出 JSON，不要其他内容"""

        response = llm.chat([{"role": "user", "content": prompt}])
        
        # 解析 JSON
        try:
            content = response["content"]
            # 去除可能的 markdown 代码块标记
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            workflow_def = json.loads(content)
        except json.JSONDecodeError as e:
            if verbose:
                print(f"解析失败，使用默认工作流：{e}")
            workflow_def = {
                "name": "默认工作流",
                "description": description,
                "steps": [{"name": "执行", "agent_description": description, "tools": []}]
            }
        
        if verbose:
            print(f"\n生成的工作流定义:")
            print(json.dumps(workflow_def, ensure_ascii=False, indent=2))
        
        # 创建 Workflow
        workflow = Workflow(
            name=workflow_def.get("name", "Workflow"),
            description=workflow_def.get("description", description)
        )
        
        # 创建步骤
        for i, step_def in enumerate(workflow_def.get("steps", []), 1):
            # 创建 Agent
            agent = create_agent(
                description=step_def.get("agent_description", f"步骤{i}"),
                tags=step_def.get("tools", [])
            )
            
            # 添加步骤
            workflow.add_step(
                name=step_def.get("name", f"步骤{i}"),
                agent=agent,
                output_key=f"step_{i}"
            )
            
            if verbose:
                print(f"\n创建 Agent: {agent}")
        
        return workflow
    
    @staticmethod
    def _parse_description(description: str) -> Dict:
        """
        解析工作流描述
        
        Args:
            description: 工作流描述
        
        Returns:
            解析后的结构
        """
        # 简单实现：按箭头分割步骤
        if "→" in description or "->" in description:
            separator = "→" if "→" in description else "->"
            steps = [s.strip() for s in description.split(separator)]
            return {
                "name": "自动生成的工作流",
                "description": description,
                "steps": steps
            }
        else:
            # 单个步骤
            return {
                "name": "简单工作流",
                "description": description,
                "steps": [description]
            }
    
    @staticmethod
    def _generate_steps(
        parsed: Dict, 
        agent_factory: Optional[callable] = None
    ) -> List[WorkflowStep]:
        """
        生成步骤列表
        
        Args:
            parsed: 解析后的描述
            agent_factory: Agent 工厂函数
        
        Returns:
            WorkflowStep 列表
        """
        steps = []
        
        if agent_factory is None:
            agent_factory = lambda desc: create_agent(description=desc, tags=[])
        
        for i, step_desc in enumerate(parsed.get("steps", []), 1):
            agent = agent_factory(step_desc)
            step = WorkflowStep(
                name=f"步骤{i}: {step_desc[:20]}",
                agent=agent,
                output_key=f"step_{i}"
            )
            steps.append(step)
        
        return steps
