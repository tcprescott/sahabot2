"""
RacerVerification Plugin implementation.

This module contains the RacerVerificationPlugin class that integrates
racer verification functionality into the SahaBot2 plugin system.
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
    APIRouteDefinition,
    RouteScope,
)

logger = logging.getLogger(__name__)


class RacerVerificationPlugin(BasePlugin):
    """
    Racer Verification Plugin.

    Provides Discord role-based racer verification based on RaceTime.gg
    race completion requirements.

    This plugin re-exports models and services from the core application
    to provide a unified interface for racer verification functionality.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "racer_verification"

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            id="racer_verification",
            name="Racer Verification",
            version="1.0.0",
            description="Discord role verification based on RaceTime.gg race completion",
            author="SahaBot2 Team",
            type=PluginType.BUILTIN,
            category=PluginCategory.UTILITY,
            enabled_by_default=True,
            private=False,
            global_plugin=False,
            requires=PluginRequirements(
                sahabot2=">=1.0.0",
                python=">=3.11",
                plugins=[PluginDependency(plugin_id="racetime")],
            ),
            provides=PluginProvides(
                models=["RacerVerification", "UserRacerVerification"],
                services=["RacerVerificationService"],
                api_routes=[
                    APIRouteDefinition(
                        prefix="/api/org/{org_id}/racer-verification",
                        scope=RouteScope.ORGANIZATION,
                        tags=["racer_verification"],
                    ),
                ],
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "auto_verify_on_link": {
                        "type": "boolean",
                        "default": True,
                        "description": "Automatically verify users when they link RaceTime account",
                    },
                    "verification_check_interval_hours": {
                        "type": "integer",
                        "default": 24,
                        "description": "How often to re-check verification eligibility",
                    },
                },
            },
        )

    # ─────────────────────────────────────────────────────────────
    # Lifecycle Hooks
    # ─────────────────────────────────────────────────────────────

    async def on_load(self) -> None:
        """Called when the plugin is loaded at startup."""
        logger.info("RacerVerification plugin loaded")

    async def on_enable(self, organization_id: int, config: PluginConfig) -> None:
        """Called when the plugin is enabled for an organization."""
        logger.info(
            "RacerVerification plugin enabled for organization %s with config: %s",
            organization_id,
            config.settings,
        )

    async def on_disable(self, organization_id: int) -> None:
        """Called when the plugin is disabled for an organization."""
        logger.info(
            "RacerVerification plugin disabled for organization %s", organization_id
        )

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded at shutdown."""
        logger.info("RacerVerification plugin unloaded")

    # ─────────────────────────────────────────────────────────────
    # Contribution Methods
    # ─────────────────────────────────────────────────────────────

    def get_models(self) -> List[Type]:
        """Return database models contributed by this plugin."""
        from plugins.builtin.racer_verification.models import (
            RacerVerification,
            UserRacerVerification,
        )

        return [RacerVerification, UserRacerVerification]

    def get_api_router(self) -> Optional[Any]:
        """
        Return FastAPI router for API endpoints.

        Note: API routes are currently managed by the core application.
        """
        return None

    def get_pages(self) -> List[Dict[str, Any]]:
        """Return page registration definitions."""
        return [
            {
                "path": "/org/{org_id}/racer-verification",
                "title": "Racer Verification Settings",
                "requires_auth": True,
                "requires_org": True,
                "active_nav": "racer_verification",
            },
        ]

    def get_event_types(self) -> List[Type]:
        """Return event types defined by this plugin."""
        from plugins.builtin.racer_verification.events.types import (
            RacerVerifiedEvent,
            RacerVerificationCreatedEvent,
            RacerVerificationUpdatedEvent,
        )

        return [
            RacerVerifiedEvent,
            RacerVerificationCreatedEvent,
            RacerVerificationUpdatedEvent,
        ]

    def get_event_listeners(self) -> List[Dict[str, Any]]:
        """Return event listeners to register."""
        return []

    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Return scheduled tasks to register."""
        return []

    def get_authorization_actions(self) -> List[str]:
        """Return authorization actions defined by this plugin."""
        return [
            "racer_verification:create",
            "racer_verification:read",
            "racer_verification:update",
            "racer_verification:delete",
            "racer_verification:verify_user",
        ]

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """Return navigation menu items to add."""
        return [
            {
                "label": "Racer Verification",
                "path": "/org/{org_id}/racer-verification",
                "icon": "verified_user",
                "position": "sidebar",
                "order": 65,
                "requires_permission": "racer_verification:read",
            },
        ]

    # ─────────────────────────────────────────────────────────────
    # Service Accessors
    # ─────────────────────────────────────────────────────────────

    def get_verification_service(self) -> Any:
        """Get the racer verification service instance."""
        from plugins.builtin.racer_verification.services import (
            RacerVerificationService,
        )

        return RacerVerificationService()
