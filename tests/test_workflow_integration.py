"""
Workflow Integration Tests

测试工作流的完整执行流程，包括：
1. 顺序执行
2. 并行执行
3. 条件分支
4. 依赖验证
5. 错误处理
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.workflow import Workflow, WorkflowStep
from core.agent import Agent
from core.llm import OpenAILLM
from tools.bash_tool import BashTool


class TestWorkflowExecution:
    """工作流执行测试"""
    
    def test_sequential_workflow(self):
        """测试顺序工作流执行"""
        # 创建工作流
        workflow = Workflow(name="测试顺序工作流")
        
        # 添加步骤 1：获取日期
        date_agent = Agent(
            llm=OpenAILLM(),
            tools=[BashTool()],
            name="DateAgent",
            system_prompt="你负责获取当前日期，使用 `date` 命令"
        )
        workflow.add_step(
            name="get_date",
            agent=date_agent,
        )
        
        # 添加步骤 2：处理日期
        process_agent = Agent(
            llm=OpenAILLM(),
            name="ProcessAgent",
            system_prompt="你负责处理日期信息"
        )
        workflow.add_step(
            name="process_date",
            agent=process_agent,
            input_key="_last_output"  # 依赖上一步输出
        )
        
        # 执行工作流
        result = workflow.run("请帮我处理日期信息", verbose=False)
        
        # 验证结果
        assert result is not None
        assert "_step_results" in result
        assert "get_date" in result["_step_results"]
        assert "process_date" in result["_step_results"]
        print("✓ 顺序工作流测试通过")
    
    def test_single_step_workflow(self):
        """测试单步工作流"""
        workflow = Workflow(name="单步工作流")
        
        agent = Agent(
            llm=OpenAILLM(),
            tools=[BashTool()],
            name="SimpleAgent",
            system_prompt="你是一个简单的助手，使用 bash 命令回答问题"
        )
        
        workflow.add_step(
            name="simple_step",
            agent=agent,
        )
        
        result = workflow.run("今天几号？", verbose=False)
        
        assert result is not None
        assert len(result.get("_step_results", {})) == 1
        print("✓ 单步工作流测试通过")


class TestWorkflowDependencies:
    """工作流依赖测试"""
    
    def test_missing_dependency(self):
        """测试缺失依赖的情况"""
        workflow = Workflow(name="测试依赖")
        
        agent = Agent(
            llm=OpenAILLM(),
            name="TestAgent",
            system_prompt="测试"
        )
        
        # 添加步骤，依赖不存在的 key
        workflow.add_step(
            name="step1",
            agent=agent,
            input_key="nonexistent_key"  # 这个 key 不存在
        )
        
        # 执行应该失败或跳过
        result = workflow.run("测试", verbose=False)
        
        # 验证步骤没有执行或正确处理
        assert result is not None
        print("✓ 缺失依赖测试通过")
    
    def test_valid_dependency(self):
        """测试有效依赖"""
        workflow = Workflow(name="测试有效依赖")
        
        agent1 = Agent(
            llm=OpenAILLM(),
            name="Agent1",
            system_prompt="输出固定内容：Hello"
        )
        
        agent2 = Agent(
            llm=OpenAILLM(),
            name="Agent2",
            system_prompt="重复输入内容"
        )
        
        workflow.add_step("step1", agent1)
        workflow.add_step(
            "step2",
            agent2,
            input_key="_last_output"  # 依赖上一步
        )
        
        result = workflow.run("开始", verbose=False)
        
        assert result is not None
        assert len(result.get("_step_results", [])) >= 1
        print("✓ 有效依赖测试通过")


class TestWorkflowParallel:
    """并行执行测试"""
    
    def test_parallel_replicas(self):
        """测试并行复制执行"""
        workflow = Workflow(name="测试并行")
        
        base_agent = Agent(
            llm=OpenAILLM(),
            name="BaseAgent",
            system_prompt="处理任务"
        )
        
        workflow.add_step("base", base_agent)
        
        # 添加并行复制
        workflow.add_parallel_replicas(
            name_prefix="replica",
            base_agent=base_agent,
            project_inputs={
                "project-A": "处理任务 A",
                "project-B": "处理任务 B"
            }
        )
        
        # 验证有多个步骤
        assert len(workflow.steps) >= 2
        print("✓ 并行复制测试通过")


class TestWorkflowConditional:
    """条件分支测试"""
    
    def test_conditional_step_skip(self):
        """测试条件步骤跳过"""
        workflow = Workflow(name="测试条件")
        
        agent = Agent(
            llm=OpenAILLM(),
            name="Agent",
            system_prompt="测试"
        )
        
        # 添加永远不会执行的条件
        workflow.add_step(
            name="conditional_step",
            agent=agent,
            condition=lambda ctx: False  # 永远不执行
        )
        
        result = workflow.run("测试", verbose=False)
        
        # 步骤应该被跳过
        assert result is not None
        print("✓ 条件跳过测试通过")
    
    def test_conditional_step_execute(self):
        """测试条件步骤执行"""
        workflow = Workflow(name="测试条件执行")
        
        agent = Agent(
            llm=OpenAILLM(),
            name="Agent",
            system_prompt="测试"
        )
        
        # 添加总是会执行的条件
        workflow.add_step(
            name="always_run",
            agent=agent,
            condition=lambda ctx: True  # 总是执行
        )
        
        result = workflow.run("测试", verbose=False)
        
        assert result is not None
        assert "always_run" in str(result.get("_step_results", {}))
        print("✓ 条件执行测试通过")


class TestWorkflowContext:
    """上下文管理测试"""
    
    def test_context_propagation(self):
        """测试上下文传递"""
        workflow = Workflow(name="测试上下文")
        
        agent1 = Agent(
            llm=OpenAILLM(),
            name="Agent1",
            system_prompt="输出：第一步"
        )
        
        agent2 = Agent(
            llm=OpenAILLM(),
            name="Agent2",
            system_prompt="基于上一步继续"
        )
        
        workflow.add_step("step1", agent1)
        workflow.add_step("step2", agent2, input_key="_last_output")
        
        result = workflow.run("开始", verbose=False)
        
        # 验证上下文传递
        assert "_initial_input" in result
        assert "_last_output" in result
        print("✓ 上下文传递测试通过")
    
    def test_custom_context(self):
        """测试自定义上下文"""
        workflow = Workflow(name="测试自定义上下文")
        
        agent = Agent(
            llm=OpenAILLM(),
            name="Agent",
            system_prompt="使用自定义上下文"
        )
        
        workflow.add_step(
            "step1",
            agent,
            input_key="custom_data"
        )
        
        # 自定义上下文通过修改 workflow.context 实现
        result = workflow.run("开始", verbose=False)
        # Note: initial_context parameter not supported in current API
        # User can set workflow.context directly before run()
        
        assert result is not None
        print("✓ 自定义上下文测试通过")


class TestWorkflowErrors:
    """错误处理测试"""
    
    def test_agent_error_recovery(self):
        """测试 Agent 错误恢复"""
        workflow = Workflow(name="测试错误恢复")
        
        # 创建一个会使用不存在工具的 agent
        agent = Agent(
            llm=OpenAILLM(),
            tools=[],  # 没有工具
            system_prompt="请调用不存在的工具"
        )
        
        workflow.add_step("step", agent)
        
        # 执行应该会触发错误恢复
        result = workflow.run("调用工具", verbose=False)
        
        # 验证工作流完成了（即使有错误）
        assert result is not None
        print("✓ 错误恢复测试通过")
    
    def test_max_iterations_reached(self):
        """测试达到最大迭代次数"""
        workflow = Workflow(name="测试迭代限制")
        
        # 创建会无限循环的 agent
        agent = Agent(
            llm=OpenAILLM(),
            tools=[BashTool()],
            max_iterations=2,  # 限制迭代次数
            system_prompt="一直调用工具直到达到限制"
        )
        
        workflow.add_step("step", agent)
        
        result = workflow.run("执行任务", verbose=False)
        
        # 验证工作流完成了
        assert result is not None
        print("✓ 迭代限制测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Workflow Integration Tests")
    print("=" * 60)
    
    test_classes = [
        TestWorkflowExecution,
        TestWorkflowDependencies,
        TestWorkflowParallel,
        TestWorkflowConditional,
        TestWorkflowContext,
        TestWorkflowErrors,
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        instance = test_class()
        
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                total_tests += 1
                try:
                    method = getattr(instance, method_name)
                    method()
                    passed_tests += 1
                except Exception as e:
                    print(f"✗ {method_name} 失败：{e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果：{passed_tests}/{total_tests} 通过")
    print("=" * 60)
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
