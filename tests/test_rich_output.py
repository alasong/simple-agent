#!/usr/bin/env python3
"""
富文本输出测试

验证 RichOutput 模块的各项功能
"""

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


class MockSwarmResult:
    """模拟 SwarmResult 用于测试"""
    
    def __init__(self):
        self.success = True
        self.output = "测试输出内容"
        self.tasks_completed = 5
        self.tasks_failed = 1
        self.total_iterations = 10
        self.execution_time = 3.14159
        self.agent_stats = {
            "agents": 3,
            "load_distribution": {
                "Agent-A": 2,
                "Agent-B": 2,
                "Agent-C": 2
            },
            "avg_load": 2.0
        }


class RichOutputTester:
    """富文本输出测试器"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.console_available = False
    
    def test_rich_import(self) -> TestResult:
        """测试 1: Rich 库导入"""
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            self.console_available = True
            return TestResult("Rich 库导入", True, "Rich 库可用")
        except ImportError as e:
            return TestResult("Rich 库导入", False, f"Rich 库不可用：{e}")
    
    def test_rich_output_initialization(self) -> TestResult:
        """测试 2: RichOutput 初始化"""
        try:
            from core.rich_output import RichOutput
            
            rich = RichOutput(use_color=True)
            
            if rich.console is None and self.console_available:
                return TestResult("RichOutput 初始化", False, "Console 未正确初始化")
            
            return TestResult("RichOutput 初始化", True, "RichOutput 实例创建成功")
        except Exception as e:
            return TestResult("RichOutput 初始化", False, f"初始化失败：{e}")
    
    def test_print_methods(self) -> TestResult:
        """测试 3: 打印方法"""
        try:
            from core.rich_output import RichOutput
            
            rich = RichOutput(use_color=True)
            
            # 测试各种打印方法
            rich.print_header("测试标题", "副标题")
            rich.print_success("成功消息")
            rich.print_error("错误消息")
            rich.print_warning("警告消息")
            rich.print_info("信息消息")
            
            return TestResult("打印方法", True, "所有打印方法执行成功")
        except Exception as e:
            return TestResult("打印方法", False, f"打印方法失败：{e}")
    
    def test_show_swarm_result(self) -> TestResult:
        """测试 4: Swarm 结果展示"""
        try:
            from core.rich_output import RichOutput, show_swarm_result
            
            rich = RichOutput(use_color=True)
            result = MockSwarmResult()
            
            # 测试实例方法
            rich.show_swarm_result(result, "测试任务：验证 Swarm 结果展示功能")
            
            # 测试全局函数
            show_swarm_result(result, "测试任务（全局函数）")
            
            return TestResult("Swarm 结果展示", True, "Swarm 结果展示成功")
        except Exception as e:
            return TestResult("Swarm 结果展示", False, f"展示失败：{e}")
    
    def test_show_task_table(self) -> TestResult:
        """测试 5: 任务表格展示"""
        try:
            from core.rich_output import RichOutput, TaskDisplayData
            
            rich = RichOutput(use_color=True)
            
            # 创建测试任务数据
            tasks = [
                TaskDisplayData(
                    id="1",
                    description="分析需求并设计系统架构",
                    status="completed",
                    agent="Developer",
                    result="完成系统架构设计文档",
                    duration=1.5
                ),
                TaskDisplayData(
                    id="2",
                    description="实现核心功能模块",
                    status="completed",
                    agent="Developer",
                    result="已实现主要功能",
                    duration=2.3
                ),
                TaskDisplayData(
                    id="3",
                    description="编写单元测试",
                    status="running",
                    agent="Tester",
                    duration=0.5
                ),
                TaskDisplayData(
                    id="4",
                    description="代码审查",
                    status="pending",
                    agent="Reviewer"
                ),
                TaskDisplayData(
                    id="5",
                    description="部署到生产环境",
                    status="failed",
                    agent="DevOps",
                    error="部署脚本执行失败：权限不足"
                ),
            ]
            
            # 测试任务表格
            rich.show_task_table(tasks, "任务执行状态")
            
            # 测试并发任务展示
            rich.show_concurrent_tasks(tasks[:3])
            
            return TestResult("任务表格展示", True, "任务表格展示成功")
        except Exception as e:
            return TestResult("任务表格展示", False, f"展示失败：{e}")
    
    def test_show_code(self) -> TestResult:
        """测试 6: 代码展示"""
        try:
            from core.rich_output import RichOutput
            
            rich = RichOutput(use_color=True)
            
            code = """
def hello_world():
    print("Hello, World!")
    
if __name__ == "__main__":
    hello_world()
"""
            rich.show_code(code, language="python")
            
            return TestResult("代码展示", True, "代码展示成功")
        except Exception as e:
            return TestResult("代码展示", False, f"展示失败：{e}")
    
    def test_show_markdown(self) -> TestResult:
        """测试 7: Markdown 展示"""
        try:
            from core.rich_output import RichOutput
            
            rich = RichOutput(use_color=True)
            
            markdown = """
# 测试标题

这是一个**测试**文档

## 列表

- 项目 1
- 项目 2
- 项目 3

## 代码

```python
print("Hello")
```
"""
            rich.show_markdown(markdown)
            
            return TestResult("Markdown 展示", True, "Markdown 展示成功")
        except Exception as e:
            return TestResult("Markdown 展示", False, f"展示失败：{e}")
    
    def test_global_functions(self) -> TestResult:
        """测试 8: 全局函数"""
        try:
            from core.rich_output import (
                print_header, print_success, print_error,
                print_warning, print_info, get_rich_output
            )
            
            # 测试全局函数
            print_header("全局函数测试")
            print_success("成功")
            print_error("错误")
            print_warning("警告")
            print_info("信息")
            
            # 测试获取全局实例
            rich = get_rich_output()
            if not isinstance(rich, object):
                return TestResult("全局函数", False, "全局实例获取失败")
            
            return TestResult("全局函数", True, "全局函数调用成功")
        except Exception as e:
            return TestResult("全局函数", False, f"调用失败：{e}")
    
    def test_task_display_data(self) -> TestResult:
        """测试 9: TaskDisplayData 数据结构"""
        try:
            from core.rich_output import TaskDisplayData
            
            # 创建任务数据
            task = TaskDisplayData(
                id="T1",
                description="测试任务",
                status="completed",
                agent="TestAgent",
                result="测试结果",
                duration=1.23
            )
            
            # 验证属性
            assert task.id == "T1"
            assert task.description == "测试任务"
            assert task.status == "completed"
            assert task.agent == "TestAgent"
            assert task.result == "测试结果"
            assert task.duration == 1.23
            
            return TestResult("TaskDisplayData", True, "数据结构创建和验证成功")
        except Exception as e:
            return TestResult("TaskDisplayData", False, f"数据结构失败：{e}")
    
    def test_fallback_mode(self) -> TestResult:
        """测试 10: 降级模式（无 Rich）"""
        try:
            # 测试禁用颜色模式
            from core.rich_output import RichOutput
            
            rich = RichOutput(use_color=False)
            
            # 在降级模式下，所有方法应该仍能工作
            rich.print_header("降级测试")
            rich.print_success("成功")
            rich.print_error("错误")
            
            return TestResult("降级模式", True, "降级模式工作正常")
        except Exception as e:
            return TestResult("降级模式", False, f"降级失败：{e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        tests = [
            self.test_rich_import,
            self.test_rich_output_initialization,
            self.test_print_methods,
            self.test_show_swarm_result,
            self.test_show_task_table,
            self.test_show_code,
            self.test_show_markdown,
            self.test_global_functions,
            self.test_task_display_data,
            self.test_fallback_mode,
        ]
        
        print("\n" + "=" * 70)
        print("富文本输出测试")
        print("=" * 70)
        print()
        
        for test_func in tests:
            result = test_func()
            self.results.append(result)
            
            status = "✓" if result.passed else "✗"
            color = "green" if result.passed else "red"
            print(f"{status} {result.name:25} {result.message}")
        
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
    tester = RichOutputTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
