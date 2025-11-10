"""
Dialog for editing member permissions within an organization.
"""

from __future__ import annotations
from typing import Optional, Callable, Awaitable, Sequence
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from application.services.organizations.organization_service import OrganizationService


class MemberPermissionsDialog(BaseDialog):
    """Dialog for assigning multiple organization permissions to a member."""

    def __init__(
        self,
        organization_id: int,
        user_id: int,
        username: str,
        current_permissions: Sequence[str],
        available_types: Sequence[dict],
        on_save: Optional[Callable[[], Awaitable[None]]] = None,
    ) -> None:
        super().__init__()
        self.organization_id = organization_id
        self.user_id = user_id
        self.username = username
        self.current_permissions = list(current_permissions)
        self.available_types = available_types
        self.on_save = on_save
        self.service = OrganizationService()

        self.permissions_select = None

    async def show(self) -> None:
        title = f"Manage Permissions: {self.username}"
        self.create_dialog(title=title, icon="admin_panel_settings")
        await super().show()

    def _render_body(self) -> None:
        with self.create_form_grid(columns=1):
            with ui.element("div").classes("span-1"):
                ui.label(f"Select permissions for {self.username}").classes(
                    "font-semibold mb-2"
                )
                # Build options dict for multiselect
                options = {
                    ptype["name"]: f"{ptype['name']} - {ptype['description']}"
                    for ptype in self.available_types
                }
                self.permissions_select = (
                    ui.select(
                        label="Permissions",
                        options=options,
                        value=self.current_permissions,
                        multiple=True,
                        with_input=True,
                    )
                    .classes("w-full")
                    .props("use-chips")
                )

        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Save", on_click=self._save).props("color=positive").classes(
                "btn"
            )

    async def _save(self) -> None:
        selected = self.permissions_select.value if self.permissions_select else []
        # Normalize to list if single value
        if not isinstance(selected, list):
            selected = [selected] if selected else []
        await self.service.set_permissions_for_member(
            self.organization_id, self.user_id, selected
        )
        if self.on_save:
            await self.on_save()
        await self.close()
