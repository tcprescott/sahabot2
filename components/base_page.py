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
                    if self.user:
                        # User is logged in - show username and menu
                        ui.label(self.user.discord_username).classes('header-username')

                        with ui.button(icon='menu').props('flat round').classes('header-menu-button'):
                            with ui.menu():
                                # Dark mode toggle
                                ui.menu_item(
                                    'Toggle Dark Mode',
                                    on_click=lambda: ui.run_javascript('document.body.classList.toggle("body--dark")')
                                ).props('icon=dark_mode')

                                ui.separator()

                                # Admin panel (only if user is admin)
                                if self.user.is_admin():
                                    ui.menu_item(
                                        'Admin Panel',
                                        on_click=lambda: ui.navigate.to('/admin')
                                    ).props('icon=admin_panel_settings')

                                # Logout
                                ui.menu_item(
                                    'Logout',
                                    on_click=self._handle_logout
                                ).props('icon=logout')
                    else:
                        # User not logged in - show login button
                        with ui.button(icon='menu').props('flat round').classes('header-menu-button'):
                            with ui.menu():
                                # Dark mode toggle
                                ui.menu_item(
                                    'Toggle Dark Mode',
                                    on_click=lambda: ui.run_javascript('document.body.classList.toggle("body--dark")')
                                ).props('icon=dark_mode')

                                ui.separator()

                                # Login
                                ui.menu_item(
                                    'Login with Discord',
                                    on_click=lambda: ui.navigate.to('/auth/login')
                                ).props('icon=login')

    async def _handle_logout(self) -> None:
        """Handle user logout."""
        await DiscordAuthService.clear_current_user()
        ui.notify('Logged out successfully', type='positive')
        ui.navigate.to('/')

    def _render_sidebar(self, items: Optional[list] = None) -> None:
        """
        Render the sidebar flyout.

        Args:
            items: List of sidebar items with 'label', 'icon', and 'action' callback
        """
        if items is None:
            items = []

        # Backdrop for mobile
        self._backdrop = ui.element('div').classes('sidebar-backdrop')
        self._backdrop.on('click', self._toggle_sidebar)

        # Sidebar container
        initial_class = 'sidebar-closed'
        self._sidebar_container = ui.element('div').classes(f'sidebar-flyout {initial_class}')

        with self._sidebar_container:
            # Sidebar header
            with ui.element('div').classes('sidebar-header'):
                ui.label('Navigation').classes('sidebar-title')
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

    async def render(
        self,
        content: Optional[Callable[[BasePage], Awaitable[None]]] = None,
        sidebar_items: Optional[list] = None
    ) -> None:
        """
        Render the page with header, sidebar, and optional content.

        Args:
            content: Async function to render page content, receives this BasePage instance
            sidebar_items: Optional list of sidebar items with 'label', 'icon', and 'action'
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
            sidebar_items: Optional[list] = None
        ) -> None:
            # Check authentication before rendering
            user = await DiscordAuthService.require_auth()
            if not user:
                return  # User was redirected to login
            await original_render(content, sidebar_items)

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
            sidebar_items: Optional[list] = None
        ) -> None:
            # Check admin permission before rendering
            user = await DiscordAuthService.require_permission(Permission.ADMIN, '/admin')
            if not user:
                return  # User was redirected
            await original_render(content, sidebar_items)

        page.render = admin_render  # type: ignore
        return page
