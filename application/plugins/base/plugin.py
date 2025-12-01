"""
Base plugin abstract class.

This module defines the BasePlugin abstract class that all plugins must implement.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from application.plugins.manifest import PluginManifest, PluginConfig

logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """
    Abstract base class for all plugins.

    Plugins must implement the abstract methods to contribute
    functionality to SahaBot2.
    """

    # ─────────────────────────────────────────────────────────────
    # Required Properties
    # ─────────────────────────────────────────────────────────────

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """
        Return the unique plugin identifier.

        Convention: lowercase, alphanumeric with underscores.
        Examples: "tournament", "async_qualifier", "smz3_support"
        """
        pass

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest:
        """
        Return the plugin manifest.

        The manifest contains metadata about the plugin including
        its ID, version, dependencies, and contributions.
        """
        pass

    # ─────────────────────────────────────────────────────────────
    # Lifecycle Methods
    # ─────────────────────────────────────────────────────────────

    async def on_load(self) -> None:
        """
        Called when the plugin is loaded into memory.

        Use this for one-time initialization that doesn't require
        database access or organization context.
        """
        pass

    async def on_enable(self, organization_id: int, config: PluginConfig) -> None:
        """
        Called when the plugin is enabled for an organization.

        Args:
            organization_id: The organization enabling the plugin
            config: Organization-specific configuration

        Use this to initialize organization-specific resources.
        """
        pass

    async def on_disable(self, organization_id: int) -> None:
        """
        Called when the plugin is disabled for an organization.

        Args:
            organization_id: The organization disabling the plugin

        Use this to clean up organization-specific resources.
        """
        pass

    async def on_unload(self) -> None:
        """
        Called when the plugin is being unloaded.

        Use this for cleanup before the plugin is removed from memory.
        """
        pass

    async def on_install(self) -> None:
        """
        Called when the plugin is first installed.

        Use this for one-time setup like database migrations.
        Only called for external plugins.
        """
        pass

    async def on_uninstall(self) -> None:
        """
        Called when the plugin is being uninstalled.

        Use this for cleanup like removing database tables.
        Only called for external plugins.
        """
        pass

    async def on_upgrade(self, old_version: str, new_version: str) -> None:
        """
        Called when the plugin is upgraded.

        Args:
            old_version: Previous version string
            new_version: New version string

        Use this for migration logic between versions.
        """
        pass

    # ─────────────────────────────────────────────────────────────
    # Contribution Methods (Default implementations)
    # ─────────────────────────────────────────────────────────────

    def get_models(self) -> List[Type]:
        """
        Return Tortoise ORM models contributed by this plugin.

        Returns:
            List of Model classes to register with Tortoise ORM
        """
        return []

    def get_api_router(self) -> Optional[Any]:
        """
        Return FastAPI router for API endpoints.

        Returns:
            APIRouter with plugin endpoints, or None
        """
        return None

    def get_pages(self) -> List[Dict[str, Any]]:
        """
        Return page registration definitions.

        Returns:
            List of dicts with keys:
            - path: URL path pattern
            - handler: Async function to render the page
            - title: Page title
            - requires_auth: Whether auth is required
            - requires_org: Whether org context is required
        """
        return []

    def get_discord_cog(self) -> Optional[Type]:
        """
        Return Discord cog class for bot commands.

        Returns:
            Cog class to load, or None
        """
        return None

    def get_event_types(self) -> List[Type]:
        """
        Return event types defined by this plugin.

        Returns:
            List of BaseEvent subclasses
        """
        return []

    def get_event_listeners(self) -> List[Dict[str, Any]]:
        """
        Return event listeners to register.

        Returns:
            List of dicts with keys:
            - event_type: The event class to listen for
            - handler: Async function to handle the event
            - priority: EventPriority enum value
        """
        return []

    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        Return scheduled tasks to register.

        Returns:
            List of dicts with keys:
            - task_id: Unique task identifier
            - name: Display name
            - handler: Async function to execute
            - schedule_type: ScheduleType enum
            - interval_seconds: For INTERVAL type
            - cron_expression: For CRON type
            - is_active: Default active state
        """
        return []

    def get_authorization_actions(self) -> List[str]:
        """
        Return authorization actions defined by this plugin.

        Returns:
            List of action strings like "tournament:create"
        """
        return []

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """
        Return navigation menu items to add.

        Returns:
            List of dicts with keys:
            - label: Menu item text
            - path: URL path
            - icon: Icon name
            - position: Menu position (e.g., "sidebar", "admin")
            - order: Sort order
            - requires_permission: Permission action required
        """
        return []

    # ─────────────────────────────────────────────────────────────
    # Context Methods
    # ─────────────────────────────────────────────────────────────

    def is_enabled_for_org(self, organization_id: int) -> bool:
        """
        Check if plugin is enabled for an organization.

        Args:
            organization_id: Organization to check

        Returns:
            True if enabled, False otherwise

        Note: This is typically called by the PluginRegistry, not
        directly by the plugin implementation.
        """
        # Import here to avoid circular imports
        from application.plugins.registry import PluginRegistry

        return PluginRegistry.is_enabled(self.plugin_id, organization_id)

    def get_config(self, organization_id: int) -> PluginConfig:
        """
        Get configuration for an organization.

        Args:
            organization_id: Organization to get config for

        Returns:
            PluginConfig with merged settings
        """
        # Import here to avoid circular imports
        from application.plugins.registry import PluginRegistry

        return PluginRegistry.get_config(self.plugin_id, organization_id)

    def __repr__(self) -> str:
        """Return string representation of the plugin."""
        return f"<{self.__class__.__name__}(id={self.plugin_id}, version={self.manifest.version})>"
