"""
Tournament admin view for managing racetime chat commands at the TOURNAMENT level.

Tournament managers can configure custom chat commands specific to their tournament.
"""

from nicegui import ui
from components.data_table import ResponsiveTable, TableColumn
from components.dialogs import RacetimeChatCommandDialog, ConfirmDialog
from models import User, RacetimeChatCommand, Organization, Tournament, CommandResponseType
from application.services.racetime.racetime_chat_command_service import RacetimeChatCommandService
import logging

logger = logging.getLogger(__name__)


class TournamentRacetimeChatCommandsView:
    """Tournament-scoped racetime chat commands view."""

    def __init__(self, current_user: User, org: Organization, tournament: Tournament):
        """
        Initialize the tournament racetime chat commands view.

        Args:
            current_user: Currently authenticated user
            org: Organization context
            tournament: Tournament context
        """
        self.current_user = current_user
        self.org = org
        self.tournament = tournament
        self.command_service = RacetimeChatCommandService()

        # State
        self.commands: list[RacetimeChatCommand] = []
        self.search_query = ""
        self.include_disabled = True
        self.table_container = None

    async def render(self):
        """Render the tournament racetime chat commands interface."""
        with ui.column().classes('full-width gap-md'):
            # Header section
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-header'):
                    ui.label('Tournament Chat Commands').classes('text-xl font-bold')
                with ui.element('div').classes('card-body'):
                    ui.label(
                        f'Configure custom chat commands for {self.tournament.name}. '
                        'These commands are only available in racetime rooms for this tournament.'
                    ).classes('text-secondary')

            # Filters and actions
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-body'):
                    with ui.row().classes('w-full gap-md items-end'):
                        # Search
                        ui.input(
                            label='Search',
                            placeholder='Search by command name...',
                            on_change=lambda e: self._on_search_change(e.value)
                        ).classes('flex-grow').props('outlined dense clearable') \
                            .props('prepend-icon=search')

                        # Filters
                        ui.checkbox(
                            'Show disabled',
                            value=self.include_disabled,
                            on_change=lambda e: self._on_filter_change(e.value)
                        )

                        # Add button
                        ui.button(
                            'Add Command',
                            icon='add',
                            on_click=self._add_command
                        ).classes('btn btn-primary').props('no-caps')

            # Commands table container
            self.table_container = ui.element('div').classes('full-width')

            # Load initial data
            await self._load_commands()

    async def _load_commands(self):
        """Load and display commands for the tournament."""
        # Fetch commands
        self.commands = await self.command_service.get_commands_for_tournament(
            self.current_user,
            self.tournament.id,
        )

        # Apply filters
        filtered_commands = self.commands

        # Search filter
        if self.search_query:
            query_lower = self.search_query.lower()
            filtered_commands = [
                cmd for cmd in filtered_commands
                if query_lower in cmd.command.lower()
            ]

        # Enabled/disabled filter
        if not self.include_disabled:
            filtered_commands = [cmd for cmd in filtered_commands if cmd.is_enabled]

        # Render table
        await self._render_table(filtered_commands)

    async def _render_table(self, commands: list[RacetimeChatCommand]):
        """Render the commands table."""
        if not self.table_container:
            return

        self.table_container.clear()

        if not commands:
            with self.table_container:
                with ui.element('div').classes('card'):
                    with ui.element('div').classes('card-body text-center'):
                        ui.icon('chat').classes('icon-large text-secondary')
                        ui.label('No custom commands for this tournament').classes('text-secondary')
                        ui.label('Add a command to customize the experience for participants').classes('text-sm text-secondary')
            return

        with self.table_container:
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-body'):
                    # Custom cell renderers
                    def render_command(row):
                        with ui.row().classes('items-center gap-2'):
                            ui.label('!').classes('font-mono text-bold')
                            ui.label(row['command']).classes('font-mono')
                            if row['require_linked_account']:
                                ui.icon('link').classes('text-sm').props('title="Requires linked account"')

                    def render_type(row):
                        if row['response_type'] == CommandResponseType.TEXT:
                            with ui.row().classes('items-center gap-1'):
                                ui.icon('description', size='sm')
                                ui.label('Static')
                        else:
                            with ui.row().classes('items-center gap-1'):
                                ui.icon('code', size='sm')
                                ui.label('Dynamic')

                    def render_response(row):
                        if row['response_type'] == CommandResponseType.TEXT:
                            text = row['response_text'] or ''
                            preview = text[:50] + '...' if len(text) > 50 else text
                            ui.label(preview).classes('text-sm')
                        else:
                            handler = row['handler_name'] or 'N/A'
                            with ui.row().classes('items-center gap-1'):
                                ui.icon('functions', size='sm')
                                ui.label(handler).classes('font-mono text-sm')

                    def render_cooldown(row):
                        cooldown = row['cooldown_seconds']
                        if cooldown > 0:
                            ui.label(f'{cooldown}s').classes('badge badge-info')
                        else:
                            ui.label('None').classes('text-secondary text-sm')

                    def render_status(row):
                        if row['is_enabled']:
                            ui.label('Enabled').classes('badge badge-success')
                        else:
                            ui.label('Disabled').classes('badge badge-warning')

                    def render_actions(row):
                        with ui.row().classes('gap-1'):
                            ui.button(
                                icon='edit',
                                on_click=lambda r=row: self._edit_command(r['id'])
                            ).props('flat dense round size=sm').classes('text-primary')
                            ui.button(
                                icon='delete',
                                on_click=lambda r=row: self._delete_command(r['id'], r['command'])
                            ).props('flat dense round size=sm').classes('text-negative')

                    # Define table columns with renderers
                    columns = [
                        TableColumn(label='Command', key='command', cell_render=render_command),
                        TableColumn(label='Type', key='response_type', cell_render=render_type),
                        TableColumn(label='Response', key='response', cell_render=render_response),
                        TableColumn(label='Cooldown', key='cooldown', cell_render=render_cooldown),
                        TableColumn(label='Status', key='status', cell_render=render_status),
                        TableColumn(label='Actions', key='actions', cell_render=render_actions),
                    ]

                    # Prepare rows
                    rows = []
                    for cmd in commands:
                        rows.append({
                            'id': cmd.id,
                            'command': cmd.command,
                            'response_type': cmd.response_type,
                            'response_text': cmd.response_text,
                            'handler_name': cmd.handler_name,
                            'cooldown_seconds': cmd.cooldown_seconds,
                            'require_linked_account': cmd.require_linked_account,
                            'is_enabled': cmd.is_enabled,
                            'created_at': cmd.created_at,
                        })

                    # Create table
                    table = ResponsiveTable(
                        columns=columns,
                        rows=rows,
                    )
                    await table.render()

    async def _on_search_change(self, query: str):
        """Handle search input change."""
        self.search_query = query
        await self._load_commands()

    async def _on_filter_change(self, include_disabled: bool):
        """Handle filter checkbox change."""
        self.include_disabled = include_disabled
        await self._load_commands()

    async def _add_command(self):
        """Show add command dialog."""
        dialog = RacetimeChatCommandDialog(
            tournament_id=self.tournament.id,
            on_save=self._load_commands
        )
        await dialog.show()

    async def _edit_command(self, command_id: int):
        """Show edit command dialog."""
        # Find command
        command = next((cmd for cmd in self.commands if cmd.id == command_id), None)
        if not command:
            ui.notify('Command not found', color='negative')
            return

        dialog = RacetimeChatCommandDialog(
            command=command,
            on_save=self._load_commands
        )
        await dialog.show()

    async def _delete_command(self, command_id: int, command_name: str):
        """Show delete confirmation dialog."""
        async def do_delete():
            try:
                await self.command_service.delete_command(self.current_user, command_id)
                ui.notify(f'Command !{command_name} deleted', color='positive')
                await self._load_commands()
            except Exception as e:
                ui.notify(f'Error deleting command: {str(e)}', color='negative')
                logger.error("Error deleting command %s: %s", command_id, e, exc_info=True)

        dialog = ConfirmDialog(
            title='Delete Chat Command',
            message=f'Are you sure you want to delete the command !{command_name}? This action cannot be undone.',
            on_confirm=do_delete,
        )
        await dialog.show()
