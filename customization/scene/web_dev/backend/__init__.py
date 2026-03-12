"""
Web Development Scene - Backend extensions

Contains tools and utilities for backend development with Node.js, Python, etc.
"""
import sys
from pathlib import Path

# Add scene parent to path
_scene_path = Path(__file__).parent.parent.parent
if str(_scene_path) not in sys.path:
    sys.path.insert(0, str(_scene_path))

# Scene definition
EXTENSIONS = []
TOOLS = []
STRATEGIES = []
AGENTS = []


def load_tools(**config):
    """Load backend development tools."""
    from simple_agent.extensions import get_tool_registry

    registry = get_tool_registry()

    # Backend tools (functions)
    def create_fastapi_endpoint(path: str, method: str = "GET", response: dict = None) -> str:
        """Create a FastAPI endpoint."""
        return f'''from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.{method.lower()}("{path}")
async def handle_{path.replace("/", "_").replace("{", "").replace("}", "")}():
    """Handle {method} request to {path}"""
    return {response or '"OK"'}'''

    def create_nodejs_route(path: str, handler: str = "handler") -> str:
        """Create a Node.js Express route."""
        return f'''const express = require('express');
const router = express.Router();

router.{method or 'get'}('{path}', {handler});

module.exports = router;'''

    def create_database_schema(name: str, fields: list) -> str:
        """Create a database schema."""
        field_str = "\n  ".join(fields) or "// fields"
        return f'''CREATE TABLE {name} (
  {field_str}
);'''

    def create_dockerfile(app_name: str, port: int = 8080) -> str:
        """Create a Dockerfile template."""
        return f'''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {port}

CMD ["uvicorn", "{app_name}:app", "--host", "0.0.0.0", "--port", "{port}"]'''

    # Register backend tools
    registry.register("create_fastapi_endpoint", create_fastapi_endpoint,
                     description="Create a FastAPI endpoint")
    registry.register("create_nodejs_route", create_nodejs_route,
                     description="Create a Node.js Express route")
    registry.register("create_database_schema", create_database_schema,
                     description="Create a database schema")
    registry.register("create_dockerfile", create_dockerfile,
                     description="Create a Dockerfile template")

    TOOLS.extend([
        "create_fastapi_endpoint",
        "create_nodejs_route",
        "create_database_schema",
        "create_dockerfile"
    ])


def load_strategies(**config):
    """Load backend development strategies."""
    from simple_agent.extensions import get_strategy_registry

    registry = get_strategy_registry()

    def api_structure(routes: list) -> dict:
        """Organize API routes into a structure."""
        return {"routes": routes, "count": len(routes)}

    registry.register("api_structure", api_structure,
                     description="Organize API routes into a structure")
    STRATEGIES.append("api_structure")


# Auto-load on module import
load_tools()
