#!/usr/bin/env python3
"""
Agent 测试脚本

验证所有 builtin agents 的加载、工具配置和领域标签
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from typing import Dict, List
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


class AgentTester:
    """Agent 测试器"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.builtin_agents_dir = Path(__file__).parent.parent / "builtin_agents" / "configs"
    
    def test_agent_loading(self) -> TestResult:
        """测试 1: Agent 配置加载"""
        try:
            yaml_files = list(self.builtin_agents_dir.glob("*.yaml"))
            if not yaml_files:
                return TestResult("Agent 配置加载", False, "未找到 YAML 配置文件")
            
            loaded_count = 0
            for yaml_file in yaml_files:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    if config and 'name' in config:
                        loaded_count += 1
            
            if loaded_count == len(yaml_files):
                return TestResult("Agent 配置加载", True, f"成功加载 {loaded_count} 个 Agent")
            else:
                return TestResult("Agent 配置加载", False, f"仅加载 {loaded_count}/{len(yaml_files)} 个 Agent")
        
        except Exception as e:
            return TestResult("Agent 配置加载", False, str(e))
    
    def test_agent_structure(self) -> TestResult:
        """测试 2: Agent 配置结构完整性"""
        required_fields = ['name', 'version', 'description', 'system_prompt', 'tools', 'max_iterations', 'domains']
        issues = []
        
        for yaml_file in self.builtin_agents_dir.glob("*.yaml"):
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            agent_name = config.get('name', yaml_file.stem)
            for field in required_fields:
                if field not in config:
                    issues.append(f"{agent_name}: 缺少字段 '{field}'")
        
        if issues:
            return TestResult("Agent 配置结构", False, "\n".join(issues[:5]))
        else:
            return TestResult("Agent 配置结构", True, f"所有 {len(list(self.builtin_agents_dir.glob('*.yaml')))} 个 Agent 结构完整")
    
    def test_tools_loading(self) -> TestResult:
        """测试 3: 工具加载"""
        try:
            from core.resource import repo
            import tools  # noqa: F401
            
            all_tools = repo.list_tools()
            if not all_tools:
                return TestResult("工具加载", False, "未注册任何工具")
            
            # 统计使用的工具
            tools_usage = {}
            for yaml_file in self.builtin_agents_dir.glob("*.yaml"):
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                for tool_name in config.get('tools', []):
                    tools_usage[tool_name] = tools_usage.get(tool_name, 0) + 1
            
            # 检查所有引用的工具是否已注册
            missing_tools = []
            for tool_name in tools_usage:
                if tool_name not in all_tools:
                    missing_tools.append(tool_name)
            
            if missing_tools:
                return TestResult("工具加载", False, f"未找到的工具：{', '.join(missing_tools)}")
            else:
                total_refs = sum(tools_usage.values())
                return TestResult("工具加载", True, f"{len(tools_usage)} 种工具被引用 {total_refs} 次")
        
        except Exception as e:
            return TestResult("工具加载", False, str(e))
    
    def test_domain_tags(self) -> TestResult:
        """测试 4: 领域标签"""
        try:
            domains_count = {}
            agents_without_domains = []
            
            for yaml_file in self.builtin_agents_dir.glob("*.yaml"):
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                agent_name = config.get('name', yaml_file.stem)
                domains = config.get('domains', [])
                
                if not domains:
                    agents_without_domains.append(agent_name)
                else:
                    for domain in domains:
                        domains_count[domain] = domains_count.get(domain, 0) + 1
            
            if agents_without_domains:
                return TestResult("领域标签", False, f"缺少领域标签：{', '.join(agents_without_domains)}")
            
            domain_summary = ", ".join([f"{k}({v})" for k, v in sorted(domains_count.items())[:5]])
            return TestResult("领域标签", True, f"{len(domains_count)} 个领域，示例：{domain_summary}")
        
        except Exception as e:
            return TestResult("领域标签", False, str(e))
    
    def test_cli_agent_websearch(self) -> TestResult:
        """测试 5: CLI Agent WebSearchTool 集成"""
        try:
            from core.resource import repo
            import tools  # noqa: F401
            
            cli_config_path = self.builtin_agents_dir / "cli.yaml"
            with open(cli_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            tools_list = config.get('tools', [])
            if 'WebSearchTool' not in tools_list:
                return TestResult("CLI Agent WebSearchTool", False, "CLI Agent 未配置 WebSearchTool")
            
            # 检查工具是否已注册
            if 'WebSearchTool' not in repo.list_tools():
                return TestResult("CLI Agent WebSearchTool", False, "WebSearchTool 未注册到资源仓库")
            
            return TestResult("CLI Agent WebSearchTool", True, "CLI Agent 已配置并可访问 WebSearchTool")
        
        except Exception as e:
            return TestResult("CLI Agent WebSearchTool", False, str(e))
    
    def test_agent_creation(self) -> TestResult:
        """测试 6: Agent 实例创建"""
        try:
            from builtin_agents import create_builtin_agent
            from core.llm import OpenAILLM
            
            llm = OpenAILLM()
            test_agents = ['cli', 'developer', 'planner']
            created = []
            failed = []
            
            for agent_type in test_agents:
                try:
                    agent = create_builtin_agent(agent_type, llm)
                    if agent:
                        created.append(agent_type)
                    else:
                        failed.append(f"{agent_type}(返回 None)")
                except Exception as e:
                    failed.append(f"{agent_type}({str(e)[:30]})")
            
            if failed:
                return TestResult("Agent 实例创建", False, f"失败：{', '.join(failed)}")
            else:
                return TestResult("Agent 实例创建", True, f"成功创建 {len(created)} 个 Agent 实例")
        
        except Exception as e:
            return TestResult("Agent 实例创建", False, str(e))
    
    def run_all_tests(self):
        """运行所有测试"""
        tests = [
            self.test_agent_loading,
            self.test_agent_structure,
            self.test_tools_loading,
            self.test_domain_tags,
            self.test_cli_agent_websearch,
            self.test_agent_creation,
        ]
        
        print("\n" + "=" * 70)
        print("Agent 系统测试")
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
    tester = AgentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
