"""
Tournament RaceTime Settings View.

Allows tournament managers to configure RaceTime room opening settings.
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

    async def render(self):
        """Render the RaceTime settings view."""
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                ui.label('RaceTime Room Settings').classes('text-xl font-bold')

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

                # Advanced Room Settings Section
                ui.label('Advanced Room Settings').classes('text-lg font-bold mt-4 mb-3')

                # Race timing
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Start countdown (seconds):').classes('w-64')
                    start_delay = ui.number(
                        value=getattr(self.tournament, 'racetime_start_delay', 15),
                        min=10,
                        max=60,
                        step=5
                    ).classes('w-32')
                    ui.label('Countdown timer before race starts').classes('text-sm text-grey')

                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Time limit (hours):').classes('w-64')
                    time_limit = ui.number(
                        value=getattr(self.tournament, 'racetime_time_limit', 24),
                        min=1,
                        max=72,
                        step=1
                    ).classes('w-32')
                    ui.label('Maximum time allowed for race completion').classes('text-sm text-grey')

                # Stream & automation settings
                ui.label('Stream & Automation').classes('font-bold mt-4 mb-2')

                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Require streaming:').classes('w-64')
                    streaming_required = ui.switch(value=getattr(self.tournament, 'racetime_streaming_required', False))
                    ui.label('All participants must be streaming').classes('text-sm text-grey')

                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Auto-start when ready:').classes('w-64')
                    auto_start = ui.switch(value=getattr(self.tournament, 'racetime_auto_start', True))
                    ui.label('Start automatically when all racers ready').classes('text-sm text-grey')

                # Chat permissions
                ui.label('Chat Permissions').classes('font-bold mt-4 mb-2')

                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Allow race comments:').classes('w-64')
                    allow_comments = ui.switch(value=getattr(self.tournament, 'racetime_allow_comments', True))
                    ui.label('Racers can leave comments on the race').classes('text-sm text-grey')

                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Hide comments until finish:').classes('w-64')
                    hide_comments = ui.switch(value=getattr(self.tournament, 'racetime_hide_comments', False))
                    ui.label('Comments hidden until race ends').classes('text-sm text-grey')

                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Pre-race chat:').classes('w-64')
                    allow_prerace_chat = ui.switch(value=getattr(self.tournament, 'racetime_allow_prerace_chat', True))
                    ui.label('Chat enabled before race starts').classes('text-sm text-grey')

                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Mid-race chat:').classes('w-64')
                    allow_midrace_chat = ui.switch(value=getattr(self.tournament, 'racetime_allow_midrace_chat', True))
                    ui.label('Chat enabled during the race').classes('text-sm text-grey')

                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Non-entrant chat:').classes('w-64')
                    allow_non_entrant_chat = ui.switch(value=getattr(self.tournament, 'racetime_allow_non_entrant_chat', True))
                    ui.label('Spectators can chat in the room').classes('text-sm text-grey')

                ui.separator()

                # Save button
                with ui.row().classes('justify-end mt-4'):
                    ui.button('Save Settings', on_click=lambda: self._save_settings(
                        auto_create_toggle.value,
                        open_minutes.value,
                        require_link_toggle.value,
                        default_goal.value,
                        start_delay.value,
                        time_limit.value,
                        streaming_required.value,
                        auto_start.value,
                        allow_comments.value,
                        hide_comments.value,
                        allow_prerace_chat.value,
                        allow_midrace_chat.value,
                        allow_non_entrant_chat.value,
                    )).classes('btn').props('color=positive')

    async def _save_settings(
        self,
        auto_create: bool,
        open_minutes: float,
        require_link: bool,
        default_goal: str,
        start_delay: float,
        time_limit: float,
        streaming_required: bool,
        auto_start: bool,
        allow_comments: bool,
        hide_comments: bool,
        allow_prerace_chat: bool,
        allow_midrace_chat: bool,
        allow_non_entrant_chat: bool,
    ):
        """
        Save RaceTime settings.

        Args:
            auto_create: Whether to auto-create rooms
            open_minutes: Minutes before scheduled time to open room
            require_link: Whether to require RaceTime link
            default_goal: Default race goal text
            start_delay: Countdown seconds before race starts
            time_limit: Time limit in hours
            streaming_required: Whether streaming is required
            auto_start: Whether to auto-start when ready
            allow_comments: Whether to allow race comments
            hide_comments: Whether to hide comments until race ends
            allow_prerace_chat: Whether to allow pre-race chat
            allow_midrace_chat: Whether to allow mid-race chat
            allow_non_entrant_chat: Whether to allow non-entrant chat
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
            racetime_default_goal=default_goal if default_goal else None,
            racetime_start_delay=int(start_delay),
            racetime_time_limit=int(time_limit),
            racetime_streaming_required=streaming_required,
            racetime_auto_start=auto_start,
            racetime_allow_comments=allow_comments,
            racetime_hide_comments=hide_comments,
            racetime_allow_prerace_chat=allow_prerace_chat,
            racetime_allow_midrace_chat=allow_midrace_chat,
            racetime_allow_non_entrant_chat=allow_non_entrant_chat,
        )

        ui.notify('RaceTime settings saved successfully', type='positive')
