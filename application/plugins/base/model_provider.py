"""
Model provider interface.

This module defines the interface for plugins that contribute database models.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Type


class ModelProvider(ABC):
    """Interface for plugins that provide database models."""

    @abstractmethod
    def get_models(self) -> List[Type]:
        """
        Return list of Tortoise ORM models.

        Returns:
            List of Model classes
        """
        pass

    def get_model_module(self) -> str:
        """
        Return the module path for models.

        Used by Tortoise ORM for model discovery.
        Override if models are in a non-standard location.

        Returns:
            Module path string (e.g., "plugins.builtin.tournament.models")
        """
        return f"plugins.builtin.{self.plugin_id}.models"

    def get_migrations_path(self) -> Optional[str]:
        """
        Return the filesystem path to migrations.

        Returns:
            Path string or None if no migrations
        """
        return None
