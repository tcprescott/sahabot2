"""
Plugin loader utilities.

This module provides utilities for discovering, loading, and validating plugins.
"""

import importlib
import logging
from pathlib import Path
from typing import List, Type

import yaml

from application.plugins.base.plugin import BasePlugin
from application.plugins.manifest import PluginManifest, PluginType
from application.plugins.exceptions import (
    PluginLoadError,
    PluginValidationError,
)

logger = logging.getLogger(__name__)

# Base directory for plugins - resolved from the application root
# Path(__file__) is application/plugins/loader.py
# parents[0] = application/plugins, parents[1] = application, parents[2] = repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGINS_BASE_DIR = _REPO_ROOT / "plugins"
BUILTIN_PLUGINS_DIR = PLUGINS_BASE_DIR / "builtin"
EXTERNAL_PLUGINS_DIR = PLUGINS_BASE_DIR / "external"


class PluginLoader:
    """
    Utility class for discovering and loading plugins.

    This class handles:
    - Discovering plugins in the filesystem
    - Loading plugin manifests
    - Instantiating plugin classes
    """

    @classmethod
    def discover_plugins(
        cls,
        include_builtin: bool = True,
        include_external: bool = True,
    ) -> List[str]:
        """
        Discover available plugins in the filesystem.

        Args:
            include_builtin: Whether to include built-in plugins
            include_external: Whether to include external plugins

        Returns:
            List of plugin IDs found
        """
        plugins = []

        if include_builtin and BUILTIN_PLUGINS_DIR.exists():
            for item in BUILTIN_PLUGINS_DIR.iterdir():
                if item.is_dir() and not item.name.startswith("_"):
                    # Check for __init__.py or manifest.yaml
                    if (item / "__init__.py").exists() or (item / "manifest.yaml").exists():
                        plugins.append(item.name)
                        logger.debug("Discovered builtin plugin: %s", item.name)

        if include_external and EXTERNAL_PLUGINS_DIR.exists():
            for item in EXTERNAL_PLUGINS_DIR.iterdir():
                if item.is_dir() and not item.name.startswith("_"):
                    if (item / "__init__.py").exists() or (item / "manifest.yaml").exists():
                        plugins.append(item.name)
                        logger.debug("Discovered external plugin: %s", item.name)

        logger.info("Discovered %d plugin(s)", len(plugins))
        return plugins

    @classmethod
    def load_manifest(cls, plugin_id: str, plugin_type: PluginType = PluginType.BUILTIN) -> PluginManifest:
        """
        Load a plugin manifest from file.

        Args:
            plugin_id: Plugin identifier
            plugin_type: Whether plugin is builtin or external

        Returns:
            PluginManifest instance

        Raises:
            PluginLoadError: If manifest cannot be loaded
        """
        if plugin_type == PluginType.BUILTIN:
            plugin_dir = BUILTIN_PLUGINS_DIR / plugin_id
        else:
            plugin_dir = EXTERNAL_PLUGINS_DIR / plugin_id

        manifest_path = plugin_dir / "manifest.yaml"

        if not manifest_path.exists():
            raise PluginLoadError(f"Manifest not found for plugin '{plugin_id}': {manifest_path}")

        try:
            with open(manifest_path, "r") as f:
                manifest_data = yaml.safe_load(f)

            manifest = PluginManifest(**manifest_data)
            logger.debug("Loaded manifest for plugin: %s", plugin_id)
            return manifest

        except yaml.YAMLError as e:
            raise PluginLoadError(f"Invalid YAML in manifest for plugin '{plugin_id}': {e}") from e
        except Exception as e:
            raise PluginLoadError(f"Failed to load manifest for plugin '{plugin_id}': {e}") from e

    @classmethod
    def load_plugin_class(
        cls,
        plugin_id: str,
        plugin_type: PluginType = PluginType.BUILTIN,
    ) -> Type[BasePlugin]:
        """
        Load a plugin class from its module.

        Args:
            plugin_id: Plugin identifier
            plugin_type: Whether plugin is builtin or external

        Returns:
            Plugin class (not instance)

        Raises:
            PluginLoadError: If plugin class cannot be loaded
        """
        if plugin_type == PluginType.BUILTIN:
            module_path = f"plugins.builtin.{plugin_id}"
        else:
            module_path = f"plugins.external.{plugin_id}"

        try:
            module = importlib.import_module(module_path)

            # Look for a class that ends with "Plugin"
            plugin_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, BasePlugin)
                    and obj is not BasePlugin
                ):
                    plugin_class = obj
                    break

            if plugin_class is None:
                raise PluginLoadError(
                    f"No BasePlugin subclass found in module '{module_path}'"
                )

            logger.debug("Loaded plugin class: %s from %s", plugin_class.__name__, module_path)
            return plugin_class

        except ImportError as e:
            raise PluginLoadError(f"Failed to import plugin module '{module_path}': {e}") from e
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin class from '{module_path}': {e}") from e

    @classmethod
    def load_plugin(
        cls,
        plugin_id: str,
        plugin_type: PluginType = PluginType.BUILTIN,
    ) -> BasePlugin:
        """
        Load and instantiate a plugin.

        Args:
            plugin_id: Plugin identifier
            plugin_type: Whether plugin is builtin or external

        Returns:
            Plugin instance

        Raises:
            PluginLoadError: If plugin cannot be loaded
        """
        logger.info("Loading plugin: %s (%s)", plugin_id, plugin_type.value)

        try:
            # Load the plugin class
            plugin_class = cls.load_plugin_class(plugin_id, plugin_type)

            # Instantiate
            plugin = plugin_class()

            # Validate that plugin_id matches manifest
            if plugin.plugin_id != plugin.manifest.id:
                raise PluginValidationError(
                    f"Plugin ID mismatch: plugin_id property is '{plugin.plugin_id}' "
                    f"but manifest ID is '{plugin.manifest.id}'"
                )

            logger.info("Loaded plugin: %s (version %s)", plugin.plugin_id, plugin.manifest.version)
            return plugin

        except Exception as e:
            logger.error("Failed to load plugin %s: %s", plugin_id, e)
            raise PluginLoadError(f"Failed to load plugin '{plugin_id}': {e}") from e

    @classmethod
    def load_all_plugins(
        cls,
        include_builtin: bool = True,
        include_external: bool = True,
    ) -> List[BasePlugin]:
        """
        Discover and load all available plugins.

        Args:
            include_builtin: Whether to include built-in plugins
            include_external: Whether to include external plugins

        Returns:
            List of loaded plugin instances
        """
        plugins = []
        failed = []

        # Discover plugins
        plugin_ids = cls.discover_plugins(include_builtin, include_external)

        for plugin_id in plugin_ids:
            # Determine plugin type based on directory
            if include_builtin and (BUILTIN_PLUGINS_DIR / plugin_id).exists():
                plugin_type = PluginType.BUILTIN
            else:
                plugin_type = PluginType.EXTERNAL

            try:
                plugin = cls.load_plugin(plugin_id, plugin_type)
                plugins.append(plugin)
            except Exception as e:
                logger.error("Failed to load plugin %s: %s", plugin_id, e)
                failed.append(plugin_id)

        if failed:
            logger.warning("Failed to load %d plugin(s): %s", len(failed), failed)

        logger.info("Loaded %d plugin(s) successfully", len(plugins))
        return plugins


def get_plugin_dir(plugin_id: str, plugin_type: PluginType = PluginType.BUILTIN) -> Path:
    """
    Get the directory path for a plugin.

    Args:
        plugin_id: Plugin identifier
        plugin_type: Whether plugin is builtin or external

    Returns:
        Path to plugin directory
    """
    if plugin_type == PluginType.BUILTIN:
        return BUILTIN_PLUGINS_DIR / plugin_id
    else:
        return EXTERNAL_PLUGINS_DIR / plugin_id
