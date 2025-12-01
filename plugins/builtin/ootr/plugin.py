"""
OOTR Plugin implementation.

This module contains the OOTRPlugin class that integrates
Ocarina of Time Randomizer functionality into the SahaBot2 plugin system.
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


class OOTRPlugin(BaseRandomizerPlugin):
    """
    Ocarina of Time Randomizer Plugin.

    Provides OoTR seed generation via the official API.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "ootr"

    @property
    def randomizer_name(self) -> str:
        """Return the display name of the randomizer."""
        return "Ocarina of Time Randomizer"

    @property
    def randomizer_short_name(self) -> str:
        """Return the short name of the randomizer."""
        return "ootr"

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            id="ootr",
            name="Ocarina of Time Randomizer",
            version="1.0.0",
            description="Ocarina of Time randomizer seed generation",
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
                services=["OOTRService"],
                api_routes=[
                    APIRouteDefinition(
                        prefix="/api/randomizer/ootr",
                        scope=RouteScope.GLOBAL,
                        tags=["randomizer", "ootr"],
                    )
                ],
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "default_version": {
                        "type": "string",
                        "default": "6.1.0",
                        "description": "Default OoTR version",
                    },
                    "default_encrypt": {
                        "type": "boolean",
                        "default": True,
                        "description": "Default encryption setting",
                    },
                },
            },
        )

    def get_service(self) -> Any:
        """Get the OOTR service instance."""
        from plugins.builtin.ootr.services import OOTRService

        return OOTRService()

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
            "ootr:generate",
            "ootr:preset:read",
        ]
