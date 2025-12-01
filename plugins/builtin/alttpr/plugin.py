"""
ALTTPR Plugin implementation.

This module contains the ALTTPRPlugin class that integrates
A Link to the Past Randomizer functionality into the SahaBot2 plugin system.
"""

import logging
from typing import Any, Dict, List, Optional, Type

from application.plugins.manifest import (
    PluginManifest,
    PluginType,
    PluginCategory,
    PluginProvides,
    PluginRequirements,
    PluginDependency,
    APIRouteDefinition,
    RouteScope,
)
from plugins.builtin._randomizer_base import BaseRandomizerPlugin

logger = logging.getLogger(__name__)


class ALTTPRPlugin(BaseRandomizerPlugin):
    """
    A Link to the Past Randomizer Plugin.

    Provides ALTTPR seed generation with mystery mode and RaceTime.gg integration.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "alttpr"

    @property
    def randomizer_name(self) -> str:
        """Return the display name of the randomizer."""
        return "A Link to the Past Randomizer"

    @property
    def randomizer_short_name(self) -> str:
        """Return the short name of the randomizer."""
        return "alttpr"

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            id="alttpr",
            name="A Link to the Past Randomizer",
            version="1.0.0",
            description="ALTTPR seed generation with mystery mode and RaceTime.gg integration",
            author="SahaBot2 Team",
            type=PluginType.BUILTIN,
            category=PluginCategory.RANDOMIZER,
            enabled_by_default=True,
            private=False,
            global_plugin=False,
            requires=PluginRequirements(
                sahabot2=">=1.0.0",
                python=">=3.11",
                plugins=[PluginDependency(plugin_id="presets")],
            ),
            provides=PluginProvides(
                services=["ALTTPRService", "ALTTPRMysteryService"],
                api_routes=[
                    APIRouteDefinition(
                        prefix="/api/randomizer/alttpr",
                        scope=RouteScope.GLOBAL,
                        tags=["randomizer", "alttpr"],
                    )
                ],
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "baseurl": {
                        "type": "string",
                        "default": "https://alttpr.com",
                        "description": "Base URL for ALTTPR API",
                    },
                    "default_tournament_mode": {
                        "type": "boolean",
                        "default": True,
                        "description": "Default tournament mode for seed generation",
                    },
                    "default_spoilers": {
                        "type": "string",
                        "default": "off",
                        "enum": ["on", "off", "generate"],
                        "description": "Default spoiler setting",
                    },
                },
            },
        )

    def get_service(self) -> Any:
        """Get the ALTTPR service instance."""
        from plugins.builtin.alttpr.services import ALTTPRService

        return ALTTPRService()

    def get_mystery_service(self) -> Any:
        """Get the ALTTPR mystery service instance."""
        from plugins.builtin.alttpr.services import ALTTPRMysteryService

        return ALTTPRMysteryService()

    def get_api_router(self) -> Optional[Any]:
        """Return FastAPI router for API endpoints."""
        # API routes will be migrated in a future phase
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
            "alttpr:generate",
            "alttpr:mystery:generate",
            "alttpr:preset:read",
        ]
