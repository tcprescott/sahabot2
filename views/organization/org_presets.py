"""
Organization Presets View for managing randomizer presets.

This view allows users to create, edit, delete, and view randomizer presets
within their organization.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import Organization, User
from components.card import Card
from components.empty_state import EmptyState
from components.datetime_label import DateTimeLabel
from components.dialogs.organization import PresetEditorDialog, ViewPresetDialog
from application.services.randomizer.randomizer_preset_service import (
    RandomizerPresetService,
)

logger = logging.getLogger(__name__)


class OrgPresetsView:
    """View for managing organization randomizer presets."""

    RANDOMIZER_LABELS = {
        "alttpr": "ALTTPR",
        "sm": "Super Metroid",
        "smz3": "SMZ3 Combo",
        "ootr": "OoTR",
        "aosr": "Aria of Sorrow",
        "z1r": "Zelda 1",
        "ffr": "FF Randomizer",
        "smb3r": "SMB3 Randomizer",
        "ctjets": "CT: Jets of Time",
        "bingosync": "Bingosync",
    }

    def __init__(
        self, user: User, organization: Organization, service: RandomizerPresetService
    ):
        """
        Initialize the organization presets view.

        Args:
            user: Current user
            organization: Current organization
            service: Preset service
        """
        self.user = user
        self.organization = organization
        self.service = service
        self.container = None
        self.filter_randomizer = None
        self.filter_mine_only = False

    async def render(self) -> None:
        """Render the presets view."""
        self.container = ui.column().classes("w-full")
        with self.container:
            await self._render_content()

    async def _refresh(self) -> None:
        """Refresh the view."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _render_content(self) -> None:
        """Render the view content."""
        with Card.create(title="Randomizer Presets"):
            # Header with description
            with ui.element("div").classes("mb-4"):
                ui.label(
                    "Create and manage YAML presets for randomizer seed generation."
                )
                ui.label(
                    "Presets can be used to quickly generate seeds with your preferred settings."
                ).classes("text-sm text-secondary")

            # Action bar
            with ui.element("div").classes("flex flex-wrap gap-2 mb-4 items-center"):
                # Create button
                async def open_create_dialog():
                    dialog = PresetEditorDialog(
                        user=self.user,
                        organization_id=self.organization.id,
                        on_save=self._refresh,
                    )
                    await dialog.show()

                ui.button(
                    "Create Preset", icon="add", on_click=open_create_dialog
                ).classes("btn").props("color=positive")

                # Filters
                ui.label("Filters:").classes("ml-4 font-bold")

                # Randomizer filter
                randomizer_options = [{"label": "All Randomizers", "value": None}]
                randomizer_options.extend(
                    [
                        {"label": label, "value": value}
                        for value, label in self.RANDOMIZER_LABELS.items()
                    ]
                )

                async def on_randomizer_change(e):
                    self.filter_randomizer = e.value
                    await self._refresh()

                ui.select(
                    label="Randomizer",
                    options=randomizer_options,
                    value=self.filter_randomizer,
                    on_change=on_randomizer_change,
                ).classes("w-48").props("outlined dense")

                # Mine only filter
                async def on_mine_only_change(e):
                    self.filter_mine_only = e.value
                    await self._refresh()

                ui.checkbox(
                    "My presets only",
                    value=self.filter_mine_only,
                    on_change=on_mine_only_change,
                )

            # Get presets
            try:
                if self.filter_mine_only:
                    # Show only user's presets
                    presets = await self.service.repository.list_for_organization(
                        organization_id=self.organization.id,
                        randomizer=self.filter_randomizer,
                        user_id=self.user.id,
                        include_public=False,
                    )
                else:
                    # Show all accessible presets
                    presets = await self.service.list_presets(
                        organization_id=self.organization.id,
                        user=self.user,
                        randomizer=self.filter_randomizer,
                    )

                if not presets:
                    # Empty state
                    EmptyState.no_items(
                        item_name="presets",
                        message="Create your first preset to get started!",
                        icon="code",
                        in_card=False,
                    )
                else:
                    # Presets grid
                    with ui.element("div").classes(
                        "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4"
                    ):
                        for preset in presets:
                            await self._render_preset_card(preset)

            except Exception as e:
                logger.error("Error loading presets: %s", e, exc_info=True)
                ui.label(f"Error loading presets: {str(e)}").classes("text-red-600")

    async def _render_preset_card(self, preset) -> None:
        """Render a single preset card."""
        with ui.card().classes("p-4 hover:shadow-lg transition-shadow"):
            # Header with name and randomizer
            with ui.element("div").classes("flex justify-between items-start mb-2"):
                with ui.element("div").classes("flex-1"):
                    ui.label(preset.name).classes("text-lg font-bold")
                    ui.label(
                        self.RANDOMIZER_LABELS.get(preset.randomizer, preset.randomizer)
                    ).classes("text-sm badge badge-secondary")

                # Public badge
                if preset.is_public:
                    ui.icon("public", size="sm").classes("text-secondary").tooltip(
                        "Public preset"
                    )

            # Description
            if preset.description:
                with ui.element("div").classes("mb-2"):
                    ui.label(preset.description).classes(
                        "text-sm text-secondary line-clamp-2"
                    )

            # Metadata
            with ui.element("div").classes("text-xs text-secondary mb-3"):
                ui.label(f"Created by: {preset.user.get_display_name()}")
                with ui.element("div").classes("flex items-center gap-1"):
                    ui.label("Updated:")
                    DateTimeLabel.create(preset.updated_at)

            # Actions
            with ui.element("div").classes("flex gap-2"):
                # View/Use button
                async def view_preset(p=preset):
                    await self._view_preset(p)

                ui.button("View", icon="visibility", on_click=view_preset).classes(
                    "btn flex-1"
                ).props("dense")

                # Edit button (only for owner or admins)
                can_edit = await self.service.can_user_edit_preset(
                    preset.id, self.organization.id, self.user
                )
                if can_edit:

                    async def edit_preset(p=preset):
                        dialog = PresetEditorDialog(
                            user=self.user,
                            organization_id=self.organization.id,
                            preset=p,
                            on_save=self._refresh,
                        )
                        await dialog.show()

                    ui.button("Edit", icon="edit", on_click=edit_preset).classes(
                        "btn flex-1"
                    ).props("dense color=primary")

                    # Delete button
                    async def delete_preset(p=preset):
                        await self._delete_preset(p)

                    ui.button("Delete", icon="delete", on_click=delete_preset).classes(
                        "btn"
                    ).props("dense color=negative icon-only")

    async def _view_preset(self, preset) -> None:
        """View preset details in a dialog."""
        dialog = ViewPresetDialog(preset=preset)
        await dialog.show()

    async def _delete_preset(self, preset) -> None:
        """Delete a preset with confirmation."""
        from components.dialogs.common.tournament_dialogs import ConfirmDialog

        async def confirm_delete():
            try:
                success = await self.service.delete_preset(
                    preset_id=preset.id,
                    organization_id=self.organization.id,
                    user=self.user,
                )
                if success:
                    ui.notify(f'Preset "{preset.name}" deleted', type="positive")
                    await self._refresh()
                else:
                    ui.notify("Preset not found", type="negative")
            except PermissionError as e:
                ui.notify(f"Permission denied: {str(e)}", type="negative")
            except Exception as e:
                logger.error("Error deleting preset: %s", e, exc_info=True)
                ui.notify(f"Error deleting preset: {str(e)}", type="negative")

        dialog = ConfirmDialog(
            title="Delete Preset",
            message=f'Are you sure you want to delete the preset "{preset.name}"? This action cannot be undone.',
            on_confirm=confirm_delete,
        )
        await dialog.show()
