"""
Base page template for SahaBot2.

This module provides a reusable base template for all pages with consistent navbar and layout.
"""

from nicegui import ui
from middleware.auth import DiscordAuthService
from models import User
from typing import Optional, Callable, Awaitable


class BasePage:
    """
    Base page template with consistent layout and navigation.
    
    This class provides a reusable template for all pages, ensuring consistent
    navbar, CSS loading, and page structure across the application.
    """
    
    def __init__(
        self,
        title: str = "SahaBot2",
        active_nav: str = "",
        require_auth: bool = False,
        require_permission: Optional[int] = None,
        redirect_path: str = "/"
    ):
        """
        Initialize the base page template.
        
        Args:
            title: Page title for the navbar
            active_nav: Which nav item is active ('home', 'admin', etc.)
            require_auth: Whether authentication is required
            require_permission: Required permission level (if any)
            redirect_path: Path to redirect to if auth fails
        """
        self.title = title
        self.active_nav = active_nav
        self.require_auth = require_auth
        self.require_permission = require_permission
        self.redirect_path = redirect_path
        self.auth_service = DiscordAuthService()
        self.user: Optional[User] = None
    
    def _load_css(self) -> None:
        """Load the main CSS stylesheet."""
        ui.add_head_html('<link rel="stylesheet" href="/static/css/main.css">')
    
    def _check_authorization(self) -> bool:
        """
        Check if user meets authentication and authorization requirements.
        
        Returns:
            bool: True if authorized, False otherwise
        """
        if self.require_permission is not None:
            self.user = self.auth_service.require_permission(
                self.require_permission,
                self.redirect_path
            )
            return self.user is not None
        elif self.require_auth:
            self.auth_service.require_auth(self.redirect_path)
            self.user = self.auth_service.get_current_user()
            return self.user is not None
        else:
            self.user = self.auth_service.get_current_user()
            return True
    
    def _render_navbar(self) -> None:
        """Render the navigation bar."""
        with ui.element('div').classes('navbar'):
            with ui.element('div').classes('navbar-content'):
                with ui.element('div').classes('navbar-brand'):
                    ui.label(self.title)
                with ui.element('div').classes('navbar-menu'):
                    # Home link
                    home_classes = 'navbar-link active' if self.active_nav == 'home' else 'navbar-link'
                    ui.link('Home', '/').classes(home_classes)
                    
                    # Admin link (if user has permission)
                    if self.user and self.user.is_admin():
                        admin_classes = 'navbar-link active' if self.active_nav == 'admin' else 'navbar-link'
                        ui.link('Admin', '/admin').classes(admin_classes)
                    
                    # Login/Logout button
                    if self.user:
                        ui.button(
                            'Logout',
                            on_click=lambda: self._handle_logout()
                        ).classes('btn btn-secondary')
                    else:
                        ui.button(
                            'Login with Discord',
                            on_click=lambda: ui.navigate.to('/auth/login')
                        ).classes('btn btn-primary')
    
    async def _handle_logout(self) -> None:
        """Handle user logout."""
        await self.auth_service.clear_current_user()
        ui.navigate.to('/')
    
    def render(self, content_fn: Callable[['BasePage'], Awaitable[None]]) -> Callable[[], Awaitable[None]]:
        """
        Render the complete page with navbar and content.
        
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
            if not self._check_authorization():
                return
            
            # Render navbar
            self._render_navbar()
            
            # Render content
            with ui.element('div').classes('page-container'):
                with ui.element('div').classes('content-wrapper'):
                    await content_fn(self)
        
        return page_renderer
    
    @staticmethod
    def simple_page(
        title: str = "SahaBot2",
        active_nav: str = "",
        show_navbar: bool = True
    ) -> 'BasePage':
        """
        Create a simple page without authentication requirements.
        
        Args:
            title: Page title
            active_nav: Active navigation item
            show_navbar: Whether to show the navbar
        
        Returns:
            BasePage: Configured base page instance
        """
        page = BasePage(title=title, active_nav=active_nav)
        
        if not show_navbar:
            # Override navbar rendering to do nothing
            page._render_navbar = lambda: None
        
        return page
    
    @staticmethod
    def authenticated_page(
        title: str = "SahaBot2",
        active_nav: str = "",
        redirect_path: str = "/"
    ) -> 'BasePage':
        """
        Create a page that requires authentication.
        
        Args:
            title: Page title
            active_nav: Active navigation item
            redirect_path: Path to redirect to after login
        
        Returns:
            BasePage: Configured base page instance
        """
        return BasePage(
            title=title,
            active_nav=active_nav,
            require_auth=True,
            redirect_path=redirect_path
        )
    
    @staticmethod
    def admin_page(
        title: str = "SahaBot2 - Admin",
        active_nav: str = "admin",
        redirect_path: str = "/admin"
    ) -> 'BasePage':
        """
        Create a page that requires admin permissions.
        
        Args:
            title: Page title
            active_nav: Active navigation item
            redirect_path: Path to redirect to if unauthorized
        
        Returns:
            BasePage: Configured base page instance
        """
        from models import Permission
        return BasePage(
            title=title,
            active_nav=active_nav,
            require_permission=Permission.ADMIN,
            redirect_path=redirect_path
        )
