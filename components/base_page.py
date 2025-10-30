"""
Base page component for consistent layout across the application.

This module provides the BasePage class which serves as the template for all pages,
including a header with branding, user info, and navigation menu.
"""

from __future__ import annotations
from typing import Optional, Callable, Awaitable
from nicegui import ui
from middleware.auth import DiscordAuthService
from models import User, Permission
from components.user_menu import UserMenu


class BasePage:
    """
    Base page component providing consistent header and layout.

    Attributes:
        title: Page title for browser tab
        user: Current authenticated user (if any)
        sidebar_open: Whether sidebar is currently open
    """

    def __init__(self, title: str = "SahaBot2"):
        """
        Initialize base page.

        Args:
            title: Page title for browser tab
        """
        self.title = title
        self.user: Optional[User] = None
        self.sidebar_open: bool = False
        self._sidebar_container = None
        self._backdrop = None
        self._content_container = None
        self._dynamic_content_container = None
        self._content_loaders: dict[str, Callable[[], Awaitable[None]]] = {}

    async def _load_user(self) -> None:
        """Load current user from session."""
        self.user = await DiscordAuthService.get_current_user()

    def _toggle_sidebar(self) -> None:
        """Toggle sidebar open/closed state."""
        self.sidebar_open = not self.sidebar_open
        if self._sidebar_container:
            if self.sidebar_open:
                self._sidebar_container.classes(remove='sidebar-closed', add='sidebar-open')
                if self._backdrop:
                    self._backdrop.classes(add='active')
            else:
                self._sidebar_container.classes(remove='sidebar-open', add='sidebar-closed')
                if self._backdrop:
                    self._backdrop.classes(remove='active')

    def _render_header(self) -> None:
        """Render the header bar with logo, app name, and user menu."""
        with ui.header().classes('header-bar'):
            with ui.row().classes('header-container'):
                # Left side: Hamburger menu, logo and app name
                with ui.row().classes('header-left gap-md'):
                    # Hamburger menu button for sidebar
                    ui.button(icon='menu', on_click=self._toggle_sidebar).props('flat round').classes('header-hamburger')
                    # Placeholder for logo (you can add an image here)
                    ui.icon('smart_toy', size='lg').classes('header-logo')
                    ui.label('SahaBot2').classes('header-brand')

                # Right side: User info and menu
                with ui.row().classes('header-right gap-md'):
                    user_menu = UserMenu(self.user)
                    user_menu.render()

    def _render_sidebar(self, items: Optional[list] = None) -> None:
        """
        Render the sidebar flyout.

        Args:
            items: List of sidebar items with 'label', 'icon', and 'action' callback
        """
        if items is None:
            items = []

        # Backdrop for mobile (hidden on desktop via CSS)
        self._backdrop = ui.element('div').classes('sidebar-backdrop')
        self._backdrop.on('click', self._toggle_sidebar)

        # Sidebar container - starts closed on mobile, but CSS overrides on desktop
        self._sidebar_container = ui.element('div').classes('sidebar-flyout sidebar-closed')

        with self._sidebar_container:
            # Sidebar header
            with ui.element('div').classes('sidebar-header'):
                ui.label('Navigation').classes('sidebar-title')
                # Close button (hidden on desktop via CSS)
                ui.button(icon='close', on_click=self._toggle_sidebar).props('flat round dense').classes('sidebar-close-btn')

            # Sidebar items
            with ui.element('div').classes('sidebar-items'):
                for item in items:
                    self._render_sidebar_item(item)

    def _render_sidebar_item(self, item: dict) -> None:
        """
        Render a single sidebar item.

        Args:
            item: Dictionary with 'label', 'icon', and 'action' keys
        """
        def handle_click():
            if 'action' in item and callable(item['action']):
                item['action']()
            self._toggle_sidebar()  # Close sidebar after clicking item

        with ui.element('div').classes('sidebar-item').on('click', handle_click):
            if 'icon' in item:
                ui.icon(item['icon']).classes('sidebar-item-icon')
            ui.label(item['label']).classes('sidebar-item-label')

    def get_dynamic_content_container(self):
        """
        Get the dynamic content container for content switching.
        
        Returns:
            The dynamic content container element
        """
        return self._dynamic_content_container
    
    def register_content_loader(self, key: str, loader: Callable[[], Awaitable[None]]) -> None:
        """
        Register a content loader function for dynamic content switching.
        
        Args:
            key: Unique identifier for this content loader
            loader: Async function that loads content into the dynamic container
        """
        self._content_loaders[key] = loader
    
    def create_sidebar_item_with_loader(self, label: str, icon: str, loader_key: str) -> dict:
        """
        Create a sidebar item that loads dynamic content.
        
        Args:
            label: Display label for the sidebar item
            icon: Material icon name
            loader_key: Key for the registered content loader
            
        Returns:
            Sidebar item dictionary
        """
        def action():
            if loader_key in self._content_loaders:
                ui.timer(0, self._content_loaders[loader_key], once=True)
        
        return {'label': label, 'icon': icon, 'action': action}
    
    async def render(
        self,
        content: Optional[Callable[[BasePage], Awaitable[None]]] = None,
        sidebar_items: Optional[list] = None,
        use_dynamic_content: bool = False
    ) -> None:
        """
        Render the page with header, sidebar, and optional content.

        Args:
            content: Async function to render page content, receives this BasePage instance
            sidebar_items: Optional list of sidebar items with 'label', 'icon', and 'action'
            use_dynamic_content: If True, creates a dynamic content container for content switching
        """
        # Load CSS
        ui.add_head_html('<link rel="stylesheet" href="/static/css/main.css">')

        # Set page title
        ui.page_title(self.title)

        # Load current user
        await self._load_user()

        # Render header
        self._render_header()

        # Render sidebar
        self._render_sidebar(sidebar_items)

        # Render content if provided
        if content:
            if use_dynamic_content:
                # Create a dynamic content container that can be cleared/reloaded
                self._content_container = ui.element('div').classes('page-container')
                with self._content_container:
                    self._dynamic_content_container = ui.column().classes('full-width')
                    with self._dynamic_content_container:
                        await content(self)
            else:
                # Standard static content
                self._content_container = ui.element('div').classes('page-container')
                with self._content_container:
                    await content(self)

    @staticmethod
    def simple_page(title: str = "SahaBot2") -> 'BasePage':
        """
        Create a simple page (no authentication required).

        Args:
            title: Page title

        Returns:
            BasePage: Configured page instance
        """
        return BasePage(title=title)

    @staticmethod
    def authenticated_page(title: str = "SahaBot2") -> 'BasePage':
        """
        Create an authenticated page (requires login).

        Args:
            title: Page title

        Returns:
            BasePage: Configured page instance that requires authentication
        """
        page = BasePage(title=title)

        # Override render to enforce authentication
        original_render = page.render

        async def authenticated_render(
            content: Optional[Callable[[BasePage], Awaitable[None]]] = None,
            sidebar_items: Optional[list] = None,
            use_dynamic_content: bool = False
        ) -> None:
            # Check authentication before rendering
            user = await DiscordAuthService.require_auth()
            if not user:
                return  # User was redirected to login
            await original_render(content, sidebar_items, use_dynamic_content)

        page.render = authenticated_render  # type: ignore
        return page

    @staticmethod
    def admin_page(title: str = "Admin - SahaBot2") -> 'BasePage':
        """
        Create an admin page (requires admin permission).

        Args:
            title: Page title

        Returns:
            BasePage: Configured page instance that requires admin permission
        """
        page = BasePage(title=title)

        # Override render to enforce admin permission
        original_render = page.render

        async def admin_render(
            content: Optional[Callable[[BasePage], Awaitable[None]]] = None,
            sidebar_items: Optional[list] = None,
            use_dynamic_content: bool = False
        ) -> None:
            # Check admin permission before rendering
            user = await DiscordAuthService.require_permission(Permission.ADMIN, '/admin')
            if not user:
                return  # User was redirected
            await original_render(content, sidebar_items, use_dynamic_content)

        page.render = admin_render  # type: ignore
        return page
