# Test Fixing Plan

## Progress Status

**Phase 1: COMPLETED ✅** (November 5, 2025)
- Fixed 26 mock import paths across 6 test files
- Created automated `tools/fix_test_imports.py` script
- Result: **160 tests passing** (+5), **42 tests failing** (-5)
- Pass rate improved from 51.5% → 53.2%

**Phase 2: IN PROGRESS 🔄** (November 5, 2025)
- Added `sample_organization` fixture to `tests/conftest.py`
- Fixed all 11 tests in `test_repositories_scheduled_task.py`
- Added `sample_discord_guild` fixture to `tests/conftest.py` (depends on sample_user + sample_organization)
- Fixed all 7 tests in `test_orphaned_event_cleanup.py` (removed local fixtures, use shared conftest.py fixtures)
- Result: **177 tests passing** (+17 total), **32 tests failing** (unchanged)
- Pass rate improved from 53.2% → 58.8% (+5.6% this session)

**Current Status** (as of November 5, 2025 - Phase 2 Priority 1 Partial):
- ✅ **301 tests collected** (0 import errors - circular dependencies fixed!)
- ✅ **177 tests passing** (58.8% pass rate) - UP from 170 / 160 / 155 (Original)
- ❌ **32 tests failing** (10.6%) - STABLE (was 42 before Phase 2)
- ❌ **92 errors** (30.5%) - DOWN from 99 (7 errors resolved!)
- **Next**: Continue Phase 2 Priority 1 - Fix remaining DiscordGuild fixture errors (~8 more tests)

**Original Status** (before Phase 1):
- ✅ **155 tests passing** (51.5% pass rate)
- ❌ **47 tests failing** (15.6%)
- ❌ **99 errors** (32.9%)

## Overview

After the service layer reorganization, we have **32 failing tests** and **92 errors** remaining. This document provides a comprehensive plan to fix all test issues systematically.

## Root Causes Analysis

### 1. Mock Path Issues (Service Reorganization)
**Impact**: ~20 tests  
**Cause**: Tests mock old service paths that moved during reorganization

**Examples**:
```python
# ❌ Old path (no longer valid)
@patch('racetime.client.RacetimeRoomService')

# ❌ Old notification handler path
@patch('application.services.notification_handlers.discord_handler.get_bot_instance')

# ❌ Old service paths
@patch('application.services.tournament_service.Match')
@patch('application.services.discord_scheduled_event_service.get_bot_instance')
```

**Files Affected**:
- `tests/test_auto_accept_join_requests.py` - 4 tests
- `tests/test_notification_handlers.py` - 2 tests
- `tests/test_racetime_room_invites.py` - 2 tests
- `tests/test_racetime_status_events.py` - Multiple tests
- `tests/integration/test_discord_scheduled_event_listeners.py` - 5 tests
- `tests/unit/test_orphaned_event_cleanup.py` - 1 test

### 2. Database/Fixture Setup Issues
**Impact**: ~99 errors  
**Cause**: Test fixtures not properly initializing async database connections

**Symptoms**:
```
RuntimeWarning: coroutine '_wrap_asyncgen_fixture.<locals>._asyncgen_fixture_wrapper.<locals>.setup' was never awaited
```

**Files Affected**:
- Most integration tests
- Tests requiring database access

### 3. Missing/Incorrect Test Dependencies
**Impact**: Variable  
**Cause**: Tests may have been written against old code patterns

**Examples**:
- Tests expecting synchronous methods that are now async
- Tests expecting different method signatures
- Tests with outdated assertions

## Fixing Strategy

### Phase 1: Fix Mock Import Paths (Priority: HIGH)
**Estimated Time**: 2-3 hours  
**Complexity**: Low  
**Impact**: Will fix ~20 tests immediately

#### Steps:

1. **Update RacetimeRoomService Mocks**
   ```python
   # Before:
   @patch('racetime.client.RacetimeRoomService')
   
   # After:
   @patch('application.services.racetime.racetime_room_service.RacetimeRoomService')
   ```
   
   **Files to fix**:
   - `tests/test_auto_accept_join_requests.py` (4 occurrences)

2. **Update Notification Handler Mocks**
   ```python
   # Before:
   @patch('application.services.notification_handlers.discord_handler.get_bot_instance')
   
   # After:
   @patch('application.services.notifications.handlers.discord_handler.get_bot_instance')
   ```
   
   **Files to fix**:
   - `tests/test_notification_handlers.py` (2 occurrences)

3. **Update Discord Event Service Mocks**
   ```python
   # Before:
   @patch('application.services.discord_scheduled_event_service.get_bot_instance')
   
   # After:
   @patch('application.services.discord.discord_scheduled_event_service.get_bot_instance')
   ```
   
   **Files to fix**:
   - `tests/integration/test_discord_scheduled_event_listeners.py` (5 occurrences)
   - `tests/unit/test_orphaned_event_cleanup.py` (1 occurrence)

4. **Update Tournament Service Mocks**
   ```python
   # Before:
   @patch('application.services.tournament_service.Match')
   
   # After:
   @patch('application.services.tournaments.tournament_service.Match')
   ```
   
   **Files to fix**:
   - `tests/test_racetime_room_invites.py` (multiple occurrences)

5. **Update UserRepository Mocks**
   ```python
   # Before:
   @patch('racetime.client.UserRepository')
   
   # After:
   @patch('application.repositories.user_repository.UserRepository')
   ```
   
   **Files to fix**:
   - `tests/test_racetime_status_events.py` (2 occurrences)

#### Automation Script

Create `tools/fix_test_imports.py`:
```python
#!/usr/bin/env python3
"""Fix test import paths after service reorganization."""

import re
from pathlib import Path

# Map old mock paths to new paths
MOCK_PATH_MAPPINGS = {
    # RaceTime services
    r"@patch\('racetime\.client\.RacetimeRoomService'\)": 
        r"@patch('application.services.racetime.racetime_room_service.RacetimeRoomService')",
    
    r"patch\('racetime\.client\.UserRepository'\)":
        r"patch('application.repositories.user_repository.UserRepository')",
    
    # Notification handlers
    r"patch\('application\.services\.notification_handlers\.discord_handler\.get_bot_instance'\)":
        r"patch('application.services.notifications.handlers.discord_handler.get_bot_instance')",
    
    # Discord services
    r"patch\('application\.services\.discord_scheduled_event_service\.get_bot_instance'\)":
        r"patch('application.services.discord.discord_scheduled_event_service.get_bot_instance')",
    
    # Tournament services
    r"patch\('application\.services\.tournament_service\.Match'\)":
        r"patch('application.services.tournaments.tournament_service.Match')",
    
    r"patch\('application\.services\.tournament_service\.RacetimeBot'\)":
        r"patch('application.services.tournaments.tournament_service.RacetimeBot')",
    
    r"patch\('application\.services\.tournament_service\.aiohttp\.ClientSession'\)":
        r"patch('application.services.tournaments.tournament_service.aiohttp.ClientSession')",
}

def fix_test_file(file_path: Path) -> int:
    """Fix mock paths in a test file."""
    content = file_path.read_text()
    replacements = 0
    
    for old_pattern, new_pattern in MOCK_PATH_MAPPINGS.items():
        new_content, count = re.subn(old_pattern, new_pattern, content)
        if count > 0:
            content = new_content
            replacements += count
            print(f"  {file_path.name}: Replaced {count} occurrences of pattern")
    
    if replacements > 0:
        file_path.write_text(content)
    
    return replacements

def main():
    """Fix all test files."""
    tests_dir = Path(__file__).parent.parent / "tests"
    total_replacements = 0
    files_updated = 0
    
    for test_file in tests_dir.rglob("test_*.py"):
        replacements = fix_test_file(test_file)
        if replacements > 0:
            files_updated += 1
            total_replacements += replacements
    
    print(f"\nFixed {total_replacements} mock paths in {files_updated} files")

if __name__ == "__main__":
    main()
```

### Phase 2: Fix Database Fixture Issues (Priority: MEDIUM)
**Estimated Time**: 4-6 hours  
**Complexity**: Medium  
**Impact**: Will fix ~99 error cases

#### Issues to Address:

1. **Async Fixture Warnings**
   - Ensure all async fixtures use `@pytest_asyncio.fixture` instead of `@pytest.fixture`
   - Verify fixture scopes are appropriate (function, module, session)

2. **Database Connection Issues**
   - Check `conftest.py` database initialization
   - Ensure Tortoise ORM is properly initialized before tests
   - Verify database cleanup happens after tests

3. **Fixture Dependencies**
   - Review fixture dependency chains
   - Ensure fixtures are awaited correctly
   - Check for missing `await` keywords

#### Files to Review:
- `tests/conftest.py` - Main fixture configuration
- `tests/integration/conftest.py` - Integration test fixtures
- `tests/unit/conftest.py` - Unit test fixtures (if exists)

### Phase 3: Fix Individual Test Logic (Priority: LOW)
**Estimated Time**: 6-8 hours  
**Complexity**: High  
**Impact**: Will fix remaining failing tests

#### Categories:

1. **Repository Tests** (10 tests in `test_repositories_scheduled_task.py`)
   - May need database schema updates
   - Check for migration issues

2. **Security Middleware Tests** (5 tests in `test_security_middleware.py`)
   - Verify middleware configuration
   - Check test environment setup

3. **Service Tests** (Various)
   - Update to match current service implementations
   - Fix any breaking API changes

## Test Categories Breakdown

### By Status:

| Status | Count | Percentage |
|--------|-------|------------|
| Passing | 155 | 51.5% |
| Failing | 47 | 15.6% |
| Errors | 99 | 32.9% |
| **Total** | **301** | **100%** |

### By Type:

| Type | Count | Pass Rate |
|------|-------|-----------|
| Unit Tests | ~200 | ~60% |
| Integration Tests | ~80 | ~30% |
| End-to-End Tests | ~21 | ~40% |

### By Domain:

| Domain | Tests | Status |
|--------|-------|--------|
| RaceTime Integration | 30+ | ⚠️ Many failing (mock path issues) |
| Notifications | 10+ | ⚠️ Mock path issues |
| Discord Services | 20+ | ⚠️ Mock path issues |
| Repositories | 15+ | ❌ Database fixture issues |
| Security | 5+ | ❌ Unknown |
| Authorization | 5+ | ✅ Mostly passing |
| Other | 216+ | ✅ Mostly passing |

## Implementation Plan

### Week 1: Mock Path Fixes
- [ ] Day 1: Create and run `fix_test_imports.py` script
- [ ] Day 2: Manually verify and fix any edge cases
- [ ] Day 3: Run tests, verify ~20 tests now pass
- [ ] Day 4: Document patterns for future test writing
- [ ] Day 5: Review and commit changes

**Expected Outcome**: 175+ passing tests (58%+ pass rate)

### Week 2: Database Fixture Fixes
- [ ] Day 1-2: Review and fix `conftest.py` fixtures
- [ ] Day 3: Fix async fixture warnings
- [ ] Day 4: Test database initialization/cleanup
- [ ] Day 5: Run full test suite, verify error count drops

**Expected Outcome**: 250+ passing tests (83%+ pass rate)

### Week 3: Individual Test Logic
- [ ] Day 1-2: Fix repository tests
- [ ] Day 3: Fix security middleware tests
- [ ] Day 4: Fix remaining service tests
- [ ] Day 5: Final verification and documentation

**Expected Outcome**: 280+ passing tests (93%+ pass rate)

## Success Criteria

### Phase 1 Complete:
- ✅ All mock path errors resolved
- ✅ At least 175 tests passing (58%+ pass rate)
- ✅ Automated script for future mock path updates

### Phase 2 Complete:
- ✅ All database fixture errors resolved
- ✅ At least 250 tests passing (83%+ pass rate)
- ✅ Clean pytest output (no warnings)

### Phase 3 Complete:
- ✅ At least 280 tests passing (93%+ pass rate)
- ✅ All critical path tests passing
- ✅ Documentation updated

### Final Goal:
- 🎯 **290+ tests passing (96%+ pass rate)**
- 🎯 **Zero fixture errors**
- 🎯 **Comprehensive test documentation**

## Quick Start

To begin fixing tests immediately:

```bash
# 1. Create the import fixing script
cd /path/to/sahabot2
# Create tools/fix_test_imports.py (content above)

# 2. Run the script
poetry run python tools/fix_test_imports.py

# 3. Verify changes
git diff tests/

# 4. Run tests to see improvements
poetry run pytest -v --tb=short

# 5. Commit if successful
git add tests/
git commit -m "Fix test mock import paths after service reorganization"
```

## Maintenance

### For Future Service Reorganizations:
1. Update `tools/fix_test_imports.py` with new mappings
2. Run script before testing
3. Manually verify edge cases

### Test Writing Guidelines:
1. Always use full import paths in mocks
2. Import services from their domain packages:
   ```python
   from application.services.racetime.racetime_service import RacetimeService
   ```
3. Document mock paths in test docstrings
4. Use fixtures for common mocks

## Resources

- **Pytest Async Guide**: https://pytest-asyncio.readthedocs.io/
- **Tortoise ORM Testing**: https://tortoise.github.io/testing.html
- **Python Mock Documentation**: https://docs.python.org/3/library/unittest.mock.html

## Notes

- Some tests may be testing deprecated functionality
- Consider removing tests for removed features
- May want to add new tests for reorganized services
- Test coverage should be measured after fixes

---

**Last Updated**: November 5, 2025  
**Status**: Planning Phase  
**Next Action**: Create `tools/fix_test_imports.py` and run Phase 1
