"""
Racer verification configuration view.

Allows organization admins to create and manage racer verification
configurations that grant Discord roles based on RaceTime race completion.
"""

import logging
from nicegui import ui
from components.data_table import ResponsiveTable, TableColumn
from components.dialogs.organization.racer_verification_dialog import RacerVerificationDialog
from application.services.racer_verification_service import RacerVerificationService
from application.services.discord_guild_service import DiscordGuildService

logger = logging.getLogger(__name__)


class RacerVerificationConfigView:
    """View for managing racer verification configurations."""

    def __init__(self, organization_id: int, user):
        """
        Initialize view.

        Args:
            organization_id: Organization ID
            user: Current user
        """
        self.organization_id = organization_id
        self.user = user
        self.service = RacerVerificationService()
        self.guild_service = DiscordGuildService()

        # State
        self.verifications = []
        self.table = None

    async def render(self):
        """Render the racer verification configuration view."""
        # Fetch verifications
        self.verifications = await self.service.get_verifications_for_organization(
            current_user=self.user,
            organization_id=self.organization_id
        )

        with ui.element('div').classes('card'):
            # Header
            with ui.element('div').classes('card-header'):
                with ui.row().classes('w-full items-center justify-between'):
                    ui.label('Racer Verification Roles').classes('text-lg font-bold')
                    ui.button(
                        icon='add',
                        on_click=self._open_create_dialog
                    ).classes('btn btn-primary').tooltip('Create Verification')

            # Body
            with ui.element('div').classes('card-body'):
                if not self.verifications:
                    ui.label('No racer verifications configured.').classes('text-secondary')
                    ui.label(
                        'Create a verification to automatically grant Discord roles '
                        'to users who have completed a minimum number of races.'
                    ).classes('text-secondary text-sm mt-2')
                else:
                    # Table
                    columns = [
                        TableColumn(
                            label='Categories',
                            cell_render=self._render_categories,
                        ),
                        TableColumn(
                            label='Role',
                            cell_render=self._render_role,
                        ),
                        TableColumn(
                            label='Minimum Races',
                            cell_render=lambda row: ui.label(str(row.minimum_races)),
                        ),
                        TableColumn(
                            label='Rules',
                            cell_render=self._render_rules,
                        ),
                        TableColumn(
                            label='Actions',
                            cell_render=self._render_actions,
                        ),
                    ]

                    self.table = ResponsiveTable(
                        columns=columns,
                        rows=self.verifications
                    )
                    await self.table.render()

    def _render_categories(self, row):
        """Render categories list."""
        if row.categories:
            ui.label(', '.join(row.categories)).classes('text-sm')
        else:
            ui.label('None').classes('text-secondary text-sm')

    def _render_role(self, row):
        """Render role information."""
        ui.label(row.role_name).classes('font-medium')

    def _render_rules(self, row):
        """Render verification rules."""
        rules = []
        if row.count_forfeits:
            rules.append('Forfeits')
        if row.count_dq:
            rules.append('DQs')

        if rules:
            ui.label(f"Count: {', '.join(rules)}").classes('text-sm text-secondary')
        else:
            ui.label('Finished only').classes('text-sm text-secondary')

    def _render_actions(self, row):
        """Render action buttons."""
        with ui.row().classes('gap-1'):
            ui.button(
                icon='edit',
                on_click=lambda r=row: self._open_edit_dialog(r)
            ).classes('btn btn-sm').tooltip('Edit')
            ui.button(
                icon='delete',
                on_click=lambda r=row: self._confirm_delete(r)
            ).classes('btn btn-sm').props('color=negative').tooltip('Delete')

    async def _open_create_dialog(self):
        """Open dialog to create new verification."""
        dialog = RacerVerificationDialog(
            organization_id=self.organization_id,
            verification=None,
            on_save=self._refresh
        )
        await dialog.show()

    async def _open_edit_dialog(self, verification):
        """Open dialog to edit verification."""
        dialog = RacerVerificationDialog(
            organization_id=self.organization_id,
            verification=verification,
            on_save=self._refresh
        )
        await dialog.show()

    async def _confirm_delete(self, verification):
        """Confirm and delete verification."""
        from components.dialogs.common.tournament_dialogs import ConfirmDialog

        dialog = ConfirmDialog(
            title='Delete Racer Verification',
            message=f'Are you sure you want to delete the racer verification for {verification.category}?',
            on_confirm=lambda: self._delete_verification(verification)
        )
        await dialog.show()

    async def _delete_verification(self, verification):
        """Delete verification."""
        result = await self.service.delete_verification(
            current_user=self.user,
            verification_id=verification.id
        )

        if result:
            ui.notify('Racer verification deleted', type='positive')
            await self._refresh()
        else:
            ui.notify('Failed to delete racer verification', type='negative')

    async def _refresh(self):
        """Refresh the view."""
        # Navigate to refresh the page
        ui.navigate.reload()
