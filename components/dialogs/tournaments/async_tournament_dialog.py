"""
Dialog for creating/editing async tournaments.

Provides form for async tournament configuration including Discord channel and runs per pool.
"""

from typing import Optional, Callable
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from models.async_tournament import AsyncTournament
import logging

logger = logging.getLogger(__name__)


class AsyncTournamentDialog(BaseDialog):
    """Dialog for creating or editing an async tournament."""

    def __init__(
        self,
        tournament: Optional[AsyncTournament] = None,
        on_save: Optional[Callable] = None,
        discord_channels: Optional[list[tuple[int, str]]] = None,
        allow_manual_channel_id: bool = False,
    ):
        """
        Initialize async tournament dialog.

        Args:
            tournament: Existing tournament to edit (None for new tournament)
            on_save: Callback function to call after successful save
            discord_channels: List of (channel_id, channel_name) tuples for Discord channel selection
            allow_manual_channel_id: Whether to allow manual entry of Discord channel ID (default: False)
        """
        super().__init__()
        self.tournament = tournament
        self.on_save = on_save
        self.discord_channels = discord_channels or []
        self.allow_manual_channel_id = allow_manual_channel_id

        # Form fields
        self.name_input: Optional[ui.input] = None
        self.description_input: Optional[ui.textarea] = None
        self.is_active_switch: Optional[ui.switch] = None
        self.hide_results_switch: Optional[ui.switch] = None
        self.require_racetime_switch: Optional[ui.switch] = None
        self.runs_per_pool_input: Optional[ui.number] = None
        self.discord_channel_select: Optional[ui.select] = None
        self.manual_channel_input: Optional[ui.input] = None

    async def show(self):
        """Display the dialog."""
        title = (
            f"Edit Async Tournament: {self.tournament.name}"
            if self.tournament
            else "Create New Async Tournament"
        )
        self.create_dialog(
            title=title,
            icon="emoji_events" if not self.tournament else "edit",
            max_width="700px",
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        # Basic Information Section
        self.create_section_title("Basic Information")

        with self.create_form_grid(columns=1):
            with ui.element("div"):
                self.name_input = (
                    ui.input(
                        label="Tournament Name",
                        placeholder="e.g., Weekly Async Tournament, Championship 2025",
                        value=self.tournament.name if self.tournament else "",
                    )
                    .classes("w-full")
                    .props("outlined")
                )
                self.name_input.props("autofocus")

            with ui.element("div"):
                self.description_input = (
                    ui.textarea(
                        label="Description (optional)",
                        placeholder="Describe the tournament format, rules, and any special conditions...",
                        value=self.tournament.description if self.tournament else "",
                    )
                    .classes("w-full")
                    .props("outlined rows=3")
                )

        ui.separator().classes("my-4")

        # Tournament Settings Section
        self.create_section_title("Tournament Settings")

        with self.create_form_grid(columns=2):
            with ui.element("div"):
                self.is_active_switch = ui.checkbox(
                    text="Tournament Active",
                    value=self.tournament.is_active if self.tournament else True,
                )
                ui.label("Allow players to start new races").classes(
                    "text-sm text-secondary"
                )

            with ui.element("div"):
                self.runs_per_pool_input = (
                    ui.number(
                        label="Runs Per Pool",
                        value=self.tournament.runs_per_pool if self.tournament else 1,
                        min=1,
                        max=10,
                        step=1,
                        precision=0,
                    )
                    .classes("w-full")
                    .props("outlined")
                )
                ui.label("How many times each pool can be attempted").classes(
                    "text-sm text-secondary"
                )

        with self.create_form_grid(columns=1):
            with ui.element("div"):
                self.hide_results_switch = ui.checkbox(
                    text="Hide Other Players' Results",
                    value=self.tournament.hide_results if self.tournament else False,
                )
                ui.label(
                    "Hide run information from other players until the tournament ends"
                ).classes("text-sm text-secondary")

            with ui.element("div"):
                self.require_racetime_switch = ui.checkbox(
                    text="Require RaceTime.gg Account",
                    value=(
                        self.tournament.require_racetime_for_async_runs
                        if self.tournament
                        else False
                    ),
                )
                ui.label(
                    "Players must link their RaceTime.gg account before starting async runs"
                ).classes("text-sm text-secondary")

        ui.separator().classes("my-4")

        # Discord Integration Section
        self.create_section_title("Discord Integration")

        with self.create_form_grid(columns=1):
            with ui.element("div"):
                if self.discord_channels:
                    # Show dropdown if we have channels
                    channel_options = {None: "No Discord Channel"}
                    channel_options.update(
                        {ch_id: ch_name for ch_id, ch_name in self.discord_channels}
                    )

                    current_value = (
                        self.tournament.discord_channel_id if self.tournament else None
                    )

                    self.discord_channel_select = (
                        ui.select(
                            label="Discord Channel (optional)",
                            options=channel_options,
                            value=current_value,
                        )
                        .classes("w-full")
                        .props("outlined")
                    )
                    ui.label(
                        "The Discord channel where players can start async runs"
                    ).classes("text-sm text-secondary")

                    # Show manual entry option only if enabled
                    if self.allow_manual_channel_id:
                        with ui.element("div").classes("mt-3"):
                            ui.label("Or enter Channel ID manually:").classes(
                                "text-sm font-semibold"
                            )
                            self.manual_channel_input = (
                                ui.input(
                                    label="Discord Channel ID",
                                    placeholder="e.g., 1234567890123456789",
                                    value=(
                                        str(self.tournament.discord_channel_id)
                                        if self.tournament
                                        and self.tournament.discord_channel_id
                                        else ""
                                    ),
                                )
                                .classes("w-full")
                                .props("outlined")
                            )
                            ui.label(
                                "Manual entry overrides the dropdown selection above"
                            ).classes("text-sm text-secondary")
                else:
                    # No channels available
                    if self.allow_manual_channel_id:
                        # Allow manual entry if enabled
                        ui.label("No Discord channels found").classes("text-warning")
                        ui.label(
                            "Enter the Discord Channel ID manually, or link a Discord server first"
                        ).classes("text-sm text-secondary mb-2")
                        self.discord_channel_select = None
                        self.manual_channel_input = (
                            ui.input(
                                label="Discord Channel ID (optional)",
                                placeholder="e.g., 1234567890123456789",
                                value=(
                                    str(self.tournament.discord_channel_id)
                                    if self.tournament
                                    and self.tournament.discord_channel_id
                                    else ""
                                ),
                            )
                            .classes("w-full")
                            .props("outlined")
                        )
                        ui.label(
                            "Right-click a channel in Discord > Copy Channel ID"
                        ).classes("text-sm text-secondary")
                    else:
                        # No channels and manual entry disabled
                        ui.label("No Discord channels available").classes(
                            "text-warning"
                        )
                        ui.label(
                            "Link a Discord server in the Discord Servers tab to enable channel selection"
                        ).classes("text-sm text-secondary")
                        self.discord_channel_select = None

        ui.separator().classes("my-4")

        # Action buttons
        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button(
                "Save" if self.tournament else "Create", on_click=self._save
            ).classes("btn").props("color=positive")

    async def _save(self):
        """Validate and save tournament data."""
        # Validate required fields
        if (
            not self.name_input
            or not self.name_input.value
            or not self.name_input.value.strip()
        ):
            ui.notify("Tournament name is required", type="warning")
            return

        if not self.runs_per_pool_input or self.runs_per_pool_input.value < 1:
            ui.notify("Runs per pool must be at least 1", type="warning")
            return

        # Determine Discord channel ID (manual input takes precedence)
        discord_channel_id = None
        if (
            self.manual_channel_input
            and self.manual_channel_input.value
            and self.manual_channel_input.value.strip()
        ):
            # Manual entry provided - validate it's a number
            try:
                discord_channel_id = int(self.manual_channel_input.value.strip())
            except ValueError:
                ui.notify("Discord Channel ID must be a number", type="warning")
                return
        elif self.discord_channel_select and self.discord_channel_select.value:
            # Use dropdown selection
            discord_channel_id = self.discord_channel_select.value

        # Prepare data
        data = {
            "name": self.name_input.value.strip(),
            "description": (
                self.description_input.value.strip()
                if self.description_input and self.description_input.value
                else None
            ),
            "is_active": (
                bool(self.is_active_switch.value) if self.is_active_switch else True
            ),
            "hide_results": (
                bool(self.hide_results_switch.value)
                if self.hide_results_switch
                else False
            ),
            "require_racetime_for_async_runs": (
                bool(self.require_racetime_switch.value)
                if self.require_racetime_switch
                else False
            ),
            "runs_per_pool": int(self.runs_per_pool_input.value),
            "discord_channel_id": discord_channel_id,
        }

        # Call the save callback
        if self.on_save:
            try:
                await self.on_save(data)
                await self.close()
            except Exception as e:
                logger.error("Error saving async tournament: %s", e)
                ui.notify(f"Error saving tournament: {str(e)}", type="negative")
        else:
            await self.close()
