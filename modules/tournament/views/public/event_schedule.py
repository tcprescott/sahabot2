"""
Event Schedule View for tournaments.

Shows upcoming matches and events for the organization.
"""

from __future__ import annotations
import logging
from typing import Optional
from nicegui import ui
from models import Organization, User, CrewRole
from models.user import Permission
from modules.tournament.models.match_schedule import Match
from components.data_table import ResponsiveTable, TableColumn
from components.tournaments import MatchCellRenderers, MatchActions, CrewManagement
from components.dialogs import (
    EditMatchDialog,
    CreateMatchDialog,
    MatchWinnerDialog,
    CheckInDialog,
)
from components.dialogs.common import ConfirmDialog
from application.services.tournaments.tournament_service import TournamentService
from application.services.organizations.organization_service import OrganizationService
from config import Settings

settings = Settings()

logger = logging.getLogger(__name__)


class EventScheduleView:
    """View for displaying event schedule."""

    def __init__(self, organization: Organization, user: User) -> None:
        self.organization = organization
        self.user = user
        self.service = TournamentService()
        self.org_service = OrganizationService()
        self.container = None
        self.matches_container = None  # Separate container for just the matches table
        self.filter_states = [
            "pending",
            "scheduled",
            "checked_in",
        ]  # Default: show pending, scheduled, checked_in
        self.selected_tournaments = []  # List of selected tournament IDs
        self.can_manage_tournaments = False  # Set during render
        self.can_edit_matches = (
            False  # Set during render (moderator or tournament admin)
        )
        self.can_approve_crew = (
            False  # Set during render (admin, tournament manager, or moderator)
        )
        self._filters_loaded = False  # Track if we've loaded filters from localStorage
        self.all_matches = []  # Cache all matches to avoid re-fetching on filter change

        # Initialize component helpers (will be configured after permissions are set)
        self.match_actions = None
        self.crew_management = None

    def _get_match_state(self, match: Match) -> str:
        """Get the state of a match."""
        if match.finished_at:
            return "finished"
        elif match.started_at:
            return "in_progress"
        elif match.checked_in_at:
            return "checked_in"
        elif match.scheduled_at:
            return "scheduled"
        else:
            return "pending"

    def _filter_matches(self, matches):
        """Filter matches based on current filter states and selected tournaments."""
        filtered = []

        for match in matches:
            # Filter by state (if any states are selected)
            if self.filter_states:
                state = self._get_match_state(match)
                if state not in self.filter_states:
                    continue

            # Filter by tournament selection
            if (
                self.selected_tournaments
                and match.tournament_id not in self.selected_tournaments
            ):
                continue

            filtered.append(match)

        return filtered

    async def _on_filter_change(self, new_states) -> None:
        """Handle filter state change."""
        self.filter_states = new_states if new_states else []
        # Save to storage
        await self._save_filters()
        # Update only the matches table, not the entire page
        await self._refresh_matches()

    async def _on_tournament_filter_change(self, selected_ids) -> None:
        """Handle tournament filter change."""
        self.selected_tournaments = selected_ids if selected_ids else []
        # Save to storage
        await self._save_filters()
        # Update only the matches table, not the entire page
        await self._refresh_matches()

    async def _load_filters(self) -> None:
        """Load filters from server-side storage."""
        if self._filters_loaded:
            return

        try:
            from nicegui import app

            # Use NiceGUI's server-side storage (session-based, persists across page loads)
            storage_key = f"event_schedule_filters_{self.organization.id}"

            # Check if we have storage available
            if hasattr(app, "storage") and hasattr(app.storage, "user"):
                saved_filters = app.storage.user.get(storage_key)

                if saved_filters and isinstance(saved_filters, dict):
                    # Apply loaded filters
                    if "states" in saved_filters and saved_filters["states"]:
                        self.filter_states = saved_filters["states"]
                        logger.info("Loaded status filters: %s", self.filter_states)
                    if "tournaments" in saved_filters and saved_filters["tournaments"]:
                        self.selected_tournaments = saved_filters["tournaments"]
                        logger.info(
                            "Loaded tournament filters: %s", self.selected_tournaments
                        )

                    logger.info(
                        "Successfully loaded event schedule filters from user storage for org %s",
                        self.organization.id,
                    )
                else:
                    logger.info(
                        "No saved filters found in user storage, using defaults: states=%s, tournaments=%s",
                        self.filter_states,
                        self.selected_tournaments,
                    )
            else:
                logger.info("User storage not available, using defaults")

            self._filters_loaded = True
        except Exception as e:
            logger.warning(
                "Could not load event schedule filters from user storage: %s", e
            )
            # Continue with default filters
            self._filters_loaded = True

    async def _save_filters(self) -> None:
        """Save filters to server-side storage."""
        try:
            from nicegui import app

            storage_key = f"event_schedule_filters_{self.organization.id}"
            filters = {
                "states": self.filter_states,
                "tournaments": self.selected_tournaments,
            }

            # Use NiceGUI's server-side storage (session-based, persists across page loads)
            if hasattr(app, "storage") and hasattr(app.storage, "user"):
                app.storage.user[storage_key] = filters
                logger.info("Saved event schedule filters to user storage: %s", filters)
            else:
                logger.warning("User storage not available for saving filters")
        except Exception as e:
            logger.warning(
                "Could not save event schedule filters to user storage: %s", e
            )

    async def _refresh(self) -> None:
        """Refresh the view by clearing and re-rendering."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _refresh_matches(self) -> None:
        """Refresh only the matches table without reloading the entire page."""
        if self.matches_container:
            self.matches_container.clear()
            with self.matches_container:
                await self._render_matches_table()

    async def _render_content(self) -> None:
        """Render the actual content."""
        # Check if user can manage tournaments
        self.can_manage_tournaments = (
            await self.org_service.user_can_manage_tournaments(
                self.user, self.organization.id
            )
        )

        # Check if user can edit matches (tournament manager or moderator)
        self.can_edit_matches = self.can_manage_tournaments or (
            self.user.has_permission(Permission.MODERATOR)
            or self.user.has_permission(Permission.ADMIN)
        )

        # Check if user can approve crew
        self.can_approve_crew = await self.org_service.user_can_approve_crew(
            self.user, self.organization.id
        )

        # Initialize component helpers with permissions
        self.match_actions = MatchActions(
            user=self.user,
            organization=self.organization,
            service=self.service,
            can_manage_tournaments=self.can_manage_tournaments,
            on_refresh=self._refresh,
        )
        self.crew_management = CrewManagement(
            user=self.user,
            organization=self.organization,
            service=self.service,
            can_approve_crew=self.can_approve_crew,
            on_refresh=self._refresh,
        )

        # Get all matches for this organization's tournaments via service (cache for filter updates)
        self.all_matches = await self.service.list_org_matches(self.organization.id)

        # Get all tournaments for filter
        all_tournaments = await self.service.list_all_org_tournaments(
            self.organization.id
        )
        tournament_options = {t.id: t.name for t in all_tournaments}

        # Filter bar
        with ui.element("div").classes("card"):
            with ui.element("div").classes("card-body"):
                with ui.row().classes("full-width items-center gap-4 flex-wrap"):
                    ui.label("Filters:").classes("font-semibold")

                    # Status filter (multi-select)
                    ui.select(
                        label="Status",
                        options={
                            "pending": "Pending",
                            "scheduled": "Scheduled",
                            "checked_in": "Checked In",
                            "in_progress": "In Progress",
                            "finished": "Finished",
                        },
                        value=self.filter_states,
                        multiple=True,
                        on_change=lambda e: self._on_filter_change(e.value),
                    ).classes("min-w-[200px]").props("use-chips")

                    # Tournament filter (multi-select)
                    ui.select(
                        label="Tournaments",
                        options=tournament_options,
                        value=self.selected_tournaments,
                        multiple=True,
                        on_change=lambda e: self._on_tournament_filter_change(e.value),
                    ).classes("min-w-[200px]").props("use-chips")

        # Container for matches table (will be updated when filters change)
        self.matches_container = ui.column().classes("w-full")
        with self.matches_container:
            await self._render_matches_table()

    async def _render_matches_table(self) -> None:
        """Render just the matches table (called when filters change)."""
        # Apply filter
        matches = self._filter_matches(self.all_matches)

        # Custom card with header action button
        with ui.element("div").classes("card"):
            # Card header with create match button
            with ui.element("div").classes("card-header"):
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label(
                        f"Event Schedule - {self.organization.name} ({len(matches)}/{len(self.all_matches)})"
                    ).classes("text-xl font-bold")
                    # Show "Create Match" button for tournament admins and admins
                    if self.can_manage_tournaments or self.user.has_permission(
                        Permission.ADMIN
                    ):
                        ui.button(
                            "Create Match",
                            icon="add_circle",
                            on_click=self._create_match,
                        ).classes("btn").props("color=primary")

            # Card body
            with ui.element("div").classes("card-body"):
                if not matches:
                    with ui.element("div").classes("text-center mt-4"):
                        ui.icon("event").classes("text-secondary icon-large")
                        ui.label("No upcoming events").classes("text-secondary")
                        ui.label("Check back later for scheduled matches").classes(
                            "text-secondary text-sm"
                        )
                else:
                    # Use MatchCellRenderers for simple cell rendering
                    renderers = MatchCellRenderers()

                    async def advance_status(
                        match_id: int, status: str, status_label: str
                    ):
                        """Advance match status with confirmation or winner selection."""
                        # Special handling for 'checked_in' status in onsite tournaments - prompt for station numbers
                        if status == "checked_in":
                            # Get match to check if tournament is onsite
                            match = (
                                await Match.filter(id=match_id)
                                .prefetch_related("tournament", "players__user")
                                .first()
                            )
                            if not match:
                                ui.notify("Match not found", type="negative")
                                return

                            # Check if tournament is onsite
                            if match.tournament.onsite_tournament:
                                # Build player list for dialog
                                players = []
                                for mp in match.players:
                                    players.append(
                                        {
                                            "id": mp.user.id,
                                            "username": mp.user.get_display_name(),
                                            "match_player_id": mp.id,
                                        }
                                    )

                                async def on_station_assigned(
                                    station_assignments: dict[int, str]
                                ):
                                    """Handle station assignment and advance status."""
                                    try:
                                        # First advance match status to checked_in
                                        result = (
                                            await self.service.advance_match_status(
                                                user=self.user,
                                                organization_id=self.organization.id,
                                                match_id=match_id,
                                                status=status,
                                            )
                                        )
                                        if not result:
                                            ui.notify(
                                                "Failed to check in match",
                                                type="negative",
                                            )
                                            return

                                        # Then update station assignments
                                        updated = await self.service.update_station_assignments(
                                            user=self.user,
                                            organization_id=self.organization.id,
                                            match_id=match_id,
                                            station_assignments=station_assignments,
                                        )
                                        if updated:
                                            ui.notify(
                                                "Match checked in with station assignments",
                                                type="positive",
                                            )
                                        else:
                                            ui.notify(
                                                "Match checked in (failed to set stations)",
                                                type="warning",
                                            )

                                        await self._refresh()
                                    except ValueError as e:
                                        logger.error("Failed to check in match: %s", e)
                                        ui.notify(f"Failed: {str(e)}", type="negative")
                                    except Exception as e:
                                        logger.error("Failed to check in match: %s", e)
                                        ui.notify(
                                            f"Failed to check in match: {str(e)}",
                                            type="negative",
                                        )

                                # Show check-in dialog with station assignment
                                dialog = CheckInDialog(
                                    match_title=match.title or f"Match {match_id}",
                                    players=players,
                                    on_checkin=on_station_assigned,
                                )
                                await dialog.show()
                                return  # Exit early, dialog handles the rest

                        # Special handling for 'finished' status - show winner selection dialog
                        if status == "finished":
                            # Get match to fetch players
                            match = (
                                await Match.filter(id=match_id)
                                .prefetch_related("players__user")
                                .first()
                            )
                            if not match:
                                ui.notify("Match not found", type="negative")
                                return

                            # Build player list for dialog
                            players = []
                            for mp in match.players:
                                players.append(
                                    {
                                        "id": mp.user.id,
                                        "username": mp.user.get_display_name(),
                                        "match_player_id": mp.id,
                                    }
                                )

                            async def on_winner_selected(match_player_id: int):
                                """Handle winner selection and advance status."""
                                try:
                                    # First advance match status
                                    result = await self.service.advance_match_status(
                                        user=self.user,
                                        organization_id=self.organization.id,
                                        match_id=match_id,
                                        status=status,
                                    )
                                    if not result:
                                        ui.notify(
                                            "Failed to advance match status",
                                            type="negative",
                                        )
                                        return

                                    # Then set the winner
                                    winner = await self.service.set_match_winner(
                                        user=self.user,
                                        organization_id=self.organization.id,
                                        match_id=match_id,
                                        match_player_id=match_player_id,
                                    )
                                    if winner:
                                        ui.notify(
                                            "Match finished and winner set",
                                            type="positive",
                                        )
                                    else:
                                        ui.notify(
                                            "Match finished (failed to set winner)",
                                            type="warning",
                                        )

                                    await self._refresh()
                                except ValueError as e:
                                    logger.error("Failed to finish match: %s", e)
                                    ui.notify(f"Failed: {str(e)}", type="negative")
                                except Exception as e:
                                    logger.error("Failed to finish match: %s", e)
                                    ui.notify(
                                        f"Failed to finish match: {str(e)}",
                                        type="negative",
                                    )

                            # Show winner selection dialog
                            dialog = MatchWinnerDialog(
                                match_title=match.title or f"Match {match_id}",
                                players=players,
                                on_select=on_winner_selected,
                            )
                            await dialog.show()
                        else:
                            # For other statuses, use confirmation dialog
                            async def on_confirm():
                                try:
                                    # Use service layer directly
                                    result = await self.service.advance_match_status(
                                        user=self.user,
                                        organization_id=self.organization.id,
                                        match_id=match_id,
                                        status=status,
                                    )
                                    if result:
                                        ui.notify(
                                            f"Match status advanced to {status_label}",
                                            type="positive",
                                        )
                                        await self._refresh()
                                    else:
                                        ui.notify(
                                            "Failed to advance match status",
                                            type="negative",
                                        )
                                except ValueError as e:
                                    logger.error(
                                        "Failed to advance match status: %s", e
                                    )
                                    ui.notify(f"Failed: {str(e)}", type="negative")
                                except Exception as e:
                                    logger.error(
                                        "Failed to advance match status: %s", e
                                    )
                                    ui.notify(
                                        f"Failed to advance status: {str(e)}",
                                        type="negative",
                                    )

                            dialog = ConfirmDialog(
                                title=f"Advance to {status_label}",
                                message=f"Are you sure you want to advance this match to {status_label}?",
                                on_confirm=on_confirm,
                            )
                            await dialog.show()

                    async def revert_status(
                        match_id: int, status: str, status_label: str
                    ):
                        """Revert match status with confirmation."""

                        async def on_confirm():
                            try:
                                # Use service layer directly
                                result = await self.service.revert_match_status(
                                    user=self.user,
                                    organization_id=self.organization.id,
                                    match_id=match_id,
                                    status=status,
                                )
                                if result:
                                    ui.notify(
                                        f"Match status reverted from {status_label}",
                                        type="positive",
                                    )
                                    await self._refresh()
                                else:
                                    ui.notify(
                                        "Failed to revert match status", type="negative"
                                    )
                            except ValueError as e:
                                logger.error("Failed to revert match status: %s", e)
                                ui.notify(f"Failed: {str(e)}", type="negative")
                            except Exception as e:
                                logger.error("Failed to revert match status: %s", e)
                                ui.notify(
                                    f"Failed to revert status: {str(e)}",
                                    type="negative",
                                )

                        dialog = ConfirmDialog(
                            title=f"Revert from {status_label}",
                            message=f"Are you sure you want to revert this match from {status_label}? This will clear the timestamp.",
                            on_confirm=on_confirm,
                        )
                        await dialog.show()

                    def render_status(match: Match):
                        # Check if match has RaceTime room (cannot advance or revert if it does)
                        has_racetime_room = bool(match.racetime_room)

                        with ui.column().classes("gap-1"):
                            # Show status badge
                            if match.confirmed_at:
                                ui.label("Recorded").classes("badge badge-dark")
                            elif match.finished_at:
                                ui.label("Finished").classes("badge badge-success")
                            elif match.started_at:
                                ui.label("In Progress").classes("badge badge-info")
                            elif match.checked_in_at:
                                ui.label("Checked In").classes("badge badge-warning")
                            elif match.scheduled_at:
                                ui.label("Scheduled").classes("badge badge-secondary")
                            else:
                                ui.label("Pending").classes("badge")

                            # Show advancement and revert buttons for tournament admins
                            # Don't show if has RaceTime room (auto-managed)
                            if self.can_manage_tournaments and not has_racetime_room:
                                with ui.row().classes("gap-1"):
                                    # Determine next available action based on current state
                                    if not match.confirmed_at:
                                        if match.finished_at:
                                            # Can advance to recorded
                                            ui.button(
                                                icon="check_circle",
                                                on_click=lambda m=match: advance_status(
                                                    m.id, "recorded", "Recorded"
                                                ),
                                            ).classes("btn btn-sm").props(
                                                "flat color=positive size=sm"
                                            ).tooltip(
                                                "Mark as recorded in bracket"
                                            )
                                            # Can revert from finished
                                            ui.button(
                                                icon="undo",
                                                on_click=lambda m=match: revert_status(
                                                    m.id, "finished", "Finished"
                                                ),
                                            ).classes("btn btn-sm").props(
                                                "flat color=negative size=sm"
                                            ).tooltip(
                                                "Revert from finished"
                                            )
                                        elif match.started_at:
                                            # Can advance to finished
                                            ui.button(
                                                icon="flag",
                                                on_click=lambda m=match: advance_status(
                                                    m.id, "finished", "Finished"
                                                ),
                                            ).classes("btn btn-sm").props(
                                                "flat color=positive size=sm"
                                            ).tooltip(
                                                "Mark as finished"
                                            )
                                            # Can revert from started
                                            ui.button(
                                                icon="undo",
                                                on_click=lambda m=match: revert_status(
                                                    m.id, "started", "Started"
                                                ),
                                            ).classes("btn btn-sm").props(
                                                "flat color=negative size=sm"
                                            ).tooltip(
                                                "Revert from started"
                                            )
                                        elif match.checked_in_at:
                                            # Can advance to started
                                            ui.button(
                                                icon="play_arrow",
                                                on_click=lambda m=match: advance_status(
                                                    m.id, "started", "Started"
                                                ),
                                            ).classes("btn btn-sm").props(
                                                "flat color=info size=sm"
                                            ).tooltip(
                                                "Mark as started"
                                            )
                                            # Can revert from checked_in
                                            ui.button(
                                                icon="undo",
                                                on_click=lambda m=match: revert_status(
                                                    m.id, "checked_in", "Checked In"
                                                ),
                                            ).classes("btn btn-sm").props(
                                                "flat color=negative size=sm"
                                            ).tooltip(
                                                "Revert from checked in"
                                            )
                                        elif match.scheduled_at:
                                            # Can advance to checked_in
                                            ui.button(
                                                icon="how_to_reg",
                                                on_click=lambda m=match: advance_status(
                                                    m.id, "checked_in", "Checked In"
                                                ),
                                            ).classes("btn btn-sm").props(
                                                "flat color=warning size=sm"
                                            ).tooltip(
                                                "Mark as checked in"
                                            )
                                    else:
                                        # Match is recorded - can revert from recorded
                                        ui.button(
                                            icon="undo",
                                            on_click=lambda m=match: revert_status(
                                                m.id, "recorded", "Recorded"
                                            ),
                                        ).classes("btn btn-sm").props(
                                            "flat color=negative size=sm"
                                        ).tooltip(
                                            "Revert from recorded"
                                        )

                    # Delegate crew rendering to crew_management component
                    def render_commentator(match: Match):
                        self.crew_management.render_commentator(match)

                    def render_tracker(match: Match):
                        self.crew_management.render_tracker(match)

                    # Delegate seed rendering to match_actions component
                    def render_seed(match: Match):
                        self.match_actions.render_seed(match)

                    # Delegate racetime and actions rendering to match_actions component
                    def render_racetime(match: Match):
                        self.match_actions.render_racetime(match)

                    def render_actions(match: Match):
                        self.match_actions.render_actions(match, self.can_edit_matches)

                    columns = [
                        TableColumn("Tournament", cell_render=renderers.render_tournament),
                        TableColumn("Match", cell_render=renderers.render_title),
                        TableColumn("Players", cell_render=renderers.render_players),
                        TableColumn("Scheduled", cell_render=renderers.render_scheduled_time),
                        TableColumn("Stream", cell_render=renderers.render_stream),
                        TableColumn("Seed", cell_render=render_seed),
                        TableColumn("RaceTime", cell_render=render_racetime),
                        TableColumn("Commentator", cell_render=render_commentator),
                        TableColumn("Tracker", cell_render=render_tracker),
                        TableColumn("Status", cell_render=render_status),
                        TableColumn("Actions", cell_render=render_actions),
                    ]

                    table = ResponsiveTable(columns, matches)
                    await table.render()

    async def _create_match(self) -> None:
        """Open dialog to create a new match."""
        # Get list of active tournaments
        tournaments = await self.service.list_all_org_tournaments(self.organization.id)
        active_tournaments = [t for t in tournaments if t.is_active]

        if not active_tournaments:
            ui.notify("No active tournaments available", type="warning")
            return

        # Filter out tournaments with SpeedGaming enabled (read-only)
        editable_tournaments = [
            t
            for t in active_tournaments
            if not getattr(t, "speedgaming_enabled", False)
        ]

        if not editable_tournaments:
            ui.notify(
                "All active tournaments have SpeedGaming integration enabled. "
                "Matches must be managed through SpeedGaming.",
                type="warning",
            )
            return

        # If only one tournament, use it directly; otherwise include tournament selector in the create dialog
        if len(editable_tournaments) == 1:
            tournament = editable_tournaments[0]
            await self._show_create_match_dialog(tournament)
        else:
            # Show combined dialog with tournament selection
            await self._show_create_match_dialog_with_tournament_select(
                editable_tournaments
            )

    async def _show_create_match_dialog_with_tournament_select(
        self, tournaments: list
    ) -> None:
        """Show create match dialog with tournament selection included."""
        from components.dialogs.common.base_dialog import BaseDialog

        class CreateMatchWithTournamentDialog(BaseDialog):
            """Dialog for creating a match with tournament selection."""

            def __init__(self, tournaments, user, organization_id, on_save):
                super().__init__()
                self.tournaments = tournaments
                self.user = user
                self.organization_id = organization_id
                self.on_save_callback = on_save

                # UI refs
                self._tournament_select = None
                self._title_input = None
                self._scheduled_input = None
                self._stream_select = None
                self._player_select = None
                self._comment_input = None

            async def show(self):
                self.create_dialog(
                    title="Create Match", icon="add_circle", max_width="dialog-card"
                )
                await super().show()

            def _render_body(self):
                with self.create_form_grid(columns=1):
                    # Tournament selection (only if multiple)
                    with ui.element("div"):
                        self._tournament_select = ui.select(
                            label="Tournament",
                            options={t.id: t.name for t in self.tournaments},
                        ).classes("w-full")

                    with ui.element("div"):
                        self._title_input = ui.input(
                            label="Match Title",
                            placeholder="e.g., Quarterfinal Match 1",
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
                        self._player_select = (
                            ui.select(
                                label="Players",
                                options={},
                                multiple=True,
                            )
                            .classes("w-full")
                            .props("use-chips")
                        )

                    with ui.element("div"):
                        self._stream_select = ui.select(
                            label="Stream Channel (Optional)",
                            options={None: "No stream"},
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

                # Load data async
                async def load_data():
                    try:
                        from application.services.tournaments.stream_channel_service import (
                            StreamChannelService,
                        )
                        from application.services.organizations.organization_service import (
                            OrganizationService,
                        )

                        stream_service = StreamChannelService()
                        streams = await stream_service.list_org_channels(
                            self.user, self.organization_id
                        )
                        stream_options = {None: "No stream"}
                        stream_options.update({s.id: s.name for s in streams})
                        if self._stream_select:
                            self._stream_select.options = stream_options
                            self._stream_select.update()

                        org_service = OrganizationService()
                        members = await org_service.list_members(self.organization_id)
                        player_options = {}
                        for member in members:
                            await member.fetch_related("user")
                            player_options[member.user.id] = (
                                member.user.discord_username
                            )
                        if self._player_select:
                            self._player_select.options = player_options
                            self._player_select.update()
                    except Exception as e:
                        logger.error("Failed to load data: %s", e)
                        ui.notify(f"Error loading data: {str(e)}", type="negative")

                ui.timer(0.1, load_data, once=True)

                with self.create_actions_row():
                    ui.button("Cancel", on_click=self.close).classes("btn")
                    ui.button("Create Match", on_click=self._handle_create).classes(
                        "btn"
                    ).props("color=positive")

            async def _handle_create(self):
                from datetime import datetime
                from application.services.tournaments.tournament_service import (
                    TournamentService,
                )

                if not self._tournament_select or not self._tournament_select.value:
                    ui.notify("Please select a tournament", type="warning")
                    return

                if not self._title_input or not self._title_input.value.strip():
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

                tournament_id = self._tournament_select.value
                title = self._title_input.value.strip()
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

                scheduled_at = None
                if scheduled_str:
                    try:
                        scheduled_at = datetime.fromisoformat(scheduled_str)
                    except ValueError as e:
                        ui.notify(f"Invalid date/time format: {e}", type="negative")
                        return

                try:
                    service = TournamentService()
                    match = await service.create_match(
                        user=self.user,
                        organization_id=self.organization_id,
                        tournament_id=tournament_id,
                        player_ids=player_ids,
                        scheduled_at=scheduled_at,
                        comment=comment,
                        title=title,
                    )

                    if match:
                        if stream_id:
                            await service.update_match(
                                user=self.user,
                                organization_id=self.organization_id,
                                match_id=match.id,
                                stream_channel_id=stream_id,
                            )

                        ui.notify(
                            f'Match "{title}" created successfully!', type="positive"
                        )

                        if self.on_save_callback:
                            await self.on_save_callback()

                        await self.close()
                    else:
                        ui.notify("Failed to create match", type="negative")

                except ValueError as e:
                    ui.notify(str(e), type="negative")
                except Exception as e:
                    ui.notify(f"Error creating match: {str(e)}", type="negative")
                    logger.error("Failed to create match: %s", e)

        dialog = CreateMatchWithTournamentDialog(
            tournaments, self.user, self.organization.id, self._refresh
        )
        await dialog.show()

    async def _show_create_match_dialog(self, tournament) -> None:
        """Show the create match dialog for the given tournament."""
        dialog = CreateMatchDialog(
            user=self.user,
            organization_id=self.organization.id,
            tournament=tournament,
            on_save=self._refresh,
        )
        await dialog.show()

    async def render(self) -> None:
        """Render the event schedule view."""
        # Create container first
        self.container = ui.column().classes("w-full")

        # Load saved filters from client storage BEFORE rendering content
        await self._load_filters()

        # Now render with loaded filter values
        with self.container:
            await self._render_content()
