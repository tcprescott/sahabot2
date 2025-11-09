"""
Tournament RaceTime Settings View.

Allows tournament managers to configure RaceTime room opening settings using race room profiles.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.organizations import Organization
from models.match_schedule import Tournament


class TournamentRacetimeSettingsView:
    """View for managing tournament-specific RaceTime settings."""

    def __init__(self, user: User, organization: Organization, tournament: Tournament):
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
        self.bots = []
        self.selected_profile_id = None
        self.profile_select = None
        self.profile_preview_container = None

    async def render(self):
        """Render the RaceTime settings view."""
        # Load available bots and profiles
        await self._load_bots()
        await self._load_profiles()

        # RaceTime Bots Card
        await self._render_bots_card()

        ui.separator().classes('my-4')

        # RaceTime Room Settings Card
        await self._render_room_settings_card()

        ui.separator().classes('my-4')

        # Race Room Profiles Management Card
        await self._render_profiles_card()

    async def _load_bots(self):
        """Load RaceTime bots available for this organization."""
        from application.services.racetime.racetime_bot_service import RacetimeBotService

        bot_service = RacetimeBotService()
        self.bots = await bot_service.get_bots_for_organization(self.organization.id, self.user)

    async def _render_bots_card(self):
        """Render card showing RaceTime bots assigned to this organization."""
        from components.data_table import ResponsiveTable, TableColumn

        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('smart_toy').classes('icon-medium')
                    ui.label('RaceTime Bots').classes('text-xl font-bold')

            with ui.element('div').classes('card-body'):
                if not self.bots:
                    with ui.element('div').classes('text-center p-4 text-secondary'):
                        ui.icon('info', size='2rem')
                        ui.label('No RaceTime bots assigned').classes('text-sm mt-2')
                        ui.label('Contact an administrator to assign bots to this organization').classes('text-xs')
                else:
                    ui.label(f'{len(self.bots)} bot{"s" if len(self.bots) != 1 else ""} assigned to this organization').classes('text-sm text-secondary mb-4')
                    
                    # Define table columns
                    columns = [
                        TableColumn(
                            label='Bot Name',
                            cell_render=lambda b: self._render_bot_name_cell(b)
                        ),
                        TableColumn(
                            label='Category',
                            cell_render=lambda b: self._render_bot_category_cell(b)
                        ),
                        TableColumn(
                            label='Status',
                            cell_render=lambda b: self._render_bot_status_cell(b)
                        ),
                    ]

                    # Render table
                    table = ResponsiveTable(columns=columns, rows=self.bots)
                    await table.render()

                    # Note about bot assignment
                    with ui.row().classes('items-center gap-2 mt-4 p-3 rounded bg-info-light'):
                        ui.icon('info', size='sm').classes('text-info')
                        ui.label('To assign additional bots to this organization, contact a global administrator.').classes('text-sm text-info')

    async def _render_room_settings_card(self):
        """Render the RaceTime room settings card."""
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                ui.label('RaceTime Room Settings').classes('text-xl font-bold')

            with ui.element('div').classes('card-body'):
                ui.label('Configure how RaceTime rooms are created for this tournament').classes('text-sm text-secondary mb-4')

                # Basic Settings Section
                ui.label('Basic Settings').classes('text-lg font-bold mb-3')

                # Auto-create toggle
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Auto-create rooms:').classes('w-64')
                    auto_create_toggle = ui.checkbox(value=self.tournament.racetime_auto_create_rooms or False)
                    ui.label('Automatically create RaceTime rooms when matches are scheduled').classes('text-sm text-secondary')

                # Bot selection
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('RaceTime Bot:').classes('w-64')
                    # Build bot options: None for "Select a bot", then all org bots
                    bot_options = {None: 'Select a bot...'}
                    for bot in self.bots:
                        status = ' (Healthy)' if bot.is_healthy() else ' (Unhealthy)'
                        bot_options[bot.id] = f"{bot.name} - {bot.category}{status}"
                    
                    bot_select = ui.select(
                        options=bot_options,
                        value=self.tournament.racetime_bot_id,
                        label='Bot to use for race rooms'
                    ).classes('w-96')
                    if not self.bots:
                        ui.label('No bots available. Contact administrator to assign bots to this organization.').classes('text-sm text-warning')
                    else:
                        ui.label('Select which bot will manage race rooms for this tournament').classes('text-sm text-secondary')

                # Room opening time
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Open room (minutes before):').classes('w-64')
                    open_minutes = ui.number(
                        value=self.tournament.room_open_minutes_before or 15,
                        min=5,
                        max=120,
                        step=5
                    ).classes('w-32')
                    ui.label('How long before scheduled time to open the room').classes('text-sm text-secondary')

                # Require RaceTime link
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Require RaceTime account:').classes('w-64')
                    require_link_toggle = ui.checkbox(value=self.tournament.require_racetime_link or False)
                    ui.label('Players must have RaceTime accounts linked').classes('text-sm text-secondary')

                # Default goal
                ui.label('Default race goal:').classes('font-bold mb-2')
                default_goal = ui.textarea(
                    value=self.tournament.racetime_default_goal or '',
                    placeholder='e.g., Beat the game'
                ).classes('w-full mb-4')

                ui.separator()

                # Race Room Profile Section
                ui.label('Race Room Configuration Profile').classes('text-lg font-bold mt-4 mb-3')
                ui.label('Select a profile to configure room settings (start delay, time limit, chat permissions, etc.)').classes('text-sm text-secondary mb-4')

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
                        bot_select.value,
                    )).classes('btn').props('color=positive')

    async def _render_profiles_card(self):
        """Render the race room profiles management card."""
        from views.organization.race_room_profile_management import RaceRoomProfileManagementView

        async def on_profiles_changed():
            """Callback when profiles are created/edited/deleted."""
            # Reload profiles
            await self._load_profiles()

            # Update dropdown options if it exists
            if self.profile_select:
                profile_options = {
                    None: 'Use defaults (no profile)',
                    **{p.id: f"{p.name}{' (Default)' if p.is_default else ''}" for p in self.profiles}
                }
                self.profile_select.set_options(profile_options)
                self.profile_select.update()

            # Refresh preview
            await self._render_profile_preview()

        view = RaceRoomProfileManagementView(
            self.user,
            self.organization,
            show_bots=False,
            on_change=on_profiles_changed
        )
        await view.render()

    def _render_bot_name_cell(self, bot):
        """Render the bot name cell."""
        with ui.row().classes('items-center gap-2'):
            ui.icon('smart_toy', size='sm')
            ui.label(bot.name).classes('font-bold')

    def _render_bot_category_cell(self, bot):
        """Render the bot category cell."""
        with ui.row().classes('items-center gap-2'):
            ui.icon('category', size='sm')
            ui.label(bot.category)

    def _render_bot_status_cell(self, bot):
        """Render the bot status cell."""
        with ui.row().classes('items-center gap-2'):
            ui.icon('circle', size='sm').classes(
                'text-positive' if bot.is_healthy() else 'text-warning'
            )
            ui.label(bot.get_status_display()).classes(
                'badge badge-success' if bot.is_healthy() else 'badge badge-warning'
            )

    async def _load_profiles(self):
        """Load available race room profiles for the organization."""
        from application.services.racetime.race_room_profile_service import RaceRoomProfileService

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
                with ui.element('div').classes('p-4 rounded border'):
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
                    with ui.element('div').classes('p-4 rounded border'):
                        ui.label(f'Profile: {profile.name}').classes('font-bold mb-2')
                        if profile.description:
                            ui.label(profile.description).classes('text-sm text-secondary mb-2')

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

    async def _save_settings(
        self,
        auto_create: bool,
        open_minutes: float,
        require_link: bool,
        default_goal: str,
        racetime_bot_id: int | None,
    ):
        """
        Save RaceTime settings.

        Args:
            auto_create: Whether to auto-create rooms
            open_minutes: Minutes before scheduled time to open room
            require_link: Whether to require RaceTime link
            default_goal: Default race goal text
            racetime_bot_id: ID of the RaceTime bot to use (None for no bot)
        """
        from application.services.tournaments.tournament_service import TournamentService

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
            racetime_bot_id=racetime_bot_id,
        )

        ui.notify('RaceTime settings saved successfully!', type='positive')
        # Reload tournament
        await self.tournament.refresh_from_db()
        await self._load_profiles()
        if self.profile_select:
            self.profile_select.value = self.tournament.race_room_profile_id
