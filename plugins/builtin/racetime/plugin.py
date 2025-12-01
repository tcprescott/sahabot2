"""
RaceTime Plugin implementation.

This module contains the RaceTimePlugin class that integrates
RaceTime.gg functionality into the SahaBot2 plugin system.
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
    APIRouteDefinition,
    RouteScope,
)

logger = logging.getLogger(__name__)


class RaceTimePlugin(BasePlugin):
    """
    RaceTime.gg Integration Plugin.

    Provides bot management, room tracking, and race handlers for
    RaceTime.gg integration.

    This plugin re-exports models, services, and handlers from the core
    application to provide a unified interface for RaceTime functionality.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "racetime"

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            id="racetime",
            name="RaceTime.gg Integration",
            version="1.0.0",
            description="RaceTime.gg bot management, room profiles, and race handlers",
            author="SahaBot2 Team",
            type=PluginType.BUILTIN,
            category=PluginCategory.INTEGRATION,
            enabled_by_default=True,
            private=False,
            global_plugin=False,
            provides=PluginProvides(
                models=[
                    "RacetimeBot",
                    "RacetimeBotOrganization",
                    "RacetimeRoom",
                    "RaceRoomProfile",
                ],
                services=[
                    "RacetimeService",
                    "RacetimeBotService",
                    "RacetimeRoomService",
                    "RaceRoomProfileService",
                    "RacetimeApiService",
                ],
                api_routes=[
                    APIRouteDefinition(
                        prefix="/api/org/{org_id}/racetime",
                        scope=RouteScope.ORGANIZATION,
                        tags=["racetime"],
                    ),
                ],
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "auto_connect_bots": {
                        "type": "boolean",
                        "default": True,
                        "description": "Automatically connect bots on startup",
                    },
                    "default_handler_class": {
                        "type": "string",
                        "default": "SahaRaceHandler",
                        "description": "Default race handler class for new bots",
                    },
                },
            },
        )

    # ─────────────────────────────────────────────────────────────
    # Lifecycle Hooks
    # ─────────────────────────────────────────────────────────────

    async def on_load(self) -> None:
        """Called when the plugin is loaded at startup."""
        logger.info("RaceTime plugin loaded")

    async def on_enable(self, organization_id: int, config: PluginConfig) -> None:
        """Called when the plugin is enabled for an organization."""
        logger.info(
            "RaceTime plugin enabled for organization %s with config: %s",
            organization_id,
            config.settings,
        )

    async def on_disable(self, organization_id: int) -> None:
        """Called when the plugin is disabled for an organization."""
        logger.info("RaceTime plugin disabled for organization %s", organization_id)

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded at shutdown."""
        logger.info("RaceTime plugin unloaded")

    # ─────────────────────────────────────────────────────────────
    # Contribution Methods
    # ─────────────────────────────────────────────────────────────

    def get_models(self) -> List[Type]:
        """
        Return database models contributed by this plugin.

        Returns RaceTime-related models from the core application.
        """
        from plugins.builtin.racetime.models import (
            RacetimeBot,
            RacetimeBotOrganization,
            RacetimeRoom,
            RaceRoomProfile,
        )

        return [
            RacetimeBot,
            RacetimeBotOrganization,
            RacetimeRoom,
            RaceRoomProfile,
        ]

    def get_api_router(self) -> Optional[Any]:
        """
        Return FastAPI router for API endpoints.

        Note: RaceTime API routes are currently managed by the core application.
        This returns None as routes are not yet migrated to the plugin.
        """
        # API routes will be migrated in a future phase
        return None

    def get_pages(self) -> List[Dict[str, Any]]:
        """
        Return page registration definitions.

        Note: RaceTime pages are registered by the core application.
        This returns metadata about the pages provided by this plugin.
        """
        return [
            {
                "path": "/org/{org_id}/racetime",
                "title": "RaceTime Configuration",
                "requires_auth": True,
                "requires_org": True,
                "active_nav": "racetime",
            },
        ]

    def get_event_types(self) -> List[Type]:
        """
        Return event types defined by this plugin.

        Returns RaceTime-related event types.
        """
        from plugins.builtin.racetime.events.types import (
            RaceRoomCreatedEvent,
            RaceRoomFinishedEvent,
            RacetimeBotStatusChangedEvent,
        )

        return [
            RaceRoomCreatedEvent,
            RaceRoomFinishedEvent,
            RacetimeBotStatusChangedEvent,
        ]

    def get_event_listeners(self) -> List[Dict[str, Any]]:
        """
        Return event listeners to register.

        Note: RaceTime event listeners are registered by the core application.
        """
        return []

    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        Return scheduled tasks to register.

        Note: No scheduled tasks are needed for RaceTime currently.
        """
        return []

    def get_authorization_actions(self) -> List[str]:
        """Return authorization actions defined by this plugin."""
        return [
            "racetime:bot:create",
            "racetime:bot:read",
            "racetime:bot:update",
            "racetime:bot:delete",
            "racetime:room:create",
            "racetime:room:read",
            "racetime:profile:create",
            "racetime:profile:read",
            "racetime:profile:update",
            "racetime:profile:delete",
        ]

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """Return navigation menu items to add."""
        return [
            {
                "label": "RaceTime",
                "path": "/org/{org_id}/racetime",
                "icon": "sports_esports",
                "position": "sidebar",
                "order": 60,
                "requires_permission": "racetime:bot:read",
            },
        ]

    # ─────────────────────────────────────────────────────────────
    # Service Accessors
    # ─────────────────────────────────────────────────────────────

    def get_racetime_service(self) -> Any:
        """Get the main RaceTime service instance."""
        from plugins.builtin.racetime.services import RacetimeService

        return RacetimeService()

    def get_bot_service(self) -> Any:
        """Get the RaceTime bot service instance."""
        from plugins.builtin.racetime.services import RacetimeBotService

        return RacetimeBotService()

    def get_room_service(self) -> Any:
        """Get the RaceTime room service instance."""
        from plugins.builtin.racetime.services import RacetimeRoomService

        return RacetimeRoomService()

    def get_profile_service(self) -> Any:
        """Get the race room profile service instance."""
        from plugins.builtin.racetime.services import RaceRoomProfileService

        return RaceRoomProfileService()
