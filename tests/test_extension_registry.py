"""
Extension Registry Tests

Tests for the ExtensionRegistry class.
"""

import pytest

from simple_agent.extensions import (
    Extension,
    ExtensionConfig,
    ExtensionRegistry,
    ExtensionStatus,
)


class SimpleExtension(Extension):
    """Simple test extension."""

    @property
    def name(self) -> str:
        return "simple"

    @property
    def description(self) -> str:
        return "Simple extension"

    def load(self) -> None:
        pass

    def unload(self) -> None:
        pass


class ComplexExtension(Extension):
    """Complex test extension."""

    @property
    def name(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "Complex extension"

    def load(self) -> None:
        pass

    def unload(self) -> None:
        pass


class FeatureExtension(Extension):
    """Feature extension for tag testing."""

    @property
    def name(self) -> str:
        return "feature"

    @property
    def description(self) -> str:
        return "Feature extension"

    def load(self) -> None:
        pass

    def unload(self) -> None:
        pass


# ==================== Registration Tests ====================

class TestRegistryRegistration:
    """Tests for extension registration."""

    def test_register_extension(self):
        """Test basic registration."""
        registry = ExtensionRegistry()

        result = registry.register(SimpleExtension)

        assert result is True
        assert registry.is_registered("simple")
        assert registry.get("simple") == SimpleExtension

    def test_register_with_config(self):
        """Test registration with config."""
        registry = ExtensionRegistry()
        config = ExtensionConfig(
            name="simple",
            version="1.2.3",
            description="Test config",
            enabled=False,
            tags=["test", "unit"],
            dependencies=["complex"]
        )

        result = registry.register(SimpleExtension, config=config)

        assert result is True
        saved_config = registry.get_config("simple")
        assert saved_config is not None
        assert saved_config.version == "1.2.3"
        assert saved_config.enabled is False

    def test_register_with_tags(self):
        """Test registration with tags."""
        registry = ExtensionRegistry()

        registry.register(
            SimpleExtension,
            tags=["core", "basic", "python"]
        )
        registry.register(
            ComplexExtension,
            tags=["core", "advanced", "python"]
        )

        # Should have all tags registered
        tags = registry.list_tags()
        assert "core" in tags
        assert "basic" in tags
        assert "advanced" in tags
        assert "python" in tags

    def test_register_multiple_extensions(self):
        """Test registering multiple extensions."""
        registry = ExtensionRegistry()

        registry.register(SimpleExtension, tags=["a"])
        registry.register(ComplexExtension, tags=["b"])
        registry.register(FeatureExtension, tags=["c"])

        assert registry.count() == 3


# ==================== Tags Tests ====================

class TestRegistryTags:
    """Tests for tag-based operations."""

    def test_find_by_single_tag(self):
        """Test finding extensions by single tag."""
        registry = ExtensionRegistry()

        registry.register(SimpleExtension, tags=["test", "unit"])
        registry.register(ComplexExtension, tags=["test", "integration"])
        registry.register(FeatureExtension, tags=["feature", "dev"])

        # Find all test extensions
        test_exts = registry.find_by_tag("test")
        assert len(test_exts) == 2
        # Create instances to access name property
        # Create instances to access name property
        names = {e(None)._name if hasattr(e(None), '_name') else e(None).name for e in test_exts}
        assert "simple" in names
        assert "complex" in names

    def test_find_by_multiple_tags_any(self):
        """Test finding extensions matching any of multiple tags."""
        registry = ExtensionRegistry()
        registry.register(SimpleExtension, tags=["a", "b"])
        registry.register(ComplexExtension, tags=["c", "d"])
        registry.register(FeatureExtension, tags=["e", "f"])

        results = registry.find_by_tags(["b", "d"], match_all=False)

        # Should find both simple and complex
        assert len(results) == 2

    def test_find_by_multiple_tags_all(self):
        """Test finding extensions matching all of multiple tags."""
        registry = ExtensionRegistry()
        registry.register(SimpleExtension, tags=["core", "test", "python"])
        registry.register(ComplexExtension, tags=["core", "test", "java"])
        registry.register(FeatureExtension, tags=["core", "feature", "python"])

        # Find extensions with both core and test
        results = registry.find_by_tags(["core", "test"], match_all=True)

        assert len(results) == 2
        # Create instances to access name property
        names = {e(None).name for e in results}
        assert "simple" in names
        assert "complex" in names

    def test_find_empty_tags(self):
        """Test finding with no tags returns all."""
        registry = ExtensionRegistry()
        registry.register(SimpleExtension, tags=["a"])
        registry.register(ComplexExtension, tags=["b"])

        results = registry.find_by_tags([])

        assert len(results) == 2


# ==================== Unregistration Tests ====================

class TestRegistryUnregistration:
    """Tests for unregistering extensions."""

    def test_unregister_extension(self):
        """Test unregistering a single extension."""
        registry = ExtensionRegistry()
        registry.register(SimpleExtension, tags=["test"])

        result = registry.unregister("simple")

        assert result is True
        assert registry.is_registered("simple") is False
        assert registry.count() == 0

    def test_unregister_removes_tags(self):
        """Test unregistering removes tag references."""
        registry = ExtensionRegistry()
        registry.register(SimpleExtension, tags=["core", "test"])

        registry.unregister("simple")

        # Tag should be empty or not contain simple
        test_exts = registry.find_by_tag("test")
        assert "simple" not in [e.name for e in test_exts]

    def test_unregister_nonexistent(self):
        """Test unregistering non-existent extension."""
        registry = ExtensionRegistry()

        result = registry.unregister("nonexistent")

        assert result is False

    def test_unregister_all(self):
        """Test clearing all registrations."""
        registry = ExtensionRegistry()
        registry.register(SimpleExtension)
        registry.register(ComplexExtension)

        registry.clear()

        assert registry.count() == 0
        assert len(registry.list_tags()) == 0


# ==================== Status Tests ====================

class TestRegistryStatus:
    """Tests for status management."""

    def test_set_status(self):
        """Test setting extension status."""
        registry = ExtensionRegistry()
        registry.register(SimpleExtension)

        result = registry.set_status("simple", ExtensionStatus.LOADED)

        assert result is True
        assert registry.get_status("simple") == ExtensionStatus.LOADED

    def test_set_status_nonexistent(self):
        """Test setting status for non-existent extension."""
        registry = ExtensionRegistry()

        result = registry.set_status("nonexistent", ExtensionStatus.LOADED)

        assert result is False

    def test_list_by_status(self):
        """Test listing extensions by status."""
        registry = ExtensionRegistry()
        registry.register(SimpleExtension)
        registry.register(ComplexExtension)

        registry.set_status("simple", ExtensionStatus.LOADED)
        registry.set_status("complex", ExtensionStatus.ACTIVE)

        loaded = registry.list_by_status(ExtensionStatus.LOADED)
        active = registry.list_by_status(ExtensionStatus.ACTIVE)

        assert len(loaded) == 1
        assert loaded[0](None).name == "simple"
        assert len(active) == 1
        assert active[0](None).name == "complex"


# ==================== Dependency Tests ====================

class TestRegistryDependencies:
    """Tests for dependency management."""

    def test_register_dependencies(self):
        """Test registering with dependencies."""
        registry = ExtensionRegistry()

        registry.register(ComplexExtension)
        registry.register(SimpleExtension, dependencies=["complex"])

        deps = registry.get_dependencies("simple")
        assert "complex" in deps

    def test_get_dependents(self):
        """Test getting dependents of an extension."""
        registry = ExtensionRegistry()

        registry.register(SimpleExtension, dependencies=["complex"])
        registry.register(ComplexExtension)

        dependents = registry.get_dependents("complex")
        assert "simple" in dependents

    def test_get_dependents_none(self):
        """Test getting dependents when none exist."""
        registry = ExtensionRegistry()
        registry.register(SimpleExtension)

        dependents = registry.get_dependents("simple")

        assert len(dependents) == 0

    def test_dependency_graph(self):
        """Test complex dependency graph."""
        registry = ExtensionRegistry()

        registry.register(SimpleExtension, dependencies=["complex"])
        registry.register(ComplexExtension, dependencies=["feature"])
        registry.register(FeatureExtension)

        # Check all dependencies
        assert "complex" in registry.get_dependencies("simple")
        assert "feature" in registry.get_dependencies("complex")
        assert len(registry.get_dependencies("feature")) == 0


# ==================== Resolution Tests ====================

class TestRegistryResolution:
    """Tests for dependency resolution."""

    def test_resolve_linear_dependencies(self):
        """Test resolving linear dependencies."""
        registry = ExtensionRegistry()

        registry.register(SimpleExtension, dependencies=["complex"])
        registry.register(ComplexExtension, dependencies=["feature"])
        registry.register(FeatureExtension)

        order = registry.resolve_dependencies(
            ["simple", "complex", "feature"]
        )

        # Feature must come first
        assert order.index("feature") < order.index("complex")
        assert order.index("complex") < order.index("simple")

    def test_resolve_single_extension(self):
        """Test resolving single extension."""
        registry = ExtensionRegistry()
        registry.register(SimpleExtension)

        order = registry.resolve_dependencies(["simple"])

        assert order == ["simple"]

    def test_resolve_no_dependencies(self):
        """Test resolving extensions with no dependencies."""
        registry = ExtensionRegistry()

        registry.register(SimpleExtension)
        registry.register(ComplexExtension)
        registry.register(FeatureExtension)

        order = registry.resolve_dependencies(
            ["simple", "complex", "feature"]
        )

        assert len(order) == 3
        assert set(order) == {"simple", "complex", "feature"}

    def test_resolve_partial(self):
        """Test resolving only some extensions."""
        registry = ExtensionRegistry()

        registry.register(SimpleExtension, dependencies=["complex"])
        registry.register(ComplexExtension, dependencies=["feature"])
        registry.register(FeatureExtension)

        # Only resolve simple and complex
        order = registry.resolve_dependencies(["simple", "complex"])

        assert len(order) == 2
        assert order.index("complex") < order.index("simple")


# ==================== Edge Cases ====================

class TestRegistryEdgeCases:
    """Tests for edge cases."""

    def test_duplicate_registration(self):
        """Test registering same extension twice."""
        registry = ExtensionRegistry()

        registry.register(SimpleExtension)
        result = registry.register(SimpleExtension)

        # Should succeed (overwrite)
        assert result is True
        assert registry.count() == 1

    def test_extension_without_name(self):
        """Test registering extension without name property will use fallback."""
        class NoNameExtension(Extension):
            @property
            def description(self) -> str:
                return "No name"

            def load(self) -> None:
                pass

            def unload(self) -> None:
                pass

        registry = ExtensionRegistry()

        result = registry.register(NoNameExtension)

        # Should use fallback name (class name without 'Extension' suffix)
        assert result is True
        assert registry.is_registered("noname")  # NoNameExtension -> noname

    def test_empty_registry(self):
        """Test operations on empty registry."""
        registry = ExtensionRegistry()

        assert registry.count() == 0
        assert registry.get("nonexistent") is None
        assert registry.find_by_tag("nonexistent") == []
        assert registry.list_tags() == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
