"""
Crew management components for tournament matches.

Handles crew signup, approval, and rendering for commentators and trackers.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Callable, Awaitable
from nicegui import ui
from models import CrewRole
from modules.tournament.models.match_schedule import Match
from components.dialogs.tournaments import AddCrewDialog

if TYPE_CHECKING:
    from models import User, Organization
    from modules.tournament.services.tournament_service import TournamentService

logger = logging.getLogger(__name__)


class CrewManagement:
    """Crew management functionality for match schedules."""

    def __init__(
        self,
        user: User,
        organization: Organization,
        service: "TournamentService",
        can_approve_crew: bool,
        on_refresh: Callable[[], Awaitable[None]],
    ):
        """Initialize crew management.

        Args:
            user: Current user
            organization: Current organization
            service: Tournament service instance
            can_approve_crew: Whether user can approve crew
            on_refresh: Callback to refresh the view
        """
        self.user = user
        self.organization = organization
        self.service = service
        self.can_approve_crew = can_approve_crew
        self.on_refresh = on_refresh

    async def signup_crew(self, match_id: int, role: CrewRole) -> None:
        """Sign up for a crew role."""
        try:
            await self.service.signup_crew(
                user=self.user,
                organization_id=self.organization.id,
                match_id=match_id,
                role=role.value,
            )
            ui.notify(f"Signed up as {role.value}", type="positive")
            await self.on_refresh()
        except Exception as e:
            logger.error("Failed to sign up as crew: %s", e)
            ui.notify(f"Failed to sign up: {str(e)}", type="negative")

    async def remove_crew(self, match_id: int, role: CrewRole) -> None:
        """Remove crew signup."""
        try:
            result = await self.service.remove_crew_signup(
                user=self.user,
                organization_id=self.organization.id,
                match_id=match_id,
                role=role.value,
            )
            if result:
                ui.notify(f"Removed {role.value} signup", type="positive")
                await self.on_refresh()
            else:
                ui.notify("Signup not found", type="warning")
        except Exception as e:
            logger.error("Failed to remove crew signup: %s", e)
            ui.notify(f"Failed to remove signup: {str(e)}", type="negative")

    async def approve_crew_signup(self, crew_id: int, role: CrewRole) -> None:
        """Approve a crew signup."""
        try:
            result = await self.service.approve_crew(
                user=self.user,
                organization_id=self.organization.id,
                crew_id=crew_id,
            )
            if result:
                ui.notify(
                    f"{role.value.capitalize()} approved", type="positive"
                )
                await self.on_refresh()
            else:
                ui.notify("Failed to approve crew", type="negative")
        except Exception as e:
            logger.error("Failed to approve crew: %s", e)
            ui.notify(f"Failed to approve: {str(e)}", type="negative")

    async def unapprove_crew_signup(self, crew_id: int, role: CrewRole) -> None:
        """Remove approval from a crew signup."""
        try:
            result = await self.service.unapprove_crew(
                user=self.user,
                organization_id=self.organization.id,
                crew_id=crew_id,
            )
            if result:
                ui.notify(
                    f"{role.value.capitalize()} approval removed",
                    type="positive",
                )
                await self.on_refresh()
            else:
                ui.notify("Failed to unapprove crew", type="negative")
        except Exception as e:
            logger.error("Failed to unapprove crew: %s", e)
            ui.notify(f"Failed to unapprove: {str(e)}", type="negative")

    async def open_add_crew_dialog(
        self, match: Match, default_role: CrewRole = CrewRole.COMMENTATOR
    ) -> None:
        """Open dialog to add crew to a match (admin action)."""
        async def on_save():
            await self.on_refresh()

        dialog = AddCrewDialog(
            admin_user=self.user,
            organization=self.organization,
            match=match,
            on_save=on_save,
        )
        # Pre-fill the role if provided
        await dialog.show()
        if dialog.role_input and default_role:
            dialog.role_input.value = default_role.value

    def render_commentator(self, match: Match) -> None:
        """Render commentator(s) with approval status color, signup button, and approval controls."""
        # Check if match is from SpeedGaming (read-only)
        is_speedgaming = (
            hasattr(match, "speedgaming_episode_id")
            and match.speedgaming_episode_id
        )

        # Get crew members with commentator role
        commentators = [
            crew
            for crew in getattr(match, "crew_members", [])
            if crew.role == CrewRole.COMMENTATOR
        ]

        # Check if current user is signed up
        user_signed_up = any(
            crew.user_id == self.user.id for crew in commentators
        )

        with ui.column().classes("gap-2"):
            if commentators:
                with ui.column().classes("gap-1"):
                    for crew in commentators:
                        with ui.row().classes("items-center gap-2"):
                            # Green for approved, yellow for unapproved
                            color_class = (
                                "text-positive"
                                if crew.approved
                                else "text-warning"
                            )
                            ui.label(crew.user.get_display_name()).classes(
                                color_class
                            )

                            # Show approval controls if user has permission and not SpeedGaming
                            if self.can_approve_crew and not is_speedgaming:
                                if crew.approved:
                                    # Show unapprove button
                                    ui.button(
                                        icon="close",
                                        on_click=lambda c=crew: self.unapprove_crew_signup(
                                            c.id, CrewRole.COMMENTATOR
                                        ),
                                    ).props(
                                        "flat round dense size=sm color=negative"
                                    ).tooltip(
                                        "Remove approval"
                                    )
                                else:
                                    # Show approve button
                                    ui.button(
                                        icon="check",
                                        on_click=lambda c=crew: self.approve_crew_signup(
                                            c.id, CrewRole.COMMENTATOR
                                        ),
                                    ).props(
                                        "flat round dense size=sm color=positive"
                                    ).tooltip(
                                        "Approve commentator"
                                    )
            else:
                ui.label("—").classes("text-secondary")

            # For SpeedGaming matches, don't show buttons (managed externally)
            if not is_speedgaming:
                # Admin add commentator button (for admins/tournament managers)
                if self.can_approve_crew:
                    ui.button(
                        icon="mic",
                        on_click=lambda m=match: self.open_add_crew_dialog(
                            m, CrewRole.COMMENTATOR
                        ),
                    ).classes("btn btn-sm").props(
                        "flat color=primary size=sm"
                    ).tooltip(
                        "Add Commentator"
                    )

                # Sign up or remove button (for regular users)
                if user_signed_up:
                    ui.button(
                        icon="remove_circle",
                        on_click=lambda m=match: self.remove_crew(
                            m.id, CrewRole.COMMENTATOR
                        ),
                    ).classes("btn btn-sm").props(
                        "flat color=negative size=sm"
                    ).tooltip(
                        "Remove your commentator signup"
                    )
                else:
                    ui.button(
                        icon="add_circle",
                        on_click=lambda m=match: self.signup_crew(
                            m.id, CrewRole.COMMENTATOR
                        ),
                    ).classes("btn btn-sm").props(
                        "flat color=positive size=sm"
                    ).tooltip(
                        "Sign up as commentator"
                    )

    def render_tracker(self, match: Match) -> None:
        """Render tracker(s) with approval status color, signup button, and approval controls."""
        # Check if match is from SpeedGaming (read-only)
        is_speedgaming = (
            hasattr(match, "speedgaming_episode_id")
            and match.speedgaming_episode_id
        )

        # Get crew members with tracker role
        trackers = [
            crew
            for crew in getattr(match, "crew_members", [])
            if crew.role == CrewRole.TRACKER
        ]

        # Check if tracker is enabled for this tournament
        tracker_enabled = getattr(match.tournament, "tracker_enabled", True)

        # Check if current user is signed up
        user_signed_up = any(
            crew.user_id == self.user.id for crew in trackers
        )

        with ui.column().classes("gap-2"):
            if trackers:
                with ui.column().classes("gap-1"):
                    for crew in trackers:
                        with ui.row().classes("items-center gap-2"):
                            # Green for approved, yellow for unapproved
                            color_class = (
                                "text-positive"
                                if crew.approved
                                else "text-warning"
                            )
                            ui.label(crew.user.get_display_name()).classes(
                                color_class
                            )

                            # Show approval controls if user has permission and not SpeedGaming
                            if self.can_approve_crew and not is_speedgaming:
                                if crew.approved:
                                    # Show unapprove button
                                    ui.button(
                                        icon="close",
                                        on_click=lambda c=crew: self.unapprove_crew_signup(
                                            c.id, CrewRole.TRACKER
                                        ),
                                    ).props(
                                        "flat round dense size=sm color=negative"
                                    ).tooltip(
                                        "Remove approval"
                                    )
                                else:
                                    # Show approve button
                                    ui.button(
                                        icon="check",
                                        on_click=lambda c=crew: self.approve_crew_signup(
                                            c.id, CrewRole.TRACKER
                                        ),
                                    ).props(
                                        "flat round dense size=sm color=positive"
                                    ).tooltip(
                                        "Approve tracker"
                                    )
            else:
                ui.label("—").classes("text-secondary")

            # For SpeedGaming matches, don't show buttons (managed externally)
            if not is_speedgaming and tracker_enabled:
                # Admin add tracker button (for admins/tournament managers)
                if self.can_approve_crew:
                    ui.button(
                        icon="timeline",
                        on_click=lambda m=match: self.open_add_crew_dialog(
                            m, CrewRole.TRACKER
                        ),
                    ).classes("btn btn-sm").props(
                        "flat color=primary size=sm"
                    ).tooltip(
                        "Add Tracker"
                    )

                # Sign up or remove button (only if tracker enabled for this tournament)
                if user_signed_up:
                    ui.button(
                        icon="remove_circle",
                        on_click=lambda m=match: self.remove_crew(
                            m.id, CrewRole.TRACKER
                        ),
                    ).classes("btn btn-sm").props(
                        "flat color=negative size=sm"
                    ).tooltip(
                        "Remove your tracker signup"
                    )
                else:
                    ui.button(
                        icon="add_circle",
                        on_click=lambda m=match: self.signup_crew(
                            m.id, CrewRole.TRACKER
                        ),
                    ).classes("btn btn-sm").props(
                        "flat color=positive size=sm"
                    ).tooltip(
                        "Sign up as tracker"
                    )
            elif not is_speedgaming:
                # Show disabled button with tooltip explaining why (only for non-SpeedGaming matches)
                ui.button(icon="block", on_click=None).classes(
                    "btn btn-sm"
                ).props("flat disable size=sm").tooltip(
                    "Tracker role not enabled for this tournament"
                )
