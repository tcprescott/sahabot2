"""
Dialog for submitting a new match.

Allows users to select a tournament, opponent, date/time, and add a comment.
"""

from __future__ import annotations
from typing import Optional, Callable, Awaitable
from datetime import datetime
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from modules.tournament.services.tournament_service import TournamentService
from models import User, Organization
import logging

logger = logging.getLogger(__name__)


class SubmitMatchDialog(BaseDialog):
    """Dialog for users to submit a match request."""

    def __init__(
        self,
        user: User,
        organization: Organization,
        on_save: Optional[Callable[[], Awaitable[None]]] = None,
    ) -> None:
        super().__init__()
        self.user = user
        self.organization = organization
        self.on_save = on_save
        self.tournament_service = TournamentService()

        # UI refs
        self.tournament_select: Optional[ui.select] = None
        self.opponent_select: Optional[ui.select] = None
        self.datetime_input: Optional[ui.input] = None
        self.comment_input: Optional[ui.textarea] = None

        # Data
        self.tournaments = []
        self.tournament_players = {}  # tournament_id -> list of players

    async def show(self) -> None:
        """Display the dialog."""
        self.create_dialog(
            title="Submit Match", icon="sports_esports", max_width="dialog-card"
        )
        await super().show()

    def _render_body(self) -> None:
        """Render dialog body with form fields."""
        with self.create_form_grid(columns=1):
            # Tournament selection
            with ui.element("div"):
                ui.label("Tournament").classes("font-semibold mb-1")
                self.tournament_select = ui.select(
                    label="Select Tournament",
                    options={},
                    with_input=True,
                    on_change=self._on_tournament_change,
                ).classes("w-full")

            # Opponent selection (disabled until tournament selected)
            with ui.element("div"):
                ui.label("Opponent").classes("font-semibold mb-1")
                self.opponent_select = ui.select(
                    label="Select Opponent",
                    options={},
                    with_input=True,
                ).classes("w-full")
                self.opponent_select.disable()

            # Date and time input
            with ui.element("div"):
                ui.label("Date & Time").classes("font-semibold mb-1")
                # Get current datetime in ISO format for datetime-local input
                now = datetime.now()
                default_datetime = now.strftime("%Y-%m-%dT%H:%M")

                self.datetime_input = ui.input(
                    label="Match Date & Time", value=default_datetime
                ).classes("w-full")
                # Set input type to datetime-local for browser native picker
                self.datetime_input.props("type=datetime-local")

                ui.label("Time is in your local timezone").classes(
                    "text-sm text-secondary mt-1"
                )

            # Comment
            with ui.element("div"):
                ui.label("Comment (optional)").classes("font-semibold mb-1")
                self.comment_input = ui.textarea(
                    label="Add any notes or details about this match"
                ).classes("w-full")

        # Actions
        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Submit Match", on_click=self._handle_submit).classes(
                "btn"
            ).props("color=positive")

        # Load tournaments asynchronously
        ui.timer(0.1, self._load_tournaments, once=True)

    async def _load_tournaments(self) -> None:
        """Load available tournaments for the organization."""
        try:
            # Get all active tournaments in the organization
            self.tournaments = await self.tournament_service.list_all_org_tournaments(
                self.organization.id
            )

            # Filter to only active tournaments
            active_tournaments = [t for t in self.tournaments if t.is_active]

            # Build options dict: tournament_id -> name
            options = {t.id: t.name for t in active_tournaments}

            if self.tournament_select:
                self.tournament_select.options = options
                self.tournament_select.update()

            if not active_tournaments:
                ui.notify("No active tournaments available", type="warning")

        except Exception as e:
            logger.error("Failed to load tournaments: %s", e)
            ui.notify("Failed to load tournaments", type="negative")

    async def _on_tournament_change(self, event) -> None:
        """Handle tournament selection change - load registered players."""
        tournament_id = event.value if event else None

        if not tournament_id or not self.opponent_select:
            return

        try:
            # Get all registered players for this tournament
            registrations = await self.tournament_service.list_tournament_players(
                self.organization.id, tournament_id
            )

            # Filter out the current user and build options
            opponents = [
                reg.user for reg in registrations if reg.user_id != self.user.id
            ]

            if not opponents:
                ui.notify(
                    "No other players registered for this tournament", type="warning"
                )
                self.opponent_select.options = {}
                self.opponent_select.disable()
            else:
                options = {u.id: u.discord_username for u in opponents}
                self.opponent_select.options = options
                self.opponent_select.enable()

            self.opponent_select.update()

        except Exception as e:
            logger.error("Failed to load tournament players: %s", e)
            ui.notify("Failed to load players", type="negative")

    async def _handle_submit(self) -> None:
        """Handle submit button click."""
        # Validate inputs
        if not self.tournament_select or not self.tournament_select.value:
            ui.notify("Please select a tournament", type="warning")
            return

        if not self.opponent_select or not self.opponent_select.value:
            ui.notify("Please select an opponent", type="warning")
            return

        if not self.datetime_input or not self.datetime_input.value:
            ui.notify("Please select a date and time", type="warning")
            return

        try:
            tournament_id = self.tournament_select.value
            opponent_id = self.opponent_select.value
            datetime_str = self.datetime_input.value
            comment = self.comment_input.value if self.comment_input else None

            # Parse the datetime string (in user's local timezone)
            # The browser datetime-local input gives us YYYY-MM-DDTHH:MM format
            scheduled_at = datetime.fromisoformat(datetime_str)

            # Create the match
            await self.tournament_service.create_match(
                user=self.user,
                organization_id=self.organization.id,
                tournament_id=tournament_id,
                player_ids=[self.user.id, opponent_id],
                scheduled_at=scheduled_at,
                comment=comment,
            )

            ui.notify("Match submitted successfully", type="positive")

            if self.on_save:
                await self.on_save()

            await self.close()

        except Exception as e:
            logger.error("Failed to submit match: %s", e)
            ui.notify(f"Failed to submit match: {str(e)}", type="negative")
