"""
Base page template for SahaBot2.

This module provides a reusable base template for all pages with consistent header, footer, and layout.
The template is designed to be responsive and work seamlessly on both mobile and desktop devices,
using a mobile-first approach while ensuring the desktop experience is polished and takes full
advantage of larger screens.

The layout includes:
- Header with navigation menu, user info, and dark mode toggle
- Optional tabbed content interface
- Footer with copyright information
- Persistent dark mode preference
"""

from nicegui import app, ui
from middleware.auth import DiscordAuthService
from models import User
from components.sidebar import Sidebar
from typing import Optional, Callable, Awaitable
import inspect


class BasePage:
    """
    Base page template with consistent layout and navigation.
    
    This class provides a reusable template for all pages, ensuring consistent
    header, footer, CSS loading, and page structure across the application.

    The template uses a responsive design approach that:
    - Works seamlessly on mobile devices (phones and tablets)
    - Provides a polished desktop experience that takes advantage of larger screens
    - Uses CSS media queries for device-appropriate layouts
    - Maintains feature parity across all devices while optimizing for each form factor
    """

    def __init__(
        self,
        title: str = "SahaBot2",
        active_nav: str = "",
        require_auth: bool = False,
        require_permission: Optional[int] = None,
        redirect_path: str = "/",
        copyright_text: str = "© 2025 SahaBot2",
        tabs: Optional[list] = None,
        default_tab: Optional[str] = None,
        use_sidebar: bool = False
    ):
        """
        Initialize the base page template.

        Args:
            title: Page title for the header
            active_nav: Which nav item is active ('home', 'admin', etc.)
            require_auth: Whether authentication is required
            require_permission: Required permission level (if any)
            redirect_path: Path to redirect to if auth fails
            copyright_text: Copyright text for footer
            tabs: Optional list of tab configurations for tabbed interface
            default_tab: Default tab to show (if using tabs)
            use_sidebar: Whether to use sidebar navigation instead of top tabs
        """
        self.title = title
        self.active_nav = active_nav
        self.require_auth = require_auth
        self.require_permission = require_permission
        self.redirect_path = redirect_path
        self.copyright_text = copyright_text
        self.tabs = tabs
        self.default_tab = default_tab
        self.auth_service = DiscordAuthService()
        self.user: Optional[User] = None
        self.dark_mode = None  # Will be initialized in render()
        self.top_menu: list[tuple[str, str]] = []
        self.show_header = True
        self.use_sidebar = use_sidebar
        self._panels = None
        self._sidebar = None
        self._backdrop_element = None
        self._rendered_tabs = set()
        self._tab_containers = {}

    def _load_css(self) -> None:
        """Load the main CSS stylesheet."""
        ui.add_head_html('<link rel="stylesheet" href="/static/css/main.css">')

    async def _check_authorization(self) -> bool:
        """
        Check if user meets authentication and authorization requirements.

        Returns:
            bool: True if authorized, False otherwise
        """
        if self.require_permission is not None:
            self.user = await self.auth_service.require_permission(
                self.require_permission,
                self.redirect_path
            )
            return self.user is not None
        elif self.require_auth:
            self.user = await self.auth_service.require_auth(self.redirect_path)
            return self.user is not None
        else:
            self.user = await self.auth_service.get_current_user()
            return True

    def _build_menu(self) -> None:
        """Build top navigation menu based on user permissions."""
        self.top_menu = [('Home', '/')]
        if self.user and self.user.is_admin():
            self.top_menu.append(('Admin', '/admin'))

    def _render_header(self) -> None:
        """Render the header with navigation menu and user controls."""
        dark_pref = bool(app.storage.user.get('dark_mode', False))
        dark_btn_ref = {'btn': None}
        header_buttons: list = []

        with ui.header() as header_el:
            # Header should always use white text regardless of theme
            header_color = 'white'
            header_text_class = 'text-white'
            header_el.classes(replace=f'row items-center {header_text_class}')
            # No burger on mobile; mobile uses a compact icon-only sidebar
            # Navigation menu
            for label, action in self.top_menu:
                btn = ui.button(label, on_click=lambda a=action: ui.navigate.to(a))
                btn.props(f'flat color={header_color}')
                btn.classes(header_text_class)
                header_buttons.append(btn)

            # User section or login
            if self.user:
                ui.label(self.user.discord_username).classes('text-lg user-name')
                avatar_url = f"https://cdn.discordapp.com/avatars/{self.user.discord_id}/{self.user.discord_avatar}.png" if self.user.discord_avatar else None
                if avatar_url:
                    ui.image(avatar_url).props('width=32 height=32 fit=cover round').classes('user-avatar')
                btn_logout = ui.button(on_click=self._handle_logout, icon='logout')
                btn_logout.props(f'flat color={header_color}')
                btn_logout.classes(header_text_class)
                header_buttons.append(btn_logout)
            else:
                btn_login = ui.button(
                    'Login with Discord',
                    on_click=lambda: ui.navigate.to('/auth/login'),
                    icon='login'
                )
                btn_login.props(f'flat color={header_color}')
                btn_login.classes('login-button')
                btn_login.classes(header_text_class)
                header_buttons.append(btn_login)

            # Dark mode toggle (always visible)
            dark_icon = 'light_mode' if dark_pref else 'dark_mode'

            def toggle_dark_mode():
                # Flip dark mode value and persist, but keep header text white
                self.dark_mode.value = not self.dark_mode.value
                app.storage.user['dark_mode'] = self.dark_mode.value
                # Only update the toggle icon; leave header/button colors as white
                if dark_btn_ref['btn'] is not None:
                    try:
                        icon = 'light_mode' if self.dark_mode.value else 'dark_mode'
                        dark_btn_ref['btn'].props(f"icon={icon}")
                        dark_btn_ref['btn'].update()
                    except Exception:
                        pass

            dark_btn_ref['btn'] = ui.button(
                icon=dark_icon,
                on_click=toggle_dark_mode
            )
            dark_btn_ref['btn'].props(f'flat color={header_color}')
            dark_btn_ref['btn'].tooltip('Toggle dark mode')
            header_buttons.append(dark_btn_ref['btn'])
    
    def _render_footer(self) -> None:
        """Render the footer with copyright text."""
        with ui.footer().classes('bg-grey-2 text-grey-7 q-pa-md footer-dark-override'):
            ui.label(self.copyright_text).classes('text-caption')
    
    async def _handle_logout(self) -> None:
        """Handle user logout."""
        await self.auth_service.clear_current_user()
        ui.navigate.to('/')
    
    async def render_tabbed_page(self, tabs: list, hide_tabs: bool = False) -> None:
        """Render a tabbed interface with the provided tab configuration.

        Args:
            tabs: List of tab dictionaries with 'label', 'icon' (optional), and 'content' keys.
                  Content can be a callable or tuple of (callable, args, kwargs).
        """
        async def render_tab_content(tab):
            """Render content for a single tab, handling both sync and async callables."""
            content = tab['content']

            # Parse content configuration
            if isinstance(content, tuple):
                content_func = content[0]
                args = content[1] if len(content) > 1 and content[1] is not None else ()
                kwargs = content[2] if len(content) > 2 and content[2] is not None else {}
            else:
                content_func = content
                # Pass self (the page) as first argument to tab content functions
                args = (self,)
                kwargs = {}

            # Call content function (async or sync)
            if inspect.iscoroutinefunction(content_func):
                await content_func(*args, **kwargs)
            else:
                content_func(*args, **kwargs)

        # Determine default tab
        tab_labels = [tab['label'] for tab in tabs]
        default_tab = self.default_tab if self.default_tab in tab_labels else tabs[0]['label']

        # Render tabs navigation (hidden when using sidebar)
        with ui.tabs().props('horizontal').classes('w-full' + (' hidden' if hide_tabs else '')) as panels:
            for tab in tabs:
                ui.tab(tab['label'], icon=tab.get('icon'))
        self._panels = panels

        # Render tab panels content - render all tabs immediately
        with ui.tab_panels(panels, value=default_tab):
            for tab in tabs:
                with ui.tab_panel(tab['label']):
                    with ui.row().classes('full-width'):
                        await render_tab_content(tab)
    
    def render(self, content_fn: Callable[['BasePage'], Awaitable[None]]) -> Callable[[], Awaitable[None]]:
        """
        Render the complete page with header, footer, and content.

        This method returns an async function that can be used as a NiceGUI page handler.

        Args:
            content_fn: Async function that renders the page content.
                       Receives the BasePage instance as an argument.

        Returns:
            Callable: Async function for NiceGUI page decorator

        Example:
            @ui.page('/')
            async def home_page():
                base = BasePage(title="Home", active_nav="home")

                async def content(page):
                    with ui.element('div').classes('card'):
                        ui.label('Welcome!')

                await base.render(content)()
        """
        async def page_renderer():
            # Load CSS
            self._load_css()

            # Check authorization
            if not await self._check_authorization():
                return

            # Initialize dark mode controller and restore user's preference
            dark_pref = bool(app.storage.user.get('dark_mode', False))
            self.dark_mode = ui.dark_mode()
            self.dark_mode.value = dark_pref

            # Build navigation menu
            self._build_menu()

            # Render header and footer
            if self.show_header:
                self._render_header()
            self._render_footer()

            # Render content (either tabbed or regular)
            if self.tabs and not self.use_sidebar:
                await self.render_tabbed_page(self.tabs)
            elif self.tabs and self.use_sidebar:
                # Responsive layout with overlay sidebar
                
                with ui.element('div').classes('page-container page-container-wide'):
                    # First render tabs to get panels reference
                    # (Use a temporary container to determine structure)
                    temp_default = self.default_tab if self.default_tab else (self.tabs[0]['label'] if self.tabs else None)
                    
                    # Create sidebar first (before content) with placeholder panels
                    self._sidebar = Sidebar(tabs=self.tabs, panels=None)
                    
                    # Create content container
                    content_container = ui.column()
                    
                    # Render sidebar elements (backdrop and sidebar)
                    self._sidebar.render(content_container)
                    
                    # Now render tab content (this creates self._panels)
                    with content_container:
                        await self.render_tabbed_page(self.tabs, hide_tabs=True)
                    
                    # Update sidebar with actual panels reference
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info("Setting sidebar.panels to %s (from self._panels)", self._panels)
                    self._sidebar.panels = self._panels
                    logger.info("Sidebar.panels is now %s", self._sidebar.panels)
            else:
                with ui.element('div').classes('page-container'):
                    with ui.element('div').classes('content-wrapper'):
                        await content_fn(self)

        return page_renderer
    
    @staticmethod
    def simple_page(
        title: str = "SahaBot2",
        active_nav: str = "",
        show_header: bool = True,
        copyright_text: str = "© 2025 SahaBot2",
        tabs: Optional[list] = None,
        default_tab: Optional[str] = None
    ) -> 'BasePage':
        """
        Create a simple page without authentication requirements.

        Args:
            title: Page title
            active_nav: Active navigation item
            show_header: Whether to show the header
            copyright_text: Copyright text for footer
            tabs: Optional list of tab configurations
            default_tab: Default tab to show

        Returns:
            BasePage: Configured base page instance
        """
        page = BasePage(
            title=title,
            active_nav=active_nav,
            copyright_text=copyright_text,
            tabs=tabs,
            default_tab=default_tab
        )

        if not show_header:
            # Use a flag to skip header rendering
            page.show_header = False

        return page
    
    @staticmethod
    def authenticated_page(
        title: str = "SahaBot2",
        active_nav: str = "",
        redirect_path: str = "/",
        copyright_text: str = "© 2025 SahaBot2",
        tabs: Optional[list] = None,
        default_tab: Optional[str] = None
    ) -> 'BasePage':
        """
        Create a page that requires authentication.

        Args:
            title: Page title
            active_nav: Active navigation item
            redirect_path: Path to redirect to after login
            copyright_text: Copyright text for footer
            tabs: Optional list of tab configurations
            default_tab: Default tab to show

        Returns:
            BasePage: Configured base page instance
        """
        return BasePage(
            title=title,
            active_nav=active_nav,
            require_auth=True,
            redirect_path=redirect_path,
            copyright_text=copyright_text,
            tabs=tabs,
            default_tab=default_tab
        )
    
    @staticmethod
    def admin_page(
        title: str = "SahaBot2 - Admin",
        active_nav: str = "admin",
        redirect_path: str = "/admin",
        copyright_text: str = "© 2025 SahaBot2",
        tabs: Optional[list] = None,
        default_tab: Optional[str] = None
    ) -> 'BasePage':
        """
        Create a page that requires admin permissions.

        Args:
            title: Page title
            active_nav: Active navigation item
            redirect_path: Path to redirect to if unauthorized
            copyright_text: Copyright text for footer
            tabs: Optional list of tab configurations
            default_tab: Default tab to show

        Returns:
            BasePage: Configured base page instance
        """
        from models import Permission as Perm
        return BasePage(
            title=title,
            active_nav=active_nav,
            require_permission=Perm.ADMIN,
            redirect_path=redirect_path,
            copyright_text=copyright_text,
            tabs=tabs,
            default_tab=default_tab
        )
