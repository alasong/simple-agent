"""
Workflow - 多 Agent 协作流程

支持:
1. 顺序执行：Agent1 → Agent2 → Agent3
2. 并行执行：Agent1, Agent2 同时执行
3. 条件分支：根据结果选择下一个 Agent
4. 自动生成：根据任务描述自动创建 Workflow
5. 上下文共享：所有 Agent 共享工作流上下文
6. 多类型结果：支持字符串、文件、结构化数据
7. 调试输出：支持将各步骤结果保存到文件
"""

import json
import os
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .agent import Agent
from .factory import create_agent, AgentGenerator


class ResultType(Enum):
    """结果类型"""
    TEXT = "text"       # 文本字符串
    FILE = "file"       # 文件路径
    FILES = "files"     # 多文件
    JSON = "json"       # 结构化数据
    AUTO = "auto"       # 自动检测


@dataclass
class StepResult:
    """步骤结果"""
    type: ResultType
    content: Any
    files: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_summary(self, max_length: int = 200) -> str:
        """生成摘要"""
        if self.type == ResultType.FILE:
            return f"[文件] {self.content}"
        elif self.type == ResultType.FILES:
            return f"[{len(self.files)} 个文件] {', '.join(self.files[:3])}"
        elif self.type == ResultType.JSON:
            return f"[JSON] {json.dumps(self.content, ensure_ascii=False)[:max_length]}"
        else:
            text = str(self.content)
            return text[:max_length] + "..." if len(text) > max_length else text


class StepType(Enum):
    """步骤类型"""
    SEQUENCE = "sequence"  # 顺序
    PARALLEL = "parallel"  # 并行
    CONDITION = "condition"  # 条件


@dataclass
class WorkflowStep:
    """工作流步骤"""
    name: str
    agent: Agent
    instance_id: Optional[str] = None  # 实例标识，用于区分同一 agent 的不同副本
    input_key: Optional[str] = None  # 从上下文获取输入的 key
    output_key: Optional[str] = None  # 输出保存到上下文的 key
    condition: Optional[Callable[[Dict], bool]] = None  # 条件函数
    result_type: ResultType = ResultType.AUTO  # 结果类型
    
    def run(self, context: Dict, shared_memory: bool = True, verbose: bool = True,
            output_dir: Optional[str] = None, step_index: int = 0) -> Dict:
        """
        执行步骤
        
        Args:
            context: 工作流上下文
            shared_memory: 是否共享上下文到 Agent memory
            verbose: 是否打印详细过程
            output_dir: 输出目录（如果指定，将结果保存到文件）
            step_index: 步骤序号（用于文件命名）
        """
        # 构建输入
        if self.input_key:
            user_input = str(context.get(self.input_key, ""))
        else:
            user_input = context.get("_last_output", "")
        
        if not user_input:
            user_input = context.get("_initial_input", "")
        
        # 如果启用共享内存，将上下文信息注入 Agent
        if shared_memory:
            context_summary = self._build_context_summary(context)
            if context_summary:
                user_input = f"{context_summary}\n\n当前任务：{user_input}"
        
        # 执行 Agent
        if verbose:
            print(f"\n{'='*50}")
            print(f"[Workflow] 步骤：{self.name}")
            print(f"[Workflow] Agent: {self.agent.name}")
            if self.instance_id:
                print(f"[Workflow] 实例 ID: {self.instance_id}")
            print(f"{'='*50}")
        
        result_text = self.agent.run(user_input, verbose=verbose)
        
        # 解析结果
        step_result = self._parse_result(result_text)
        
        # 保存输出
        if self.output_key:
            context[self.output_key] = step_result
        
        context["_last_output"] = result_text
        context["_last_result"] = step_result
        context["_step_results"] = context.get("_step_results", {})
        context["_step_results"][self.name] = step_result
        
        # 如果指定了输出目录，保存结果到文件
        if output_dir:
            self._save_to_file(output_dir, step_index, result_text, step_result)
        
        return context
    
    def _build_context_summary(self, context: Dict) -> str:
        """构建上下文摘要"""
        parts = []
        
        # 初始任务
        if context.get("_initial_input"):
            parts.append(f"初始任务：{context['_initial_input']}")
        
        # 之前步骤结果
        step_results = context.get("_step_results", {})
        if step_results:
            parts.append("\n之前步骤的结果:")
            for step_name, result in step_results.items():
                summary = result.to_summary()
                parts.append(f"  [{step_name}]: {summary}")
        
        return "\n".join(parts) if parts else ""
    
    def _parse_result(self, result_text: str) -> StepResult:
        """解析结果"""
        result = StepResult(type=ResultType.TEXT, content=result_text)
        
        # 检测文件路径
        import re
        # 匹配文件路径模式
        file_patterns = [
            r'(?:文件 | 保存到 | 写入 | 输出)[:：]?\s*([/\w\-\.]+\.\w+)',
            r'([/\w\-\.]+\.(?:txt|json|csv|py|md|html|xml))',
        ]
        
        files = []
        for pattern in file_patterns:
            matches = re.findall(pattern, result_text)
            files.extend(matches)
        
        if len(files) == 1:
            result.type = ResultType.FILE
            result.content = files[0]
            result.files = files
        elif len(files) > 1:
            result.type = ResultType.FILES
            result.files = files
        
        # 尝试解析 JSON
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
            if json_match:
                result.type = ResultType.JSON
                result.content = json.loads(json_match.group(1))
        except:
            pass
        
        return result
    
    def _save_to_file(self, output_dir: str, step_index: int, result_text: str, step_result: StepResult):
        """保存步骤结果到文件"""
        # 文件名格式：01_[instance_id_] 步骤名_output.txt
        safe_name = self.name.replace("/", "_").replace("\\", "_").replace(":", "_")
        
        # 如果有 instance_id，添加到文件名中
        if self.instance_id:
            safe_instance = self.instance_id.replace("/", "_").replace("\\", "_").replace(":", "_")
            filename = f"{step_index:02d}_{safe_instance}_{safe_name}_output.txt"
        else:
            filename = f"{step_index:02d}_{safe_name}_output.txt"
        
        filepath = os.path.join(output_dir, filename)
        
        # 保存文本输出
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Step: {self.name}\n")
            if self.instance_id:
                f.write(f"# Instance ID: {self.instance_id}\n")
            f.write(f"# Agent: {self.agent.name} (v{self.agent.version})\n")
            f.write(f"# Result Type: {step_result.type.value}\n")
            f.write("\n")
            f.write(result_text)
        
        # 如果有生成的文件，复制到输出目录
        if step_result.files:
            import shutil
            files_dir = os.path.join(output_dir, "files")
            os.makedirs(files_dir, exist_ok=True)
            
            for file_path in step_result.files:
                if os.path.exists(file_path):
                    # 复制文件到输出目录
                    dest_path = os.path.join(files_dir, os.path.basename(file_path))
                    shutil.copy2(file_path, dest_path)
        
        # 如果是 JSON 结果，额外保存一个纯 JSON 文件
        if step_result.type == ResultType.JSON:
            if self.instance_id:
                json_filename = f"{step_index:02d}_{self.instance_id}_{safe_name}_data.json"
            else:
                json_filename = f"{step_index:02d}_{safe_name}_data.json"
            json_filepath = os.path.join(output_dir, json_filename)
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(step_result.content, f, ensure_ascii=False, indent=2)


@dataclass
class Workflow:
    """
    工作流 - 多 Agent 协作
    
    特性:
    - 顺序执行多个 Agent
    - 共享工作流上下文
    - 支持多种结果类型（文本、文件、JSON）
    - 每个步骤结果可传递给下一步
    - 支持调试输出到文件
    
    示例:
        workflow = Workflow("代码审查流程")
        workflow.add_step("读取", file_agent, output_key="file_content")
        workflow.add_step("检查", check_agent, input_key="file_content")
        workflow.add_step("报告", report_agent)
        
        result = workflow.run("检查 /tmp/code.py")
    """
    
    name: str
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    shared_memory: bool = True  # 是否共享上下文
    
    def add_step(
        self,
        name: str,
        agent: Agent,
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
        condition: Optional[Callable[[Dict], bool]] = None,
        result_type: ResultType = ResultType.AUTO,
        instance_id: Optional[str] = None
    ) -> "Workflow":
        """添加步骤"""
        step = WorkflowStep(
            name=name,
            agent=agent,
            instance_id=instance_id,
            input_key=input_key,
            output_key=output_key,
            condition=condition,
            result_type=result_type
        )
        self.steps.append(step)
        return self
    
    def add_replica_step(
        self,
        name: str,
        base_agent: Agent,
        instance_id: str,
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
        result_type: ResultType = ResultType.AUTO,
        output_subdir: Optional[str] = None
    ) -> "Workflow":
        """
        基于现有 agent 创建一个副本步骤
        
        Args:
            name: 步骤名称
            base_agent: 基础 agent（模板）
            instance_id: 实例标识，如 "project-A", "project-B"
            input_key: 输入 key
            output_key: 输出 key
            result_type: 结果类型
            output_subdir: 输出子目录（如果不指定，默认使用 instance_id）
        
        Returns:
            Workflow 自身，支持链式调用
        
        示例:
            workflow.add_replica_step(
                name="项目 A 开发",
                base_agent=dev_agent,
                instance_id="project-A",
                output_key="result_A"
            )
        """
        # 克隆 agent
        agent_replica = base_agent.clone(instance_id)
        
        # 添加步骤
        return self.add_step(
            name=name,
            agent=agent_replica,
            instance_id=instance_id,
            input_key=input_key,
            output_key=output_key,
            result_type=result_type
        )
    
    def add_parallel_replicas(
        self,
        name_prefix: str,
        base_agent: Agent,
        project_inputs: Dict[str, str],
        output_key_prefix: Optional[str] = None
    ) -> "Workflow":
        """
        为多个项目批量创建 agent 副本步骤
        
        Args:
            name_prefix: 步骤名称前缀
            base_agent: 基础 agent
            project_inputs: {项目 ID: 输入内容}
            output_key_prefix: 输出 key 前缀
        
        Returns:
            Workflow 自身，支持链式调用
        
        示例:
            workflow.add_parallel_replicas(
                name_prefix="审查",
                base_agent=reviewer_agent,
                project_inputs={
                    "project-A": "审查 /path/to/project-a",
                    "project-B": "审查 /path/to/project-b"
                },
                output_key_prefix="review_"
            )
        """
        for project_id, input_text in project_inputs.items():
            step_name = f"{name_prefix}-{project_id}"
            output_key = f"{output_key_prefix or 'result_'}{project_id}"
            self.add_replica_step(
                name=step_name,
                base_agent=base_agent,
                instance_id=project_id,
                output_key=output_key
            )
        return self
    
    def run(
        self, 
        initial_input: str, 
        verbose: bool = True, 
        output_dir: Optional[str] = None,
        isolate_by_instance: bool = False
    ) -> Dict:
        """
        执行工作流
        
        Args:
            initial_input: 初始输入
            verbose: 是否打印详细过程
            output_dir: 输出目录（如果指定，将各步骤结果保存到文件）
            isolate_by_instance: 是否按 instance_id 隔离输出目录
        
        Returns:
            执行上下文（包含所有步骤的输出）
        """
        # 初始化上下文
        self.context = {
            "_initial_input": initial_input,
            "_last_output": initial_input,
            "_step_results": {}
        }
        
        # 如果指定了输出目录，创建工作流输出文件夹
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            # 保存初始输入
            initial_file = os.path.join(output_dir, "00_initial_input.txt")
            with open(initial_file, 'w', encoding='utf-8') as f:
                f.write(initial_input)
            if verbose:
                print(f"\n[Debug] 结果将保存到：{output_dir}")
                if isolate_by_instance:
                    print(f"[Debug] 已启用按实例隔离输出目录")
        
        if verbose:
            print(f"\n{'#'*50}")
            print(f"# Workflow: {self.name}")
            print(f"# 步骤数：{len(self.steps)}")
            print(f"# 共享上下文：{self.shared_memory}")
            if output_dir:
                print(f"# 输出目录：{output_dir}")
                if isolate_by_instance:
                    print(f"# 隔离模式：按 instance_id 分离子目录")
            print(f"{'#'*50}")
        
        # 顺序执行所有步骤
        for i, step in enumerate(self.steps, 1):
            # 检查条件
            if step.condition and not step.condition(self.context):
                if verbose:
                    print(f"\n[Workflow] 跳过步骤 {i}: {step.name} (条件不满足)")
                continue
            
            if verbose:
                print(f"\n[Workflow] 步骤 {i}/{len(self.steps)}")
            
            # 确定输出目录
            step_output_dir = output_dir
            if isolate_by_instance and output_dir and step.instance_id:
                # 为每个实例创建独立的子目录
                step_output_dir = os.path.join(output_dir, step.instance_id)
                os.makedirs(step_output_dir, exist_ok=True)
                if verbose:
                    print(f"[Workflow] 实例 {step.instance_id} 输出目录：{step_output_dir}")
            
            # 执行步骤，传入输出目录
            self.context = step.run(
                self.context, 
                shared_memory=self.shared_memory,
                verbose=verbose,
                output_dir=step_output_dir,
                step_index=i
            )
        
        if verbose:
            print(f"\n{'#'*50}")
            print(f"# Workflow 完成")
            if output_dir:
                print(f"# 结果已保存到：{output_dir}")
                if isolate_by_instance:
                    print(f"# 各实例输出已隔离到对应子目录")
            print(f"{'#'*50}")
        
        return self.context
    
    def get_result(self, key: str = "_last_output") -> Any:
        """获取执行结果"""
        return self.context.get(key)
    
    def get_step_result(self, step_name: str) -> Optional[StepResult]:
        """获取指定步骤的结果"""
        return self.context.get("_step_results", {}).get(step_name)
    
    def get_all_files(self) -> List[str]:
        """获取所有生成的文件"""
        files = []
        for result in self.context.get("_step_results", {}).values():
            if isinstance(result, StepResult):
                files.extend(result.files)
        return list(set(files))
    
    def to_dict(self) -> Dict:
        """序列化"""
        return {
            "name": self.name,
            "description": self.description,
            "shared_memory": self.shared_memory,
            "steps": [
                {
                    "name": s.name,
                    "agent": s.agent.to_dict(),  # 保存完整 Agent 定义
                    "instance_id": s.instance_id,
                    "input_key": s.input_key,
                    "output_key": s.output_key,
                    "result_type": s.result_type.value
                }
                for s in self.steps
            ]
        }
    
    def to_json(self) -> str:
        """序列化为 JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, path: str) -> "Workflow":
        """从文件加载 Workflow"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Workflow":
        """从字典创建 Workflow"""
        workflow = cls(
            name=data.get("name", "Workflow"),
            description=data.get("description", ""),
            shared_memory=data.get("shared_memory", True)
        )
        
        # 重建步骤和 Agent
        for step_data in data.get("steps", []):
            # 从保存的数据重建 Agent
            agent_dict = step_data.get("agent", {})
            if agent_dict:
                agent = Agent.from_dict(agent_dict)
            else:
                # 兼容旧格式：只有 agent_name
                agent = create_agent(
                    description=step_data.get("agent_name", "Agent"),
                    tags=[]
                )
            
            workflow.add_step(
                name=step_data.get("name", "步骤"),
                agent=agent,
                instance_id=step_data.get("instance_id"),
                input_key=step_data.get("input_key"),
                output_key=step_data.get("output_key"),
                result_type=ResultType(step_data.get("result_type", "auto"))
            )
        
        return workflow


# ==================== 自动生成 Workflow (委托给 WorkflowGenerator) ====================

def generate_workflow(description: str, verbose: bool = True) -> Workflow:
    """
    根据描述自动生成 Workflow
    
    委托给 WorkflowGenerator 类处理
    
    Args:
        description: 工作流描述
        verbose: 是否打印详细过程
    
    Returns:
        Workflow 实例
    """
    from .workflow_generator import WorkflowGenerator
    return WorkflowGenerator.from_description(description, verbose)


# ==================== 快捷函数 ====================

def create_workflow(
    name: str,
    description: str = "",
    steps: Optional[List[Dict]] = None
) -> Workflow:
    """
    创建工作流
    
    Args:
        name: 工作流名称
        description: 描述
        steps: 步骤列表 [{"name": "步骤名", "agent": Agent, "input_key": ..., "output_key": ...}]
    
    Returns:
        Workflow 实例
    """
    workflow = Workflow(name=name, description=description)
    
    if steps:
        for step in steps:
            workflow.add_step(
                name=step.get("name", ""),
                agent=step["agent"],
                input_key=step.get("input_key"),
                output_key=step.get("output_key")
            )
    
    return workflow
