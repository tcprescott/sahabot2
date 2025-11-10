"""
Dialog for creating/updating a global setting.
"""

from __future__ import annotations
from typing import Optional, Callable, Awaitable, Any
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from application.services.core.settings_service import SettingsService


class GlobalSettingDialog(BaseDialog):
    """Dialog for editing or creating a global setting."""

    def __init__(
        self,
        key: Optional[str] = None,
        value: Optional[Any] = None,
        description: Optional[str] = None,
        is_public: bool = False,
        on_save: Optional[Callable[[], Awaitable[None]]] = None,
    ) -> None:
        super().__init__()
        self.key = key or ""
        self.value = value
        self.description = description or ""
        self.is_public = is_public
        self.on_save = on_save
        self.service = SettingsService()

        self.key_input = None
        self.value_input = None
        self.desc_input = None
        self.public_switch = None

    async def show(self) -> None:
        title = (
            "Create Global Setting"
            if not self.key
            else f"Edit Global Setting: {self.key}"
        )
        self.create_dialog(title=title, icon="tune")
        await super().show()

    def _render_body(self) -> None:
        with self.create_form_grid(columns=2):
            with ui.element("div").classes("span-2"):
                self.key_input = ui.input(
                    label="Key", value=self.key, placeholder="e.g., maintenance_mode"
                ).classes("w-full")
            with ui.element("div").classes("span-2"):
                self.value_input = (
                    ui.input(
                        label="Value",
                        value="" if self.value is None else str(self.value),
                    )
                    .props("type=textarea autogrow")
                    .classes("w-full")
                )
            with ui.element("div").classes("span-2"):
                self.desc_input = ui.input(
                    label="Description", value=self.description
                ).classes("w-full")
            with ui.element("div"):
                self.public_switch = ui.checkbox(
                    "Publicly Readable", value=self.is_public
                )
        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Save", on_click=self._save).props("color=positive").classes(
                "btn"
            )

    async def _save(self) -> None:
        # Store as plain string
        value: str = (self.value_input.value or "") if self.value_input else ""
        await self.service.set_global(
            key=(self.key_input.value or "").strip(),
            value=value,
            description=(
                (self.desc_input.value or "").strip() if self.desc_input else None
            ),
            is_public=bool(self.public_switch.value) if self.public_switch else False,
        )
        if self.on_save:
            await self.on_save()
        await self.close()
