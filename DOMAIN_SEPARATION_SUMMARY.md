# Domain Separation Summary

**Date**: November 10, 2025  
**PR**: Separate Tournament and Async Qualifier Domains

## Overview

This document summarizes the domain separation work completed to cleanly separate tournament and async qualifier code in the SahaBot2 codebase. Previously, these two distinct domains were intermixed in shared directories and files, making the codebase harder to navigate and maintain.

## Changes Made

### 1. Directory Structure Reorganization

#### Created New Directories
- `views/async_qualifiers/` - Async qualifier public views
- `components/dialogs/async_qualifiers/` - Async qualifier dialogs
- `application/services/async_qualifiers/` - Async qualifier services

#### Moved Files

**Views** (`views/tournaments/` → `views/async_qualifiers/`):
- `async_qualifier_dashboard.py` - Player dashboard view
- `async_qualifier_leaderboard.py` - Leaderboard view
- `async_qualifier_live_races.py` - Live races view
- `async_qualifier_permalink.py` - Permalink view
- `async_qualifier_player_history.py` - Player history view
- `async_qualifier_pools.py` - Pools view
- `async_qualifier_review_queue.py` - Review queue view

**Dialogs** (`components/dialogs/tournaments/` → `components/dialogs/async_qualifiers/`):
- `async_qualifier_dialog.py` - Main async qualifier dialog
- `create_live_race_dialog.py` - Live race creation dialog
- `permalink_dialog.py` - Permalink dialog
- `pool_dialog.py` - Pool management dialog
- `race_reattempt_dialog.py` - Race reattempt dialog
- `race_review_dialog.py` - Race review dialog

**Services** (`application/services/tournaments/` → `application/services/async_qualifiers/`):
- `async_qualifier_service.py` - Main async qualifier service
- `async_live_race_service.py` - Live race service

### 2. Page Route Separation

**Created**: `pages/async_qualifiers.py`
- Contains all async qualifier public routes
- Routes: `/org/{id}/async`, `/org/{id}/async/{id}/*`

**Updated**: `pages/tournaments.py`
- Removed all async qualifier routes
- Now only contains tournament routes
- Routes: `/org/{id}`, `/org/{id}/tournament`
- **Fixed bug**: Parameter name mismatch (qualifier_id → tournament_id)

### 3. Import Updates

Updated imports in **21+ files** across the codebase:
- API routes: `api/routes/async_live_races.py`, `api/routes/async_qualifiers.py`
- Pages: `pages/async_qualifier_admin.py`, `pages/tournaments.py`
- Views: All async qualifier views, organization views
- Services: Task handlers, event listeners
- Discord bot: Commands and views
- Dialogs: All async qualifier dialogs

Key import changes:
```python
# Before
from application.services.tournaments.async_qualifier_service import AsyncQualifierService
from views.tournaments import AsyncDashboardView
from components.dialogs.tournaments.pool_dialog import PoolDialog

# After
from application.services.async_qualifiers.async_qualifier_service import AsyncQualifierService
from views.async_qualifiers import AsyncDashboardView
from components.dialogs.async_qualifiers.pool_dialog import PoolDialog
```

### 4. __init__.py Updates

Updated package exports in:
- `views/tournaments/__init__.py` - Removed async qualifier exports
- `views/async_qualifiers/__init__.py` - New file with async qualifier exports
- `components/dialogs/tournaments/__init__.py` - Removed async qualifier dialogs
- `components/dialogs/async_qualifiers/__init__.py` - New file with async qualifier dialogs
- `application/services/tournaments/__init__.py` - Removed async qualifier services
- `application/services/async_qualifiers/__init__.py` - New file with async qualifier services
- `components/dialogs/__init__.py` - Added async qualifier section
- `pages/__init__.py` - Added async_qualifiers import

### 5. Frontend Registration

**Updated**: `frontend.py`
- Fixed bug: `async_tournament_admin` → `async_qualifier_admin`
- Added import and registration for `async_qualifiers` page

### 6. Documentation Updates

**Updated**: `docs/ROUTE_HIERARCHY.md`
- Corrected file references for all async qualifier routes
- Removed duplicate async qualifier admin section
- Updated route table to show `pages/async_qualifiers.py` as source
- Removed `/org/{id}/async` from organization routes (now in separate section)

### 7. Code Cleanup

**Removed**:
- `views/organization/org_async_tournaments.py` - Orphaned dead code
- `pages/tournaments.py.backup` - Temporary backup file

### 8. Code Quality

- Applied `black` formatting to all changed files
- Verified Python syntax on all files
- Ran `ruff` linting (1 minor lambda warning remains - idiomatic for NiceGUI)

## Final Directory Structure

```
views/
├── async_qualifiers/          # ✅ Async qualifier views (NEW)
│   ├── async_qualifier_dashboard.py
│   ├── async_qualifier_leaderboard.py
│   ├── async_qualifier_live_races.py
│   ├── async_qualifier_permalink.py
│   ├── async_qualifier_player_history.py
│   ├── async_qualifier_pools.py
│   └── async_qualifier_review_queue.py
├── tournaments/               # ✅ Tournament-only views
│   ├── event_schedule.py
│   ├── my_matches.py
│   ├── my_settings.py
│   ├── tournament_management.py
│   └── tournament_org_select.py
└── tournament_admin/          # ✅ Tournament admin views
    ├── tournament_overview.py
    ├── tournament_players.py
    ├── tournament_settings.py
    └── ...

components/dialogs/
├── async_qualifiers/          # ✅ Async qualifier dialogs (NEW)
│   ├── async_qualifier_dialog.py
│   ├── create_live_race_dialog.py
│   ├── permalink_dialog.py
│   ├── pool_dialog.py
│   ├── race_reattempt_dialog.py
│   └── race_review_dialog.py
└── tournaments/               # ✅ Tournament-only dialogs
    ├── create_match_dialog.py
    ├── edit_match_dialog.py
    ├── match_seed_dialog.py
    └── ...

application/services/
├── async_qualifiers/          # ✅ Async qualifier services (NEW)
│   ├── async_qualifier_service.py
│   └── async_live_race_service.py
└── tournaments/               # ✅ Tournament-only services
    ├── tournament_service.py
    ├── tournament_usage_service.py
    ├── stream_channel_service.py
    └── ...

pages/
├── async_qualifiers.py        # ✅ Async qualifier routes (NEW)
├── async_qualifier_admin.py   # ✅ Async qualifier admin
├── tournaments.py             # ✅ Tournament routes only
└── tournament_admin.py        # ✅ Tournament admin
```

## Already Properly Separated

These areas were already cleanly separated and required no changes:

- **API Routes**: `api/routes/tournaments.py` vs `api/routes/async_qualifiers.py`
- **API Schemas**: `api/schemas/tournament.py` vs `api/schemas/async_qualifier.py`
- **Repositories**: `tournament_repository.py` vs `async_qualifier_repository.py`
- **Models**: Tournament models in separate files from async qualifier models
- **Discord Bot**: Commands properly organized in `discordbot/commands/`

## Domain Boundaries

### Tournament Domain
- **Purpose**: Traditional bracket-style tournaments with scheduled matches
- **Key Features**: Match scheduling, player registration, bracket management
- **Routes**: `/org/{id}/tournament`, `/org/{id}/tournament/{id}/admin`
- **Files**: All `tournament_*` files

### Async Qualifier Domain
- **Purpose**: Asynchronous race qualifiers where players race at their own pace
- **Key Features**: Pools, permalinks, race review, leaderboards
- **Routes**: `/org/{id}/async`, `/org/{id}/async/{id}/*`
- **Files**: All `async_qualifier_*` files

## Benefits

1. **Improved Code Organization**: Clear separation makes it easier to find domain-specific code
2. **Better Maintainability**: Changes to one domain don't affect the other
3. **Clearer Architecture**: Domain boundaries are explicit in the file structure
4. **Easier Onboarding**: New developers can quickly understand the codebase structure
5. **Reduced Coupling**: Each domain can evolve independently
6. **Better Testing**: Domain-specific tests can be organized separately

## Verification Checklist

- [x] All async qualifier files moved to new directories
- [x] All tournament files remain in tournament directories
- [x] No async qualifier code in tournament directories
- [x] No tournament code in async qualifier directories
- [x] All imports updated across the codebase
- [x] __init__.py files updated
- [x] Frontend registration updated
- [x] Documentation updated
- [x] Orphaned files removed
- [x] Code formatted with black
- [x] Python syntax verified
- [x] Linting passed (with 1 acceptable warning)

## Future Considerations

1. **Test Organization**: As test coverage grows, consider organizing tests by domain
2. **Model File Naming**: `models/async_tournament.py` could be renamed to `async_qualifier.py` for consistency (contains AsyncQualifier model)
3. **Documentation**: Archive documentation uses old "async tournament" terminology - could be updated for consistency

## Related Documentation

- `docs/ROUTE_HIERARCHY.md` - Complete route documentation
- `docs/ARCHITECTURE.md` - System architecture
- `docs/PATTERNS.md` - Code patterns and conventions
