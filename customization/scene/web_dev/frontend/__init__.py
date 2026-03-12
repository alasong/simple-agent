"""
Web Development Scene - Frontend extensions

Contains tools and utilities for frontend development with React, Vue, etc.
"""
import sys
from pathlib import Path

# Add scene parent to path
_scene_path = Path(__file__).parent.parent.parent
if str(_scene_path) not in sys.path:
    sys.path.insert(0, str(_scene_path))

# Scene definition
EXTENSIONS = ["frontend", "backend", "database", "api"]
TOOLS = []
STRATEGIES = []
AGENTS = []

# Import and register tools when loaded
def load_tools(**config):
    """Load frontend development tools."""
    from simple_agent.extensions import get_tool_registry

    registry = get_tool_registry()

    # Frontend tools (functions)
    def create_react_component(name: str, props: dict = None) -> str:
        """Create a React component template."""
        props_str = ", ".join(f"{k}={v}" for k, v in (props or {}).items()) or "props"
        return f'''import React from 'react';

interface {name}Props {{
  {props_str}: any;
}}

const {name}: React.FC<{name}Props> = ({{ {props_str} }}) => {{
  return (
    <div className="{name}">
      <h1>{name} Component</h1>
    </div>
  );
}};

export default {name};'''

    def create_vue_component(name: str, data: dict = None) -> str:
        """Create a Vue component template."""
        data_str = ", ".join(f"{k}: {v}" for k, v in (data or {}).items()) or "message: 'Hello'"
        return f'''<template>
  <div class="{name}">
    <h1>{name} Component</h1>
  </div>
</template>

<script setup lang="ts">
const {{ {data_str} }} = defineProps<{name}Props>();
</script>'''

    def create_typescript_interface(name: str, fields: list) -> str:
        """Create a TypeScript interface."""
        field_str = "\n  ".join(fields) or "// fields"
        return f'''interface {name} {{
  {field_str}
}}'''

    # Register frontend tools
    registry.register("create_react_component", create_react_component,
                     description="Create a React component template")
    registry.register("create_vue_component", create_vue_component,
                     description="Create a Vue component template")
    registry.register("create_typescript_interface", create_typescript_interface,
                     description="Create a TypeScript interface")

    TOOLS.extend(["create_react_component", "create_vue_component", "create_typescript_interface"])


def load_strategies(**config):
    """Load frontend development strategies."""
    from simple_agent.extensions import get_strategy_registry

    registry = get_strategy_registry()

    def component_tree(components: list, depth: int = 0) -> list:
        """Organize components into a tree structure."""
        return [{"name": c, "depth": depth} for c in components]

    registry.register("component_tree", component_tree,
                     description="Organize components into a tree structure")
    STRATEGIES.append("component_tree")


# Auto-load on module import
load_tools()
