"""
SpeedGaming Plugin implementation.

This module contains the SpeedGamingPlugin class that integrates
SpeedGaming.org functionality into the SahaBot2 plugin system.
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


class SpeedGamingPlugin(BasePlugin):
    """
    SpeedGaming.org Integration Plugin.

    Provides schedule sync and match import from SpeedGaming.org
    for tournament management.

    This plugin re-exports services from the core application to provide
    a unified interface for SpeedGaming functionality.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "speedgaming"

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            id="speedgaming",
            name="SpeedGaming.org Integration",
            version="1.0.0",
            description="SpeedGaming.org schedule sync and match import",
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
                services=["SpeedGamingService", "SpeedGamingETLService"],
                tasks=["speedgaming_sync"],
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "sync_interval_minutes": {
                        "type": "integer",
                        "default": 5,
                        "description": "How often to sync schedule from SpeedGaming",
                    },
                    "auto_create_users": {
                        "type": "boolean",
                        "default": True,
                        "description": "Automatically create users from SpeedGaming data",
                    },
                    "sync_window_days": {
                        "type": "integer",
                        "default": 7,
                        "description": "Number of days ahead to sync schedule",
                    },
                },
            },
        )

    # ─────────────────────────────────────────────────────────────
    # Lifecycle Hooks
    # ─────────────────────────────────────────────────────────────

    async def on_load(self) -> None:
        """Called when the plugin is loaded at startup."""
        logger.info("SpeedGaming plugin loaded")

    async def on_enable(self, organization_id: int, config: PluginConfig) -> None:
        """Called when the plugin is enabled for an organization."""
        logger.info(
            "SpeedGaming plugin enabled for organization %s with config: %s",
            organization_id,
            config.settings,
        )

    async def on_disable(self, organization_id: int) -> None:
        """Called when the plugin is disabled for an organization."""
        logger.info("SpeedGaming plugin disabled for organization %s", organization_id)

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded at shutdown."""
        logger.info("SpeedGaming plugin unloaded")

    # ─────────────────────────────────────────────────────────────
    # Contribution Methods
    # ─────────────────────────────────────────────────────────────

    def get_models(self) -> List[Type]:
        """
        Return database models contributed by this plugin.

        SpeedGaming doesn't have its own models - it imports data into
        Tournament and Match models.
        """
        return []

    def get_api_router(self) -> Optional[Any]:
        """
        Return FastAPI router for API endpoints.

        Note: SpeedGaming API routes are currently managed by the core application.
        """
        return None

    def get_pages(self) -> List[Dict[str, Any]]:
        """
        Return page registration definitions.

        SpeedGaming configuration is part of the Tournament admin pages.
        """
        return []

    def get_event_types(self) -> List[Type]:
        """
        Return event types defined by this plugin.
        """
        from plugins.builtin.speedgaming.events.types import (
            SpeedGamingSyncStartedEvent,
            SpeedGamingSyncCompletedEvent,
        )

        return [
            SpeedGamingSyncStartedEvent,
            SpeedGamingSyncCompletedEvent,
        ]

    def get_event_listeners(self) -> List[Dict[str, Any]]:
        """Return event listeners to register."""
        return []

    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        Return scheduled tasks to register.

        The SpeedGaming sync task is currently managed by the core task scheduler.
        """
        return []

    def get_authorization_actions(self) -> List[str]:
        """Return authorization actions defined by this plugin."""
        return [
            "speedgaming:sync:trigger",
            "speedgaming:config:read",
            "speedgaming:config:update",
        ]

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """Return navigation menu items to add."""
        return []

    # ─────────────────────────────────────────────────────────────
    # Service Accessors
    # ─────────────────────────────────────────────────────────────

    def get_speedgaming_service(self) -> Any:
        """Get the SpeedGaming API service instance."""
        from plugins.builtin.speedgaming.services import SpeedGamingService

        return SpeedGamingService()

    def get_etl_service(self) -> Any:
        """Get the SpeedGaming ETL service instance."""
        from plugins.builtin.speedgaming.services import SpeedGamingETLService

        return SpeedGamingETLService()
