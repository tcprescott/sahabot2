"""
Plugin-specific exceptions.

This module defines all exceptions that can be raised by the plugin system.
"""


class PluginError(Exception):
    """Base exception for plugin errors."""

    pass


class PluginNotFoundError(PluginError):
    """Plugin not found in registry."""

    pass


class PluginLoadError(PluginError):
    """Error during plugin loading."""

    pass


class PluginDependencyError(PluginError):
    """Missing or incompatible dependency."""

    pass


class PluginConfigurationError(PluginError):
    """Invalid plugin configuration."""

    pass


class PluginLifecycleError(PluginError):
    """Error during lifecycle transition."""

    pass


class PluginAlreadyEnabledError(PluginError):
    """Plugin already enabled for organization."""

    pass


class PluginNotEnabledError(PluginError):
    """Plugin not enabled for organization."""

    pass


class BuiltinPluginError(PluginError):
    """Cannot perform action on builtin plugin."""

    pass


class PluginValidationError(PluginError):
    """Plugin manifest validation failed."""

    pass
