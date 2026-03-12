"""
Extension Manager - Lifecycle management for extensions.

Coordinates loading, enabling, disabling, and unloading of extensions.
"""

from typing import Dict, List, Optional, Any, Callable, Type
from pathlib import Path

from .base import Extension, ExtensionConfig, ExtensionStatus
from .loader import ExtensionLoader
from .registry import ExtensionRegistry


class ExtensionManager:
    """
    Manages the full lifecycle of extensions.

    Features:
    - Load/unload extensions
    - Enable/disable extensions
    - Execute extension actions
    - Trigger events on extensions
    """

    def __init__(
        self,
        search_paths: List[str] = None,
        auto_load: bool = False
    ):
        """
        Initialize the extension manager.

        Args:
            search_paths: Directories to search for extensions
            auto_load: Whether to auto-load on registration
        """
        self.loader = ExtensionLoader(search_paths)
        self.registry = ExtensionRegistry()

        # Active extension instances
        self._instances: Dict[str, Extension] = {}

        # Loaded paths for reload
        self._loaded_paths: Dict[str, str] = {}  # name -> path

        # Event callbacks
        self._on_load: List[Callable[[Extension], None]] = []
        self._on_unload: List[Callable[[Extension], None]] = []
        self._on_enable: List[Callable[[Extension], None]] = []
        self._on_disable: List[Callable[[Extension], None]] = []

        # Auto-load settings
        self.auto_load = auto_load

        # Default config
        self._default_configs: Dict[str, ExtensionConfig] = {}

    def register_default_config(self, name: str, config: ExtensionConfig) -> None:
        """Register default config for an extension."""
        self._default_configs[name] = config

    def load_extension(
        self,
        path: str,
        config: Optional[ExtensionConfig] = None,
        **kwargs
    ) -> Optional[Extension]:
        """
        Load an extension from a file or directory.

        Args:
            path: File or directory path
            config: Optional config to override
            **kwargs: Additional arguments passed to extension constructor

        Returns:
            Extension instance or None
        """
        path = Path(path)

        if not path.exists():
            return None

        if path.is_dir():
            # Load all from directory
            return self._load_directory(path, config)

        # Single file
        return self._load_file(path, config, **kwargs)

    def load_registered(self, name: str) -> Optional[Extension]:
        """
        Load an extension by registered name.

        Args:
            name: Extension name

        Returns:
            Extension instance or None
        """
        ext_class = self.registry.get(name)
        if not ext_class:
            return None

        # Get config from registry
        config = self._default_configs.get(name)
        registry_config = self.registry.get_config(name)
        if config:
            config = ExtensionConfig(**config.__dict__)
        elif registry_config:
            config = ExtensionConfig(**registry_config.__dict__)
        else:
            config = ExtensionConfig(name=name)

        # Also copy tags from registry's tag mapping (stored separately)
        # Find the actual name from registry
        actual_name = name
        if actual_name not in self.registry._registered:
            # Try to find by checking values
            for reg_name, reg_class in self.registry._registered.items():
                if reg_class == ext_class:
                    actual_name = reg_name
                    break

        # Get tags from registry's tag mapping
        for tag, names in self.registry._tags.items():
            if actual_name in names and tag not in config.tags:
                config.tags.append(tag)

        try:
            ext = ext_class(config)
            if ext.initialize(config):
                self._instances[name] = ext
                self.registry.set_status(name, ExtensionStatus.LOADED)
                self._invoke_callback(self._on_load, ext)
                return ext
        except Exception as e:
            print(f"[ExtensionManager] Error loading {name}: {e}")

        return None

    def unload_extension(self, name: str) -> bool:
        """
        Unload an extension by name.

        Args:
            name: Extension name

        Returns:
            True if successful
        """
        ext = self._instances.get(name)
        if not ext:
            return False

        try:
            ext.unload()
            self.registry.set_status(name, ExtensionStatus.UNLOADED)
            del self._instances[name]
            self._invoke_callback(self._on_unload, ext)
            return True
        except Exception as e:
            print(f"[ExtensionManager] Error unloading {name}: {e}")
            return False

    def unload_all(self) -> int:
        """
        Unload all extensions.

        Returns:
            Count of unloaded extensions
        """
        count = 0
        for name in list(self._instances.keys()):
            if self.unload_extension(name):
                count += 1
        return count

    def enable_extension(self, name: str) -> bool:
        """
        Enable an extension.

        Args:
            name: Extension name

        Returns:
            True if successful
        """
        ext = self._instances.get(name)
        if not ext:
            return False

        if ext.enable():
            self.registry.set_status(name, ExtensionStatus.ACTIVE)
            self._invoke_callback(self._on_enable, ext)
            return True
        return False

    def disable_extension(self, name: str) -> bool:
        """
        Disable an extension.

        Args:
            name: Extension name

        Returns:
            True if successful
        """
        ext = self._instances.get(name)
        if not ext:
            return False

        if ext.disable():
            self.registry.set_status(name, ExtensionStatus.LOADED)
            self._invoke_callback(self._on_disable, ext)
            return True
        return False

    def execute(self, name: str, action: str, data: Any = None) -> Any:
        """
        Execute an action on an extension.

        Args:
            name: Extension name
            action: Action name
            data: Optional data

        Returns:
            Action result
        """
        ext = self._instances.get(name)
        if not ext:
            return None

        # Try on_{action} first, then direct {action} method
        method_name = f"on_{action}"
        if hasattr(ext, method_name) and callable(getattr(ext, method_name)):
            method = getattr(ext, method_name)
            return method(data) if data is not None else method()

        # Try direct method name
        if hasattr(ext, action) and callable(getattr(ext, action)):
            method = getattr(ext, action)
            return method(data) if data is not None else method()

        return None

    def execute_all(self, action: str, data: Any = None) -> Dict[str, Any]:
        """
        Execute an action on all active extensions.

        Args:
            action: Action name
            data: Optional data

        Returns:
            Dict of extension name -> result
        """
        results = {}
        for name, ext in self._instances.items():
            if ext.is_active():
                # Try on_{action} first
                method_name = f"on_{action}"
                if hasattr(ext, method_name) and callable(getattr(ext, method_name)):
                    results[name] = getattr(ext, method_name)(data)
                elif hasattr(ext, action) and callable(getattr(ext, action)):
                    results[name] = getattr(ext, action)(data)
                else:
                    results[name] = None
        return results

    def trigger_event(self, event: str, data: Any = None) -> Dict[str, Any]:
        """
        Trigger an event on all active extensions.

        Args:
            event: Event name
            data: Event data

        Returns:
            Dict of extension name -> result
        """
        return self.execute_all(f"on_{event}", data)

    def register_extension(
        self,
        ext_class: Type[Extension],
        config: Optional[ExtensionConfig] = None,
        **kwargs
    ) -> bool:
        """
        Register an extension class for later loading.

        Args:
            ext_class: Extension class
            config: Optional config
            **kwargs: Registration options

        Returns:
            True if successful
        """
        # Extract tags and dependencies from kwargs if provided
        tags = kwargs.get('tags', [])
        dependencies = kwargs.get('dependencies', [])

        if config:
            tags = getattr(config, 'tags', []) or tags
            dependencies = getattr(config, 'dependencies', []) or dependencies

        return self.registry.register(
            ext_class,
            config=config,
            tags=tags,
            dependencies=dependencies
        )

    def get_extension(self, name: str) -> Optional[Extension]:
        """Get an extension instance by name."""
        return self._instances.get(name)

    def get_registered(self, name: str) -> Optional[Type[Extension]]:
        """Get a registered extension class by name."""
        return self.registry.get(name)

    def list_extensions(self) -> List[str]:
        """List loaded extension names."""
        return list(self._instances.keys())

    def list_registered(self) -> List[str]:
        """List registered extension names."""
        return list(self.registry._registered.keys())

    def list_by_tag(self, tag: str) -> List[str]:
        """List loaded extensions with a tag."""
        extensions = []

        # First check loaded extensions
        for name, ext in self._instances.items():
            if tag in ext.config.tags:
                extensions.append(name)

        # Also check registered (but not loaded) extensions
        for ext_name, ext_class in self.registry._registered.items():
            if ext_name not in self._instances:
                # Get tags from registry's tag mapping
                for registry_tag, names in self.registry._tags.items():
                    if registry_tag == tag and ext_name in names:
                        extensions.append(ext_name)
                        break

        return extensions

    def get_status(self, name: str) -> Optional[ExtensionStatus]:
        """Get status of an extension."""
        return self.registry.get_status(name)

    def reload_extension(self, name: str) -> Optional[Extension]:
        """
        Reload an extension.

        Args:
            name: Extension name

        Returns:
            New extension instance or None
        """
        # Get original path
        path = self._loaded_paths.get(name)
        if not path:
            return None

        # Unload current
        self.unload_extension(name)

        # Reload from path
        return self.load_extension(path)

    def reload_all(self) -> Dict[str, bool]:
        """
        Reload all extensions from their original paths.

        Returns:
            Dict of name -> success
        """
        results = {}
        for name, path in list(self._loaded_paths.items()):
            results[name] = self.reload_extension(name) is not None
        return results

    def discover_and_load(self, path: str = None) -> List[Extension]:
        """
        Discover and load extensions from path.

        Args:
            path: Directory to scan (uses search paths if None)

        Returns:
            List of loaded extensions
        """
        if path is None:
            extensions = self.loader.scan_all()
        else:
            extensions = self.loader.load_from_directory(path)

        loaded = []
        for ext in extensions:
            if self._register_with_manager(ext):
                loaded.append(ext)
                self._loaded_paths[ext.name] = str(path)

        return loaded

    def _load_directory(
        self,
        dir_path: Path,
        config: Optional[ExtensionConfig] = None
    ) -> List[Extension]:
        """Load all extensions from a directory."""
        extensions = self.loader.load_from_directory(str(dir_path))

        loaded = []
        for ext in extensions:
            if config:
                ext.config = config
            if self._register_with_manager(ext):
                loaded.append(ext)
                self._loaded_paths[ext.name] = str(dir_path)

        return loaded

    def _load_file(
        self,
        file_path: Path,
        config: Optional[ExtensionConfig] = None,
        **kwargs
    ) -> Optional[Extension]:
        """Load a single file as an extension."""
        ext = None

        if file_path.suffix == '.py':
            ext = self.loader.load_from_module(str(file_path))
        elif file_path.suffix in ['.yaml', '.yml']:
            ext = self.loader.load_from_yaml(str(file_path))

        if ext:
            if config:
                ext.config = config
            # Initialize the extension to run load()
            ext.initialize(config)

        return ext if self._register_with_manager(ext, str(file_path)) else None

    def _register_with_manager(
        self,
        ext: Optional[Extension],
        path: Optional[str] = None
    ) -> bool:
        """Register an extension instance with the manager."""
        if not ext:
            return False

        name = ext.name
        self.registry.set_status(name, ExtensionStatus.LOADED)

        # Track path for reload
        if path:
            self._loaded_paths[name] = path

        # Check dependencies
        deps = self.registry.get_dependencies(name)
        for dep in deps:
            if dep not in self._instances:
                print(f"[ExtensionManager] Missing dependency: {dep}")
                return False

        self._instances[name] = ext
        return True

    def _invoke_callback(self, callbacks: List[Callable], ext: Extension) -> None:
        """Invoke a list of callbacks."""
        for callback in callbacks:
            try:
                callback(ext)
            except Exception as e:
                print(f"[ExtensionManager] Callback error: {e}")

    # Callback registration
    def on_load(self, callback: Callable[[Extension], None]) -> None:
        """Register callback for extension load."""
        self._on_load.append(callback)

    def on_unload(self, callback: Callable[[Extension], None]) -> None:
        """Register callback for extension unload."""
        self._on_unload.append(callback)

    def on_enable(self, callback: Callable[[Extension], None]) -> None:
        """Register callback for extension enable."""
        self._on_enable.append(callback)

    def on_disable(self, callback: Callable[[Extension], None]) -> None:
        """Register callback for extension disable."""
        self._on_disable.append(callback)

    # Properties
    @property
    def active_count(self) -> int:
        """Count of active extensions."""
        return len([e for e in self._instances.values() if e.is_active()])

    @property
    def total_count(self) -> int:
        """Count of total loaded extensions."""
        return len(self._instances)
