"""
HttpTool - HTTP 请求工具

发送 HTTP 请求，支持常见 HTTP 方法
"""

import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Union
from core.tool import BaseTool, ToolResult


class HttpTool(BaseTool):
    """HTTP 请求工具：发送 HTTP 请求并返回响应"""
    
    @property
    def name(self) -> str:
        return "http"
    
    @property
    def description(self) -> str:
        return """发送 HTTP 请求。

使用场景：
- API 调用：调用 REST API、GraphQL 等
- 数据获取：获取网页内容、JSON 数据
- 健康检查：检查服务是否可用
- 测试调试：测试 API 端点

支持的方法：GET, POST, PUT, DELETE, PATCH, HEAD

注意：
- 默认超时 30 秒
- 自动处理 JSON 响应
- 支持自定义请求头
"""
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "请求 URL"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP 方法",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"],
                    "default": "GET"
                },
                "headers": {
                    "type": "object",
                    "description": "请求头，如 {\"Content-Type\": \"application/json\"}"
                },
                "body": {
                    "type": "string",
                    "description": "请求体（POST/PUT/PATCH 时使用）"
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒），默认 30",
                    "default": 30
                },
                "follow_redirects": {
                    "type": "boolean",
                    "description": "是否跟随重定向，默认 true",
                    "default": True
                }
            },
            "required": ["url"]
        }
    
    def execute(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        timeout: int = 30,
        follow_redirects: bool = True,
        **kwargs
    ) -> ToolResult:
        """发送 HTTP 请求"""
        try:
            # 构建请求
            request = urllib.request.Request(
                url,
                method=method.upper()
            )
            
            # 添加请求头
            if headers:
                for key, value in headers.items():
                    request.add_header(key, value)
            
            # 默认 User-Agent
            if "User-Agent" not in (headers or {}):
                request.add_header("User-Agent", "SimpleAgent/1.0")
            
            # 添加请求体
            if body and method in ["POST", "PUT", "PATCH"]:
                request.data = body.encode("utf-8")
                
                # 自动添加 Content-Type
                if "Content-Type" not in (headers or {}):
                    request.add_header("Content-Type", "application/json")
            
            # 发送请求
            response = urllib.request.urlopen(
                request,
                timeout=timeout
            )
            
            # 读取响应
            response_body = response.read().decode("utf-8")
            
            # 解析 JSON
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                try:
                    data = json.loads(response_body)
                    # 格式化 JSON 输出
                    response_body = json.dumps(data, indent=2, ensure_ascii=False)
                except json.JSONDecodeError:
                    pass
            
            # 构建输出
            output_parts = [
                f"[响应] {response.status} {response.reason}",
                f"[URL] {response.url}",
                f"[大小] {len(response_body)} 字节",
                "",
                response_body
            ]
            
            return ToolResult(
                success=200 <= response.status < 300,
                output="\n".join(output_parts),
                error=None if 200 <= response.status < 300 else f"HTTP {response.status}"
            )
            
        except urllib.error.HTTPError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"HTTP 错误: {e.code} {e.reason}"
            )
        except urllib.error.URLError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"URL 错误: {e.reason}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"请求失败: {e}"
            )


# 注册工具到资源仓库
from core.resource import repo
repo.register_tool(
    HttpTool,
    tags=["http", "network", "api", "request"],
    description="发送 HTTP 请求"
)