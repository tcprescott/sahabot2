# Preset Selection Rules - UI Integration Summary

## Overview

This document summarizes the complete integration of conditional preset selection rules into the tournament administration UI. The feature allows tournament administrators to define declarative JSON rules that conditionally select which randomizer preset to use for each match based on match context (pool, round, players, settings submissions).

## What Was Implemented

### 1. Core Service Layer ✅

**File**: `application/services/tournaments/preset_selection_service.py` (580+ lines)

Complete rule evaluation engine with:
- **Declarative JSON Rule Schema**: Safe, validated rule definitions with no code execution
- **Rule Evaluation**: `select_preset_for_match()` evaluates rules against match context
- **Nested Logic**: Supports AND/OR/NOT operators for complex conditions
- **Rich Operators**: 11 comparison operators (eq, ne, gt, lt, contains, in, etc.)
- **Type Safety**: Strong validation with detailed error messages
- **Security**: No eval(), exec(), or code execution - pure data-driven evaluation

### 2. UI Components ✅

**File**: `views/tournament_admin/tournament_preset_selection_rules.py` (380+ lines)

Two main components:

#### TournamentPresetSelectionRulesView
Main view class providing:
- Card-based layout showing current configuration
- "Add Rule" button to add new conditional rules
- List of existing rules with preset names and field conditions
- Delete buttons for each rule
- "Save Configuration" button with validation

#### RuleBuilder  
Dialog for creating/editing individual rules:
- Preset dropdown (loads all presets for tournament's randomizer)
- Field selection dropdown (pool_name, round_number, match_title, etc.)
- Operator selection (equals, contains, greater than, etc.)
- Value input field
- Add/Cancel buttons
- Validation before adding rule

**Simplified for v1**: Single condition per rule (not full nested AND/OR logic)

### 3. Tournament Admin Integration ✅

**File**: `pages/tournament_admin.py`

Added preset selection rules to tournament admin page:
- Imported `TournamentPresetSelectionRulesView`
- Created `load_preset_rules()` async content loader function
- Registered loader with key `"preset-rules"`
- Added sidebar navigation item:
  - Label: "Preset Selection Rules"
  - Icon: `"rule"`
  - Loader: `"preset-rules"`

**Navigation**: Admin → Organizations → {Org} → Tournaments → {Tournament} → Admin → **Preset Selection Rules** (sidebar)

### 4. Database Schema ✅

**File**: `models/match_schedule.py`

Added field to `Tournament` model:
```python
preset_selection_rules = fields.JSONField(
    null=True
)  # Conditional preset selection rules (evaluated per match)
```

**Migration**: `migrations/models/54_20251109183352_add_preset_selection_rules_to_tournament.py`

Migration adds:
- `preset_selection_rules` JSON column to `tournament` table
- Also includes `randomizer` and `randomizer_preset_id` fields (from fixed manual migration)
- Includes proper upgrade/downgrade functions
- Generated with Aerich (includes required MODELS_STATE tracking)

## JSON Schema

Rules are stored as JSON in the `preset_selection_rules` field:

```json
{
  "rules": [
    {
      "preset_id": 123,
      "condition": {
        "field": "pool_name",
        "operator": "eq",
        "value": "Top 8"
      }
    },
    {
      "preset_id": 456,
      "condition": {
        "field": "round_number",
        "operator": "gte",
        "value": 4
      }
    }
  ],
  "fallback_preset_id": 789
}
```

## How It Works

### Rule Evaluation Flow

1. **Seed Generation Request**: When generating a seed for a match
2. **Check for Rules**: Service checks if tournament has `preset_selection_rules` configured
3. **Build Context**: Gather match context (pool_name, round_number, players, settings)
4. **Evaluate Rules**: Iterate through rules in order, evaluate conditions
5. **First Match Wins**: First rule with condition evaluating to `True` wins
6. **Fallback**: If no rules match, use `fallback_preset_id` or tournament default
7. **Generate Seed**: Use selected preset to generate seed/permalink

### Available Context Fields

Rules can reference these match context fields:

| Field | Type | Description |
|-------|------|-------------|
| `pool_name` | string | Name of pool (if match in pool) |
| `round_number` | int | Round number in tournament bracket |
| `match_title` | string | Custom match title |
| `player_count` | int | Number of players in match |
| `player_names` | list[string] | List of player Discord usernames |
| `player_ids` | list[int] | List of player user IDs |
| `has_crew` | bool | Whether match has crew members |
| `settings_*` | mixed | Any field from settings submissions (e.g., `settings_difficulty`) |

### Supported Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equals | `pool_name eq "Top 8"` |
| `ne` | Not equals | `round_number ne 1` |
| `gt` | Greater than | `player_count gt 2` |
| `gte` | Greater than or equal | `round_number gte 4` |
| `lt` | Less than | `round_number lt 3` |
| `lte` | Less than or equal | `player_count lte 4` |
| `in` | Value in list | `pool_name in ["Group A", "Group B"]` |
| `not_in` | Value not in list | `player_names not_in ["banned_user"]` |
| `contains` | List/string contains value | `player_names contains "champion123"` |
| `not_contains` | List/string doesn't contain | `match_title not_contains "practice"` |
| `exists` | Field exists/not null | `pool_name exists true` |

## User Experience

### Creating Rules

1. Navigate to tournament admin → "Preset Selection Rules"
2. Click "Add Rule" button
3. In dialog:
   - Select preset from dropdown
   - Select field to check (e.g., "Pool Name")
   - Select operator (e.g., "equals")
   - Enter value (e.g., "Top 8")
4. Click "Add Rule"
5. Rule appears in list
6. Click "Save Configuration" to persist

### Rule Evaluation Order

- Rules are evaluated **in the order displayed** (top to bottom)
- **First matching rule wins** - evaluation stops after first match
- If no rules match, **fallback preset** is used
- If no fallback preset and no match, **tournament default preset** is used

### Example Use Cases

**Use Case 1: Different Presets by Pool**
- Pool "Beginners" → Easy preset
- Pool "Advanced" → Hard preset
- Fallback → Medium preset

**Use Case 2: Escalating Difficulty**
- Round 1-2 → Easy preset  
- Round 3-4 → Medium preset
- Round 5+ → Hard preset

**Use Case 3: Player-Specific Settings**
- If player "champion123" in match → Tournament preset
- If player submitted settings_difficulty="hard" → Hard preset
- Fallback → Normal preset

## Files Modified/Created

### Created Files (3)
1. `application/services/tournaments/preset_selection_service.py` - Service layer (580 lines)
2. `views/tournament_admin/tournament_preset_selection_rules.py` - UI components (380 lines)
3. `migrations/models/54_20251109183352_add_preset_selection_rules_to_tournament.py` - Database migration

### Modified Files (4)
1. `models/match_schedule.py` - Added `preset_selection_rules` JSONField to Tournament model
2. `pages/tournament_admin.py` - Added view import, content loader, sidebar item
3. `views/tournament_admin/__init__.py` - Added TournamentPresetSelectionRulesView export
4. `application/services/tournaments/__init__.py` - (Assumed) Added PresetSelectionService export

### Documentation (3)
1. `docs/features/PRESET_SELECTION_RULES.md` - Complete design specification (440+ lines)
2. `docs/features/PRESET_SELECTION_INTEGRATION_EXAMPLE.md` - Integration examples
3. `docs/features/PRESET_SELECTION_IMPLEMENTATION_SUMMARY.md` - Implementation summary
4. `PRESET_SELECTION_UI_INTEGRATION.md` - This document

**Total Lines of Code**: 2000+ (service + UI + documentation)

## Next Steps

### 1. Apply Database Migration ⏳

```bash
cd /Users/tprescott/Library/CloudStorage/OneDrive-Personal/Documents/VSCode/sahabot2
poetry run aerich upgrade
```

This will:
- Add `preset_selection_rules` JSON column to `tournament` table
- Add `randomizer` and `randomizer_preset_id` columns (if not already present)
- Enable storing rule configurations

### 2. Test UI Integration ⏳

1. Start development server: `./start.sh dev`
2. Navigate to a tournament admin page
3. Click "Preset Selection Rules" in sidebar
4. Verify view loads correctly
5. Test adding/removing rules
6. Test saving configuration
7. Verify validation works (try invalid values)

### 3. Wire into Seed Generation ⏳

Currently, seed generation uses `tournament.randomizer_preset_id` directly. Need to integrate preset selection:

**File to modify**: `views/tournaments/event_schedule.py` (or wherever seed generation happens)

**Integration code** (see `docs/features/PRESET_SELECTION_INTEGRATION_EXAMPLE.md` for details):

```python
from application.services.tournaments.preset_selection_service import PresetSelectionService

async def generate_seed(self, match: Match):
    """Generate seed for a match."""
    # Get tournament
    tournament = await match.tournament
    
    # Check if tournament has preset selection rules
    if tournament.preset_selection_rules:
        # Use preset selection service
        preset_service = PresetSelectionService()
        selected_preset = await preset_service.select_preset_for_match(match)
        
        if selected_preset:
            preset_id = selected_preset.id
        else:
            # Fallback to tournament default
            preset_id = tournament.randomizer_preset_id
    else:
        # No rules configured, use tournament default
        preset_id = tournament.randomizer_preset_id
    
    # Generate seed with selected preset
    # ... existing seed generation logic using preset_id ...
```

### 4. Add Audit Logging (Optional) ⏳

Log when preset selection rules are created/updated:

```python
from application.services.audit_service import AuditService

audit = AuditService()
await audit.log_action(
    user=current_user,
    action="tournament_preset_rules_updated",
    details={
        "tournament_id": tournament.id,
        "rule_count": len(rules)
    },
    organization_id=tournament.organization_id
)
```

### 5. Add Tests (Recommended) ⏳

**Unit Tests**:
- Test `PresetSelectionService.select_preset_for_match()` with various contexts
- Test `PresetSelectionService.validate_rules()` with valid/invalid rules
- Test operator evaluation (`_compare_values()`)
- Test nested condition evaluation (`_evaluate_condition()`)

**Integration Tests**:
- Test full flow: configure rules → generate seed → verify correct preset used
- Test fallback behavior when no rules match
- Test edge cases (empty rules, null values, invalid operators)

**UI Tests** (manual for now):
- Test adding/removing rules via UI
- Test saving/loading configuration
- Test validation error messages
- Test preset dropdown loading

## Architecture Compliance

This implementation follows SahaBot2 architectural principles:

✅ **Four-Layer Architecture**: UI → Service → Repository → Model (no skipping layers)
✅ **Separation of Concerns**: UI handles presentation, service handles business logic
✅ **Type Safety**: Full type hints throughout
✅ **Async/Await**: All database/service operations properly async
✅ **Logging Standards**: Lazy % formatting, no print() statements
✅ **Security**: No code execution, declarative rules only, validation before save
✅ **Documentation**: Comprehensive docstrings and external documentation
✅ **Mobile-First UI**: Card-based responsive design
✅ **External CSS**: No inline styles, uses existing CSS classes
✅ **Multi-Tenant**: Organization-scoped, validated membership
✅ **Event System**: (Can add event emission for rule updates)

## Security Considerations

1. **No Code Execution**: Rules are pure data, no eval()/exec()/compile()
2. **Validation**: Rules validated before save via `validate_rules()`
3. **Type Checking**: Strong type validation for field values
4. **Safe Operators**: Only predefined operators allowed
5. **Authorization**: Service methods check organization membership (when wired to seed generation)
6. **Injection Prevention**: All values compared as data, not executed as code

## Known Limitations (v1)

1. **Single Condition Per Rule**: Full nested AND/OR/NOT logic not implemented in UI (service supports it)
2. **No Rule Reordering**: Rules evaluated in order they appear, no drag-to-reorder (yet)
3. **No Rule Testing**: No "test rule" feature to see which preset would be selected for a hypothetical match
4. **No Preset Preview**: UI doesn't show preset details (name, description, settings)
5. **No Validation Feedback**: Validation happens on save, not as-you-type
6. **Not Wired to Seed Generation**: Rules are saved but not yet used in actual seed generation flow

## Future Enhancements

Potential improvements for future iterations:

1. **Advanced Rule Builder**: Full AND/OR/NOT logic with nested conditions in UI
2. **Drag-to-Reorder**: Reorder rules visually to change evaluation priority
3. **Rule Testing Tool**: "Test Rule" button to simulate evaluation with mock match data
4. **Preset Preview**: Show preset details when hovering/selecting in dropdown
5. **Live Validation**: Validate field/operator/value as user types
6. **Bulk Operations**: Copy rules between tournaments, import/export rule sets
7. **Rule Templates**: Pre-built rule templates for common scenarios
8. **Statistics**: Track which presets are selected most often, rule hit rates
9. **Audit Trail**: Log every preset selection decision for transparency
10. **API Endpoints**: RESTful API for managing rules programmatically
11. **Discord Bot Commands**: Commands to view/modify rules from Discord

## Success Metrics

After integration and testing, success can be measured by:

1. **Functionality**: Rules correctly select presets based on match context
2. **Usability**: Tournament admins can create rules without documentation
3. **Performance**: Rule evaluation adds <100ms to seed generation time
4. **Reliability**: No failed seed generations due to rule evaluation errors
5. **Adoption**: Tournament admins use preset selection rules for conditional logic

## References

- **Design Document**: `docs/features/PRESET_SELECTION_RULES.md`
- **Integration Examples**: `docs/features/PRESET_SELECTION_INTEGRATION_EXAMPLE.md`
- **Implementation Summary**: `docs/features/PRESET_SELECTION_IMPLEMENTATION_SUMMARY.md`
- **Copilot Instructions**: `.github/copilot-instructions.md` (migration patterns, service usage)

---

**Last Updated**: November 9, 2025  
**Status**: UI Integration Complete, Database Migration Created, Ready for Testing
