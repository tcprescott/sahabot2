"""
Tournament RaceTime Settings View.

Allows tournament managers to configure RaceTime room opening settings using race room profiles.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.organizations import Organization
from models.async_tournament import AsyncTournament


class TournamentRacetimeSettingsView:
    """View for managing tournament-specific RaceTime settings."""

    def __init__(self, user: User, organization: Organization, tournament: AsyncTournament):
        """
        Initialize the RaceTime settings view.

        Args:
            user: Current user
            organization: Tournament's organization
            tournament: Tournament to configure
        """
        self.user = user
        self.organization = organization
        self.tournament = tournament
        self.profiles = []
        self.selected_profile_id = None
        self.profile_select = None
        self.profile_preview_container = None

    async def render(self):
        """Render the RaceTime settings view."""
        # Load available profiles
        await self._load_profiles()

        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                with ui.row().classes('items-center justify-between w-full'):
                    ui.label('RaceTime Room Settings').classes('text-xl font-bold')
                    ui.button('Manage Profiles', icon='tune', on_click=self._manage_profiles).classes('btn')

            with ui.element('div').classes('card-body'):
                ui.label('Configure how RaceTime rooms are created for this tournament').classes('text-sm text-grey mb-4')

                # Basic Settings Section
                ui.label('Basic Settings').classes('text-lg font-bold mb-3')

                # Auto-create toggle
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Auto-create rooms:').classes('w-64')
                    auto_create_toggle = ui.switch(value=self.tournament.racetime_auto_create_rooms or False)
                    ui.label('Automatically create RaceTime rooms when matches are scheduled').classes('text-sm text-grey')

                # Room opening time
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Open room (minutes before):').classes('w-64')
                    open_minutes = ui.number(
                        value=self.tournament.room_open_minutes_before or 15,
                        min=5,
                        max=120,
                        step=5
                    ).classes('w-32')
                    ui.label('How long before scheduled time to open the room').classes('text-sm text-grey')

                # Require RaceTime link
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Require RaceTime account:').classes('w-64')
                    require_link_toggle = ui.switch(value=self.tournament.require_racetime_link or False)
                    ui.label('Players must have RaceTime accounts linked').classes('text-sm text-grey')

                # Default goal
                ui.label('Default race goal:').classes('font-bold mb-2')
                default_goal = ui.textarea(
                    value=self.tournament.racetime_default_goal or '',
                    placeholder='e.g., Beat the game'
                ).classes('w-full mb-4')

                ui.separator()

                # Race Room Profile Section
                ui.label('Race Room Configuration Profile').classes('text-lg font-bold mt-4 mb-3')
                ui.label('Select a profile to configure room settings (start delay, time limit, chat permissions, etc.)').classes('text-sm text-grey mb-4')

                # Profile selection
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Profile:').classes('w-64')
                    profile_options = {
                        None: 'Use defaults (no profile)',
                        **{p.id: f"{p.name}{' (Default)' if p.is_default else ''}" for p in self.profiles}
                    }
                    self.profile_select = ui.select(
                        options=profile_options,
                        value=self.tournament.race_room_profile_id,
                        on_change=self._on_profile_change
                    ).classes('w-96')

                # Profile preview (shows settings when profile selected)
                self.profile_preview_container = ui.element('div').classes('mt-4')
                await self._render_profile_preview()

                ui.separator()

                # Save button
                with ui.row().classes('justify-end mt-4'):
                    ui.button('Save Settings', on_click=lambda: self._save_settings(
                        auto_create_toggle.value,
                        open_minutes.value,
                        require_link_toggle.value,
                        default_goal.value,
                    )).classes('btn').props('color=positive')

    async def _load_profiles(self):
        """Load available race room profiles for the organization."""
        from application.services.race_room_profile_service import RaceRoomProfileService

        service = RaceRoomProfileService()
        self.profiles = await service.list_profiles(self.user, self.organization.id)

        # Set selected profile to tournament's current profile
        if self.tournament.race_room_profile_id:
            await self.tournament.fetch_related('race_room_profile')
            self.selected_profile_id = self.tournament.race_room_profile_id

    async def _on_profile_change(self, e):
        """Handle profile selection change."""
        self.selected_profile_id = e.value
        await self._render_profile_preview()

    async def _render_profile_preview(self):
        """Render preview of selected profile's settings."""
        self.profile_preview_container.clear()

        with self.profile_preview_container:
            if self.selected_profile_id is None:
                # Show defaults
                with ui.element('div').classes('p-4 rounded bg-grey-2'):
                    ui.label('Default Settings (No Profile)').classes('font-bold mb-2')
                    ui.label('Start delay: 15 seconds').classes('text-sm')
                    ui.label('Time limit: 24 hours').classes('text-sm')
                    ui.label('Streaming required: No').classes('text-sm')
                    ui.label('Auto-start: Yes').classes('text-sm')
                    ui.label('All chat permissions: Enabled').classes('text-sm')
            else:
                # Find and show selected profile
                profile = next((p for p in self.profiles if p.id == self.selected_profile_id), None)
                if profile:
                    with ui.element('div').classes('p-4 rounded bg-grey-2'):
                        ui.label(f'Profile: {profile.name}').classes('font-bold mb-2')
                        if profile.description:
                            ui.label(profile.description).classes('text-sm text-grey mb-2')

                        # Display settings in a grid
                        with ui.element('div').classes('grid grid-cols-2 gap-2 mt-3'):
                            ui.label(f'Start delay: {profile.start_delay}s').classes('text-sm')
                            ui.label(f'Time limit: {profile.time_limit}h').classes('text-sm')
                            ui.label(f'Streaming required: {"Yes" if profile.streaming_required else "No"}').classes('text-sm')
                            ui.label(f'Auto-start: {"Yes" if profile.auto_start else "No"}').classes('text-sm')
                            ui.label(f'Allow comments: {"Yes" if profile.allow_comments else "No"}').classes('text-sm')
                            ui.label(f'Hide comments: {"Yes" if profile.hide_comments else "No"}').classes('text-sm')
                            ui.label(f'Pre-race chat: {"Yes" if profile.allow_prerace_chat else "No"}').classes('text-sm')
                            ui.label(f'Mid-race chat: {"Yes" if profile.allow_midrace_chat else "No"}').classes('text-sm')
                            ui.label(f'Non-entrant chat: {"Yes" if profile.allow_non_entrant_chat else "No"}').classes('text-sm')

    async def _manage_profiles(self):
        """Open dialog to manage race room profiles."""
        from views.organization.race_room_profile_management import RaceRoomProfileManagementView

        # Create a dialog to show the profile management view
        with ui.dialog() as dialog:
            with ui.element('div').classes('card dialog-card-xl'):
                # Header
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('tune').classes('icon-medium')
                            ui.label('Manage Race Room Profiles').classes('text-xl font-bold')
                        ui.button(icon='close', on_click=dialog.close).props('flat round dense')

                # Body with profile management view
                with ui.element('div').classes('card-body'):
                    view = RaceRoomProfileManagementView(self.user, self.organization)
                    await view.render()

        dialog.open()

        # Reload profiles when dialog closes
        async def on_close():
            await self._load_profiles()
            if self.profile_select:
                self.profile_select.update()
            await self._render_profile_preview()

        dialog.on('close', on_close)

    async def _save_settings(
        self,
        auto_create: bool,
        open_minutes: float,
        require_link: bool,
        default_goal: str,
    ):
        """
        Save RaceTime settings.

        Args:
            auto_create: Whether to auto-create rooms
            open_minutes: Minutes before scheduled time to open room
            require_link: Whether to require RaceTime link
            default_goal: Default race goal text
        """
        from application.services.tournament_service import TournamentService

        service = TournamentService()
        await service.update_tournament(
            user=self.user,
            organization_id=self.organization.id,
            tournament_id=self.tournament.id,
            racetime_auto_create=auto_create,
            room_open_minutes=int(open_minutes),
            require_racetime_link=require_link,
            racetime_default_goal=default_goal,
            race_room_profile_id=self.selected_profile_id,
        )

        ui.notify('RaceTime settings saved successfully!', type='positive')
        # Reload tournament
        await self.tournament.refresh_from_db()
        await self._load_profiles()
        if self.profile_select:
            self.profile_select.value = self.tournament.race_room_profile_id
