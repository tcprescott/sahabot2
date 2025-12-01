"""
DiscordEvents Plugin implementation.

This module contains the DiscordEventsPlugin class that integrates
Discord Scheduled Events functionality into the SahaBot2 plugin system.
"""

import logging
from typing import Any, Dict, List, Optional, Type

from application.plugins.base.plugin import BasePlugin
from application.plugins.manifest import (
    PluginManifest,
    PluginConfig,
    PluginType,
    PluginCategory,
    PluginProvides,
    PluginRequirements,
    PluginDependency,
)

logger = logging.getLogger(__name__)


class DiscordEventsPlugin(BasePlugin):
    """
    Discord Scheduled Events Integration Plugin.

    Provides Discord scheduled events integration for tournament matches,
    including auto-creation, status sync, and cleanup.

    This plugin re-exports models and services from the core application
    to provide a unified interface for Discord Events functionality.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "discord_events"

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            id="discord_events",
            name="Discord Scheduled Events",
            version="1.0.0",
            description="Discord scheduled events integration for tournament matches",
            author="SahaBot2 Team",
            type=PluginType.BUILTIN,
            category=PluginCategory.INTEGRATION,
            enabled_by_default=True,
            private=False,
            global_plugin=False,
            requires=PluginRequirements(
                sahabot2=">=1.0.0",
                python=">=3.11",
                plugins=[PluginDependency(plugin_id="tournament")],
            ),
            provides=PluginProvides(
                models=["DiscordScheduledEvent"],
                services=["DiscordScheduledEventService"],
                tasks=["scheduled_events_sync", "orphaned_events_cleanup"],
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "auto_create_events": {
                        "type": "boolean",
                        "default": True,
                        "description": "Automatically create Discord events for matches",
                    },
                    "cleanup_orphaned_events": {
                        "type": "boolean",
                        "default": True,
                        "description": "Automatically cleanup orphaned Discord events",
                    },
                    "default_event_description": {
                        "type": "string",
                        "default": "Tournament match scheduled via SahaBot2",
                        "description": "Default description for created events",
                    },
                },
            },
        )

    # ─────────────────────────────────────────────────────────────
    # Lifecycle Hooks
    # ─────────────────────────────────────────────────────────────

    async def on_load(self) -> None:
        """Called when the plugin is loaded at startup."""
        logger.info("DiscordEvents plugin loaded")

    async def on_enable(self, organization_id: int, config: PluginConfig) -> None:
        """Called when the plugin is enabled for an organization."""
        logger.info(
            "DiscordEvents plugin enabled for organization %s with config: %s",
            organization_id,
            config.settings,
        )

    async def on_disable(self, organization_id: int) -> None:
        """Called when the plugin is disabled for an organization."""
        logger.info(
            "DiscordEvents plugin disabled for organization %s", organization_id
        )

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded at shutdown."""
        logger.info("DiscordEvents plugin unloaded")

    # ─────────────────────────────────────────────────────────────
    # Contribution Methods
    # ─────────────────────────────────────────────────────────────

    def get_models(self) -> List[Type]:
        """
        Return database models contributed by this plugin.
        """
        from plugins.builtin.discord_events.models import DiscordScheduledEvent

        return [DiscordScheduledEvent]

    def get_api_router(self) -> Optional[Any]:
        """
        Return FastAPI router for API endpoints.

        Note: Discord Events API routes are currently managed by the core application.
        """
        return None

    def get_pages(self) -> List[Dict[str, Any]]:
        """
        Return page registration definitions.

        Discord Events configuration is part of the Tournament admin pages.
        """
        return []

    def get_event_types(self) -> List[Type]:
        """Return event types defined by this plugin."""
        from plugins.builtin.discord_events.events.types import (
            DiscordEventCreatedEvent,
            DiscordEventUpdatedEvent,
            DiscordEventDeletedEvent,
        )

        return [
            DiscordEventCreatedEvent,
            DiscordEventUpdatedEvent,
            DiscordEventDeletedEvent,
        ]

    def get_event_listeners(self) -> List[Dict[str, Any]]:
        """Return event listeners to register."""
        return []

    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        Return scheduled tasks to register.

        The sync and cleanup tasks are currently managed by the core task scheduler.
        """
        return []

    def get_authorization_actions(self) -> List[str]:
        """Return authorization actions defined by this plugin."""
        return [
            "discord_events:create",
            "discord_events:read",
            "discord_events:update",
            "discord_events:delete",
            "discord_events:sync",
        ]

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """Return navigation menu items to add."""
        return []

    # ─────────────────────────────────────────────────────────────
    # Service Accessors
    # ─────────────────────────────────────────────────────────────

    def get_event_service(self) -> Any:
        """Get the Discord Scheduled Event service instance."""
        from plugins.builtin.discord_events.services import DiscordScheduledEventService

        return DiscordScheduledEventService()
