"""
Tournament Preset Selection Rules View.

Configure conditional logic for selecting randomizer presets based on match properties.
"""

from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional, Callable
from nicegui import ui
from models import User
from models.organizations import Organization
from modules.tournament.models.match_schedule import Tournament
from models.randomizer_preset import RandomizerPreset
from application.services.tournaments.preset_selection_service import (
    PresetSelectionService,
)
from application.services.randomizer.randomizer_preset_service import (
    RandomizerPresetService,
)

logger = logging.getLogger(__name__)


class TournamentPresetSelectionRulesView:
    """View for managing tournament preset selection rules."""

    def __init__(self, user: User, organization: Organization, tournament: Tournament):
        """
        Initialize the preset selection rules view.

        Args:
            user: Current user
            organization: Tournament's organization
            tournament: Tournament to manage
        """
        self.user = user
        self.organization = organization
        self.tournament = tournament
        self.selection_service = PresetSelectionService()
        self.preset_service = RandomizerPresetService()
        self.rules: List[RuleBuilder] = []
        self.rules_container = None
        self.available_presets: List[RandomizerPreset] = []

    async def render(self):
        """Render the preset selection rules view."""
        # Load available presets for this randomizer
        await self._load_presets()

        with ui.element("div").classes("card"):
            with ui.element("div").classes("card-header"):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label("Preset Selection Rules").classes("text-xl font-bold")
                    ui.button(
                        "Add Rule", icon="add", on_click=self._add_rule
                    ).props("color=primary")

            with ui.element("div").classes("card-body"):
                # Info section
                with ui.element("div").classes("card mb-4").props("flat"):
                    with ui.element("div").classes("card-body"):
                        ui.markdown(
                            """
                            **How Rules Work:**
                            
                            Rules allow you to automatically select different presets based on match conditions.
                            Rules are evaluated **in order** from top to bottom. The **first rule that matches**
                            determines which preset to use.
                            
                            If no rules match, the tournament's default preset (from Randomizer Settings) is used.
                            
                            **Example Use Cases:**
                            - Use beginner presets for early rounds, expert presets for finals
                            - Select presets based on player-submitted settings (difficulty, mode, etc.)
                            - Use different presets for different days or times
                            """
                        ).classes("text-sm")

                # Check if randomizer is configured
                if not self.tournament.randomizer:
                    with ui.element("div").classes("card bg-warning-light p-4"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("warning", color="warning")
                            ui.label(
                                "Please configure a randomizer in Randomizer Settings first."
                            ).classes("font-bold")
                    return

                # Check if presets are available
                if not self.available_presets:
                    with ui.element("div").classes("card bg-warning-light p-4"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("warning", color="warning")
                            ui.label(
                                f"No presets available for {self.tournament.randomizer}. "
                                "Create presets first before configuring rules."
                            ).classes("font-bold")
                    return

                # Rules container
                self.rules_container = ui.column().classes("w-full gap-4 mt-4")

                # Load existing rules
                await self._load_existing_rules()

                # Action buttons
                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=self._cancel).classes("btn")
                    ui.button("Save Rules", on_click=self._save_rules).props(
                        "color=positive"
                    ).classes("btn")

    async def _load_presets(self):
        """Load available presets for this tournament's randomizer."""
        if not self.tournament.randomizer:
            return

        self.available_presets = await self.preset_service.list_presets(
            user=self.user,
            randomizer=self.tournament.randomizer,
            include_global=True,
        )

    async def _load_existing_rules(self):
        """Load existing rules from tournament config."""
        if not self.tournament.preset_selection_rules:
            # Start with one empty rule
            self._add_rule()
            return

        rules_config = self.tournament.preset_selection_rules
        rules_list = rules_config.get("rules", [])

        if not rules_list:
            # Start with one empty rule
            self._add_rule()
            return

        for rule_config in rules_list:
            self._add_rule(rule_config)

    def _add_rule(self, rule_config: Optional[Dict[str, Any]] = None):
        """Add a new rule builder."""
        rule_builder = RuleBuilder(
            presets=self.available_presets,
            rule_config=rule_config,
            on_delete=self._remove_rule,
        )

        with self.rules_container:
            rule_builder.render()

        self.rules.append(rule_builder)

    def _remove_rule(self, rule_builder):
        """Remove a rule builder."""
        if rule_builder in self.rules:
            self.rules.remove(rule_builder)

            # Remove from UI
            if rule_builder.container:
                rule_builder.container.delete()

    async def _save_rules(self):
        """Save rules configuration to tournament."""
        # Collect all rule configs
        rules_configs = [rule.get_rule_config() for rule in self.rules]

        # Build complete config
        config = {"rules": rules_configs}

        # Validate rules
        is_valid, error = await self.selection_service.validate_rules(
            config, self.tournament.id
        )

        if not is_valid:
            ui.notify(f"Invalid rules: {error}", type="negative")
            return

        # Save to tournament
        self.tournament.preset_selection_rules = config
        await self.tournament.save()

        ui.notify("Rules saved successfully", type="positive")

        # Refresh the view
        if self.rules_container:
            self.rules_container.clear()
            self.rules.clear()
            await self._load_existing_rules()

    def _cancel(self):
        """Cancel editing."""
        # Reload the view
        ui.navigate.to(
            f"/org/{self.organization.id}/tournament/{self.tournament.id}/admin/preset-rules"
        )


class RuleBuilder:
    """Visual builder for a single preset selection rule."""

    # Available fields
    FIELDS = [
        {"value": "match.title", "label": "Match Title"},
        {"value": "match.round_number", "label": "Round Number"},
        {"value": "match.game_number", "label": "Game Number"},
        {"value": "match.scheduled_at.day_of_week", "label": "Day of Week"},
        {"value": "match.scheduled_at.hour", "label": "Hour of Day"},
        {"value": "settings.difficulty", "label": "Setting: difficulty"},
        {"value": "settings.mode", "label": "Setting: mode"},
    ]

    # Operators by type
    OPERATORS = {
        "text": [
            {"value": "equals", "label": "equals"},
            {"value": "not_equals", "label": "does not equal"},
            {"value": "contains", "label": "contains"},
        ],
        "number": [
            {"value": "equals", "label": "="},
            {"value": ">", "label": ">"},
            {"value": ">=", "label": "≥"},
            {"value": "<", "label": "<"},
            {"value": "<=", "label": "≤"},
        ],
    }

    def __init__(
        self,
        presets: List[RandomizerPreset],
        rule_config: Optional[Dict[str, Any]] = None,
        on_delete: Optional[Callable] = None,
    ):
        """
        Initialize rule builder.

        Args:
            presets: Available presets
            rule_config: Existing rule config (None for new)
            on_delete: Callback when user deletes this rule
        """
        self.presets = presets
        self.rule_config = rule_config or {}
        self.on_delete = on_delete

        # UI components
        self.rule_name_input = None
        self.preset_select = None
        self.field_select = None
        self.operator_select = None
        self.value_input = None
        self.container = None

    def render(self):
        """Render the rule builder UI."""
        with ui.card().classes("w-full p-4") as container:
            self.container = container

            # Header
            with ui.row().classes("w-full items-center justify-between mb-4"):
                self.rule_name_input = ui.input(
                    label="Rule Name",
                    value=self.rule_config.get("name", "New Rule"),
                ).classes("flex-grow")

                ui.button(
                    icon="delete",
                    on_click=lambda: self.on_delete(self) if self.on_delete else None,
                ).props("flat color=negative")

            ui.separator()

            # Preset selection
            with ui.row().classes("w-full items-center gap-2 mt-4"):
                ui.label("Use preset:").classes("text-lg")

                preset_options = [{"value": p.id, "label": p.name} for p in self.presets]

                self.preset_select = ui.select(
                    options=preset_options,
                    label="Preset",
                    value=self.rule_config.get(
                        "preset_id", preset_options[0]["value"] if preset_options else None
                    ),
                ).classes("flex-grow")

            ui.separator().classes("my-4")

            # Condition builder (simplified - single condition for now)
            ui.label("When this condition is true:").classes("text-lg mb-2")

            with ui.row().classes("w-full items-center gap-2"):
                self.field_select = ui.select(
                    options=self.FIELDS,
                    label="Field",
                    value="match.round_number",
                    on_change=self._on_field_changed,
                ).classes("w-1/3")

                self.operator_select = ui.select(
                    options=self.OPERATORS["number"],
                    label="Operator",
                    value="<=",
                ).classes("w-1/4")

                self.value_input = ui.input(label="Value", value="").classes("flex-grow")

            # Load existing condition if editing
            if self.rule_config.get("conditions"):
                self._load_existing_condition()

    def _on_field_changed(self):
        """Update operators when field changes."""
        field = self.field_select.value

        # Numeric fields
        if field in [
            "match.round_number",
            "match.game_number",
            "match.scheduled_at.hour",
        ]:
            self.operator_select.options = self.OPERATORS["number"]
        else:
            # Text fields
            self.operator_select.options = self.OPERATORS["text"]

        self.operator_select.update()

    def _load_existing_condition(self):
        """Load existing condition values."""
        conditions = self.rule_config.get("conditions", {})

        if conditions.get("type") == "condition":
            # Simple condition
            self.field_select.value = conditions.get("field", "match.round_number")
            self.operator_select.value = conditions.get("operator", "<=")
            self.value_input.value = str(conditions.get("value", ""))

    def get_rule_config(self) -> Dict[str, Any]:
        """Get rule configuration as JSON."""
        value = self.value_input.value

        # Convert to appropriate type based on field
        field = self.field_select.value
        if field in [
            "match.round_number",
            "match.game_number",
            "match.scheduled_at.hour",
        ]:
            try:
                value = int(value) if value else 0
            except ValueError:
                value = 0

        return {
            "name": self.rule_name_input.value,
            "preset_id": self.preset_select.value,
            "conditions": {
                "type": "condition",
                "field": field,
                "operator": self.operator_select.value,
                "value": value,
            },
        }
