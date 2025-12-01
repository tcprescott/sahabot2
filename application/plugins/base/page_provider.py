"""
Page provider interface.

This module defines the interface for plugins that contribute UI pages.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional
from dataclasses import dataclass


@dataclass
class PageRegistration:
    """Page registration definition."""

    path: str
    handler: Callable
    title: str
    requires_auth: bool = True
    requires_org: bool = True
    active_nav: Optional[str] = None
    permission: Optional[str] = None


class PageProvider(ABC):
    """Interface for plugins that provide UI pages."""

    @abstractmethod
    def get_pages(self) -> List[PageRegistration]:
        """
        Return page registration definitions.

        Returns:
            List of PageRegistration instances
        """
        pass

    def register_pages(self) -> None:
        """
        Register pages with NiceGUI.

        Called by PluginRegistry during page registration.
        Default implementation uses get_pages().
        """
        # Import here to avoid circular imports
        from nicegui import ui

        for page in self.get_pages():

            @ui.page(page.path)
            async def page_handler(p: PageRegistration = page) -> Any:
                """Wrapper for plugin page handler."""
                return await p.handler()
