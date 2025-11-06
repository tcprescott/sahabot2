"""
Dialog for creating/editing async tournament live races.
"""

from __future__ import annotations
from typing import Optional, Callable
from datetime import datetime, timezone, timedelta
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from models import AsyncTournamentPool, AsyncTournamentPermalink, RaceRoomProfile
import logging

logger = logging.getLogger(__name__)


class CreateLiveRaceDialog(BaseDialog):
    """Dialog for creating a new live race."""

    def __init__(
        self,
        organization_id: int,
        tournament_id: int,
        pools: list[AsyncTournamentPool],
        permalinks: list[AsyncTournamentPermalink],
        profiles: list[RaceRoomProfile],
        on_save: Optional[Callable] = None,
    ):
        """
        Initialize the create live race dialog.

        Args:
            organization_id: Organization ID
            tournament_id: Tournament ID
            pools: List of tournament pools
            permalinks: List of available permalinks
            profiles: List of race room profiles
            on_save: Optional callback after successful creation
        """
        super().__init__()
        self.organization_id = organization_id
        self.tournament_id = tournament_id
        self.pools = pools
        self.permalinks = permalinks
        self.profiles = profiles
        self.on_save = on_save

        # Form fields
        self.pool_select: Optional[ui.select] = None
        self.scheduled_date: Optional[ui.date] = None
        self.scheduled_time: Optional[ui.time] = None
        self.match_title: Optional[ui.input] = None
        self.permalink_select: Optional[ui.select] = None
        self.episode_id: Optional[ui.input] = None
        self.profile_select: Optional[ui.select] = None
        self.error_label: Optional[ui.label] = None

    async def show(self):
        """Display the create live race dialog."""
        self.create_dialog(
            title='Schedule Live Race',
            icon='event',
        )
        await super().show()

    def _render_body(self) -> None:
        """Render dialog content."""
        # Error message area
        with ui.row().classes('w-full'):
            self.error_label = ui.label('').classes('text-negative')
            self.error_label.set_visibility(False)

        ui.separator()

        # Form section
        self.create_section_title('Race Details')

        with self.create_form_grid(columns=2):
            # Pool selection (required)
            with ui.element('div'):
                pool_options = {p.id: p.name for p in self.pools}
                self.pool_select = ui.select(
                    label='Pool *',
                    options=pool_options,
                ).classes('w-full').props('outlined')

            # Match title (optional)
            with ui.element('div'):
                self.match_title = ui.input(
                    label='Match Title',
                    placeholder='Optional descriptive title',
                ).classes('w-full').props('outlined')

        ui.separator()

        # Date and time section
        self.create_section_title('Schedule')

        with self.create_form_grid(columns=2):
            # Date picker
            with ui.element('div'):
                # Default to tomorrow
                tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
                self.scheduled_date = ui.date(
                    value=tomorrow.strftime('%Y-%m-%d'),
                ).classes('w-full').props('outlined')
                ui.label('Scheduled Date *').classes('text-sm text-caption mt-1')

            # Time picker
            with ui.element('div'):
                # Default to 20:00 UTC
                self.scheduled_time = ui.time(
                    value='20:00',
                ).classes('w-full').props('outlined')
                ui.label('Scheduled Time (UTC) *').classes('text-sm text-caption mt-1')

        ui.separator()

        # Settings section
        self.create_section_title('Settings')

        with self.create_form_grid(columns=2):
            # Permalink selection (optional)
            with ui.element('div'):
                permalink_options = {0: 'None (Use pool default)'}
                permalink_options.update({p.id: p.permalink for p in self.permalinks})
                self.permalink_select = ui.select(
                    label='Permalink',
                    options=permalink_options,
                    value=0,
                ).classes('w-full').props('outlined')

            # Episode ID (optional)
            with ui.element('div'):
                self.episode_id = ui.input(
                    label='Episode ID',
                    placeholder='Optional episode number',
                ).classes('w-full').props('outlined')

        # Race room profile (optional)
        with ui.element('div').classes('w-full'):
            profile_options = {0: 'None (Use tournament default)'}
            profile_options.update({p.id: p.name for p in self.profiles})
            self.profile_select = ui.select(
                label='Race Room Profile',
                options=profile_options,
                value=0,
            ).classes('w-full').props('outlined')

        ui.separator()

        # Actions
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Create', on_click=self._save).classes('btn').props('color=positive')

    async def _save(self):
        """Validate and create the live race."""
        # Validation
        if not self.pool_select or not self.pool_select.value:
            self._show_error('Please select a pool')
            return

        if not self.scheduled_date or not self.scheduled_date.value:
            self._show_error('Please select a date')
            return

        if not self.scheduled_time or not self.scheduled_time.value:
            self._show_error('Please select a time')
            return

        try:
            # Combine date and time into datetime
            date_str = self.scheduled_date.value
            time_str = self.scheduled_time.value

            # Parse the date and time
            scheduled_dt = datetime.strptime(
                f"{date_str} {time_str}",
                '%Y-%m-%d %H:%M'
            ).replace(tzinfo=timezone.utc)

            # Check if in the past
            if scheduled_dt < datetime.now(timezone.utc):
                self._show_error('Scheduled time must be in the future')
                return

            # Build request data
            from application.services.tournaments.async_live_race_service import AsyncLiveRaceService
            from middleware.auth import DiscordAuthService

            service = AsyncLiveRaceService()
            current_user = DiscordAuthService.get_current_user()

            if not current_user:
                self._show_error('Not authenticated')
                return

            # Create the live race
            data = {
                'pool_id': int(self.pool_select.value),
                'scheduled_at': scheduled_dt,
            }

            if self.match_title and self.match_title.value:
                data['match_title'] = self.match_title.value

            if self.permalink_select and self.permalink_select.value and int(self.permalink_select.value) > 0:
                data['permalink_id'] = int(self.permalink_select.value)

            if self.episode_id and self.episode_id.value:
                try:
                    data['episode_id'] = int(self.episode_id.value)
                except ValueError:
                    self._show_error('Episode ID must be a number')
                    return

            if self.profile_select and self.profile_select.value and int(self.profile_select.value) > 0:
                data['race_room_profile_id'] = int(self.profile_select.value)

            live_race = await service.create_live_race(
                current_user=current_user,
                organization_id=self.organization_id,
                tournament_id=self.tournament_id,
                **data,
            )

            logger.info("Created live race %s", live_race.id)

            # Call callback
            if self.on_save:
                await self.on_save()

            # Close dialog
            await self.close()

        except ValueError as e:
            self._show_error(str(e))
        except Exception as e:
            logger.error("Failed to create live race: %s", e, exc_info=True)
            self._show_error(f"Failed to create live race: {e}")

    def _show_error(self, message: str):
        """Display error message."""
        if self.error_label:
            self.error_label.set_text(message)
            self.error_label.set_visibility(True)
