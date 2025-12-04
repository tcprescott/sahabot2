"""
Async Qualifier Review Queue view.

Displays a list of async races awaiting review with filtering and review capabilities.
Only accessible to users with ASYNC_REVIEWER or ADMIN permissions.
"""

from nicegui import ui
import httpx

from models import User
from modules.async_qualifier.models.async_qualifier import AsyncQualifier
from components.card import Card
from components.empty_state import EmptyState
from components.data_table import ResponsiveTable, TableColumn
from components.dialogs.async_qualifiers import RaceReviewDialog


class AsyncReviewQueueView:
    """View for reviewing async qualifier races."""

    def __init__(self, tournament: AsyncQualifier, user: User, organization_id: int):
        """
        Initialize the review queue view.

        Args:
            tournament: The async qualifier
            user: Current user
            organization_id: Organization ID
        """
        self.tournament = tournament
        self.user = user
        self.organization_id = organization_id
        self.races = []
        self.selected_status = "finished"
        self.selected_review_status = "pending"
        self.selected_reviewer = -1  # -1 = unreviewed
        self.status_select = None
        self.review_status_select = None
        self.reviewer_select = None
        self.race_list_container = None

    async def render(self):
        """Render the review queue view."""
        with Card.create(title=f"Review Queue - {self.tournament.name}"):
            ui.label("Review and approve async race submissions").classes(
                "text-secondary mb-4"
            )

            # Filters
            with ui.row().classes("gap-md mb-4 w-full flex-wrap"):
                with ui.element("div").classes("flex-grow"):
                    ui.label("Race Status:").classes("text-sm font-semibold mb-1")
                    status_select = ui.select(
                        options=[
                            "all",
                            "pending",
                            "in_progress",
                            "finished",
                            "forfeit",
                            "disqualified",
                        ],
                        value=self.selected_status,
                        on_change=self._on_filter_change,
                    ).classes("w-full")

                with ui.element("div").classes("flex-grow"):
                    ui.label("Review Status:").classes("text-sm font-semibold mb-1")
                    review_status_select = ui.select(
                        options=["all", "pending", "accepted", "rejected"],
                        value=self.selected_review_status,
                        on_change=self._on_filter_change,
                    ).classes("w-full")

                with ui.element("div").classes("flex-grow"):
                    ui.label("Reviewer:").classes("text-sm font-semibold mb-1")
                    reviewer_select = ui.select(
                        options={-1: "Unreviewed", 0: "All", self.user.id: "Me"},
                        value=self.selected_reviewer,
                        on_change=self._on_filter_change,
                    ).classes("w-full")

                ui.button("Refresh", on_click=self._load_races, icon="refresh").classes(
                    "btn-primary mt-6"
                )

            # Store select references for filter changes
            self.status_select = status_select
            self.review_status_select = review_status_select
            self.reviewer_select = reviewer_select

            # Race list container
            self.race_list_container = ui.element("div").classes("w-full")

            # Load initial data
            await self._load_races()

    async def _load_races(self):
        """Load races from API."""
        self.race_list_container.clear()

        with self.race_list_container:
            with ui.element("div").classes("flex justify-center p-4"):
                ui.spinner(size="lg")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"/api/async-tournaments/{self.tournament.id}/review-queue",
                    params={
                        "organization_id": self.organization_id,
                        "status": self.selected_status,
                        "review_status": self.selected_review_status,
                        "reviewed_by_id": self.selected_reviewer,
                        "limit": 100,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    self.races = data.get("items", [])
                else:
                    ui.notify(
                        f"Failed to load review queue: {response.status_code}",
                        type="negative",
                    )
                    self.races = []

        except Exception as e:
            ui.notify(f"Error loading review queue: {str(e)}", type="negative")
            self.races = []

        self._render_race_list()

    def _render_race_list(self):
        """Render the race list table."""
        self.race_list_container.clear()

        with self.race_list_container:
            if not self.races:
                EmptyState.no_results(
                    title="No races found",
                    message="Try adjusting your filters to see more results",
                    in_card=False,
                )
                return

            # Define columns for the responsive table
            columns = [
                TableColumn(label="ID", key="id"),
                TableColumn(label="Player", key="player"),
                TableColumn(label="Pool", key="pool"),
                TableColumn(label="Time", key="time"),
                TableColumn(label="Status", key="status"),
                TableColumn(label="Review", key="review_status_display"),
                TableColumn(label="Reviewer", key="reviewed_by"),
                TableColumn(
                    label="Actions",
                    cell_render=lambda row: ui.button(
                        "Review",
                        on_click=lambda r=row: self._open_review_dialog(r["id"]),
                    ).props("size=sm color=primary"),
                ),
            ]

            # Transform races into table rows
            rows = []
            for race in self.races:
                # Build review status display with flag indicator
                review_status_text = race["review_status"].title()
                if (
                    race.get("review_requested_by_user")
                    and race["review_status"] == "pending"
                ):
                    review_status_text = f"🚩 {review_status_text} (User Flagged)"

                rows.append(
                    {
                        "id": race["id"],
                        "player": race["user"]["discord_username"],
                        "pool": race.get("pool_name", "N/A"),
                        "time": race["elapsed_time_formatted"],
                        "status": race["status"].title(),
                        "review_status_display": review_status_text,
                        "reviewed_by": (
                            race["reviewed_by"]["discord_username"]
                            if race.get("reviewed_by")
                            else "None"
                        ),
                        "flagged": race.get(
                            "review_requested_by_user", False
                        ),  # For potential future styling
                    }
                )

            # Render the responsive table
            table = ResponsiveTable(columns=columns, rows=rows, table_classes="mt-4")

            # Run the render in an async context
            async def render_table():
                await table.render()

            ui.timer(0, render_table, once=True)

    def _on_filter_change(self):
        """Handle filter changes."""
        self.selected_status = self.status_select.value
        self.selected_review_status = self.review_status_select.value
        self.selected_reviewer = self.reviewer_select.value
        ui.run_javascript("window.WindowUtils.dispatchResize(100);")

    def _open_review_dialog(self, race_id: int):
        """Open the review dialog for a specific race."""
        # Find the race data
        race_data = next((r for r in self.races if r["id"] == race_id), None)
        if not race_data:
            ui.notify("Race not found", type="negative")
            return

        dialog = RaceReviewDialog(
            race_data=race_data,
            organization_id=self.organization_id,
            on_save=self._load_races,
        )
        dialog.show()
