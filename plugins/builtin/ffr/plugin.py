"""
FFR Plugin implementation.

This module contains the FFRPlugin class that integrates
Final Fantasy Randomizer functionality into the SahaBot2 plugin system.
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


class FFRPlugin(BaseRandomizerPlugin):
    """
    Final Fantasy Randomizer Plugin.

    Provides FFR seed generation.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "ffr"

    @property
    def randomizer_name(self) -> str:
        """Return the display name of the randomizer."""
        return "Final Fantasy Randomizer"

    @property
    def randomizer_short_name(self) -> str:
        """Return the short name of the randomizer."""
        return "ffr"

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            id="ffr",
            name="Final Fantasy Randomizer",
            version="1.0.0",
            description="Final Fantasy (NES) randomizer seed generation",
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
                services=["FFRService"],
                api_routes=[
                    APIRouteDefinition(
                        prefix="/api/randomizer/ffr",
                        scope=RouteScope.GLOBAL,
                        tags=["randomizer", "ffr"],
                    )
                ],
            ),
        )

    def get_service(self) -> Any:
        """Get the FFR service instance."""
        from plugins.builtin.ffr.services import FFRService

        return FFRService()

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
            "ffr:generate",
            "ffr:preset:read",
        ]
