"""
Tests for the PluginLifecycleManager.
"""

import pytest

from application.plugins.lifecycle import PluginLifecycleManager
from application.plugins.registry import PluginRegistry
from application.plugins.manifest import PluginManifest, PluginConfig, PluginType, PluginCategory
from application.plugins.base.plugin import BasePlugin
from application.plugins.exceptions import (
    PluginLifecycleError,
    PluginNotFoundError,
)


class MockPlugin(BasePlugin):
    """Mock plugin for testing."""

    def __init__(self, plugin_id: str = "mock_plugin", **manifest_overrides):
        self._plugin_id = plugin_id
        self._manifest_overrides = manifest_overrides
        self.on_load_called = False
        self.on_unload_called = False
        self.on_enable_called = False
        self.on_disable_called = False
        self.enabled_org_ids = []
        self.disabled_org_ids = []

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

    async def on_load(self) -> None:
        self.on_load_called = True

    async def on_unload(self) -> None:
        self.on_unload_called = True

    async def on_enable(self, organization_id: int, config: PluginConfig) -> None:
        self.on_enable_called = True
        self.enabled_org_ids.append(organization_id)

    async def on_disable(self, organization_id: int) -> None:
        self.on_disable_called = True
        self.disabled_org_ids.append(organization_id)


class TestPluginLifecycleManager:
    """Tests for PluginLifecycleManager class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Clear the registry before each test."""
        PluginRegistry.clear()
        yield
        PluginRegistry.clear()

    @pytest.mark.asyncio
    async def test_load_plugin(self):
        """Test loading a plugin."""
        plugin = MockPlugin()

        await PluginLifecycleManager.load_plugin(plugin)

        assert plugin.on_load_called
        assert PluginRegistry.has("mock_plugin")

    @pytest.mark.asyncio
    async def test_load_plugin_already_registered(self):
        """Test that loading an already registered plugin fails."""
        plugin1 = MockPlugin()
        plugin2 = MockPlugin()

        await PluginLifecycleManager.load_plugin(plugin1)

        with pytest.raises(PluginLifecycleError):
            await PluginLifecycleManager.load_plugin(plugin2)

    @pytest.mark.asyncio
    async def test_unload_plugin(self):
        """Test unloading a plugin."""
        plugin = MockPlugin()
        await PluginLifecycleManager.load_plugin(plugin)

        await PluginLifecycleManager.unload_plugin("mock_plugin")

        assert plugin.on_unload_called
        assert not PluginRegistry.has("mock_plugin")

    @pytest.mark.asyncio
    async def test_unload_plugin_not_found(self):
        """Test that unloading a non-existent plugin fails."""
        with pytest.raises(PluginNotFoundError):
            await PluginLifecycleManager.unload_plugin("nonexistent")

    @pytest.mark.asyncio
    async def test_enable_plugin(self):
        """Test enabling a plugin for an organization."""
        plugin = MockPlugin(enabled_by_default=False)
        await PluginLifecycleManager.load_plugin(plugin)

        await PluginLifecycleManager.enable_plugin("mock_plugin", 1)

        assert plugin.on_enable_called
        assert 1 in plugin.enabled_org_ids
        assert PluginRegistry.is_enabled("mock_plugin", 1)

    @pytest.mark.asyncio
    async def test_enable_plugin_already_enabled(self):
        """Test enabling an already enabled plugin is a no-op."""
        plugin = MockPlugin(enabled_by_default=True)
        await PluginLifecycleManager.load_plugin(plugin)

        # First enable should work
        await PluginLifecycleManager.enable_plugin("mock_plugin", 1)

        # Second enable should be a no-op
        plugin.on_enable_called = False
        await PluginLifecycleManager.enable_plugin("mock_plugin", 1)

        # on_enable should not be called again
        assert not plugin.on_enable_called

    @pytest.mark.asyncio
    async def test_enable_plugin_with_config(self):
        """Test enabling a plugin with configuration."""
        plugin = MockPlugin(enabled_by_default=False)
        await PluginLifecycleManager.load_plugin(plugin)

        config = PluginConfig(enabled=True, settings={"key": "value"})
        await PluginLifecycleManager.enable_plugin("mock_plugin", 1, config)

        result_config = PluginRegistry.get_config("mock_plugin", 1)
        assert result_config.settings == {"key": "value"}

    @pytest.mark.asyncio
    async def test_enable_plugin_not_found(self):
        """Test that enabling a non-existent plugin fails."""
        with pytest.raises(PluginNotFoundError):
            await PluginLifecycleManager.enable_plugin("nonexistent", 1)

    @pytest.mark.asyncio
    async def test_disable_plugin(self):
        """Test disabling a plugin for an organization."""
        plugin = MockPlugin(enabled_by_default=True)
        await PluginLifecycleManager.load_plugin(plugin)
        PluginRegistry.set_enabled("mock_plugin", 1, True)

        await PluginLifecycleManager.disable_plugin("mock_plugin", 1)

        assert plugin.on_disable_called
        assert 1 in plugin.disabled_org_ids
        assert not PluginRegistry.is_enabled("mock_plugin", 1)

    @pytest.mark.asyncio
    async def test_disable_plugin_already_disabled(self):
        """Test disabling an already disabled plugin is a no-op."""
        plugin = MockPlugin(enabled_by_default=False)
        await PluginLifecycleManager.load_plugin(plugin)
        PluginRegistry.set_enabled("mock_plugin", 1, False)

        await PluginLifecycleManager.disable_plugin("mock_plugin", 1)

        # on_disable should not be called
        assert not plugin.on_disable_called

    @pytest.mark.asyncio
    async def test_disable_plugin_not_found(self):
        """Test that disabling a non-existent plugin fails."""
        with pytest.raises(PluginNotFoundError):
            await PluginLifecycleManager.disable_plugin("nonexistent", 1)

    @pytest.mark.asyncio
    async def test_load_all_plugins(self):
        """Test loading multiple plugins."""
        plugins = [
            MockPlugin("plugin1"),
            MockPlugin("plugin2"),
            MockPlugin("plugin3"),
        ]

        loaded = await PluginLifecycleManager.load_all_plugins(plugins)

        assert loaded == 3
        for plugin in plugins:
            assert plugin.on_load_called
            assert PluginRegistry.has(plugin.plugin_id)

    @pytest.mark.asyncio
    async def test_unload_all_plugins(self):
        """Test unloading all plugins."""
        plugins = [
            MockPlugin("plugin1"),
            MockPlugin("plugin2"),
        ]
        for plugin in plugins:
            await PluginLifecycleManager.load_plugin(plugin)

        unloaded = await PluginLifecycleManager.unload_all_plugins()

        assert unloaded == 2
        for plugin in plugins:
            assert plugin.on_unload_called
        assert PluginRegistry.get_plugin_count() == 0
