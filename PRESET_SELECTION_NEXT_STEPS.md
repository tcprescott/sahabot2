# Preset Selection Rules - Next Steps Checklist

## Immediate Actions Required

### 1. Apply Database Migration ⏳ CRITICAL
```bash
cd /Users/tprescott/Library/CloudStorage/OneDrive-Personal/Documents/VSCode/sahabot2
poetry run aerich upgrade
```

**What it does**:
- Adds `preset_selection_rules` JSON column to `tournament` table
- Adds `randomizer` VARCHAR(50) column to `tournament` table  
- Adds `randomizer_preset_id` INT column to `tournament` table
- Creates foreign key constraint to `randomizer_presets` table

**Why it's critical**: Without this, the UI will fail when trying to save rules because the database column doesn't exist.

---

### 2. Test UI Integration ⏳ HIGH PRIORITY

**Steps**:
1. Start development server:
   ```bash
   ./start.sh dev
   ```

2. Navigate to tournament admin:
   - Go to Admin → Organizations
   - Select an organization
   - Select a tournament
   - Click "Admin" in sidebar
   - **Look for "Preset Selection Rules" in sidebar**

3. Test basic functionality:
   - [ ] Click "Preset Selection Rules" - verify view loads
   - [ ] Click "Add Rule" - verify dialog opens
   - [ ] Select a preset - verify dropdown works
   - [ ] Select a field - verify dropdown has options
   - [ ] Select an operator - verify dropdown changes based on field
   - [ ] Enter a value - verify input accepts text/numbers
   - [ ] Click "Add Rule" - verify rule appears in list
   - [ ] Click delete icon - verify rule is removed
   - [ ] Click "Save Configuration" - verify success notification
   - [ ] Refresh page - verify rules persist

4. Test validation:
   - [ ] Try adding rule without preset - should show error
   - [ ] Try adding rule without field - should show error
   - [ ] Try adding rule without operator - should show error
   - [ ] Try adding rule without value - should show error
   - [ ] Try saving empty configuration - should succeed (clears rules)

5. Test error handling:
   - [ ] Try with tournament that has no presets - should show empty state
   - [ ] Try with invalid JSON in database - should show error message

---

### 3. Wire into Seed Generation ⏳ HIGH PRIORITY

**File to modify**: Find where seed generation happens (likely `views/tournaments/event_schedule.py` or similar)

**Search for seed generation code**:
```bash
grep -r "generate_seed\|permalink" views/tournaments/*.py
grep -r "randomizer_preset" views/tournaments/*.py
```

**Integration pattern** (see `docs/features/PRESET_SELECTION_INTEGRATION_EXAMPLE.md`):

```python
from application.services.tournaments.preset_selection_service import PresetSelectionService

async def generate_seed(self, match: Match):
    """Generate seed for a match."""
    # Get tournament
    tournament = await match.tournament
    
    # Determine preset to use
    preset_id = None
    
    # Check if tournament has preset selection rules
    if tournament.preset_selection_rules:
        preset_service = PresetSelectionService()
        selected_preset = await preset_service.select_preset_for_match(match)
        
        if selected_preset:
            preset_id = selected_preset.id
            logger.info(
                "Selected preset %s for match %s via rules",
                preset_id, match.id
            )
    
    # Fallback to tournament default preset
    if not preset_id:
        preset_id = tournament.randomizer_preset_id
        logger.info(
            "Using tournament default preset %s for match %s",
            preset_id, match.id
        )
    
    if not preset_id:
        raise ValueError("No preset configured for tournament")
    
    # Generate seed with selected preset
    # ... existing seed generation logic using preset_id ...
```

**Testing seed generation**:
1. Configure rules in UI for a tournament
2. Create a match that should trigger a rule
3. Generate seed for the match
4. Verify correct preset was used (check logs or seed details)
5. Create a match that doesn't match any rule
6. Verify fallback preset was used

---

## Optional Enhancements

### 4. Add Audit Logging ⏳ MEDIUM PRIORITY

**Why**: Track when preset rules are modified for accountability

**Implementation**:
```python
from application.services.audit_service import AuditService

# In TournamentPresetSelectionRulesView._save_configuration():
audit = AuditService()
await audit.log_action(
    user=self.user,
    action="tournament_preset_rules_updated",
    details={
        "tournament_id": self.tournament.id,
        "rule_count": len(rules_config["rules"]) if rules_config else 0,
        "has_fallback": "fallback_preset_id" in (rules_config or {})
    },
    organization_id=self.organization.id
)
```

---

### 5. Add Unit Tests ⏳ MEDIUM PRIORITY

**Test file**: `tests/unit/test_preset_selection_service.py`

**Test cases to cover**:
- [ ] Test `select_preset_for_match()` with simple condition (eq operator)
- [ ] Test `select_preset_for_match()` with numeric comparison (gt, lt, gte, lte)
- [ ] Test `select_preset_for_match()` with list operators (in, not_in, contains)
- [ ] Test `select_preset_for_match()` with no matching rules (fallback)
- [ ] Test `select_preset_for_match()` with null/missing fields
- [ ] Test `validate_rules()` with valid rules
- [ ] Test `validate_rules()` with invalid rules (missing fields, bad operators)
- [ ] Test `_compare_values()` with different types (string, int, bool, list)
- [ ] Test `_evaluate_condition()` with nested AND/OR/NOT logic
- [ ] Test edge cases (empty rules, null preset_id, invalid field names)

**Example test**:
```python
import pytest
from application.services.tournaments.preset_selection_service import PresetSelectionService
from models import Match, Tournament, RandomizerPreset

@pytest.mark.asyncio
async def test_select_preset_simple_condition(db):
    """Test preset selection with simple equality condition."""
    # Setup
    service = PresetSelectionService()
    
    # Create tournament with rules
    tournament = await Tournament.create(
        organization_id=1,
        name="Test Tournament",
        preset_selection_rules={
            "rules": [
                {
                    "preset_id": 123,
                    "condition": {
                        "field": "pool_name",
                        "operator": "eq",
                        "value": "Top 8"
                    }
                }
            ],
            "fallback_preset_id": 456
        }
    )
    
    # Create match with pool_name = "Top 8"
    match = await Match.create(
        tournament=tournament,
        pool_name="Top 8"
    )
    
    # Execute
    selected_preset = await service.select_preset_for_match(match)
    
    # Verify
    assert selected_preset is not None
    assert selected_preset.id == 123
```

---

### 6. Add Integration Tests ⏳ LOW PRIORITY

**Test file**: `tests/integration/test_preset_selection_flow.py`

**Test cases**:
- [ ] End-to-end: Configure rules via UI → generate seed → verify correct preset used
- [ ] Test fallback behavior when no rules match
- [ ] Test with multiple rules, ensure first match wins
- [ ] Test with settings submissions (settings_* fields in context)
- [ ] Test with null/missing context fields
- [ ] Test error handling (invalid rules in database)

---

### 7. Export Service from __init__.py ⏳ LOW PRIORITY

**File**: `application/services/tournaments/__init__.py`

**Add**:
```python
from .preset_selection_service import PresetSelectionService

__all__ = [
    # ... existing services ...
    "PresetSelectionService",
]
```

---

## Testing Scenarios

### Scenario 1: Basic Rule (Pool-Based Preset)

**Setup**:
1. Tournament has 3 presets:
   - "Easy" (id=100)
   - "Medium" (id=200)  
   - "Hard" (id=300)

2. Configure rules:
   - Rule 1: If pool_name = "Beginners" → Use "Easy" preset
   - Rule 2: If pool_name = "Advanced" → Use "Hard" preset
   - Fallback: "Medium" preset

**Test**:
- Create match in "Beginners" pool → Should use Easy preset (100)
- Create match in "Advanced" pool → Should use Hard preset (300)
- Create match with no pool → Should use Medium preset (200)

---

### Scenario 2: Round-Based Escalation

**Setup**:
1. Configure rules:
   - Rule 1: If round_number <= 2 → Use "Easy" preset
   - Rule 2: If round_number <= 4 → Use "Medium" preset
   - Rule 3: If round_number > 4 → Use "Hard" preset

**Test**:
- Match in round 1 → Easy
- Match in round 3 → Medium
- Match in round 5 → Hard
- Match in round 10 → Hard

---

### Scenario 3: Player-Specific Settings

**Setup**:
1. Configure rules:
   - Rule 1: If player_names contains "champion123" → Use "Tournament" preset
   - Rule 2: If settings_difficulty = "hard" → Use "Hard" preset
   - Fallback: "Normal" preset

**Test**:
- Match with player "champion123" → Tournament preset
- Match where player submitted settings_difficulty="hard" → Hard preset
- Match with regular players → Normal preset

---

## Troubleshooting

### Issue: UI doesn't load / blank page
**Solution**: 
1. Check browser console for JavaScript errors
2. Check server logs for Python errors
3. Verify tournament has randomizer configured
4. Verify database migration applied successfully

### Issue: Rules don't save
**Solution**:
1. Check if database migration applied: `poetry run aerich history`
2. Check server logs for save errors
3. Verify tournament_id is correct
4. Try manually checking database: `SELECT preset_selection_rules FROM tournament WHERE id=X`

### Issue: Wrong preset selected
**Solution**:
1. Add logging to `select_preset_for_match()` to see evaluation
2. Check rule order (first match wins)
3. Verify match context has expected field values
4. Check operator logic (eq vs contains, etc.)

### Issue: Presets dropdown is empty
**Solution**:
1. Verify tournament has `randomizer` field set (alttpr, sm, smz3, etc.)
2. Check that presets exist for that randomizer
3. Check user has permission to view presets
4. Add logging to `_load_presets()` method

---

## Success Criteria

✅ **Database Migration Applied**: Column exists in database  
✅ **UI Loads**: View appears in tournament admin sidebar  
✅ **Rules CRUD Works**: Can add, view, delete, and save rules  
✅ **Validation Works**: Invalid rules are rejected with clear errors  
✅ **Persistence Works**: Rules saved to database and reload correctly  
✅ **Preset Selection Works**: Correct preset selected based on match context  
✅ **Fallback Works**: Fallback preset used when no rules match  
✅ **Logging Works**: Rule evaluation decisions logged for debugging  

---

## Documentation

All documentation complete:

1. ✅ **Design Spec**: `docs/features/PRESET_SELECTION_RULES.md` (440+ lines)
2. ✅ **Integration Examples**: `docs/features/PRESET_SELECTION_INTEGRATION_EXAMPLE.md`
3. ✅ **Implementation Summary**: `docs/features/PRESET_SELECTION_IMPLEMENTATION_SUMMARY.md`
4. ✅ **UI Integration Summary**: `PRESET_SELECTION_UI_INTEGRATION.md`
5. ✅ **Next Steps Checklist**: `PRESET_SELECTION_NEXT_STEPS.md` (this file)

---

**Last Updated**: November 9, 2025  
**Current Status**: UI integration complete, migration created, ready to test
