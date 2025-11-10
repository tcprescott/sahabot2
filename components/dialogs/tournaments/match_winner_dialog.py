"""Dialog for selecting the winner of a match."""

from __future__ import annotations
from typing import Optional, Callable, List
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
import logging

logger = logging.getLogger(__name__)


class MatchWinnerDialog(BaseDialog):
    """Dialog for selecting the winner of a match."""

    def __init__(
        self,
        *,
        match_title: str,
        players: List[dict],  # List of dicts with 'id', 'username', 'match_player_id'
        on_select: Optional[
            Callable[[int], None]
        ] = None,  # Callback with match_player_id
    ) -> None:
        """
        Initialize the match winner dialog.

        Args:
            match_title: Title of the match
            players: List of player dicts with id, username, match_player_id
            on_select: Callback when winner is selected (receives match_player_id)
        """
        super().__init__()
        self._match_title = match_title
        self._players = players
        self._on_select = on_select
        self._selected_player_id: Optional[int] = None

        # UI refs
        self._radio_group: Optional[ui.radio] = None

    async def show(self) -> None:
        """Display the dialog."""
        self.create_dialog(
            title=f"Select Winner: {self._match_title}",
            icon="emoji_events",
            max_width="600px",
        )
        await super().show()

    def _render_body(self) -> None:
        """Render dialog body with player selection."""
        # Instructions
        ui.label("Select the winner of this match:").classes("text-lg mb-2")

        ui.separator()

        # Player selection
        if not self._players:
            ui.label("No players found for this match").classes("text-secondary")
        else:
            # Create radio options
            options = {
                player["match_player_id"]: player["username"]
                for player in self._players
            }

            self._radio_group = ui.radio(options=options, value=None).classes("w-full")

        ui.separator()

        with self.create_actions_row():
            # Left side - cancel
            ui.button("Cancel", on_click=self.close).classes("btn")

            # Right side - confirm
            ui.button("Confirm Winner", on_click=self._handle_confirm).classes(
                "btn"
            ).props("color=positive")

    async def _handle_confirm(self) -> None:
        """Handle confirm click and call callback."""
        if not self._radio_group or not self._radio_group.value:
            ui.notify("Please select a winner", type="warning")
            return

        selected_id = self._radio_group.value

        if self._on_select:
            await self._on_select(selected_id)

        await self.close()
