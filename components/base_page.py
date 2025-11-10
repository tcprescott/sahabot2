"""
Base page component for consistent layout across the application.

This module provides the BasePage class which serves as the template for all pages,
including a header with branding, user info, and navigation menu.
"""

from __future__ import annotations
from typing import Optional, Callable, Awaitable, Any
import inspect
import hashlib
from pathlib import Path
from nicegui import ui
from middleware.auth import DiscordAuthService
from models import User, Permission
from components.header import Header
from components.footer import Footer
from components.sidebar import Sidebar
from components.motd_banner import MOTDBanner


def get_css_version() -> str:
    """
    Get CSS cache-busting version based on main.css content hash.

    Returns:
        Version string (MD5 hash of main.css content, first 8 chars)
    """
    try:
        css_file = Path(__file__).parent.parent / "static" / "css" / "main.css"
        if not css_file.exists():
            return "1"

        # Calculate MD5 hash of file content
        content = css_file.read_bytes()
        hash_digest = hashlib.md5(content).hexdigest()

        # Return first 8 characters of hash (sufficient for cache busting)
        return hash_digest[:8]
    except Exception:
        # Fallback to static version if anything goes wrong
        return "1"


def get_js_version(filename: str) -> str:
    """
    Get JavaScript cache-busting version based on file content hash.

    Args:
        filename: Relative path to JS file from static/js/ directory

    Returns:
        Version string (MD5 hash of file content, first 8 chars)
    """
    try:
        js_file = Path(__file__).parent.parent / "static" / "js" / filename
        if not js_file.exists():
            return "1"

        # Calculate MD5 hash of file content
        content = js_file.read_bytes()
        hash_digest = hashlib.md5(content).hexdigest()

        # Return first 8 characters of hash (sufficient for cache busting)
        return hash_digest[:8]
    except Exception:
        # Fallback to static version if anything goes wrong
        return "1"


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
        self._current_view_key: Optional[str] = None
        self.initial_view: Optional[str] = None  # View from query parameter

    async def _load_user(self) -> None:
        """Load current user from session."""
        self.user = await DiscordAuthService.get_current_user()

    def _load_sentry_browser(self) -> None:
        """
        Load Sentry browser monitoring script with configuration.

        This loads the Sentry browser SDK to capture frontend JavaScript errors,
        unhandled promise rejections, and client-side performance data.
        Only loads if SENTRY_DSN is configured in settings.
        """
        from config import settings

        # Only load if DSN is configured
        if not settings.SENTRY_DSN:
            return

        # Get configuration
        environment = settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT
        traces_sample_rate = settings.SENTRY_TRACES_SAMPLE_RATE

        # Session replay is disabled by default (can be expensive)
        # Set to > 0 to enable session recording
        replays_session_sample_rate = 0.0
        replays_on_error_sample_rate = 0.0

        # Load Sentry browser initialization script with configuration
        # Note: DSN is intentionally embedded in HTML for browser SDK to function.
        # Sentry DSNs are public client-side credentials by design - they're safe
        # to expose in frontend code. Security is enforced via Sentry's rate limiting,
        # allowed origins/domains configuration, and project settings.
        js_version = get_js_version("monitoring/sentry-browser.js")
        sentry_script = f"""<script
            src="/static/js/monitoring/sentry-browser.js?v={js_version}"
            data-sentry-dsn="{settings.SENTRY_DSN}"
            data-sentry-environment="{environment}"
            data-traces-sample-rate="{traces_sample_rate}"
            data-replays-session-sample-rate="{replays_session_sample_rate}"
            data-replays-on-error-sample-rate="{replays_on_error_sample_rate}"
        ></script>"""
        ui.add_head_html(sentry_script)

    async def _show_query_param_notifications(self) -> None:
        """Display notifications based on query parameters (success, error, message)."""
        # Get query parameters from URL using URLManager
        params = await ui.run_javascript("return window.URLManager.getParams();")

        if not params:
            return

        # Show success notification
        if params.get("success"):
            message = params["success"].replace("_", " ").title()
            ui.notify(message, type="positive", timeout=5000)

        # Show error notification
        if params.get("error"):
            message = params["error"].replace("_", " ").title()
            ui.notify(message, type="negative", timeout=5000)

        # Show info message
        if params.get("message"):
            message = params["message"].replace("_", " ").title()
            ui.notify(message, type="info", timeout=5000)

    async def _get_view_from_query(self) -> Optional[str]:
        """
        Get the view parameter from URL query string.

        Returns:
            The view key from the query parameter if it exists, None otherwise
        """
        # Get 'view' query parameter from URL using URLManager
        view_value = await ui.run_javascript(
            "return window.URLManager.getParam('view');"
        )
        return view_value if view_value else None

    def _toggle_sidebar(self) -> None:
        """Toggle sidebar open/closed state."""
        self.sidebar_open = not self.sidebar_open
        if self._sidebar_container:
            if self.sidebar_open:
                self._sidebar_container.classes(
                    remove="sidebar-closed", add="sidebar-open"
                )
                if self._backdrop:
                    self._backdrop.classes(remove="hidden", add="active")
            else:
                self._sidebar_container.classes(
                    remove="sidebar-open", add="sidebar-closed"
                )
                if self._backdrop:
                    self._backdrop.classes(remove="active", add="hidden")

    def _render_header(self) -> None:
        """Render the header using the Header component."""
        header = Header(self.user, self._toggle_sidebar)
        header.render()

    async def _render_impersonation_banner(self) -> None:
        """Render an impersonation warning banner if currently impersonating."""
        if not DiscordAuthService.is_impersonating():
            return

        # Get original user
        original_user = await DiscordAuthService.get_original_user()
        if not original_user or not self.user:
            return

        # Create warning banner
        with ui.element("div").classes("w-full").style(
            "background-color: #ff9800; "
            "color: white; "
            "padding: 0.75rem 1rem; "
            "text-align: center; "
            "font-weight: 600; "
            "box-shadow: 0 2px 4px rgba(0,0,0,0.2);"
        ):
            with ui.row().classes("items-center justify-center gap-4"):
                ui.icon("warning").classes("text-2xl")
                ui.label(
                    f"IMPERSONATING: {self.user.discord_username} "
                    f"(Logged in as: {original_user.discord_username})"
                ).classes("text-base")

                # Stop impersonation button
                async def stop_impersonation():
                    from application.services.core.user_service import UserService

                    user_service = UserService()
                    await user_service.stop_impersonation(
                        original_user=original_user,
                        impersonated_user=self.user,
                        ip_address=None,
                    )
                    await DiscordAuthService.stop_impersonation()
                    ui.notify("Stopped impersonation", type="info")
                    ui.navigate.to("/")

                ui.button(
                    "Stop Impersonation", icon="close", on_click=stop_impersonation
                ).props("flat").style("color: white; border: 1px solid white;")

    async def _render_motd_banner(self) -> None:
        """Render the MOTD banner if there is an active message."""
        await MOTDBanner.render()

    def _render_sidebar(self, items: Optional[list] = None) -> None:
        """
        Render the sidebar flyout.

        Args:
            items: List of sidebar items with 'label', 'icon', and 'action' callback
        """
        if items is None:
            items = []

        # Backdrop for mobile (hidden on desktop via CSS) - start hidden by default
        self._backdrop = ui.element("div").classes("sidebar-backdrop hidden")
        self._backdrop.on("click", self._toggle_sidebar)

        # Sidebar container - starts closed on mobile, but CSS overrides on desktop
        self._sidebar_container = ui.element("div").classes(
            "sidebar-flyout sidebar-closed"
        )

        with self._sidebar_container:
            # Sidebar header
            with ui.element("div").classes("sidebar-header"):
                ui.label("Navigation").classes("sidebar-title")
                # Close button (hidden on desktop via CSS)
                ui.button(icon="close", on_click=self._toggle_sidebar).props(
                    "flat round dense"
                ).classes("sidebar-close-btn")

            # Sidebar items
            with ui.element("div").classes("sidebar-items"):
                for item in items:
                    self._render_sidebar_item(item)

    def _render_sidebar_item(self, item: dict) -> None:
        """
        Render a single sidebar item or separator.

        Args:
            item: Dictionary with 'label', 'icon', 'action', or 'type' keys
        """
        # Separator line support
        if item.get("type") == "separator":
            ui.element("div").classes("sidebar-separator")
            return

        # Handle subsection groups
        children = item.get("children") if isinstance(item, dict) else None
        if children and isinstance(children, list):
            exp = ui.expansion(
                text=item.get("label", ""), icon=item.get("icon", None)
            ).classes("sidebar-section")
            with exp:
                for child in children:
                    self._render_sidebar_item(child)
            return

        # Leaf navigation item
        def handle_click():
            if "action" in item and callable(item["action"]):
                item["action"]()
            self._toggle_sidebar()  # Close sidebar after clicking item

        with ui.element("div").classes("sidebar-item").on("click", handle_click):
            if "icon" in item and item["icon"]:
                ui.icon(item["icon"]).classes("sidebar-item-icon")
            ui.label(item.get("label", "")).classes("sidebar-item-label")

    def create_sidebar_section(
        self, label: str, icon: Optional[str], children: list[dict]
    ) -> dict:
        """Create a collapsible sidebar section with child items.

        Args:
            label: Section title
            icon: Optional icon name for the section header
            children: List of sidebar item dicts (label, icon, action) to render inside the section

        Returns:
            Sidebar section dictionary compatible with _render_sidebar_item
        """
        return {
            "label": label,
            "icon": icon,
            "children": children,
        }

    def get_dynamic_content_container(self):
        """
        Get the dynamic content container for content switching.

        Returns:
            The dynamic content container element
        """
        return self._dynamic_content_container

    def register_content_loader(
        self, key: str, loader: Callable[[], Awaitable[None]]
    ) -> None:
        """
        Register a content loader function for dynamic content switching.

        Args:
            key: Unique identifier for this content loader
            loader: Async function that loads content into the dynamic container
        """

        async def wrapped_loader():
            """Wrapped loader that updates the URL query parameter when loading content."""
            self._current_view_key = key
            # Update URL query parameter to reflect current view using URLManager
            ui.run_javascript(f"window.URLManager.setParam('view', '{key}');")
            await loader()

        self._content_loaders[key] = wrapped_loader

    def create_sidebar_item_with_loader(
        self, label: str, icon: str, loader_key: str
    ) -> dict:
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

        return {"label": label, "icon": icon, "action": action}

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

        return {"label": label, "icon": icon, "action": action}

    def create_separator(self) -> dict:
        """Create a visual separator item for the sidebar.

        Returns:
            Sidebar separator item dictionary
        """
        return {"type": "separator"}

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
                self._content_container = ui.element("div").classes("page-container")
                container = self._content_container

            container.clear()
            with container:
                # Delegate actual rendering to the view class
                await view_class.render(self.user)

        return loader

    def create_instance_view_loader(
        self, factory: Callable[[], Any], method: str = "render"
    ) -> Callable[[], Awaitable[None]]:
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
                self._content_container = ui.element("div").classes("page-container")
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

    async def load_view_into_container(self, view_instance: Any) -> None:
        """Load a view instance into the dynamic content container.

        This is a convenience method that encapsulates the common pattern of:
        1. Getting the dynamic content container
        2. Clearing it
        3. Rendering a view instance into it

        This reduces boilerplate in page loader functions.

        Args:
            view_instance: A view instance with an async render() method

        Example:
            async def load_players():
                view = TournamentPlayersView(page.user, org, tournament)
                await page.load_view_into_container(view)
        """
        container = self.get_dynamic_content_container() or self._content_container
        if container is None:
            # Initialize a default content container if not present
            self._content_container = ui.element("div").classes("page-container")
            container = self._content_container

        container.clear()
        with container:
            render_fn = getattr(view_instance, "render", None)
            if render_fn is None:
                return
            result = render_fn()
            if inspect.iscoroutine(result):
                await result

    def register_view_loader(
        self, key: str, view_factory: Callable[[], Any]
    ) -> None:
        """Register a view loader with automatic container management.

        This is a convenience method that combines view instantiation and loader
        registration into a single call, reducing boilerplate.

        Args:
            key: Unique identifier for this content loader
            view_factory: Callable that returns a view instance

        Example:
            # Instead of:
            async def load_players():
                view = TournamentPlayersView(page.user, org, tournament)
                await page.load_view_into_container(view)
            page.register_content_loader("players", load_players)

            # Use:
            page.register_view_loader(
                "players",
                lambda: TournamentPlayersView(page.user, org, tournament)
            )
        """

        async def loader():
            view = view_factory()
            await self.load_view_into_container(view)

        self.register_content_loader(key, loader)

    def register_instance_view(
        self, key: str, view_factory: Callable[[], Any]
    ) -> None:
        """Register an instance view loader.

        This is a shorthand for the common pattern of using create_instance_view_loader
        with register_content_loader.

        Args:
            key: Unique identifier for this content loader
            view_factory: Zero-argument callable that returns a view instance

        Example:
            # Instead of:
            page.register_content_loader(
                "profile",
                page.create_instance_view_loader(lambda: ProfileInfoView(page.user))
            )

            # Use:
            page.register_instance_view("profile", lambda: ProfileInfoView(page.user))
        """
        self.register_content_loader(key, self.create_instance_view_loader(view_factory))

    def register_multiple_views(
        self, view_mappings: list[tuple[str, Callable[[], Any]]]
    ) -> None:
        """Register multiple view loaders at once.

        This is a convenience method to reduce repetitive registration calls.

        Args:
            view_mappings: List of (key, view_factory) tuples

        Example:
            # Instead of:
            page.register_view_loader("overview", lambda: OverviewView(org, user))
            page.register_view_loader("members", lambda: MembersView(org, user))
            page.register_view_loader("settings", lambda: SettingsView(org, user))

            # Use:
            page.register_multiple_views([
                ("overview", lambda: OverviewView(org, user)),
                ("members", lambda: MembersView(org, user)),
                ("settings", lambda: SettingsView(org, user)),
            ])
        """
        for key, view_factory in view_mappings:
            self.register_view_loader(key, view_factory)

    def create_sidebar_items(
        self, items: list[tuple[str, str, str]]
    ) -> list[dict]:
        """Create multiple sidebar items with loaders at once.

        This is a convenience method to reduce repetitive sidebar item creation.

        Args:
            items: List of (label, icon, loader_key) tuples

        Returns:
            List of sidebar item dictionaries

        Example:
            # Instead of:
            sidebar_items = [
                page.create_sidebar_item_with_loader("Overview", "dashboard", "overview"),
                page.create_sidebar_item_with_loader("Members", "people", "members"),
                page.create_sidebar_item_with_loader("Settings", "settings", "settings"),
            ]

            # Use:
            sidebar_items = page.create_sidebar_items([
                ("Overview", "dashboard", "overview"),
                ("Members", "people", "members"),
                ("Settings", "settings", "settings"),
            ])
        """
        return [
            self.create_sidebar_item_with_loader(label, icon, loader_key)
            for label, icon, loader_key in items
        ]

    async def render(
        self,
        content: Optional[Callable[[BasePage], Awaitable[None]]] = None,
        sidebar_items: Optional[list] = None,
        use_dynamic_content: bool = False,
    ) -> None:
        """
        Render the page with header, sidebar, and optional content.

        Args:
            content: Async function to render page content, receives this BasePage instance
            sidebar_items: Optional list of sidebar items with 'label', 'icon', and 'action'
            use_dynamic_content: If True, creates a dynamic content container for content switching
        """
        # Load CSS with automatic cache busting
        css_version = get_css_version()
        ui.add_head_html(
            f'<link rel="stylesheet" href="/static/css/main.css?v={css_version}">'
        )

        # Set HTML language attribute for accessibility (executed immediately in head)
        ui.add_head_html(
            '<script>if(document.documentElement)document.documentElement.lang="en";</script>'
        )

        # Load JavaScript modules with cache busting
        # Core modules must load in <head> and run immediately to prevent flash
        js_modules = [
            "core/dark-mode.js",  # Dark mode (must be first to prevent flash)
            "core/url-manager.js",  # URL/query parameter management
            "utils/clipboard.js",  # Clipboard operations
            "utils/window-utils.js",  # Window operations
        ]

        for module in js_modules:
            js_version = get_js_version(module)
            ui.add_head_html(
                f'<script src="/static/js/{module}?v={js_version}"></script>'
            )

        # Load Sentry browser monitoring (if configured)
        self._load_sentry_browser()

        # Set page title
        ui.page_title(self.title)

        # Load current user
        await self._load_user()

        # Render header
        self._render_header()

        # Render impersonation banner if active
        await self._render_impersonation_banner()

        # Render MOTD banner if there is an active message
        await self._render_motd_banner()

        # Render sidebar via component
        sidebar_component = Sidebar(self._toggle_sidebar)
        self._sidebar_container, self._backdrop = sidebar_component.render(
            sidebar_items or []
        )

        # Render content if provided
        if content:
            if use_dynamic_content:
                # Check for view parameter BEFORE rendering content
                # Store it so pages can check if they should skip default rendering
                self.initial_view = await self._get_view_from_query()

                # Create a dynamic content container that can be cleared/reloaded
                self._content_container = (
                    ui.element("div")
                    .classes("page-container")
                    .props('id="main-content"')
                )
                with self._content_container:
                    self._dynamic_content_container = ui.column().classes("full-width")
                    with self._dynamic_content_container:
                        # Call content() which registers loaders and may render default view
                        # Pages can check page.initial_view to skip default rendering
                        await content(self)
                    # Footer at the bottom of the page container
                    Footer.render()

                # If there was a view parameter and it's now registered, load it
                # (verify it's valid after loaders are registered)
                if self.initial_view and self.initial_view in self._content_loaders:
                    # Load the view from query parameter
                    await self._content_loaders[self.initial_view]()

                # Show any notifications from query parameters
                await self._show_query_param_notifications()
            else:
                # Standard static content
                self._content_container = (
                    ui.element("div")
                    .classes("page-container")
                    .props('id="main-content"')
                )
                with self._content_container:
                    await content(self)
                    # Footer at the bottom of the page container
                    Footer.render()

                # Show any notifications from query parameters
                await self._show_query_param_notifications()

    @staticmethod
    def simple_page(title: str = "SahaBot2") -> "BasePage":
        """
        Create a simple page (no authentication required).

        Args:
            title: Page title

        Returns:
            BasePage: Configured page instance
        """
        return BasePage(title=title)

    @staticmethod
    def authenticated_page(title: str = "SahaBot2") -> "BasePage":
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
            use_dynamic_content: bool = False,
        ) -> None:
            # Check authentication before rendering
            user = await DiscordAuthService.require_auth()
            if not user:
                return  # User was redirected to login
            await original_render(content, sidebar_items, use_dynamic_content)

        page.render = authenticated_render  # type: ignore
        return page

    @staticmethod
    def admin_page(title: str = "Admin - SahaBot2") -> "BasePage":
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
            use_dynamic_content: bool = False,
        ) -> None:
            # Check admin permission before rendering
            user = await DiscordAuthService.require_permission(
                Permission.ADMIN, "/admin"
            )
            if not user:
                return  # User was redirected
            await original_render(content, sidebar_items, use_dynamic_content)

        page.render = admin_render  # type: ignore
        return page
