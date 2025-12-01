"""
AsyncQualifier Plugin implementation.

This module contains the AsyncQualifierPlugin class that integrates
async qualifier functionality into the SahaBot2 plugin system.

The AsyncQualifier plugin provides:
- Async qualifier creation and management
- Pool and permalink management
- Race submission and scoring
- Live race events with RaceTime.gg integration
- Discord command integration for race actions
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


class AsyncQualifierPlugin(BasePlugin):
    """
    AsyncQualifier System Plugin.

    Provides async qualifier management with pool-based racing, scoring,
    and live race events with RaceTime.gg integration.

    This plugin re-exports models, services, and events from the core
    application to provide a unified interface for async qualifier functionality.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "async_qualifier"

    @property
    def manifest(self) -> PluginManifest:
        """
        Return the plugin manifest.

        Note: This is a code-defined manifest that mirrors manifest.yaml.
        The manifest.yaml file serves as documentation for the plugin.
        """
        return PluginManifest(
            id="async_qualifier",
            name="Async Qualifier System",
            version="1.0.0",
            description="Async qualifier management with pool-based racing, scoring, and live race events",
            author="SahaBot2 Team",
            type=PluginType.BUILTIN,
            category=PluginCategory.COMPETITION,
            enabled_by_default=True,
            private=False,
            global_plugin=False,
            config_schema={
                "type": "object",
                "properties": {
                    "enable_live_races": {
                        "type": "boolean",
                        "default": True,
                        "description": "Enable live race feature with RaceTime.gg integration",
                    },
                    "enable_discord_integration": {
                        "type": "boolean",
                        "default": True,
                        "description": "Enable Discord thread creation for async races",
                    },
                    "default_runs_per_pool": {
                        "type": "integer",
                        "default": 1,
                        "description": "Default number of runs allowed per pool",
                    },
                    "race_timeout_minutes": {
                        "type": "integer",
                        "default": 240,
                        "description": "Timeout for async races in minutes (default 4 hours)",
                    },
                },
            },
        )

    # ─────────────────────────────────────────────────────────────
    # Lifecycle Hooks
    # ─────────────────────────────────────────────────────────────

    async def on_load(self) -> None:
        """Called when the plugin is loaded at startup."""
        logger.info("AsyncQualifier plugin loaded")

    async def on_enable(self, organization_id: int, config: PluginConfig) -> None:
        """Called when the plugin is enabled for an organization."""
        logger.info(
            "AsyncQualifier plugin enabled for organization %s with config: %s",
            organization_id,
            config.settings,
        )

    async def on_disable(self, organization_id: int) -> None:
        """Called when the plugin is disabled for an organization."""
        logger.info("AsyncQualifier plugin disabled for organization %s", organization_id)

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded at shutdown."""
        logger.info("AsyncQualifier plugin unloaded")

    # ─────────────────────────────────────────────────────────────
    # Contribution Methods
    # ─────────────────────────────────────────────────────────────

    def get_models(self) -> List[Type]:
        """
        Return database models contributed by this plugin.

        Returns async qualifier-related models from the core application.
        """
        from plugins.builtin.async_qualifier.models import (
            AsyncQualifier,
            AsyncQualifierPool,
            AsyncQualifierPermalink,
            AsyncQualifierRace,
            AsyncQualifierLiveRace,
            AsyncQualifierAuditLog,
        )

        return [
            AsyncQualifier,
            AsyncQualifierPool,
            AsyncQualifierPermalink,
            AsyncQualifierRace,
            AsyncQualifierLiveRace,
            AsyncQualifierAuditLog,
        ]

    def get_api_router(self) -> Optional[Any]:
        """
        Return FastAPI router for API endpoints.

        Returns the async qualifier API router from the core application.
        Note: AsyncQualifier has two routers (async_qualifiers and async_live_races).
        This returns the primary async_qualifiers router.
        """
        from plugins.builtin.async_qualifier.api import async_qualifiers_router

        return async_qualifiers_router

    def get_additional_routers(self) -> List[Any]:
        """
        Return additional FastAPI routers.

        AsyncQualifier has multiple API routers - this returns the secondary ones.
        """
        from plugins.builtin.async_qualifier.api import async_live_races_router

        return [async_live_races_router]

    def get_pages(self) -> List[Dict[str, Any]]:
        """
        Return page registration definitions.

        Note: Async qualifier pages are registered by the core application.
        This returns metadata about the pages provided by this plugin.
        """
        return [
            {
                "path": "/org/{org_id}/async",
                "title": "Async Qualifiers",
                "requires_auth": True,
                "requires_org": True,
                "active_nav": "async-qualifiers",
            },
            {
                "path": "/org/{org_id}/async/{qualifier_id}",
                "title": "Async Qualifier Detail",
                "requires_auth": True,
                "requires_org": True,
                "active_nav": "async-qualifiers",
            },
            {
                "path": "/org/{org_id}/async-admin",
                "title": "Async Qualifier Admin",
                "requires_auth": True,
                "requires_org": True,
                "active_nav": "async-admin",
            },
            {
                "path": "/org/{org_id}/async-admin/{qualifier_id}",
                "title": "Async Qualifier Admin Detail",
                "requires_auth": True,
                "requires_org": True,
                "active_nav": "async-admin",
            },
        ]

    def get_event_types(self) -> List[Type]:
        """
        Return event types defined by this plugin.

        Returns async qualifier-related event types from the core application.
        """
        from application.events import (
            RaceSubmittedEvent,
            RaceApprovedEvent,
            RaceRejectedEvent,
            AsyncLiveRaceCreatedEvent,
            AsyncLiveRaceUpdatedEvent,
            AsyncLiveRaceRoomOpenedEvent,
            AsyncLiveRaceStartedEvent,
            AsyncLiveRaceFinishedEvent,
            AsyncLiveRaceCancelledEvent,
        )

        return [
            RaceSubmittedEvent,
            RaceApprovedEvent,
            RaceRejectedEvent,
            AsyncLiveRaceCreatedEvent,
            AsyncLiveRaceUpdatedEvent,
            AsyncLiveRaceRoomOpenedEvent,
            AsyncLiveRaceStartedEvent,
            AsyncLiveRaceFinishedEvent,
            AsyncLiveRaceCancelledEvent,
        ]

    def get_event_listeners(self) -> List[Dict[str, Any]]:
        """
        Return event listeners to register.

        Note: Async qualifier event listeners are registered by the core application.
        This returns an empty list as listeners are managed centrally.
        """
        # Event listeners are registered via application/events/listeners.py
        # In a future phase, they may be moved here
        return []

    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        Return scheduled tasks to register.

        Note: Async qualifier tasks are managed by the core task scheduler.
        This returns an empty list as tasks are managed centrally.
        """
        # Tasks are registered via the core task scheduler
        # In a future phase, they may be moved here
        return []

    def get_authorization_actions(self) -> List[str]:
        """Return authorization actions defined by this plugin."""
        return [
            "async_qualifier:create",
            "async_qualifier:read",
            "async_qualifier:update",
            "async_qualifier:delete",
            "async_race:submit",
            "async_race:review",
            "async_live_race:create",
            "async_live_race:manage",
        ]

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """Return navigation menu items to add."""
        return [
            {
                "label": "Async Qualifiers",
                "path": "/org/{org_id}/async",
                "icon": "timer",
                "position": "sidebar",
                "order": 20,
                "requires_permission": "async_qualifier:read",
            },
            {
                "label": "Async Admin",
                "path": "/org/{org_id}/async-admin",
                "icon": "settings",
                "position": "admin",
                "order": 20,
                "requires_permission": "async_qualifier:update",
            },
        ]
