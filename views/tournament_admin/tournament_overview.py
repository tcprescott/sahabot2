"""
Tournament Overview View.

Shows tournament dashboard with stats and quick actions.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.organizations import Organization
from models.async_tournament import AsyncTournament
from application.repositories.audit_repository import AuditRepository
from components.datetime_label import DateTimeLabel


class TournamentOverviewView:
    """View for tournament overview dashboard."""

    def __init__(
        self, user: User, organization: Organization, tournament: AsyncTournament
    ):
        """
        Initialize the overview view.

        Args:
            user: Current user
            organization: Tournament's organization
            tournament: Tournament to display
        """
        self.user = user
        self.organization = organization
        self.tournament = tournament
        self.audit_repository = AuditRepository()

    async def render(self):
        """Render the tournament overview."""
        with ui.element("div").classes("card"):
            with ui.element("div").classes("card-header"):
                ui.label("Tournament Overview").classes("text-xl font-bold")

            with ui.element("div").classes("card-body"):
                # Tournament info
                with ui.row().classes("gap-4 mb-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("Name:").classes("font-bold")
                        ui.label(self.tournament.name)

                    with ui.column().classes("flex-1"):
                        ui.label("Status:").classes("font-bold")
                        status_text = (
                            "Active" if self.tournament.is_active else "Inactive"
                        )
                        ui.label(status_text)

                ui.separator()

                # Description
                ui.label("Description:").classes("font-bold mt-4 mb-2")
                ui.label(
                    self.tournament.description or "No description provided"
                ).classes("text-sm")

                ui.separator()

                # Quick stats (placeholders for future implementation)
                ui.label("Quick Stats").classes("text-lg font-bold mt-4 mb-2")
                with ui.row().classes("gap-4"):
                    with ui.element("div").classes("card flex-1"):
                        with ui.element("div").classes("card-body text-center"):
                            ui.label("0").classes("text-3xl font-bold")
                            ui.label("Total Matches").classes("text-sm text-grey")

                    with ui.element("div").classes("card flex-1"):
                        with ui.element("div").classes("card-body text-center"):
                            ui.label("0").classes("text-3xl font-bold")
                            ui.label("Active Players").classes("text-sm text-grey")

                    with ui.element("div").classes("card flex-1"):
                        with ui.element("div").classes("card-body text-center"):
                            ui.label("0").classes("text-3xl font-bold")
                            ui.label("Completed Races").classes("text-sm text-grey")

        # SpeedGaming Integration section (if enabled)
        if self.tournament.speedgaming_enabled:
            await self._render_speedgaming_sync_section()

    async def _render_speedgaming_sync_section(self):
        """Render SpeedGaming sync information section."""
        with ui.element("div").classes("card mt-4"):
            with ui.element("div").classes("card-header"):
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label("SpeedGaming Integration").classes("text-xl font-bold")
                    ui.badge("Active").classes("badge-success")

            with ui.element("div").classes("card-body"):
                # Integration info
                with ui.row().classes("gap-4 mb-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("Event Slug:").classes("font-bold")
                        ui.label(
                            self.tournament.speedgaming_event_slug or "Not configured"
                        ).classes("text-sm")

                    with ui.column().classes("flex-1"):
                        ui.label("Sync Frequency:").classes("font-bold")
                        ui.label("Every 5 minutes").classes("text-sm")

                ui.separator().classes("my-4")

                # Sync History
                ui.label("Recent Sync Activity").classes("text-lg font-bold mb-2")

                # Fetch recent sync logs via repository
                sync_logs = await self.audit_repository.get_speedgaming_sync_logs_for_tournament(
                    organization_id=self.organization.id,
                    tournament_id=self.tournament.id,
                    limit=10,
                )

                if not sync_logs:
                    with ui.element("div").classes("text-center py-4"):
                        ui.icon("sync").classes("text-secondary icon-large")
                        ui.label("No sync activity yet").classes("text-secondary")
                        ui.label("The next sync will occur within 5 minutes").classes(
                            "text-secondary text-sm"
                        )
                else:
                    # Display sync history table
                    with ui.element("div").classes("overflow-x-auto"):
                        with ui.element("table").classes("data-table"):
                            # Header
                            with ui.element("thead"):
                                with ui.element("tr"):
                                    with ui.element("th").classes("text-left"):
                                        ui.label("Time")
                                    with ui.element("th").classes("text-left"):
                                        ui.label("Status")
                                    with ui.element("th").classes("text-center"):
                                        ui.label("Imported")
                                    with ui.element("th").classes("text-center"):
                                        ui.label("Updated")
                                    with ui.element("th").classes("text-center"):
                                        ui.label("Deleted")
                                    with ui.element("th").classes("text-left"):
                                        ui.label("Duration")
                                    with ui.element("th").classes("text-left"):
                                        ui.label("Details")

                            # Body
                            with ui.element("tbody"):
                                for log in sync_logs:
                                    details = log.details or {}
                                    success = details.get("success", False)
                                    error = details.get("error")

                                    with ui.element("tr"):
                                        # Time
                                        with ui.element("td"):
                                            DateTimeLabel.create(
                                                log.created_at, format_type="relative"
                                            )

                                        # Status
                                        with ui.element("td"):
                                            if success:
                                                ui.badge("Success").classes(
                                                    "badge-success"
                                                )
                                            else:
                                                ui.badge("Failed").classes(
                                                    "badge-danger"
                                                )

                                        # Imported
                                        with ui.element("td").classes("text-center"):
                                            imported = details.get("imported", 0)
                                            if imported > 0:
                                                ui.label(str(imported)).classes(
                                                    "text-positive font-bold"
                                                )
                                            else:
                                                ui.label(str(imported)).classes(
                                                    "text-secondary"
                                                )

                                        # Updated
                                        with ui.element("td").classes("text-center"):
                                            updated = details.get("updated", 0)
                                            if updated > 0:
                                                ui.label(str(updated)).classes(
                                                    "text-info font-bold"
                                                )
                                            else:
                                                ui.label(str(updated)).classes(
                                                    "text-secondary"
                                                )

                                        # Deleted
                                        with ui.element("td").classes("text-center"):
                                            deleted = details.get("deleted", 0)
                                            if deleted > 0:
                                                ui.label(str(deleted)).classes(
                                                    "text-warning font-bold"
                                                )
                                            else:
                                                ui.label(str(deleted)).classes(
                                                    "text-secondary"
                                                )

                                        # Duration
                                        with ui.element("td"):
                                            duration_ms = details.get("duration_ms")
                                            if duration_ms is not None:
                                                if duration_ms < 1000:
                                                    ui.label(
                                                        f"{duration_ms}ms"
                                                    ).classes("text-sm")
                                                else:
                                                    ui.label(
                                                        f"{duration_ms / 1000:.1f}s"
                                                    ).classes("text-sm")
                                            else:
                                                ui.label("—").classes("text-secondary")

                                        # Details/Error
                                        with ui.element("td"):
                                            if error:
                                                with ui.row().classes(
                                                    "items-center gap-1"
                                                ):
                                                    ui.icon("error", size="sm").classes(
                                                        "text-negative"
                                                    )
                                                    ui.label(error).classes(
                                                        "text-sm text-negative"
                                                    )
                                            else:
                                                ui.label("—").classes(
                                                    "text-secondary text-sm"
                                                )

                # Error summary (if any recent errors)
                recent_errors = [
                    log
                    for log in sync_logs
                    if log.details and not log.details.get("success", False)
                ]
                if recent_errors:
                    ui.separator().classes("my-4")
                    with ui.element("div").classes("p-3 bg-danger-light rounded"):
                        with ui.row().classes("items-start gap-2"):
                            ui.icon("warning", color="negative")
                            with ui.column().classes("gap-1"):
                                ui.label("Recent Sync Errors").classes(
                                    "font-bold text-negative"
                                )
                                ui.label(
                                    f"{len(recent_errors)} of the last {len(sync_logs)} sync attempts failed. "
                                    "Check the sync history above for details."
                                ).classes("text-sm")

        # Placeholder Users section (if SpeedGaming enabled)
        if self.tournament.speedgaming_enabled:
            await self._render_placeholder_users_section()

    async def _render_placeholder_users_section(self):
        """Render section showing placeholder users from SpeedGaming imports."""
        from application.repositories.user_repository import UserRepository

        # Get placeholder users via repository
        user_repo = UserRepository()
        all_placeholders = await user_repo.get_placeholder_users_for_tournament(
            self.tournament.id
        )

        if not all_placeholders:
            return  # No placeholder users, don't show section

        # Render placeholder users card
        with ui.element("div").classes("card mt-4"):
            with ui.element("div").classes("card-header"):
                ui.label("Placeholder Users from SpeedGaming").classes(
                    "text-lg font-bold"
                )
                ui.label(
                    f"{len(all_placeholders)} placeholder user(s) created from SpeedGaming imports"
                ).classes("text-sm text-secondary")

            with ui.element("div").classes("card-body"):
                ui.label(
                    "These users were automatically created when importing matches/crew from SpeedGaming. "
                    "They should be linked to real Discord accounts by the users themselves."
                ).classes("text-sm mb-3")

                # Display placeholder users as a simple list
                with ui.element("div").classes("overflow-x-auto"):
                    with ui.element("table").classes("data-table"):
                        # Header
                        with ui.element("thead"):
                            with ui.element("tr"):
                                with ui.element("th").classes("text-left"):
                                    ui.label("Username")
                                with ui.element("th").classes("text-left"):
                                    ui.label("Display Name")
                                with ui.element("th").classes("text-left"):
                                    ui.label("Created")
                                with ui.element("th").classes("text-left"):
                                    ui.label("Roles")

                        # Body
                        with ui.element("tbody"):
                            for placeholder in all_placeholders:
                                with ui.element("tr"):
                                    # Username
                                    with ui.element("td"):
                                        ui.label(placeholder.discord_username).classes(
                                            "font-mono"
                                        )

                                    # Display Name
                                    with ui.element("td"):
                                        if placeholder.display_name:
                                            ui.label(placeholder.display_name)
                                        else:
                                            ui.label("—").classes("text-secondary")

                                    # Created date
                                    with ui.element("td"):
                                        DateTimeLabel.create(
                                            placeholder.created_at,
                                            format_type="relative",
                                        )

                    # Role column
                    with ui.element("td"):
                        # Use role metadata from repository if available
                        if hasattr(placeholder, "_placeholder_roles"):
                            roles = placeholder._placeholder_roles
                        else:
                            # Fallback: determine roles from prefetched data
                            roles = []
                            if hasattr(placeholder, "match_players"):
                                try:
                                    match_players = (
                                        await placeholder.match_players.all()
                                    )
                                    if match_players:
                                        roles.append("Player")
                                except:
                                    pass
                            if hasattr(placeholder, "crew_memberships"):
                                try:
                                    crew_memberships = (
                                        await placeholder.crew_memberships.all()
                                    )
                                    if crew_memberships:
                                        roles.append("Crew")
                                except:
                                    pass

                        ui.label(", ".join(roles) if roles else "—")
