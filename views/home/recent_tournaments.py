"""
Recent tournaments view for home page.

Shows user's recently accessed tournaments.
"""

import logging
from nicegui import ui
from models import User
from application.services.tournaments.tournament_usage_service import (
    TournamentUsageService,
)
from components.card import Card
from components.datetime_label import DateTimeLabel

logger = logging.getLogger(__name__)


class RecentTournamentsView:
    """View showing user's recently accessed tournaments."""

    def __init__(self, user: User):
        """
        Initialize the recent tournaments view.

        Args:
            user: Current user
        """
        self.user = user
        self.usage_service = TournamentUsageService()

    async def render(self):
        """Render the recent tournaments view."""
        recent_tournaments = await self.usage_service.get_recent_tournaments(
            self.user, limit=5
        )

        with Card.create(title="Recent Tournaments"):
            if not recent_tournaments:
                with ui.element("div").classes("text-center py-4"):
                    ui.icon("event_note").classes("text-secondary icon-large")
                    ui.label("No recent tournaments").classes("text-secondary")
                    ui.label("Visit tournaments to see them here").classes(
                        "text-secondary text-sm"
                    )
            else:
                with ui.column().classes("gap-sm w-full"):
                    for tournament_info in recent_tournaments:
                        with ui.element("div").classes("card"):
                            with ui.element("div").classes("card-body"):
                                with ui.row().classes(
                                    "w-full items-center justify-between"
                                ):
                                    with ui.column().classes("gap-1 flex-grow"):
                                        # Tournament name as clickable link
                                        ui.link(
                                            tournament_info["tournament_name"],
                                            f"/org/{tournament_info['organization_id']}/tournament?tournament_id={tournament_info['tournament_id']}",
                                        ).classes("text-lg font-semibold")

                                        # Organization name
                                        with ui.row().classes("gap-2 items-center"):
                                            ui.icon("business").classes(
                                                "text-sm text-secondary"
                                            )
                                            ui.label(
                                                tournament_info["organization_name"]
                                            ).classes("text-sm text-secondary")

                                        # Last accessed time
                                        with ui.row().classes("gap-2 items-center"):
                                            ui.icon("schedule").classes(
                                                "text-sm text-secondary"
                                            )
                                            ui.label("Last visited:").classes(
                                                "text-xs text-secondary"
                                            )
                                            DateTimeLabel.datetime(
                                                tournament_info["last_accessed"],
                                                classes="text-xs",
                                            )

                                    # Quick access button
                                    with ui.column().classes("items-end"):
                                        ui.button(
                                            icon="arrow_forward",
                                            on_click=lambda t=tournament_info: ui.navigate.to(
                                                f"/org/{t['organization_id']}/tournament?tournament_id={t['tournament_id']}"
                                            ),
                                        ).classes("btn-icon").props("flat")
