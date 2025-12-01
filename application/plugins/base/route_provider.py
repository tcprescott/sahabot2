"""
Route provider interface.

This module defines the interface for plugins that contribute API routes.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from application.plugins.manifest import RouteScope


class PageRoute(BaseModel):
    """Page route definition."""

    path: str
    name: str
    scope: RouteScope = RouteScope.ORGANIZATION
    requires_auth: bool = True
    reason: Optional[str] = None

    def validate_root_scope(self) -> None:
        """Ensure root-scoped routes have a reason."""
        if self.scope == RouteScope.ROOT and not self.reason:
            raise ValueError("Root-scoped routes must provide a 'reason' field")


class APIRoute(BaseModel):
    """API route definition."""

    prefix: str
    scope: RouteScope = RouteScope.ORGANIZATION
    tags: List[str] = Field(default_factory=list)
    reason: Optional[str] = None

    def validate_root_scope(self) -> None:
        """Ensure root-scoped routes have a reason."""
        if self.scope == RouteScope.ROOT and not self.reason:
            raise ValueError("Root-scoped routes must provide a 'reason' field")


class RouteProvider(ABC):
    """Interface for plugins that provide routes."""

    @abstractmethod
    def get_page_routes(self) -> List[PageRoute]:
        """
        Return list of page routes this plugin provides.

        Returns:
            List of PageRoute instances
        """
        pass

    @abstractmethod
    def get_api_routes(self) -> List[APIRoute]:
        """
        Return list of API routes this plugin provides.

        Returns:
            List of APIRoute instances
        """
        pass

    def get_api_router(self) -> Optional[Any]:
        """
        Return FastAPI router with endpoints.

        The router will be mounted at /api/plugins/{plugin_id}/

        Returns:
            APIRouter instance or None
        """
        return None

    def get_route_prefix(self) -> str:
        """
        Return the route prefix for this plugin.

        Override to customize the mount point.

        Returns:
            Route prefix string (default: plugin_id)
        """
        return getattr(self, "plugin_id", "")

    def get_route_tags(self) -> List[str]:
        """
        Return OpenAPI tags for routes.

        Returns:
            List of tag strings
        """
        plugin_id = getattr(self, "plugin_id", "unknown")
        return [plugin_id]

    def get_route_dependencies(self) -> List[Any]:
        """
        Return dependencies to apply to all routes.

        Returns:
            List of FastAPI Depends instances
        """
        return []
