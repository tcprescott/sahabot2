# Tournament Preset Selection Rules

## Overview

Tournament admins can configure conditional logic for selecting which randomizer preset to use for a match based on match properties, player submissions, or tournament state.

## Architecture

### Safety-First Design

**NO arbitrary code execution** - uses a declarative JSON rule format that is:
- ✅ Safe (no code injection possible)
- ✅ Validated at configuration time
- ✅ Predictable and auditable
- ✅ Extensible through new rule types

### Rule Evaluation Flow

```
Match Created/Updated
    ↓
Tournament has preset_selection_rules? → No → Use tournament.randomizer_preset
    ↓ Yes
Evaluate rules in order
    ↓
First matching rule → Use specified preset
    ↓
No rules match → Use default (tournament.randomizer_preset)
```

## Rule Schema

### Tournament Model Addition

```python
# In models/match_schedule.py - Tournament model
preset_selection_rules = fields.JSONField(null=True)
# Stores list of rule objects evaluated in order
```

### Rule Structure

```json
{
  "rules": [
    {
      "name": "Winners Bracket Finals",
      "description": "Use hard preset for finals matches",
      "conditions": {
        "type": "AND",
        "conditions": [
          {
            "field": "match.title",
            "operator": "contains",
            "value": "Finals"
          },
          {
            "field": "match.round_number",
            "operator": ">=",
            "value": 5
          }
        ]
      },
      "preset_id": 123
    },
    {
      "name": "Best-of-5 Series",
      "description": "Use progressive difficulty based on game number",
      "conditions": {
        "field": "match.game_number",
        "operator": "in",
        "value": [3, 4, 5]
      },
      "preset_id": 456
    },
    {
      "name": "Player Preference Override",
      "description": "Use custom preset if both players requested it",
      "conditions": {
        "type": "AND",
        "conditions": [
          {
            "field": "settings.preset",
            "operator": "equals",
            "value": "custom"
          },
          {
            "field": "settings.difficulty",
            "operator": ">=",
            "value": 7
          }
        ]
      },
      "preset_id": 789
    }
  ]
}
```

## Supported Condition Fields

### Match Properties

- `match.title` - Match title string
- `match.round_number` - Round number (if applicable)
- `match.scheduled_at` - Match datetime (ISO format)
- `match.game_number` - Game number in best-of-N series
- `match.player_count` - Number of players

### Player Submissions (from TournamentMatchSettings)

- `settings.*` - Any field from player-submitted settings
- `settings.preset` - Requested preset name
- `settings.difficulty` - Difficulty level
- `settings.mode` - Game mode
- (Any custom fields from DynamicFormBuilder)

### Tournament State

- `tournament.round_name` - Current round name
- `tournament.stage` - Tournament stage (pools, brackets, finals)
- `tournament.match_count` - Total matches in tournament

## Supported Operators

### Comparison Operators

- `equals` - Exact match (string, number, boolean)
- `not_equals` - Not equal
- `contains` - String contains substring (case-insensitive)
- `starts_with` - String starts with
- `ends_with` - String ends with
- `matches_regex` - Regex pattern match (limited to safe patterns)

### Numeric Operators

- `>`, `>=`, `<`, `<=` - Numeric comparison
- `between` - Value between two numbers (inclusive)

### List Operators

- `in` - Value in list
- `not_in` - Value not in list
- `any_in` - Any value from list A in list B

### Logical Operators

- `AND` - All conditions must be true
- `OR` - At least one condition must be true
- `NOT` - Negate condition result

## Implementation Components

### 1. Rule Evaluation Service

```python
# application/services/tournaments/preset_selection_service.py

class PresetSelectionService:
    """Evaluates preset selection rules for matches."""
    
    async def select_preset_for_match(
        self,
        match: Match,
        tournament: Tournament,
        player_settings: Optional[TournamentMatchSettings] = None
    ) -> Optional[int]:
        """
        Evaluate rules and return preset_id to use.
        
        Args:
            match: The match to select preset for
            tournament: Tournament configuration
            player_settings: Optional player-submitted settings
            
        Returns:
            preset_id to use, or None to use tournament default
        """
        if not tournament.preset_selection_rules:
            return tournament.randomizer_preset_id
        
        # Build evaluation context
        context = await self._build_context(match, tournament, player_settings)
        
        # Evaluate rules in order
        rules = tournament.preset_selection_rules.get('rules', [])
        for rule in rules:
            if await self._evaluate_rule(rule, context):
                return rule.get('preset_id')
        
        # No rules matched, use default
        return tournament.randomizer_preset_id
```

### 2. Rule Validator

```python
# application/services/tournaments/preset_rule_validator.py

class PresetRuleValidator:
    """Validates preset selection rule configurations."""
    
    ALLOWED_FIELDS = {
        'match.title', 'match.round_number', 'match.scheduled_at',
        'match.game_number', 'match.player_count',
        'tournament.round_name', 'tournament.stage',
        # Plus dynamic 'settings.*' fields
    }
    
    ALLOWED_OPERATORS = {
        'equals', 'not_equals', 'contains', 'starts_with', 'ends_with',
        '>', '>=', '<', '<=', 'between', 'in', 'not_in',
        'AND', 'OR', 'NOT'
    }
    
    def validate_rules(self, rules_config: dict) -> tuple[bool, Optional[str]]:
        """
        Validate rule configuration.
        
        Returns:
            (is_valid, error_message)
        """
        # Validate structure
        # Validate field names
        # Validate operators
        # Validate value types
        # Check preset_id references exist
```

### 3. UI Components

#### Admin View: Rule Editor

```python
# views/tournament_admin/preset_selection_rules.py

class PresetSelectionRulesView:
    """View for configuring preset selection rules."""
    
    async def render(self):
        """Render rule editor interface."""
        # Visual rule builder (no code required)
        # - Add/remove rules
        # - Drag to reorder priority
        # - Condition builder with dropdowns
        # - Preset selector dropdown
        # - Test/preview button
```

#### Testing Interface

```python
# Test rules against example matches
test_button = ui.button("Test Rules", on_click=self._test_rules)

async def _test_rules(self):
    """Show dialog with example matches and which preset would be selected."""
    # Display table:
    # | Match Example | Matched Rule | Selected Preset |
```

### 4. Integration with Seed Generation

```python
# When generating seed for match (in views/tournaments/event_schedule.py)

async def generate_seed(match_id: int):
    preset_service = PresetSelectionService()
    
    # Get player settings if submitted
    settings_service = TournamentMatchSettingsService()
    player_settings = await settings_service.get_submission(user, match_id, game_number=1)
    
    # Evaluate rules to determine preset
    selected_preset_id = await preset_service.select_preset_for_match(
        match=match,
        tournament=tournament,
        player_settings=player_settings
    )
    
    # Use selected preset or fall back to tournament default
    if selected_preset_id:
        preset = await RandomizerPreset.get(id=selected_preset_id)
        settings_dict = preset.settings.get("settings", preset.settings)
    else:
        settings_dict = {}
    
    # Generate seed
    randomizer = RandomizerFactory.get_randomizer(tournament.randomizer)
    result = await randomizer.generate(settings_dict)
```

## Example Use Cases

### Use Case 1: Progressive Difficulty

Tournament wants harder settings as rounds progress:

```json
{
  "rules": [
    {
      "name": "Round 1-2 (Easy)",
      "conditions": {
        "field": "match.round_number",
        "operator": "<=",
        "value": 2
      },
      "preset_id": 100  // Easy preset
    },
    {
      "name": "Round 3-4 (Medium)",
      "conditions": {
        "field": "match.round_number",
        "operator": "between",
        "value": [3, 4]
      },
      "preset_id": 101  // Medium preset
    },
    {
      "name": "Finals (Hard)",
      "conditions": {
        "field": "match.round_number",
        "operator": ">=",
        "value": 5
      },
      "preset_id": 102  // Hard preset
    }
  ]
}
```

### Use Case 2: Player Preference with Approval

Allow players to request presets, but only certain ones:

```json
{
  "rules": [
    {
      "name": "Allow approved custom presets",
      "conditions": {
        "field": "settings.preset",
        "operator": "in",
        "value": ["preset-a", "preset-b", "preset-c"]
      },
      "preset_id": "${lookup:settings.preset}"  // Special token
    }
  ]
}
```

### Use Case 3: Time-Based Rotation

Different presets for different days:

```json
{
  "rules": [
    {
      "name": "Monday Challenge",
      "conditions": {
        "type": "AND",
        "conditions": [
          {
            "field": "match.scheduled_at.day_of_week",
            "operator": "equals",
            "value": "Monday"
          }
        ]
      },
      "preset_id": 200
    }
  ]
}
```

## Security Considerations

### ✅ Safe

- No code execution
- All operations predefined
- Input validation at configuration time
- Preset IDs validated to exist
- Field names whitelisted
- Operators whitelisted
- Regex patterns limited to safe subset

### ⚠️ Potential Issues

- **Circular references**: Ensure rules don't create infinite loops
- **Performance**: Complex rule sets could be slow (limit rule count)
- **Field access**: Only allow safe fields (no internal system fields)

### Mitigations

1. **Rule count limit**: Max 20 rules per tournament
2. **Condition depth limit**: Max 5 levels of nesting
3. **Field validation**: Only allow documented fields
4. **Timeout**: Evaluate rules with timeout
5. **Audit logging**: Log which rule matched for each match

## Database Migration

```python
# migrations/models/XX_add_preset_selection_rules.py

async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `tournament` ADD `preset_selection_rules` JSON NULL;
    """
```

## Testing Strategy

1. **Unit Tests**: Rule evaluation logic
2. **Integration Tests**: Full flow with real matches
3. **Security Tests**: Injection attempts, malformed rules
4. **Performance Tests**: Complex rule sets
5. **UI Tests**: Rule builder interface

## Future Enhancements

- **Template library**: Pre-built rule templates for common scenarios
- **Rule debugging**: Show why a rule matched/didn't match
- **Rule analytics**: Track which rules are used most
- **Conditional actions**: Not just preset selection (e.g., auto-generate seed, send notifications)
- **External data sources**: Query external APIs in conditions (carefully sandboxed)

## Documentation for Tournament Admins

Include in-app help:
- Field reference with examples
- Operator reference
- Common patterns/recipes
- Troubleshooting guide

## Alternatives Considered

### ❌ Python Expression Evaluation

```python
# Using eval() or ast.literal_eval()
rule = "match.round_number >= 5 and settings.difficulty > 7"
```

**Rejected**: Too dangerous, code injection risk

### ❌ Lua Sandboxing

```lua
-- Embedded Lua scripts
if match.round_number >= 5 then
  return preset_hard
end
```

**Rejected**: Adds complexity, still has security concerns

### ✅ Declarative JSON Rules (Chosen)

- Safe by design
- Easy to validate
- Easy to test
- Easy for admins to understand
- Can build nice UI for it

## Implementation Phases

### Phase 1: Core Engine (MVP)
- Rule evaluation service
- Basic operators (equals, >, <, in)
- Match field support
- Integration with seed generation

### Phase 2: UI Builder
- Visual rule editor
- Drag-and-drop rule ordering
- Preset selector
- Test interface

### Phase 3: Advanced Features
- Settings field support
- Complex logical operators (AND/OR/NOT)
- Template library
- Rule debugging tools

### Phase 4: Analytics & Optimization
- Usage tracking
- Performance optimization
- Rule suggestions based on patterns
