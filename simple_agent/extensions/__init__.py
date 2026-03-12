"""
Extension System - Unified Plugin Framework

This module provides a unified extension/plugin system for the Simple Agent framework.
Extensions can be loaded at runtime to add new capabilities without modifying core code.

Core Components:
- Extension: Base class for all extensions
- ExtensionLoader: Loads extensions from files/directories
- ExtensionRegistry: Registers and discovers extensions
- ExtensionManager: Manages extension lifecycle
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

__all__ = [
    'Extension',
    'ExtensionConfig',
    'ExtensionStatus',
    'ExtensionLoader',
    'ExtensionRegistry',
    'ExtensionManager',
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
