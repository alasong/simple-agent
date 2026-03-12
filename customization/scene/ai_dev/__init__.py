"""
AI Development Scene - Main entry

Load all AI development extensions including PyTorch, Transformers, etc.
"""

from importlib import import_module

# Scene definition
EXTENSIONS = ["ml", "llm"]
TOOLS = []
STRATEGIES = []
AGENTS = []


def load_tools(**config):
    """Load all AI development tools."""
    TOOLS.clear()
    STRATEGIES.clear()

    # Load ML tools
    try:
        ml = import_module(".ml", __name__)
        ml.load_tools(**config)
        TOOLS.extend(getattr(ml, "TOOLS", []))
        STRATEGIES.extend(getattr(ml, "STRATEGIES", []))
    except ImportError as e:
        print(f"Warning: Could not load ML tools: {e}")

    # Load LLM tools
    try:
        llm = import_module(".llm", __name__)
        llm.load_tools(**config)
        TOOLS.extend(getattr(llm, "TOOLS", []))
        STRATEGIES.extend(getattr(llm, "STRATEGIES", []))
    except ImportError as e:
        print(f"Warning: Could not load LLM tools: {e}")


def load_strategies(**config):
    """Load all AI development strategies."""
    strategies = []

    return strategies


# Auto-load on module import
load_tools()

__all__ = ["load_tools", "load_strategies", "EXTENSIONS", "TOOLS", "STRATEGIES", "AGENTS"]
