#!/usr/bin/env python3
"""
Swarm 并发执行测试

验证多任务同时下发和并行执行能力
"""

import asyncio
import time
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List
from dataclasses import dataclass


@dataclass
class TestResult:
    """测试结果"""
    name: str
    passed: bool
    message: str = ""
    duration_ms: float = 0


class TimingMockAgent:
    """带计时的 Mock Agent，用于测试并发执行"""
    
    def __init__(self, name: str, delay: float = 0.5):
        self.name = name
        self.instance_id = name
        self.description = f"通用 Agent，延迟 {delay}秒"
        self.delay = delay
        self.executed_tasks: List[str] = []
        self.execution_times: List[float] = []
        self.run_count = 0
    
    def run(self, user_input: str, verbose: bool = False) -> str:
        """模拟执行，带固定延迟"""
        start = time.time()
        time.sleep(self.delay)  # 模拟执行耗时
        elapsed = time.time() - start
        
        self.run_count += 1
        self.executed_tasks.append(user_input[:50])
        self.execution_times.append(elapsed)
        
        return f"[{self.name}] 完成：{user_input[:30]} (耗时:{elapsed:.2f}s)"


class ConcurrentSwarmTester:
    """Swarm 并发测试器"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results: List[TestResult] = []
    
    def test_concurrent_no_dependencies(self) -> TestResult:
        """
        测试 1: 无依赖任务的并发执行
        
        创建 3 个无依赖任务，验证是否并发执行
        预期：总耗时接近单个任务耗时（~0.5 秒），而不是累加（~1.5 秒）
        """
        from swarm.orchestrator import SwarmOrchestrator
        from swarm.scheduler import Task
        
        try:
            # 创建 3 个无依赖任务
            tasks = [
                Task(id="1", description="任务 1: 分析需求", dependencies=[], required_skills=[]),
                Task(id="2", description="任务 2: 设计方案", dependencies=[], required_skills=[]),
                Task(id="3", description="任务 3: 编写文档", dependencies=[], required_skills=[]),
            ]
            
            # 创建 3 个 Agent，每个延迟 0.5 秒
            agents = [TimingMockAgent(f"A{i}", delay=0.5) for i in range(3)]
            
            # 创建 Orchestrator（禁用富文本输出以避免依赖问题）
            orchestrator = SwarmOrchestrator(
                agent_pool=agents,
                verbose=self.verbose,
                use_rich_output=False
            )
            orchestrator._build_task_graph(tasks)
            
            # 记录开始时间
            start_time = time.time()
            
            # 执行 - 直接调用 _execute_loop
            async def run():
                # 手动设置运行状态
                orchestrator._running = True
                orchestrator._iteration = 0
                orchestrator._start_time = start_time
                return await orchestrator._execute_loop("并发测试：无依赖任务")
            
            result = asyncio.run(run())
            
            # 计算总耗时
            elapsed = time.time() - start_time
            
            # 验证
            if result.tasks_completed != 3:
                return TestResult(
                    "并发执行（无依赖）",
                    False,
                    f"期望完成 3 个任务，实际完成 {result.tasks_completed}",
                    elapsed * 1000
                )
            
            # 并发执行时，总时间应接近 0.5 秒（允许 1.2 秒的误差）
            if elapsed > 1.2:
                return TestResult(
                    "并发执行（无依赖）",
                    False,
                    f"并发执行失败：耗时{elapsed:.2f}秒（预期<1.2 秒，实际{elapsed:.2f}秒）",
                    elapsed * 1000
                )
            
            # 验证每个 Agent 只执行了一个任务
            for agent in agents:
                if agent.run_count != 1:
                    return TestResult(
                        "并发执行（无依赖）",
                        False,
                        f"Agent {agent.name} 执行了{agent.run_count}个任务（预期 1 个）",
                        elapsed * 1000
                    )
            
            return TestResult(
                "并发执行（无依赖）",
                True,
                f"3 个任务并发执行，耗时{elapsed:.2f}秒（串行预期 1.5 秒）",
                elapsed * 1000
            )
        
        except Exception as e:
            return TestResult(
                "并发执行（无依赖）",
                False,
                f"执行异常：{str(e)}",
                0
            )
    
    def test_sequential_with_dependencies(self) -> TestResult:
        """
        测试 2: 有依赖任务的顺序执行
        
        创建 3 个有依赖关系的任务，验证顺序执行
        任务 1 -> 任务 2 -> 任务 3
        """
        from swarm.orchestrator import SwarmOrchestrator
        from swarm.scheduler import Task
        
        try:
            # 创建有依赖的任务链
            tasks = [
                Task(id="1", description="任务 1: 分析需求", dependencies=[], required_skills=[]),
                Task(id="2", description="任务 2: 设计方案", dependencies=["1"], required_skills=[]),
                Task(id="3", description="任务 3: 实现功能", dependencies=["2"], required_skills=[]),
            ]
            
            agents = [TimingMockAgent("SequentialAgent", delay=0.3)]
            
            orchestrator = SwarmOrchestrator(
                agent_pool=agents,
                verbose=self.verbose,
                use_rich_output=False
            )
            orchestrator._build_task_graph(tasks)
            
            start_time = time.time()
            
            async def run():
                orchestrator._running = True
                orchestrator._iteration = 0
                orchestrator._start_time = start_time
                return await orchestrator._execute_loop("顺序测试：有依赖任务")
            
            result = asyncio.run(run())
            elapsed = time.time() - start_time
            
            # 验证任务完成数
            if result.tasks_completed != 3:
                return TestResult(
                    "顺序执行（有依赖）",
                    False,
                    f"期望完成 3 个任务，实际完成 {result.tasks_completed}",
                    elapsed * 1000
                )
            
            # 顺序执行时，总时间应接近 0.9 秒（3 * 0.3）
            if elapsed < 0.8:
                return TestResult(
                    "顺序执行（有依赖）",
                    False,
                    f"顺序执行异常：耗时{elapsed:.2f}秒（预期>0.8 秒）",
                    elapsed * 1000
                )
            
            return TestResult(
                "顺序执行（有依赖）",
                True,
                f"3 个任务顺序执行，耗时{elapsed:.2f}秒（预期~0.9 秒）",
                elapsed * 1000
            )
        
        except Exception as e:
            return TestResult(
                "顺序执行（有依赖）",
                False,
                f"执行异常：{str(e)}",
                0
            )
    
    def test_mixed_dependencies(self) -> TestResult:
        """
        测试 3: 混合依赖关系
        
        任务结构：
        任务 1 (独立)
        任务 2 (独立)
        任务 3 (依赖任务 1)
        任务 4 (依赖任务 2)
        
        预期：任务 1 和 2 并发，任务 3 和 4 并发
        """
        from swarm.orchestrator import SwarmOrchestrator
        from swarm.scheduler import Task
        
        try:
            tasks = [
                Task(id="1", description="任务 1: 独立任务 A", dependencies=[], required_skills=[]),
                Task(id="2", description="任务 2: 独立任务 B", dependencies=[], required_skills=[]),
                Task(id="3", description="任务 3: 依赖任务 1", dependencies=["1"], required_skills=[]),
                Task(id="4", description="任务 4: 依赖任务 2", dependencies=["2"], required_skills=[]),
            ]
            
            agents = [TimingMockAgent(f"A{i}", delay=0.3) for i in range(4)]
            
            orchestrator = SwarmOrchestrator(
                agent_pool=agents,
                verbose=self.verbose,
                use_rich_output=False
            )
            orchestrator._build_task_graph(tasks)
            
            start_time = time.time()
            
            async def run():
                orchestrator._running = True
                orchestrator._iteration = 0
                orchestrator._start_time = start_time
                return await orchestrator._execute_loop("混合依赖测试")
            
            result = asyncio.run(run())
            elapsed = time.time() - start_time
            
            if result.tasks_completed != 4:
                return TestResult(
                    "混合依赖执行",
                    False,
                    f"期望完成 4 个任务，实际完成 {result.tasks_completed}",
                    elapsed * 1000
                )
            
            # 理想并发时间：2 轮 * 0.3 秒 = 0.6 秒
            if elapsed > 1.0:
                return TestResult(
                    "混合依赖执行",
                    False,
                    f"并发执行不足：耗时{elapsed:.2f}秒（预期<1.0 秒）",
                    elapsed * 1000
                )
            
            return TestResult(
                "混合依赖执行",
                True,
                f"4 个任务（2 轮并发）执行，耗时{elapsed:.2f}秒",
                elapsed * 1000
            )
        
        except Exception as e:
            return TestResult(
                "混合依赖执行",
                False,
                f"执行异常：{str(e)}",
                0
            )
    
    def test_concurrent_with_multiple_agents(self) -> TestResult:
        """
        测试 4: 多 Agent 并发
        
        5 个任务，2 个 Agent，验证任务分配和并发
        """
        from swarm.orchestrator import SwarmOrchestrator
        from swarm.scheduler import Task
        
        try:
            tasks = [
                Task(id="1", description="任务 1", dependencies=[], required_skills=[]),
                Task(id="2", description="任务 2", dependencies=[], required_skills=[]),
                Task(id="3", description="任务 3", dependencies=[], required_skills=[]),
                Task(id="4", description="任务 4", dependencies=[], required_skills=[]),
                Task(id="5", description="任务 5", dependencies=[], required_skills=[]),
            ]
            
            # 2 个 Agent
            agents = [
                TimingMockAgent("Agent-A", delay=0.3),
                TimingMockAgent("Agent-B", delay=0.3),
            ]
            
            orchestrator = SwarmOrchestrator(
                agent_pool=agents,
                verbose=self.verbose,
                use_rich_output=False
            )
            orchestrator._build_task_graph(tasks)
            
            start_time = time.time()
            
            async def run():
                orchestrator._running = True
                orchestrator._iteration = 0
                orchestrator._start_time = start_time
                return await orchestrator._execute_loop("多 Agent 并发测试")
            
            result = asyncio.run(run())
            elapsed = time.time() - start_time
            
            if result.tasks_completed != 5:
                return TestResult(
                    "多 Agent 并发",
                    False,
                    f"期望完成 5 个任务，实际完成 {result.tasks_completed}",
                    elapsed * 1000
                )
            
            # 验证负载均衡
            stats = orchestrator.scheduler.get_agent_stats()
            
            # 理想时间：3 轮 * 0.3 秒 ≈ 0.9 秒（考虑取整分配）
            if elapsed > 1.2:
                return TestResult(
                    "多 Agent 并发",
                    False,
                    f"并发效率低：耗时{elapsed:.2f}秒（预期<1.2 秒）",
                    elapsed * 1000
                )
            
            return TestResult(
                "多 Agent 并发",
                True,
                f"5 个任务由 2 个 Agent 并发执行，耗时{elapsed:.2f}秒",
                elapsed * 1000
            )
        
        except Exception as e:
            return TestResult(
                "多 Agent 并发",
                False,
                f"执行异常：{str(e)}",
                0
            )
    
    def test_task_execution_order(self) -> TestResult:
        """
        测试 5: 任务执行顺序验证
        
        验证依赖关系是否正确维护
        """
        from swarm.orchestrator import SwarmOrchestrator
        from swarm.scheduler import Task, TaskStatus
        
        try:
            execution_order = []
            
            class RecordingAgent:
                def __init__(self, name):
                    self.name = name
                    self.instance_id = name
                    self.description = "记录 Agent"
                
                def run(self, user_input, verbose=False):
                    # 记录执行顺序
                    task_id = user_input.split(":")[0].strip() if ":" in user_input else "unknown"
                    execution_order.append(task_id)
                    return f"完成：{task_id}"
            
            tasks = [
                Task(id="A", description="A: 第一步", dependencies=[], required_skills=[]),
                Task(id="B", description="B: 依赖 A", dependencies=["A"], required_skills=[]),
                Task(id="C", description="C: 依赖 B", dependencies=["B"], required_skills=[]),
            ]
            
            agent = RecordingAgent("Recorder")
            
            orchestrator = SwarmOrchestrator(
                agent_pool=[agent],
                verbose=False,
                use_rich_output=False
            )
            orchestrator._build_task_graph(tasks)
            
            async def run():
                orchestrator._running = True
                orchestrator._iteration = 0
                orchestrator._start_time = time.time()
                return await orchestrator._execute_loop("顺序验证测试")
            
            result = asyncio.run(run())
            
            # 验证执行顺序
            expected_order = ["A", "B", "C"]
            
            if execution_order != expected_order:
                return TestResult(
                    "任务执行顺序",
                    False,
                    f"执行顺序错误：期望{expected_order}，实际{execution_order}",
                    0
                )
            
            return TestResult(
                "任务执行顺序",
                True,
                f"执行顺序正确：{' -> '.join(execution_order)}",
                0
            )
        
        except Exception as e:
            return TestResult(
                "任务执行顺序",
                False,
                f"执行异常：{str(e)}",
                0
            )
    
    def run_all_tests(self):
        """运行所有并发测试"""
        tests = [
            self.test_concurrent_no_dependencies,
            self.test_sequential_with_dependencies,
            self.test_mixed_dependencies,
            self.test_concurrent_with_multiple_agents,
            self.test_task_execution_order,
        ]
        
        print("\n" + "=" * 70)
        print("Swarm 并发执行测试")
        print("=" * 70)
        print()
        
        for test_func in tests:
            result = test_func()
            self.results.append(result)
            
            status = "✓" if result.passed else "✗"
            color = "green" if result.passed else "red"
            
            duration_str = f" ({result.duration_ms:.0f}ms)" if result.duration_ms > 0 else ""
            print(f"{status} {result.name:25} {result.message}{duration_str}")
        
        print()
        print("=" * 70)
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        if passed == total:
            print(f"✓ 全部通过 ({passed}/{total})")
        else:
            print(f"✗ {passed}/{total} 通过")
            failed_tests = [r for r in self.results if not r.passed]
            for ft in failed_tests:
                print(f"  - {ft.name}: {ft.message}")
        
        print("=" * 70)
        print()
        
        return passed == total


def main():
    """主函数"""
    tester = ConcurrentSwarmTester(verbose=False)
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
