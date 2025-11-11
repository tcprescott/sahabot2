"""
Base page component for consistent layout across the application.

This module provides the BasePage class which serves as the template for all pages,
including a header with branding, user info, and navigation menu.
"""

from __future__ import annotations
from typing import Optional, Callable, Awaitable
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

        # Success message (green notification)
        if "success" in params:
            message = params["success"]
            # Convert underscores to spaces and title case
            formatted = message.replace("_", " ").title()
            ui.notify(formatted, color="positive")

        # Error message (red notification)
        if "error" in params:
            message = params["error"]
            # Convert underscores to spaces and title case
            formatted = message.replace("_", " ").title()
            ui.notify(formatted, color="negative")

        # Info message (blue notification)
        if "message" in params:
            message = params["message"]
            # Convert underscores to spaces and title case
            formatted = message.replace("_", " ").title()
            ui.notify(formatted, color="info")

    def _render_header(self) -> None:
        """Render the header bar."""
        header = Header(self.user, self._toggle_sidebar)
        header.render()

    async def _render_impersonation_banner(self) -> None:
        """Render impersonation banner if user is impersonating another user."""
        if not self.user:
            return

        # Check if user is impersonating
        from middleware.auth import DiscordAuthService

        if not DiscordAuthService.is_impersonating():
            return

        # Get the original user (the impersonator)
        original_user = await DiscordAuthService.get_original_user()
        if not original_user:
            return

        # Render impersonation banner
        with ui.element("div").classes("impersonation-banner"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("person_off").classes("text-xl")
                ui.label(f"Impersonating: {self.user.discord_username}").classes(
                    "text-base font-semibold"
                )
                ui.label(f"(as {original_user.discord_username})").classes(
                    "text-sm text-secondary"
                )
                ui.button(
                    "Stop Impersonation",
                    on_click=lambda: ui.navigate.to("/admin/users/impersonate/stop"),
                ).classes("btn").props("color=warning size=sm")

    async def _render_motd_banner(self) -> None:
        """Render MOTD banner if there is an active message."""
        await MOTDBanner.render()

    def _toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        self.sidebar_open = not self.sidebar_open

        if self._sidebar_container:
            if self.sidebar_open:
                self._sidebar_container.classes(remove="sidebar-closed", add="sidebar-open")
            else:
                self._sidebar_container.classes(remove="sidebar-open", add="sidebar-closed")

        if self._backdrop:
            self._backdrop.set_visibility(self.sidebar_open)

    def create_nav_link(self, label: str, icon: str, to: str, active: bool = False) -> dict:
        """Create a sidebar item that navigates to a route.

        Args:
            label: Display label for the link
            icon: Material icon name
            to: Target route/path to navigate to
            active: Whether this link is currently active (for highlighting)

        Returns:
            Sidebar item dictionary that, when clicked, navigates to the given route
        """

        def action() -> None:
            ui.navigate.to(to)

        item = {"label": label, "icon": icon, "action": action}
        if active:
            item["active"] = True
        return item

    def create_separator(self) -> dict:
        """Create a visual separator item for the sidebar.

        Returns:
            Sidebar separator item dictionary
        """
        return {"type": "separator"}

    async def render(
        self,
        content: Optional[Callable[[BasePage], Awaitable[None]]] = None,
        sidebar_items: Optional[list] = None,
    ) -> None:
        """
        Render the page with header, sidebar, and optional content.

        Args:
            content: Async function to render page content, receives this BasePage instance
            sidebar_items: Optional list of sidebar items with 'label', 'icon', and 'action'
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
            "core/navigation.js",  # Navigation operations
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
            BasePage: Configured page instance that redirects to login if not authenticated
        """
        user = DiscordAuthService.require_auth()
        if not user:
            # User will be redirected by require_auth()
            return BasePage(title=title)

        return BasePage(title=title)

    @staticmethod
    def admin_page(title: str = "SahaBot2 - Admin") -> "BasePage":
        """
        Create an admin page (requires admin permission).

        Args:
            title: Page title

        Returns:
            BasePage: Configured page instance that redirects if not admin
        """
        user = DiscordAuthService.require_permission(Permission.ADMIN)
        if not user:
            # User will be redirected by require_permission()
            return BasePage(title=title)

        return BasePage(title=title)
