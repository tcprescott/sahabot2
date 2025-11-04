"""
Tournament Settings View.

Manage general tournament settings.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.organizations import Organization
from models.async_tournament import AsyncTournament


class TournamentSettingsView:
    """View for managing general tournament settings."""

    def __init__(self, user: User, organization: Organization, tournament: AsyncTournament):
        """
        Initialize the settings view.

        Args:
            user: Current user
            organization: Tournament's organization
            tournament: Tournament to manage
        """
        self.user = user
        self.organization = organization
        self.tournament = tournament

    async def render(self):
        """Render the tournament settings view."""
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                ui.label('Tournament Settings').classes('text-xl font-bold')

            with ui.element('div').classes('card-body'):
                ui.label('Configure general tournament settings').classes('text-sm text-grey mb-4')

                # Basic settings
                ui.label('Name:').classes('font-bold mb-2')
                name_input = ui.input(value=self.tournament.name).classes('w-full mb-4')

                ui.label('Description:').classes('font-bold mb-2')
                description_input = ui.textarea(
                    value=self.tournament.description or ''
                ).classes('w-full mb-4')

                # Status
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Active:')
                    active_toggle = ui.switch(value=self.tournament.is_active)

                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Enable Tracker:')
                    tracker_toggle = ui.switch(value=self.tournament.tracker_enabled or False)

                ui.separator()

                # Save button
                with ui.row().classes('justify-end mt-4'):
                    ui.button('Save Settings', on_click=lambda: self._save_settings(
                        name_input.value,
                        description_input.value,
                        active_toggle.value,
                        tracker_toggle.value
                    )).classes('btn').props('color=positive')

    async def _save_settings(
        self,
        name: str,
        description: str,
        is_active: bool,
        tracker_enabled: bool
    ):
        """
        Save tournament settings.

        Args:
            name: Tournament name
            description: Tournament description
            is_active: Whether tournament is active
            tracker_enabled: Whether tracker is enabled
        """
        from application.services.tournament_service import TournamentService

        service = TournamentService()
        await service.update_tournament(
            user=self.user,
            organization_id=self.organization.id,
            tournament_id=self.tournament.id,
            name=name,
            description=description,
            is_active=is_active,
            tracker_enabled=tracker_enabled
        )

        ui.notify('Tournament settings saved successfully', type='positive')
        # Refresh the page to show updated tournament name in header
        ui.navigate.reload()
