"""
BaseDialog - Reusable dialog component with standardized structure.

Provides consistent card layout, header, body, actions, and utility methods
for all application dialogs.
"""

from __future__ import annotations
from typing import Optional, Callable, Any
from nicegui import ui
from models import Permission
import logging

logger = logging.getLogger(__name__)


class BaseDialog:
    """Base class for all application dialogs with standardized structure."""

    def __init__(self) -> None:
        """Initialize the base dialog."""
        self.dialog: Optional[ui.dialog] = None

    def create_dialog(
        self,
        title: str,
        icon: str = "info",
        max_width: str = "dialog-card",
    ) -> ui.dialog:
        """Create and return a dialog with standard card structure.

        Args:
            title: Dialog title text
            icon: Material icon name for the header
            max_width: CSS class for dialog width (default: dialog-card)

        Returns:
            ui.dialog: The created dialog instance
        """
        self.dialog = ui.dialog()
        with self.dialog:
            with ui.element("div").classes(f"card {max_width}").props(
                'role="dialog" aria-modal="true"'
            ):
                # Header
                with ui.element("div").classes("card-header"):
                    with ui.row().classes("items-center gap-sm"):
                        ui.icon(icon).classes("icon-medium").props('aria-hidden="true"')
                        ui.element("h2").classes("text-xl text-bold").add_slot(
                            "default", title
                        )

                # Body container - subclasses will populate
                with ui.element("div").classes("card-body"):
                    self._render_body()

        return self.dialog

    def _render_body(self) -> None:
        """Render dialog body content. Override in subclasses."""
        ui.label("Dialog body not implemented")

    async def show(self) -> None:
        """Display the dialog."""
        if self.dialog:
            self.dialog.open()

    async def close(self) -> None:
        """Close the dialog."""
        if self.dialog:
            self.dialog.close()

    @staticmethod
    def create_form_grid(columns: int = 2) -> ui.element:
        """Create a responsive form grid container.

        Args:
            columns: Number of columns on desktop (default: 2)

        Returns:
            ui.element: Grid container element
        """
        classes = "form-grid"
        if columns == 2:
            classes += " form-grid-2"
        return ui.element("div").classes(classes)

    @staticmethod
    def create_actions_row() -> ui.element:
        """Create a standardized actions row for dialog buttons.

        Returns:
            ui.element: Actions container using left/right convention

        Convention:
        - Place neutral/negative actions FIRST; they will align to the far left
        - Place the primary/positive action LAST; it will align to the far right
        This layout is achieved via CSS (justify-content: space-between).
        """
        return ui.element("div").classes("dialog-actions")

    @staticmethod
    def create_permission_select(
        current_permission: Permission,
        max_permission: Permission,
        on_change: Callable[[Permission], None],
        label: str = "Permission",
    ) -> ui.select:
        """Create a permission select dropdown with proper enum handling.

        Args:
            current_permission: Current permission value
            max_permission: Maximum permission level that can be assigned
            on_change: Callback invoked with normalized Permission enum
            label: Label for the select (default: "Permission")

        Returns:
            ui.select: Configured permission select element
        """
        available = [p for p in Permission if p < max_permission]
        permission_select = ui.select(
            label=label,
            options={p.value: p.name for p in available},
            value=current_permission.value,
        ).classes("w-full")

        # Normalize the emitted value to a Permission enum
        def normalize_and_callback(e: Any) -> None:
            """Normalize select value to Permission enum."""
            val = e.args
            try:
                if isinstance(val, dict):
                    val = val.get("value")
                if isinstance(val, Permission):
                    on_change(val)
                    return
                on_change(Permission(int(val)))
            except Exception as ex:
                logger.warning("Failed to parse permission value: %s", ex)

        permission_select.on("update:model-value", normalize_and_callback)
        return permission_select

    @staticmethod
    def create_info_row(label: str, value: str) -> None:
        """Create a read-only information row.

        Args:
            label: Label text (will be bolded)
            value: Value text
        """
        with ui.row().classes("full-width"):
            ui.label(f"{label}:").classes("font-semibold")
            ui.label(value)

    @staticmethod
    def create_section_title(text: str) -> None:
        """Create a section title within the dialog.

        Args:
            text: Section title text
        """
        ui.element("h3").classes("font-bold text-lg").add_slot("default", text)
