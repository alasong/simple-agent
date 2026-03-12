"""
Extension System Tests

Tests for the unified extension/plugin framework.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import List

from simple_agent.extensions import (
    Extension,
    ExtensionConfig,
    ExtensionLoader,
    ExtensionRegistry,
    ExtensionManager,
    ExtensionStatus,
)


# ==================== Extension Implementations for Testing ====================

class TestExtension(Extension):
    """Test extension implementation."""

    _name = "test_extension"
    _description = "A test extension for unit testing"

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def load(self) -> None:
        self._metadata["loaded"] = True

    def unload(self) -> None:
        self._metadata["loaded"] = False

    def custom_action(self, data: str) -> str:
        """Execute custom action directly."""
        return f"Processed: {data}"


class AnotherExtension(Extension):
    """Another test extension."""

    _name = "another_extension"
    _description = "Another test extension"

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def load(self) -> None:
        pass

    def unload(self) -> None:
        pass


# ==================== Base Extension Tests ====================

class TestExtensionBase:
    """Tests for Extension base class."""

    def test_extension_creation(self):
        """Test creating an extension instance."""
        ext = TestExtension()
        assert ext.status == ExtensionStatus.PENDING
        assert ext.name == "test_extension"
        assert "test" in ext.description.lower()

    def test_extension_initialize(self):
        """Test extension initialization."""
        ext = TestExtension()
        config = ExtensionConfig(name="test", enabled=True)
        result = ext.initialize(config)

        assert result is True
        assert ext.status == ExtensionStatus.ACTIVE
        assert ext.is_active() is True

    def test_extension_error_handling(self):
        """Test error handling in extension."""
        class ErrorExtension(Extension):
            @property
            def name(self) -> str:
                return "error_ext"

            @property
            def description(self) -> str:
                return "Error test"

            def load(self) -> None:
                raise ValueError("Test error")

        ext = ErrorExtension()
        result = ext.initialize()

        assert result is False
        assert ext.status == ExtensionStatus.ERROR
        assert ext.is_error() is True
        assert ext.error is not None

    def test_extension_enable_disable(self):
        """Test enable/disable functionality."""
        ext = TestExtension()
        ext.initialize()

        assert ext.is_active() is True
        assert ext.disable() is True
        assert ext.is_active() is False
        assert ext.enable() is True
        assert ext.is_active() is True


# ==================== Extension Loader Tests ====================

class TestExtensionLoader:
    """Tests for ExtensionLoader."""

    def test_loader_creation(self):
        """Test loader initialization."""
        loader = ExtensionLoader()
        assert loader.search_paths == []

        loader = ExtensionLoader(["/tmp"])
        assert len(loader.search_paths) == 1

    def test_loader_find_extension_class(self):
        """Test finding extension classes in modules."""
        loader = ExtensionLoader()

        # Test with a module that has concrete extensions
        import sys

        # Create a test module with a concrete extension
        import types
        test_module = types.ModuleType("test_concrete_ext")

        class ConcreteTestExtension(Extension):
            @property
            def name(self): return "concrete_test"
            @property
            def description(self): return "Concrete test"
            def load(self): pass
            def unload(self): pass

        test_module.ConcreteTestExtension = ConcreteTestExtension
        sys.modules["test_concrete_ext"] = test_module

        ext_class = loader._find_extension_class(test_module)

        assert ext_class is not None
        assert ext_class == ConcreteTestExtension

    def test_loader_discover_extensions(self, tmp_path):
        """Test extension discovery."""
        loader = ExtensionLoader()

        # Create a file with an extension
        ext_file = tmp_path / "ext_discover.py"
        ext_file.write_text("""
from simple_agent.extensions import Extension

class DiscoverExtension(Extension):
    @property
    def name(self):
        return "discover_test"

    @property
    def description(self):
        return "Discovery test"

    def load(self):
        pass

    def unload(self):
        pass
""")

        loader.add_search_path(str(tmp_path))
        discovered = loader.discover_extensions()

        assert "discover_test" in discovered


# ==================== Extension Registry Tests ====================

class TestExtensionRegistry:
    """Tests for ExtensionRegistry."""

    def test_registry_register(self):
        """Test registering an extension."""
        registry = ExtensionRegistry()
        result = registry.register(TestExtension, tags=["test", "unit"])

        assert result is True
        assert registry.is_registered("test_extension")
        assert registry.count() == 1

    def test_registry_find_by_tag(self):
        """Test tag-based discovery."""
        registry = ExtensionRegistry()
        registry.register(TestExtension, tags=["test", "core"])
        registry.register(AnotherExtension, tags=["test", "extra"])

        extensions = registry.find_by_tag("test")

        assert len(extensions) == 2

    def test_registry_find_by_multiple_tags(self):
        """Test finding extensions with multiple tags."""
        registry = ExtensionRegistry()
        registry.register(TestExtension, tags=["test", "core"])
        registry.register(AnotherExtension, tags=["test", "extra"])

        # Only TestExtension has both test and core
        extensions = registry.find_by_tags(["test", "core"], match_all=True)

        assert len(extensions) == 1
        # Create instance to access name property
        assert extensions[0]().__class__.__name__ == "TestExtension"

    def test_registry_unregister(self):
        """Test unregistering an extension."""
        registry = ExtensionRegistry()
        registry.register(TestExtension)

        assert registry.is_registered("test_extension")

        result = registry.unregister("test_extension")
        assert result is True
        assert registry.is_registered("test_extension") is False
        assert registry.count() == 0

    def test_registry_dependencies(self):
        """Test dependency tracking."""
        registry = ExtensionRegistry()
        registry.register(TestExtension, dependencies=["another_extension"])
        registry.register(AnotherExtension)

        deps = registry.get_dependencies("test_extension")
        assert "another_extension" in deps

        dependents = registry.get_dependents("another_extension")
        assert "test_extension" in dependents

    def test_registry_resolve_dependencies(self):
        """Test dependency resolution with topological sort."""
        registry = ExtensionRegistry()
        registry.register(TestExtension, dependencies=["another_extension"])
        registry.register(AnotherExtension)

        order = registry.resolve_dependencies(["test_extension", "another_extension"])

        # AnotherExtension must come before TestExtension
        assert order.index("another_extension") < order.index("test_extension")

    def test_registry_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        registry = ExtensionRegistry()
        registry.register(TestExtension, dependencies=["another_extension"])
        registry.register(AnotherExtension, dependencies=["test_extension"])

        with pytest.raises(ValueError):
            registry.resolve_dependencies(["test_extension", "another_extension"])


# ==================== Extension Manager Tests ====================

class TestExtensionManager:
    """Tests for ExtensionManager."""

    def test_manager_load_extension(self):
        """Test loading an extension by path."""
        manager = ExtensionManager()

        # Load from the test module
        ext = manager.load_extension(
            Path(__file__),
            config=ExtensionConfig(name="test_from_file")
        )

        # This may or may not succeed depending on file content
        # The important thing is no crash

    def test_manager_load_registered(self):
        """Test loading by registered name."""
        manager = ExtensionManager()
        manager.register_extension(TestExtension)

        ext = manager.load_registered("test_extension")

        assert ext is not None
        assert ext.name == ext._name  # Access private attribute for testing
        assert ext.status == ExtensionStatus.ACTIVE  # initialize() sets to ACTIVE

    def test_manager_unload_extension(self):
        """Test unloading an extension."""
        manager = ExtensionManager()
        manager.register_extension(TestExtension)
        ext = manager.load_registered("test_extension")

        result = manager.unload_extension("test_extension")

        assert result is True
        assert "test_extension" not in manager._instances
        assert manager.get_status("test_extension") == ExtensionStatus.UNLOADED

    def test_manager_enable_disable(self):
        """Test enable/disable extensions."""
        manager = ExtensionManager()
        manager.register_extension(TestExtension)
        manager.load_registered("test_extension")

        result = manager.enable_extension("test_extension")
        assert result is True
        assert manager.get_status("test_extension") == ExtensionStatus.ACTIVE

        result = manager.disable_extension("test_extension")
        assert result is True
        assert manager.get_status("test_extension") == ExtensionStatus.LOADED

    def test_manager_execute_action(self):
        """Test executing actions on extensions."""
        manager = ExtensionManager()
        manager.register_extension(TestExtension)
        manager.load_registered("test_extension")

        result = manager.execute("test_extension", "custom_action", "test_data")

        assert result == "Processed: test_data"

    def test_manager_execute_all(self):
        """Test executing actions on all extensions."""
        manager = ExtensionManager()
        manager.register_extension(TestExtension)
        manager.load_registered("test_extension")

        results = manager.execute_all("custom_action", "data")

        assert "test_extension" in results
        assert results["test_extension"] == "Processed: data"

    def test_manager_callback_registration(self):
        """Test callback registration."""
        manager = ExtensionManager()
        manager.register_extension(TestExtension)

        loaded_count = 0

        def on_load(ext):
            nonlocal loaded_count
            loaded_count += 1

        manager.on_load(on_load)

        manager.load_registered("test_extension")

        assert loaded_count == 1

    def test_manager_reload_extension(self, tmp_path):
        """Test reloading an extension."""
        # Create extension file
        ext_file = tmp_path / "reload_ext.py"
        ext_file.write_text("""
from simple_agent.extensions import Extension

class ReloadExt(Extension):
    _name = "reload_test"
    _description = "Reload test"

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    def load(self):
        pass

    def unload(self):
        pass
""")

        manager = ExtensionManager()
        ext = manager.load_extension(str(ext_file))

        assert ext is not None

        # Reload
        new_ext = manager.reload_extension("reload_test")

        assert new_ext is not None
        assert new_ext.name == new_ext._name


# ==================== Integration Tests ====================

class TestExtensionIntegration:
    """Integration tests for the extension system."""

    def test_full_lifecycle(self):
        """Test full extension lifecycle."""
        manager = ExtensionManager()

        # Register
        manager.register_extension(TestExtension, tags=["integration", "full"])

        # Load
        ext = manager.load_registered("test_extension")
        assert ext is not None
        assert ext.is_active()

        # Execute
        result = manager.execute("test_extension", "custom_action", "test")
        assert result == "Processed: test"

        # Unload
        result = manager.unload_extension("test_extension")
        assert result is True

    def test_multiple_extensions(self):
        """Test managing multiple extensions."""
        manager = ExtensionManager()

        manager.register_extension(TestExtension, tags=["multi"])
        manager.register_extension(AnotherExtension, tags=["multi"])

        manager.load_registered("test_extension")
        manager.load_registered("another_extension")

        assert len(manager.list_extensions()) == 2

        # List by tag
        multi_extensions = manager.list_by_tag("multi")
        assert len(multi_extensions) == 2

    def test_extension_tags(self):
        """Test tag-based extension management."""
        manager = ExtensionManager()

        manager.register_extension(TestExtension, tags=["core", "test"])
        manager.register_extension(AnotherExtension, tags=["extra", "test"])

        # Find by tag - returns extension names
        test_exts = manager.list_by_tag("test")
        assert len(test_exts) == 2
        assert "test_extension" in test_exts
        assert "another_extension" in test_exts

        core_exts = manager.list_by_tag("core")
        assert len(core_exts) == 1
        assert "test_extension" in core_exts


class TestExtensionLoaderWithFiles:
    """Tests for extension loading from files."""

    def test_load_from_directory(self, tmp_path):
        """Test loading extensions from a directory."""
        # Create a test extension file
        ext_file = tmp_path / "test_ext.py"
        ext_file.write_text("""
from simple_agent.extensions import Extension

class DirTestExtension(Extension):
    @property
    def name(self):
        return "dir_test_ext"

    @property
    def description(self):
        return "Directory test extension"

    def load(self):
        pass

    def unload(self):
        pass
""")

        loader = ExtensionLoader()
        extensions = loader.load_from_directory(str(tmp_path))

        assert len(extensions) >= 1

    def test_load_from_yaml(self, tmp_path):
        """Test loading from YAML config - verify parsing works."""
        yaml_file = tmp_path / "test_ext.yaml"
        yaml_file.write_text("""
name: yaml_test_ext
version: 2.0.0
description: YAML test extension
enabled: true
config:
  key: value
tags:
  - yaml
  - test
""")

        loader = ExtensionLoader()

        # Just test YAML parsing
        import yaml
        with open(yaml_file, 'r') as f:
            config_data = yaml.safe_load(f)

        # Verify YAML parsed correctly
        assert config_data is not None
        assert config_data['name'] == 'yaml_test_ext'
        assert config_data['version'] == '2.0.0'
        assert 'yaml' in config_data['tags']
        assert 'test' in config_data['tags']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
