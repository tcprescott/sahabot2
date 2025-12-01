"""
Command provider interface.

This module defines the interface for plugins that contribute Discord commands.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Type


class CommandProvider(ABC):
    """Interface for plugins that provide Discord commands."""

    @abstractmethod
    def get_discord_cog(self) -> Optional[Type]:
        """
        Return Discord cog class.

        Returns:
            Cog class to load, or None
        """
        pass

    def get_extension_name(self) -> str:
        """
        Return the extension module name for load_extension().

        Returns:
            Module path string
        """
        plugin_id = getattr(self, "plugin_id", "unknown")
        return f"plugins.builtin.{plugin_id}.commands"

    def get_required_intents(self) -> List[str]:
        """
        Return Discord intents required by this plugin.

        Returns:
            List of intent names (e.g., ["guilds", "members"])
        """
        return []
