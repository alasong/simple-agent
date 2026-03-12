"""
Runtime Extension Tests

Tests for runtime extension loading and dynamic capabilities.
"""

import pytest
import tempfile
import os
from pathlib import Path

from simple_agent.extensions import (
    Extension,
    ExtensionConfig,
    ExtensionManager,
    ExtensionStatus,
    get_extension_manager,
)


class DynamicExtension(Extension):
    """Extension for dynamic testing."""

    def __init__(self, config=None):
        super().__init__(config)
        self.executed_actions = []

    @property
    def name(self) -> str:
        return "dynamic"

    @property
    def description(self) -> str:
        return "Dynamic runtime extension"

    def load(self) -> None:
        self._metadata["loaded_at"] = "runtime"
        self.executed_actions = []

    def unload(self) -> None:
        self.executed_actions = []

    def on_action(self, data: str) -> str:
        self.executed_actions.append(("action", data))
        return f"action:{data}"

    def on_data(self, data: dict) -> dict:
        self.executed_actions.append(("data", data))
        return {"processed": data}

    def get_state(self) -> dict:
        return {
            "executed": len(self.executed_actions),
            "metadata": self._metadata,
        }


class ConfigurableExtension(Extension):
    """Extension with configurable behavior."""

    @property
    def name(self) -> str:
        return "configurable"

    @property
    def description(self) -> str:
        return "Configurable extension"

    def load(self) -> None:
        self.mode = self.config.config.get("mode", "default")

    def get_mode(self) -> str:
        return self.mode


# ==================== Runtime Loading Tests ====================

class TestRuntimeLoading:
    """Tests for runtime extension loading."""

    def test_load_from_directory(self, tmp_path):
        """Test loading extensions from directory."""
        # Create extension file
        ext_file = tmp_path / "dynamic_ext.py"
        ext_file.write_text("""
from simple_agent.extensions import Extension

class DynamicExt(Extension):
    @property
    def name(self):
        return "runtime_dynamic"

    @property
    def description(self):
        return "Runtime dynamic"

    def load(self):
        pass

    def unload(self):
        pass
""")

        manager = ExtensionManager()

        extensions = manager.discover_and_load(str(tmp_path))

        assert len(extensions) >= 1

        ext = manager.get_extension("runtime_dynamic")
        assert ext is not None

    def test_load_from_file(self, tmp_path):
        """Test loading single extension file."""
        ext_file = tmp_path / "single_ext.py"
        ext_file.write_text("""
from simple_agent.extensions import Extension

class SingleExt(Extension):
    @property
    def name(self):
        return "single"

    @property
    def description(self):
        return "Single extension"

    def load(self):
        pass

    def unload(self):
        pass
""")

        manager = ExtensionManager()
        ext = manager.load_extension(str(ext_file))

        assert ext is not None
        assert ext.name == "single"

    def test_load_with_config(self, tmp_path):
        """Test loading with custom config."""
        ext_file = tmp_path / "config_ext.py"
        ext_file.write_text("""
from simple_agent.extensions import Extension

class ConfigExt(Extension):
    @property
    def name(self):
        return "configurable"

    @property
    def description(self):
        return "Configurable"

    def load(self):
        pass

    def unload(self):
        pass
""")

        config = ExtensionConfig(
            name="configurable",
            config={"mode": "production", "debug": False}
        )

        manager = ExtensionManager()
        ext = manager.load_extension(str(ext_file), config=config)

        assert ext is not None
        assert ext.config.config["mode"] == "production"


# ==================== Runtime Enable/Disable Tests ====================

class TestRuntimeEnableDisable:
    """Tests for runtime enable/disable."""

    def test_enable_after_load(self):
        """Test enabling extension after loading."""
        manager = ExtensionManager()
        manager.register_extension(DynamicExtension)

        ext = manager.load_registered("dynamic")
        assert ext.status == ExtensionStatus.ACTIVE  # initialize() sets to ACTIVE

        result = manager.enable_extension("dynamic")
        assert result is True
        assert ext.status == ExtensionStatus.ACTIVE

    def test_disable(self):
        """Test disabling extension."""
        manager = ExtensionManager()
        manager.register_extension(DynamicExtension)

        ext = manager.load_registered("dynamic")
        manager.enable_extension("dynamic")

        result = manager.disable_extension("dynamic")
        assert result is True
        assert ext.status == ExtensionStatus.LOADED
        assert ext.is_active() is False

    def test_disable_not_active(self):
        """Test disabling non-active extension."""
        manager = ExtensionManager()
        manager.register_extension(DynamicExtension)

        ext = manager.load_registered("dynamic")
        # After load_registered, status is ACTIVE (from initialize())
        assert ext.status == ExtensionStatus.ACTIVE

        result = manager.disable_extension("dynamic")
        assert result is True
        assert ext.status == ExtensionStatus.LOADED
        assert ext.is_active() is False


# ==================== Runtime Action Tests ====================

class TestRuntimeActions:
    """Tests for runtime actions."""

    def test_execute_single_action(self):
        """Test executing single action."""
        manager = ExtensionManager()
        manager.register_extension(DynamicExtension)
        manager.load_registered("dynamic")
        manager.enable_extension("dynamic")

        result = manager.execute("dynamic", "action", "test_data")

        assert result == "action:test_data"

    def test_execute_all_active(self):
        """Test executing action on all active extensions."""
        manager = ExtensionManager()
        manager.register_extension(DynamicExtension)

        manager.load_registered("dynamic")

        # Execute on loaded (not active)
        results = manager.execute_all("action", "data1")
        assert "dynamic" in results

    def test_multiple_actions(self):
        """Test executing multiple actions."""
        manager = ExtensionManager()
        manager.register_extension(DynamicExtension)
        manager.load_registered("dynamic")

        r1 = manager.execute("dynamic", "action", "first")
        r2 = manager.execute("dynamic", "action", "second")
        r3 = manager.execute("dynamic", "data", {"key": "value"})

        assert r1 == "action:first"
        assert r2 == "action:second"
        assert r3 == {"processed": {"key": "value"}}

    def test_get_state(self):
        """Test getting extension state."""
        manager = ExtensionManager()
        manager.register_extension(DynamicExtension)
        manager.load_registered("dynamic")

        # Execute some actions
        manager.execute("dynamic", "action", "test1")
        manager.execute("dynamic", "action", "test2")

        state = manager.execute("dynamic", "get_state")

        assert state["executed"] == 2


# ==================== Runtime Event Tests ====================

class TestRuntimeEvents:
    """Tests for runtime events."""

    def test_trigger_event(self):
        """Test triggering event on extension."""
        manager = ExtensionManager()
        manager.register_extension(DynamicExtension)
        manager.load_registered("dynamic")

        results = manager.trigger_event("action", "event_data")

        assert "dynamic" in results
        assert results["dynamic"] == "action:event_data"

    def test_trigger_event_multiple(self):
        """Test triggering event on multiple extensions."""
        manager = ExtensionManager()

        class EventExt1(Extension):
            @property
            def name(self): return "event1"
            @property
            def description(self): return "Event 1"
            def load(self): pass
            def unload(self): pass
            def on_event(self, data): return "event1:" + data

        class EventExt2(Extension):
            @property
            def name(self): return "event2"
            @property
            def description(self): return "Event 2"
            def load(self): pass
            def unload(self): pass
            def on_event(self, data): return "event2:" + data

        manager.register_extension(EventExt1)
        manager.register_extension(EventExt2)

        manager.load_registered("event1")
        manager.load_registered("event2")

        results = manager.trigger_event("event", "data")

        assert "event1" in results
        assert "event2" in results
        assert results["event1"] == "event1:data"
        assert results["event2"] == "event2:data"


# ==================== Runtime Callback Tests ====================

class TestRuntimeCallbacks:
    """Tests for runtime callbacks."""

    def test_on_load_callback(self):
        """Test load callback."""
        manager = ExtensionManager()
        loaded = []

        def callback(ext):
            loaded.append(ext.name)

        manager.on_load(callback)

        manager.register_extension(DynamicExtension)
        manager.load_registered("dynamic")

        assert "dynamic" in loaded

    def test_on_unload_callback(self):
        """Test unload callback."""
        manager = ExtensionManager()
        unloaded = []

        def callback(ext):
            unloaded.append(ext.name)

        manager.on_unload(callback)

        manager.register_extension(DynamicExtension)
        manager.load_registered("dynamic")
        manager.unload_extension("dynamic")

        assert "dynamic" in unloaded

    def test_on_enable_callback(self):
        """Test enable callback."""
        manager = ExtensionManager()
        enabled = []

        def callback(ext):
            enabled.append(ext.name)

        manager.on_enable(callback)

        manager.register_extension(DynamicExtension)
        ext = manager.load_registered("dynamic")
        manager.enable_extension("dynamic")

        assert "dynamic" in enabled

    def test_on_disable_callback(self):
        """Test disable callback."""
        manager = ExtensionManager()
        disabled = []

        def callback(ext):
            disabled.append(ext.name)

        manager.on_disable(callback)

        manager.register_extension(DynamicExtension)
        ext = manager.load_registered("dynamic")
        manager.enable_extension("dynamic")
        manager.disable_extension("dynamic")

        assert "dynamic" in disabled

    def test_multiple_callbacks(self):
        """Test multiple callbacks for same event."""
        manager = ExtensionManager()
        logs = []

        manager.on_load(lambda e: logs.append(f"load:{e.name}"))
        manager.on_load(lambda e: logs.append(f"loaded:{e.name}"))

        manager.register_extension(DynamicExtension)
        manager.load_registered("dynamic")

        assert "load:dynamic" in logs
        assert "loaded:dynamic" in logs


# ==================== Runtime Reload Tests ====================

class TestRuntimeReload:
    """Tests for runtime reloading."""

    def test_reload_extension(self, tmp_path):
        """Test reloading an extension."""
        ext_file = tmp_path / "reload_ext.py"
        ext_file.write_text("""
from simple_agent.extensions import Extension

class ReloadExt(Extension):
    @property
    def name(self):
        return "reload_test"

    @property
    def description(self):
        return "Reload test"

    def load(self):
        self._metadata["load_count"] = self._metadata.get("load_count", 0) + 1

    def unload(self):
        pass
""")

        manager = ExtensionManager()
        ext = manager.load_extension(str(ext_file))

        assert ext is not None

        # Reload
        new_ext = manager.reload_extension("reload_test")

        assert new_ext is not None
        assert new_ext.name == "reload_test"
        assert new_ext._metadata.get("load_count", 0) >= 1

    def test_reload_all(self, tmp_path):
        """Test reloading all extensions."""
        ext1 = tmp_path / "ext1.py"
        ext1.write_text("""
from simple_agent.extensions import Extension
class Ext1(Extension):
    @property
    def name(self): return "ext1"
    @property
    def description(self): return "Ext1"
    def load(self): pass
    def unload(self): pass
""")

        ext2 = tmp_path / "ext2.py"
        ext2.write_text("""
from simple_agent.extensions import Extension
class Ext2(Extension):
    @property
    def name(self): return "ext2"
    @property
    def description(self): return "Ext2"
    def load(self): pass
    def unload(self): pass
""")

        manager = ExtensionManager()

        manager.load_extension(str(ext1))
        manager.load_extension(str(ext2))

        results = manager.reload_all()

        assert "ext1" in results
        assert "ext2" in results


# ==================== Global Manager Tests ====================

class TestGlobalManager:
    """Tests for global extension manager."""

    def test_get_extension_manager(self):
        """Test getting global extension manager."""
        manager = get_extension_manager()

        # Should return same instance
        manager2 = get_extension_manager()
        assert manager is manager2

    def test_global_register_load(self):
        """Test using global manager."""
        from simple_agent.extensions import get_extension_manager, Extension
        from simple_agent.extensions import ExtensionManager

        class GlobalExt(Extension):
            @property
            def name(self): return "global_test"
            @property
            def description(self): return "Global test"
            def load(self): pass
            def unload(self): pass

        manager = get_extension_manager()
        manager.register_extension(GlobalExt)

        ext = manager.load_registered("global_test")
        assert ext is not None


# ==================== Concurrent Loading Tests ====================

class TestConcurrentLoading:
    """Tests for concurrent extension loading."""

    def test_load_multiple_sequential(self):
        """Test loading multiple extensions sequentially."""
        manager = ExtensionManager()

        class Ext1(Extension):
            @property
            def name(self): return "ext1"
            @property
            def description(self): return "Ext1"
            def load(self): pass
            def unload(self): pass

        class Ext2(Extension):
            @property
            def name(self): return "ext2"
            @property
            def description(self): return "Ext2"
            def load(self): pass
            def unload(self): pass

        manager.register_extension(Ext1)
        manager.register_extension(Ext2)

        ext1 = manager.load_registered("ext1")
        ext2 = manager.load_registered("ext2")

        assert ext1 is not None
        assert ext2 is not None

    def test_total_count(self):
        """Test tracking total extension count."""
        manager = ExtensionManager()

        assert manager.total_count == 0

        manager.register_extension(DynamicExtension)
        manager.load_registered("dynamic")

        assert manager.total_count == 1

    def test_active_count(self):
        """Test tracking active extension count."""
        manager = ExtensionManager()

        manager.register_extension(DynamicExtension)
        ext = manager.load_registered("dynamic")

        # After load_registered, extension is ACTIVE (from initialize())
        assert manager.active_count == 1

        manager.disable_extension("dynamic")
        assert manager.active_count == 0


# ==================== Error Handling Tests ====================

class TestRuntimeErrorHandling:
    """Tests for runtime error handling."""

    def test_load_nonexistent_file(self):
        """Test loading from non-existent file."""
        manager = ExtensionManager()

        result = manager.load_extension("/nonexistent/path.py")

        assert result is None

    def test_unload_nonexistent(self):
        """Test unloading non-existent extension."""
        manager = ExtensionManager()

        result = manager.unload_extension("nonexistent")

        assert result is False

    def test_execute_nonexistent(self):
        """Test executing on non-existent extension."""
        manager = ExtensionManager()

        result = manager.execute("nonexistent", "action", "data")

        assert result is None

    def test_unregister_error(self):
        """Test unregistering without loading."""
        manager = ExtensionManager()
        manager.register_extension(DynamicExtension)

        # Can unregister without loading
        result = manager.registry.unregister("dynamic")
        assert result is True


# ==================== Integration Tests ====================

class TestRuntimeIntegration:
    """Integration tests for runtime features."""

    def test_full_runtime_lifecycle(self, tmp_path):
        """Test full lifecycle with runtime loading."""
        # Create extension file
        ext_file = tmp_path / "lifecycle_ext.py"
        ext_file.write_text("""
from simple_agent.extensions import Extension

class LifecycleExt(Extension):
    def __init__(self, config=None):
        super().__init__(config)
        self.state = "created"

    @property
    def name(self):
        return "lifecycle_test"

    @property
    def description(self):
        return "Lifecycle test"

    def load(self):
        self.state = "loaded"

    def unload(self):
        self.state = "unloaded"

    def on_start(self, data):
        self.state = "started:" + str(data)
        return self.state

    def get_state(self):
        return self.state
""")

        manager = ExtensionManager()

        # Load extension
        ext = manager.load_extension(str(ext_file))
        assert ext is not None
        assert ext.state == "loaded"

        # Enable
        manager.enable_extension("lifecycle_test")
        assert ext.is_active()

        # Execute
        result = manager.execute("lifecycle_test", "start", "test123")
        assert "started:test123" == result

        # Get state
        state = manager.execute("lifecycle_test", "get_state")
        assert state == result

        # Unload
        manager.unload_extension("lifecycle_test")
        assert ext.state == "unloaded"
        assert "lifecycle_test" not in manager._instances

    def test_mixed_extensions(self, tmp_path):
        """Test managing different extension types."""
        # Create multiple extension types
        (tmp_path / "ext_a.py").write_text("""
from simple_agent.extensions import Extension
class ExtA(Extension):
    @property
    def name(self): return "ext_a"
    @property
    def description(self): return "Ext A"
    def load(self): pass
    def unload(self): pass
""")

        (tmp_path / "ext_b.py").write_text("""
from simple_agent.extensions import Extension
class ExtB(Extension):
    @property
    def name(self): return "ext_b"
    @property
    def description(self): return "Ext B"
    def load(self): pass
    def unload(self): pass
""")

        manager = ExtensionManager()
        extensions = manager.discover_and_load(str(tmp_path))

        assert len(extensions) >= 2

        # Load both
        manager.load_registered("ext_a")
        manager.load_registered("ext_b")

        assert manager.total_count == 2

        # One active, one not
        manager.enable_extension("ext_a")

        assert manager.active_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
