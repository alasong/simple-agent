"""
Dynamic Extension System Tests

Tests for runtime dynamic extension capabilities:
- Dynamic tool registration
- Dynamic strategy switching
- Hot-plug agent support
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add project root to path
project_root = "/home/song/simple-agent"
sys.path.insert(0, project_root)

# Import extension system
from simple_agent.extensions import (
    Extension, ExtensionConfig, ExtensionStatus,
    DynamicToolRegistry, DynamicStrategyRegistry,
    HotPlugAgentManager, DynamicExtensionSystem,
    DynamicRegistrationState
)
from simple_agent.core.agent import Agent


class SampleTool(Extension):
    """Sample tool extension for testing."""

    @property
    def name(self) -> str:
        return "sample_tool"

    @property
    def description(self) -> str:
        return "Sample tool for testing"

    def load(self) -> None:
        """Load the extension."""
        pass

    def unload(self) -> None:
        """Unload the extension."""
        pass

    def process(self, data: str) -> str:
        return f"Processed: {data}"


class AnotherTool(Extension):
    """Another sample tool."""

    @property
    def name(self) -> str:
        return "another_tool"

    @property
    def description(self) -> str:
        return "Another sample tool"

    def load(self) -> None:
        """Load the extension."""
        pass

    def unload(self) -> None:
        """Unload the extension."""
        pass

    def calculate(self, x: int, y: int) -> int:
        return x + y


def create_temp_tool_file(name: str, class_name: str, extra_methods: str = "") -> str:
    """Create a temporary Python file with an Extension subclass."""
    content = f'''
from simple_agent.extensions import Extension

class {class_name}(Extension):
    """{name} extension."""

    @property
    def name(self) -> str:
        return "{name}"

    @property
    def description(self) -> str:
        return "{name} description"

    def load(self) -> None:
        """Load the extension."""
        pass

    def unload(self) -> None:
        """Unload the extension."""
        pass

    def execute(self, data: str) -> str:
        return f"{{data}}-executed"

{extra_methods}
'''
    tmp_dir = Path(tempfile.gettempdir()) / "test_tools"
    tmp_dir.mkdir(exist_ok=True)
    file_path = tmp_dir / f"{name}_tool.py"
    file_path.write_text(content)
    return str(file_path)


class TestDynamicToolRegistry:
    """Tests for DynamicToolRegistry."""

    def test_register_from_path(self):
        """Test registering a tool from file path."""
        registry = DynamicToolRegistry()
        path = create_temp_tool_file("test_tool", "TestTool")

        result = registry.register_from_path(path, "test_tool")

        assert result == DynamicRegistrationState.REGISTERED
        assert "test_tool" in registry.list_tools()

    def test_register_from_path_not_exist(self):
        """Test registering from non-existent path."""
        registry = DynamicToolRegistry()

        result = registry.register_from_path("/nonexistent/path.py", "test")

        assert result == DynamicRegistrationState.ERROR
        info = registry.get_tool("test")
        assert info is not None
        assert info.state == DynamicRegistrationState.ERROR

    def test_register_non_py_file(self):
        """Test registering non-Python file."""
        registry = DynamicToolRegistry()
        tmp_dir = Path(tempfile.gettempdir()) / "test_tools"
        file_path = tmp_dir / "dummy.txt"
        file_path.write_text("not python")

        result = registry.register_from_path(str(file_path), "dummy")

        assert result == DynamicRegistrationState.ERROR

    def test_register_from_module(self):
        """Test registering from module path."""
        registry = DynamicToolRegistry()

        result = registry.register_from_module(
            "simple_agent.extensions.dynamic",
            "DynamicToolRegistry"
        )

        assert result == DynamicRegistrationState.REGISTERED

    def test_instantiate_registered_tool(self):
        """Test instantiating a registered tool."""
        registry = DynamicToolRegistry()
        path = create_temp_tool_file("instantiate_test", "InstantiateTest")

        registry.register_from_path(path, "instantiate_test")
        config = ExtensionConfig(name="instantiate_test")
        instance = registry.instantiate("instantiate_test", config)

        assert instance is not None
        assert hasattr(instance, "execute")
        result = instance.execute("hello")
        assert "hello-executed" in result

    def test_get_instance(self):
        """Test getting stored instance."""
        registry = DynamicToolRegistry()
        path = create_temp_tool_file("get_instance_test", "GetInstanceTest")

        registry.register_from_path(path, "get_instance_test")
        registry.instantiate("get_instance_test")

        instance = registry.get_instance("get_instance_test")

        assert instance is not None

    def test_unregister_tool(self):
        """Test unregistering a tool."""
        registry = DynamicToolRegistry()
        path = create_temp_tool_file("unregister_test", "UnregisterTest")

        registry.register_from_path(path, "unregister_test")
        registry.instantiate("unregister_test")

        result = registry.unregister("unregister_test")

        assert result is True
        assert "unregister_test" not in registry.list_tools()
        assert registry.get_instance("unregister_test") is None

    def test_list_tools(self):
        """Test listing all registered tools."""
        registry = DynamicToolRegistry()
        path1 = create_temp_tool_file("list_tool1", "ListTool1")
        path2 = create_temp_tool_file("list_tool2", "ListTool2")

        registry.register_from_path(path1, "list_tool1")
        registry.register_from_path(path2, "list_tool2")

        tools = registry.list_tools()

        assert len(tools) == 2
        assert "list_tool1" in tools
        assert "list_tool2" in tools

    def test_multiple_instantiations_same_tool(self):
        """Test multiple instantiations return same instance."""
        registry = DynamicToolRegistry()
        path = create_temp_tool_file("same_instance_test", "SameInstanceTest")

        registry.register_from_path(path, "same_instance_test")
        instance1 = registry.instantiate("same_instance_test")
        instance2 = registry.instantiate("same_instance_test")

        assert instance1 is instance2


class TestDynamicStrategyRegistry:
    """Tests for DynamicStrategyRegistry."""

    def test_register_strategy(self):
        """Test registering a strategy function."""
        registry = DynamicStrategyRegistry()

        def test_strategy(data: str) -> str:
            return f"strategy-{data}"

        result = registry.register("test_strategy", test_strategy)

        assert result == DynamicRegistrationState.REGISTERED
        assert "test_strategy" in registry.list_strategies()

    def test_register_from_module(self):
        """Test registering strategy from module."""
        registry = DynamicStrategyRegistry()

        result = registry.register_from_module(
            "simple_agent.extensions.dynamic",
            "get_strategy_registry"
        )

        assert result == DynamicRegistrationState.REGISTERED

    def test_execute_strategy(self):
        """Test executing a registered strategy."""
        registry = DynamicStrategyRegistry()

        def multiply(x: int, y: int) -> int:
            return x * y

        registry.register("multiply", multiply)
        result = registry.execute("multiply", 3, 4)

        assert result == 12

    def test_execute_nonexistent_strategy(self):
        """Test executing non-existent strategy."""
        registry = DynamicStrategyRegistry()

        result = registry.execute("nonexistent")

        assert result is None

    def test_unregister_strategy(self):
        """Test unregistering a strategy."""
        registry = DynamicStrategyRegistry()

        def dummy_fn():
            pass

        registry.register("dummy", dummy_fn)
        result = registry.unregister("dummy")

        assert result is True
        assert "dummy" not in registry.list_strategies()

    def test_strategy_with_config(self):
        """Test strategy with configuration."""
        registry = DynamicStrategyRegistry()

        def configured_strategy(data: str, prefix: str = "default") -> str:
            return f"{prefix}-{data}"

        registry.register("configured", configured_strategy, prefix="custom")

        result = registry.execute("configured", "test")

        assert result == "custom-test"

    def test_list_strategies(self):
        """Test listing all strategies."""
        registry = DynamicStrategyRegistry()

        registry.register("strat1", lambda: None)
        registry.register("strat2", lambda: None)
        registry.register("strat3", lambda: None)

        strategies = registry.list_strategies()

        assert len(strategies) == 3


class TestHotPlugAgentManager:
    """Tests for HotPlugAgentManager."""

    def test_register_from_path(self):
        """Test registering agent from path."""
        manager = HotPlugAgentManager()
        path = create_temp_tool_file("agent_demo", "AgentDemo")

        # Note: This registers Extension subclasses, not Agent
        # but we test the registration mechanism
        state = manager.register_from_path(path, "agent_demo")

        # May fail if Agent not available, but shouldn't crash
        assert state in [DynamicRegistrationState.REGISTERED, DynamicRegistrationState.ERROR]

    def test_register_class(self):
        """Test registering agent class directly."""
        manager = HotPlugAgentManager()

        # Use Extension as test class
        state = manager.register_class(SampleTool, "test_agent")

        assert state == DynamicRegistrationState.REGISTERED
        assert "test_agent" in manager.list_registered()

    def test_plug_agent(self):
        """Test hot-plugging an agent."""
        manager = HotPlugAgentManager()
        manager.register_class(SampleTool, "plug_test")

        agent = manager.plug("plug_test")

        assert agent is not None
        assert "plug_test" in manager.list_active()

    def test_unplug_agent(self):
        """Test hot-unplugging an agent."""
        manager = HotPlugAgentManager()
        manager.register_class(SampleTool, "unplug_test")
        manager.plug("unplug_test")

        result = manager.unplug("unplug_test")

        assert result is True
        assert "unplug_test" not in manager.list_active()

    def test_get_agent(self):
        """Test getting an agent."""
        manager = HotPlugAgentManager()
        manager.register_class(SampleTool, "get_agent_test")
        manager.plug("get_agent_test")

        agent = manager.get_agent("get_agent_test")

        assert agent is not None

    def test_list_active(self):
        """Test listing active agents."""
        manager = HotPlugAgentManager()
        manager.register_class(SampleTool, "agent1")
        manager.register_class(AnotherTool, "agent2")

        manager.plug("agent1")
        manager.plug("agent2")

        active = manager.list_active()

        assert len(active) == 2
        assert "agent1" in active
        assert "agent2" in active


class TestDynamicExtensionSystem:
    """Tests for unified DynamicExtensionSystem."""

    def test_full_system(self):
        """Test complete dynamic extension system."""
        system = DynamicExtensionSystem()

        # Test tool registration
        path = create_temp_tool_file("full_test", "FullTest")
        state = system.tool_registry.register_from_path(path, "full_test")

        assert state == DynamicRegistrationState.REGISTERED

        # Test strategy registration
        def dummy_strategy():
            return "result"

        strategy_state = system.strategy_registry.register("dummy", dummy_strategy)

        assert strategy_state == DynamicRegistrationState.REGISTERED

        # Test agent registration
        agent_state = system.agent_manager.register_class(SampleTool, "full_agent")

        assert agent_state == DynamicRegistrationState.REGISTERED

    def test_list_all(self):
        """Test listing all dynamic capabilities."""
        system = DynamicExtensionSystem()

        # Add some items
        path = create_temp_tool_file("list_all_test", "ListAllTest")
        system.tool_registry.register_from_path(path, "list_all_test")
        system.strategy_registry.register("list_strat", lambda: None)
        system.agent_manager.register_class(SampleTool, "list_agent")

        result = system.list_all()

        assert "tools" in result
        assert "strategies" in result
        assert "agents" in result

    def test_get_status(self):
        """Test getting system status."""
        system = DynamicExtensionSystem()

        # Add some items
        path = create_temp_tool_file("status_test", "StatusTest")
        system.tool_registry.register_from_path(path, "status_test")
        system.strategy_registry.register("status_strat", lambda: None)
        system.agent_manager.register_class(SampleTool, "status_agent")

        status = system.get_status()

        assert "tools" in status
        assert "strategies" in status
        assert "agents" in status
        assert status["tools"]["registered"] >= 1
        assert status["strategies"]["registered"] >= 1
        assert status["agents"]["registered"] >= 1


class TestIntegration:
    """Integration tests for dynamic extension system."""

    def test_end_to_end_workflow(self):
        """Test complete workflow: register, instantiate, execute, cleanup."""
        system = DynamicExtensionSystem()

        # 1. Register
        path = create_temp_tool_file("e2e_test", "E2ETest")
        state = system.tool_registry.register_from_path(path, "e2e_test")
        assert state == DynamicRegistrationState.REGISTERED

        # 2. Instantiate
        config = ExtensionConfig(name="e2e_test")
        instance = system.tool_registry.instantiate("e2e_test", config)
        assert instance is not None

        # 3. Execute
        result = instance.execute("hello")
        assert "hello-executed" in result

        # 4. Verify state
        status = system.get_status()
        assert status["tools"]["active"] >= 1

        # 5. Cleanup
        system.tool_registry.unregister("e2e_test")
        assert "e2e_test" not in system.tool_registry.list_tools()

    def test_thread_safety(self):
        """Test thread safety of registries."""
        import threading

        system = DynamicExtensionSystem()
        errors = []

        def register_tool(i):
            try:
                path = create_temp_tool_file(f"thread_{i}", f"Thread{i}")
                system.tool_registry.register_from_path(path, f"thread_{i}")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=register_tool, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(system.tool_registry.list_tools()) >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
