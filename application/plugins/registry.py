"""
Plugin registry singleton.

This module provides the central registry for all plugins in the application.
The PluginRegistry is responsible for plugin discovery, registration,
enablement tracking, and configuration management.
"""

import logging
from typing import Dict, List, Optional, Type

from application.plugins.base.plugin import BasePlugin
from application.plugins.manifest import PluginConfig, PluginManifest
from application.plugins.exceptions import (
    PluginNotFoundError,
    PluginAlreadyEnabledError,
    PluginDependencyError,
)

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry for all plugins.

    This is a singleton class that manages all registered plugins,
    tracks their enablement status per organization, and provides
    access to plugin instances and configuration.
    """

    # Class-level storage (singleton pattern)
    _plugins: Dict[str, BasePlugin] = {}
    _enabled: Dict[str, Dict[int, bool]] = {}  # plugin_id -> {org_id -> enabled}
    _configs: Dict[str, Dict[int, PluginConfig]] = {}  # plugin_id -> {org_id -> config}
    _initialized: bool = False

    @classmethod
    def register(cls, plugin: BasePlugin) -> None:
        """
        Register a plugin with the registry.

        Args:
            plugin: Plugin instance to register

        Raises:
            ValueError: If plugin with same ID is already registered
        """
        plugin_id = plugin.plugin_id
        if plugin_id in cls._plugins:
            raise ValueError(f"Plugin '{plugin_id}' is already registered")

        cls._plugins[plugin_id] = plugin
        cls._enabled[plugin_id] = {}
        cls._configs[plugin_id] = {}
        logger.info("Registered plugin: %s (version %s)", plugin_id, plugin.manifest.version)

    @classmethod
    def unregister(cls, plugin_id: str) -> None:
        """
        Unregister a plugin from the registry.

        Args:
            plugin_id: ID of plugin to unregister

        Raises:
            PluginNotFoundError: If plugin is not registered
        """
        if plugin_id not in cls._plugins:
            raise PluginNotFoundError(f"Plugin '{plugin_id}' is not registered")

        del cls._plugins[plugin_id]
        if plugin_id in cls._enabled:
            del cls._enabled[plugin_id]
        if plugin_id in cls._configs:
            del cls._configs[plugin_id]
        logger.info("Unregistered plugin: %s", plugin_id)

    @classmethod
    def get(cls, plugin_id: str) -> BasePlugin:
        """
        Get a plugin by ID.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Plugin instance

        Raises:
            PluginNotFoundError: If plugin is not registered
        """
        if plugin_id not in cls._plugins:
            raise PluginNotFoundError(f"Plugin '{plugin_id}' is not registered")
        return cls._plugins[plugin_id]

    @classmethod
    def get_all(cls) -> List[BasePlugin]:
        """
        Get all registered plugins.

        Returns:
            List of all registered plugin instances
        """
        return list(cls._plugins.values())

    @classmethod
    def get_all_ids(cls) -> List[str]:
        """
        Get all registered plugin IDs.

        Returns:
            List of all registered plugin IDs
        """
        return list(cls._plugins.keys())

    @classmethod
    def has(cls, plugin_id: str) -> bool:
        """
        Check if a plugin is registered.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if plugin is registered, False otherwise
        """
        return plugin_id in cls._plugins

    @classmethod
    def get_plugin_count(cls) -> int:
        """
        Get the number of registered plugins.

        Returns:
            Number of registered plugins
        """
        return len(cls._plugins)

    # ─────────────────────────────────────────────────────────────
    # Enablement Management
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def is_enabled(cls, plugin_id: str, organization_id: int) -> bool:
        """
        Check if a plugin is enabled for an organization.

        Args:
            plugin_id: Plugin identifier
            organization_id: Organization ID

        Returns:
            True if enabled, False otherwise
        """
        if plugin_id not in cls._plugins:
            return False

        # Global plugins are always enabled
        plugin = cls._plugins[plugin_id]
        if plugin.manifest.global_plugin:
            return True

        # Check organization-specific enablement
        if plugin_id in cls._enabled:
            org_enabled = cls._enabled[plugin_id].get(organization_id)
            if org_enabled is not None:
                return org_enabled

        # Default to enabled_by_default from manifest
        return plugin.manifest.enabled_by_default

    @classmethod
    def set_enabled(
        cls,
        plugin_id: str,
        organization_id: int,
        enabled: bool,
    ) -> None:
        """
        Set plugin enablement for an organization.

        Args:
            plugin_id: Plugin identifier
            organization_id: Organization ID
            enabled: Whether to enable or disable

        Raises:
            PluginNotFoundError: If plugin is not registered
        """
        if plugin_id not in cls._plugins:
            raise PluginNotFoundError(f"Plugin '{plugin_id}' is not registered")

        if plugin_id not in cls._enabled:
            cls._enabled[plugin_id] = {}

        cls._enabled[plugin_id][organization_id] = enabled
        logger.info(
            "Plugin %s %s for organization %s",
            plugin_id,
            "enabled" if enabled else "disabled",
            organization_id,
        )

    @classmethod
    def get_enabled_plugins(cls, organization_id: int) -> List[BasePlugin]:
        """
        Get all plugins enabled for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            List of enabled plugin instances
        """
        return [
            plugin
            for plugin in cls._plugins.values()
            if cls.is_enabled(plugin.plugin_id, organization_id)
        ]

    # ─────────────────────────────────────────────────────────────
    # Configuration Management
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def get_config(cls, plugin_id: str, organization_id: int) -> PluginConfig:
        """
        Get configuration for a plugin and organization.

        Args:
            plugin_id: Plugin identifier
            organization_id: Organization ID

        Returns:
            PluginConfig with merged settings
        """
        if plugin_id not in cls._configs:
            return PluginConfig()

        org_config = cls._configs[plugin_id].get(organization_id)
        if org_config:
            return org_config

        return PluginConfig()

    @classmethod
    def set_config(
        cls,
        plugin_id: str,
        organization_id: int,
        config: PluginConfig,
    ) -> None:
        """
        Set configuration for a plugin and organization.

        Args:
            plugin_id: Plugin identifier
            organization_id: Organization ID
            config: Configuration to set

        Raises:
            PluginNotFoundError: If plugin is not registered
        """
        if plugin_id not in cls._plugins:
            raise PluginNotFoundError(f"Plugin '{plugin_id}' is not registered")

        if plugin_id not in cls._configs:
            cls._configs[plugin_id] = {}

        cls._configs[plugin_id][organization_id] = config
        logger.info(
            "Updated config for plugin %s in organization %s",
            plugin_id,
            organization_id,
        )

    # ─────────────────────────────────────────────────────────────
    # Dependency Management
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def check_dependencies(cls, plugin_id: str) -> List[str]:
        """
        Check if all dependencies for a plugin are satisfied.

        Args:
            plugin_id: Plugin identifier

        Returns:
            List of missing dependency plugin IDs
        """
        if plugin_id not in cls._plugins:
            raise PluginNotFoundError(f"Plugin '{plugin_id}' is not registered")

        plugin = cls._plugins[plugin_id]
        missing = []

        for dep in plugin.manifest.requires.plugins:
            if dep.plugin_id not in cls._plugins:
                missing.append(dep.plugin_id)

        return missing

    @classmethod
    def get_dependents(cls, plugin_id: str) -> List[str]:
        """
        Get plugins that depend on the given plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            List of dependent plugin IDs
        """
        dependents = []
        for pid, plugin in cls._plugins.items():
            for dep in plugin.manifest.requires.plugins:
                if dep.plugin_id == plugin_id:
                    dependents.append(pid)
                    break
        return dependents

    # ─────────────────────────────────────────────────────────────
    # Utility Methods
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def get_by_category(cls, category: str) -> List[BasePlugin]:
        """
        Get all plugins in a category.

        Args:
            category: Category name

        Returns:
            List of plugins in the category
        """
        return [
            plugin
            for plugin in cls._plugins.values()
            if plugin.manifest.category.value == category
        ]

    @classmethod
    def get_builtin_plugins(cls) -> List[BasePlugin]:
        """
        Get all built-in plugins.

        Returns:
            List of built-in plugin instances
        """
        return [
            plugin
            for plugin in cls._plugins.values()
            if plugin.manifest.type.value == "builtin"
        ]

    @classmethod
    def get_external_plugins(cls) -> List[BasePlugin]:
        """
        Get all external plugins.

        Returns:
            List of external plugin instances
        """
        return [
            plugin
            for plugin in cls._plugins.values()
            if plugin.manifest.type.value == "external"
        ]

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered plugins.

        Warning: This should only be used for testing purposes.
        """
        cls._plugins.clear()
        cls._enabled.clear()
        cls._configs.clear()
        cls._initialized = False
        logger.warning("Plugin registry cleared")

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Check if the registry has been initialized.

        Returns:
            True if initialized, False otherwise
        """
        return cls._initialized

    @classmethod
    def set_initialized(cls, value: bool = True) -> None:
        """
        Set the initialization status.

        Args:
            value: Initialization status
        """
        cls._initialized = value
