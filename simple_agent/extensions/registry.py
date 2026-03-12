"""
Extension Registry - Register and discover extensions.

Provides tag-based discovery and registration of extensions.
"""

from typing import Dict, List, Optional, Any, Set
from typing import Type
from collections import defaultdict
from .base import Extension, ExtensionConfig, ExtensionStatus


class ExtensionRegistry:
    """
    Registry for tracking and discovering extensions.

    Supports:
    - Registration by name
    - Tag-based discovery
    - Version management
    - Dependency resolution
    """

    def __init__(self):
        """Initialize the registry."""
        # Name -> Extension class mapping
        self._registered: Dict[str, Type[Extension]] = {}

        # Tag -> List of extension names
        self._tags: Dict[str, List[str]] = defaultdict(list)

        # Name -> ExtensionConfig mapping
        self._configs: Dict[str, ExtensionConfig] = {}

        # Name -> status mapping
        self._statuses: Dict[str, ExtensionStatus] = {}

        # Dependency graph: name -> set of dependencies
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)

    def register(
        self,
        ext_class: Type[Extension],
        config: Optional[ExtensionConfig] = None,
        tags: List[str] = None,
        dependencies: List[str] = None
    ) -> bool:
        """
        Register an extension class.

        Args:
            ext_class: Extension class to register
            config: Optional config for the extension
            tags: List of tags for discovery
            dependencies: List of extension names this depends on

        Returns:
            True if successful
        """
        # Use property descriptor directly for @property decorated name attribute
        name_attr = getattr(ext_class, 'name', None)
        if name_attr is None or not hasattr(ext_class, 'name'):
            return False

        # Check if it's a property, and if so, create instance to get value
        # Check if it's a non-data property descriptor
        if isinstance(name_attr, property):
            try:
                # Create instance to get the name value
                instance = ext_class.__new__(ext_class)
                instance.__init__()
                name = instance.name
            except Exception:
                # Fallback: use class name without 'Extension' suffix
                name = ext_class.__name__.replace('Extension', '').lower()
        else:
            name = name_attr

        if not name:
            return False

        # Store the class
        self._registered[name] = ext_class

        # Store config
        if config:
            self._configs[name] = config
        else:
            self._configs[name] = ExtensionConfig(name=name)

        # Store tags
        if tags:
            for tag in tags:
                if tag not in self._tags:
                    self._tags[tag] = []
                if name not in self._tags[tag]:
                    self._tags[tag].append(name)

        # Store dependencies
        if dependencies:
            self._dependencies[name] = set(dependencies)

        # Set initial status
        self._statuses[name] = ExtensionStatus.PENDING

        return True

    def unregister(self, name: str) -> bool:
        """
        Unregister an extension by name.

        Args:
            name: Extension name to unregister

        Returns:
            True if successful
        """
        if name not in self._registered:
            return False

        # Remove from all tag lists
        for tag, names in self._tags.items():
            if name in names:
                names.remove(name)

        # Remove all stored data
        del self._registered[name]
        self._statuses.pop(name, None)
        self._configs.pop(name, None)
        self._dependencies.pop(name, None)

        return True

    def get(self, name: str) -> Optional[Type[Extension]]:
        """
        Get an extension class by name.

        Args:
            name: Extension name

        Returns:
            Extension class or None
        """
        return self._registered.get(name)

    def get_config(self, name: str) -> Optional[ExtensionConfig]:
        """Get config for an extension by name."""
        return self._configs.get(name)

    def get_status(self, name: str) -> Optional[ExtensionStatus]:
        """Get status for an extension by name."""
        return self._statuses.get(name)

    def set_status(self, name: str, status: ExtensionStatus) -> bool:
        """Set status for an extension by name."""
        if name not in self._statuses:
            return False
        self._statuses[name] = status
        return True

    def find_by_tag(self, tag: str) -> List[Type[Extension]]:
        """
        Find extensions by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of extension classes
        """
        names = self._tags.get(tag, [])
        return [self._registered[name] for name in names if name in self._registered]

    def find_by_tags(self, tags: List[str], match_all: bool = True) -> List[Type[Extension]]:
        """
        Find extensions matching tags.

        Args:
            tags: Tags to search for
            match_all: If True, must have all tags; if False, any tag

        Returns:
            List of extension classes
        """
        if not tags:
            return list(self._registered.values())

        results = set()
        for tag in tags:
            names = self._tags.get(tag, [])
            for name in names:
                if name in self._registered:
                    if not match_all:
                        results.add(self._registered[name])
                    else:
                        # Check if extension has all tags
                        ext_tags = set()
                        for t, n in self._tags.items():
                            if name in n:
                                ext_tags.add(t)
                        if ext_tags.issuperset(tags):
                            results.add(self._registered[name])

        return list(results)

    def list_all(self) -> List[Type[Extension]]:
        """List all registered extensions."""
        return list(self._registered.values())

    def list_by_status(self, status: ExtensionStatus) -> List[Type[Extension]]:
        """List extensions with a specific status."""
        result = []
        for ext_name, ext_class in self._registered.items():
            if self._statuses.get(ext_name) == status:
                result.append(ext_class)
        return result

    def list_tags(self) -> List[str]:
        """List all registered tags."""
        return list(self._tags.keys())

    def get_dependencies(self, name: str) -> List[str]:
        """Get dependencies for an extension."""
        return list(self._dependencies.get(name, []))

    def get_dependents(self, name: str) -> List[str]:
        """Get extensions that depend on this one."""
        return [
            ext_name for ext_name, deps in self._dependencies.items()
            if name in deps
        ]

    def resolve_dependencies(self, names: List[str]) -> List[str]:
        """
        Resolve extension loading order based on dependencies.

        Uses topological sort.

        Args:
            names: Extension names to resolve

        Returns:
            Names in correct loading order

        Raises:
            ValueError: If circular dependency detected
        """
        # Build subgraph of only requested extensions
        requested = set(names)
        graph: Dict[str, Set[str]] = {}

        for name in requested:
            deps = self._dependencies.get(name, set())
            graph[name] = deps & requested  # Only dependencies in requested set

        # Topological sort
        result = []
        visited: Set[str] = set()
        temp_mark: Set[str] = set()

        def visit(node: str):
            if node in temp_mark:
                raise ValueError(f"Circular dependency detected at {node}")
            if node in visited:
                return

            temp_mark.add(node)

            for dep in graph.get(node, set()):
                if dep in requested:
                    visit(dep)

            temp_mark.remove(node)
            visited.add(node)
            result.append(node)

        for name in requested:
            if name not in visited:
                visit(name)

        return result

    def is_registered(self, name: str) -> bool:
        """Check if an extension is registered."""
        return name in self._registered

    def count(self) -> int:
        """Count of registered extensions."""
        return len(self._registered)

    def clear(self) -> None:
        """Clear all registrations."""
        self._registered.clear()
        self._tags.clear()
        self._configs.clear()
        self._statuses.clear()
        self._dependencies.clear()
