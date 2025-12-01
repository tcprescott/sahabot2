"""
Bingosync Plugin implementation.

This module contains the BingosyncPlugin class that integrates
Bingosync functionality into the SahaBot2 plugin system.
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


class BingosyncPlugin(BasePlugin):
    """
    Bingosync Plugin.

    Provides Bingosync room creation and bingo card management.

    Note: This plugin doesn't depend on presets as it's not a traditional
    randomizer - it creates bingo rooms.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "bingosync"

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            id="bingosync",
            name="Bingosync",
            version="1.0.0",
            description="Bingosync room creation and bingo card management",
            author="SahaBot2 Team",
            type=PluginType.BUILTIN,
            category=PluginCategory.RANDOMIZER,
            enabled_by_default=True,
            private=False,
            global_plugin=False,
            provides=PluginProvides(
                services=["BingosyncService"],
                api_routes=[
                    APIRouteDefinition(
                        prefix="/api/bingosync",
                        scope=RouteScope.GLOBAL,
                        tags=["bingosync"],
                    )
                ],
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "default_nickname": {
                        "type": "string",
                        "default": "SahaBot2",
                        "description": "Default nickname for room creation",
                    },
                },
            },
        )

    def get_service(self, nickname: str = "SahaBot2") -> Any:
        """Get the Bingosync service instance."""
        from plugins.builtin.bingosync.services import BingosyncService

        return BingosyncService(nickname=nickname)

    async def on_load(self) -> None:
        """Called when the plugin is loaded at startup."""
        logger.info("Bingosync plugin loaded")

    async def on_enable(self, organization_id: int, config: PluginConfig) -> None:
        """Called when the plugin is enabled for an organization."""
        logger.info("Bingosync plugin enabled for organization %s", organization_id)

    async def on_disable(self, organization_id: int) -> None:
        """Called when the plugin is disabled for an organization."""
        logger.info("Bingosync plugin disabled for organization %s", organization_id)

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded at shutdown."""
        logger.info("Bingosync plugin unloaded")

    def get_api_router(self) -> Optional[Any]:
        """Return FastAPI router for API endpoints."""
        return None

    def get_pages(self) -> List[Dict[str, Any]]:
        """Return page registration definitions."""
        return []

    def get_event_types(self) -> List[Type]:
        """Return event types defined by this plugin."""
        return []

    def get_event_listeners(self) -> List[Dict[str, Any]]:
        """Return event listeners to register."""
        return []

    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Return scheduled tasks to register."""
        return []

    def get_authorization_actions(self) -> List[str]:
        """Return authorization actions defined by this plugin."""
        return [
            "bingosync:create_room",
            "bingosync:new_card",
        ]
