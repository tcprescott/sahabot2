"""
Dialog for creating/editing async tournament pools.

Provides form for pool name and description with validation.
"""

from typing import Optional, Callable
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from modules.async_qualifier.models.async_qualifier import AsyncQualifierPool
import logging

logger = logging.getLogger(__name__)


class PoolDialog(BaseDialog):
    """Dialog for creating or editing an async tournament pool."""

    def __init__(
        self,
        pool: Optional[AsyncQualifierPool] = None,
        on_save: Optional[Callable] = None,
    ):
        """
        Initialize pool dialog.

        Args:
            pool: Existing pool to edit (None for new pool)
            on_save: Callback function to call after successful save
        """
        super().__init__()
        self.pool = pool
        self.on_save = on_save

        # Form fields
        self.name_input: Optional[ui.input] = None
        self.description_input: Optional[ui.textarea] = None

    async def show(self):
        """Display the dialog."""
        title = f"Edit Pool: {self.pool.name}" if self.pool else "Create New Pool"
        self.create_dialog(
            title=title, icon="folder" if not self.pool else "edit", max_width="600px"
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        with self.create_form_grid(columns=1):
            with ui.element("div"):
                self.name_input = (
                    ui.input(
                        label="Pool Name",
                        placeholder="e.g., Week 1, Qualifier A, Finals",
                        value=self.pool.name if self.pool else "",
                    )
                    .classes("w-full")
                    .props("outlined")
                )
                self.name_input.props("autofocus")

            with ui.element("div"):
                self.description_input = (
                    ui.textarea(
                        label="Description (optional)",
                        placeholder="Additional details about this pool...",
                        value=self.pool.description if self.pool else "",
                    )
                    .classes("w-full")
                    .props("outlined rows=3")
                )

        ui.separator()

        # Action buttons
        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Save" if self.pool else "Create", on_click=self._save).classes(
                "btn"
            ).props("color=positive")

    async def _save(self):
        """Validate and save pool data."""
        # Validation
        name = self.name_input.value.strip() if self.name_input else ""
        if not name:
            ui.notify("Pool name is required", type="negative")
            return

        description = (
            self.description_input.value.strip() if self.description_input else None
        )

        # Call save callback with data
        if self.on_save:
            try:
                await self.on_save({"name": name, "description": description})
                ui.notify(
                    f'Pool {"updated" if self.pool else "created"} successfully',
                    type="positive",
                )
                await self.close()
            except Exception as e:
                logger.error("Error saving pool: %s", e)
                ui.notify(f"Error: {str(e)}", type="negative")
