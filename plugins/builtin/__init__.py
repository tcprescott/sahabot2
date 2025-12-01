"""
Built-in plugins for SahaBot2.

This package contains core plugins that ship with the application.
Built-in plugins cannot be uninstalled but can be disabled per-organization.

Plugins in this package:
- tournament: Live tournament management
- async_qualifier: Asynchronous qualifier races
- (more to be added during migration)
"""

from plugins.builtin.tournament import TournamentPlugin
from plugins.builtin.async_qualifier import AsyncQualifierPlugin

# List of built-in plugin classes
# This list is populated as plugins are created
BUILTIN_PLUGINS = [
    TournamentPlugin,
    AsyncQualifierPlugin,
]

__all__ = ["BUILTIN_PLUGINS", "TournamentPlugin", "AsyncQualifierPlugin"]
