"""
API Server - FastAPI 主服务

Simple Agent 本地服务化平台入口

用法:
    python -m core.api_server --port 8000 --host 0.0.0.0

API 文档:
    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import router
from .auth import init_auth, get_auth
from .usage_tracker import init_tracker


# ============================================================================
# 创建 FastAPI 应用
# ============================================================================

def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""

    # 初始化认证和追踪
    config_dir = Path(__file__).parent / "config"
    init_auth(str(config_dir / "api_keys.json"))
    init_tracker(str(config_dir / "usage_stats.json"))

    # 创建应用
    app = FastAPI(
        title="Simple Agent API",
        description="Simple Agent 本地服务化平台 - 多 Agent 协作系统 API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # React 开发服务器
            "http://localhost:8080",  # Vue 开发服务器
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(router)

    # 全局错误处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局异常处理"""
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": str(exc),
                "details": {
                    "path": str(request.url.path),
                    "method": request.method,
                    "timestamp": datetime.now().isoformat(),
                }
            }
        )

    # 启动事件
    @app.on_event("startup")
    async def startup_event():
        """应用启动事件"""
        print("=" * 60)
        print("Simple Agent API 服务启动")
        print("=" * 60)
        print(f"Swagger UI: http://localhost:8000/docs")
        print(f"ReDoc: http://localhost:8000/redoc")
        print(f"OpenAPI: http://localhost:8000/openapi.json")
        print("=" * 60)

        # 启动定时任务调度器
        from simple_agent.services.task_scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.start()
        print(f"[定时任务] 调度器已启动")

        # 注册定时任务执行回调
        scheduler._execute_callback = _execute_scheduled_task
        print(f"[定时任务] 已注册执行回调")

        # 如果没有 API Key，生成一个默认的
        auth = get_auth()
        if not auth.list_keys():
            print("\n[提示] 未检测到 API Key，已生成默认 Key:")
            default_key = auth.generate_key(
                name="default",
                rate_limit=1000,
                permissions={"read", "write", "admin"}
            )
            print(f"  API Key: {default_key.key}")
            print("  请保存此 Key，刷新页面后将无法再次查看")
            print("=" * 60)

    # 关闭事件
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭事件"""
        print("\nSimple Agent API 服务关闭")

    return app


# ============================================================================
# 应用实例（模块级别，供 uvicorn 使用）
# ============================================================================

# 延迟初始化，避免导入时执行
_app_instance: Optional[FastAPI] = None


def get_app() -> FastAPI:
    """获取应用实例"""
    global _app_instance
    if _app_instance is None:
        _app_instance = create_app()
    return _app_instance


# 模块级 app 变量，供 uvicorn 使用
app = get_app()


# ============================================================================
# 命令行入口
# ============================================================================

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="Simple Agent API Server")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="监听地址 (默认：127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="端口号 (默认：8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用热重载（开发模式）"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="工作进程数 (默认：1)"
    )

    args = parser.parse_args()

    # 确保 config 目录存在
    config_dir = Path(__file__).parent / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    # 启动服务
    uvicorn.run(
        "simple_agent.services.api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level="info",
    )


if __name__ == "__main__":
    main()
