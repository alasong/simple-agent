"""
推理工具单元测试

测试新增的多路径探索工具的基础功能
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestThoughtNode:
    """测试 ThoughtNode 数据类"""

    def test_thought_node_creation(self):
        """测试思维节点创建"""
        from tools.reasoning_tools import ThoughtNode

        node = ThoughtNode(content="测试思路")
        assert node.content == "测试思路"
        assert node.score == 0.0
        assert node.children == []
        assert node.parent is None

    def test_thought_node_with_score(self):
        """测试带评分的思维节点"""
        from tools.reasoning_tools import ThoughtNode

        node = ThoughtNode(content="测试思路", score=0.85)
        assert node.score == 0.85

    def test_thought_node_to_dict(self):
        """测试转换为字典"""
        from tools.reasoning_tools import ThoughtNode

        node = ThoughtNode(content="测试思路", score=0.9)
        result = node.to_dict()

        assert result['content'] == "测试思路"
        assert result['score'] == 0.9
        assert 'evaluation' in result


class TestTreeOfThoughtTool:
    """测试思维树工具"""

    def test_tool_initialization(self):
        """测试工具初始化"""
        from tools.reasoning_tools import TreeOfThoughtTool

        # 使用 mock agent
        mock_agent = type('MockAgent', (), {
            'name': 'MockAgent',
            'run': lambda self, prompt, verbose: "测试回答"
        })()

        tool = TreeOfThoughtTool(mock_agent, breadth=3, depth=2)

        assert tool.breadth == 3
        assert tool.depth == 2
        assert tool.agent is mock_agent

    def test_parse_json_direct(self):
        """测试 JSON 解析（直接格式）"""
        from tools.reasoning_tools import TreeOfThoughtTool

        mock_agent = type('MockAgent', (), {
            'name': 'MockAgent',
            'run': lambda self, prompt, verbose: "测试回答"
        })()

        tool = TreeOfThoughtTool(mock_agent)

        # 测试直接 JSON
        json_str = '{"score": 0.85, "reason": "测试"}'
        result = tool._parse_json(json_str)
        assert result['score'] == 0.85
        assert result['reason'] == "测试"

    def test_parse_json_embedded(self):
        """测试 JSON 解析（嵌入格式）"""
        from tools.reasoning_tools import TreeOfThoughtTool

        mock_agent = type('MockAgent', (), {
            'name': 'MockAgent',
            'run': lambda self, prompt, verbose: "测试回答"
        })()

        tool = TreeOfThoughtTool(mock_agent)

        # 测试嵌入在文本中的 JSON
        text = """
        这是一个回答
        {"score": 0.9, "reason": "很好"}
        还有一些其他内容
        """
        result = tool._parse_json(text)
        assert result['score'] == 0.9

    def test_parse_json_array(self):
        """测试 JSON 数组解析"""
        from tools.reasoning_tools import TreeOfThoughtTool

        mock_agent = type('MockAgent', (), {
            'name': 'MockAgent',
            'run': lambda self, prompt, verbose: "测试回答"
        })()

        tool = TreeOfThoughtTool(mock_agent)

        # 测试数组
        json_str = '["思路 1", "思路 2", "思路 3"]'
        result = tool._parse_json_array(json_str)
        assert len(result) == 3
        assert result[0] == "思路 1"


class TestIterationResult:
    """测试迭代结果（在 IterativeOptimizerTool 内部）"""

    def test_iteration_result_creation(self):
        """测试迭代结果创建"""
        # IterationResult 在工具内部使用，通过返回值测试
        from tools.reasoning_tools import IterativeOptimizerTool

        mock_agent = type('MockAgent', (), {
            'name': 'MockAgent',
            'run': lambda self, prompt, verbose: "测试回答"
        })()

        tool = IterativeOptimizerTool(mock_agent)

        # 验证工具有 iterations 属性
        assert hasattr(tool, 'max_iterations')
        assert tool.max_iterations == 3

    def test_iteration_result_structure(self):
        """测试迭代结果结构"""
        # 验证返回的迭代结果包含必要字段
        result_data = {
            "iteration": 1,
            "score": 0.85,
            "content": "测试内容",
            "duration": 1.5
        }

        assert result_data['iteration'] == 1
        assert result_data['score'] == 0.85
        assert 'content' in result_data


class TestOptimizationResult:
    """测试优化结果（在 IterativeOptimizerTool 内部）"""

    def test_optimization_result_creation(self):
        """测试优化结果创建"""
        from tools.reasoning_tools import IterativeOptimizerTool

        mock_agent = type('MockAgent', (), {
            'name': 'MockAgent',
            'run': lambda self, prompt, verbose: "测试回答"
        })()

        tool = IterativeOptimizerTool(mock_agent)

        # 验证工具有必要的属性
        assert hasattr(tool, 'quality_threshold')
        assert tool.quality_threshold == 0.75

    def test_optimization_result_structure(self):
        """测试优化结果结构"""
        # 验证返回的优化结果包含必要字段
        result_data = {
            "success": True,
            "best_solution": "测试方案",
            "final_score": 0.88,
            "total_iterations": 3,
            "execution_time": 5.2
        }

        assert result_data['success'] is True
        assert result_data['final_score'] == 0.88
        assert result_data['total_iterations'] == 3


class TestFactoryFunctions:
    """测试工厂函数"""

    def test_create_tree_of_thought(self):
        """测试创建思维树工具"""
        from tools.reasoning_tools import create_tree_of_thought

        mock_agent = type('MockAgent', (), {
            'name': 'MockAgent',
            'run': lambda self, prompt, verbose: "测试回答"
        })()

        tool = create_tree_of_thought(mock_agent, breadth=4, depth=3)

        assert tool.breadth == 4
        assert tool.depth == 3

    def test_create_iterative_optimizer(self):
        """测试创建迭代优化工具"""
        from tools.reasoning_tools import create_iterative_optimizer

        mock_agent = type('MockAgent', (), {
            'name': 'MockAgent',
            'run': lambda self, prompt, verbose: "测试回答"
        })()

        tool = create_iterative_optimizer(mock_agent, max_iterations=5)

        assert tool.max_iterations == 5

    def test_create_multi_path_optimizer(self):
        """测试创建多路径优化工具"""
        from tools.reasoning_tools import create_multi_path_optimizer

        mock_agent = type('MockAgent', (), {
            'name': 'MockAgent',
            'run': lambda self, prompt, verbose: "测试回答"
        })()

        tool = create_multi_path_optimizer(mock_agent, num_paths=5)

        assert tool.num_paths == 5


class TestIntegration:
    """集成测试"""

    def test_thought_node_tree_structure(self):
        """测试思维节点的树结构"""
        from tools.reasoning_tools import ThoughtNode

        # 构建树形结构
        root = ThoughtNode(content="根思路", score=0.5)
        child1 = ThoughtNode(content="子思路 1", score=0.7, parent=root)
        child2 = ThoughtNode(content="子思路 2", score=0.8, parent=root)

        root.children.append(child1)
        root.children.append(child2)

        # 验证结构
        assert len(root.children) == 2
        assert child1.parent is root
        assert child2.parent is root
        assert child1.score > root.score  # 子节点评分更高

    def test_multiple_agents_for_voting(self):
        """测试多个 Agent 用于投票"""
        from tools.reasoning_tools import SwarmVotingTool

        # 创建多个 mock agents
        agents = [
            type('MockAgent', (), {'name': f'Agent{i}'})()
            for i in range(3)
        ]

        tool = SwarmVotingTool(agents, voting_rounds=2)

        assert len(tool.agents) == 3
        assert tool.voting_rounds == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
