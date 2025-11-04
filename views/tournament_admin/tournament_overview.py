"""
Tournament Overview View.

Shows tournament dashboard with stats and quick actions.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.organizations import Organization
from models.async_tournament import AsyncTournament


class TournamentOverviewView:
    """View for tournament overview dashboard."""

    def __init__(self, user: User, organization: Organization, tournament: AsyncTournament):
        """
        Initialize the overview view.

        Args:
            user: Current user
            organization: Tournament's organization
            tournament: Tournament to display
        """
        self.user = user
        self.organization = organization
        self.tournament = tournament

    async def render(self):
        """Render the tournament overview."""
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                ui.label('Tournament Overview').classes('text-xl font-bold')

            with ui.element('div').classes('card-body'):
                # Tournament info
                with ui.row().classes('gap-4 mb-4'):
                    with ui.column().classes('flex-1'):
                        ui.label('Name:').classes('font-bold')
                        ui.label(self.tournament.name)

                    with ui.column().classes('flex-1'):
                        ui.label('Status:').classes('font-bold')
                        status_text = 'Active' if self.tournament.is_active else 'Inactive'
                        ui.label(status_text)

                ui.separator()

                # Description
                ui.label('Description:').classes('font-bold mt-4 mb-2')
                ui.label(self.tournament.description or 'No description provided').classes('text-sm')

                ui.separator()

                # Quick stats (placeholders for future implementation)
                ui.label('Quick Stats').classes('text-lg font-bold mt-4 mb-2')
                with ui.row().classes('gap-4'):
                    with ui.element('div').classes('card flex-1'):
                        with ui.element('div').classes('card-body text-center'):
                            ui.label('0').classes('text-3xl font-bold')
                            ui.label('Total Matches').classes('text-sm text-grey')

                    with ui.element('div').classes('card flex-1'):
                        with ui.element('div').classes('card-body text-center'):
                            ui.label('0').classes('text-3xl font-bold')
                            ui.label('Active Players').classes('text-sm text-grey')

                    with ui.element('div').classes('card flex-1'):
                        with ui.element('div').classes('card-body text-center'):
                            ui.label('0').classes('text-3xl font-bold')
                            ui.label('Completed Races').classes('text-sm text-grey')
