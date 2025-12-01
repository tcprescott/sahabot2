"""
Tournament Plugin implementation.

This module contains the TournamentPlugin class that integrates
tournament functionality into the SahaBot2 plugin system.

Note: This is currently a skeleton implementation. The actual
tournament functionality is still in the core application and
will be migrated in a future phase.
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


class TournamentPlugin(BasePlugin):
    """
    Tournament System Plugin.

    Provides live tournament management with scheduling, crew signups,
    and RaceTime.gg integration.

    This is a skeleton implementation that will be fully migrated
    in a future phase. Currently, tournament functionality is still
    provided by the core application modules.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "tournament"

    @property
    def manifest(self) -> PluginManifest:
        """
        Return the plugin manifest.

        Note: This is a code-defined manifest for the skeleton implementation.
        In a future phase, this will be loaded from manifest.yaml for consistency.
        The manifest.yaml file serves as the source of truth for documentation.
        """
        return PluginManifest(
            id="tournament",
            name="Tournament System",
            version="1.0.0",
            description="Live tournament management with scheduling, crew signups, and RaceTime.gg integration",
            author="SahaBot2 Team",
            type=PluginType.BUILTIN,
            category=PluginCategory.COMPETITION,
            enabled_by_default=True,
            private=False,
            global_plugin=False,
            config_schema={
                "type": "object",
                "properties": {
                    "enable_racetime_integration": {
                        "type": "boolean",
                        "default": True,
                        "description": "Enable RaceTime.gg room creation for matches",
                    },
                    "enable_speedgaming_sync": {
                        "type": "boolean",
                        "default": False,
                        "description": "Enable automatic schedule sync from SpeedGaming.org",
                    },
                    "default_room_visibility": {
                        "type": "string",
                        "default": "unlisted",
                        "description": "Default visibility for RaceTime rooms",
                    },
                },
            },
        )

    # ─────────────────────────────────────────────────────────────
    # Lifecycle Hooks
    # ─────────────────────────────────────────────────────────────

    async def on_load(self) -> None:
        """Called when the plugin is loaded at startup."""
        logger.info("Tournament plugin loaded")

    async def on_enable(self, organization_id: int, config: PluginConfig) -> None:
        """Called when the plugin is enabled for an organization."""
        logger.info(
            "Tournament plugin enabled for organization %s with config: %s",
            organization_id,
            config.settings,
        )

    async def on_disable(self, organization_id: int) -> None:
        """Called when the plugin is disabled for an organization."""
        logger.info("Tournament plugin disabled for organization %s", organization_id)

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded at shutdown."""
        logger.info("Tournament plugin unloaded")

    # ─────────────────────────────────────────────────────────────
    # Contribution Methods
    # Note: These are skeleton implementations. The actual models,
    # services, pages, etc. are still in the core application and
    # will be migrated in a future phase.
    # ─────────────────────────────────────────────────────────────

    def get_models(self) -> List[Type]:
        """
        Return database models contributed by this plugin.

        Note: Tournament models are currently in models/match_schedule.py
        and will be migrated here in a future phase.
        """
        # Future: return [Tournament, Match, MatchPlayers, ...]
        return []

    def get_api_router(self) -> Optional[Any]:
        """
        Return FastAPI router for API endpoints.

        Note: Tournament API routes are currently in api/routes/tournaments.py
        and will be migrated here in a future phase.
        """
        # Future: return router from plugins.builtin.tournament.api
        return None

    def get_pages(self) -> List[Dict[str, Any]]:
        """
        Return page registration definitions.

        Note: Tournament pages are currently in pages/tournaments.py
        and will be migrated here in a future phase.
        """
        # Future: return page registrations
        return []

    def get_event_types(self) -> List[Type]:
        """
        Return event types defined by this plugin.

        Note: Tournament events are currently in application/events/types.py
        and will be migrated here in a future phase.
        """
        # Future: return [TournamentCreatedEvent, MatchScheduledEvent, ...]
        return []

    def get_event_listeners(self) -> List[Dict[str, Any]]:
        """
        Return event listeners to register.

        Note: Tournament listeners are currently in application/events/listeners.py
        and will be migrated here in a future phase.
        """
        # Future: return listener registrations
        return []

    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        Return scheduled tasks to register.

        Note: Tournament tasks are currently in the task scheduler
        and will be migrated here in a future phase.
        """
        # Future: return task registrations
        return []

    def get_authorization_actions(self) -> List[str]:
        """Return authorization actions defined by this plugin."""
        return [
            "tournament:create",
            "tournament:read",
            "tournament:update",
            "tournament:delete",
            "match:create",
            "match:read",
            "match:update",
            "match:delete",
            "crew:manage",
        ]

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """Return navigation menu items to add."""
        return [
            {
                "label": "Tournaments",
                "path": "/org/{org_id}/tournaments",
                "icon": "trophy",
                "position": "sidebar",
                "order": 10,
                "requires_permission": "tournament:read",
            },
            {
                "label": "Tournament Admin",
                "path": "/org/{org_id}/tournament-admin",
                "icon": "settings",
                "position": "admin",
                "order": 10,
                "requires_permission": "tournament:update",
            },
        ]
