"""Dialog for editing an existing match."""

from __future__ import annotations
from typing import Optional, Callable, List
from datetime import datetime
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from models import User
from modules.tournament.models.match_schedule import Tournament, Match, StreamChannel
import logging

logger = logging.getLogger(__name__)


class EditMatchDialog(BaseDialog):
    """Dialog for editing an existing match."""

    def __init__(
        self,
        *,
        match: Match,
        organization_id: int,
        on_save: Optional[Callable] = None,
    ) -> None:
        super().__init__()
        self.match = match
        self.organization_id = organization_id
        self.on_save = on_save

        # UI refs
        self._title_input: Optional[ui.input] = None
        self._scheduled_input: Optional[ui.input] = None
        self._stream_select: Optional[ui.select] = None
        self._comment_input: Optional[ui.textarea] = None

        # Data
        self._streams: List[StreamChannel] = []

    async def show(self) -> None:
        """Display the dialog."""
        self.create_dialog(
            title=f'Edit Match: {self.match.title or f"Match #{self.match.id}"}',
            icon="edit",
            max_width="dialog-card",
        )
        await super().show()

    def _render_body(self) -> None:
        """Render dialog body with form fields."""
        # Convert scheduled_at to local timezone for display
        local_scheduled = ""
        if self.match.scheduled_at:
            # Format as datetime-local input format: "YYYY-MM-DDTHH:MM"
            # The browser will automatically display this in the user's local timezone
            local_scheduled = self.match.scheduled_at.strftime("%Y-%m-%dT%H:%M")

        with self.create_form_grid(columns=1):
            with ui.element("div"):
                self._title_input = ui.input(
                    label="Match Title", value=self.match.title or ""
                ).classes("w-full")

            with ui.element("div"):
                self._scheduled_input = (
                    ui.input(label="Scheduled Time", value=local_scheduled)
                    .props("type=datetime-local")
                    .classes("w-full")
                )
                ui.label("Time will be displayed in your local timezone").classes(
                    "text-xs text-secondary"
                )

            with ui.element("div"):
                # Stream selection
                self._stream_select = ui.select(
                    label="Stream Channel", options={None: "(Loading...)"}, value=None
                ).classes("w-full")

            with ui.element("div"):
                self._comment_input = ui.textarea(
                    label="Comments", value=self.match.comment or ""
                ).classes("w-full")

        # Load stream channels async
        async def load_streams():
            try:
                from modules.tournament.models.match_schedule import StreamChannel

                streams = await StreamChannel.filter(
                    organization_id=self.organization_id, is_active=True
                ).all()

                # Build options dictionary
                stream_options = {None: "(None)"}
                for s in streams:
                    stream_options[s.id] = s.name

                # Update the select widget
                if self._stream_select:
                    self._stream_select.options = stream_options
                    self._stream_select.value = (
                        self.match.stream_channel_id
                        if self.match.stream_channel_id
                        else None
                    )
                    self._stream_select.update()

                logger.info(
                    "Loaded %d stream channels for org %s",
                    len(streams),
                    self.organization_id,
                )
            except Exception as e:
                logger.error("Failed to load stream channels: %s", e)
                if self._stream_select:
                    self._stream_select.options = {None: "(Error loading streams)"}
                    self._stream_select.update()

        # Trigger async load
        ui.timer(0.1, load_streams, once=True)

        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Save", on_click=self._handle_save).classes("btn").props(
                "color=positive"
            )

    async def _handle_save(self) -> None:
        """Handle Save click and call callback."""
        if not self._title_input or not self._scheduled_input:
            ui.notify("Title and scheduled time are required", type="warning")
            return

        title = self._title_input.value.strip() if self._title_input.value else None
        scheduled_str = (
            self._scheduled_input.value.strip() if self._scheduled_input.value else None
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

        # Parse the datetime-local value (comes in as "YYYY-MM-DDTHH:MM" in user's local time)
        # The browser sends this in the user's timezone, but we need to convert it to server time
        scheduled_at = None
        if scheduled_str:
            try:
                # Parse the datetime string (naive datetime in user's local timezone)
                scheduled_at = datetime.fromisoformat(scheduled_str)
                # Note: The datetime object is naive (no timezone info)
                # When we save it to the database, Tortoise ORM will treat it as server time
                logger.info(
                    "Parsed scheduled time: %s (will be saved as server timezone)",
                    scheduled_at,
                )
            except ValueError as e:
                ui.notify(f"Invalid date/time format: {e}", type="negative")
                logger.error("Failed to parse datetime: %s - %s", scheduled_str, e)
                return

        if self.on_save:
            await self.on_save(title, scheduled_at, stream_id, comment)

        await self.close()
