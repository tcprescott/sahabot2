"""
Race Re-attempt Confirmation Dialog.

Dialog to confirm re-attempting a race with warnings about limits.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.async_tournament import AsyncQualifierRace
from components.dialogs.common.base_dialog import BaseDialog
from application.services.async_qualifiers.async_qualifier_service import (
    AsyncQualifierService,
)


class RaceReattemptDialog(BaseDialog):
    """Dialog to confirm re-attempting a race."""

    def __init__(
        self,
        race: AsyncQualifierRace,
        current_user: User,
        organization_id: int,
        on_success=None,
    ):
        """
        Initialize the reattempt confirmation dialog.

        Args:
            race: Race to re-attempt
            current_user: User requesting re-attempt
            organization_id: Organization ID
            on_success: Callback function called after successful re-attempt
        """
        super().__init__()
        self.race = race
        self.current_user = current_user
        self.organization_id = organization_id
        self.on_success = on_success
        self.service = AsyncQualifierService()

    async def show(self):
        """Display the confirmation dialog."""
        # Get tournament info
        await self.race.fetch_related("tournament", "permalink", "permalink__pool")
        tournament = self.race.tournament

        # Check if re-attempt is allowed
        can_reattempt, reason = await self.service.can_reattempt_race(
            self.current_user, self.organization_id, self.race.id
        )

        if not can_reattempt:
            # Show error dialog instead
            with ui.dialog() as dialog, ui.card().classes("w-full max-w-md"):
                ui.label("Cannot Re-attempt Race").classes(
                    "text-h6 mb-4 text-danger font-bold"
                )
                ui.label(reason).classes("text-danger mb-4")
                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button("Close", on_click=dialog.close).classes("btn")
            dialog.open()
            return

        # Get current reattempt count (for potential future use)
        _ = await self.service.get_reattempt_count(
            self.current_user, self.organization_id, tournament.id
        )

        self.create_dialog(
            title="Confirm Re-attempt",
            icon="restart_alt",
            max_width="600px",
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        # Sync get tournament data
        tournament = self.race.tournament
        pool_name = self.race.permalink.pool.name

        # Warning section
        with ui.element("div").classes("mb-4 p-3 bg-yellow-50 rounded"):
            ui.icon("warning").classes("text-warning text-2xl")
            ui.label("Warning").classes("text-warning font-bold ml-2 text-lg")
            ui.label(
                "Re-attempting this race will mark it as excluded from scoring. "
                "You will need to start a new race for this pool."
            ).classes("mt-2 text-sm")

        ui.separator()

        # Race info
        self.create_section_title("Race Information")
        self.create_info_row("Tournament", tournament.name)
        self.create_info_row("Pool", pool_name)
        self.create_info_row("Status", self.race.status_formatted)
        if self.race.elapsed_time:
            self.create_info_row("Time", self.race.elapsed_time_formatted)
        if self.race.score is not None:
            self.create_info_row("Score", self.race.score_formatted)

        ui.separator()

        # Re-attempt limits info
        self.create_section_title("Re-attempt Information")
        if tournament.max_reattempts == 0:
            ui.label("Re-attempts are not allowed for this tournament.").classes(
                "text-sm text-danger"
            )
        elif tournament.max_reattempts > 0:
            self.create_info_row(
                "Maximum Re-attempts Allowed", str(tournament.max_reattempts)
            )
            ui.label(
                "After this re-attempt, you will have used one of your allowed re-attempts."
            ).classes("text-sm text-secondary mt-2")
        else:  # -1 = unlimited
            ui.label("Unlimited re-attempts are allowed for this tournament.").classes(
                "text-sm text-secondary"
            )

        ui.separator()

        # Action buttons
        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Re-attempt Race", on_click=self._confirm_reattempt).classes(
                "btn"
            ).props("color=warning")

    async def _confirm_reattempt(self):
        """Confirm and execute re-attempt."""
        # Mark race as reattempted
        updated_race = await self.service.mark_race_as_reattempted(
            self.current_user, self.organization_id, self.race.id
        )

        if not updated_race:
            ui.notify("Failed to mark race as re-attempted", type="negative")
            return

        ui.notify("Race marked for re-attempt. You can now start a new race.", type="positive")

        # Call success callback
        if self.on_success:
            await self.on_success()

        await self.close()
