"""
Decorator Extensions - Simplify Extension development with decorators

Provides decorators to create Extensions from functions without
needing to inherit from Extension base class.

Usage:
    from simple_agent.extensions.decorator import tool_extension, strategy_extension

    # Create a tool using decorator
    @tool_extension(name="math_calc", description="Math calculator")
    def calculate(expression: str) -> float:
        return eval(expression)

    tool = calculate()
    result = tool.execute("run", "2 + 2")

    # Create a strategy using decorator
    @strategy_extension(name="parallel", description="Run tasks in parallel")
    def parallel_strategy(tasks: list) -> list:
        return [process_task(t) for t in tasks]

    strategy = parallel_strategy()
    result = strategy.execute("run", tasks)
"""

from typing import Callable, Optional, Dict, Any, List
from functools import wraps
import sys
from pathlib import Path

# Add customization to path
_custom_path = Path(__file__).parent.parent
if str(_custom_path) not in sys.path:
    sys.path.insert(0, str(_custom_path))

# Find base module - try customization first, then simple_agent
try:
    from base import Extension, ExtensionConfig, ToolExtension, StrategyExtension
except ImportError:
    from simple_agent.extensions.base import Extension, ExtensionConfig, ToolExtension, StrategyExtension


def tool_extension(
    name: str,
    description: str = "",
    tools: Optional[List[str]] = None
):
    """
    Decorator to create a ToolExtension from a function.

    Usage:
        @tool_extension(name="weather", description="Get weather for city")
        def get_weather(city: str) -> str:
            return f"Weather in {city}: sunny, 25°C"

        # Create an instance
        weather_tool = get_weather()
        # Or use directly with execute
        result = get_weather().execute("run", "Beijing")

    Args:
        name: Tool name (unique identifier)
        description: Tool description
        tools: List of tool names to provide (if different from function name)

    Returns:
        A callable that returns a ToolExtension instance
    """
    def decorator(func: Callable):
        class SimpleToolExtension(ToolExtension):
            def __init__(self, config: Optional[ExtensionConfig] = None):
                super().__init__(config or ExtensionConfig(
                    name=name,
                    description=description or func.__doc__ or "",
                    tags=["decorator", "tool"]
                ))
                self._func = func
                self._tools = tools or [name]

            @property
            def name(self) -> str:
                return name

            @property
            def description(self) -> str:
                return description or func.__doc__ or ""

            @property
            def tools(self) -> List[Any]:
                # Return a list of bound methods
                return [getattr(self, tool, None) for tool in self._tools if hasattr(self, tool)]

            def load(self) -> None:
                self._status = ExtensionStatus.ACTIVE

            def unload(self) -> None:
                self._status = ExtensionStatus.UNLOADED

            def execute(self, action: str, data: Any = None) -> Any:
                """Execute the tool function"""
                if action == "run" and data is not None:
                    try:
                        return self._func(data)
                    except Exception as e:
                        return {"error": str(e)}
                return None

            def on_run(self, data: Any) -> Any:
                """Alias for execute with 'run' action"""
                return self.execute("run", data)

        # Make the decorator itself callable to create instances
        @wraps(func)
        def create_instance(config: Optional[ExtensionConfig] = None) -> SimpleToolExtension:
            return SimpleToolExtension(config)

        # Add class attributes for introspection
        create_instance._extension_class = SimpleToolExtension
        create_instance._extension_name = name
        create_instance._extension_type = "tool"

        return create_instance

    return decorator


def strategy_extension(
    name: str,
    description: str = "",
    config_schema: Optional[Dict[str, Any]] = None
):
    """
    Decorator to create a StrategyExtension from a function.

    Usage:
        @strategy_extension(name="parallel", description="Run tasks in parallel")
        def parallel_strategy(tasks: list, max_workers: int = 3) -> list:
            return [process_task(t) for t in tasks[:max_workers]]

        # Create an instance
        strategy = parallel_strategy()
        # Or with config
        config = ExtensionConfig(name="parallel", config={"max_workers": 5})
        strategy = parallel_strategy(config)
        result = strategy.execute("run", tasks)

    Args:
        name: Strategy name (unique identifier)
        description: Strategy description
        config_schema: Optional schema for configuration validation

    Returns:
        A callable that returns a StrategyExtension instance
    """
    def decorator(func: Callable):
        class SimpleStrategyExtension(StrategyExtension):
            def __init__(self, config: Optional[ExtensionConfig] = None):
                super().__init__(config or ExtensionConfig(
                    name=name,
                    description=description or func.__doc__ or "",
                    tags=["decorator", "strategy"]
                ))
                self._func = func
                self._config_schema = config_schema or {}
                self._default_config = {}

            @property
            def name(self) -> str:
                return name

            @property
            def description(self) -> str:
                return description or func.__doc__ or ""

            @property
            def strategies(self) -> Dict[str, Callable]:
                return {name: self._execute}

            def load(self) -> None:
                self._status = ExtensionStatus.ACTIVE

            def unload(self) -> None:
                self._status = ExtensionStatus.UNLOADED

            def _execute(self, *args, **kwargs) -> Any:
                """Execute the strategy function"""
                # Merge default config with execution kwargs
                merged_kwargs = {**self._default_config, **kwargs}
                try:
                    return self._func(*args, **merged_kwargs)
                except Exception as e:
                    return {"error": str(e)}

            def execute(self, action: str, data: Any = None) -> Any:
                """Execute the strategy"""
                if action == "run" and callable(data):
                    return self._execute(data)
                elif action == "run" and isinstance(data, (list, tuple)):
                    return self._execute(*data)
                elif action == "run" and data is not None:
                    return self._execute(data)
                return None

            def set_config(self, **config) -> 'SimpleStrategyExtension':
                """Set configuration for the strategy"""
                self._default_config = config
                return self

        # Make the decorator itself callable to create instances
        @wraps(func)
        def create_instance(config: Optional[ExtensionConfig] = None) -> SimpleStrategyExtension:
            return SimpleStrategyExtension(config)

        # Add class attributes for introspection
        create_instance._extension_class = SimpleStrategyExtension
        create_instance._extension_name = name
        create_instance._extension_type = "strategy"

        return create_instance

    return decorator


def agent_extension(name: str, description: str = "", agent_class: Any = None):
    """
    Decorator to create an AgentExtension from a class or function.

    Usage:
        @agent_extension(name="web_crawler", description="Web crawler agent")
        class WebCrawler:
            def crawl(self, url: str) -> str:
                return f"Crawled {url}"

        agent = WebCrawler()
        # Or
        @agent_extension(name="search_agent", description="Search agent")
        def create_search_agent():
            return SearchAgent()

        agent = create_search_agent()

    Args:
        name: Agent name (unique identifier)
        description: Agent description
        agent_class: Optional class to use as the agent

    Returns:
        A callable that returns an AgentExtension instance
    """
    def decorator(func_or_class):
        class SimpleAgentExtension(AgentExtension):
            def __init__(self, config: Optional[ExtensionConfig] = None):
                super().__init__(config or ExtensionConfig(
                    name=name,
                    description=description,
                    tags=["decorator", "agent"]
                ))
                self._agent_class = func_or_class
                self._instance = None

            @property
            def name(self) -> str:
                return name

            @property
            def description(self) -> str:
                return description

            @property
            def agents(self) -> Dict[str, Any]:
                return {name: self._get_or_create_agent}

            def load(self) -> None:
                self._status = ExtensionStatus.ACTIVE

            def unload(self) -> None:
                self._status = ExtensionStatus.UNLOADED
                if self._instance:
                    if hasattr(self._instance, 'cleanup'):
                        self._instance.cleanup()
                    self._instance = None

            def _get_or_create_agent(self, **kwargs) -> Any:
                """Get or create the agent instance"""
                if self._instance is None:
                    if callable(self._agent_class):
                        try:
                            self._instance = self._agent_class(**kwargs)
                        except TypeError:
                            # Try without kwargs
                            self._instance = self._agent_class()
                    else:
                        self._instance = self._agent_class
                return self._instance

            def execute(self, action: str, data: Any = None) -> Any:
                """Execute on the agent"""
                if action == "create" and callable(data):
                    return data(self._get_or_create_agent())
                return None

        # Make the decorator itself callable to create instances
        @wraps(func_or_class)
        def create_instance(config: Optional[ExtensionConfig] = None) -> SimpleAgentExtension:
            return SimpleAgentExtension(config)

        # Add class attributes for introspection
        create_instance._extension_class = SimpleAgentExtension
        create_instance._extension_name = name
        create_instance._extension_type = "agent"

        return create_instance

    return decorator


# ============================================================================
# Simple Factory Functions
# ============================================================================

def create_tool(name: str, description: str = ""):
    """
    Create a simple tool factory.

    Usage:
        # Create a factory
        my_tool_factory = create_tool("my_tool", "My custom tool")

        # Create a tool function
        @my_tool_factory
        def process(data: str) -> str:
            return f"Processed: {data}"

    Args:
        name: Tool name
        description: Tool description

    Returns:
        A decorator factory
    """
    def decorator(func: Callable):
        return tool_extension(name, description)(func)
    return decorator


def create_strategy(name: str, description: str = ""):
    """
    Create a simple strategy factory.

    Usage:
        my_strategy_factory = create_strategy("my_strategy", "My strategy")

        @my_strategy_factory
        def run_strategy(data: Any) -> Any:
            return process(data)

    Args:
        name: Strategy name
        description: Strategy description

    Returns:
        A decorator factory
    """
    def decorator(func: Callable):
        return strategy_extension(name, description)(func)
    return decorator


# Global registry for decorator-created extensions
_decorator_registry: Dict[str, Any] = {}


def register_decorator_extension(extension_func, name: str, extension_type: str):
    """
    Register a decorator extension for later instantiation.

    Args:
        extension_func: The extension creator function
        name: Name to register under
        extension_type: Type of extension ('tool', 'strategy', 'agent')
    """
    _decorator_registry[name] = {
        'func': extension_func,
        'type': extension_type
    }


def get_registered_extension(name: str) -> Optional[Any]:
    """
    Get a registered extension by name.

    Args:
        name: Extension name

    Returns:
        Extension instance or None if not found
    """
    info = _decorator_registry.get(name)
    if info:
        return info['func']()
    return None


def list_registered_extensions() -> List[Dict[str, str]]:
    """
    List all registered decorator extensions.

    Returns:
        List of extension info dicts
    """
    return [
        {'name': name, 'type': info['type']}
        for name, info in _decorator_registry.items()
    ]


def clear_registered_extensions():
    """Clear all registered extensions (for testing)."""
    _decorator_registry.clear()
