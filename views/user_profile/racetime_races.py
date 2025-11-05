"""
RaceTime.gg race history view for user profile.

This view displays a user's race history from RaceTime.gg.
"""

import logging
from typing import Dict, Any
from nicegui import ui
from models import User
from application.services.racetime_api_service import RacetimeApiService
from components.datetime_label import DateTimeLabel
from datetime import datetime

logger = logging.getLogger(__name__)


class RacetimeRacesView:
    """View for displaying user's RaceTime.gg race history."""

    def __init__(self, user: User):
        """
        Initialize the race history view.

        Args:
            user: Current user
        """
        self.user = user
        self.api_service = RacetimeApiService()
        self.races = []
        self.loading = False
        self.error_message = None
        self.selected_category = 'all'

    async def render(self):
        """Render the race history view."""
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                with ui.row().classes('items-center justify-between w-full'):
                    ui.label('Race History').classes('text-lg font-bold')
                    
                    # Category filter
                    with ui.row().classes('items-center gap-2'):
                        ui.label('Category:')
                        ui.select(
                            options=['all', 'alttpr', 'ootr', 'smz3', 'sm', 'alttp'],
                            value=self.selected_category,
                            on_change=lambda e: self._on_category_change(e.value)
                        ).classes('min-w-32')

            with ui.element('div').classes('card-body'):
                # Check if user has linked account
                if not self.user.racetime_id:
                    with ui.column().classes('items-center gap-4 py-8'):
                        ui.icon('link_off', size='3rem').classes('text-secondary')
                        ui.label('No RaceTime.gg Account Linked').classes('text-lg')
                        ui.label('Link your RaceTime.gg account to view your race history.').classes('text-secondary')
                        ui.button(
                            'Link Account',
                            on_click=lambda: ui.navigate.to('/racetime/link/initiate')
                        ).classes('btn btn-primary')
                    return

                # Loading indicator
                if self.loading:
                    with ui.column().classes('items-center gap-4 py-8'):
                        ui.spinner(size='lg')
                        ui.label('Loading race history...').classes('text-secondary')
                    return

                # Error message
                if self.error_message:
                    with ui.column().classes('items-center gap-4 py-8'):
                        ui.icon('error', size='3rem').classes('text-negative')
                        ui.label('Error Loading Races').classes('text-lg')
                        ui.label(self.error_message).classes('text-secondary')
                        ui.button(
                            'Retry',
                            on_click=self._load_races
                        ).classes('btn btn-secondary')
                    return

                # Race list
                if not self.races:
                    with ui.column().classes('items-center gap-4 py-8'):
                        ui.icon('sports_score', size='3rem').classes('text-secondary')
                        ui.label('No Races Found').classes('text-lg')
                        ui.label('You haven\'t participated in any races yet.').classes('text-secondary')
                else:
                    # Display races
                    await self._render_race_list()

        # Auto-load races on initial render
        if not self.races and not self.loading and not self.error_message:
            await self._load_races()

    async def _load_races(self):
        """Load race history from RaceTime API."""
        self.loading = True
        self.error_message = None
        ui.update()

        try:
            # Get races from API
            if self.selected_category == 'all':
                self.races = await self.api_service.get_user_races(self.user)
            else:
                self.races = await self.api_service.get_past_races(
                    self.user,
                    self.selected_category,
                    limit=50
                )

            logger.info("Loaded %s races for user %s", len(self.races), self.user.id)
        except ValueError as e:
            logger.error("Error loading races: %s", str(e))
            self.error_message = str(e)
        except Exception as e:
            logger.error("Error loading races: %s", str(e), exc_info=True)
            self.error_message = "An error occurred while loading your race history."
        finally:
            self.loading = False
            ui.update()

    async def _on_category_change(self, category: str):
        """Handle category filter change."""
        self.selected_category = category
        await self._load_races()

    async def _render_race_list(self):
        """Render the list of races."""
        with ui.column().classes('w-full gap-2'):
            for race in self.races[:20]:  # Limit to 20 races for performance
                await self._render_race_card(race)

    async def _render_race_card(self, race: Dict[str, Any]):
        """
        Render a single race card.

        Args:
            race: Race data from RaceTime API
        """
        race_name = race.get('name', 'Unknown')
        category = race.get('category', {}).get('name', 'Unknown')
        goal = race.get('goal', {}).get('name', 'Beat the game')
        started_at = race.get('started_at')

        # Find user's entrant data
        user_entrant = None
        entrants = race.get('entrants', [])
        for entrant in entrants:
            if entrant.get('user', {}).get('id') == self.user.racetime_id:
                user_entrant = entrant
                break

        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-body'):
                with ui.row().classes('items-start justify-between w-full'):
                    # Left side: Race info
                    with ui.column().classes('gap-1 flex-1'):
                        # Race name and category
                        with ui.row().classes('items-center gap-2'):
                            ui.label(race_name).classes('font-bold')
                            ui.label(f'[{category}]').classes('text-sm badge badge-secondary')

                        # Goal
                        ui.label(goal).classes('text-secondary text-sm')

                        # Time info
                        if started_at:
                            with ui.row().classes('items-center gap-2 text-sm text-secondary'):
                                ui.icon('schedule', size='sm')
                                started_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                                DateTimeLabel.create(started_dt, format_type='relative')

                    # Right side: User's result
                    if user_entrant:
                        with ui.column().classes('items-end gap-1'):
                            # Placement
                            place = user_entrant.get('place')
                            if place:
                                place_text = f"#{place}"
                                place_class = 'badge-success' if place <= 3 else 'badge-secondary'
                                ui.label(place_text).classes(f'badge {place_class}')

                            # Finish time
                            finish_time = user_entrant.get('finish_time')
                            if finish_time:
                                ui.label(self._format_finish_time(finish_time)).classes('font-mono text-sm')

                            # Status
                            entrant_status = user_entrant.get('status', {}).get('value', 'unknown')
                            status_class = self._get_status_class(entrant_status)
                            ui.label(entrant_status.title()).classes(f'badge {status_class} text-sm')

                # Race link
                with ui.row().classes('w-full justify-end mt-2'):
                    race_url = f"{self.api_service.racetime_url}/{race_name}"
                    ui.link(
                        'View on RaceTime.gg',
                        race_url,
                        new_tab=True
                    ).classes('text-sm')

    def _format_finish_time(self, finish_time: str) -> str:
        """
        Format finish time for display.

        Args:
            finish_time: Finish time in ISO duration format (e.g., 'PT1H23M45S')

        Returns:
            str: Formatted time (e.g., '1:23:45')
        """
        try:
            # Parse ISO duration (PT1H23M45S)
            if not finish_time.startswith('PT'):
                return finish_time

            time_str = finish_time[2:]  # Remove 'PT'
            hours = 0
            minutes = 0
            seconds = 0

            if 'H' in time_str:
                hours_str, time_str = time_str.split('H')
                hours = int(hours_str)

            if 'M' in time_str:
                minutes_str, time_str = time_str.split('M')
                minutes = int(minutes_str)

            if 'S' in time_str:
                seconds_str = time_str.replace('S', '')
                seconds = int(float(seconds_str))

            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"

        except Exception as e:
            logger.warning("Error formatting finish time %s: %s", finish_time, str(e))
            return finish_time

    def _get_status_class(self, status: str) -> str:
        """
        Get CSS class for entrant status.

        Args:
            status: Entrant status value

        Returns:
            str: CSS class name
        """
        status_classes = {
            'done': 'badge-success',
            'dnf': 'badge-warning',
            'dq': 'badge-danger',
            'ready': 'badge-info',
            'not_ready': 'badge-secondary',
        }
        return status_classes.get(status, 'badge-secondary')
