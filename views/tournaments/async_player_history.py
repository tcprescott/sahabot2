"""
Async Tournament Player History View.

Shows all races for a specific player in a tournament.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.async_tournament import AsyncTournament
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from components.dialogs.tournaments import RaceReattemptDialog
from application.services.tournaments.async_tournament_service import (
    AsyncTournamentService,
)


class AsyncPlayerHistoryView:
    """View for a player's race history in an async tournament."""

    def __init__(self, current_user: User, tournament: AsyncTournament, player_id: int):
        self.current_user = current_user
        self.tournament = tournament
        self.player_id = player_id
        self.service = AsyncTournamentService()

    async def render(self):
        """Render the player history view."""
        # Get player
        from application.services.core.user_service import UserService

        user_service = UserService()
        player = await user_service.get_user_by_id(self.player_id)

        if not player:
            ui.label("Player not found").classes("text-danger")
            return

        # Check if results should be hidden
        is_viewing_own_history = self.current_user.id == player.id
        if (
            self.tournament.hide_results
            and self.tournament.is_active
            and not is_viewing_own_history
        ):
            with Card.create(
                title=f"{self.tournament.name} - {player.discord_username}"
            ):
                with ui.element("div").classes("text-center py-8"):
                    ui.icon("visibility_off").classes("text-secondary icon-large")
                    ui.label("Player Results Hidden").classes(
                        "text-secondary text-lg mt-4"
                    )
                    ui.label(
                        "Player results will be visible after the tournament ends"
                    ).classes("text-secondary mt-2")
            return

        with Card.create(title=f"{self.tournament.name} - {player.discord_username}"):
            # Get player's races
            races = await self.service.get_user_races(
                player,  # Use the player user object
                self.tournament.organization_id,
                self.tournament.id,
            )

            if not races:
                with ui.element("div").classes("text-center mt-4"):
                    ui.icon("history").classes("text-secondary icon-large")
                    ui.label("No race history").classes("text-secondary")
                return

            # Races table
            await self._render_races_table(races)

    async def _render_races_table(self, races):
        """Render table of races."""
        # Define columns
        columns = [
            TableColumn(label="ID", key="id"),
            TableColumn(
                label="Date/Time", cell_render=lambda r: self._render_datetime(r)
            ),
            TableColumn(
                label="Pool", cell_render=lambda r: ui.label(r.permalink.pool.name)
            ),
            TableColumn(
                label="Permalink", cell_render=lambda r: self._render_permalink(r)
            ),
            TableColumn(label="VOD", cell_render=lambda r: self._render_vod(r)),
            TableColumn(label="Thread", cell_render=lambda r: self._render_thread(r)),
            TableColumn(label="Finish Time", key="elapsed_time_formatted"),
            TableColumn(label="Score", key="score_formatted"),
            TableColumn(label="Status", cell_render=lambda r: self._render_status(r)),
            TableColumn(
                label="Reattempted", cell_render=lambda r: self._render_reattempted(r)
            ),
            TableColumn(label="Actions", cell_render=lambda r: self._render_actions(r)),
        ]

        # Fetch related data for all races
        for race in races:
            await race.fetch_related("permalink", "permalink__pool")

        # Render table
        table = ResponsiveTable(columns=columns, rows=races)
        await table.render()

    def _render_datetime(self, race):
        """Render date/time cell."""
        if race.thread_open_time:
            time_str = race.thread_open_time.strftime("%Y-%m-%d %H:%M")
        else:
            time_str = "N/A"
        ui.label(time_str)

    def _render_permalink(self, race):
        """Render permalink cell."""
        permalink_link = f"/org/{self.tournament.organization_id}/async/{self.tournament.id}/permalink/{race.permalink_id}"
        ui.link(race.permalink.url, permalink_link, new_tab=True)

    def _render_vod(self, race):
        """Render VOD cell."""
        if race.runner_vod_url:
            ui.link("VOD", race.runner_vod_url, new_tab=True)
        else:
            ui.label("—")

    def _render_thread(self, race):
        """Render thread cell."""
        if race.discord_thread_id:
            thread_url = f"https://discord.com/channels/@me/{race.discord_thread_id}"
            ui.link("Thread", thread_url, new_tab=True)
        else:
            ui.label("—")

    def _render_status(self, race):
        """Render status cell."""
        status_badge_class = {
            "finished": "badge-success",
            "in_progress": "badge-info",
            "pending": "badge-warning",
            "forfeit": "badge-danger",
            "disqualified": "badge-danger",
        }.get(race.status, "badge")
        ui.label(race.status_formatted).classes(f"badge {status_badge_class}")

    def _render_reattempted(self, race):
        """Render reattempted cell."""
        if race.reattempted:
            ui.label("Yes").classes("badge badge-warning")
        else:
            ui.label("—")

    def _render_actions(self, race):
        """Render actions cell."""
        # Only show re-attempt button for the current user's races
        if self.current_user.id != self.player_id:
            ui.label("—")
            return

        # Only show re-attempt for finished or forfeit races that haven't been reattempted
        if race.status in ["finished", "forfeit"] and not race.reattempted:
            ui.button(
                icon="replay",
                on_click=lambda r=race: self._show_reattempt_dialog(r),
            ).classes("btn btn-sm").tooltip("Re-attempt Race")
        else:
            ui.label("—")

    async def _show_reattempt_dialog(self, race):
        """Show the re-attempt dialog for a race."""
        dialog = RaceReattemptDialog(
            race=race,
            current_user=self.current_user,
            organization_id=self.tournament.organization_id,
            on_success=self._on_reattempt_success,
        )
        await dialog.show()

    async def _on_reattempt_success(self):
        """Handle successful re-attempt."""
        # Re-render the view to show updated status
        await self.render()
