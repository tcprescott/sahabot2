"""
My Settings View for tournaments.

Allows users to manage their tournament-related settings.
"""

from __future__ import annotations
from nicegui import ui
from models import Organization, User
from components.card import Card
from components.datetime_label import DateTimeLabel
from application.services.tournament_service import TournamentService


class MySettingsView:
    """View for managing user's tournament settings."""

    def __init__(
        self,
        user: User,
        organization: Organization,
        service: TournamentService
    ):
        """Initialize the my settings view."""
        self.user = user
        self.organization = organization
        self.service = service
        self.container = None

    async def render(self) -> None:
        """Render the my settings view."""
        self.container = ui.column().classes('w-full')
        with self.container:
            await self._render_content()

    async def _refresh(self) -> None:
        """Refresh the view by clearing and re-rendering content."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _render_content(self) -> None:
        """Render the settings content."""
        # Get all tournaments in the organization
        all_tournaments = await self.service.list_all_org_tournaments(self.organization.id)
        
        # Get tournaments the user is registered for
        tournament_registrations = await self.service.list_user_tournament_registrations(
            self.organization.id,
            self.user.id
        )
        registered_tournament_ids = {reg.tournament_id for reg in tournament_registrations}
        
        with Card.create(title='My Tournament Settings'):
            with ui.element('div').classes('mb-4'):
                ui.label('Manage your tournament preferences and registrations')
            
            # Available Tournaments Section
            with ui.element('div').classes('mb-6'):
                ui.label('Available Tournaments').classes('text-lg font-bold mb-2')
                
                if not all_tournaments:
                    with ui.element('div').classes('text-center mt-4'):
                        ui.icon('emoji_events').classes('text-secondary icon-large')
                        ui.label('No tournaments available').classes('text-secondary')
                else:
                    with ui.element('div').classes('flex flex-col gap-2'):
                        for tournament in all_tournaments:
                            is_registered = tournament.id in registered_tournament_ids
                            
                            with ui.element('div').classes('card'):
                                with ui.element('div').classes('card-body'):
                                    with ui.row().classes('w-full items-center justify-between'):
                                        with ui.column().classes('gap-1'):
                                            ui.label(tournament.name).classes('font-bold')
                                            if tournament.description:
                                                ui.label(tournament.description).classes('text-sm text-secondary')
                                        
                                        with ui.row().classes('items-center gap-2'):
                                            # Status badge
                                            if tournament.is_active:
                                                ui.label('Active').classes('badge badge-success')
                                            else:
                                                ui.label('Inactive').classes('badge badge-secondary')
                                            
                                            # Register/Unregister button
                                            if is_registered:
                                                async def unregister(t_id=tournament.id):
                                                    success = await self.service.unregister_user_from_tournament(
                                                        self.organization.id,
                                                        t_id,
                                                        self.user.id
                                                    )
                                                    if success:
                                                        ui.notify('Successfully unregistered from tournament', type='positive')
                                                        await self._refresh()
                                                    else:
                                                        ui.notify('Failed to unregister', type='negative')
                                                
                                                ui.button('Unregister', icon='remove_circle', on_click=unregister).classes('btn').props('color=negative')
                                            else:
                                                async def register(t_id=tournament.id):
                                                    result = await self.service.register_user_for_tournament(
                                                        self.organization.id,
                                                        t_id,
                                                        self.user.id
                                                    )
                                                    if result:
                                                        ui.notify('Successfully registered for tournament', type='positive')
                                                        await self._refresh()
                                                    else:
                                                        ui.notify('Failed to register', type='negative')
                                                
                                                ui.button('Register', icon='add_circle', on_click=register).classes('btn').props('color=positive')
            
            # My Registrations Section
            with ui.element('div').classes('mb-6'):
                ui.label('My Registrations').classes('text-lg font-bold mb-2')
                
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
                                            with ui.row().classes('items-center gap-1'):
                                                ui.label('Registered:').classes('text-sm')
                                                DateTimeLabel.date(reg.created_at, classes='text-sm')
                                        
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
