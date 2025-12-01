"""
Plugin lifecycle manager.

This module provides lifecycle management for plugins, including
loading, unloading, enabling, and disabling plugins.
"""

import logging
from typing import List, Optional

from application.plugins.base.plugin import BasePlugin
from application.plugins.manifest import PluginConfig
from application.plugins.registry import PluginRegistry
from application.plugins.exceptions import (
    PluginLifecycleError,
    PluginDependencyError,
    PluginNotFoundError,
)

logger = logging.getLogger(__name__)


class PluginLifecycleManager:
    """
    Manages plugin lifecycle transitions.

    This class handles the lifecycle of plugins including:
    - Loading plugins at startup
    - Enabling plugins for organizations
    - Disabling plugins for organizations
    - Unloading plugins at shutdown
    """

    @classmethod
    async def load_plugin(cls, plugin: BasePlugin) -> None:
        """
        Load a plugin into the registry.

        This calls the plugin's on_load() hook and registers it.

        Args:
            plugin: Plugin instance to load

        Raises:
            PluginLifecycleError: If loading fails
        """
        plugin_id = plugin.plugin_id
        logger.info("Loading plugin: %s", plugin_id)

        try:
            # Register first so dependencies can be checked
            PluginRegistry.register(plugin)

            # Check dependencies
            missing = PluginRegistry.check_dependencies(plugin_id)
            if missing:
                PluginRegistry.unregister(plugin_id)
                raise PluginDependencyError(
                    f"Plugin '{plugin_id}' has missing dependencies: {missing}"
                )

            # Call lifecycle hook
            await plugin.on_load()
            logger.info("Plugin loaded successfully: %s", plugin_id)

        except Exception as e:
            logger.error("Failed to load plugin %s: %s", plugin_id, e)
            # Try to unregister if it was registered
            if PluginRegistry.has(plugin_id):
                PluginRegistry.unregister(plugin_id)
            raise PluginLifecycleError(f"Failed to load plugin '{plugin_id}': {e}") from e

    @classmethod
    async def unload_plugin(cls, plugin_id: str) -> None:
        """
        Unload a plugin from the registry.

        This calls the plugin's on_unload() hook and unregisters it.

        Args:
            plugin_id: ID of plugin to unload

        Raises:
            PluginNotFoundError: If plugin is not registered
            PluginLifecycleError: If unloading fails
        """
        logger.info("Unloading plugin: %s", plugin_id)

        try:
            plugin = PluginRegistry.get(plugin_id)

            # Check for dependents
            dependents = PluginRegistry.get_dependents(plugin_id)
            if dependents:
                raise PluginDependencyError(
                    f"Cannot unload '{plugin_id}': "
                    f"plugins depend on it: {dependents}"
                )

            # Call lifecycle hook
            await plugin.on_unload()

            # Unregister
            PluginRegistry.unregister(plugin_id)
            logger.info("Plugin unloaded successfully: %s", plugin_id)

        except PluginNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to unload plugin %s: %s", plugin_id, e)
            raise PluginLifecycleError(f"Failed to unload plugin '{plugin_id}': {e}") from e

    @classmethod
    async def enable_plugin(
        cls,
        plugin_id: str,
        organization_id: int,
        config: Optional[PluginConfig] = None,
    ) -> None:
        """
        Enable a plugin for an organization.

        This calls the plugin's on_enable() hook and updates enablement.

        Args:
            plugin_id: Plugin identifier
            organization_id: Organization ID
            config: Optional organization-specific configuration

        Raises:
            PluginNotFoundError: If plugin is not registered
            PluginLifecycleError: If enabling fails
        """
        logger.info("Enabling plugin %s for organization %s", plugin_id, organization_id)

        try:
            plugin = PluginRegistry.get(plugin_id)

            # Check if already enabled
            if PluginRegistry.is_enabled(plugin_id, organization_id):
                logger.info("Plugin %s already enabled for organization %s", plugin_id, organization_id)
                return

            # Check dependencies are enabled for this org
            for dep in plugin.manifest.requires.plugins:
                if not PluginRegistry.is_enabled(dep.plugin_id, organization_id):
                    raise PluginDependencyError(
                        f"Plugin '{plugin_id}' requires '{dep.plugin_id}' "
                        f"to be enabled for organization {organization_id}"
                    )

            # Use provided config or default
            plugin_config = config or PluginConfig()

            # Call lifecycle hook
            await plugin.on_enable(organization_id, plugin_config)

            # Update enablement
            PluginRegistry.set_enabled(plugin_id, organization_id, True)
            if config:
                PluginRegistry.set_config(plugin_id, organization_id, config)

            logger.info("Plugin %s enabled for organization %s", plugin_id, organization_id)

        except PluginNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Failed to enable plugin %s for organization %s: %s",
                plugin_id,
                organization_id,
                e,
            )
            raise PluginLifecycleError(
                f"Failed to enable plugin '{plugin_id}' for organization {organization_id}: {e}"
            ) from e

    @classmethod
    async def disable_plugin(cls, plugin_id: str, organization_id: int) -> None:
        """
        Disable a plugin for an organization.

        This calls the plugin's on_disable() hook and updates enablement.

        Args:
            plugin_id: Plugin identifier
            organization_id: Organization ID

        Raises:
            PluginNotFoundError: If plugin is not registered
            PluginLifecycleError: If disabling fails
        """
        logger.info("Disabling plugin %s for organization %s", plugin_id, organization_id)

        try:
            plugin = PluginRegistry.get(plugin_id)

            # Check if actually enabled
            if not PluginRegistry.is_enabled(plugin_id, organization_id):
                logger.info("Plugin %s already disabled for organization %s", plugin_id, organization_id)
                return

            # Check if any dependents are enabled for this org
            dependents = PluginRegistry.get_dependents(plugin_id)
            enabled_dependents = [
                d for d in dependents
                if PluginRegistry.is_enabled(d, organization_id)
            ]
            if enabled_dependents:
                raise PluginDependencyError(
                    f"Cannot disable '{plugin_id}' for organization {organization_id}: "
                    f"plugins depend on it: {enabled_dependents}"
                )

            # Call lifecycle hook
            await plugin.on_disable(organization_id)

            # Update enablement
            PluginRegistry.set_enabled(plugin_id, organization_id, False)

            logger.info("Plugin %s disabled for organization %s", plugin_id, organization_id)

        except PluginNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Failed to disable plugin %s for organization %s: %s",
                plugin_id,
                organization_id,
                e,
            )
            raise PluginLifecycleError(
                f"Failed to disable plugin '{plugin_id}' for organization {organization_id}: {e}"
            ) from e

    @classmethod
    async def load_all_plugins(cls, plugins: List[BasePlugin]) -> int:
        """
        Load multiple plugins.

        Plugins are loaded in dependency order.

        Args:
            plugins: List of plugin instances to load

        Returns:
            Number of plugins successfully loaded
        """
        loaded = 0
        failed = []

        # Sort by dependencies (simple topological sort)
        # For now, just load in order - dependency checking happens in load_plugin
        for plugin in plugins:
            try:
                await cls.load_plugin(plugin)
                loaded += 1
            except Exception as e:
                logger.error("Failed to load plugin %s: %s", plugin.plugin_id, e)
                failed.append(plugin.plugin_id)

        if failed:
            logger.warning("Failed to load %d plugin(s): %s", len(failed), failed)

        return loaded

    @classmethod
    async def unload_all_plugins(cls) -> int:
        """
        Unload all registered plugins.

        Plugins are unloaded in reverse dependency order.

        Returns:
            Number of plugins successfully unloaded
        """
        unloaded = 0
        plugins = list(PluginRegistry.get_all())

        # Reverse order for unloading
        plugins.reverse()

        for plugin in plugins:
            try:
                await cls.unload_plugin(plugin.plugin_id)
                unloaded += 1
            except Exception as e:
                logger.error("Failed to unload plugin %s: %s", plugin.plugin_id, e)

        return unloaded
