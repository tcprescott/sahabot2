"""
Twitch OAuth2 pages.

This module handles Twitch account linking OAuth flow using NiceGUI pages.
"""

import secrets
import time
import logging
from nicegui import ui, app
from components import BasePage
from middleware.twitch_oauth import TwitchOAuthService
from middleware.auth import DiscordAuthService
from application.services.core.user_service import UserService

logger = logging.getLogger(__name__)


def register():
    """Register Twitch OAuth routes."""

    twitch_service = TwitchOAuthService()
    auth_service = DiscordAuthService()

    @ui.page('/twitch/link/initiate')
    async def initiate_link():
        """
        Initiate Twitch OAuth2 flow for account linking.
        """
        # Check if user is authenticated
        user = await auth_service.get_current_user()
        if not user:
            logger.warning("Unauthenticated user attempted to initiate Twitch link")
            ui.navigate.to('/auth/login')
            return

        # Generate CSRF state token
        state = secrets.token_urlsafe(32)

        # Store state with timestamp and user ID in browser storage
        if 'twitch_oauth_states' not in app.storage.browser:
            app.storage.browser['twitch_oauth_states'] = {}

        # Clean up old states (older than 10 minutes)
        current_time = time.time()
        app.storage.browser['twitch_oauth_states'] = {
            k: v for k, v in app.storage.browser['twitch_oauth_states'].items()
            if current_time - v['timestamp'] < 600  # 10 minutes
        }

        # Store new state with current timestamp and user ID
        app.storage.browser['twitch_oauth_states'][state] = {
            'timestamp': current_time,
            'user_id': user.id
        }

        # Get authorization URL and redirect
        auth_url = twitch_service.get_authorization_url(state)
        logger.info("User %s initiating Twitch account link", user.id)
        ui.navigate.to(auth_url, new_tab=False)

    @ui.page('/twitch/link/callback')
    async def link_callback(code: str = None, state: str = None, error: str = None):
        """
        OAuth2 callback page.

        Args:
            code: Authorization code from Twitch
            state: CSRF state token
            error: Error message if authorization failed
        """
        base = BasePage.simple_page(title="SahaBot2 - Twitch Account Linking")

        async def content(page: BasePage):  # noqa: ARG001 - required by BasePage pattern
            """Render callback content."""
            # Check for errors
            if error:
                with ui.element('div').classes('card text-center'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Twitch Linking Failed')
                    with ui.element('div').classes('card-body'):
                        ui.label(f'Error: {error}').classes('text-error')
                        ui.button('Back to Profile', on_click=lambda: ui.navigate.to('/profile')).classes('btn btn-primary mt-2')
                return

            # Verify CSRF state
            stored_states = app.storage.browser.get('twitch_oauth_states', {})

            # Check if state exists and is valid
            if not state:
                logger.warning("Twitch OAuth callback received without state parameter")
                with ui.element('div').classes('card text-center'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Linking Failed')
                    with ui.element('div').classes('card-body'):
                        ui.label('Invalid state token. Please try again.').classes('text-error')
                        ui.button('Back to Profile', on_click=lambda: ui.navigate.to('/profile')).classes('btn btn-primary mt-2')
                return

            if state not in stored_states:
                logger.warning("Twitch OAuth state mismatch - state not found")
                with ui.element('div').classes('card text-center'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Linking Failed')
                    with ui.element('div').classes('card-body'):
                        ui.label('Invalid state token. Please try again.').classes('text-error')
                        ui.label('This can happen if you took too long or if cookies are disabled.').classes('text-secondary text-sm mt-2')
                        ui.button('Back to Profile', on_click=lambda: ui.navigate.to('/profile')).classes('btn btn-primary mt-2')
                return

            # Check if state is expired (older than 10 minutes)
            state_data = stored_states[state]
            if time.time() - state_data['timestamp'] > 600:
                logger.warning("Twitch OAuth state expired")
                with ui.element('div').classes('card text-center'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Linking Failed')
                    with ui.element('div').classes('card-body'):
                        ui.label('Linking session expired. Please try again.').classes('text-error')
                        ui.button('Back to Profile', on_click=lambda: ui.navigate.to('/profile')).classes('btn btn-primary mt-2')
                return

            # Get user ID from state
            user_id = state_data['user_id']

            # Exchange code for token and link account
            if code:
                try:
                    # Get user from database
                    user_service = UserService()
                    current_user = await user_service.get_user_by_id(user_id)

                    if not current_user:
                        logger.warning("User %s not found for Twitch callback", user_id)
                        with ui.element('div').classes('card text-center'):
                            with ui.element('div').classes('card-header'):
                                ui.label('Linking Failed')
                            with ui.element('div').classes('card-body'):
                                ui.label('User not found. Please log in again.').classes('text-error')
                                ui.button('Login', on_click=lambda: ui.navigate.to('/auth/login')).classes('btn btn-primary mt-2')
                        return

                    # Exchange code for token
                    token_data = await twitch_service.exchange_code_for_token(code)
                    access_token = token_data['access_token']

                    # Get user info from Twitch
                    userinfo = await twitch_service.get_user_info(access_token)
                    twitch_id = userinfo['id']
                    twitch_name = userinfo['login']
                    twitch_display_name = userinfo['display_name']

                    # Extract token information
                    refresh_token = token_data.get('refresh_token')
                    expires_in = token_data.get('expires_in')
                    expires_at = None
                    if expires_in:
                        expires_at = twitch_service.calculate_token_expiry(expires_in)

                    # Link the account
                    await user_service.link_twitch_account(
                        user=current_user,
                        twitch_id=twitch_id,
                        twitch_name=twitch_name,
                        twitch_display_name=twitch_display_name,
                        access_token=access_token,
                        refresh_token=refresh_token,
                        expires_at=expires_at
                    )

                    logger.info("Successfully linked Twitch account %s to user %s", twitch_id, current_user.id)

                    # Clear the used OAuth state
                    stored_states = app.storage.browser.get('twitch_oauth_states', {})
                    stored_states.pop(state, None)
                    app.storage.browser['twitch_oauth_states'] = stored_states

                    # Success message and redirect
                    with ui.element('div').classes('card text-center'):
                        with ui.element('div').classes('card-header'):
                            ui.label('Account Linked Successfully!')
                        with ui.element('div').classes('card-body'):
                            ui.label(f'Your Twitch account "{twitch_display_name}" has been linked.').classes('text-success')
                            ui.button('Go to Profile', on_click=lambda: ui.navigate.to('/profile')).classes('btn btn-primary mt-2')

                except ValueError as e:
                    logger.error("Error linking Twitch account: %s", str(e))
                    with ui.element('div').classes('card text-center'):
                        with ui.element('div').classes('card-header'):
                            ui.label('Linking Failed')
                        with ui.element('div').classes('card-body'):
                            ui.label(str(e)).classes('text-error')
                            ui.button('Back to Profile', on_click=lambda: ui.navigate.to('/profile')).classes('btn btn-primary mt-2')
                except Exception as e:
                    logger.error("Error in Twitch callback: %s", str(e), exc_info=True)
                    with ui.element('div').classes('card text-center'):
                        with ui.element('div').classes('card-header'):
                            ui.label('Linking Failed')
                        with ui.element('div').classes('card-body'):
                            ui.label('An error occurred while linking your account. Please try again.').classes('text-error')
                            ui.button('Back to Profile', on_click=lambda: ui.navigate.to('/profile')).classes('btn btn-primary mt-2')
            else:
                # No code provided
                with ui.element('div').classes('card text-center'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Linking Failed')
                    with ui.element('div').classes('card-body'):
                        ui.label('No authorization code received.').classes('text-error')
                        ui.button('Back to Profile', on_click=lambda: ui.navigate.to('/profile')).classes('btn btn-primary mt-2')

        await base.render(content)
