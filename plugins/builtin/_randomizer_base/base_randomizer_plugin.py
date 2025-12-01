"""
Base class for randomizer plugins.

This module provides an abstract base class that all randomizer plugins
should inherit from to ensure consistent behavior and interface.
"""

import logging
from abc import abstractmethod
from typing import Any, Dict, List

from application.plugins.base.plugin import BasePlugin
from application.plugins.manifest import (
    PluginConfig,
    PluginCategory,
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
