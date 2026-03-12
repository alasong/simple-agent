"""
Data Analysis Scene - Main entry

Load all data analysis extensions including pandas, numpy, matplotlib, etc.
"""

from importlib import import_module

# Scene definition
EXTENSIONS = ["analysis", "visualization"]
TOOLS = []
STRATEGIES = []
AGENTS = []


def load_tools(**config):
    """Load all data analysis tools."""
    TOOLS.clear()
    STRATEGIES.clear()

    # Load analysis
    try:
        analysis = import_module(".analysis", __name__)
        analysis.load_tools(**config)
        TOOLS.extend(getattr(analysis, "TOOLS", []))
        STRATEGIES.extend(getattr(analysis, "STRATEGIES", []))
    except ImportError as e:
        print(f"Warning: Could not load analysis tools: {e}")

    # Load visualization
    try:
        visualization = import_module(".visualization", __name__)
        visualization.load_tools(**config)
        TOOLS.extend(getattr(visualization, "TOOLS", []))
        STRATEGIES.extend(getattr(visualization, "STRATEGIES", []))
    except ImportError as e:
        print(f"Warning: Could not load visualization tools: {e}")


def load_strategies(**config):
    """Load all data analysis strategies."""
    strategies = []

    return strategies


# Auto-load on module import
load_tools()

__all__ = ["load_tools", "load_strategies", "EXTENSIONS", "TOOLS", "STRATEGIES", "AGENTS"]
