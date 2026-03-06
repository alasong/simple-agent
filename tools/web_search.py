"""
Web Search - 网络搜索功能实现

提供互联网搜索能力，支持多种搜索源
增强功能：支持网页内容自动抓取
"""

import os
import re
import requests
from typing import Optional, List
from dataclasses import dataclass
from bs4 import BeautifulSoup


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str


@dataclass
class SearchResults:
    """搜索结果集合"""
    query: str
    search_results: List[SearchResult]
    total_results: int = 0


def WebSearch(
    query: str,
    allowed_domains: Optional[List[str]] = None,
    blocked_domains: Optional[List[str]] = None,
    num_results: int = 10,
    fetch_content: bool = False,
    content_max_length: int = 3000
) -> SearchResults:
    """
    执行网络搜索
    
    Args:
        query: 搜索查询词
        allowed_domains: 可选，只从这些域名获取结果
        blocked_domains: 可选，排除这些域名的结果
        num_results: 返回结果数量
        fetch_content: 是否自动抓取第一个结果的网页内容
        content_max_length: 抓取内容的最大长度
    
    Returns:
        SearchResults 对象
    
    Raises:
        Exception: 搜索失败时抛出异常
    """
    # 检查是否配置了搜索 API
    bing_api_key = os.environ.get("BING_SEARCH_API_KEY")
    google_api_key = os.environ.get("GOOGLE_SEARCH_API_KEY")
    google_cse_id = os.environ.get("GOOGLE_CSE_ID")
    
    # 优先使用 Bing API
    if bing_api_key:
        results = _bing_search(query, bing_api_key, allowed_domains, blocked_domains, num_results)
    # 其次使用 Google Custom Search
    elif google_api_key and google_cse_id:
        results = _google_search(query, google_api_key, google_cse_id, allowed_domains, blocked_domains, num_results)
    # 回退到 DuckDuckGo HTML 搜索（无需 API）
    else:
        results = _duckduckgo_search(query, allowed_domains, blocked_domains, num_results)
    
    # 如果需要抓取网页内容
    if fetch_content and results.search_results:
        # 获取第一个结果的 URL
        first_result = results.search_results[0]
        if first_result.url:
            # 抓取网页内容并添加到 snippet 中
            content = fetch_webpage_content(first_result.url, content_max_length)
            if content and not content.startswith("抓取") and not content.startswith("解析"):
                # 将网页内容添加到第一个结果的 snippet 前面
                first_result.snippet = f"[网页内容] {content}\n\n[原始摘要] {first_result.snippet}"
    
    return results


def _bing_search(
    query: str,
    api_key: str,
    allowed_domains: Optional[List[str]] = None,
    blocked_domains: Optional[List[str]] = None,
    num_results: int = 10
) -> SearchResults:
    """使用 Bing Search API"""
    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    
    # 构建查询
    search_query = query
    if allowed_domains:
        domain_filter = " OR ".join([f"site:{d}" for d in allowed_domains])
        search_query = f"({query}) ({domain_filter})"
    if blocked_domains:
        for domain in blocked_domains:
            search_query = f"{search_query} -site:{domain}"
    
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {"q": search_query, "count": num_results, "mkt": "zh-CN"}
    
    response = requests.get(endpoint, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    results = []
    
    for item in data.get("webPages", {}).get("value", []):
        results.append(SearchResult(
            title=item.get("name", ""),
            url=item.get("url", ""),
            snippet=item.get("snippet", "")
        ))
    
    total = data.get("webPages", {}).get("totalEstimatedMatches", 0)
    
    return SearchResults(
        query=query,
        search_results=results,
        total_results=total
    )


def _google_search(
    query: str,
    api_key: str,
    cse_id: str,
    allowed_domains: Optional[List[str]] = None,
    blocked_domains: Optional[List[str]] = None,
    num_results: int = 10
) -> SearchResults:
    """使用 Google Custom Search API"""
    endpoint = "https://www.googleapis.com/customsearch/v1"
    
    # 构建查询
    search_query = query
    if allowed_domains:
        domain_filter = " OR ".join([f"site:{d}" for d in allowed_domains])
        search_query = f"({query}) ({domain_filter})"
    if blocked_domains:
        for domain in blocked_domains:
            search_query = f"{search_query} -site:{domain}"
    
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": search_query,
        "num": min(num_results, 10),  # Google 最多返回 10 条
        "gl": "cn"  # 中国地区
    }
    
    response = requests.get(endpoint, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    results = []
    
    for item in data.get("items", []):
        results.append(SearchResult(
            title=item.get("title", ""),
            url=item.get("link", ""),
            snippet=item.get("snippet", "")
        ))
    
    total = int(data.get("searchInformation", {}).get("totalResults", 0))
    
    return SearchResults(
        query=query,
        search_results=results,
        total_results=total
    )


def _duckduckgo_search(
    query: str,
    allowed_domains: Optional[List[str]] = None,
    blocked_domains: Optional[List[str]] = None,
    num_results: int = 10
) -> SearchResults:
    """
    使用 DuckDuckGo HTML 搜索（无需 API）
    
    注意：这是降级方案，适合测试使用
    """
    # 构建查询
    search_query = query
    if allowed_domains:
        for domain in allowed_domains:
            search_query = f"{search_query} site:{domain}"
    if blocked_domains:
        for domain in blocked_domains:
            search_query = f"{search_query} -site:{domain}"
    
    # DuckDuckGo HTML 搜索
    url = "https://html.duckduckgo.com/html/"
    data = {"q": search_query}
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.post(url, data=data, headers=headers, timeout=10)
    response.raise_for_status()
    
    # 解析 HTML 结果
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    results = []
    for result in soup.select('.result')[:num_results]:
        title_elem = result.select_one('.result__title')
        snippet_elem = result.select_one('.result__snippet')
        url_elem = result.select_one('.result__url')
        
        title = title_elem.get_text(strip=True) if title_elem else ""
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
        url = url_elem.get('href', '') if url_elem else ""
        
        # DuckDuckGo 返回的是相对 URL，需要转换
        if url and url.startswith('/'):
            url = f"https://duckduckgo.com{url}"
        
        if title or snippet:
            results.append(SearchResult(
                title=title,
                url=url,
                snippet=snippet
            ))
    
    return SearchResults(
        query=query,
        search_results=results,
        total_results=len(results)
    )


def fetch_webpage_content(url: str, max_length: int = 3000) -> str:
    """
    抓取网页内容并提取主要文本
    
    Args:
        url: 网页 URL
        max_length: 返回内容最大长度
    
    Returns:
        提取的网页主要内容
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=True)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除不需要的元素
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # 尝试提取主要内容
        main_content = None
        
        # 1. 尝试提取 <main> 标签
        main_tag = soup.find('main')
        if main_tag:
            main_content = main_tag
        
        # 2. 尝试提取 article 标签
        if not main_content:
            article_tag = soup.find('article')
            if article_tag:
                main_content = article_tag
        
        # 3. 尝试提取具有主要内容的 div（通过 class 名）
        if not main_content:
            content_classes = ['content', 'main', 'article', 'post', 'entry', 'text']
            for class_name in content_classes:
                content_div = soup.find('div', class_=lambda x: x and class_name in x.lower())
                if content_div and len(content_div.get_text(strip=True)) > 200:
                    main_content = content_div
                    break
        
        # 4. 如果没有找到主要内容区域，使用 body
        if not main_content:
            body_tag = soup.find('body')
            if body_tag:
                main_content = body_tag
            else:
                main_content = soup
        
        # 提取文本并清理
        text = main_content.get_text(separator='\n', strip=True)
        
        # 清理多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 限制长度
        if len(text) > max_length:
            text = text[:max_length] + "\n\n...(内容过长，已截断)"
        
        return text if text else "未能提取到网页内容"
        
    except requests.RequestException as e:
        return f"抓取网页失败：{str(e)}"
    except Exception as e:
        return f"解析网页失败：{str(e)}"


# 便捷函数：直接搜索并返回格式化文本
def search_web(
    query: str,
    allowed_domains: Optional[List[str]] = None,
    blocked_domains: Optional[List[str]] = None,
    num_results: int = 10
) -> str:
    """
    执行网络搜索并返回格式化文本
    
    Returns:
        格式化的搜索结果文本
    """
    results = WebSearch(query, allowed_domains, blocked_domains, num_results)
    
    if not results.search_results:
        return "未找到相关结果"
    
    lines = [f"搜索：{results.query}\n"]
    lines.append(f"共找到 {results.total_results} 条结果\n")
    
    for i, result in enumerate(results.search_results, 1):
        lines.append(f"{i}. **{result.title}**")
        lines.append(f"   链接：{result.url}")
        if result.snippet:
            lines.append(f"   摘要：{result.snippet}")
        lines.append("")
    
    return "\n".join(lines)
