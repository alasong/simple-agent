#!/usr/bin/env python3
"""
工具执行测试脚本

验证各个工具的功能是否正常
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Callable
from dataclasses import dataclass


def cprint(text, color=None, attrs=None):
    """简化版 cprint"""
    print(text)


@dataclass
class TestResult:
    """测试结果"""
    name: str
    passed: bool
    message: str = ""
    duration_ms: float = 0


class ToolTester:
    """工具测试器"""
    
    def __init__(self):
        self.results: List[TestResult] = []
    
    def test_websearch_tool(self) -> TestResult:
        """测试 WebSearchTool"""
        try:
            from core.resource import repo
            import tools  # noqa: F401
            
            # 获取工具
            web_search_tool = repo.get_tool("WebSearchTool")
            if not web_search_tool:
                return TestResult("WebSearchTool", False, "工具未注册")
            
            # 实例化工具
            tool_instance = web_search_tool()
            
            # 检查工具属性
            if not tool_instance.name:
                return TestResult("WebSearchTool", False, "缺少 name 属性")
            
            if not tool_instance.description:
                return TestResult("WebSearchTool", False, "缺少 description 属性")
            
            if not tool_instance.parameters:
                return TestResult("WebSearchTool", False, "缺少 parameters 定义")
            
            # 检查参数定义
            params = tool_instance.parameters
            if 'properties' not in params:
                return TestResult("WebSearchTool", False, "parameters 缺少 properties")
            
            if 'query' not in params['properties']:
                return TestResult("WebSearchTool", False, "缺少 query 参数")
            
            if 'query' not in params.get('required', []):
                return TestResult("WebSearchTool", False, "query 不是必需参数")
            
            return TestResult("WebSearchTool", True, f"工具属性完整，描述：{tool_instance.description[:30]}...")
        
        except Exception as e:
            return TestResult("WebSearchTool", False, str(e))
    
    def test_invoke_agent_tool(self) -> TestResult:
        """测试 InvokeAgentTool"""
        try:
            from core.resource import repo
            import tools  # noqa: F401
            
            tool_class = repo.get_tool("InvokeAgentTool")
            if not tool_class:
                return TestResult("InvokeAgentTool", False, "工具未注册")
            
            tool_instance = tool_class()
            
            if not tool_instance.name:
                return TestResult("InvokeAgentTool", False, "缺少 name 属性")
            
            # 检查参数
            params = tool_instance.parameters
            if 'agent_type' not in params.get('properties', {}):
                return TestResult("InvokeAgentTool", False, "缺少 agent_type 参数")
            
            if 'task' not in params.get('properties', {}):
                return TestResult("InvokeAgentTool", False, "缺少 task 参数")
            
            return TestResult("InvokeAgentTool", True, f"工具属性完整")
        
        except Exception as e:
            return TestResult("InvokeAgentTool", False, str(e))
    
    def test_create_workflow_tool(self) -> TestResult:
        """测试 CreateWorkflowTool"""
        try:
            from core.resource import repo
            import tools  # noqa: F401
            
            tool_class = repo.get_tool("CreateWorkflowTool")
            if not tool_class:
                return TestResult("CreateWorkflowTool", False, "工具未注册")
            
            tool_instance = tool_class()
            
            if not tool_instance.name:
                return TestResult("CreateWorkflowTool", False, "缺少 name 属性")
            
            # 检查参数
            params = tool_instance.parameters
            if 'workflow_name' not in params.get('properties', {}):
                return TestResult("CreateWorkflowTool", False, "缺少 workflow_name 参数")
            
            if 'steps' not in params.get('properties', {}):
                return TestResult("CreateWorkflowTool", False, "缺少 steps 参数")
            
            return TestResult("CreateWorkflowTool", True, f"工具属性完整")
        
        except Exception as e:
            return TestResult("CreateWorkflowTool", False, str(e))
    
    def test_read_file_tool(self) -> TestResult:
        """测试 ReadFileTool"""
        try:
            from core.resource import repo
            import tools  # noqa: F401
            
            tool_class = repo.get_tool("ReadFileTool")
            if not tool_class:
                return TestResult("ReadFileTool", False, "工具未注册")
            
            tool_instance = tool_class()
            
            if not tool_instance.name:
                return TestResult("ReadFileTool", False, "缺少 name 属性")
            
            return TestResult("ReadFileTool", True, f"工具属性完整")
        
        except Exception as e:
            return TestResult("ReadFileTool", False, str(e))
    
    def test_write_file_tool(self) -> TestResult:
        """测试 WriteFileTool"""
        try:
            from core.resource import repo
            import tools  # noqa: F401
            
            tool_class = repo.get_tool("WriteFileTool")
            if not tool_class:
                return TestResult("WriteFileTool", False, "工具未注册")
            
            tool_instance = tool_class()
            
            if not tool_instance.name:
                return TestResult("WriteFileTool", False, "缺少 name 属性")
            
            return TestResult("WriteFileTool", True, f"工具属性完整")
        
        except Exception as e:
            return TestResult("WriteFileTool", False, str(e))
    
    def test_list_agents_tool(self) -> TestResult:
        """测试 ListAgentsTool"""
        try:
            from core.resource import repo
            import tools  # noqa: F401
            
            tool_class = repo.get_tool("ListAgentsTool")
            if not tool_class:
                return TestResult("ListAgentsTool", False, "工具未注册")
            
            tool_instance = tool_class()
            
            if not tool_instance.name:
                return TestResult("ListAgentsTool", False, "缺少 name 属性")
            
            return TestResult("ListAgentsTool", True, f"工具属性完整")
        
        except Exception as e:
            return TestResult("ListAgentsTool", False, str(e))
    
    def run_all_tests(self):
        """运行所有工具测试"""
        tests = [
            self.test_websearch_tool,
            self.test_invoke_agent_tool,
            self.test_create_workflow_tool,
            self.test_read_file_tool,
            self.test_write_file_tool,
            self.test_list_agents_tool,
        ]
        
        print("\n" + "=" * 70)
        print("工具执行测试")
        print("=" * 70)
        print()
        
        for test_func in tests:
            result = test_func()
            self.results.append(result)
            
            status = "✓" if result.passed else "✗"
            color = "green" if result.passed else "red"
            print(f"{status} {result.name:20} {result.message}")
        
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
    tester = ToolTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
