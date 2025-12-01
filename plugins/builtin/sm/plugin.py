"""
SM Plugin implementation.

This module contains the SMPlugin class that integrates
Super Metroid Randomizer functionality into the SahaBot2 plugin system.
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


class SMPlugin(BaseRandomizerPlugin):
    """
    Super Metroid Randomizer Plugin.

    Provides SM seed generation via VARIA and DASH with RaceTime.gg integration.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "sm"

    @property
    def randomizer_name(self) -> str:
        """Return the display name of the randomizer."""
        return "Super Metroid Randomizer"

    @property
    def randomizer_short_name(self) -> str:
        """Return the short name of the randomizer."""
        return "sm"

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            id="sm",
            name="Super Metroid Randomizer",
            version="1.0.0",
            description="Super Metroid seed generation via VARIA and DASH randomizers",
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
                services=["SMService"],
                api_routes=[
                    APIRouteDefinition(
                        prefix="/api/randomizer/sm",
                        scope=RouteScope.GLOBAL,
                        tags=["randomizer", "sm", "varia", "dash"],
                    )
                ],
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "varia_baseurl": {
                        "type": "string",
                        "default": "https://sm.samus.link",
                        "description": "Base URL for VARIA API",
                    },
                    "dash_baseurl": {
                        "type": "string",
                        "default": "https://dashrando.net",
                        "description": "Base URL for DASH API",
                    },
                    "default_randomizer_type": {
                        "type": "string",
                        "default": "varia",
                        "enum": ["varia", "dash", "total", "multiworld"],
                        "description": "Default SM randomizer type",
                    },
                },
            },
        )

    def get_service(self) -> Any:
        """Get the SM service instance."""
        from plugins.builtin.sm.services import SMService

        return SMService()

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
            "sm:generate",
            "sm:preset:read",
        ]
