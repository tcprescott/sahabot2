"""
Dialog for creating/editing async tournament permalinks.

Provides form for permalink URL and notes with validation.
"""

from typing import Optional, Callable
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from models.async_tournament import AsyncTournamentPermalink
import logging

logger = logging.getLogger(__name__)


class PermalinkDialog(BaseDialog):
    """Dialog for creating or editing an async tournament permalink."""

    def __init__(
        self,
        permalink: Optional[AsyncTournamentPermalink] = None,
        on_save: Optional[Callable] = None,
    ):
        """
        Initialize permalink dialog.

        Args:
            permalink: Existing permalink to edit (None for new permalink)
            on_save: Callback function to call after successful save
        """
        super().__init__()
        self.permalink = permalink
        self.on_save = on_save

        # Form fields
        self.url_input: Optional[ui.input] = None
        self.notes_input: Optional[ui.textarea] = None

    async def show(self):
        """Display the dialog."""
        title = "Edit Permalink" if self.permalink else "Add New Permalink"
        self.create_dialog(
            title=title,
            icon="link" if not self.permalink else "edit",
            max_width="600px",
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        with self.create_form_grid(columns=1):
            with ui.element("div"):
                self.url_input = (
                    ui.input(
                        label="Permalink URL",
                        placeholder="https://alttpr.com/h/...",
                        value=self.permalink.url if self.permalink else "",
                    )
                    .classes("w-full")
                    .props("outlined")
                )
                self.url_input.props("autofocus")

            with ui.element("div"):
                self.notes_input = (
                    ui.textarea(
                        label="Notes (optional)",
                        placeholder="Any special notes about this seed...",
                        value=self.permalink.notes if self.permalink else "",
                    )
                    .classes("w-full")
                    .props("outlined rows=3")
                )

        # Show par time if editing existing permalink
        if self.permalink and self.permalink.par_time is not None:
            ui.separator()
            with ui.element("div").classes("card-body"):
                ui.label("Current Par Time:").classes("font-bold")
                ui.label(self.permalink.par_time_formatted).classes("text-lg")

        ui.separator()

        # Action buttons
        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Save" if self.permalink else "Add", on_click=self._save).classes(
                "btn"
            ).props("color=positive")

    async def _save(self):
        """Validate and save permalink data."""
        # Validation
        url = self.url_input.value.strip() if self.url_input else ""
        if not url:
            ui.notify("Permalink URL is required", type="negative")
            return

        # Basic URL validation
        if not url.startswith("http://") and not url.startswith("https://"):
            ui.notify("URL must start with http:// or https://", type="negative")
            return

        notes = self.notes_input.value.strip() if self.notes_input else None

        # Call save callback with data
        if self.on_save:
            try:
                await self.on_save({"url": url, "notes": notes})
                ui.notify(
                    f'Permalink {"updated" if self.permalink else "added"} successfully',
                    type="positive",
                )
                await self.close()
            except Exception as e:
                logger.error("Error saving permalink: %s", e)
                ui.notify(f"Error: {str(e)}", type="negative")
