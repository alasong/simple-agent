"""
Extension Loader - Load extensions from files/directories.

Supports loading from:
- Python modules (.py)
- YAML configuration files (.yaml, .yml)
- Directories (loads all valid extensions)
"""

import os
import sys
import importlib.util
from typing import Dict, List, Optional, Any, Type
from pathlib import Path
import yaml

from .base import Extension, ExtensionConfig, ExtensionStatus


class ExtensionLoader:
    """
    Loads extensions from various sources.

    Supports:
    - Python modules with Extension subclasses
    - YAML configuration files
    - Directories (recursive scanning)
    """

    def __init__(self, search_paths: List[str] = None):
        """
        Initialize loader with optional search paths.

        Args:
            search_paths: List of directories to search for extensions
        """
        self.search_paths: List[Path] = []
        if search_paths:
            for path in search_paths:
                self.search_paths.append(Path(path))

        # Cache of loaded extension classes
        self._loaded_classes: Dict[str, Type[Extension]] = {}

    def add_search_path(self, path: str) -> None:
        """Add a directory to search for extensions."""
        self.search_paths.append(Path(path))

    def load_from_module(self, module_path: str) -> Optional[Extension]:
        """
        Load an extension from a Python module.

        Args:
            module_path: Path to Python module

        Returns:
            Extension instance or None if load failed
        """
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(
                "ext_module", module_path
            )
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules["ext_module"] = module
            spec.loader.exec_module(module)

            # Find Extension subclass in module
            extension = self._find_extension_class(module)
            if extension:
                return extension()

            return None

        except Exception as e:
            print(f"[ExtensionLoader] Error loading from {module_path}: {e}")
            return None

    def load_from_yaml(self, yaml_path: str) -> Optional[Extension]:
        """
        Load an extension from a YAML configuration file.

        Args:
            yaml_path: Path to YAML configuration

        Returns:
            Extension instance or None if load failed
        """
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                return None

            # Extract extension config
            config = ExtensionConfig.from_dict(config_data)

            # Try to import the extension class
            module_path = config.config.get('module')
            class_name = config.config.get('class')

            if not module_path or not class_name:
                print(f"[ExtensionLoader] Missing module or class in {yaml_path}")
                return None

            # Import the module
            module = self._import_module(module_path)
            if not module:
                return None

            # Get the class
            ext_class = getattr(module, class_name, None)
            if not ext_class or not issubclass(ext_class, Extension):
                return None

            # Check if abstract (and not a config class which may be used for loading)
            if getattr(ext_class, '__abstractmethods__', None):
                # Abstract class - cannot instantiate
                return None

            # Create instance with config
            return ext_class(config)

        except Exception as e:
            print(f"[ExtensionLoader] Error loading from {yaml_path}: {e}")
            return None

    def load_from_directory(self, dir_path: str, recursive: bool = True) -> List[Extension]:
        """
        Load all extensions from a directory.

        Args:
            dir_path: Directory to scan
            recursive: Whether to search subdirectories

        Returns:
            List of loaded Extension instances
        """
        extensions = []
        dir_path = Path(dir_path)

        if not dir_path.exists():
            return extensions

        # Find all Python files and YAML files
        patterns = ['*.py']
        if recursive:
            patterns.append('**/*.py')
            patterns.append('**/*.yaml')
            patterns.append('**/*.yml')

        for pattern in patterns:
            for file_path in dir_path.glob(pattern):
                if file_path.name.startswith('_'):
                    continue  # Skip __pycache__, etc.

                ext = self._try_load_file(file_path)
                if ext:
                    extensions.append(ext)

        return extensions

    def scan_all(self) -> List[Extension]:
        """Scan all search paths and return loaded extensions."""
        all_extensions = []
        for path in self.search_paths:
            if path.is_dir():
                all_extensions.extend(self.load_from_directory(str(path)))
            elif path.suffix in ['.py', '.yaml', '.yml']:
                ext = self._try_load_file(path)
                if ext:
                    all_extensions.append(ext)
        return all_extensions

    def _try_load_file(self, file_path: Path) -> Optional[Extension]:
        """Try to load a single file as an extension."""
        suffix = file_path.suffix.lower()

        if suffix == '.py':
            return self.load_from_module(str(file_path))
        elif suffix in ['.yaml', '.yml']:
            return self.load_from_yaml(str(file_path))

        return None

    def _import_module(self, module_path: str) -> Optional[Any]:
        """Import a module by path."""
        try:
            # Try direct import first
            parts = module_path.split('.')
            if len(parts) >= 2:
                module_name = '.'.join(parts[:-1])
                attr_name = parts[-1]

                module = importlib.import_module(module_name)
                return getattr(module, attr_name, None)
            else:
                return importlib.import_module(module_path)
        except Exception as e:
            print(f"[ExtensionLoader] Error importing module {module_path}: {e}")
            return None

    def _find_extension_class(self, module: Any) -> Optional[Type[Extension]]:
        """
        Find the first Extension subclass in a module.

        Args:
            module: Python module object

        Returns:
            Extension subclass or None
        """
        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            # Check if it's a class that inherits from Extension
            if (
                isinstance(attr, type) and
                issubclass(attr, Extension) and
                attr != Extension and
                not getattr(attr, '__abstractmethods__', None)
            ):
                return attr

        return None

    def discover_extensions(self) -> Dict[str, Type[Extension]]:
        """
        Discover all available extensions in search paths.

        Returns:
            Dict mapping extension name to class
        """
        discovered = {}

        for path in self.search_paths:
            if not path.exists():
                continue

            for file_path in path.rglob('*.py'):
                if file_path.name.startswith('_'):
                    continue

                try:
                    spec = importlib.util.spec_from_file_location(
                        "ext_module", file_path
                    )
                    if not spec:
                        continue

                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    ext_class = self._find_extension_class(module)
                    if ext_class:
                        # Get the actual name value by creating instance
                        name = self._get_extension_name(ext_class)
                        if name:
                            discovered[name] = ext_class

                except Exception:
                    continue

        return discovered

    def _get_extension_name(self, ext_class: Type[Extension]) -> Optional[str]:
        """
        Get the extension name from an Extension class.

        Handles both @property name attributes and regular attributes.

        Args:
            ext_class: Extension class

        Returns:
            Extension name string or None
        """
        if not hasattr(ext_class, 'name'):
            return None

        try:
            # Try to create an instance to get the name
            instance = ext_class.__new__(ext_class)
            instance.__init__()
            return instance.name
        except Exception:
            # If that fails, return None
            return None
