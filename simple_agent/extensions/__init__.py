"""
Extension System - Unified Plugin Framework

This module provides a unified extension/plugin system for the Simple Agent framework.
Extensions can be loaded at runtime to add new capabilities without modifying core code.

Core Components:
- Extension: Base class for all extensions
- ExtensionLoader: Loads extensions from files/directories
- ExtensionRegistry: Registers and discovers extensions
- ExtensionManager: Manages extension lifecycle

Decorators (for simplified extension creation):
- tool_extension: Create tools from functions
- strategy_extension: Create strategies from functions
- agent_extension: Create agents from classes/functions

Dynamic Capabilities:
- DynamicToolRegistry: Runtime tool registration
- DynamicStrategyRegistry: Runtime strategy registration
- HotPlugAgentManager: Hot-plug agent support

Scene Extensions:
- Scene-based extension packages for common scenarios (web_dev, data_analysis, ai_dev)
"""

from .base import Extension, ExtensionConfig, ExtensionStatus
from .loader import ExtensionLoader
from .registry import ExtensionRegistry
from .manager import ExtensionManager
from .dynamic import (
    DynamicToolRegistry,
    DynamicStrategyRegistry,
    HotPlugAgentManager,
    DynamicExtensionSystem,
    DynamicRegistrationState,
    DynamicToolInfo,
    DynamicStrategyInfo,
    get_tool_registry,
    get_strategy_registry,
    get_agent_manager,
    get_dynamic_system,
    clear_all
)
from .decorator import (
    tool_extension,
    strategy_extension,
    agent_extension,
    create_tool,
    create_strategy,
    register_decorator_extension,
    get_registered_extension,
    list_registered_extensions,
    clear_registered_extensions,
)

# Scene extensions from customization
try:
    from customization.scene import load_scene, list_scenes, list_all_scenes
except ImportError:
    # Fallback to custom location
    try:
        from simple_agent.customization.scene import load_scene, list_scenes, list_all_scenes
    except ImportError:
        load_scene = None
        list_scenes = lambda: []
        list_all_scenes = lambda: {}

__all__ = [
    'Extension',
    'ExtensionConfig',
    'ExtensionStatus',
    'ExtensionLoader',
    'ExtensionRegistry',
    'ExtensionManager',
    # Decorators
    'tool_extension',
    'strategy_extension',
    'agent_extension',
    'create_tool',
    'create_strategy',
    'register_decorator_extension',
    'get_registered_extension',
    'list_registered_extensions',
    'clear_registered_extensions',
    # Dynamic capabilities
    'DynamicToolRegistry',
    'DynamicStrategyRegistry',
    'HotPlugAgentManager',
    'DynamicExtensionSystem',
    'DynamicRegistrationState',
    'DynamicToolInfo',
    'DynamicStrategyInfo',
    'get_tool_registry',
    'get_strategy_registry',
    'get_agent_manager',
    'get_dynamic_system',
    'clear_all',
    # Scene extensions
    'load_scene',
    'list_scenes',
    'list_all_scenes',
]

# Global extension manager instance
_default_manager: ExtensionManager = None


def get_extension_manager() -> ExtensionManager:
    """Get the global extension manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = ExtensionManager()
    return _default_manager


def load_extension(path: str, **kwargs) -> bool:
    """Load an extension from path using default manager."""
    return get_extension_manager().load_extension(path, **kwargs)


def unload_extension(name: str) -> bool:
    """Unload an extension by name using default manager."""
    return get_extension_manager().unload_extension(name)


def list_extensions() -> list:
    """List all loaded extensions using default manager."""
    return get_extension_manager().list_extensions()
