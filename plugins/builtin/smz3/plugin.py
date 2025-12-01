"""
SMZ3 Plugin implementation.

This module contains the SMZ3Plugin class that integrates
Super Metroid/ALTTP Combo Randomizer functionality into the SahaBot2 plugin system.
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


class SMZ3Plugin(BaseRandomizerPlugin):
    """
    SMZ3 Combo Randomizer Plugin.

    Provides SMZ3 combo seed generation with RaceTime.gg integration.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "smz3"

    @property
    def randomizer_name(self) -> str:
        """Return the display name of the randomizer."""
        return "SMZ3 Combo Randomizer"

    @property
    def randomizer_short_name(self) -> str:
        """Return the short name of the randomizer."""
        return "smz3"

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            id="smz3",
            name="SMZ3 Combo Randomizer",
            version="1.0.0",
            description="Super Metroid and A Link to the Past combo randomizer seed generation",
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
                services=["SMZ3Service"],
                api_routes=[
                    APIRouteDefinition(
                        prefix="/api/randomizer/smz3",
                        scope=RouteScope.GLOBAL,
                        tags=["randomizer", "smz3"],
                    )
                ],
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "baseurl": {
                        "type": "string",
                        "default": "https://samus.link",
                        "description": "Base URL for SMZ3 API",
                    },
                    "default_tournament_mode": {
                        "type": "boolean",
                        "default": True,
                        "description": "Default tournament mode for seed generation",
                    },
                },
            },
        )

    def get_service(self) -> Any:
        """Get the SMZ3 service instance."""
        from plugins.builtin.smz3.services import SMZ3Service

        return SMZ3Service()

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
            "smz3:generate",
            "smz3:preset:read",
        ]
