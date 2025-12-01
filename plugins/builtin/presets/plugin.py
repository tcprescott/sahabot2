"""
Presets Plugin implementation.

This module contains the PresetsPlugin class that integrates
preset management functionality into the SahaBot2 plugin system.

The Presets plugin provides:
- Preset namespace management
- Randomizer preset CRUD operations
- Preset sharing and visibility controls
"""

import logging
from typing import Any, Dict, List, Optional, Type

from application.plugins.base.plugin import BasePlugin
from application.plugins.manifest import (
    PluginManifest,
    PluginConfig,
    PluginType,
    PluginCategory,
)

logger = logging.getLogger(__name__)


class PresetsPlugin(BasePlugin):
    """
    Preset Management System Plugin.

    Provides core preset storage, namespaces, and sharing functionality
    for all randomizer plugins.

    This plugin re-exports models, services, and events from the core
    application to provide a unified interface for preset functionality.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "presets"

    @property
    def manifest(self) -> PluginManifest:
        """
        Return the plugin manifest.

        Note: This is a code-defined manifest that mirrors manifest.yaml.
        The manifest.yaml file serves as documentation for the plugin.
        """
        return PluginManifest(
            id="presets",
            name="Preset Management System",
            version="1.0.0",
            description="Core preset storage, namespaces, and sharing functionality for randomizers",
            author="SahaBot2 Team",
            type=PluginType.BUILTIN,
            category=PluginCategory.CORE,
            enabled_by_default=True,
            private=False,
            global_plugin=False,
            config_schema={
                "type": "object",
                "properties": {
                    "max_presets_per_user": {
                        "type": "integer",
                        "default": 100,
                        "description": "Maximum number of presets per user",
                    },
                    "max_preset_size_kb": {
                        "type": "integer",
                        "default": 100,
                        "description": "Maximum size of preset YAML in kilobytes",
                    },
                },
            },
        )

    # ─────────────────────────────────────────────────────────────
    # Lifecycle Hooks
    # ─────────────────────────────────────────────────────────────

    async def on_load(self) -> None:
        """Called when the plugin is loaded at startup."""
        logger.info("Presets plugin loaded")

    async def on_enable(self, organization_id: int, config: PluginConfig) -> None:
        """Called when the plugin is enabled for an organization."""
        logger.info(
            "Presets plugin enabled for organization %s with config: %s",
            organization_id,
            config.settings,
        )

    async def on_disable(self, organization_id: int) -> None:
        """Called when the plugin is disabled for an organization."""
        logger.info("Presets plugin disabled for organization %s", organization_id)

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded at shutdown."""
        logger.info("Presets plugin unloaded")

    # ─────────────────────────────────────────────────────────────
    # Contribution Methods
    # ─────────────────────────────────────────────────────────────

    def get_models(self) -> List[Type]:
        """
        Return database models contributed by this plugin.

        Returns preset-related models from the core application.
        """
        from plugins.builtin.presets.models import (
            PresetNamespace,
            RandomizerPreset,
        )

        return [
            PresetNamespace,
            RandomizerPreset,
        ]

    def get_api_router(self) -> Optional[Any]:
        """
        Return FastAPI router for API endpoints.

        Note: Preset API routes are currently managed by the core application.
        This returns None as routes are not yet migrated to the plugin.
        """
        # API routes will be migrated in a future phase
        return None

    def get_pages(self) -> List[Dict[str, Any]]:
        """
        Return page registration definitions.

        Note: Preset pages are registered by the core application.
        This returns metadata about the pages provided by this plugin.
        """
        return [
            {
                "path": "/org/{org_id}/presets",
                "title": "Preset Management",
                "requires_auth": True,
                "requires_org": True,
                "active_nav": "presets",
            },
        ]

    def get_event_types(self) -> List[Type]:
        """
        Return event types defined by this plugin.

        Returns preset-related event types from the core application.
        """
        from plugins.builtin.presets.events.types import (
            PresetCreatedEvent,
            PresetUpdatedEvent,
            PresetDeletedEvent,
            NamespaceCreatedEvent,
            NamespaceUpdatedEvent,
        )

        return [
            PresetCreatedEvent,
            PresetUpdatedEvent,
            PresetDeletedEvent,
            NamespaceCreatedEvent,
            NamespaceUpdatedEvent,
        ]

    def get_event_listeners(self) -> List[Dict[str, Any]]:
        """
        Return event listeners to register.

        Note: Preset event listeners are registered by the core application.
        This returns an empty list as listeners are managed centrally.
        """
        return []

    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        Return scheduled tasks to register.

        Note: No scheduled tasks are needed for presets currently.
        """
        return []

    def get_authorization_actions(self) -> List[str]:
        """Return authorization actions defined by this plugin."""
        return [
            "preset:create",
            "preset:read",
            "preset:update",
            "preset:delete",
            "namespace:create",
            "namespace:read",
            "namespace:update",
            "namespace:delete",
        ]

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """Return navigation menu items to add."""
        return [
            {
                "label": "Presets",
                "path": "/org/{org_id}/presets",
                "icon": "settings",
                "position": "sidebar",
                "order": 50,
                "requires_permission": "preset:read",
            },
        ]
