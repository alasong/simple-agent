"""
CLI Agent - 统一的用户交互入口

职责:
1. 与用户自然语言交流
2. 理解用户意图和场景
3. 创建或调用合适的 builtin agent
4. 动态组织 workflow
5. 合并和呈现结果给用户
"""

import json
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from core.agent import Agent
from core.llm import OpenAILLM
from core.workflow import Workflow


class TaskType(Enum):
    """任务类型"""
    DEVELOPMENT = "development"      # 开发任务
    REVIEW = "review"                # 审查任务
    TEST = "test"                    # 测试任务
    DOCUMENTATION = "documentation"  # 文档任务
    DEPLOYMENT = "deployment"        # 部署任务
    DEBUG = "debug"                  # 调试任务
    MULTI_STEP = "multi_step"        # 多步骤任务
    PARALLEL = "parallel"            # 并行任务（多副本）
    GENERAL = "general"              # 通用任务


@dataclass
class Intent:
    """用户意图分析结果"""
    task_type: TaskType
    description: str
    needs_workflow: bool = False
    agents_needed: List[str] = None
    is_parallel: bool = False
    parallel_count: int = 0
    parallel_inputs: Optional[Dict[str, str]] = None  # {instance_id: input}
    
    def __post_init__(self):
        if self.agents_needed is None:
            self.agents_needed = []


class CLIAgent:
    """
    CLI 入口 Agent
    
    负责理解用户需求并分发到合适的 agent 或 workflow
    """
    
    def __init__(self, llm: Optional[OpenAILLM] = None):
        self.llm = llm or OpenAILLM()
        
        # 创建 CLI agent 本身（用于意图分析）
        self.agent = Agent(
            llm=self.llm,
            name="CLI Agent",
            description="用户交互入口，理解和分发任务",
            system_prompt=self._create_system_prompt(),
            max_iterations=5
        )
        
        # Builtin agents 缓存
        self._builtin_agents: Dict[str, Agent] = {}
    
    def _create_system_prompt(self) -> str:
        """创建 system prompt"""
        return """你是 CLI Agent，是与用户交互的唯一入口。

你的职责：
1. 理解用户的自然语言输入
2. 分析任务类型和场景
3. 选择合适的专业 agent 来完成任务
4. 如果需要多步骤，创建工作流
5. 执行并合并结果返回给用户

可用的专业 agent：
- developer: 开发工程师，负责代码编写、功能实现
- reviewer: 代码审查员，负责质量检查、代码审查
- tester: 测试工程师，负责测试用例编写和执行
- architect: 架构师，负责技术设计、架构规划
- documenter: 文档工程师，负责文档编写、整理
- deployer: 部署工程师，负责部署配置、CI/CD

根据用户需求选择合适的 agent 或创建工作流。"""
    
    def analyze_intent(self, user_input: str) -> Intent:
        """
        分析用户意图
        
        Args:
            user_input: 用户输入
        
        Returns:
            Intent 对象
        """
        prompt = f"""分析用户意图，返回 JSON 格式。

用户输入：{user_input}

可用 agent 类型：
- developer: 代码编写、功能实现
- reviewer: 质量检查、代码审查  
- tester: 测试用例、执行测试
- architect: 技术设计、架构规划
- documenter: 文档编写、整理
- deployer: 部署配置、CI/CD

返回 JSON 格式：
{{
    "task_type": "development|review|test|documentation|deployment|debug|multi_step|parallel|general",
    "description": "任务描述",
    "needs_workflow": true/false,
    "agents_needed": ["developer", "reviewer"],
    "is_parallel": true/false,
    "parallel_count": 0,
    "parallel_inputs": {{"instance-1": "input1", "instance-2": "input2"}}
}}

判断规则：
1. 如果提到多个项目/任务（如"A、B、C 三个项目"），is_parallel=true，parallel_count=数量
2. 如果提到多步骤（如"先设计，再编码，最后检查"），needs_workflow=true
3. 根据任务内容选择合适的 agents_needed
4. 简单任务只需一个 agent，needs_workflow=false

只返回 JSON，不要其他内容。"""
        
        try:
            # 调用 LLM 分析意图
            response = self.llm.chat([{"role": "user", "content": prompt}])
            content = response["content"]
            
            # 提取 JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group()
            
            intent_data = json.loads(content)
            
            # 构建 Intent 对象
            intent = Intent(
                task_type=TaskType(intent_data.get("task_type", "general")),
                description=intent_data.get("description", user_input),
                needs_workflow=intent_data.get("needs_workflow", False),
                agents_needed=intent_data.get("agents_needed", []),
                is_parallel=intent_data.get("is_parallel", False),
                parallel_count=intent_data.get("parallel_count", 0),
                parallel_inputs=intent_data.get("parallel_inputs")
            )
            
            return intent
            
        except Exception as e:
            # 分析失败，返回通用意图
            print(f"[CLI Agent] 意图分析失败：{e}，使用通用模式")
            return Intent(
                task_type=TaskType.GENERAL,
                description=user_input,
                agents_needed=["developer"]
            )
    
    def _get_builtin_agent(self, agent_type: str) -> Agent:
        """
        获取 builtin agent
        
        Args:
            agent_type: agent 类型
        
        Returns:
            Agent 实例
        """
        # 检查缓存
        if agent_type in self._builtin_agents:
            return self._builtin_agents[agent_type]
        
        # 动态导入并创建
        try:
            from builtin_agents import get_agent
            agent = get_agent(agent_type)
            self._builtin_agents[agent_type] = agent
            return agent
        except ImportError:
            # builtin_agents 未实现时，创建临时 agent
            agent = self._create_fallback_agent(agent_type)
            self._builtin_agents[agent_type] = agent
            return agent
    
    def _create_fallback_agent(self, agent_type: str) -> Agent:
        """创建临时 agent（当 builtin_agents 未实现时）"""
        prompts = {
            "developer": "你是开发工程师，擅长编写代码和实现功能。",
            "reviewer": "你是代码审查员，擅长检查代码质量和规范性。",
            "tester": "你是测试工程师，擅长编写和执行测试用例。",
            "architect": "你是架构师，擅长技术设计和架构规划。",
            "documenter": "你是文档工程师，擅长编写技术文档。",
            "deployer": "你是部署工程师，擅长部署配置和 CI/CD。"
        }
        
        return Agent(
            llm=self.llm,
            name=f"{agent_type.capitalize()} Agent",
            description=f"Builtin {agent_type} agent",
            system_prompt=prompts.get(agent_type, "你是专业助手。"),
            max_iterations=10
        )
    
    def execute(self, user_input: str, verbose: bool = True, 
                output_dir: Optional[str] = None, isolate_by_instance: bool = False) -> Any:
        """
        执行任务
        
        Args:
            user_input: 用户输入
            verbose: 是否打印详细过程
            output_dir: 输出目录
            isolate_by_instance: 是否按实例隔离输出
        
        Returns:
            执行结果
        """
        # 1. 分析意图
        if verbose:
            print(f"\n[CLI Agent] 分析用户意图...")
        
        intent = self.analyze_intent(user_input)
        
        if verbose:
            print(f"[CLI Agent] 任务类型：{intent.task_type.value}")
            print(f"[CLI Agent] 需要 Workflow: {intent.needs_workflow}")
            print(f"[CLI Agent] 需要 Agents: {intent.agents_needed}")
            print(f"[CLI Agent] 并行模式：{intent.is_parallel}")
            if intent.parallel_count > 0:
                print(f"[CLI Agent] 副本数量：{intent.parallel_count}")
        
        # 2. 根据意图执行
        if intent.is_parallel and intent.parallel_inputs:
            # 并行任务模式
            result = self._execute_parallel(
                intent, user_input, verbose, output_dir, isolate_by_instance
            )
        elif intent.needs_workflow and len(intent.agents_needed) > 1:
            # 多步骤 workflow 模式
            result = self._execute_workflow(
                intent, user_input, verbose, output_dir, isolate_by_instance
            )
        elif intent.agents_needed:
            # 单个 agent 模式
            agent_type = intent.agents_needed[0]
            result = self._execute_single_agent(
                agent_type, user_input, verbose
            )
        else:
            # 默认模式：使用 CLI agent 自己
            result = self.agent.run(user_input, verbose=verbose)
        
        return result
    
    def _execute_single_agent(self, agent_type: str, user_input: str, 
                              verbose: bool = True) -> Any:
        """执行单个 agent 任务"""
        if verbose:
            print(f"\n[CLI Agent] 调用 {agent_type} agent 执行任务...")
        
        agent = self._get_builtin_agent(agent_type)
        result = agent.run(user_input, verbose=verbose)
        
        if verbose:
            print(f"\n[CLI Agent] 任务完成")
        
        return result
    
    def _execute_workflow(self, intent: Intent, user_input: str, 
                         verbose: bool = True, output_dir: Optional[str] = None,
                         isolate_by_instance: bool = False) -> Any:
        """执行多步骤 workflow"""
        if verbose:
            print(f"\n[CLI Agent] 创建工作流...")
        
        workflow = Workflow(
            name="动态工作流",
            description=f"执行：{intent.description}"
        )
        
        # 为每个需要的 agent 添加步骤
        current_input = None
        for i, agent_type in enumerate(intent.agents_needed):
            agent = self._get_builtin_agent(agent_type)
            step_name = f"{agent_type.capitalize()} 执行"
            
            workflow.add_step(
                name=step_name,
                agent=agent,
                input_key=current_input,
                output_key=f"step_{i}"
            )
            
            if i == 0:
                current_input = f"step_{i}"
        
        if verbose:
            print(f"[CLI Agent] 工作流包含 {len(workflow.steps)} 个步骤")
            for i, step in enumerate(workflow.steps, 1):
                print(f"  {i}. {step.name} -> {step.agent.name}")
        
        # 执行工作流
        result = workflow.run(
            user_input,
            verbose=verbose,
            output_dir=output_dir,
            isolate_by_instance=isolate_by_instance
        )
        
        return result.get("_last_output", "完成")
    
    def _execute_parallel(self, intent: Intent, user_input: str,
                         verbose: bool = True, output_dir: Optional[str] = None,
                         isolate_by_instance: bool = False) -> Any:
        """执行并行任务（多副本）"""
        if verbose:
            print(f"\n[CLI Agent] 创建并行任务...")
        
        workflow = Workflow(
            name="并行工作流",
            description=f"执行：{intent.description}"
        )
        
        # 获取基础 agent
        agent_type = intent.agents_needed[0] if intent.agents_needed else "developer"
        base_agent = self._get_builtin_agent(agent_type)
        
        if verbose:
            print(f"[CLI Agent] 使用 agent: {base_agent.name}")
            print(f"[CLI Agent] 创建 {intent.parallel_count} 个副本")
        
        # 如果有明确的 parallel_inputs，使用它们
        if intent.parallel_inputs:
            workflow.add_parallel_replicas(
                name_prefix="任务",
                base_agent=base_agent,
                project_inputs=intent.parallel_inputs,
                output_key_prefix="result_"
            )
        else:
            # 否则根据 parallel_count 创建
            inputs = {
                f"task-{i}": user_input 
                for i in range(1, intent.parallel_count + 1)
            }
            workflow.add_parallel_replicas(
                name_prefix="任务",
                base_agent=base_agent,
                project_inputs=inputs,
                output_key_prefix="result_"
            )
        
        if verbose:
            print(f"[CLI Agent] 工作流包含 {len(workflow.steps)} 个并行步骤")
            for step in workflow.steps:
                print(f"  - {step.name} (instance_id={step.instance_id})")
        
        # 执行工作流
        result = workflow.run(
            user_input,
            verbose=verbose,
            output_dir=output_dir,
            isolate_by_instance=isolate_by_instance
        )
        
        # 合并并行结果
        return self._merge_parallel_results(result)
    
    def _merge_parallel_results(self, context: Dict) -> str:
        """合并并行任务的结果"""
        results = []
        for key, value in context.items():
            if key.startswith("result_"):
                results.append(f"[{key}]: {value}")
        
        if not results:
            return "并行任务完成"
        
        return "\n\n".join(results)
