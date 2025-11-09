"""Dialog for checking in matches with station assignments (onsite tournaments)."""

import logging
from typing import Callable
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog

logger = logging.getLogger(__name__)


class CheckInDialog(BaseDialog):
    """Dialog for checking in matches and assigning station numbers (onsite mode)."""

    def __init__(
        self,
        match_title: str,
        players: list[dict],
        on_checkin: Callable[[dict[int, str]], None]
    ):
        """
        Initialize check-in dialog.

        Args:
            match_title: Title of the match being checked in
            players: List of player dicts with keys: 'id', 'username', 'match_player_id'
            on_checkin: Async callback function that accepts dict mapping match_player_id to station number
        """
        super().__init__()
        self.match_title = match_title
        self.players = players
        self.on_checkin = on_checkin
        self.station_inputs: dict[int, ui.input] = {}

    async def show(self):
        """Display the check-in dialog."""
        self.create_dialog(
            title='Check In Match',
            icon='how_to_reg',
            max_width='600px'
        )

        await super().show()

    def _render_body(self):
        """Render dialog content."""
        # Match title
        self.create_section_title(self.match_title)

        ui.separator()

        # Info message
        with ui.column().classes('gap-sm w-full'):
            ui.label('Assign station numbers for each player:').classes('text-weight-bold')
            ui.label('Station numbers are used to identify where players are seated during the match.').classes('text-secondary text-sm')

        ui.separator()

        # Station inputs for each player
        with self.create_form_grid(columns=1):
            for player in self.players:
                with ui.row().classes('gap-2 w-full items-center'):
                    # Player name label (fixed width)
                    ui.label(player['username']).classes('text-weight-medium').style('min-width: 150px')
                    
                    # Station number input
                    station_input = ui.input(
                        label='Station Number',
                        placeholder='e.g., 5'
                    ).classes('flex-grow')
                    
                    self.station_inputs[player['match_player_id']] = station_input

        ui.separator()

        # Actions row at root level
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button(
                'Check In',
                on_click=self._check_in
            ).classes('btn').props('color=positive')

    async def _check_in(self):
        """Handle check-in submission."""
        # Collect station assignments
        station_assignments = {}
        has_empty = False

        for match_player_id, input_field in self.station_inputs.items():
            station = input_field.value.strip() if input_field.value else ''
            if not station:
                has_empty = True
            else:
                station_assignments[match_player_id] = station

        # Validate that all stations are provided
        if has_empty:
            ui.notify('Please provide station numbers for all players', type='warning')
            return

        # Validate station numbers are unique
        station_numbers = list(station_assignments.values())
        if len(station_numbers) != len(set(station_numbers)):
            ui.notify('Station numbers must be unique', type='warning')
            return

        # Call the callback with station assignments
        try:
            await self.on_checkin(station_assignments)
            await self.close()
        except Exception as e:
            logger.error("Error during check-in callback: %s", e)
            ui.notify(f'Check-in failed: {str(e)}', type='negative')
