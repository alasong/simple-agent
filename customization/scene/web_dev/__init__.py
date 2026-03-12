"""
Web Development Scene - Main entry

Load all web development extensions.
"""
import sys
from pathlib import Path

# Get the parent of web_dev (extensions/scene) to add to path
_scene_path = Path(__file__).parent.parent
if str(_scene_path) not in sys.path:
    sys.path.insert(0, str(_scene_path))

from importlib import import_module

# Scene definition
EXTENSIONS = ["frontend", "backend", "database"]
TOOLS = []
STRATEGIES = []
AGENTS = []


def load_tools(**config):
    """Load all web development tools."""
    TOOLS.clear()
    STRATEGIES.clear()

    # Load frontend, backend, database using absolute name
    for module_name in ["web_dev.frontend", "web_dev.backend", "web_dev.database"]:
        try:
            module = import_module(module_name)
            if hasattr(module, "load_tools"):
                module.load_tools(**config)
            if hasattr(module, "TOOLS"):
                TOOLS.extend(getattr(module, "TOOLS", []))
            if hasattr(module, "STRATEGIES"):
                STRATEGIES.extend(getattr(module, "STRATEGIES", []))
        except ImportError as e:
            print(f"Warning: Could not load {module_name}: {e}")


def load_strategies(**config):
    """Load all web development strategies."""
    strategies = []

    try:
        backend = import_module("backend")
        strategies.extend(getattr(backend, "STRATEGIES", []))
    except ImportError:
        pass

    return strategies


# Auto-load on module import
load_tools()

__all__ = ["load_tools", "load_strategies", "EXTENSIONS", "TOOLS", "STRATEGIES", "AGENTS"]
