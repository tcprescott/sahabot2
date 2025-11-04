"""
RaceTime Bot administration view.

Provides interface for managing RaceTime bot configurations and organization assignments.
"""

from nicegui import ui
from components.data_table import ResponsiveTable, TableColumn
from models import User, RacetimeBot, Organization
from application.services.racetime_bot_service import RacetimeBotService
from application.services.organization_service import OrganizationService
from components.dialogs import RacetimeBotEditDialog, RacetimeBotAddDialog, RacetimeBotOrganizationsDialog
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

        # Define columns
        columns = [
            TableColumn(name='category', label='Category', field='category', sortable=True, mobile_primary=True),
            TableColumn(name='name', label='Name', field='name', sortable=True),
            TableColumn(name='client_id', label='Client ID', field='client_id', mobile_hide=True),
            TableColumn(name='status', label='Status', field='status', align='center'),
            TableColumn(name='actions', label='Actions', field='actions', align='center', sortable=False),
        ]

        # Prepare rows
        rows = []
        for bot in self.bots:
            # Get organization count
            orgs = await self.bot_service.get_organizations_for_bot(bot.id, self.current_user)

            rows.append({
                'id': bot.id,
                'category': bot.category,
                'name': bot.name,
                'client_id': bot.client_id[:20] + '...' if len(bot.client_id) > 20 else bot.client_id,
                'status': bot,  # Pass bot object for custom rendering
                'actions': bot,  # Pass bot object for action buttons
                '_org_count': len(orgs),
            })

        # Create table
        table = ResponsiveTable(
            columns=columns,
            rows=rows,
            row_key='id',
        )

        # Custom cell rendering for status
        table.add_slot(
            'body-cell-status',
            '''
            <q-td :props="props">
                <div style="display: flex; flex-direction: column; gap: 4px;">
                    <div>
                        <q-badge v-if="props.row.status.is_active" color="positive" style="margin-right: 4px;">Active</q-badge>
                        <q-badge v-else color="grey" style="margin-right: 4px;">Inactive</q-badge>
                    </div>
                    <div v-if="props.row.status.status === 0">
                        <q-badge color="grey-7">
                            <q-icon name="help" size="xs" style="margin-right: 4px;"/>
                            Unknown
                        </q-badge>
                    </div>
                    <div v-else-if="props.row.status.status === 1">
                        <q-badge color="positive">
                            <q-icon name="check_circle" size="xs" style="margin-right: 4px;"/>
                            Connected
                        </q-badge>
                    </div>
                    <div v-else-if="props.row.status.status === 2">
                        <q-badge color="negative">
                            <q-icon name="key_off" size="xs" style="margin-right: 4px;"/>
                            Auth Failed
                            <q-tooltip v-if="props.row.status.status_message" max-width="300px">
                                {{ props.row.status.status_message }}
                            </q-tooltip>
                        </q-badge>
                    </div>
                    <div v-else-if="props.row.status.status === 3">
                        <q-badge color="negative">
                            <q-icon name="error" size="xs" style="margin-right: 4px;"/>
                            Connection Error
                            <q-tooltip v-if="props.row.status.status_message" max-width="300px">
                                {{ props.row.status.status_message }}
                            </q-tooltip>
                        </q-badge>
                    </div>
                    <div v-else-if="props.row.status.status === 4">
                        <q-badge color="warning">
                            <q-icon name="cloud_off" size="xs" style="margin-right: 4px;"/>
                            Disconnected
                        </q-badge>
                    </div>
                    <div v-if="props.row.status.last_connected_at" class="text-caption text-grey-7" style="font-size: 0.7rem;">
                        Last: {{ new Date(props.row.status.last_connected_at).toLocaleString() }}
                    </div>
                </div>
            </q-td>
            '''
        )

        # Custom cell rendering for actions
        def render_actions_cell():
            return '''
            <q-td :props="props" auto-width>
                <q-btn flat round dense icon="edit" color="primary" size="sm"
                       @click="$parent.$emit('edit-bot', props.row.id)">
                    <q-tooltip>Edit Bot</q-tooltip>
                </q-btn>
                <q-btn flat round dense icon="groups" color="primary" size="sm"
                       @click="$parent.$emit('manage-orgs', props.row.id)">
                    <q-tooltip>Manage Organizations ({{ props.row._org_count }})</q-tooltip>
                </q-btn>
                <q-btn flat round dense icon="delete" color="negative" size="sm"
                       @click="$parent.$emit('delete-bot', props.row.id)">
                    <q-tooltip>Delete Bot</q-tooltip>
                </q-btn>
            </q-td>
            '''

        table.add_slot('body-cell-actions', render_actions_cell())

        # Event handlers
        table.on('edit-bot', lambda e: self._open_edit_bot(e.args))
        table.on('manage-orgs', lambda e: self._open_manage_organizations(e.args))
        table.on('delete-bot', lambda e: self._confirm_delete_bot(e.args))

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

        # Show confirmation dialog
        with ui.dialog() as dialog:
            with ui.element('div').classes('card dialog-card'):
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('warning', color='negative').classes('icon-medium')
                            ui.label('Confirm Delete').classes('text-xl font-bold')
                        ui.button(icon='close', on_click=dialog.close).props('flat round dense')

                with ui.element('div').classes('card-body'):
                    ui.label(f'Are you sure you want to delete bot "{bot.name}" ({bot.category})?').classes('mb-4')

                    if orgs:
                        with ui.row().classes('items-center gap-2 p-3 rounded bg-warning text-white mb-4'):
                            ui.icon('info')
                            ui.label(f'This bot is assigned to {len(orgs)} organization(s). Deleting will remove all assignments.')

                    with ui.row().classes('justify-end gap-2'):
                        ui.button('Cancel', on_click=dialog.close).classes('btn')
                        ui.button('Delete', on_click=lambda: [dialog.close(), do_delete()]).classes('btn').props('color=negative')

        dialog.open()
