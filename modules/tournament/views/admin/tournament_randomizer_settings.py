"""
Tournament Randomizer Settings View.

Configure the randomizer and preset used for seed generation in this tournament.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import User
from models.organizations import Organization
from modules.tournament.models.match_schedule import Tournament
from application.services.randomizer.randomizer_service import RandomizerService
from application.services.randomizer.randomizer_preset_service import (
    RandomizerPresetService,
)

logger = logging.getLogger(__name__)


class TournamentRandomizerSettingsView:
    """View for managing tournament randomizer settings."""

    def __init__(self, user: User, organization: Organization, tournament: Tournament):
        """
        Initialize the randomizer settings view.

        Args:
            user: Current user
            organization: Tournament's organization
            tournament: Tournament to manage
        """
        self.user = user
        self.organization = organization
        self.tournament = tournament
        self.randomizer_service = RandomizerService()
        self.preset_service = RandomizerPresetService()

    async def render(self):
        """Render the tournament randomizer settings view."""
        with ui.element("div").classes("card"):
            with ui.element("div").classes("card-header"):
                ui.label("Randomizer Settings").classes("text-xl font-bold")

            with ui.element("div").classes("card-body"):
                ui.label(
                    "Configure which randomizer and preset to use when generating seeds for this tournament."
                ).classes("text-sm text-grey mb-4")

                # Get available randomizers
                available_randomizers = self.randomizer_service.list_randomizers()
                randomizer_options = {r: r.upper() for r in available_randomizers}

                # Randomizer selection
                ui.label("Randomizer:").classes("font-bold mb-2")
                randomizer_select = ui.select(
                    label="Select Randomizer",
                    options=randomizer_options,
                    value=self.tournament.randomizer,
                ).classes("w-full mb-4")

                ui.label(
                    "Choose the randomizer to use for generating seeds in the Event Schedule."
                ).classes("text-caption text-grey mb-4")

                # Preset selection
                ui.label("Preset:").classes("font-bold mb-2")
                preset_select = ui.select(
                    label="Select Preset", options={}, value=None
                ).classes("w-full mb-4")

                ui.label(
                    "Select a preset configuration for the randomizer. Presets are loaded based on the selected randomizer."
                ).classes("text-caption text-grey mb-4")

                # Info message about generating seeds
                with ui.row().classes(
                    "items-start gap-2 mb-4 p-3 bg-info-light rounded"
                ):
                    ui.icon("info", color="info")
                    with ui.column().classes("gap-1"):
                        ui.label("Seed Generation").classes("font-bold text-info")
                        ui.label(
                            "Once configured, you can generate seeds directly from the Event Schedule "
                            "using the dice icon button next to each match."
                        ).classes("text-sm")

                # Load presets when randomizer changes
                async def load_presets():
                    """Load presets for the selected randomizer."""
                    selected_randomizer = randomizer_select.value
                    if not selected_randomizer:
                        preset_select.options = {}
                        preset_select.value = None
                        preset_select.update()
                        return

                    # Load presets for this randomizer
                    presets = await self.preset_service.list_presets(
                        user=self.user,
                        randomizer=selected_randomizer,
                        mine_only=False,
                        include_global=True,
                    )

                    # Build options
                    preset_options = {None: "No preset (default settings)"}
                    for preset in presets:
                        # Show namespace or "Global" in label
                        if preset.is_global:
                            label = f"{preset.name} (Global)"
                        else:
                            label = f"{preset.name}"
                        preset_options[preset.id] = label

                    preset_select.options = preset_options

                    # Set current value if tournament has a preset
                    if self.tournament.randomizer_preset_id:
                        preset_select.value = self.tournament.randomizer_preset_id
                    else:
                        preset_select.value = None

                    preset_select.update()

                # Load presets initially if randomizer is set
                if self.tournament.randomizer:
                    ui.timer(0.1, load_presets, once=True)

                # Re-load presets when randomizer changes
                randomizer_select.on("update:model-value", lambda: load_presets())

                ui.separator().classes("my-4")

                # Save button
                with ui.row().classes("justify-end mt-4"):
                    ui.button(
                        "Save Settings",
                        on_click=lambda: self._save_settings(
                            randomizer_select.value, preset_select.value
                        ),
                    ).classes("btn").props("color=positive")

    async def _save_settings(self, randomizer: str, preset_id: int):
        """
        Save randomizer settings.

        Args:
            randomizer: Selected randomizer type
            preset_id: Selected preset ID (or None)
        """
        from modules.tournament.services.tournament_service import (
            TournamentService,
        )

        # Validate randomizer
        if randomizer and randomizer not in self.randomizer_service.list_randomizers():
            ui.notify("Invalid randomizer selected", type="negative")
            return

        service = TournamentService()
        try:
            await service.update_tournament(
                user=self.user,
                organization_id=self.organization.id,
                tournament_id=self.tournament.id,
                randomizer=randomizer,
                randomizer_preset_id=preset_id,
            )

            ui.notify("Randomizer settings saved successfully", type="positive")
            # No need to reload page - just show confirmation
        except ValueError as e:
            ui.notify(str(e), type="negative")
        except Exception as e:
            logger.error("Failed to save randomizer settings: %s", e)
            ui.notify(f"Error saving settings: {str(e)}", type="negative")
