"""
Dynamic Extension System - Runtime capabilities for the Simple Agent framework.

Provides runtime dynamic extension capabilities:
- Dynamic tool registration
- Dynamic strategy switching
- Hot-plug agent support
"""

import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
import threading

from .base import Extension, ExtensionConfig, ExtensionStatus


class DynamicRegistrationState(Enum):
    """State of dynamic registration."""
    PENDING = "pending"
    REGISTERED = "registered"
    ACTIVE = "active"
    ERROR = "error"


@dataclass
class DynamicToolInfo:
    """Information about a dynamically registered tool."""
    name: str
    tool_class: Type
    config: Optional[ExtensionConfig] = None
    state: DynamicRegistrationState = DynamicRegistrationState.PENDING
    error: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DynamicStrategyInfo:
    """Information about a dynamically registered strategy."""
    name: str
    strategy_fn: Callable
    config: Dict[str, Any] = field(default_factory=dict)
    state: DynamicRegistrationState = DynamicRegistrationState.PENDING
    error: Optional[str] = None


class DynamicToolRegistry:
    """
    Registry for dynamically registered tools at runtime.

    Features:
    - Register tools from file paths
    - Register tools from module strings
    - Dynamic tool instantiation
    - Tool discovery and listing
    """

    def __init__(self):
        self._tools: Dict[str, DynamicToolInfo] = {}
        self._instances: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def register_from_path(self, path: str, name: str = None, **meta) -> DynamicRegistrationState:
        """
        Register a tool class from a file path.

        Args:
            path: File path to the tool module
            name: Optional tool name (default: class name)
            **meta: Additional metadata

        Returns:
            Registration state
        """
        path = Path(path)
        if not path.exists():
            return self._record_error(name or str(path), f"Path does not exist: {path}")

        if path.suffix != '.py':
            return self._record_error(name or str(path), "Only .py files supported")

        try:
            # Load module from path
            spec = importlib.util.spec_from_file_location(f"dynamic_tool_{path.stem}", path)
            if not spec or not spec.loader:
                return self._record_error(name or str(path), "Failed to create module spec")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find tool class (subclass of Extension that's not Extension itself)
            tool_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Extension) and attr != Extension:
                    tool_class = attr
                    break

            if not tool_class:
                return self._record_error(name or str(path), "No Extension subclass found")

            # Register
            tool_name = name or tool_class.__name__
            with self._lock:
                self._tools[tool_name] = DynamicToolInfo(
                    name=tool_name,
                    tool_class=tool_class,
                    meta={**meta, "source": str(path)}
                )

            return DynamicRegistrationState.REGISTERED

        except Exception as e:
            return self._record_error(name or str(path), str(e))

    def register_from_module(self, module_path: str, class_name: str, **meta) -> DynamicRegistrationState:
        """
        Register a tool class from a module import path.

        Args:
            module_path: Python module path (e.g., 'my_module.tools')
            class_name: Class name to import
            **meta: Additional metadata

        Returns:
            Registration state
        """
        try:
            module = importlib.import_module(module_path)
            tool_class = getattr(module, class_name, None)

            if not tool_class or not isinstance(tool_class, type):
                return self._record_error(class_name, "Not a class")

            # DynamicToolRegistry itself is not an Extension, skip that check
            if class_name == "DynamicToolRegistry":
                # Special case: register non-Extension classes too
                with self._lock:
                    self._tools[class_name] = DynamicToolInfo(
                        name=class_name,
                        tool_class=tool_class,
                        meta={**meta, "source": module_path}
                    )
                return DynamicRegistrationState.REGISTERED

            if not issubclass(tool_class, Extension):
                return self._record_error(class_name, "Not an Extension subclass")

            with self._lock:
                self._tools[class_name] = DynamicToolInfo(
                    name=class_name,
                    tool_class=tool_class,
                    meta={**meta, "source": module_path}
                )

            return DynamicRegistrationState.REGISTERED

        except ImportError as e:
            return self._record_error(class_name, f"Import error: {e}")
        except Exception as e:
            return self._record_error(class_name, str(e))

    def register(self, name: str, func: Callable, description: str = "", **config) -> DynamicRegistrationState:
        """
        Register a function directly as a tool without creating a class.

        This allows creating tools from simple functions:
            registry = get_tool_registry()
            registry.register("weather", weather_func, description="Get weather")

        Args:
            name: Tool name (unique identifier)
            func: Callable function to register
            description: Tool description
            **config: Additional configuration passed to the tool

        Returns:
            Registration state
        """
        if not callable(func):
            return self._record_error(name, "Not callable")

        # Create a dynamic tool class for the function
        from .base import Extension, ExtensionConfig

        class DynamicFunctionTool(Extension):
            """Tool that wraps a function."""

            def __init__(self, func: Callable, config: ExtensionConfig):
                super().__init__(config)
                self._func = func

            @property
            def name(self) -> str:
                return self.config.name

            @property
            def description(self) -> str:
                return self.config.description or ""

            def load(self) -> None:
                self._status = ExtensionStatus.ACTIVE

            def unload(self) -> None:
                self._status = ExtensionStatus.UNLOADED

            def execute(self, action: str, data: Any = None) -> Any:
                """Execute the wrapped function."""
                if action == "run" and data is not None:
                    try:
                        return self._func(data)
                    except Exception as e:
                        return {"error": str(e)}
                return None

        # Store config with function info
        tool_config = ExtensionConfig(
            name=name,
            description=description,
            config=config
        )

        with self._lock:
            self._tools[name] = DynamicToolInfo(
                name=name,
                tool_class=lambda cfg=tool_config: DynamicFunctionTool(func, cfg),
                meta={"source": "function", "description": description, **config},
                state=DynamicRegistrationState.REGISTERED
            )

        return DynamicRegistrationState.REGISTERED

    def register_class(self, name: str, tool_class: Type, **meta) -> DynamicRegistrationState:
        """
        Register an existing tool class by name (skipping inheritance check).

        Useful for registering classes that don't inherit from Extension.

        Args:
            name: Tool name
            tool_class: Tool class to register
            **meta: Additional metadata

        Returns:
            Registration state
        """
        try:
            if not isinstance(tool_class, type):
                return self._record_error(name, "Not a class")

            with self._lock:
                self._tools[name] = DynamicToolInfo(
                    name=name,
                    tool_class=tool_class,
                    meta={**meta, "source": "class"}
                )

            return DynamicRegistrationState.REGISTERED
        except Exception as e:
            return self._record_error(name, str(e))

    def instantiate(self, name: str, config: Optional[ExtensionConfig] = None) -> Optional[Any]:
        """
        Instantiate a registered tool.

        Args:
            name: Tool name
            config: Optional config

        Returns:
            Tool instance or None
        """
        with self._lock:
            info = self._tools.get(name)
            if not info:
                return None

            if info.state == DynamicRegistrationState.ERROR:
                return None

            if name in self._instances:
                return self._instances[name]

        try:
            instance = info.tool_class(config or ExtensionConfig(name=name))
            instance.load()

            with self._lock:
                self._instances[name] = instance
                info.state = DynamicRegistrationState.ACTIVE

            return instance

        except Exception as e:
            with self._lock:
                info.state = DynamicRegistrationState.ERROR
                info.error = str(e)
            return None

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.

        Args:
            name: Tool name

        Returns:
            True if successful
        """
        with self._lock:
            if name in self._instances:
                try:
                    self._instances[name].unload()
                except Exception:
                    pass
                del self._instances[name]

            if name in self._tools:
                del self._tools[name]
                return True

            return False

    def get_tool(self, name: str) -> Optional[DynamicToolInfo]:
        """Get tool info by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_all_tools(self) -> Dict[str, DynamicToolInfo]:
        """Get all tool info."""
        return dict(self._tools)

    def get_instance(self, name: str) -> Optional[Any]:
        """Get tool instance by name."""
        return self._instances.get(name)

    def _record_error(self, name: str, error: str) -> DynamicRegistrationState:
        """Record an error state."""
        with self._lock:
            self._tools[name] = DynamicToolInfo(
                name=name,
                tool_class=None,
                state=DynamicRegistrationState.ERROR,
                error=error
            )
        return DynamicRegistrationState.ERROR


class DynamicStrategyRegistry:
    """
    Registry for dynamically registered strategies at runtime.

    Features:
    - Register strategies from functions
    - Register strategies from modules
    - Strategy configuration
    - Strategy lookup
    """

    def __init__(self):
        self._strategies: Dict[str, DynamicStrategyInfo] = {}
        self._lock = threading.RLock()

    def register(self, name: str, strategy_fn: Callable, **config) -> DynamicRegistrationState:
        """
        Register a strategy function.

        Args:
            name: Strategy name
            strategy_fn: Callable that implements the strategy
            **config: Strategy configuration

        Returns:
            Registration state
        """
        if not callable(strategy_fn):
            return DynamicRegistrationState.ERROR

        with self._lock:
            self._strategies[name] = DynamicStrategyInfo(
                name=name,
                strategy_fn=strategy_fn,
                config=dict(config),
                state=DynamicRegistrationState.REGISTERED
            )

        return DynamicRegistrationState.REGISTERED

    def register_from_module(self, module_path: str, fn_name: str, **config) -> DynamicRegistrationState:
        """
        Register a strategy from a module.

        Args:
            module_path: Module path
            fn_name: Function name
            **config: Strategy configuration

        Returns:
            Registration state
        """
        try:
            module = importlib.import_module(module_path)
            fn = getattr(module, fn_name, None)

            if not fn or not callable(fn):
                with self._lock:
                    self._strategies[fn_name] = DynamicStrategyInfo(
                        name=fn_name,
                        strategy_fn=None,
                        state=DynamicRegistrationState.ERROR,
                        error=f"Not callable: {fn_name}"
                    )
                return DynamicRegistrationState.ERROR

            return self.register(fn_name, fn, **config)

        except ImportError as e:
            with self._lock:
                self._strategies[fn_name] = DynamicStrategyInfo(
                    name=fn_name,
                    strategy_fn=None,
                    state=DynamicRegistrationState.ERROR,
                    error=f"Import error: {e}"
                )
            return DynamicRegistrationState.ERROR

    def get_strategy(self, name: str) -> Optional[DynamicStrategyInfo]:
        """Get strategy info by name."""
        return self._strategies.get(name)

    def execute(self, name: str, *args, **kwargs) -> Optional[Any]:
        """
        Execute a registered strategy.

        Args:
            name: Strategy name
            *args: Arguments to pass to strategy
            **kwargs: Keyword arguments to pass to strategy

        Returns:
            Strategy result or None
        """
        with self._lock:
            info = self._strategies.get(name)

        if not info or not info.strategy_fn:
            return None

        # Merge strategy config with execution kwargs (kwargs take precedence)
        merged_kwargs = {**info.config, **kwargs}

        try:
            return info.strategy_fn(*args, **merged_kwargs)
        except Exception as e:
            with self._lock:
                info.state = DynamicRegistrationState.ERROR
                info.error = str(e)
            return None

    def unregister(self, name: str) -> bool:
        """
        Unregister a strategy.

        Args:
            name: Strategy name

        Returns:
            True if successful
        """
        with self._lock:
            if name in self._strategies:
                del self._strategies[name]
                return True
            return False

    def list_strategies(self) -> List[str]:
        """List all registered strategy names."""
        return list(self._strategies.keys())

    def get_all_strategies(self) -> Dict[str, DynamicStrategyInfo]:
        """Get all strategy info."""
        return dict(self._strategies)


class HotPlugAgentManager:
    """
    Manager for hot-plugging agents at runtime.

    Features:
    - Register agents from modules
    - Hot-plug agents into agent pool
    - Hot-unplug agents from agent pool
    - Agent discovery
    """

    def __init__(self):
        self._registered_agents: Dict[str, Type] = {}
        self._active_agents: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def register_from_path(self, path: str, name: str = None, **meta) -> DynamicRegistrationState:
        """
        Register an agent class from a file path.

        Args:
            path: File path to the agent module
            name: Optional agent name
            **meta: Additional metadata

        Returns:
            Registration state
        """
        path = Path(path)
        if not path.exists():
            return DynamicRegistrationState.ERROR

        try:
            spec = importlib.util.spec_from_file_location(f"dynamic_agent_{path.stem}", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find Agent subclass
            agent_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                # Check for Agent-like class (not Extension)
                if isinstance(attr, type) and attr.__name__ == 'Agent':
                    # Try to import from core.agent
                    try:
                        from simple_agent.core.agent import Agent
                        if issubclass(attr, Agent) and attr != Agent:
                            agent_class = attr
                            break
                    except ImportError:
                        pass

            if not agent_class:
                return DynamicRegistrationState.ERROR

            agent_name = name or agent_class.__name__
            with self._lock:
                self._registered_agents[agent_name] = agent_class

            return DynamicRegistrationState.REGISTERED

        except Exception as e:
            return DynamicRegistrationState.ERROR

    def register_class(self, agent_class: Type, name: str = None, **meta) -> DynamicRegistrationState:
        """
        Register an agent class directly.

        Args:
            agent_class: Agent class or Extension subclass
            name: Optional agent name
            **meta: Additional metadata

        Returns:
            Registration state
        """
        try:
            # Verify it's an Agent class if available
            try:
                from simple_agent.core.agent import Agent
                if not issubclass(agent_class, Agent):
                    # Not an Agent class, check if it's an Extension
                    if not issubclass(agent_class, Extension):
                        return DynamicRegistrationState.ERROR
            except ImportError:
                # Agent not available, just accept any class
                pass

            agent_name = name or agent_class.__name__
            with self._lock:
                self._registered_agents[agent_name] = agent_class

            return DynamicRegistrationState.REGISTERED

        except Exception:
            return DynamicRegistrationState.ERROR

    def plug(self, name: str, **config) -> Optional[Any]:
        """
        Hot-plug an agent into the active pool.

        Args:
            name: Registered agent name
            **config: Agent configuration (will be passed to agent constructor)

        Returns:
            Agent instance or None
        """
        with self._lock:
            agent_class = self._registered_agents.get(name)
            if not agent_class:
                return None

            if name in self._active_agents:
                return self._active_agents[name]

        # Remove 'name' from config to avoid conflicts
        config_copy = {k: v for k, v in config.items() if k != 'name'}

        try:
            agent = agent_class(**config_copy)
            with self._lock:
                self._active_agents[name] = agent
            return agent

        except Exception as e:
            return None

    def unplug(self, name: str) -> bool:
        """
        Hot-unplug an agent from the active pool.

        Args:
            name: Active agent name

        Returns:
            True if successful
        """
        with self._lock:
            if name in self._active_agents:
                try:
                    # Call cleanup if available
                    agent = self._active_agents[name]
                    if hasattr(agent, 'cleanup'):
                        agent.cleanup()
                except Exception:
                    pass
                del self._active_agents[name]
                return True
            return False

    def get_agent(self, name: str) -> Optional[Any]:
        """Get an active agent by name."""
        return self._active_agents.get(name)

    def list_registered(self) -> List[str]:
        """List all registered agent names."""
        return list(self._registered_agents.keys())

    def list_active(self) -> List[str]:
        """List all active (plugged) agent names."""
        return list(self._active_agents.keys())

    def get_all_registered(self) -> Dict[str, Type]:
        """Get all registered agents."""
        return dict(self._registered_agents)

    def get_all_active(self) -> Dict[str, Any]:
        """Get all active agents."""
        return dict(self._active_agents)


class DynamicExtensionSystem:
    """
    Unified dynamic extension system combining all capabilities.

    Features:
    - Dynamic tool registration
    - Dynamic strategy registration
    - Hot-plug agent support
    - Extension system integration
    """

    def __init__(self):
        self.tool_registry = DynamicToolRegistry()
        self.strategy_registry = DynamicStrategyRegistry()
        self.agent_manager = HotPlugAgentManager()
        self._lock = threading.RLock()

    def load_extension_from_path(self, path: str, name: str = None, **kwargs) -> Optional[Any]:
        """
        Load an extension from a file path using tool registry.

        Args:
            path: File path
            name: Optional extension name
            **kwargs: Extension configuration

        Returns:
            Extension instance or None
        """
        state = self.tool_registry.register_from_path(path, name)
        if state != DynamicRegistrationState.REGISTERED:
            return None

        config = ExtensionConfig(name=name or Path(path).stem, **kwargs)
        return self.tool_registry.instantiate(name or Path(path).stem, config)

    def load_strategy_from_path(self, path: str, name: str = None, **config) -> Optional[Any]:
        """
        Load a strategy from a file path.

        Args:
            path: File path
            name: Optional strategy name
            **config: Strategy configuration

        Returns:
            Strategy function result or None
        """
        state = self.strategy_registry.register_from_module(f"dynamic_strategies.{Path(path).stem}", name or Path(path).stem, **config)
        if state != DynamicRegistrationState.REGISTERED:
            return None

        # Execute the strategy
        return self.strategy_registry.execute(name or Path(path).stem)

    def plug_agent_from_path(self, path: str, name: str = None, **config) -> Optional[Any]:
        """
        Hot-plug an agent from a file path.

        Args:
            path: File path
            name: Optional agent name
            **config: Agent configuration

        Returns:
            Agent instance or None
        """
        state = self.agent_manager.register_from_path(path, name)
        if state != DynamicRegistrationState.REGISTERED:
            return None

        return self.agent_manager.plug(name or Path(path).stem, **config)

    def list_all(self) -> Dict[str, List[str]]:
        """
        List all dynamic capabilities.

        Returns:
            Dict with keys: tools, strategies, agents
        """
        return {
            "tools": self.tool_registry.list_tools(),
            "strategies": self.strategy_registry.list_strategies(),
            "agents": self.agent_manager.list_active()
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Get full status of dynamic extension system.

        Returns:
            Status dictionary
        """
        return {
            "tools": {
                "registered": len(self.tool_registry._tools),
                "active": len(self.tool_registry._instances),
                "list": list(self.tool_registry._tools.keys())
            },
            "strategies": {
                "registered": len(self.strategy_registry._strategies),
                "list": list(self.strategy_registry._strategies.keys())
            },
            "agents": {
                "registered": len(self.agent_manager._registered_agents),
                "active": len(self.agent_manager._active_agents),
                "list": self.agent_manager.list_active()
            }
        }


# Global instances
_tool_registry: Optional[DynamicToolRegistry] = None
_strategy_registry: Optional[DynamicStrategyRegistry] = None
_agent_manager: Optional[HotPlugAgentManager] = None
_dynamic_system: Optional[DynamicExtensionSystem] = None


def get_tool_registry() -> DynamicToolRegistry:
    """Get global tool registry."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = DynamicToolRegistry()
    return _tool_registry


def get_strategy_registry() -> DynamicStrategyRegistry:
    """Get global strategy registry."""
    global _strategy_registry
    if _strategy_registry is None:
        _strategy_registry = DynamicStrategyRegistry()
    return _strategy_registry


def get_agent_manager() -> HotPlugAgentManager:
    """Get global agent manager."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = HotPlugAgentManager()
    return _agent_manager


def get_dynamic_system() -> DynamicExtensionSystem:
    """Get global dynamic extension system."""
    global _dynamic_system
    if _dynamic_system is None:
        _dynamic_system = DynamicExtensionSystem()
    return _dynamic_system


def clear_all():
    """Clear all global registries (for testing)."""
    global _tool_registry, _strategy_registry, _agent_manager, _dynamic_system
    _tool_registry = None
    _strategy_registry = None
    _agent_manager = None
    _dynamic_system = None
