"""
WebSearchTool - 网络搜索工具

提供互联网搜索能力，获取最新信息和实时数据
"""

from typing import Optional
import requests
from simple_agent.core.tool import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    """网络搜索工具：搜索互联网获取最新信息"""
    
    @property
    def name(self) -> str:
        return "WebSearchTool"
    
    @property
    def description(self) -> str:
        return "搜索互联网获取最新信息、实时数据、新闻资讯等。适用于需要最新外部信息的场景。"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询词"
                },
                "allowed_domains": {
                    "type": "array",
                    "description": "可选：只从这些域名获取结果",
                    "items": {"type": "string"}
                },
                "blocked_domains": {
                    "type": "array",
                    "description": "可选：排除这些域名的结果",
                    "items": {"type": "string"}
                },
                "fetch_content": {
                    "type": "boolean",
                    "description": "可选：是否自动抓取第一个结果的网页内容（默认 false）"
                },
                "content_max_length": {
                    "type": "integer",
                    "description": "可选：抓取内容的最大长度（默认 3000）"
                }
            },
            "required": ["query"]
        }
    
    def execute(
        self,
        query: str,
        allowed_domains: Optional[list] = None,
        blocked_domains: Optional[list] = None,
        fetch_content: bool = False,
        content_max_length: int = 3000,
        **kwargs
    ) -> ToolResult:
        """执行网络搜索"""
        try:
            # 导入实际的搜索函数
            from simple_agent.tools.web_search import WebSearch as web_search_func
            
            # 构建搜索参数
            search_kwargs = {
                "query": query,
                "fetch_content": fetch_content,
                "content_max_length": content_max_length
            }
            if allowed_domains:
                search_kwargs["allowed_domains"] = allowed_domains
            if blocked_domains:
                search_kwargs["blocked_domains"] = blocked_domains
            
            # 执行搜索
            results = web_search_func(**search_kwargs)
            
            # 格式化搜索结果
            result_lines = []
            if hasattr(results, 'search_results'):
                for result in results.search_results:
                    title = result.title if hasattr(result, 'title') else result.get('title', '')
                    url = result.url if hasattr(result, 'url') else result.get('url', '')
                    snippet = result.snippet if hasattr(result, 'snippet') else result.get('snippet', '')
                    result_lines.append(f"**{title}**")
                    result_lines.append(f"  链接：{url}")
                    if snippet:
                        result_lines.append(f"  摘要：{snippet}")
                    result_lines.append("")
            else:
                # 如果没有结构化结果，返回原始数据
                result_lines.append(str(results))
            
            return ToolResult(
                success=True,
                output="\n".join(result_lines) if result_lines else "未找到相关结果"
            )
            
        except ImportError as e:
            # WebSearch 函数不可用
            error_msg = "网络搜索功能不可用。请确保已安装 requests 和 beautifulsoup4。"
            suggestion = "安装方法：pip install requests beautifulsoup4"
            return ToolResult(
                success=False,
                output=f"{error_msg}\n\n建议：{suggestion}",
                error=f"WebSearch 函数未找到：{e}"
            )
        except requests.exceptions.Timeout as e:
            # 网络超时
            error_msg = "网络搜索超时，可能是网络连接不稳定。"
            suggestion = "建议：1. 检查网络连接 2. 稍后重试查询 3. 如使用代理，请确认代理配置"
            fallback = "或者我可以基于已有知识为您提供相关信息（非实时）。"
            return ToolResult(
                success=False,
                output=f"{error_msg}\n\n{suggestion}\n\n{fallback}",
                error=f"网络超时：{e}"
            )
        except requests.exceptions.ConnectionError as e:
            # 网络连接错误
            error_msg = "无法连接到搜索引擎，请检查网络。"
            suggestion = "建议：1. 检查网络连接 2. 确认 DNS 设置正确 3. 如使用代理，请确认代理配置"
            fallback = "或者我可以基于已有知识为您提供相关信息（非实时）。"
            return ToolResult(
                success=False,
                output=f"{error_msg}\n\n{suggestion}\n\n{fallback}",
                error=f"连接错误：{e}"
            )
        except Exception as e:
            error_msg = f"网络搜索遇到错误。"
            suggestion = "建议：检查网络连接后重试，或尝试其他查询。"
            return ToolResult(
                success=False,
                output=f"{error_msg}\n\n{suggestion}\n\n错误详情：{str(e)}",
                error=f"网络搜索失败：{e}"
            )


# 注册工具到资源仓库
from simple_agent.core.resource import repo
repo.register_tool(
    WebSearchTool,
    tags=["search", "internet", "information"],
    description="搜索互联网获取最新信息、实时数据、新闻资讯等"
)
