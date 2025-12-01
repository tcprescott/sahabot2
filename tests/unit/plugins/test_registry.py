"""
Tests for the PluginRegistry singleton.
"""

import pytest
from application.plugins.registry import PluginRegistry
from application.plugins.manifest import PluginManifest, PluginConfig, PluginType, PluginCategory
from application.plugins.base.plugin import BasePlugin
from application.plugins.exceptions import PluginNotFoundError


class MockPlugin(BasePlugin):
    """Mock plugin for testing."""

    def __init__(self, plugin_id: str = "mock_plugin", **manifest_overrides):
        self._plugin_id = plugin_id
        self._manifest_overrides = manifest_overrides

    @property
    def plugin_id(self) -> str:
        return self._plugin_id

    @property
    def manifest(self) -> PluginManifest:
        defaults = {
            "id": self._plugin_id,
            "name": "Mock Plugin",
            "version": "1.0.0",
            "description": "A mock plugin for testing",
            "type": PluginType.BUILTIN,
            "category": PluginCategory.UTILITY,
        }
        defaults.update(self._manifest_overrides)
        return PluginManifest(**defaults)


class TestPluginRegistry:
    """Tests for PluginRegistry class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Clear the registry before each test."""
        PluginRegistry.clear()
        yield
        PluginRegistry.clear()

    def test_register_plugin(self):
        """Test registering a plugin."""
        plugin = MockPlugin()
        PluginRegistry.register(plugin)

        assert PluginRegistry.has("mock_plugin")
        assert PluginRegistry.get_plugin_count() == 1

    def test_register_duplicate_raises(self):
        """Test that registering a duplicate plugin raises an error."""
        plugin1 = MockPlugin()
        plugin2 = MockPlugin()

        PluginRegistry.register(plugin1)

        with pytest.raises(ValueError, match="already registered"):
            PluginRegistry.register(plugin2)

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        plugin = MockPlugin()
        PluginRegistry.register(plugin)

        PluginRegistry.unregister("mock_plugin")

        assert not PluginRegistry.has("mock_plugin")
        assert PluginRegistry.get_plugin_count() == 0

    def test_unregister_not_found_raises(self):
        """Test that unregistering a non-existent plugin raises an error."""
        with pytest.raises(PluginNotFoundError):
            PluginRegistry.unregister("nonexistent")

    def test_get_plugin(self):
        """Test getting a plugin by ID."""
        plugin = MockPlugin()
        PluginRegistry.register(plugin)

        result = PluginRegistry.get("mock_plugin")

        assert result is plugin

    def test_get_not_found_raises(self):
        """Test that getting a non-existent plugin raises an error."""
        with pytest.raises(PluginNotFoundError):
            PluginRegistry.get("nonexistent")

    def test_get_all_plugins(self):
        """Test getting all registered plugins."""
        plugin1 = MockPlugin("plugin1")
        plugin2 = MockPlugin("plugin2")

        PluginRegistry.register(plugin1)
        PluginRegistry.register(plugin2)

        all_plugins = PluginRegistry.get_all()

        assert len(all_plugins) == 2
        assert plugin1 in all_plugins
        assert plugin2 in all_plugins

    def test_get_all_ids(self):
        """Test getting all plugin IDs."""
        PluginRegistry.register(MockPlugin("plugin1"))
        PluginRegistry.register(MockPlugin("plugin2"))

        ids = PluginRegistry.get_all_ids()

        assert set(ids) == {"plugin1", "plugin2"}

    def test_is_enabled_default(self):
        """Test that is_enabled returns enabled_by_default value."""
        plugin = MockPlugin(enabled_by_default=True)
        PluginRegistry.register(plugin)

        assert PluginRegistry.is_enabled("mock_plugin", 1) is True

    def test_is_enabled_disabled_by_default(self):
        """Test plugin disabled by default."""
        plugin = MockPlugin(enabled_by_default=False)
        PluginRegistry.register(plugin)

        assert PluginRegistry.is_enabled("mock_plugin", 1) is False

    def test_is_enabled_global_plugin(self):
        """Test that global plugins are always enabled."""
        plugin = MockPlugin(global_plugin=True, enabled_by_default=False)
        PluginRegistry.register(plugin)

        assert PluginRegistry.is_enabled("mock_plugin", 1) is True

    def test_set_enabled(self):
        """Test setting plugin enablement for an organization."""
        plugin = MockPlugin(enabled_by_default=False)
        PluginRegistry.register(plugin)

        PluginRegistry.set_enabled("mock_plugin", 1, True)

        assert PluginRegistry.is_enabled("mock_plugin", 1) is True

    def test_set_enabled_not_found_raises(self):
        """Test that set_enabled raises for non-existent plugin."""
        with pytest.raises(PluginNotFoundError):
            PluginRegistry.set_enabled("nonexistent", 1, True)

    def test_get_enabled_plugins(self):
        """Test getting all enabled plugins for an organization."""
        plugin1 = MockPlugin("plugin1", enabled_by_default=True)
        plugin2 = MockPlugin("plugin2", enabled_by_default=False)
        plugin3 = MockPlugin("plugin3", enabled_by_default=True)

        PluginRegistry.register(plugin1)
        PluginRegistry.register(plugin2)
        PluginRegistry.register(plugin3)

        enabled = PluginRegistry.get_enabled_plugins(1)

        assert len(enabled) == 2
        assert plugin1 in enabled
        assert plugin3 in enabled
        assert plugin2 not in enabled

    def test_get_config_default(self):
        """Test getting default config."""
        plugin = MockPlugin()
        PluginRegistry.register(plugin)

        config = PluginRegistry.get_config("mock_plugin", 1)

        assert config.enabled is True
        assert config.settings == {}

    def test_set_config(self):
        """Test setting plugin config."""
        plugin = MockPlugin()
        PluginRegistry.register(plugin)

        config = PluginConfig(enabled=True, settings={"key": "value"})
        PluginRegistry.set_config("mock_plugin", 1, config)

        result = PluginRegistry.get_config("mock_plugin", 1)

        assert result.settings == {"key": "value"}

    def test_set_config_not_found_raises(self):
        """Test that set_config raises for non-existent plugin."""
        config = PluginConfig()
        with pytest.raises(PluginNotFoundError):
            PluginRegistry.set_config("nonexistent", 1, config)

    def test_check_dependencies_no_deps(self):
        """Test checking dependencies for plugin with no deps."""
        plugin = MockPlugin()
        PluginRegistry.register(plugin)

        missing = PluginRegistry.check_dependencies("mock_plugin")

        assert missing == []

    def test_get_dependents_none(self):
        """Test getting dependents when none exist."""
        plugin = MockPlugin()
        PluginRegistry.register(plugin)

        dependents = PluginRegistry.get_dependents("mock_plugin")

        assert dependents == []

    def test_get_by_category(self):
        """Test getting plugins by category."""
        plugin1 = MockPlugin("plugin1", category=PluginCategory.UTILITY)
        plugin2 = MockPlugin("plugin2", category=PluginCategory.COMPETITION)

        PluginRegistry.register(plugin1)
        PluginRegistry.register(plugin2)

        utility_plugins = PluginRegistry.get_by_category("utility")

        assert len(utility_plugins) == 1
        assert plugin1 in utility_plugins

    def test_get_builtin_plugins(self):
        """Test getting built-in plugins."""
        plugin1 = MockPlugin("plugin1", type=PluginType.BUILTIN)
        plugin2 = MockPlugin("plugin2", type=PluginType.EXTERNAL)

        PluginRegistry.register(plugin1)
        PluginRegistry.register(plugin2)

        builtin = PluginRegistry.get_builtin_plugins()

        assert len(builtin) == 1
        assert plugin1 in builtin

    def test_get_external_plugins(self):
        """Test getting external plugins."""
        plugin1 = MockPlugin("plugin1", type=PluginType.BUILTIN)
        plugin2 = MockPlugin("plugin2", type=PluginType.EXTERNAL)

        PluginRegistry.register(plugin1)
        PluginRegistry.register(plugin2)

        external = PluginRegistry.get_external_plugins()

        assert len(external) == 1
        assert plugin2 in external

    def test_clear(self):
        """Test clearing the registry."""
        PluginRegistry.register(MockPlugin())
        PluginRegistry.set_initialized(True)

        PluginRegistry.clear()

        assert PluginRegistry.get_plugin_count() == 0
        assert not PluginRegistry.is_initialized()
