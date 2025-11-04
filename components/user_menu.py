"""
User menu component for the header bar.

This module provides the UserMenu component for displaying user info and menu options.
"""

from typing import Optional, List, Dict, Any
from nicegui import ui
from models import User
from middleware.auth import DiscordAuthService


class UserMenu:
    """
    User menu component for header navigation.

    Displays username and dropdown menu with customizable menu items.
    """

    def __init__(self, user: Optional[User] = None, menu_items: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize user menu.

        Args:
            user: Current authenticated user (None if not logged in)
            menu_items: Optional list of custom menu items. If None, uses default items.
                       Each item should be a dict with:
                       - 'name': Display text for the menu item
                       - 'icon': Material icon name
                       - 'on_click': Callback function
                       - 'separator': Optional bool, if True adds separator before item
                       - 'condition': Optional callable that returns bool for conditional display
        """
        self.user = user
        self.menu_items = menu_items or self._get_default_menu_items()

    async def _handle_logout(self) -> None:
        """Handle user logout."""
        await DiscordAuthService.clear_current_user()
        ui.notify('Logged out successfully', type='positive')
        ui.navigate.to('/')

    def _get_avatar_url(self) -> Optional[str]:
        """
        Get the Discord avatar URL for the user.

        Returns:
            Discord CDN URL for the user's avatar, or None if not available
        """
        if not self.user or not self.user.discord_avatar:
            return None

        # Discord CDN URL format
        return f"https://cdn.discordapp.com/avatars/{self.user.discord_id}/{self.user.discord_avatar}.png"

    def _get_default_menu_items(self) -> List[Dict[str, Any]]:
        """
        Get default menu items based on user authentication state.

        Returns:
            List of menu item dictionaries
        """
        def toggle_dark_mode():
            """Toggle dark mode using the external DarkMode API."""
            ui.run_javascript('window.DarkMode.toggle()')
        
        items = [
            {
                'name': 'Toggle Dark Mode',
                'icon': 'dark_mode',
                'on_click': toggle_dark_mode
            }
        ]

        if self.user:
            # Authenticated user items
            items.extend([
                {
                    'separator': True
                },
                {
                    'name': 'My Profile',
                    'icon': 'person',
                    'on_click': lambda: ui.navigate.to('/profile')
                },
                {
                    'name': 'Admin Panel',
                    'icon': 'admin_panel_settings',
                    'on_click': lambda: ui.navigate.to('/admin'),
                    'condition': lambda: self.user.is_admin()
                },
                {
                    'name': 'Logout',
                    'icon': 'logout',
                    'on_click': self._handle_logout
                }
            ])
        else:
            # Guest user items
            items.extend([
                {
                    'separator': True
                },
                {
                    'name': 'Login with Discord',
                    'icon': 'login',
                    'on_click': lambda: ui.navigate.to('/auth/login')
                }
            ])

        return items

    def render(self) -> None:
        """Render the user menu component."""
        # Show display name (with pronouns if enabled) if logged in
        if self.user:
            # Use full display name with pronouns in italics
            display_text = self.user.get_display_name()
            if self.user.show_pronouns and self.user.pronouns:
                with ui.row().classes('items-center gap-1 header-username-row'):
                    ui.label(display_text).classes('header-username')
                    ui.label(f'({self.user.pronouns})').classes('header-username-pronouns')
            else:
                ui.label(display_text).classes('header-username')

        # Render menu button with avatar or generic icon
        avatar_url = self._get_avatar_url()

        if avatar_url:
            # Use Discord avatar
            with ui.button().props('flat round').classes('header-menu-button'):
                ui.image(avatar_url).classes('w-8 h-8 rounded-full')
                with ui.menu():
                    self._render_menu_items()
        else:
            # Use generic account_circle icon
            with ui.button(icon='account_circle').props('flat round').classes('header-menu-button'):
                with ui.menu():
                    self._render_menu_items()

    def _render_menu_items(self) -> None:
        """Render the menu items."""
        for item in self.menu_items:
            # Check if this is a separator
            if item.get('separator'):
                ui.separator()
                continue

            # Check condition if specified
            condition = item.get('condition')
            if condition and callable(condition) and not condition():
                continue

            # Render menu item
            with ui.menu_item(on_click=item['on_click']):
                with ui.row().classes('items-center'):
                    ui.icon(item['icon']).classes('q-mr-sm')
                    ui.label(item['name'])
