"""Dialog for creating a new match."""

from __future__ import annotations
from typing import Optional, Callable, List
from datetime import datetime
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from models import User
from models.match_schedule import Tournament, StreamChannel
import logging

logger = logging.getLogger(__name__)


class CreateMatchDialog(BaseDialog):
    """Dialog for creating a new match."""

    def __init__(
        self,
        *,
        user: User,
        organization_id: int,
        tournament: Tournament,
        on_save: Optional[Callable] = None,
    ) -> None:
        super().__init__()
        self.user = user
        self.organization_id = organization_id
        self.tournament = tournament
        self.on_save = on_save

        # UI refs
        self._title_input: Optional[ui.input] = None
        self._scheduled_input: Optional[ui.input] = None
        self._stream_select: Optional[ui.select] = None
        self._player_select: Optional[ui.select] = None
        self._comment_input: Optional[ui.textarea] = None

        # Data
        self._streams: List[StreamChannel] = []
        self._available_players: List[User] = []

    async def show(self) -> None:
        """Display the dialog."""
        self.create_dialog(
            title=f"Create Match - {self.tournament.name}",
            icon="add_circle",
            max_width="dialog-card",
        )
        await super().show()

    def _render_body(self) -> None:
        """Render dialog body with form fields."""
        with self.create_form_grid(columns=1):
            with ui.element("div"):
                self._title_input = ui.input(
                    label="Match Title", placeholder="e.g., Quarterfinal Match 1"
                ).classes("w-full")

            with ui.element("div"):
                self._scheduled_input = (
                    ui.input(
                        label="Scheduled Time (Optional)",
                        placeholder="YYYY-MM-DD HH:MM",
                    )
                    .classes("w-full")
                    .props("type=datetime-local")
                )

            with ui.element("div"):
                # Player selection (multi-select)
                self._player_select = (
                    ui.select(
                        label="Players",
                        options={},  # Populated async
                        multiple=True,
                    )
                    .classes("w-full")
                    .props("use-chips")
                )

            with ui.element("div"):
                # Stream channel selection
                self._stream_select = ui.select(
                    label="Stream Channel (Optional)",
                    options={None: "No stream"},  # Populated async
                ).classes("w-full")

            with ui.element("div"):
                self._comment_input = (
                    ui.textarea(
                        label="Notes/Comments (Optional)",
                        placeholder="Add any notes about this match...",
                    )
                    .classes("w-full")
                    .props("rows=3")
                )

        ui.separator()

        # Load streams and players asynchronously
        async def load_data():
            """Load stream channels and players."""
            try:
                from application.services.tournaments.stream_channel_service import (
                    StreamChannelService,
                )
                from application.services.organizations.organization_service import (
                    OrganizationService,
                )

                # Load streams
                stream_service = StreamChannelService()
                streams = await stream_service.list_org_channels(
                    self.user, self.organization_id
                )
                self._streams = streams

                stream_options = {None: "No stream"}
                stream_options.update({s.id: s.name for s in streams})

                if self._stream_select:
                    self._stream_select.options = stream_options
                    self._stream_select.update()

                logger.info(
                    "Loaded %d stream channels for org %s",
                    len(streams),
                    self.organization_id,
                )

                # Load available players (organization members)
                org_service = OrganizationService()
                members = await org_service.list_members(self.organization_id)

                player_options = {}
                for member in members:
                    await member.fetch_related("user")
                    player_options[member.user.id] = member.user.discord_username

                if self._player_select:
                    self._player_select.options = player_options
                    self._player_select.update()

                logger.info(
                    "Loaded %d potential players for org %s",
                    len(members),
                    self.organization_id,
                )

            except Exception as e:
                logger.error("Failed to load data: %s", e)
                if self._stream_select:
                    self._stream_select.options = {None: "(Error loading streams)"}
                    self._stream_select.update()
                if self._player_select:
                    self._player_select.options = {}
                    self._player_select.update()
                ui.notify(f"Error loading data: {str(e)}", type="negative")

        # Trigger async load
        ui.timer(0.1, load_data, once=True)

        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Create Match", on_click=self._handle_create).classes(
                "btn"
            ).props("color=positive")

    async def _handle_create(self) -> None:
        """Handle Create click and call callback."""
        if not self._title_input or not self._player_select:
            ui.notify("Title and players are required", type="warning")
            return

        title = self._title_input.value.strip() if self._title_input.value else None
        if not title:
            ui.notify("Match title is required", type="warning")
            return

        player_ids = (
            self._player_select.value
            if self._player_select and self._player_select.value
            else []
        )
        if not player_ids or len(player_ids) < 1:
            ui.notify("At least one player is required", type="warning")
            return

        scheduled_str = (
            self._scheduled_input.value.strip()
            if self._scheduled_input and self._scheduled_input.value
            else None
        )
        stream_id = (
            self._stream_select.value
            if self._stream_select and self._stream_select.value
            else None
        )
        comment = (
            self._comment_input.value.strip()
            if self._comment_input and self._comment_input.value
            else None
        )

        # Parse the datetime-local value
        scheduled_at = None
        if scheduled_str:
            try:
                scheduled_at = datetime.fromisoformat(scheduled_str)
                logger.info("Parsed scheduled time: %s", scheduled_at)
            except ValueError as e:
                ui.notify(f"Invalid date/time format: {e}", type="negative")
                logger.error("Failed to parse datetime: %s - %s", scheduled_str, e)
                return

        # Call the service to create the match
        try:
            from application.services.tournaments.tournament_service import (
                TournamentService,
            )

            service = TournamentService()
            match = await service.create_match(
                user=self.user,
                organization_id=self.organization_id,
                tournament_id=self.tournament.id,
                player_ids=player_ids,
                scheduled_at=scheduled_at,
                comment=comment,
                title=title,
            )

            if match:
                # Update stream channel if specified
                if stream_id:
                    await service.update_match(
                        user=self.user,
                        organization_id=self.organization_id,
                        match_id=match.id,
                        stream_channel_id=stream_id,
                    )

                ui.notify(f'Match "{title}" created successfully!', type="positive")

                if self.on_save:
                    await self.on_save()

                await self.close()
            else:
                ui.notify("Failed to create match", type="negative")

        except ValueError as e:
            # RaceTime requirement error
            ui.notify(str(e), type="negative")
            logger.warning("Match creation failed: %s", e)
        except Exception as e:
            ui.notify(f"Error creating match: {str(e)}", type="negative")
            logger.error("Failed to create match: %s", e)
