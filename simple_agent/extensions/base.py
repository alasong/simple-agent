"""
Extension Base Classes

Defines the base classes for all extensions in the Simple Agent framework.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum


class ExtensionStatus(Enum):
    """Extension lifecycle status."""
    PENDING = "pending"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    UNLOADED = "unloaded"


@dataclass
class ExtensionConfig:
    """Configuration for an extension."""
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtensionConfig':
        """Create config from dictionary."""
        return cls(
            name=data.get('name', ''),
            version=data.get('version', '1.0.0'),
            description=data.get('description', ''),
            enabled=data.get('enabled', True),
            config=data.get('config', {}),
            tags=data.get('tags', []),
            dependencies=data.get('dependencies', []),
        )


class Extension(ABC):
    """
    Base class for all extensions.

    Subclasses must implement:
    - name: Unique identifier
    - description: Human-readable description
    - load(): Initialize the extension
    - unload(): Cleanup when unloading
    """

    def __init__(self, config: Optional[ExtensionConfig] = None):
        self.config = config or ExtensionConfig()
        self._status = ExtensionStatus.PENDING
        self._error: Optional[str] = None
        self._metadata: Dict[str, Any] = {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this extension."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""
        pass

    @property
    def status(self) -> ExtensionStatus:
        """Current status of the extension."""
        return self._status

    @property
    def error(self) -> Optional[str]:
        """Last error if any."""
        return self._error

    @property
    def metadata(self) -> Dict[str, Any]:
        """Extension metadata."""
        return self._metadata

    def initialize(self, config: Optional[ExtensionConfig] = None) -> bool:
        """
        Initialize the extension with optional config.

        Args:
            config: Optional config to override default

        Returns:
            True if successful, False otherwise
        """
        try:
            if config:
                self.config = config
            self._status = ExtensionStatus.LOADED
            self.load()
            self._status = ExtensionStatus.ACTIVE
            return True
        except Exception as e:
            self._status = ExtensionStatus.ERROR
            self._error = str(e)
            return False

    @abstractmethod
    def load(self) -> None:
        """
        Load/initialize the extension.

        Called after initialize() succeeds.
        Override to add custom initialization logic.
        """
        pass

    def unload(self) -> None:
        """
        Cleanup and unload the extension.

        Override to add custom cleanup logic.
        """
        pass

    def enable(self) -> bool:
        """Enable the extension."""
        if self._status == ExtensionStatus.ACTIVE:
            return True
        if self._status == ExtensionStatus.ERROR:
            return False
        self._status = ExtensionStatus.ACTIVE
        return True

    def disable(self) -> bool:
        """Disable the extension."""
        if self._status != ExtensionStatus.ACTIVE:
            return False
        self._status = ExtensionStatus.LOADED
        return True

    def execute(self, action: str, data: Any = None) -> Any:
        """
        Execute an action on the extension.

        Args:
            action: Action name to execute
            data: Optional data for the action

        Returns:
            Action result
        """
        method_name = f"on_{action}"
        if hasattr(self, method_name) and callable(getattr(self, method_name)):
            method = getattr(self, method_name)
            return method(data)
        return None

    def is_active(self) -> bool:
        """Check if extension is active."""
        return self._status == ExtensionStatus.ACTIVE

    def is_error(self) -> bool:
        """Check if extension is in error state."""
        return self._status == ExtensionStatus.ERROR


class ToolExtension(Extension):
    """Base class for extensions that provide tools."""

    @property
    @abstractmethod
    def tools(self) -> List[Any]:
        """List of tools provided by this extension."""
        pass


class StrategyExtension(Extension):
    """Base class for extensions that provide strategies."""

    @property
    @abstractmethod
    def strategies(self) -> Dict[str, Callable]:
        """Dictionary of strategy name to callable."""
        pass


class AgentExtension(Extension):
    """Base class for extensions that provide agents."""

    @property
    @abstractmethod
    def agents(self) -> Dict[str, Any]:
        """Dictionary of agent name to agent class/factory."""
        pass


class DecoratorExtension(Extension):
    """
    Base class for extensions that provide decorators.

    Useful for adding behavior to existing components without modification.
    """

    @property
    @abstractmethod
    def decorators(self) -> Dict[str, Callable]:
        """Dictionary of decorator name to decorator function."""
        pass
