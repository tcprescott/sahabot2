"""
Avianart Plugin implementation.

This module contains the AvianartPlugin class that integrates
Avianart door randomizer functionality into the SahaBot2 plugin system.
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


class AvianartPlugin(BaseRandomizerPlugin):
    """
    Avianart Door Randomizer Plugin.

    Provides ALTTPR door randomizer seed generation via Avianart.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "avianart"

    @property
    def randomizer_name(self) -> str:
        """Return the display name of the randomizer."""
        return "Avianart Door Randomizer"

    @property
    def randomizer_short_name(self) -> str:
        """Return the short name of the randomizer."""
        return "avianart"

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            id="avianart",
            name="Avianart Door Randomizer",
            version="1.0.0",
            description="ALTTPR door randomizer seed generation via Avianart",
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
                services=["AvianartService"],
                api_routes=[
                    APIRouteDefinition(
                        prefix="/api/randomizer/avianart",
                        scope=RouteScope.GLOBAL,
                        tags=["randomizer", "avianart", "door"],
                    )
                ],
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "default_race": {
                        "type": "boolean",
                        "default": True,
                        "description": "Default race mode setting",
                    },
                },
            },
        )

    def get_service(self) -> Any:
        """Get the Avianart service instance."""
        from plugins.builtin.avianart.services import AvianartService

        return AvianartService()

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
            "avianart:generate",
            "avianart:preset:read",
        ]
