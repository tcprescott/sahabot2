# Async Qualifier Rename Plan

## Overview

This document outlines the comprehensive plan to rename "Async Tournament" features to "Async Qualifier" throughout the SahaBot2 codebase. The intent is to reduce confusion between "Tournament" (traditional competitive brackets/matches) and "Async Qualifier" (self-paced race events where players complete runs asynchronously).

**Status**: Planning Phase  
**Scope**: Complete system-wide rename  
**Data Loss Risk**: None (no production data exists)  
**Migration Strategy**: Full rewrite of migrations; rollback not needed for early-stage development

---

## Why This Rename?

### Problem
- Two distinct tournament types create naming confusion:
  - **Tournament**: Traditional bracket-based events with scheduled matches
  - **Async Tournament**: Self-paced qualifier events (currently confusing)

### Solution
- Rename "Async Tournament" → "Async Qualifier" for clarity
- Maintain "Tournament" for traditional competitive tournaments
- Reduces cognitive load and improves code clarity

---

## Scope Analysis

### Database Schema (Primary Impact)

**Tables to Rename** (6 tables):
1. `async_tournaments` → `async_qualifiers`
2. `async_tournament_pools` → `async_qualifier_pools`
3. `async_tournament_permalinks` → `async_qualifier_permalinks`
4. `async_tournament_races` → `async_qualifier_races`
5. `async_tournament_live_races` → `async_qualifier_live_races`
6. `async_tournament_audit_logs` → `async_qualifier_audit_logs`

**Foreign Key Constraints** (13 FKs):
- All tables referencing `async_tournaments` → `async_qualifiers`
- All tables referencing `async_tournament_*` → `async_qualifier_*`
- Updates required in:
  - `scheduled_tasks` table (references async tournaments for task types)
  - All internal foreign key references

### Python Models (6 files)

**File**: `models/async_tournament.py`
- **Classes to Rename**:
  - `AsyncTournament` → `AsyncQualifier`
  - `AsyncTournamentPool` → `AsyncQualifierPool`
  - `AsyncTournamentPermalink` → `AsyncQualifierPermalink`
  - `AsyncTournamentRace` → `AsyncQualifierRace`
  - `AsyncTournamentLiveRace` → `AsyncQualifierLiveRace`
  - `AsyncTournamentAuditLog` → `AsyncQualifierAuditLog`
  
- **Other Changes**:
  - Table names in `Meta` classes (match DB schema)
  - Related names in ForeignKey fields
  - `related_name` attributes for reverse relations
  - Documentation strings

**Estimated Lines**: ~400-500 lines total

### Repository Layer (1 major file)

**File**: `application/repositories/async_tournament_repository.py`
- **Rename to**: `application/repositories/async_qualifier_repository.py`
- **Changes**:
  - Class name: `AsyncTournamentRepository` → `AsyncQualifierRepository`
  - Import statements (model imports)
  - All type hints and method return types
  - Docstrings and method documentation
  - Internal model references
  - Logger names

**Estimated Changes**: ~50+ references throughout the class

### Service Layer (1 major file)

**File**: `application/services/tournaments/async_tournament_service.py`
- **Rename to**: `application/services/tournaments/async_qualifier_service.py`
- **Changes**:
  - Class name: `AsyncTournamentService` → `AsyncQualifierService`
  - Import statements (models, repository)
  - All method type hints and return types
  - Method names: `can_manage_async_tournaments()` → `can_manage_async_qualifiers()`
  - Internal event emission references
  - Logger output and method documentation
  - Repository instantiation

**Estimated Changes**: ~100+ references throughout the service

### API Layer (3 files)

**File**: `api/routes/async_tournaments.py`
- **Rename to**: `api/routes/async_qualifiers.py`
- **Changes**:
  - Endpoint prefixes: `/async-tournaments/` → `/async-qualifiers/`
  - Route function names
  - Service instantiation
  - Import statements
  - Response schema references
  - Documentation and docstrings

**File**: `api/schemas/async_tournament.py`
- **Rename to**: `api/schemas/async_qualifier.py`
- **Changes**:
  - All class names: `AsyncTournament*` → `AsyncQualifier*`
  - Field descriptions
  - Documentation strings
  - Import references in other files

**File**: `api/routes/async_live_races.py`
- **Partial changes**:
  - Update service references
  - Update model imports
  - Update endpoint documentation

### UI/Dialog Components (5 files)

**Components Directory**: `components/dialogs/tournaments/`

1. **File**: `async_tournament_dialog.py` → `async_qualifier_dialog.py`
   - Class: `AsyncTournamentDialog` → `AsyncQualifierDialog`
   - Import statements
   - UI labels and placeholder text
   - Method references

2. **File**: `race_reattempt_dialog.py` (PARTIAL)
   - Update imports only
   - Reference to AsyncQualifierService
   - Model imports

3. **File**: `__init__.py`
   - Update export statements

### UI/View Components (8 files)

**Views Directory**: `views/tournaments/` and `views/organization/`

1. **File**: `async_player_history.py` → `async_qualifier_player_history.py`
   - Class name changes
   - Import statements
   - Method references

2. **File**: `async_review_queue.py` → `async_qualifier_review_queue.py`
   - Class name changes
   - Service references

3. **File**: `async_dashboard.py` → `async_qualifier_dashboard.py`
   - Class name changes

4. **File**: `async_leaderboard.py` → `async_qualifier_leaderboard.py`
   - Class name changes

5. **File**: `async_pools.py` → `async_qualifier_pools.py`
   - Class name changes

6. **File**: `async_permalink.py` → `async_qualifier_permalink.py`
   - Class name changes

7. **File**: `async_live_races.py` → `async_qualifier_live_races.py`
   - Class name changes

8. **File**: `views/organization/org_async_tournaments.py` → `org_async_qualifiers.py`
   - Class name changes

### Page Handlers (3 files)

1. **File**: `pages/async_tournament_admin.py` → `pages/async_qualifier_admin.py`
   - Route decorators: `/async-tournament-admin` → `/async-qualifier-admin`
   - Function names
   - Service references
   - Navigation links

2. **File**: `pages/tournaments.py` (PARTIAL)
   - Multiple async tournament routes → async qualifier routes
   - Service references (~15-20 references)
   - Function names (~8 page functions)

3. **File**: `pages/__init__.py`
   - Import updates
   - Page registration

### Discord Bot Integration (2 files)

1. **File**: `discordbot/async_tournament_views.py` → `async_qualifier_views.py`
   - Class names
   - Model references
   - Service references

2. **File**: `discordbot/client.py` (PARTIAL)
   - Import statements only

### Database Migrations (1 new migration file)

**Action**: Create new comprehensive migration (NOT modify existing)
- Drop existing async_tournament_* tables
- Create new async_qualifier_* tables with same schema
- Update any references in other tables (e.g., scheduled_tasks)

**File**: `migrations/models/56_20251110000000_rename_async_tournaments_to_qualifiers.py`
- Upgrade: Create new tables and schema
- Downgrade: Drop new tables (rollback not needed)

### Configuration and References (5 files)

1. **File**: `api/auto_register.py`
   - Update route auto-registration
   - Import statement updates

2. **File**: `models/__init__.py`
   - Export statements

3. **File**: `application/repositories/__init__.py`
   - Repository exports

4. **File**: `application/services/tournaments/__init__.py`
   - Service exports

5. **File**: `views/__init__.py` and subdirectories
   - View exports

### Documentation (3 files)

1. **File**: `docs/ARCHITECTURE.md`
   - Update references to async tournaments
   - Update component descriptions

2. **File**: `RACE_REATTEMPT_IMPLEMENTATION.md`
   - Update all references
   - Update file paths and class names

3. **File**: Create new documentation if needed

---

## Detailed Implementation Plan

### Phase 1: Database & Models (Day 1)

**Steps**:
1. Create new migration file `56_*_rename_async_tournaments_to_qualifiers.py`
   - SQL to drop old tables
   - SQL to create new tables with correct schema
2. Update `models/async_tournament.py`:
   - Rename all classes
   - Update table names in Meta classes
   - Update related_name attributes
   - Update all docstrings
3. Apply migration: `poetry run aerich upgrade`
4. Verify schema in database

**Effort**: 2-3 hours

### Phase 2: Repository Layer (Day 1)

**Steps**:
1. Rename file: `async_tournament_repository.py` → `async_qualifier_repository.py`
2. Update class name and all references
3. Update imports in the file
4. Update `application/repositories/__init__.py` exports
5. Run type checking to catch broken references

**Effort**: 1-2 hours

### Phase 3: Service Layer (Day 1)

**Steps**:
1. Rename file: `async_tournament_service.py` → `async_qualifier_service.py`
2. Update class name: `AsyncTournamentService` → `AsyncQualifierService`
3. Update method names (e.g., `can_manage_async_tournaments()`)
4. Update all import statements
5. Update repository instantiation
6. Update event emission class names
7. Update logger messages (if needed)
8. Update `application/services/tournaments/__init__.py`

**Effort**: 2-3 hours

### Phase 4: API Layer (Day 2)

**Steps**:
1. Rename `api/routes/async_tournaments.py` → `api/routes/async_qualifiers.py`
2. Update all route prefixes
3. Update service instantiation
4. Update response schema names
5. Rename `api/schemas/async_tournament.py` → `api/schemas/async_qualifier.py`
6. Update all schema class names
7. Update `api/routes/async_live_races.py` service/model references
8. Update `api/auto_register.py` if needed
9. Test all endpoints

**Effort**: 2-3 hours

### Phase 5: UI Components - Dialogs (Day 2)

**Steps**:
1. Rename `components/dialogs/tournaments/async_tournament_dialog.py` → `async_qualifier_dialog.py`
2. Update class name and all references
3. Update model imports
4. Update `components/dialogs/tournaments/__init__.py`
5. Update `components/dialogs/__init__.py`

**Effort**: 1 hour

### Phase 6: UI Components - Views (Day 2-3)

**Steps**:
1. Rename all view files in `views/tournaments/`:
   - `async_player_history.py` → `async_qualifier_player_history.py`
   - `async_review_queue.py` → `async_qualifier_review_queue.py`
   - `async_dashboard.py` → `async_qualifier_dashboard.py`
   - `async_leaderboard.py` → `async_qualifier_leaderboard.py`
   - `async_pools.py` → `async_qualifier_pools.py`
   - `async_permalink.py` → `async_qualifier_permalink.py`
   - `async_live_races.py` → `async_qualifier_live_races.py`
2. Rename `views/organization/org_async_tournaments.py` → `org_async_qualifiers.py`
3. Update all class names in each file
4. Update service references
5. Update model imports
6. Update `views/tournaments/__init__.py` exports
7. Update `views/organization/__init__.py` exports

**Effort**: 3-4 hours

### Phase 7: Pages & Routes (Day 3)

**Steps**:
1. Rename `pages/async_tournament_admin.py` → `pages/async_qualifier_admin.py`
2. Update route decorators (change URL paths)
3. Update function names
4. Update service instantiation
5. Update `pages/__init__.py` imports and registration
6. Update `pages/tournaments.py`:
   - Rename page functions (8+ functions)
   - Update route decorators
   - Update service references
   - Update view references
   - Update navigation links

**Effort**: 2-3 hours

### Phase 8: Discord Bot Integration (Day 3)

**Steps**:
1. Rename `discordbot/async_tournament_views.py` → `async_qualifier_views.py`
2. Update all class names
3. Update model references
4. Update service references
5. Update `discordbot/client.py` imports

**Effort**: 1 hour

### Phase 9: Configuration & Exports (Day 3)

**Steps**:
1. Update all `__init__.py` files:
   - `models/__init__.py`
   - `application/repositories/__init__.py`
   - `application/services/tournaments/__init__.py`
   - `views/__init__.py` (all subdirectories)
   - `pages/__init__.py`
   - `components/dialogs/__init__.py`
   - `api/auto_register.py`
2. Verify all imports work
3. Run type checker to find missing imports

**Effort**: 1-2 hours

### Phase 10: Documentation & Testing (Day 4)

**Steps**:
1. Update `docs/ARCHITECTURE.md` references
2. Update `RACE_REATTEMPT_IMPLEMENTATION.md` with new file paths
3. Update any other documentation files
4. Comprehensive testing:
   - Run application server
   - Test all async qualifier pages
   - Test API endpoints
   - Test dialog functions
   - Test Discord bot commands
5. Verify no broken imports
6. Check for any missed references via grep

**Effort**: 2-3 hours

---

## Migration Strategy

### Why Not Modify Existing Migration 7?

The existing migration `7_20251101000000_add_async_tournament_models.py` contains:
- `MODELS_STATE` constant (required by Aerich)
- Auto-generated by Aerich (shouldn't be manually edited)

**Solution**: Create new migration that:
1. Drops old async_tournament_* tables
2. Creates new async_qualifier_* tables
3. Includes proper upgrade/downgrade

### Migration File Structure

```python
# migrations/models/56_20251110000000_rename_async_tournaments_to_qualifiers.py
from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True

async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `async_tournament_audit_logs`;
        DROP TABLE IF EXISTS `async_tournament_live_races`;
        DROP TABLE IF EXISTS `async_tournament_races`;
        DROP TABLE IF EXISTS `async_tournament_permalinks`;
        DROP TABLE IF EXISTS `async_tournament_pools`;
        DROP TABLE IF EXISTS `async_tournaments`;
        
        -- Create new tables with new names (same schema)
        CREATE TABLE IF NOT EXISTS `async_qualifiers` (
            ... (same schema as async_tournaments)
        );
        -- ... repeat for all other tables
    """

async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `async_qualifier_audit_logs`;
        DROP TABLE IF EXISTS `async_qualifier_live_races`;
        DROP TABLE IF EXISTS `async_qualifier_races`;
        DROP TABLE IF EXISTS `async_qualifier_permalinks`;
        DROP TABLE IF EXISTS `async_qualifier_pools`;
        DROP TABLE IF EXISTS `async_qualifiers`;
    """

MODELS_STATE = "..."  # Generated by Aerich after model changes
```

---

## Testing Checklist

### Unit Tests
- [ ] Repository methods work with new table names
- [ ] Service layer methods function correctly
- [ ] Schema matches new table definitions

### Integration Tests
- [ ] API endpoints respond correctly
- [ ] Database operations successful
- [ ] Foreign key constraints intact

### UI/Frontend Tests
- [ ] All pages load without errors
- [ ] Dialogs open and function
- [ ] Views render correctly
- [ ] Navigation links work

### API Tests
- [ ] All CRUD operations work
- [ ] Response schemas valid
- [ ] Endpoints properly registered

### Discord Bot Tests
- [ ] Bot commands work
- [ ] Modal views display correctly
- [ ] Data persists to database

---

## File Checklist

### Files to Rename (15 files)
- [ ] `models/async_tournament.py` (keep name, update contents)
- [ ] `application/repositories/async_tournament_repository.py` → `async_qualifier_repository.py`
- [ ] `application/services/tournaments/async_tournament_service.py` → `async_qualifier_service.py`
- [ ] `api/routes/async_tournaments.py` → `api/routes/async_qualifiers.py`
- [ ] `api/schemas/async_tournament.py` → `api/schemas/async_qualifier.py`
- [ ] `components/dialogs/tournaments/async_tournament_dialog.py` → `async_qualifier_dialog.py`
- [ ] `views/tournaments/async_player_history.py` → `async_qualifier_player_history.py`
- [ ] `views/tournaments/async_review_queue.py` → `async_qualifier_review_queue.py`
- [ ] `views/tournaments/async_dashboard.py` → `async_qualifier_dashboard.py`
- [ ] `views/tournaments/async_leaderboard.py` → `async_qualifier_leaderboard.py`
- [ ] `views/tournaments/async_pools.py` → `async_qualifier_pools.py`
- [ ] `views/tournaments/async_permalink.py` → `async_qualifier_permalink.py`
- [ ] `views/tournaments/async_live_races.py` → `async_qualifier_live_races.py`
- [ ] `views/organization/org_async_tournaments.py` → `org_async_qualifiers.py`
- [ ] `pages/async_tournament_admin.py` → `pages/async_qualifier_admin.py`
- [ ] `discordbot/async_tournament_views.py` → `async_qualifier_views.py`

### Files to Update (25+ files)
- [ ] `models/__init__.py`
- [ ] `application/repositories/__init__.py`
- [ ] `application/services/tournaments/__init__.py`
- [ ] `api/auto_register.py`
- [ ] `api/routes/async_live_races.py` (partial)
- [ ] `components/dialogs/tournaments/__init__.py`
- [ ] `components/dialogs/__init__.py`
- [ ] `components/dialogs/tournaments/race_reattempt_dialog.py` (partial)
- [ ] `views/__init__.py`
- [ ] `views/tournaments/__init__.py`
- [ ] `views/organization/__init__.py`
- [ ] `views/organization/org_overview.py` (partial)
- [ ] `pages/__init__.py`
- [ ] `pages/tournaments.py` (partial, 8+ page functions)
- [ ] `discordbot/client.py` (partial, imports only)
- [ ] `docs/ARCHITECTURE.md`
- [ ] `RACE_REATTEMPT_IMPLEMENTATION.md`
- [ ] ... (other documentation as needed)

### Database Migration
- [ ] Create `migrations/models/56_*_rename_async_tournaments_to_qualifiers.py`

---

## Estimated Effort

- **Total Time**: 4-5 days (assuming 8 hours/day)
- **Parallel Work**: Phases 1-3 can be compressed to 1-2 days
- **Testing**: 1 day
- **Buffer**: 0.5-1 day for unforeseen issues

**Breakdown**:
- Phase 1 (DB & Models): 2-3 hours
- Phase 2 (Repository): 1-2 hours
- Phase 3 (Service): 2-3 hours
- Phase 4 (API): 2-3 hours
- Phase 5 (Dialogs): 1 hour
- Phase 6 (Views): 3-4 hours
- Phase 7 (Pages): 2-3 hours
- Phase 8 (Discord Bot): 1 hour
- Phase 9 (Configuration): 1-2 hours
- Phase 10 (Documentation & Testing): 2-3 hours

---

## Risk Assessment

### Low Risk
- File renames (git tracks history)
- Class/method renames (type hints catch errors)
- DB table renames (no production data)

### Medium Risk
- Missed references in configuration
- Incomplete import updates
- Broken navigation links

### Mitigation
- Use IDE refactoring tools for bulk renaming
- Run type checker (`mypy` or similar) after changes
- Search for any remaining "async_tournament" references
- Test all pages and endpoints

---

## Alternative Approaches Considered

### Option 1: Use Aliases (NOT RECOMMENDED)
Keep old names, create aliases to new names. Leaves old names in code, creates confusion.

### Option 2: Gradual Migration (NOT RECOMMENDED)
Migrate in phases over time. Creates dual naming period, harder to maintain.

### Option 3: Full System Rename (RECOMMENDED) ✅
Complete rename across all layers at once. Ensures consistency, simpler to test, no ambiguity.

---

## Success Criteria

✅ All tests pass
✅ No broken imports
✅ All pages load without errors
✅ API endpoints function correctly
✅ Database schema correct
✅ No references to old table names in code
✅ Documentation updated
✅ Git history clean (files renamed, not deleted/recreated)

---

## Next Steps

1. Confirm this plan is acceptable
2. Review file list for completeness
3. Create task tickets for each phase
4. Begin Phase 1: Database & Models
5. Monitor progress and adjust timeline as needed

