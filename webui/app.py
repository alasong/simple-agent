"""
Web UI - FastAPI 静态文件服务

提供前端静态文件和 API 集成

用法:
    python -m webui.app --port 3000 --host 0.0.0.0
"""

import argparse
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.routing import APIRouter

from services.api.auth import init_auth, get_auth
from services.api.usage_tracker import init_tracker
from services.session_store import init_store


# ============================================================================
# 创建 FastAPI 应用
# ============================================================================

def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""

    # 初始化认证和追踪
    config_dir = Path(__file__).parent.parent / "core" / "config"
    init_auth(str(config_dir / "api_keys.json"))
    init_tracker(str(config_dir / "usage_stats.json"))
    init_store(str(Path(__file__).parent.parent / "sessions"))

    # 创建应用
    app = FastAPI(
        title="Simple Agent Web UI",
        description="Simple Agent 本地服务化平台 - Web 界面",
        version="1.0.0",
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 获取 frontend 目录
    frontend_dir = Path(__file__).parent / "frontend"

    # 如果 frontend 目录存在，挂载静态文件
    if frontend_dir.exists():
        static_dir = frontend_dir / "static"
        if static_dir.exists():
            app.mount(
                "/static",
                StaticFiles(directory=str(static_dir), html=True),
                name="static"
            )

    # 根路由 - 返回前端页面
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """返回前端页面"""
        if frontend_dir.exists():
            index_file = frontend_dir / "index.html"
            if index_file.exists():
                with open(index_file, "r", encoding="utf-8") as f:
                    return f.read()

        # 如果没有前端文件，返回简单的提示页面
        return get_fallback_html()

    # API 状态端点（用于前端检查后端状态）
    @app.get("/api/status")
    async def api_status():
        """API 状态"""
        auth = get_auth()
        tracker = init_tracker()

        return {
            "status": "ok",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "api_keys_configured": len(auth.list_keys()) > 0,
            "uptime": tracker.get_uptime(),
        }

    # 启动事件
    @app.on_event("startup")
    async def startup_event():
        """应用启动事件"""
        print("=" * 60)
        print("Simple Agent Web UI 服务启动")
        print("=" * 60)
        print(f"访问地址：http://localhost:3000")
        print("=" * 60)

    return app


# 模块级 app 变量，供 uvicorn 使用
app = create_app()


def get_fallback_html() -> str:
    """返回备用的 HTML 页面"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Agent Web UI</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 8px;
            padding: 40px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        .status { color: #22c55e; }
        .api-docs {
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-radius: 4px;
            padding: 16px;
            margin: 20px 0;
        }
        .api-docs a { color: #0284c7; }
        .loading { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Simple Agent Web UI</h1>
        <p class="status">✅ 服务已启动</p>

        <div class="api-docs">
            <h3>📚 API 文档</h3>
            <p>访问 <a href="http://localhost:8000/docs" target="_blank">http://localhost:8000/docs</a> 查看 API 文档</p>
        </div>

        <div class="loading">
            <p>前端界面正在开发中...</p>
            <p>您可以直接使用 API 与 Simple Agent 交互</p>
        </div>

        <h3>快速开始</h3>
        <pre style="background: #f4f4f4; padding: 16px; border-radius: 4px; overflow-x: auto;">
# 运行 Agent
curl -X POST "http://localhost:8000/api/v1/agent/run?X-API-Key=your-key" \\
  -H "Content-Type: application/json" \\
  -d '{"agent_name": "developer", "input": "分析当前目录"}'

# 查询任务状态
curl "http://localhost:8000/api/v1/task/{task_id}/status?X-API-Key=your-key"
        </pre>
    </div>
</body>
</html>
"""


# ============================================================================
# 命令行入口
# ============================================================================

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="Simple Agent Web UI Server")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="监听地址 (默认：127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="端口号 (默认：3000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用热重载（开发模式）"
    )

    args = parser.parse_args()

    # 确保 frontend 目录存在
    frontend_dir = Path(__file__).parent / "frontend"
    frontend_dir.mkdir(parents=True, exist_ok=True)

    # 启动服务
    uvicorn.run(
        "webui.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
