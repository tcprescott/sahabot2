"""
Async Tournament Leaderboard View.

Shows tournament leaderboard with player scores and filtering options.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.async_tournament import AsyncTournament
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from application.services.tournaments.async_tournament_service import (
    AsyncTournamentService,
    LeaderboardEntry,
)


class AsyncLeaderboardView:
    """View for async tournament leaderboard."""

    def __init__(self, user: User, tournament: AsyncTournament):
        self.user = user
        self.tournament = tournament
        self.service = AsyncTournamentService()

    async def render(self):
        """Render the leaderboard view."""
        # Check if results should be hidden
        if self.tournament.hide_results and self.tournament.is_active:
            await self._render_hidden_state()
            return

        # Get leaderboard
        leaderboard = await self.service.get_leaderboard(
            self.user, self.tournament.organization_id, self.tournament.id
        )

        # Get pools
        await self.tournament.fetch_related("pools")
        pools = list(self.tournament.pools)

        # Render header
        await self._render_header(leaderboard)

        # Render leaderboard
        if not leaderboard:
            await self._render_empty_state()
        else:
            await self._render_leaderboard_table(leaderboard, pools)

    async def _render_hidden_state(self):
        """Render hidden state when results are private."""
        with Card.create(title=f"{self.tournament.name} - Leaderboard"):
            with ui.element("div").classes(
                "flex flex-wrap justify-between items-center gap-md"
            ):
                # Description
                if self.tournament.description:
                    with ui.element("div").classes("flex-grow"):
                        ui.markdown(self.tournament.description)

        with Card.create(title="Standings"):
            with ui.element("div").classes("text-center py-8"):
                ui.icon("visibility_off").classes("text-secondary icon-large")
                ui.label("Results Hidden").classes("text-secondary text-lg mt-4")
                ui.label(
                    "Player results will be visible after the tournament ends"
                ).classes("text-secondary mt-2")

    async def _render_header(self, leaderboard: list[LeaderboardEntry]):
        """Render tournament header with stats."""
        with Card.create(title=f"{self.tournament.name} - Leaderboard"):
            with ui.element("div").classes(
                "flex flex-wrap justify-between items-center gap-md"
            ):
                # Description
                if self.tournament.description:
                    with ui.element("div").classes("flex-grow"):
                        ui.markdown(self.tournament.description)

                # Stats
                with ui.element("div").classes("flex gap-md"):
                    # Participant count
                    with ui.element("div").classes("text-center"):
                        ui.label(str(len(leaderboard))).classes("stat-value text-lg")
                        ui.label("Participants").classes("stat-label text-xs")

                    # Runs per pool
                    with ui.element("div").classes("text-center"):
                        ui.label(str(self.tournament.runs_per_pool)).classes(
                            "stat-value text-lg"
                        )
                        ui.label("Runs/Pool").classes("stat-label text-xs")

    async def _render_empty_state(self):
        """Render empty state."""
        with Card.create(title="Standings"):
            with ui.element("div").classes("text-center py-8"):
                ui.icon("leaderboard").classes("text-secondary icon-large")
                ui.label("No entries yet").classes("text-secondary text-lg mt-4")
                ui.label("Be the first to complete a race!").classes(
                    "text-secondary mt-2"
                )

    async def _render_leaderboard_table(
        self, leaderboard: list[LeaderboardEntry], pools: list
    ):
        """Render leaderboard table with filtering."""
        # Sort by score descending
        sorted_leaderboard = sorted(leaderboard, key=lambda e: e.score, reverse=True)

        with Card.create(title="Standings"):
            # Filter controls
            with ui.element("div").classes("flex flex-wrap gap-md mb-4"):
                # Search by player name
                search_input = ui.input(
                    label="Search Player", placeholder="Enter player name..."
                ).classes("filter-select")

                # Min races filter
                min_races_input = ui.number(
                    label="Min Completed Races", value=0, min=0
                ).classes("filter-select")

            # Container for filtered results
            leaderboard_container = ui.element("div")

            async def refresh_leaderboard():
                """Refresh leaderboard based on filters."""
                leaderboard_container.clear()
                with leaderboard_container:
                    await self._render_filtered_leaderboard(
                        sorted_leaderboard,
                        pools,
                        search_input.value or "",
                        int(min_races_input.value or 0),
                    )

            search_input.on("update:model-value", refresh_leaderboard)
            min_races_input.on("update:model-value", refresh_leaderboard)

            # Initial render
            with leaderboard_container:
                await self._render_filtered_leaderboard(
                    sorted_leaderboard, pools, "", 0
                )

    async def _render_filtered_leaderboard(
        self,
        leaderboard: list[LeaderboardEntry],
        pools: list,
        search_term: str,
        min_races: int,
    ):
        """Render filtered leaderboard content."""
        # Apply filters
        filtered = leaderboard
        if search_term:
            filtered = [
                e
                for e in filtered
                if search_term.lower() in e.user.get_display_name().lower()
            ]
        if min_races > 0:
            filtered = [e for e in filtered if e.finished_race_count >= min_races]

        if not filtered:
            with ui.element("div").classes("text-center py-4"):
                ui.label("No players match the selected filters").classes(
                    "text-secondary"
                )
            return

        # Desktop: Full table
        with ui.element("div").classes("hidden md:block"):
            await self._render_desktop_leaderboard(filtered, pools)

        # Mobile: Card view
        with ui.element("div").classes("block md:hidden"):
            await self._render_mobile_leaderboard(filtered)

    async def _render_desktop_leaderboard(
        self, leaderboard: list[LeaderboardEntry], pools
    ):  # noqa: ARG002
        """Render desktop leaderboard table."""
        # Create leaderboard with rank data
        ranked_leaderboard = [
            {"rank": i + 1, "entry": entry} for i, entry in enumerate(leaderboard)
        ]

        # Define columns
        columns = [
            TableColumn(
                label="Rank", cell_render=lambda item: self._render_rank(item["rank"])
            ),
            TableColumn(
                label="Player",
                cell_render=lambda item: self._render_player(item["entry"]),
            ),
            TableColumn(
                label="Total Score",
                cell_render=lambda item: self._render_score(item["entry"]),
                cell_classes="font-bold text-success",
            ),
            TableColumn(
                label="Completed",
                cell_render=lambda item: ui.label(
                    str(item["entry"].finished_race_count)
                ),
            ),
            TableColumn(
                label="Forfeit",
                cell_render=lambda item: self._render_forfeit(item["entry"]),
            ),
            TableColumn(
                label="Remaining",
                cell_render=lambda item: ui.label(
                    str(item["entry"].unattempted_race_count)
                ),
            ),
            TableColumn(
                label="Actions",
                cell_render=lambda item: self._render_actions(item["entry"]),
            ),
        ]

        # Render table
        table = ResponsiveTable(columns=columns, rows=ranked_leaderboard)
        await table.render()

    def _render_rank(self, rank: int):
        """Render rank cell."""
        rank_display = str(rank)
        if rank == 1:
            rank_display = "🥇 1st"
        elif rank == 2:
            rank_display = "🥈 2nd"
        elif rank == 3:
            rank_display = "🥉 3rd"
        ui.label(rank_display)

    def _render_player(self, entry: LeaderboardEntry):
        """Render player cell."""
        player_name = entry.user.get_display_name()
        if entry.user.id == self.user.id:
            player_name += " (You)"
        ui.label(player_name).classes("font-bold")

    def _render_score(self, entry: LeaderboardEntry):
        """Render score cell."""
        ui.label(f"{entry.score:.1f}")

    def _render_forfeit(self, entry: LeaderboardEntry):
        """Render forfeit cell."""
        forfeit_class = "text-danger" if entry.forfeited_race_count > 0 else ""
        ui.label(str(entry.forfeited_race_count)).classes(forfeit_class)

    def _render_actions(self, entry: LeaderboardEntry):
        """Render actions cell."""
        player_link = f"/org/{self.tournament.organization_id}/async/{self.tournament.id}/player/{entry.user.id}"
        ui.link("View History", player_link).classes("btn-link")  # Internal link

    async def _render_mobile_leaderboard(self, leaderboard: list[LeaderboardEntry]):
        """Render mobile leaderboard cards."""
        for rank, entry in enumerate(leaderboard, 1):
            await self._render_mobile_card(rank, entry)

    async def _render_mobile_card(self, rank: int, entry: LeaderboardEntry):
        """Render mobile leaderboard card."""
        # Highlight current user
        card_class = "border-primary" if entry.user.id == self.user.id else ""

        with ui.element("div").classes(f"card mb-4 {card_class}"):
            with ui.element("div").classes("card-body"):
                # Rank and Player
                with ui.element("div").classes(
                    "flex justify-between items-center mb-3"
                ):
                    with ui.element("div"):
                        # Rank with medal
                        rank_display = str(rank)
                        if rank == 1:
                            rank_display = "🥇 1st"
                        elif rank == 2:
                            rank_display = "🥈 2nd"
                        elif rank == 3:
                            rank_display = "🥉 3rd"
                        ui.label(rank_display).classes("badge badge-primary")

                    with ui.element("div"):
                        player_name = entry.user.get_display_name()
                        if entry.user.id == self.user.id:
                            player_name += " (You)"
                        ui.label(player_name).classes("font-bold")

                # Score (large)
                with ui.element("div").classes("text-center my-3"):
                    ui.label(f"{entry.score:.1f}").classes(
                        "text-3xl font-bold text-success"
                    )
                    ui.label("Total Score").classes("text-sm text-secondary")

                # Stats grid
                with ui.element("div").classes("grid grid-cols-3 gap-md mt-3"):
                    # Completed
                    with ui.element("div").classes("text-center"):
                        ui.label(str(entry.finished_race_count)).classes("font-bold")
                        ui.label("Completed").classes("text-xs text-secondary")

                    # Forfeit
                    with ui.element("div").classes("text-center"):
                        forfeit_class = (
                            "text-danger" if entry.forfeited_race_count > 0 else ""
                        )
                        ui.label(str(entry.forfeited_race_count)).classes(
                            f"font-bold {forfeit_class}"
                        )
                        ui.label("Forfeit").classes("text-xs text-secondary")

                    # Remaining
                    with ui.element("div").classes("text-center"):
                        ui.label(str(entry.unattempted_race_count)).classes("font-bold")
                        ui.label("Remaining").classes("text-xs text-secondary")

                # View history button
                player_link = f"/org/{self.tournament.organization_id}/async/{self.tournament.id}/player/{entry.user.id}"
                ui.button(
                    "View Race History", on_click=lambda: ui.navigate.to(player_link)
                ).classes("btn btn-sm w-full mt-3")
