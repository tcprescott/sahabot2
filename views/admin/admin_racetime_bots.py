"""
RaceTime Bot administration view.

Provides interface for managing RaceTime bot configurations and organization assignments.
"""

from nicegui import ui
from components.data_table import ResponsiveTable, TableColumn
from components.datetime_label import DateTimeLabel
from models import User, RacetimeBot
from application.services.racetime_bot_service import RacetimeBotService
from application.services.organization_service import OrganizationService
from components.dialogs import RacetimeBotEditDialog, RacetimeBotAddDialog, RacetimeBotOrganizationsDialog, ConfirmDialog
import logging

logger = logging.getLogger(__name__)


class AdminRacetimeBotsView:
    """RaceTime bot administration view."""

    def __init__(self, current_user: User):
        """
        Initialize the RaceTime bots admin view.

        Args:
            current_user: Currently authenticated admin user
        """
        self.current_user = current_user
        self.bot_service = RacetimeBotService()
        self.org_service = OrganizationService()

        # State
        self.bots: list[RacetimeBot] = []
        self.search_query = ""
        self.include_inactive = True
        self.table_container = None

    async def render(self):
        """Render the RaceTime bot administration interface."""
        with ui.column().classes('full-width gap-md'):
            # Header section
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-header'):
                    ui.label('RaceTime Bot Management').classes('text-xl font-bold')
                with ui.element('div').classes('card-body'):
                    ui.label('Configure RaceTime.gg bot instances and assign them to organizations.').classes('text-secondary')

            # Search and filters
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-body'):
                    with ui.row().classes('full-width gap-4 items-center justify-between'):
                        # Search input
                        with ui.row().classes('items-center gap-4 flex-grow'):
                            search_input = ui.input(
                                label='Search bots',
                                placeholder='Search by category or name...'
                            ).classes('flex-grow')
                            search_input.on('update:model-value', lambda e: self._on_search_change(e.args))

                        # Include inactive checkbox
                        with ui.row().classes('items-center gap-3'):
                            inactive_switch = ui.switch('Include Inactive', value=self.include_inactive)
                            inactive_switch.on('update:model-value', lambda e: self._on_filter_change(e.args))

                            # Refresh button
                            ui.button(
                                icon='refresh',
                                on_click=self._refresh_bots
                            ).classes('btn').props('flat')

                            # Add bot button
                            ui.button(
                                'Add Bot',
                                icon='add',
                                on_click=self._open_add_bot
                            ).classes('btn btn-primary')

            # Bot table
            self.table_container = ui.column().classes('full-width')
            await self._refresh_bots()

    async def _refresh_bots(self):
        """Refresh the bot list and re-render the table."""
        # Load bots
        all_bots = await self.bot_service.get_all_bots(self.current_user)

        # Apply filters
        self.bots = all_bots
        if not self.include_inactive:
            self.bots = [b for b in self.bots if b.is_active]

        if self.search_query:
            query_lower = self.search_query.lower()
            self.bots = [
                b for b in self.bots
                if query_lower in b.category.lower() or query_lower in b.name.lower()
            ]

        # Re-render table
        if self.table_container:
            self.table_container.clear()
            with self.table_container:
                await self._render_table()

    async def _render_table(self):
        """Render the bots table."""
        if not self.bots:
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-body'):
                    with ui.row().classes('items-center gap-2 text-secondary'):
                        ui.icon('info')
                        ui.label('No RaceTime bots found. Click "Add Bot" to create one.')
            return

        # Prepare rows with organization counts
        rows = []
        for bot in self.bots:
            orgs = await self.bot_service.get_organizations_for_bot(bot.id, self.current_user)
            rows.append({
                'bot': bot,
                'org_count': len(orgs),
            })

        # Define cell renderers
        def render_category(row):
            ui.label(row['bot'].category)

        def render_name(row):
            ui.label(row['bot'].name)

        def render_client_id(row):
            bot = row['bot']
            client_id_display = bot.client_id[:20] + '...' if len(bot.client_id) > 20 else bot.client_id
            ui.label(client_id_display)

        async def render_status(row):
            bot = row['bot']
            with ui.column().classes('gap-1'):
                # Active/Inactive badge
                with ui.row().classes('gap-1'):
                    if bot.is_active:
                        ui.badge('Active', color='positive')
                    else:
                        ui.badge('Inactive', color='grey')

                # Connection status badge
                if bot.status == 0:  # UNKNOWN
                    with ui.badge(color='grey-7').classes('gap-1'):
                        ui.icon('help', size='xs')
                        ui.label('Unknown')
                elif bot.status == 1:  # CONNECTED
                    with ui.badge(color='positive').classes('gap-1'):
                        ui.icon('check_circle', size='xs')
                        ui.label('Connected')
                elif bot.status == 2:  # AUTH_FAILED
                    with ui.badge(color='negative').classes('gap-1'):
                        ui.icon('key_off', size='xs')
                        ui.label('Auth Failed')
                        if bot.status_message:
                            ui.tooltip(bot.status_message)
                elif bot.status == 3:  # CONNECTION_ERROR
                    with ui.badge(color='negative').classes('gap-1'):
                        ui.icon('error', size='xs')
                        ui.label('Connection Error')
                        if bot.status_message:
                            ui.tooltip(bot.status_message)
                elif bot.status == 4:  # DISCONNECTED
                    with ui.badge(color='warning').classes('gap-1'):
                        ui.icon('cloud_off', size='xs')
                        ui.label('Disconnected')

                # Last connected timestamp using DateTimeLabel
                if bot.last_connected_at:
                    with ui.row().classes('items-center gap-1'):
                        ui.label('Last:').classes('text-xs text-grey-7')
                        DateTimeLabel.create(
                            bot.last_connected_at,
                            format_type='datetime',
                            classes='text-xs text-grey-7'
                        )

        def render_actions(row):
            bot = row['bot']
            org_count = row['org_count']
            with ui.row().classes('gap-1'):
                ui.button(
                    icon='edit',
                    on_click=lambda b=bot: self._open_edit_bot(b.id)
                ).props('flat round dense size=sm').tooltip('Edit Bot')
                
                # Restart button (only for active bots)
                if bot.is_active:
                    ui.button(
                        icon='refresh',
                        on_click=lambda b=bot: self._restart_bot(b.id)
                    ).props('flat round dense size=sm color=primary').tooltip('Restart Bot')
                
                ui.button(
                    icon='groups',
                    on_click=lambda b=bot: self._open_manage_organizations(b.id)
                ).props('flat round dense size=sm').tooltip(f'Manage Organizations ({org_count})')
                ui.button(
                    icon='delete',
                    on_click=lambda b=bot: self._confirm_delete_bot(b.id)
                ).props('flat round dense size=sm color=negative').tooltip('Delete Bot')

        # Define columns
        columns = [
            TableColumn(label='Category', cell_render=render_category),
            TableColumn(label='Name', cell_render=render_name),
            TableColumn(label='Client ID', cell_render=render_client_id),
            TableColumn(label='Status', cell_render=render_status),
            TableColumn(label='Actions', cell_render=render_actions),
        ]

        # Render table wrapped in card
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-body'):
                table = ResponsiveTable(columns=columns, rows=rows)
                await table.render()

    async def _on_search_change(self, value: str):
        """Handle search query change."""
        self.search_query = value
        await self._refresh_bots()

    async def _on_filter_change(self, value: bool):
        """Handle include inactive filter change."""
        self.include_inactive = value
        await self._refresh_bots()

    async def _open_add_bot(self):
        """Open the add bot dialog."""
        dialog = RacetimeBotAddDialog(
            current_user=self.current_user,
            on_save=self._refresh_bots
        )
        await dialog.show()

    async def _open_edit_bot(self, bot_id: int):
        """Open the edit bot dialog."""
        bot = await self.bot_service.get_bot_by_id(bot_id, self.current_user)
        if not bot:
            ui.notify('Bot not found', type='negative')
            return

        dialog = RacetimeBotEditDialog(
            bot=bot,
            current_user=self.current_user,
            on_save=self._refresh_bots
        )
        await dialog.show()

    async def _restart_bot(self, bot_id: int):
        """Restart a bot."""
        bot = await self.bot_service.get_bot_by_id(bot_id, self.current_user)
        if not bot:
            ui.notify('Bot not found', type='negative')
            return

        if not bot.is_active:
            ui.notify('Cannot restart inactive bot', type='warning')
            return

        # Show loading notification
        ui.notify(f'Restarting bot "{bot.name}"...', type='info')

        success = await self.bot_service.restart_bot(bot_id, self.current_user)

        if success:
            ui.notify(f'Bot "{bot.name}" restarted successfully', type='positive')
            await self._refresh_bots()
        else:
            ui.notify(f'Failed to restart bot "{bot.name}"', type='negative')

    async def _open_manage_organizations(self, bot_id: int):
        """Open the manage organizations dialog."""
        bot = await self.bot_service.get_bot_by_id(bot_id, self.current_user)
        if not bot:
            ui.notify('Bot not found', type='negative')
            return

        dialog = RacetimeBotOrganizationsDialog(
            bot=bot,
            current_user=self.current_user,
            on_save=self._refresh_bots
        )
        await dialog.show()

    async def _confirm_delete_bot(self, bot_id: int):
        """Confirm and delete a bot."""
        bot = await self.bot_service.get_bot_by_id(bot_id, self.current_user)
        if not bot:
            ui.notify('Bot not found', type='negative')
            return

        # Check organization assignments
        orgs = await self.bot_service.get_organizations_for_bot(bot_id, self.current_user)

        async def do_delete():
            success = await self.bot_service.delete_bot(bot_id, self.current_user)
            if success:
                ui.notify(f'Bot "{bot.name}" deleted successfully', type='positive')
                await self._refresh_bots()
            else:
                ui.notify('Failed to delete bot (permission denied)', type='negative')

        # Build confirmation message
        message = f'Are you sure you want to delete bot "{bot.name}" ({bot.category})?'
        if orgs:
            message += f'\n\nThis bot is assigned to {len(orgs)} organization(s). Deleting will remove all assignments.'

        # Show confirmation dialog
        dialog = ConfirmDialog(
            title='Confirm Delete',
            message=message,
            on_confirm=do_delete
        )
        await dialog.show()

