"""
Match cell renderers for tournament schedule tables.

Provides reusable rendering functions for table cells in match schedules.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import Match
from components.datetime_label import DateTimeLabel

logger = logging.getLogger(__name__)


class MatchCellRenderers:
    """Reusable cell renderers for match schedule tables."""

    @staticmethod
    def render_tournament(match: Match) -> None:
        """Render tournament name."""
        ui.label(match.tournament.name)

    @staticmethod
    def render_title(match: Match) -> None:
        """Render match title with SpeedGaming badge if applicable."""
        with ui.row().classes("items-center gap-2"):
            if match.title:
                ui.label(match.title)
            else:
                ui.label("—").classes("text-secondary")

            # Show SpeedGaming badge if imported from SpeedGaming
            if (
                hasattr(match, "speedgaming_episode_id")
                and match.speedgaming_episode_id
            ):
                ui.badge("SpeedGaming").classes("badge-info").tooltip(
                    "Imported from SpeedGaming"
                )

    @staticmethod
    def render_scheduled_time(match: Match) -> None:
        """Render scheduled time or TBD."""
        if match.scheduled_at:
            DateTimeLabel.datetime(match.scheduled_at)
        else:
            ui.label("TBD").classes("text-secondary")

    @staticmethod
    def render_stream(match: Match) -> None:
        """Render stream channel name."""
        if match.stream_channel:
            ui.label(match.stream_channel.name)
        else:
            ui.label("—").classes("text-secondary")

    @staticmethod
    def render_players(match: Match) -> None:
        """Render the players participating in this match."""
        players = getattr(match, "players", [])

        if players:
            with ui.column().classes("gap-1"):
                for player in players:
                    display_name = player.user.get_display_name()
                    # Add checkmark for winner (finish_rank == 1)
                    is_winner = player.finish_rank == 1
                    if is_winner:
                        display_name = f"✓ {display_name}"
                    
                    # Show station number if assigned (onsite tournaments)
                    if player.assigned_station:
                        with ui.row().classes("gap-1 items-center"):
                            ui.label(display_name).classes("text-sm")
                            ui.label(
                                f"({player.assigned_station})"
                            ).classes("text-sm text-secondary")
                    else:
                        ui.label(display_name).classes("text-sm")
        else:
            ui.label("—").classes("text-secondary")
