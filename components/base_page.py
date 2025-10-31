"""
Base page component for consistent layout across the application.

This module provides the BasePage class which serves as the template for all pages,
including a header with branding, user info, and navigation menu.
"""

from __future__ import annotations
from typing import Optional, Callable, Awaitable, Any
import inspect
from nicegui import ui
from middleware.auth import DiscordAuthService
from models import User, Permission
from components.header import Header
from components.footer import Footer
from components.sidebar import Sidebar


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
                    self._backdrop.classes(remove='hidden', add='active')
            else:
                self._sidebar_container.classes(remove='sidebar-open', add='sidebar-closed')
                if self._backdrop:
                    self._backdrop.classes(remove='active', add='hidden')

    def _render_header(self) -> None:
        """Render the header using the Header component."""
        header = Header(self.user, self._toggle_sidebar)
        header.render()

    def _render_sidebar(self, items: Optional[list] = None) -> None:
        """
        Render the sidebar flyout.

        Args:
            items: List of sidebar items with 'label', 'icon', and 'action' callback
        """
        if items is None:
            items = []

        # Backdrop for mobile (hidden on desktop via CSS) - start hidden by default
        self._backdrop = ui.element('div').classes('sidebar-backdrop hidden')
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
        Render a single sidebar item or separator.

        Args:
            item: Dictionary with 'label', 'icon', 'action', or 'type' keys
        """
        # Separator line support
        if item.get('type') == 'separator':
            ui.element('div').classes('sidebar-separator')
            return

        # Handle subsection groups
        children = item.get('children') if isinstance(item, dict) else None
        if children and isinstance(children, list):
            exp = ui.expansion(text=item.get('label', ''), icon=item.get('icon', None)).classes('sidebar-section')
            with exp:
                for child in children:
                    self._render_sidebar_item(child)
            return

        # Leaf navigation item
        def handle_click():
            if 'action' in item and callable(item['action']):
                item['action']()
            self._toggle_sidebar()  # Close sidebar after clicking item

        with ui.element('div').classes('sidebar-item').on('click', handle_click):
            if 'icon' in item and item['icon']:
                ui.icon(item['icon']).classes('sidebar-item-icon')
            ui.label(item.get('label', '')).classes('sidebar-item-label')

    def create_sidebar_section(self, label: str, icon: Optional[str], children: list[dict]) -> dict:
        """Create a collapsible sidebar section with child items.

        Args:
            label: Section title
            icon: Optional icon name for the section header
            children: List of sidebar item dicts (label, icon, action) to render inside the section

        Returns:
            Sidebar section dictionary compatible with _render_sidebar_item
        """
        return {
            'label': label,
            'icon': icon,
            'children': children,
        }

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

    def create_nav_link(self, label: str, icon: str, to: str) -> dict:
        """Create a sidebar item that navigates to a route.

        Args:
            label: Display label for the link
            icon: Material icon name
            to: Target route/path to navigate to

        Returns:
            Sidebar item dictionary that, when clicked, navigates to the given route
        """
        def action() -> None:
            ui.navigate.to(to)

        return {'label': label, 'icon': icon, 'action': action}

    def create_separator(self) -> dict:
        """Create a visual separator item for the sidebar.

        Returns:
            Sidebar separator item dictionary
        """
        return {'type': 'separator'}

    def create_view_loader(self, view_class: Any) -> Callable[[], Awaitable[None]]:
        """Create a loader that renders a view class into the page content container.

        This expects the provided view class to expose an async `render(user)` method.

        Args:
            view_class: A view class with an async static/class method `render(user)`

        Returns:
            An async no-arg callable that clears the current content area and renders the view.
        """
        async def loader() -> None:
            # Prefer the dynamic content container when present; fall back to the main content container
            container = self.get_dynamic_content_container() or self._content_container
            if container is None:
                # Fallback: create a standard page container to host the content
                self._content_container = ui.element('div').classes('page-container')
                container = self._content_container

            container.clear()
            with container:
                # Delegate actual rendering to the view class
                await view_class.render(self.user)

        return loader

    def create_instance_view_loader(self, factory: Callable[[], Any], method: str = "render") -> Callable[[], Awaitable[None]]:
        """Create a loader that instantiates a view and invokes its render method.

        This is intended for views that require construction (e.g., need `self` or
        constructor arguments) instead of a static/class `render(user)` method.

        Args:
            factory: Zero-argument callable that returns a view instance.
            method: Name of the render method to invoke on the instance. Defaults to "render".

        Returns:
            An async no-arg callable that clears the current content area and renders the instance view.
        """
        async def loader() -> None:
            container = self.get_dynamic_content_container() or self._content_container
            if container is None:
                # Initialize a default content container if not present
                self._content_container = ui.element('div').classes('page-container')
                container = self._content_container

            container.clear()
            with container:
                instance = factory()
                render_fn = getattr(instance, method, None)
                if render_fn is None:
                    return
                result = render_fn()
                if inspect.iscoroutine(result):
                    await result

        return loader
    
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
        
        # Render sidebar via component
        sidebar_component = Sidebar(self._toggle_sidebar)
        self._sidebar_container, self._backdrop = sidebar_component.render(sidebar_items or [])

        # Render content if provided
        if content:
            if use_dynamic_content:
                # Create a dynamic content container that can be cleared/reloaded
                self._content_container = ui.element('div').classes('page-container')
                with self._content_container:
                    self._dynamic_content_container = ui.column().classes('full-width')
                    with self._dynamic_content_container:
                        await content(self)
                    # Footer at the bottom of the page container
                    Footer.render()
            else:
                # Standard static content
                self._content_container = ui.element('div').classes('page-container')
                with self._content_container:
                    await content(self)
                    # Footer at the bottom of the page container
                    Footer.render()

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
