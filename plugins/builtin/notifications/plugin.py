"""
Notifications Plugin implementation.

This module contains the NotificationsPlugin class that integrates
notification functionality into the SahaBot2 plugin system.
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


class NotificationsPlugin(BasePlugin):
    """
    Notification System Plugin.

    Provides user notification subscriptions and multi-channel delivery
    for event notifications.

    This plugin re-exports models and services from the core application
    to provide a unified interface for notification functionality.
    """

    @property
    def plugin_id(self) -> str:
        """Return the unique plugin identifier."""
        return "notifications"

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            id="notifications",
            name="Notification System",
            version="1.0.0",
            description="User notification subscriptions and multi-channel delivery",
            author="SahaBot2 Team",
            type=PluginType.BUILTIN,
            category=PluginCategory.UTILITY,
            enabled_by_default=True,
            private=False,
            global_plugin=False,
            provides=PluginProvides(
                models=["NotificationSubscription", "NotificationLog"],
                services=["NotificationService", "NotificationProcessor"],
                api_routes=[
                    APIRouteDefinition(
                        prefix="/api/user/notifications",
                        scope=RouteScope.GLOBAL,
                        tags=["notifications"],
                    ),
                ],
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "retry_failed_notifications": {
                        "type": "boolean",
                        "default": True,
                        "description": "Automatically retry failed notifications",
                    },
                    "max_retry_attempts": {
                        "type": "integer",
                        "default": 3,
                        "description": "Maximum retry attempts for failed notifications",
                    },
                    "retry_delay_seconds": {
                        "type": "integer",
                        "default": 60,
                        "description": "Delay between retry attempts",
                    },
                },
            },
        )

    # ─────────────────────────────────────────────────────────────
    # Lifecycle Hooks
    # ─────────────────────────────────────────────────────────────

    async def on_load(self) -> None:
        """Called when the plugin is loaded at startup."""
        logger.info("Notifications plugin loaded")

    async def on_enable(self, organization_id: int, config: PluginConfig) -> None:
        """Called when the plugin is enabled for an organization."""
        logger.info(
            "Notifications plugin enabled for organization %s with config: %s",
            organization_id,
            config.settings,
        )

    async def on_disable(self, organization_id: int) -> None:
        """Called when the plugin is disabled for an organization."""
        logger.info("Notifications plugin disabled for organization %s", organization_id)

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded at shutdown."""
        logger.info("Notifications plugin unloaded")

    # ─────────────────────────────────────────────────────────────
    # Contribution Methods
    # ─────────────────────────────────────────────────────────────

    def get_models(self) -> List[Type]:
        """Return database models contributed by this plugin."""
        from plugins.builtin.notifications.models import (
            NotificationSubscription,
            NotificationLog,
        )

        return [NotificationSubscription, NotificationLog]

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
                "path": "/user/notifications",
                "title": "Notification Settings",
                "requires_auth": True,
                "requires_org": False,
                "active_nav": "notifications",
            },
        ]

    def get_event_types(self) -> List[Type]:
        """Return event types defined by this plugin."""
        from plugins.builtin.notifications.events.types import (
            NotificationSentEvent,
            NotificationFailedEvent,
            SubscriptionCreatedEvent,
            SubscriptionUpdatedEvent,
        )

        return [
            NotificationSentEvent,
            NotificationFailedEvent,
            SubscriptionCreatedEvent,
            SubscriptionUpdatedEvent,
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
            "notification:subscribe",
            "notification:unsubscribe",
            "notification:read_history",
            "notification:admin",
        ]

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """Return navigation menu items to add."""
        return [
            {
                "label": "Notifications",
                "path": "/user/notifications",
                "icon": "notifications",
                "position": "user_menu",
                "order": 10,
                "requires_permission": None,  # All authenticated users
            },
        ]

    # ─────────────────────────────────────────────────────────────
    # Service Accessors
    # ─────────────────────────────────────────────────────────────

    def get_notification_service(self) -> Any:
        """Get the notification service instance."""
        from plugins.builtin.notifications.services import NotificationService

        return NotificationService()

    def get_notification_processor(self) -> Any:
        """Get the notification processor instance."""
        from plugins.builtin.notifications.services import NotificationProcessor

        return NotificationProcessor()
