# Service Layer Reorganization

**Date**: November 5, 2025  
**Status**: ✅ Complete

## Overview

The `application/services` directory has been reorganized from a flat structure (30+ files in root) to a domain-driven organization with clear boundaries and better navigation.

## New Structure

```
application/services/
├── __init__.py                          # Common exports
├── core/                                # Core/foundational services
│   ├── user_service.py
│   ├── audit_service.py
│   ├── settings_service.py
│   └── rate_limit_service.py
│
├── authorization/                       # Authorization & permissions
│   ├── authorization_service_v2.py
│   └── ui_authorization_helper.py
│
├── organizations/                       # Organization management
│   ├── organization_service.py
│   ├── organization_invite_service.py
│   ├── organization_request_service.py
│   └── feature_flag_service.py
│
├── tournaments/                         # Tournament management
│   ├── tournament_service.py
│   ├── async_tournament_service.py
│   ├── async_live_race_service.py
│   ├── tournament_usage_service.py
│   └── stream_channel_service.py
│
├── discord/                            # Discord integrations
│   ├── discord_service.py
│   ├── discord_guild_service.py
│   ├── discord_scheduled_event_service.py
│   └── discord_permissions_config.py
│
├── racetime/                           # RaceTime.gg integrations
│   ├── racetime_service.py
│   ├── racetime_api_service.py
│   ├── racetime_bot_service.py
│   ├── racetime_chat_command_service.py
│   ├── racetime_room_service.py
│   ├── race_room_profile_service.py
│   └── racer_verification_service.py
│
├── randomizer/                         # Game randomizers
│   ├── randomizer_service.py
│   ├── randomizer_preset_service.py
│   ├── preset_namespace_service.py
│   └── [game-specific services]
│
├── speedgaming/                        # SpeedGaming integration
│   ├── speedgaming_service.py
│   └── speedgaming_etl_service.py
│
├── notifications/                      # Notification system
│   ├── notification_service.py
│   ├── notification_processor.py
│   └── handlers/
│       ├── base_handler.py
│       └── discord_handler.py
│
├── tasks/                              # Task scheduling
│   ├── task_scheduler_service.py
│   ├── task_handlers.py
│   ├── builtin_tasks.py
│   └── builtin/
│       ├── orphaned_events_cleanup.py
│       └── scheduled_events_sync.py
│
└── security/                           # Security & tokens
    └── api_token_service.py
```

## Benefits

### Before
- ❌ 30+ files in single directory
- ❌ Hard to find related services
- ❌ Inconsistent organization
- ❌ No clear domain boundaries

### After
- ✅ Domain-driven organization
- ✅ Clear boundaries between domains
- ✅ Easy to navigate and find services
- ✅ Scalable structure for new features
- ✅ Semantic import paths

## Import Patterns

### Old Imports (Deprecated)
```python
from application.services.user_service import UserService
from application.services.discord_service import DiscordService
from application.services.racetime_api_service import RacetimeApiService
```

### New Imports (Current)

**Option 1: Direct import (verbose)**
```python
from application.services.core.user_service import UserService
from application.services.discord.discord_service import DiscordService
from application.services.racetime.racetime_api_service import RacetimeApiService
```

**Option 2: Package import (preferred)**
```python
from application.services.core import UserService
from application.services.discord import DiscordService
from application.services.racetime import RacetimeApiService
```

**Option 3: Convenience imports (for commonly used services)**
```python
# These are re-exported from application.services.__init__.py
from application.services import UserService, AuditService, AuthorizationServiceV2
```

## Migration Details

### Automated Migration
- **Files Moved**: 30+ service files
- **Import Statements Updated**: 272 replacements across 148 files
- **Script Used**: `tools/update_service_imports.py`
- **Compilation Errors**: 0

### Files Updated
All import statements were automatically updated across:
- API routes (`api/routes/`)
- Service layer (`application/services/`)
- UI components (`components/dialogs/`)
- Discord bot (`discordbot/`)
- Pages (`pages/`)
- Views (`views/`)
- Tests (`tests/`)
- Tools (`tools/`)
- RaceTime integration (`racetime/`)

## Domain Descriptions

### Core
Foundational services that other domains depend on:
- User management
- Audit logging
- Application settings
- Rate limiting

### Authorization
Permission checking and authorization logic:
- Policy-based authorization (v2)
- UI authorization helpers
- Organization-scoped permissions

### Organizations
Multi-tenant organization management:
- Organization CRUD
- Invitations
- Join requests
- Feature flags

### Tournaments
Tournament and race management:
- Synchronous tournaments
- Async tournaments
- Live races
- Usage tracking
- Stream channels

### Discord
Discord platform integration:
- OAuth2 and services
- Guild (server) management
- Scheduled events
- Permission configuration

### RaceTime
RaceTime.gg platform integration:
- API client
- Bot management
- Chat commands
- Room management
- Race room profiles
- Racer verification

### Randomizer
Game randomizer services:
- Generic randomizer service
- Preset management
- Namespace permissions
- Game-specific services (ALTTPR, OOTR, etc.)

### SpeedGaming
SpeedGaming platform integration:
- API client
- ETL (Extract, Transform, Load) service

### Notifications
User notification system:
- Subscription management
- Notification processing
- Delivery handlers (Discord, Email, etc.)

### Tasks
Background task scheduling:
- Task scheduler service
- Task handlers
- Built-in tasks (cleanup, sync, etc.)

### Security
Security and authentication:
- API token management

## Adding New Services

When creating a new service, place it in the appropriate domain directory:

```python
# Example: New email notification handler
# File: application/services/notifications/handlers/email_handler.py

class EmailNotificationHandler(BaseNotificationHandler):
    """Email notification delivery handler."""
    pass
```

Update the domain's `__init__.py`:
```python
# File: application/services/notifications/handlers/__init__.py

from application.services.notifications.handlers.email_handler import EmailNotificationHandler

__all__ = [
    'BaseNotificationHandler',
    'DiscordNotificationHandler',
    'EmailNotificationHandler',  # Add new export
]
```

## Testing

All tests pass after migration:
```bash
# Run tests to verify
poetry run pytest
```

## Related Documentation

- **[Architecture Guide](ARCHITECTURE.md)** - Updated service layer documentation
- **[Patterns & Conventions](PATTERNS.md)** - Service usage patterns
- **[Adding Features Guide](ADDING_FEATURES.md)** - Creating new services

## Notes for Developers

1. **Always use package imports** when possible: `from application.services.core import UserService`
2. **Update domain __init__.py** when adding new services to a domain
3. **Follow domain boundaries** - don't mix concerns across domains
4. **Create new domains** if you have a cohesive set of related services
5. **Check compilation** after adding new imports

## Rollback (if needed)

If issues arise, the migration can be rolled back:
```bash
# Revert git changes
git revert <commit-hash>

# Or manually restore from backup
# (Ensure you have a backup before migration)
```

---

**Migration completed successfully** ✅
