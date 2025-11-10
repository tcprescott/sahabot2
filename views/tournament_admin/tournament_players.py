"""
Tournament Players View.

Manage tournament player registrations.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.organizations import Organization
from models.match_schedule import Tournament
from components.data_table import ResponsiveTable, TableColumn
from components.dialogs import RegisterPlayerDialog, ConfirmDialog
from application.services.tournaments.tournament_service import TournamentService
import logging

logger = logging.getLogger(__name__)


class TournamentPlayersView:
    """View for managing tournament players."""

    def __init__(self, user: User, organization: Organization, tournament: Tournament):
        """
        Initialize the players view.

        Args:
            user: Current user
            organization: Tournament's organization
            tournament: Tournament to manage
        """
        self.user = user
        self.organization = organization
        self.tournament = tournament
        self.tournament_service = TournamentService()

    async def render(self):
        """Render the players management view."""
        # Get registrations for this tournament
        registrations = await self.tournament_service.list_tournament_players(
            self.organization.id, self.tournament.id
        )

        async def open_register_dialog():
            """Open dialog to register a new player."""
            dialog = RegisterPlayerDialog(
                admin_user=self.user,
                organization=self.organization,
                tournament=self.tournament,
                on_save=self._refresh,
            )
            await dialog.show()

        async def unregister_player(registration):
            """Unregister a player from the tournament."""

            async def confirm_unregister():
                result = (
                    await self.tournament_service.admin_unregister_user_from_tournament(
                        admin_user=self.user,
                        organization_id=self.organization.id,
                        tournament_id=self.tournament.id,
                        user_id=registration.user_id,
                    )
                )
                if result:
                    ui.notify("Player unregistered successfully", type="positive")
                    await self._refresh()
                else:
                    ui.notify("Failed to unregister player", type="negative")

            dialog = ConfirmDialog(
                title="Unregister Player",
                message=f"Are you sure you want to unregister {registration.user.get_display_name()} from this tournament?",
                on_confirm=confirm_unregister,
            )
            await dialog.show()

        with ui.element("div").classes("card"):
            with ui.element("div").classes("card-header"):
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label(f"Registered Players ({len(registrations)})").classes(
                        "text-xl font-bold"
                    )
                    ui.button(
                        "Register Player",
                        icon="person_add",
                        on_click=open_register_dialog,
                    ).classes("btn").props("color=primary")

            with ui.element("div").classes("card-body"):
                if not registrations:
                    with ui.element("div").classes("text-center mt-4"):
                        ui.icon("people_outline").classes("text-secondary icon-large")
                        ui.label("No players registered yet").classes("text-secondary")
                        ui.label(
                            'Click "Register Player" to add players to this tournament'
                        ).classes("text-secondary text-sm")
                else:

                    def render_username(reg):
                        with ui.row().classes("items-center gap-2"):
                            ui.label(reg.user.get_display_name())
                            if reg.user.is_placeholder:
                                from components.badge import Badge

                                Badge.placeholder(True)

                    def render_registered_date(reg):
                        from components.datetime_label import DateTimeLabel

                        DateTimeLabel.datetime(reg.created_at)

                    def render_actions(reg):
                        ui.button(
                            icon="person_remove",
                            on_click=lambda r=reg: unregister_player(r),
                        ).classes("btn btn-sm").props("flat color=negative").tooltip(
                            "Unregister player"
                        )

                    columns = [
                        TableColumn("Username", cell_render=render_username),
                        TableColumn("Registered", cell_render=render_registered_date),
                        TableColumn("Actions", cell_render=render_actions),
                    ]

                    table = ResponsiveTable(columns, registrations)
                    await table.render()

    async def _refresh(self):
        """Refresh the view after changes."""
        # Trigger a page reload of the players view
        ui.navigate.reload()
