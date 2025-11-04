"""
Authentication pages for Discord OAuth2.

This module handles login, callback, and logout pages using BasePage.
"""

import secrets
import time
import logging
from nicegui import ui, app
from components import BasePage
from middleware.auth import DiscordAuthService

logger = logging.getLogger(__name__)


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

        # Store state with timestamp in browser storage (persists across redirects)
        # Use a dict to support multiple concurrent login attempts (multiple tabs)
        if 'oauth_states' not in app.storage.browser:
            app.storage.browser['oauth_states'] = {}

        # Clean up old states (older than 10 minutes)
        current_time = time.time()
        app.storage.browser['oauth_states'] = {
            k: v for k, v in app.storage.browser['oauth_states'].items()
            if current_time - v < 600  # 10 minutes
        }

        # Store new state with current timestamp
        app.storage.browser['oauth_states'][state] = current_time

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
        # CRITICAL: Prevent multiple executions of the same callback
        # Discord OAuth codes can only be used once, and NiceGUI may render pages multiple times
        callback_key = f"oauth_callback_{code}_{state}" if code and state else None
        
        # Check if we've already processed this exact callback
        if callback_key and app.storage.user.get(callback_key):
            logger.info("OAuth callback already processed, skipping duplicate execution")
            # Redirect to home since we already processed this
            ui.navigate.to('/')
            return
        
        # Mark this callback as being processed
        if callback_key:
            app.storage.user[callback_key] = True
        
        base = BasePage.simple_page(title="SahaBot2 - Authentication")

        async def content(page: BasePage):  # noqa: ARG001 - required by BasePage pattern
            """Render authentication callback content."""
            # Check for errors
            if error:
                with ui.element('div').classes('card text-center'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Authentication Failed')
                    with ui.element('div').classes('card-body'):
                        ui.label(f'Error: {error}').classes('text-error')
                        ui.button('Try Again', on_click=lambda: ui.navigate.to('/auth/login')).classes('btn btn-primary mt-2')
                return

            # Verify CSRF state
            stored_states = app.storage.browser.get('oauth_states', {})
            
            logger.info("OAuth callback - state: %s, stored states count: %d", 
                       state[:10] + "..." if state else "None", 
                       len(stored_states))
            
            # Check if state exists and is valid
            if not state:
                logger.warning("OAuth callback received without state parameter")
                with ui.element('div').classes('card text-center'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Authentication Failed')
                    with ui.element('div').classes('card-body'):
                        ui.label('Invalid state token. Please try again.').classes('text-error')
                        ui.button('Try Again', on_click=lambda: ui.navigate.to('/auth/login')).classes('btn btn-primary mt-2')
                return
            
            if state not in stored_states:
                logger.warning("OAuth state mismatch - state not found in stored states. Received: %s", state[:10] + "...")
                logger.debug("Stored states: %s", [k[:10] + "..." for k in stored_states.keys()])
                with ui.element('div').classes('card text-center'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Authentication Failed')
                    with ui.element('div').classes('card-body'):
                        ui.label('Invalid state token. Please try again.').classes('text-error')
                        ui.label('This can happen if you took too long to log in or if cookies are disabled.').classes('text-secondary text-sm mt-2')
                        ui.button('Try Again', on_click=lambda: ui.navigate.to('/auth/login')).classes('btn btn-primary mt-2')
                return
            
            # Check if state is expired (older than 10 minutes)
            state_timestamp = stored_states[state]
            if time.time() - state_timestamp > 600:
                logger.warning("OAuth state expired - state is older than 10 minutes")
                with ui.element('div').classes('card text-center'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Authentication Failed')
                    with ui.element('div').classes('card-body'):
                        ui.label('Login session expired. Please try again.').classes('text-error')
                        ui.button('Try Again', on_click=lambda: ui.navigate.to('/auth/login')).classes('btn btn-primary mt-2')
                return

            # Exchange code for token and authenticate
            if code:
                try:
                    # Get IP address (for audit log)
                    ip_address = None

                    # Authenticate user
                    logger.info("Starting OAuth authentication for code: %s...", code[:10] if code else "None")
                    user = await auth_service.authenticate_user(code, ip_address)

                    # Set user in session
                    await auth_service.set_current_user(user)

                    # Clear the used OAuth state
                    stored_states = app.storage.browser.get('oauth_states', {})
                    stored_states.pop(state, None)
                    app.storage.browser['oauth_states'] = stored_states
                    
                    # Also clear legacy oauth_state if present
                    app.storage.browser.pop('oauth_state', None)
                    
                    # Clean up callback tracking (no longer needed after successful auth)
                    if callback_key:
                        app.storage.user.pop(callback_key, None)

                    # Redirect to requested page or home
                    redirect_url = app.storage.user.pop('redirect_after_login', '/')
                    logger.info("OAuth authentication successful, redirecting to: %s", redirect_url)
                    ui.navigate.to(redirect_url)

                except Exception as e:
                    logger.error("OAuth authentication failed: %s", str(e), exc_info=True)
                    
                    # Clean up callback tracking on error
                    if callback_key:
                        app.storage.user.pop(callback_key, None)
                    
                    with ui.element('div').classes('card text-center'):
                        with ui.element('div').classes('card-header'):
                            ui.label('Authentication Failed')
                        with ui.element('div').classes('card-body'):
                            ui.label(f'Error: {str(e)}').classes('text-error')
                            ui.button('Try Again', on_click=lambda: ui.navigate.to('/auth/login')).classes('btn btn-primary mt-2')
            else:
                # No code provided
                with ui.element('div').classes('card text-center'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Authentication Failed')
                    with ui.element('div').classes('card-body'):
                        ui.label('No authorization code received.').classes('text-error')
                        ui.button('Try Again', on_click=lambda: ui.navigate.to('/auth/login')).classes('btn btn-primary mt-2')

        await base.render(content)

    @ui.page('/auth/logout')
    async def logout_page():
        """Logout page - clears session and redirects to home."""
        await auth_service.clear_current_user()
        ui.navigate.to('/')
