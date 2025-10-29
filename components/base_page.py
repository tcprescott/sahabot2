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
        self.use_sidebar = use_sidebar
        self._panels = None
        self._mobile_drawer = None
        self.sidebar_collapsed: bool = bool(app.storage.user.get('sidebar_collapsed', False))
    
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

        def toggle_dark_mode():
            self.dark_mode.value = not self.dark_mode.value
            app.storage.user['dark_mode'] = self.dark_mode.value
            # Update icon to reflect current state
            if dark_btn_ref['btn'] is not None:
                icon = 'light_mode' if self.dark_mode.value else 'dark_mode'
                dark_btn_ref['btn'].props(f"icon={icon}")
                dark_btn_ref['btn'].update()

        with ui.header().classes(replace='row items-center'):
            # Burger for mobile to toggle drawer
            ui.button(icon='menu', on_click=self._toggle_drawer).props('flat color=white').classes('mobile-only')
            # Navigation menu
            for label, action in self.top_menu:
                ui.button(label, on_click=lambda a=action: ui.navigate.to(a)).props('flat color=white')

            # User section or login
            if self.user:
                ui.label(self.user.discord_username).classes('text-lg user-name')
                avatar_url = f"https://cdn.discordapp.com/avatars/{self.user.discord_id}/{self.user.discord_avatar}.png" if self.user.discord_avatar else None
                if avatar_url:
                    ui.image(avatar_url).props('width=32 height=32 fit=cover round').classes('user-avatar')
                ui.button(on_click=self._handle_logout, icon='logout').props('flat color=white')
            else:
                ui.button(
                    'Login with Discord',
                    on_click=lambda: ui.navigate.to('/auth/login'),
                    icon='login'
                ).props('flat color=white').classes('login-button')
            
            # Dark mode toggle (always visible)
            dark_icon = 'light_mode' if dark_pref else 'dark_mode'
            dark_btn_ref['btn'] = ui.button(
                icon=dark_icon,
                on_click=toggle_dark_mode
            ).props('flat color=white').tooltip('Toggle dark mode')

    def _toggle_drawer(self) -> None:
        """Toggle the mobile drawer."""
        if self._mobile_drawer is not None:
            self._mobile_drawer.value = not self._mobile_drawer.value

    def _toggle_sidebar_collapse(self) -> None:
        """Toggle desktop sidebar collapsed state and persist preference."""
        self.sidebar_collapsed = not self.sidebar_collapsed
        app.storage.user['sidebar_collapsed'] = self.sidebar_collapsed
        # No direct element refs here; classes are applied on render per state

    def _on_select_tab(self, label: str) -> None:
        """Select a tab in the hidden tab panels via sidebar/drawer."""
        if self._panels is not None:
            self._panels.value = label
    
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
        def on_tab_change(event):
            """Update URL query param when tab changes."""
            ui.navigate.history.push(f'?tab={event.value}')

        # Determine default tab
        tab_labels = [tab['label'] for tab in tabs]
        default_tab = self.default_tab if self.default_tab in tab_labels else tabs[0]['label']

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
                args = ()
                kwargs = {}
            
            # Call content function (async or sync)
            if inspect.iscoroutinefunction(content_func):
                await content_func(*args, **kwargs)
            else:
                content_func(*args, **kwargs)

        # Render tabs navigation (hidden when using sidebar)
        with ui.tabs(on_change=on_tab_change).props('horizontal').classes('w-full' + (' hidden' if hide_tabs else '')) as panels:
            for tab in tabs:
                ui.tab(tab['label'], icon=tab.get('icon'))
        self._panels = panels
        
        # Render tab panels content
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
            
            # Render header (footer will be rendered after content)
            self._render_header()
            
            # Render content (either tabbed or regular)
            if self.tabs and not self.use_sidebar:
                await self.render_tabbed_page(self.tabs)
            elif self.tabs and self.use_sidebar:
                # Mobile drawer with menu
                with ui.left_drawer(bordered=True, value=False).classes('mobile-only') as drawer:
                    self._mobile_drawer = drawer
                    # Build mobile menu
                    for tab in self.tabs:
                        def make_handler(lbl: str):
                            return lambda: (self._on_select_tab(lbl), setattr(drawer, 'value', False))
                        ui.button(tab['label'], icon=tab.get('icon'), on_click=make_handler(tab['label']))
                # Desktop layout with sidebar and content
                with ui.element('div').classes('page-container page-container-wide'):
                    # Use responsive grid: sidebar takes width on md+ screens
                    with ui.row().classes('full-width q-gutter-md'):
                        # Sidebar (desktop only)
                        with ui.column().classes('desktop-only col-12 col-md-3'):
                            sidebar_classes = 'sidebar' + (' collapsed' if self.sidebar_collapsed else '')
                            with ui.element('div').classes(sidebar_classes):
                                # Sidebar items
                                for tab in self.tabs:
                                    # Use a flat button to handle clicks; style it like a sidebar item
                                    ui.button(
                                        tab['label'],
                                        icon=tab.get('icon') or 'chevron_right',
                                        on_click=lambda lbl=tab['label']: self._on_select_tab(lbl)
                                    ).props('flat').classes('sidebar-item full-width justify-start')
                                ui.element('div').classes('spacer')
                                # Collapse toggle
                                ui.button(icon='chevron_left' if not self.sidebar_collapsed else 'chevron_right',
                                          on_click=self._toggle_sidebar_collapse).props('flat')
                        # Content area
                        with ui.column().classes('full-width col-12 col-md-9'):
                            await self.render_tabbed_page(self.tabs, hide_tabs=True)
            else:
                with ui.element('div').classes('page-container'):
                    with ui.element('div').classes('content-wrapper'):
                        await content_fn(self)
            
            # Render footer after content so it appears at the bottom
            self._render_footer()
        
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
            # Override header rendering to do nothing
            page._render_header = lambda: None
        
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
