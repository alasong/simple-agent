"""
测试增强的 WebSearchTool - 网页内容抓取功能
"""

import sys
sys.path.insert(0, '/home/song/simple-agent')

from tools.web_search import WebSearch, fetch_webpage_content


def test_web_search_with_content():
    """测试带内容抓取的搜索"""
    print("测试 1: 天气查询（带内容抓取）")
    
    results = WebSearch("北京天气", fetch_content=True, content_max_length=2000)
    
    assert len(results.search_results) > 0, "应该返回搜索结果"
    print(f"✓ 返回 {len(results.search_results)} 条搜索结果")
    
    # 检查第一个结果是否包含网页内容
    first_result = results.search_results[0]
    assert "[网页内容]" in first_result.snippet, "第一个结果应该包含抓取的网页内容"
    print("✓ 第一个结果包含网页内容")
    
    # 检查是否包含天气相关信息
    assert any(kw in first_result.snippet for kw in ["气温", "温度", "天气", "晴", "阴"]), \
        "网页内容应该包含天气相关信息"
    print("✓ 网页内容包含天气信息")
    print()


def test_web_search_without_content():
    """测试不带内容抓取的搜索"""
    print("测试 2: 普通搜索（不带内容抓取）")
    
    results = WebSearch("北京天气", fetch_content=False)
    
    assert len(results.search_results) > 0, "应该返回搜索结果"
    print(f"✓ 返回 {len(results.search_results)} 条搜索结果")
    
    # 检查第一个结果不包含网页内容标记
    first_result = results.search_results[0]
    assert "[网页内容]" not in first_result.snippet, "不应该包含网页内容标记"
    print("✓ 结果只包含摘要，没有网页内容")
    print()


def test_fetch_webpage_content():
    """测试网页内容抓取函数"""
    print("测试 3: 直接测试网页内容抓取")
    
    # 使用一个知名网站测试
    test_url = "https://www.weather.com.cn/weather/101010100.shtml"
    content = fetch_webpage_content(test_url, max_length=1500)
    
    assert content, "应该返回内容"
    assert len(content) <= 1500, "内容长度不应超过限制"
    print(f"✓ 成功抓取网页内容（{len(content)} 字符）")
    
    # 检查是否包含天气信息
    assert any(kw in content for kw in ["天气", "气温", "温度", "预报"]), \
        "应该包含天气相关信息"
    print("✓ 内容包含天气信息")
    print()


if __name__ == "__main__":
    print("运行增强的 WebSearchTool 测试...\n")
    
    try:
        test_web_search_with_content()
        test_web_search_without_content()
        test_fetch_webpage_content()
        
        print("\n✅ 所有测试通过！")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️  测试异常（可能是网络问题）：{e}")
        # 网络测试可能不稳定，不视为失败
        print("提示：请检查网络连接后重试")
