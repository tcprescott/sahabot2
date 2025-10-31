"""
My Settings View for tournaments.

Allows users to manage their tournament-related settings.
"""

from __future__ import annotations
from nicegui import ui
from models import Organization, User
from components.card import Card
from application.services.tournament_service import TournamentService


class MySettingsView:
    """View for managing user's tournament settings."""

    def __init__(self, organization: Organization, user: User) -> None:
        self.organization = organization
        self.user = user
        self.service = TournamentService()

    async def render(self) -> None:
        """Render the my settings view."""
        # Get tournaments the user is registered for via service
        tournament_registrations = await self.service.list_user_tournament_registrations(
            self.organization.id,
            self.user.id
        )
        
        with Card.create(title='My Tournament Settings'):
            with ui.element('div').classes('mb-4'):
                ui.label('Manage your tournament preferences and registrations')
            
            # Tournament Registrations Section
            with ui.element('div').classes('mb-6'):
                ui.label('Tournament Registrations').classes('text-lg font-bold mb-2')
                
                if not tournament_registrations:
                    with ui.element('div').classes('text-center mt-4'):
                        ui.icon('emoji_events').classes('text-secondary icon-large')
                        ui.label('Not registered for any tournaments').classes('text-secondary')
                        ui.label('Contact a tournament organizer to register').classes('text-secondary text-sm')
                else:
                    with ui.element('div').classes('flex flex-col gap-2'):
                        for reg in tournament_registrations:
                            tournament = reg.tournament
                            with ui.element('div').classes('card'):
                                with ui.element('div').classes('card-body'):
                                    with ui.row().classes('w-full items-center justify-between'):
                                        with ui.column().classes('gap-1'):
                                            ui.label(tournament.name).classes('font-bold')
                                            if tournament.description:
                                                ui.label(tournament.description).classes('text-sm text-secondary')
                                            ui.label(f'Registered: {reg.created_at.strftime("%Y-%m-%d")}').classes('text-sm')
                                        
                                        # Status badge
                                        if tournament.is_active:
                                            ui.label('Active').classes('badge badge-success')
                                        else:
                                            ui.label('Inactive').classes('badge badge-secondary')
            
            # Placeholder for future settings
            with ui.element('div').classes('mt-6'):
                ui.label('Notification Preferences').classes('text-lg font-bold mb-2')
                ui.label('Coming soon: Configure notifications for match reminders, check-ins, and results').classes('text-secondary text-sm')
            
            with ui.element('div').classes('mt-6'):
                ui.label('Display Preferences').classes('text-lg font-bold mb-2')
                ui.label('Coming soon: Customize how matches and schedules are displayed').classes('text-secondary text-sm')
