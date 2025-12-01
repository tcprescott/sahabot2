"""
Presets plugin for SahaBot2.

This plugin provides core preset management functionality including:
- Preset namespace management (user and organization namespaces)
- Randomizer preset CRUD operations
- Preset sharing and visibility controls

This plugin is a dependency for all randomizer plugins.
"""

from plugins.builtin.presets.plugin import PresetsPlugin

__all__ = ["PresetsPlugin"]
