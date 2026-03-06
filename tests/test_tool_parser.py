"""
测试工具调用解析器
"""

import sys
sys.path.insert(0, '/home/song/simple-agent')

from core.tool_parser import ToolCallParser


def test_python_like():
    """测试 Python-like 格式解析"""
    parser = ToolCallParser()
    
    # 测试用例 1: 单个参数
    content1 = '我需要搜索北京的最新天气信息。\n\n[WebSearchTool(query="北京天气")]'
    result1 = parser.parse(content1)
    
    assert len(result1) == 1, f"应该解析出 1 个工具调用，实际 {len(result1)}"
    assert result1[0]["name"] == "WebSearchTool", f"工具名应该是 WebSearchTool, 实际 {result1[0]['name']}"
    assert result1[0]["arguments"] == {"query": "北京天气"}, f"参数错误：{result1[0]['arguments']}"
    print("✓ Python-like 格式 (单参数) 测试通过")
    
    # 测试用例 2: 多个参数
    content2 = '[WebSearchTool(query="北京天气", date="2026-03-06")]'
    result2 = parser.parse(content2)
    
    assert len(result2) == 1
    assert result2[0]["name"] == "WebSearchTool"
    assert result2[0]["arguments"]["query"] == "北京天气"
    assert result2[0]["arguments"]["date"] == "2026-03-06"
    print("✓ Python-like 格式 (多参数) 测试通过")


def test_json_format():
    """测试 JSON 格式解析"""
    parser = ToolCallParser()
    
    content = '让我调用工具 {"name":"GetCurrentDateTool","arguments":{}}'
    result = parser.parse(content)
    
    assert len(result) == 1, f"应该解析出 1 个工具调用，实际 {len(result)}"
    assert result[0]["name"] == "GetCurrentDateTool", f"工具名错误：{result[0]['name']}"
    assert result[0]["arguments"] == {}, f"参数应该为空字典：{result[0]['arguments']}"
    print("✓ JSON 格式测试通过")


def test_xml_format():
    """测试 XML 格式解析"""
    parser = ToolCallParser()
    
    content = '''让我查询天气
<function_calls>
<invoke name="WebSearchTool">
</invoke>
</function_calls>
'''
    result = parser.parse(content)
    
    # XML 测试只验证工具名，因为测试用例中没有参数
    assert len(result) == 1, f"应该解析出 1 个工具调用，实际 {len(result)}"
    assert result[0]["name"] == "WebSearchTool", f"工具名错误：{result[0]['name']}"
    print("✓ XML 格式测试通过")


def test_no_tool_calls():
    """测试无工具调用的情况"""
    parser = ToolCallParser()
    
    content = "今天天气不错，适合出去散步。"
    result = parser.parse(content)
    
    assert result == [], f"应该返回空列表，实际 {result}"
    print("✓ 无工具调用测试通过")


if __name__ == "__main__":
    print("运行工具调用解析器测试...\n")
    
    test_python_like()
    test_json_format()
    test_xml_format()
    test_no_tool_calls()
    
    print("\n✓ 所有测试通过！")
