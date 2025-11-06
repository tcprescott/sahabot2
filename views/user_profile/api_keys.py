"""
API Keys management view.

Allow users to generate and manage their API keys.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from components.datetime_label import DateTimeLabel
from components.dialogs import CreateApiKeyDialog
from application.services.security.api_token_service import ApiTokenService
import logging

logger = logging.getLogger(__name__)


class ApiKeysView:
    """View for managing API keys."""

    def __init__(self, user: User) -> None:
        self.user = user
        self.service = ApiTokenService()
        self.container = None

    async def _refresh(self) -> None:
        """Refresh the API keys list."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _generate_new_key(self) -> None:
        """Generate a new API key."""
        async def create_token(name: str) -> str:
            """Create the token with the given name and return the plaintext token."""
            try:
                token_data = await self.service.create_token(self.user.id, name)
                return token_data['token']
            except Exception as e:
                logger.error("Failed to generate API key: %s", e)
                ui.notify(f'Failed to generate API key: {e}', type='negative')
                return None

        # Show create dialog which will also display the token
        dialog = CreateApiKeyDialog(on_create=create_token, on_complete=self._refresh)
        await dialog.show()

    async def _revoke_token(self, token_id: int) -> None:
        """Revoke an API token."""
        try:
            await self.service.revoke_token(token_id)
            ui.notify('API key revoked', type='positive')
            await self._refresh()
        except Exception as e:
            logger.error("Failed to revoke API key: %s", e)
            ui.notify(f'Failed to revoke API key: {e}', type='negative')

    async def _render_content(self) -> None:
        """Render the API keys management interface."""
        all_tokens = await self.service.list_user_tokens(self.user.id)
        # Filter out revoked tokens
        tokens = [t for t in all_tokens if t.is_active]

        with Card.create(title='API Keys'):
            with ui.row().classes('w-full justify-between mb-4'):
                ui.label(f'{len(tokens)} active API key(s)').classes('text-secondary')
                ui.button('Generate New Key', icon='add_circle', on_click=self._generate_new_key).props('color=positive').classes('btn')

            if not tokens:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('key').classes('text-secondary icon-large')
                    ui.label('No API keys yet').classes('text-secondary')
                    ui.label('Generate a key to access the API').classes('text-secondary text-sm')
            else:
                def render_name(t):
                    return ui.label(t.name)

                def render_created(t):
                    return DateTimeLabel.datetime(t.created_at)

                def render_last_used(t):
                    if t.last_used_at:
                        return DateTimeLabel.datetime(t.last_used_at)
                    return ui.label('Never').classes('text-secondary')

                def render_status(t):
                    if t.expires_at and t.expires_at < t.created_at:  # Basic check
                        return ui.label('Expired').classes('badge badge-warning')
                    return ui.label('Active').classes('badge badge-success')

                def render_actions(t):
                    with ui.row().classes('gap-2'):
                        ui.button('Revoke', icon='block', on_click=lambda token=t: self._revoke_token(token.id)).props('color=negative').classes('btn')

                columns = [
                    TableColumn('Name', cell_render=render_name),
                    TableColumn('Created', cell_render=render_created),
                    TableColumn('Last Used', cell_render=render_last_used),
                    TableColumn('Status', cell_render=render_status),
                    TableColumn('Actions', cell_render=render_actions),
                ]
                table = ResponsiveTable(columns, tokens)
                await table.render()

    async def render(self) -> None:
        """Render the API keys view."""
        self.container = ui.column().classes('full-width')
        with self.container:
            await self._render_content()
