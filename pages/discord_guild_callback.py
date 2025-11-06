"""
Discord Guild OAuth2 callback page.

Handles the OAuth2 redirect after a user adds the bot to a Discord server.
"""

import logging
from nicegui import ui
from components import BasePage
from application.services.discord.discord_guild_service import DiscordGuildService
from config import settings

logger = logging.getLogger(__name__)


def register():
    """Register Discord guild callback route."""

    @ui.page('/discord-guild/callback')
    async def discord_guild_callback(
        code: str = None,
        state: str = None,
        guild_id: str = None,
        error: str = None
    ):
        """
        Handle Discord OAuth2 callback after bot is added to a server.

        Args:
            code: OAuth2 authorization code
            state: State parameter containing organization ID
            guild_id: Discord guild ID (server ID) that the bot was added to
            error: Error message if authorization failed
        """
        # Require authentication via session
        base = BasePage.authenticated_page(
            title="SahaBot2 - Discord Server Linking"
        )

        async def content(page: BasePage):
            """Render callback content."""
            # Check for errors
            if error:
                with ui.element('div').classes('card text-center'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Failed to Link Discord Server')
                    with ui.element('div').classes('card-body'):
                        ui.label(f'Error: {error}').classes('text-error')
                        ui.button(
                            'Back to Home',
                            on_click=lambda: ui.navigate.to('/')
                        ).classes('btn btn-primary mt-2')
                return

            # Verify we have required parameters
            if not code or not state:
                logger.warning("Discord guild callback missing required parameters")
                with ui.element('div').classes('card text-center'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Invalid Request')
                    with ui.element('div').classes('card-body'):
                        ui.label('Missing required parameters.').classes('text-error')
                        ui.button(
                            'Back to Home',
                            on_click=lambda: ui.navigate.to('/')
                        ).classes('btn btn-primary mt-2')
                return

            # Parse organization ID from state
            try:
                if not state.startswith('org:'):
                    raise ValueError("Invalid state format")
                organization_id = int(state.split(':', 1)[1])
            except (ValueError, IndexError):
                logger.error("Invalid state parameter: %s", state)
                with ui.element('div').classes('card text-center'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Invalid Request')
                    with ui.element('div').classes('card-body'):
                        ui.label('Invalid state parameter.').classes('text-error')
                        ui.button(
                            'Back to Home',
                            on_click=lambda: ui.navigate.to('/')
                        ).classes('btn btn-primary mt-2')
                return

            # Show processing message
            with ui.element('div').classes('card text-center'):
                with ui.element('div').classes('card-header'):
                    ui.label('Linking Discord Server...')
                with ui.element('div').classes('card-body'):
                    ui.spinner(size='lg')
                    ui.label('Verifying permissions and creating link...').classes('mt-2')

            # Process the callback
            service = DiscordGuildService()
            base_url = settings.BASE_URL or "http://localhost:8080"
            redirect_uri = f"{base_url}/discord-guild/callback"

            try:
                guild, error_code = await service.verify_and_link_guild(
                    user=page.user,
                    organization_id=organization_id,
                    code=code,
                    redirect_uri=redirect_uri,
                    guild_id=guild_id
                )

                if guild:
                    logger.info(
                        "Successfully linked Discord guild %s to organization %s",
                        guild.guild_id,
                        organization_id
                    )
                    # Redirect to organization admin page with success message
                    ui.navigate.to(
                        f'/orgs/{organization_id}/admin?view=discord_servers&success=discord_server_linked'
                    )
                else:
                    # Failed to link - use specific error message
                    logger.warning(
                        "Failed to link Discord guild for organization %s (error: %s)",
                        organization_id,
                        error_code or 'unknown'
                    )

                    # Map error codes to user-friendly messages
                    error_messages = {
                        'no_membership': 'not_organization_member',
                        'oauth_failed': 'oauth_authentication_failed',
                        'no_access_token': 'oauth_authentication_failed',
                        'guild_not_found': 'discord_server_not_found',
                        'no_admin_permissions': 'insufficient_discord_permissions',
                        'already_linked': 'discord_server_already_linked',
                    }
                    error_msg = error_messages.get(error_code, 'failed_to_link_discord_server')

                    # Redirect to organization admin page with specific error
                    ui.navigate.to(
                        f'/orgs/{organization_id}/admin?view=discord_servers&error={error_msg}'
                    )

            except Exception as e:
                logger.exception("Error processing Discord guild callback: %s", e)
                # Redirect to organization admin page with error
                ui.navigate.to(
                    f'/orgs/{organization_id}/admin?view=discord_servers&error=failed_to_link_discord_server'
                )

        await base.render(content)
