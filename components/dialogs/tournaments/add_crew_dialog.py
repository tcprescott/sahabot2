"""
AddCrewDialog component for admins to add crew to a match.

This dialog belongs to the presentation layer and delegates all business logic
to services in application/services.
"""

from __future__ import annotations
from typing import Optional, Callable, Awaitable
from nicegui import ui
from models import User, Organization, CrewRole
from models import Match
from application.services.core.user_service import UserService
from application.services.organizations.organization_service import OrganizationService
from components.dialogs.common.base_dialog import BaseDialog
import logging

logger = logging.getLogger(__name__)


class AddCrewDialog(BaseDialog):
    """Dialog for admins to add crew to a match."""

    def __init__(
        self,
        admin_user: User,
        organization: Organization,
        match: Match,
        on_save: Optional[Callable[[], Awaitable[None]]] = None,
    ) -> None:
        """Initialize add crew dialog.

        Args:
            admin_user: User performing the admin action
            organization: Organization context
            match: Match to add crew to
            on_save: Callback to execute after successful save
        """
        super().__init__()
        self.admin_user = admin_user
        self.organization = organization
        self.match = match
        self.on_save = on_save
        self.user_service = UserService()
        self.org_service = OrganizationService()

        # UI refs
        self.user_select: Optional[ui.select] = None
        self.role_input: Optional[ui.input] = None
        self.approved_checkbox: Optional[ui.checkbox] = None

    async def show(self) -> None:
        """Display the dialog."""
        match_title = self.match.title or f"Match #{self.match.id}"
        self.create_dialog(
            title=f"Add Crew to {match_title}", icon="people", max_width="dialog-card"
        )
        await super().show()

    def _render_body(self) -> None:
        """Render the dialog body content."""
        # Info section
        self.create_section_title("Match Information")
        match_title = self.match.title or f"Match #{self.match.id}"
        self.create_info_row("Match", match_title)
        if self.match.scheduled_at:
            with ui.row().classes("items-center gap-2"):
                ui.label("Scheduled:").classes("font-semibold")
                from components.datetime_label import DateTimeLabel

                DateTimeLabel.create(self.match.scheduled_at, format_type="relative")

        ui.separator()

        # Form section
        self.create_section_title("Crew Details")

        with self.create_form_grid(columns=1):
            # User selection
            with ui.element("div"):
                ui.label("Select User").classes("text-sm font-semibold mb-1")
                self.user_select = ui.select(
                    options={}, label="User", with_input=True
                ).classes("w-full")
                ui.label("Start typing to search organization members").classes(
                    "text-xs text-secondary"
                )

            # Role selection
            with ui.element("div"):
                ui.label("Role").classes("text-sm font-semibold mb-1")
                self.role_input = ui.select(
                    options={
                        CrewRole.COMMENTATOR.value: "Commentator",
                        CrewRole.TRACKER.value: "Tracker",
                        CrewRole.RESTREAMER.value: "Restreamer",
                    },
                    label="Crew Role",
                ).classes("w-full")
                ui.label("Select the role for this crew member").classes(
                    "text-xs text-secondary"
                )

            # Approved checkbox
            with ui.element("div"):
                self.approved_checkbox = ui.checkbox(
                    "Pre-approve this crew member", value=True
                ).classes("mt-2")
                ui.label("Uncheck if crew needs manual approval later").classes(
                    "text-xs text-secondary ml-7"
                )

        # Load organization members
        ui.timer(0.1, self._load_members, once=True)

        ui.separator()

        # Actions
        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Add Crew", on_click=self._handle_add_crew).classes("btn").props(
                "color=positive"
            )

    async def _load_members(self) -> None:
        """Load organization members for selection."""
        try:
            members = await self.org_service.list_members(self.organization.id)

            # Create options dict {user_id: display_name}
            options = {}
            for member in members:
                user = await member.user
                display_name = user.display_name or user.discord_username
                options[user.id] = f"{display_name} (@{user.discord_username})"

            if self.user_select:
                self.user_select.options = options
                self.user_select.update()

        except Exception as e:
            logger.error("Failed to load organization members: %s", e)
            ui.notify("Failed to load members", type="negative")

    async def _handle_add_crew(self) -> None:
        """Handle add crew button click."""
        # Validation
        if not self.user_select or not self.user_select.value:
            ui.notify("Please select a user", type="warning")
            return

        if (
            not self.role_input
            or not self.role_input.value
            or not self.role_input.value.strip()
        ):
            ui.notify("Please enter a crew role", type="warning")
            return

        user_id = self.user_select.value
        role = self.role_input.value.strip()
        approved = self.approved_checkbox.value if self.approved_checkbox else True

        try:
            from application.services.tournaments import TournamentService

            tournament_service = TournamentService()

            # Add crew via admin method
            result = await tournament_service.admin_add_crew(
                admin_user=self.admin_user,
                organization_id=self.organization.id,
                match_id=self.match.id,
                user_id=user_id,
                role=role,
                approved=approved,
            )

            if result:
                approval_status = "and approved" if approved else "(pending approval)"
                ui.notify(f"Crew member added {approval_status}", type="positive")
                if self.on_save:
                    await self.on_save()
                await self.close()
            else:
                ui.notify(
                    "Failed to add crew. Check permissions or if user is already assigned to this role.",
                    type="negative",
                )

        except Exception as e:
            logger.error("Failed to add crew: %s", e)
            ui.notify(f"Error: {str(e)}", type="negative")
