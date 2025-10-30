"""
Authentication pages for Discord OAuth2.

This module handles login, callback, and logout pages.
"""

import secrets
from nicegui import ui, app
from middleware.auth import DiscordAuthService


def register():
    """Register authentication routes."""

    auth_service = DiscordAuthService()

    @ui.page('/auth/login')
    async def login_page():
        """
        Login page - redirects to Discord OAuth2.
        """
        # Generate CSRF state token
        state = secrets.token_urlsafe(32)

        # Store state in browser storage (persists across redirects)
        app.storage.browser['oauth_state'] = state

        # Redirect to Discord authorization
        auth_url = auth_service.get_authorization_url(state)
        ui.navigate.to(auth_url, new_tab=False)

    @ui.page('/auth/callback')
    async def callback_page(code: str = None, state: str = None, error: str = None):
        """
        OAuth2 callback page.

        Args:
            code: Authorization code from Discord
            state: CSRF state token
            error: Error message if authorization failed
        """
        # Check for errors first (before any UI rendering)
        if error:
            ui.add_head_html('<link rel="stylesheet" href="/static/css/main.css">')
            with ui.element('div').classes('page-container'):
                with ui.element('div').classes('content-wrapper'):
                    with ui.element('div').classes('card text-center'):
                        with ui.element('div').classes('card-header'):
                            ui.label('Authentication Failed')
                        with ui.element('div').classes('card-body'):
                            ui.label(f'Error: {error}').classes('text-error')
                            ui.button('Try Again', on_click=lambda: ui.navigate.to('/auth/login')).classes('btn btn-primary mt-2')
            return

        # Verify CSRF state
        stored_state = app.storage.browser.get('oauth_state')
        if not state or state != stored_state:
            ui.add_head_html('<link rel="stylesheet" href="/static/css/main.css">')
            with ui.element('div').classes('page-container'):
                with ui.element('div').classes('content-wrapper'):
                    with ui.element('div').classes('card text-center'):
                        with ui.element('div').classes('card-header'):
                            ui.label('Authentication Failed')
                        with ui.element('div').classes('card-body'):
                            ui.label(f'Invalid state token. Please try again. (Expected: {stored_state}, Got: {state})').classes('text-error')
                            ui.button('Try Again', on_click=lambda: ui.navigate.to('/auth/login')).classes('btn btn-primary mt-2')
            return

        # Exchange code for token and authenticate (before rendering UI)
        if code:
            try:
                # Get IP address (for audit log)
                ip_address = None

                # Authenticate user
                user = await auth_service.authenticate_user(code, ip_address)

                # Set user in session
                await auth_service.set_current_user(user)

                # Clear OAuth state
                app.storage.browser.pop('oauth_state', None)

                # Redirect to requested page or home (immediate redirect, no UI)
                redirect_url = app.storage.user.pop('redirect_after_login', '/')
                ui.navigate.to(redirect_url)

            except Exception as e:
                # Only render UI on error
                ui.add_head_html('<link rel="stylesheet" href="/static/css/main.css">')
                with ui.element('div').classes('page-container'):
                    with ui.element('div').classes('content-wrapper'):
                        with ui.element('div').classes('card text-center'):
                            with ui.element('div').classes('card-header'):
                                ui.label('Authentication Failed')
                            with ui.element('div').classes('card-body'):
                                ui.label(f'Error: {str(e)}').classes('text-error')
                                ui.button('Try Again', on_click=lambda: ui.navigate.to('/auth/login')).classes('btn btn-primary mt-2')
        else:
            # No code provided
            ui.add_head_html('<link rel="stylesheet" href="/static/css/main.css">')
            with ui.element('div').classes('page-container'):
                with ui.element('div').classes('content-wrapper'):
                    with ui.element('div').classes('card text-center'):
                        with ui.element('div').classes('card-header'):
                            ui.label('Authentication Failed')
                        with ui.element('div').classes('card-body'):
                            ui.label('No authorization code received.').classes('text-error')
                            ui.button('Try Again', on_click=lambda: ui.navigate.to('/auth/login')).classes('btn btn-primary mt-2')

    @ui.page('/auth/logout')
    async def logout_page():
        """Logout page - clears session and redirects to home."""
        await auth_service.clear_current_user()
        ui.navigate.to('/')
