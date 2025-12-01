"""
Base class for randomizer plugins.

This module provides an abstract base class that all randomizer plugins
should inherit from to ensure consistent behavior and interface.
"""

import logging
from abc import abstractmethod
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
)

logger = logging.getLogger(__name__)


class BaseRandomizerPlugin(BasePlugin):
    """
    Abstract base class for randomizer plugins.

    Provides common functionality and interface for all randomizer plugins.
    Each randomizer plugin should inherit from this class and implement
    the abstract methods.
    """

    @property
    @abstractmethod
    def randomizer_name(self) -> str:
        """
        Return the display name of the randomizer.

        Examples: "A Link to the Past Randomizer", "Super Metroid Randomizer"
        """
        pass

    @property
    @abstractmethod
    def randomizer_short_name(self) -> str:
        """
        Return the short/slug name of the randomizer.

        Examples: "alttpr", "sm", "smz3", "ootr"
        """
        pass

    @property
    def category(self) -> PluginCategory:
        """Return the plugin category (always RANDOMIZER)."""
        return PluginCategory.RANDOMIZER

    def _create_manifest(
        self,
        plugin_id: str,
        name: str,
        version: str,
        description: str,
        has_racetime_handler: bool = False,
        has_discord_commands: bool = True,
        additional_services: Optional[List[str]] = None,
        additional_events: Optional[List[str]] = None,
    ) -> PluginManifest:
        """
        Helper method to create a standardized manifest for randomizer plugins.

        Args:
            plugin_id: Unique plugin identifier
            name: Display name of the plugin
            version: Version string
            description: Plugin description
            has_racetime_handler: Whether plugin provides RaceTime.gg handler
            has_discord_commands: Whether plugin provides Discord commands
            additional_services: Additional service names provided
            additional_events: Additional event types provided

        Returns:
            PluginManifest with standard randomizer configuration
        """
        services = [f"{name.replace(' ', '')}Service"]
        if additional_services:
            services.extend(additional_services)

        events = []
        if additional_events:
            events.extend(additional_events)

        return PluginManifest(
            id=plugin_id,
            name=name,
            version=version,
            description=description,
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
                services=services,
                events=events,
            ),
        )

    def get_service(self) -> Any:
        """
        Get the randomizer service instance.

        Returns:
            The randomizer service instance for seed generation
        """
        raise NotImplementedError("Subclasses must implement get_service()")

    async def on_load(self) -> None:
        """Called when the plugin is loaded at startup."""
        logger.info("%s plugin loaded", self.randomizer_name)

    async def on_enable(self, organization_id: int, config: PluginConfig) -> None:
        """Called when the plugin is enabled for an organization."""
        logger.info(
            "%s plugin enabled for organization %s",
            self.randomizer_name,
            organization_id,
        )

    async def on_disable(self, organization_id: int) -> None:
        """Called when the plugin is disabled for an organization."""
        logger.info(
            "%s plugin disabled for organization %s",
            self.randomizer_name,
            organization_id,
        )

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded at shutdown."""
        logger.info("%s plugin unloaded", self.randomizer_name)

    def get_authorization_actions(self) -> List[str]:
        """Return authorization actions for this randomizer plugin."""
        return [
            f"{self.randomizer_short_name}:generate",
            f"{self.randomizer_short_name}:preset:read",
        ]

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """Return navigation menu items (none by default for randomizers)."""
        return []
