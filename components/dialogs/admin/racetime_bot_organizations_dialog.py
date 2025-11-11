"""
RacetimeBotOrganizationsDialog component for managing bot assignments to organizations.

This dialog belongs to the presentation layer and delegates all business logic
to services in application/services.
"""

from __future__ import annotations
from typing import Optional, Callable
from nicegui import ui
from models import User, RacetimeBot, Organization
from application.services.racetime.racetime_bot_service import RacetimeBotService
from application.services.organizations.organization_service import OrganizationService
from components.dialogs.common.base_dialog import BaseDialog
import logging

logger = logging.getLogger(__name__)


class RacetimeBotOrganizationsDialog(BaseDialog):
    """Dialog for managing RaceTime bot organization assignments."""

    def __init__(
        self,
        bot: RacetimeBot,
        current_user: User,
        on_save: Optional[Callable] = None,
    ):
        """
        Initialize organizations dialog.

        Args:
            bot: Bot to manage organizations for
            current_user: Currently logged in user
            on_save: Callback to execute after changes
        """
        super().__init__()
        self.bot = bot
        self.current_user = current_user
        self.on_save = on_save
        self.bot_service = RacetimeBotService()
        self.org_service = OrganizationService()

        # State
        self.all_organizations: list[Organization] = []
        self.assigned_org_ids: set[int] = set()
        self.selected_orgs: set[int] = set()
        self.org_list_container = None

    async def show(self) -> None:
        """Display the organizations dialog using BaseDialog structure."""
        self.create_dialog(
            title=f"Manage Organizations: {self.bot.name}",
            icon="groups",
            max_width="800px",
        )
        await super().show()

    def _render_body(self) -> None:
        """Render the dialog body content."""
        # Bot info
        with ui.row().classes("items-center gap-2"):
            ui.icon("category")
            ui.label(f"Category: {self.bot.category}").classes("font-bold")

        # Instructions
        with ui.row().classes("items-center gap-2 p-3 rounded").style(
            "background-color: var(--info-bg); color: var(--info-text);"
        ):
            ui.icon("info")
            ui.label("Select organizations that can use this RaceTime bot.")

        ui.separator()

        # Organization list
        self.org_list_container = ui.column().classes("full-width gap-2")
        self._render_org_list()

        ui.separator()

        # Actions
        with self.create_actions_row():
            ui.button("Close", on_click=self._close_and_callback).classes("btn")
            ui.button("Save Changes", on_click=self._save_and_close).classes(
                "btn"
            ).props("color=positive")

    def _render_org_list(self) -> None:
        """Render the organization checklist (synchronous helper)."""
        # We'll load data asynchronously after dialog is shown
        with self.org_list_container:
            ui.label("Loading organizations...").classes("text-secondary")
            # Schedule async load
            ui.timer(0.1, self._load_organizations, once=True)

    async def _load_organizations(self) -> None:
        """Load organizations and assigned bot data."""
        # Load all organizations
        self.all_organizations = await self.org_service.list_organizations()

        # Load assigned organizations for this bot
        assigned_orgs = await self.bot_service.get_organizations_for_bot(
            self.bot.id, self.current_user
        )
        self.assigned_org_ids = {org.id for org in assigned_orgs}
        self.selected_orgs = self.assigned_org_ids.copy()

        # Re-render list
        self.org_list_container.clear()
        with self.org_list_container:
            if not self.all_organizations:
                with ui.row().classes("items-center gap-2 text-secondary"):
                    ui.icon("info")
                    ui.label("No organizations found.")
            else:
                for org in self.all_organizations:
                    is_assigned = org.id in self.assigned_org_ids
                    with ui.row().classes("items-center gap-2 p-2 rounded").style(
                        "background-color: var(--selected-bg);"
                        if org.id in self.selected_orgs
                        else ""
                    ):
                        checkbox = ui.checkbox(
                            text="", value=org.id in self.selected_orgs
                        )
                        checkbox.on(
                            "update:model-value",
                            lambda e, org_id=org.id: self._toggle_org(org_id, e.args),
                        )

                        ui.label(org.name).classes("font-bold")

                        if is_assigned:
                            ui.badge("Currently Assigned", color="positive")

    def _toggle_org(self, org_id: int, checked: bool) -> None:
        """Toggle organization selection."""
        if checked:
            self.selected_orgs.add(org_id)
        else:
            self.selected_orgs.discard(org_id)

    async def _save_and_close(self) -> None:
        """Save organization assignments and close dialog."""
        # Determine additions and removals
        to_add = self.selected_orgs - self.assigned_org_ids
        to_remove = self.assigned_org_ids - self.selected_orgs

        if not to_add and not to_remove:
            ui.notify("No changes to save", type="info")
            await self._close_and_callback()
            return

        try:
            # Add new assignments
            for org_id in to_add:
                await self.bot_service.assign_bot_to_organization(
                    self.bot.id, org_id, self.current_user
                )

            # Remove assignments
            for org_id in to_remove:
                await self.bot_service.unassign_bot_from_organization(
                    self.bot.id, org_id, self.current_user
                )

            ui.notify("Organization assignments updated successfully", type="positive")
            await self._close_and_callback()

        except Exception as e:
            logger.error(
                "Error updating bot organization assignments: %s", e, exc_info=True
            )
            ui.notify("An error occurred while updating assignments", type="negative")

    async def _close_and_callback(self) -> None:
        """Close dialog and trigger callback."""
        if self.on_save:
            await self.on_save()
        await self.close()
