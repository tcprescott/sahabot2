"""
Dialog for inviting (adding) a member to an organization.
"""

from __future__ import annotations
from typing import Optional, Callable, Awaitable
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from application.services.organizations.organization_service import OrganizationService
from application.services.core.user_service import UserService


class InviteMemberDialog(BaseDialog):
    """Dialog for adding a user as a member of the organization.

    For now, this immediately adds the member (auto-accept).
    Future: this will create an invite that the user must accept.
    """

    def __init__(
        self,
        organization_id: int,
        organization_name: str,
        on_save: Optional[Callable[[], Awaitable[None]]] = None,
    ) -> None:
        super().__init__()
        self.organization_id = organization_id
        self.organization_name = organization_name
        self.on_save = on_save
        self.org_service = OrganizationService()
        self.user_service = UserService()

        self.user_select = None

    async def show(self) -> None:
        title = f"Invite Member to {self.organization_name}"
        self.create_dialog(title=title, icon="person_add")
        await super().show()

    def _render_body(self) -> None:
        with self.create_form_grid(columns=1):
            with ui.element("div").classes("span-1"):
                ui.label("Select a user to add to this organization").classes(
                    "font-semibold mb-2"
                )

                # Get all users for the dropdown
                # Note: this loads synchronously; in production you might want lazy loading
                self.user_select = ui.select(
                    label="User",
                    options={},
                    with_input=True,
                ).classes("w-full")

                # Load users asynchronously
                async def load_users():
                    users = await self.user_service.get_all_users()
                    # Build options dict: user_id -> display name (email addresses are private)
                    options = {u.id: u.discord_username for u in users}
                    self.user_select.options = options
                    self.user_select.update()

                ui.timer(0.1, load_users, once=True)

        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Add Member", on_click=self._save).props(
                "color=positive"
            ).classes("btn")

    async def _save(self) -> None:
        if not self.user_select or not self.user_select.value:
            ui.notify("Please select a user", type="warning")
            return

        user_id = self.user_select.value
        try:
            await self.org_service.add_member(self.organization_id, user_id)
            ui.notify("Member added successfully", type="positive")
            if self.on_save:
                await self.on_save()
            await self.close()
        except Exception as e:
            ui.notify(f"Failed to add member: {str(e)}", type="negative")
