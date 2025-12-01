"""
Preset Selection Rule Builder UI Component.

Provides a visual interface for tournament admins to build preset selection rules
without needing to write JSON manually.
"""

from nicegui import ui
from typing import List, Dict, Any, Optional, Callable
import logging

from application.services.tournaments import PresetSelectionService
from models.randomizer_preset import RandomizerPreset

logger = logging.getLogger(__name__)


class RuleConditionBuilder:
    """
    Visual builder for a single rule condition.
    
    Allows users to select field, operator, and value through dropdowns and inputs.
    """
    
    # Available fields that can be used in conditions
    AVAILABLE_FIELDS = [
        {'value': 'match.title', 'label': 'Match Title'},
        {'value': 'match.round_number', 'label': 'Round Number'},
        {'value': 'match.game_number', 'label': 'Game Number'},
        {'value': 'match.scheduled_at.day_of_week', 'label': 'Day of Week'},
        {'value': 'match.scheduled_at.hour', 'label': 'Hour of Day'},
        {'value': 'settings.difficulty', 'label': 'Player Setting: difficulty'},
        # Add more as needed
    ]
    
    # Operators grouped by type
    OPERATORS = {
        'text': [
            {'value': 'equals', 'label': 'equals'},
            {'value': 'not_equals', 'label': 'does not equal'},
            {'value': 'contains', 'label': 'contains'},
            {'value': 'starts_with', 'label': 'starts with'},
            {'value': 'ends_with', 'label': 'ends with'},
        ],
        'number': [
            {'value': 'equals', 'label': '='},
            {'value': 'not_equals', 'label': '≠'},
            {'value': '>', 'label': '>'},
            {'value': '>=', 'label': '≥'},
            {'value': '<', 'label': '<'},
            {'value': '<=', 'label': '≤'},
            {'value': 'between', 'label': 'between'},
        ],
        'list': [
            {'value': 'in', 'label': 'is one of'},
            {'value': 'not_in', 'label': 'is not one of'},
        ]
    }
    
    def __init__(self, on_delete: Optional[Callable] = None):
        """
        Initialize condition builder.
        
        Args:
            on_delete: Callback when user clicks delete button
        """
        self.on_delete = on_delete
        
        # UI components (will be created in render)
        self.field_select = None
        self.operator_select = None
        self.value_input = None
        self.container = None
    
    def render(self) -> ui.element:
        """
        Render the condition builder UI.
        
        Returns:
            Container element for the condition
        """
        with ui.card().classes('w-full mb-2') as container:
            self.container = container
            
            with ui.row().classes('w-full items-center gap-2'):
                # Field selector
                self.field_select = ui.select(
                    options=self.AVAILABLE_FIELDS,
                    label='Field',
                    value='match.round_number',
                    on_change=self._on_field_changed
                ).classes('w-1/4')
                
                # Operator selector (populated based on field type)
                self.operator_select = ui.select(
                    options=self.OPERATORS['number'],
                    label='Operator',
                    value='equals'
                ).classes('w-1/4')
                
                # Value input (type changes based on field/operator)
                self.value_input = ui.input(
                    label='Value',
                    value=''
                ).classes('w-1/3')
                
                # Delete button
                ui.button(
                    icon='delete',
                    on_click=lambda: self._on_delete_clicked() if self.on_delete else None
                ).props('flat color=negative').classes('mt-4')
        
        # Initialize operator options based on default field
        self._on_field_changed()
        
        return container
    
    def _on_field_changed(self):
        """Update operator options when field changes."""
        field = self.field_select.value
        
        # Determine field type and update operators
        if field in ['match.round_number', 'match.game_number', 'match.scheduled_at.hour']:
            # Numeric field
            self.operator_select.options = self.OPERATORS['number']
            self.value_input.props('type=number')
        elif field in ['match.scheduled_at.day_of_week', 'settings.difficulty']:
            # Categorical field (should use 'in' operator with predefined values)
            self.operator_select.options = self.OPERATORS['text'] + self.OPERATORS['list']
            self.value_input.props('type=text')
        else:
            # Text field
            self.operator_select.options = self.OPERATORS['text']
            self.value_input.props('type=text')
    
    def _on_delete_clicked(self):
        """Handle delete button click."""
        if self.on_delete:
            self.on_delete(self)
    
    def get_condition_config(self) -> Dict[str, Any]:
        """
        Get the condition configuration as JSON.
        
        Returns:
            Condition configuration dictionary
        """
        value = self.value_input.value
        
        # Convert to appropriate type
        operator = self.operator_select.value
        field = self.field_select.value
        
        # Numeric fields should have numeric values
        if field in ['match.round_number', 'match.game_number', 'match.scheduled_at.hour']:
            try:
                if operator == 'between':
                    # Parse comma-separated min,max
                    parts = value.split(',')
                    value = [float(parts[0]), float(parts[1])]
                else:
                    value = int(value) if value else 0
            except (ValueError, IndexError):
                value = 0
        
        # List operators should have array values
        elif operator in ['in', 'not_in']:
            # Parse comma-separated values
            value = [v.strip() for v in value.split(',')]
        
        return {
            'type': 'condition',
            'field': field,
            'operator': operator,
            'value': value
        }


class PresetSelectionRuleBuilder:
    """
    Visual builder for a complete preset selection rule.
    
    Combines multiple conditions with AND/OR logic and selects a preset to use.
    """
    
    def __init__(
        self,
        presets: List[RandomizerPreset],
        rule_config: Optional[Dict[str, Any]] = None,
        on_delete: Optional[Callable] = None
    ):
        """
        Initialize rule builder.
        
        Args:
            presets: Available presets to choose from
            rule_config: Existing rule configuration to edit (None for new)
            on_delete: Callback when user deletes this rule
        """
        self.presets = presets
        self.rule_config = rule_config or {}
        self.on_delete = on_delete
        
        # UI components
        self.rule_name_input = None
        self.preset_select = None
        self.logical_operator_select = None
        self.conditions: List[RuleConditionBuilder] = []
        self.conditions_container = None
        self.container = None
    
    def render(self) -> ui.element:
        """
        Render the rule builder UI.
        
        Returns:
            Container element for the rule
        """
        with ui.card().classes('w-full mb-4 p-4') as container:
            self.container = container
            
            # Rule header
            with ui.row().classes('w-full items-center justify-between mb-4'):
                self.rule_name_input = ui.input(
                    label='Rule Name',
                    value=self.rule_config.get('name', 'New Rule')
                ).classes('w-1/2')
                
                ui.button(
                    'Delete Rule',
                    icon='delete',
                    on_click=lambda: self._on_delete_clicked() if self.on_delete else None
                ).props('flat color=negative')
            
            ui.separator()
            
            # Preset selection
            with ui.row().classes('w-full items-center gap-4 mt-4 mb-4'):
                ui.label('When conditions match, use preset:').classes('text-lg')
                
                preset_options = [
                    {'value': p.id, 'label': p.name}
                    for p in self.presets
                ]
                
                self.preset_select = ui.select(
                    options=preset_options,
                    label='Preset',
                    value=self.rule_config.get('preset_id', preset_options[0]['value'] if preset_options else None)
                ).classes('w-1/2')
            
            ui.separator()
            
            # Conditions section
            with ui.column().classes('w-full gap-2 mt-4'):
                # Logical operator (AND/OR)
                with ui.row().classes('w-full items-center gap-2'):
                    ui.label('Match when').classes('text-lg')
                    
                    self.logical_operator_select = ui.select(
                        options=[
                            {'value': 'AND', 'label': 'ALL of these conditions are true (AND)'},
                            {'value': 'OR', 'label': 'ANY of these conditions are true (OR)'}
                        ],
                        value='AND'
                    ).classes('w-2/3')
                
                # Conditions container
                self.conditions_container = ui.column().classes('w-full gap-2 mt-2')
                
                # Add condition button
                ui.button(
                    'Add Condition',
                    icon='add',
                    on_click=self._add_condition
                ).props('flat color=primary').classes('mt-2')
            
            # Load existing conditions if editing
            if self.rule_config.get('conditions'):
                self._load_existing_conditions()
            else:
                # Start with one empty condition
                self._add_condition()
        
        return container
    
    def _add_condition(self):
        """Add a new condition builder."""
        condition_builder = RuleConditionBuilder(
            on_delete=self._remove_condition
        )
        
        with self.conditions_container:
            condition_builder.render()
        
        self.conditions.append(condition_builder)
    
    def _remove_condition(self, condition_builder: RuleConditionBuilder):
        """Remove a condition builder."""
        if condition_builder in self.conditions:
            self.conditions.remove(condition_builder)
            
            # Remove from UI
            if condition_builder.container:
                condition_builder.container.delete()
        
        # Ensure at least one condition remains
        if not self.conditions:
            self._add_condition()
    
    def _load_existing_conditions(self):
        """Load conditions from existing rule config."""
        # TODO: Parse existing conditions and create builders
        # For now, just add empty conditions
        self._add_condition()
    
    def _on_delete_clicked(self):
        """Handle delete button click."""
        if self.on_delete:
            self.on_delete(self)
    
    def get_rule_config(self) -> Dict[str, Any]:
        """
        Get the complete rule configuration as JSON.
        
        Returns:
            Rule configuration dictionary
        """
        # Get all condition configs
        condition_configs = [
            cond.get_condition_config()
            for cond in self.conditions
        ]
        
        # Wrap in logical operator if multiple conditions
        if len(condition_configs) > 1:
            conditions = {
                'type': self.logical_operator_select.value,
                'conditions': condition_configs
            }
        elif len(condition_configs) == 1:
            conditions = condition_configs[0]
        else:
            # No conditions - invalid rule
            conditions = {}
        
        return {
            'name': self.rule_name_input.value,
            'preset_id': self.preset_select.value,
            'conditions': conditions
        }


class PresetSelectionRulesEditor:
    """
    Complete editor for preset selection rules configuration.
    
    Manages multiple rules with visual builder interface.
    """
    
    def __init__(self, tournament):
        """
        Initialize rules editor.
        
        Args:
            tournament: Tournament to configure rules for
        """
        self.tournament = tournament
        self.rules: List[PresetSelectionRuleBuilder] = []
        self.rules_container = None
        self.presets: List[RandomizerPreset] = []
    
    async def render(self):
        """Render the rules editor UI."""
        # Load available presets
        await self._load_presets()
        
        with ui.column().classes('w-full gap-4'):
            # Header
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.label('Preset Selection Rules').classes('text-2xl font-bold')
                
                ui.button(
                    'Add Rule',
                    icon='add',
                    on_click=self._add_rule
                ).props('color=primary')
            
            # Info card
            with ui.card().classes('w-full p-4 mb-4').props('flat'):
                ui.markdown('''
                    **How Rules Work:**
                    
                    Rules are evaluated **in order** from top to bottom.
                    The **first rule that matches** determines which preset to use.
                    If no rules match, the tournament's default preset is used.
                ''')
            
            # Rules container
            self.rules_container = ui.column().classes('w-full gap-4')
            
            # Load existing rules if any
            if self.tournament.preset_selection_rules:
                await self._load_existing_rules()
            
            # Action buttons
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancel', on_click=self._cancel).classes('btn')
                ui.button(
                    'Save Rules',
                    on_click=self._save_rules
                ).props('color=positive').classes('btn')
    
    async def _load_presets(self):
        """Load available presets for this tournament's randomizer."""
        # Get presets for this randomizer type
        self.presets = await RandomizerPreset.filter(
            randomizer=self.tournament.randomizer
        ).all()
        
        if not self.presets:
            ui.notify('No presets available for this randomizer', type='warning')
    
    async def _load_existing_rules(self):
        """Load existing rules from tournament config."""
        rules_config = self.tournament.preset_selection_rules
        rules_list = rules_config.get('rules', [])
        
        for rule_config in rules_list:
            self._add_rule(rule_config)
    
    def _add_rule(self, rule_config: Optional[Dict[str, Any]] = None):
        """Add a new rule builder."""
        rule_builder = PresetSelectionRuleBuilder(
            presets=self.presets,
            rule_config=rule_config,
            on_delete=self._remove_rule
        )
        
        with self.rules_container:
            rule_builder.render()
        
        self.rules.append(rule_builder)
    
    def _remove_rule(self, rule_builder: PresetSelectionRuleBuilder):
        """Remove a rule builder."""
        if rule_builder in self.rules:
            self.rules.remove(rule_builder)
            
            # Remove from UI
            if rule_builder.container:
                rule_builder.container.delete()
    
    async def _save_rules(self):
        """Save rules configuration to tournament."""
        # Collect all rule configs
        rules_configs = [
            rule.get_rule_config()
            for rule in self.rules
        ]
        
        # Build complete config
        config = {
            'rules': rules_configs
        }
        
        # Validate rules
        service = PresetSelectionService()
        is_valid, error = await service.validate_rules(config, self.tournament.id)
        
        if not is_valid:
            ui.notify(f'Invalid rules: {error}', type='negative')
            return
        
        # Save to tournament
        self.tournament.preset_selection_rules = config
        await self.tournament.save()
        
        ui.notify('Rules saved successfully', type='positive')
    
    def _cancel(self):
        """Cancel editing and close dialog."""
        ui.navigate.back()
