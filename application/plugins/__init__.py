"""
Plugin system for SahaBot2.

This package provides the plugin architecture that allows features to be
developed as modular, isolated plugins. Plugins can contribute:

- Database models
- API routes
- UI pages
- Discord commands
- Events and listeners
- Scheduled tasks

Usage:
    from application.plugins import PluginRegistry, BasePlugin

    # Get a plugin
    plugin = PluginRegistry.get('tournament')

    # Check if enabled for an organization
    if PluginRegistry.is_enabled('tournament', org_id):
        # Use plugin functionality
        pass

For plugin development, see docs/plugins/PLUGIN_DEVELOPMENT.md
"""

from application.plugins.manifest import (
    PluginManifest,
    PluginConfig,
    PluginType,
    PluginCategory,
    RouteScope,
)
from application.plugins.registry import PluginRegistry
from application.plugins.lifecycle import PluginLifecycleManager
from application.plugins.loader import PluginLoader
from application.plugins.config_service import PluginConfigService
from application.plugins.base import (
    BasePlugin,
    ModelProvider,
    RouteProvider,
    PageProvider,
    CommandProvider,
    EventProvider,
    TaskProvider,
)
from application.plugins.exceptions import (
    PluginError,
    PluginNotFoundError,
    PluginLoadError,
    PluginDependencyError,
    PluginConfigurationError,
    PluginLifecycleError,
    PluginAlreadyEnabledError,
    PluginNotEnabledError,
    BuiltinPluginError,
    PluginValidationError,
)

__all__ = [
    # Manifest and config
    "PluginManifest",
    "PluginConfig",
    "PluginType",
    "PluginCategory",
    "RouteScope",
    # Core classes
    "PluginRegistry",
    "PluginLifecycleManager",
    "PluginLoader",
    "PluginConfigService",
    # Base classes
    "BasePlugin",
    "ModelProvider",
    "RouteProvider",
    "PageProvider",
    "CommandProvider",
    "EventProvider",
    "TaskProvider",
    # Exceptions
    "PluginError",
    "PluginNotFoundError",
    "PluginLoadError",
    "PluginDependencyError",
    "PluginConfigurationError",
    "PluginLifecycleError",
    "PluginAlreadyEnabledError",
    "PluginNotEnabledError",
    "BuiltinPluginError",
    "PluginValidationError",
]
