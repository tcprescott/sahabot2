# SahasrahBot to SahaBot2 Data Migration Plan

## Overview

This document outlines the strategy and implementation plan for migrating data from the original SahasrahBot MySQL database to the new SahaBot2 database. The migration will preserve historical tournament data, user information, and other critical records while adapting them to SahaBot2's multi-tenant architecture.

**Status**: Planning Phase  
**Last Updated**: November 5, 2025  
**Migration Script**: `tools/data_migration.py` (to be created)

---

## Architecture Differences

### Original SahasrahBot
- **Single-tenant**: Global bot serving all Discord servers
- **No organizations**: Data scoped by Discord guild_id only
- **Flat user model**: Single `users` table with `discord_user_id`
- **Direct Discord associations**: Tournaments directly reference guild_id/channel_id
- **Permissions**: User-based and Discord role-based permissions per tournament

### SahaBot2
- **Multi-tenant**: Organization-based isolation
- **Organization model**: All data scoped to organizations
- **Enhanced user model**: Discord OAuth2 with permission levels
- **Organization membership**: Explicit user-to-organization relationships
- **Unified permissions**: Global + organization-scoped permissions

---

## Migration Strategy

### Phase 1: Core Infrastructure ✅
**Status**: Complete (already implemented in SahaBot2)

- [x] User model with Discord OAuth2
- [x] Organization model
- [x] Organization membership
- [x] Organization permissions
- [x] Audit logging system

### Phase 2: User Migration
**Status**: Planned

**Source Table**: `users` (SahasrahBot)  
**Target Tables**: `user`, `organization_member` (SahaBot2)

**Mapping**:
```
SahasrahBot users                  → SahaBot2 user
├── id                            → (new auto-increment, log mapping)
├── discord_user_id               → discord_id
├── twitch_name                   → (custom field or ignored)
├── rtgg_id (racetime_id)         → racetime_id
├── rtgg_access_token             → racetime_access_token
├── display_name                  → (stored in racetime_name or custom field)
├── test_user                     → (flag for migration testing)
├── created                       → created_at
└── updated                       → updated_at
```

**Challenges**:
- Need to map old user IDs to new user IDs for foreign key relationships
- RaceTime token refresh fields need to be added during migration
- Default permission level for migrated users (USER)

**Implementation Steps**:
1. Create user_id_mapping table (old_id → new_id)
2. Insert users into SahaBot2 with discord_id as unique key
3. Set racetime fields if present
4. Create default organization memberships (see Phase 3)
5. Log all user ID mappings for foreign key resolution

### Phase 3: Organization Creation from Discord Guilds
**Status**: Planned

**Source Data**: Distinct `guild_id` values from `asynctournament`, `racerverification`, `config`, etc.  
**Target Table**: `organization` (SahaBot2)

**Mapping Strategy**:
```
Discord Guild (from SahasrahBot data) → SahaBot2 Organization
├── guild_id                          → (store in discord_guild table)
├── guild name (from Discord API)     → name
├── description                       → "Migrated from SahasrahBot"
├── owner                            → (determine from guild or first admin)
└── created_at                       → earliest tournament created date
```

**Challenges**:
- Discord guilds may no longer exist (bot may not be in server)
- Need to fetch guild info from Discord API (requires bot to still be in guilds)
- Determining organization owner (could use first admin or tournament creator)
- Some features (like `racerverification`) might span multiple guilds

**Implementation Steps**:
1. Extract unique guild_ids from source tables
2. Attempt to fetch guild info from Discord API
3. Create organization for each guild
4. Create discord_guild records linking org to Discord server
5. Create organization memberships for users who participated in that guild
6. Log guild_id → organization_id mappings

### Phase 4: Async Tournament Migration
**Status**: Planned (highest priority)

#### 4.1: Tournament Core Data

**Source Table**: `asynctournament`  
**Target Table**: `async_tournament`

**Mapping**:
```
SahasrahBot asynctournament            → SahaBot2 async_tournament
├── id                                → (new ID, log mapping)
├── name                              → name
├── guild_id                          → organization_id (via guild mapping)
├── channel_id                        → discord_channel_id
├── report_channel_id                 → (custom field or ignore)
├── owner_id                          → owner_discord_id
├── created                           → created_at
├── updated                           → updated_at
├── active                            → active
├── allowed_reattempts                → allowed_reattempts
├── runs_per_pool                     → (custom field or default 1)
└── customization                     → (custom field or ignore)
```

**Status**: ✅ **Already implemented in SahaBot2** (core fields)  
**Missing fields**: `report_channel_id`, `runs_per_pool`, `customization`

**Implementation Steps**:
1. Map guild_id to organization_id
2. Create tournament with organization reference
3. Log old tournament_id → new tournament_id mapping
4. Migrate associated data (pools, permalinks, races) in subsequent steps

#### 4.2: Permalink Pools

**Source Table**: `asynctournamentpermalinkpool`  
**Target Table**: `async_tournament_permalink_pool` (to be created)

**Mapping**:
```
SahasrahBot asynctournamentpermalinkpool → SahaBot2 async_tournament_permalink_pool
├── id                                   → (new ID, log mapping)
├── tournament_id                        → async_tournament_id (via mapping)
├── name                                 → name
├── preset                               → preset
├── created                              → created_at
└── updated                              → updated_at
```

**Status**: ⚠️ **Partially implemented** (model exists, needs pool support)

#### 4.3: Permalinks

**Source Table**: `asynctournamentpermalink`  
**Target Table**: `async_tournament_permalink` (to be created)

**Mapping**:
```
SahasrahBot asynctournamentpermalink → SahaBot2 async_tournament_permalink
├── id                              → (new ID, log mapping)
├── pool_id                         → pool_id (via mapping)
├── url                             → url
├── notes                           → notes
├── live_race                       → (ignore or custom field)
├── par_time                        → par_time
├── par_updated_at                  → par_updated_at
├── created                         → created_at
└── updated                         → updated_at
```

**Status**: ⚠️ **Needs implementation** (permalink model needed)

#### 4.4: Races

**Source Table**: `asynctournamentrace`  
**Target Table**: `async_tournament_race` (to be created)

**Mapping**:
```
SahasrahBot asynctournamentrace     → SahaBot2 async_tournament_race
├── id                             → (new ID, log mapping)
├── tournament_id                  → async_tournament_id (via mapping)
├── permalink_id                   → permalink_id (via mapping)
├── user_id                        → user_id (via user mapping)
├── thread_id                      → thread_id
├── thread_open_time               → thread_opened_at
├── thread_timeout_time            → thread_timeout_at
├── start_time                     → started_at
├── end_time                       → finished_at
├── status                         → status
├── review_status                  → review_status
├── reviewed_by_id                 → reviewed_by_id (via user mapping)
├── reviewed_at                    → reviewed_at
├── reviewer_notes                 → reviewer_notes
├── runner_notes                   → runner_notes
├── runner_vod_url                 → vod_url
├── run_collection_rate            → collection_rate
├── run_igt                        → igt_time
├── reattempted                    → reattempted
├── reattempt_reason               → reattempt_reason
├── score                          → score
├── score_updated_at               → score_updated_at
├── created                        → created_at
└── updated                        → updated_at
```

**Status**: ⚠️ **Needs implementation** (race model needed)

#### 4.5: Live Races

**Source Table**: `asynctournamentliverace`  
**Target Table**: (to be created or ignored)

**Decision**: Consider whether to migrate live races or mark them as historical only.

**Status**: ⏸️ **Deferred** (low priority, historical data)

#### 4.6: Tournament Permissions

**Source Table**: `asynctournamentpermissions`  
**Target Table**: `organization_member` with roles, or custom tournament permissions

**Mapping Strategy**:
```
SahasrahBot permissions             → SahaBot2 organization_member or custom
├── user_id                        → user_id (via user mapping)
├── discord_role_id                → discord_role_id
├── role (admin/mod/public)        → organization role or tournament role
└── tournament_id                  → async_tournament_id
```

**Challenges**:
- SahaBot2 uses organization-level permissions, not tournament-level
- May need to create custom tournament permission table
- Discord role-based permissions need to be mapped to new system

**Status**: ⚠️ **Needs design decision** (permission model mismatch)

#### 4.7: Tournament Whitelist

**Source Table**: `asynctournamentwhitelist`  
**Target Table**: (to be created or use organization members)

**Decision**: Determine if tournament whitelists should be:
- Migrated to organization members (invited users)
- Separate tournament whitelist table
- Ignored (deprecated feature)

**Status**: ⏸️ **Deferred** (needs decision)

#### 4.8: Audit Logs

**Source Table**: `asynctournamentauditlog`  
**Target Table**: `audit_log`

**Mapping**:
```
SahasrahBot asynctournamentauditlog → SahaBot2 audit_log
├── user_id                        → user_id (via mapping)
├── tournament_id                  → (context: async_tournament)
├── action                         → action
├── details                        → details (JSON)
├── created                        → created_at
└── updated                        → updated_at
```

**Status**: ✅ **Audit system exists**, needs migration script

#### 4.9: Review Notes

**Source Table**: `asynctournamentreviewnotes`  
**Target Table**: (to be created)

**Mapping**:
```
SahasrahBot asynctournamentreviewnotes → SahaBot2 race_review_notes
├── id                                → (new ID)
├── race_id                           → race_id (via mapping)
├── author_id                         → author_id (via user mapping)
├── note                              → note
└── created                           → created_at
```

**Status**: ⚠️ **Needs implementation** (review notes table)

### Phase 5: Racer Verification Migration
**Status**: Planned

**Source Table**: `racerverification`, `verifiedracer`  
**Target Table**: `racer_verification`, `verified_racer`

**Mapping**:
```
SahasrahBot racerverification         → SahaBot2 racer_verification
├── id                               → (new ID, log mapping)
├── guild_id                         → organization_id (via guild mapping)
├── message_id                       → message_id
├── role_id                          → role_id
├── racetime_categories              → racetime_category (first or primary)
├── use_alttpr_ladder                → (custom field or ignore)
├── minimum_races                    → minimum_races
├── time_period_days                 → time_period_days
├── reverify_period_days             → reverify_period_days
├── channel_id                       → channel_id
├── audit_channel_id                 → audit_channel_id
├── revoke_ineligible                → revoke_ineligible
├── created                          → created_at
└── updated                          → updated_at
```

**Note**: SahaBot2 `racer_verification` supports **multiple categories** via many-to-many relationship. Original data has comma-separated categories in single field.

**Status**: ✅ **Model exists**, needs migration for category splitting

**Verified Racers**:
```
SahasrahBot verifiedracer            → SahaBot2 verified_racer
├── id                              → (new ID)
├── racer_verification_id           → racer_verification_id (via mapping)
├── user_id                         → user_id (via user mapping)
├── estimated_count                 → race_count
├── created                         → created_at
└── last_verified                   → last_verified_at
```

**Status**: ✅ **Model exists**, needs migration script

### Phase 6: Preset/Randomizer Data Migration
**Status**: Planned (lower priority)

**Source Tables**:
- `presetnamespacescollaborators` → `preset_namespace_permission`
- `presets` → `randomizer_preset`
- `presetnamespacescollaborators` → `preset_namespace_permission`

**Status**: ✅ **Models exist**, needs migration script with user ID mapping

### Phase 7: Other Tables (Lower Priority)
**Status**: Deferred

**Tables to Evaluate**:
- `audit_generated_games` - Game generation history (analytics)
- `audit_messages` - Discord message audit (may not be needed)
- `config` - Guild configuration (migrate to organization settings)
- `daily` - Daily challenges (deprecated?)
- `patch_distribution` - Patch usage tracking (analytics)
- `spoiler_races` - Spoiler race tracking (deprecated?)
- `triforcetexts` - Custom triforce texts (feature-specific)
- `voice_role` - Voice role automation (Discord-specific feature)

**Decision**: Evaluate which features are being ported to SahaBot2 before migrating.

---

## Database Mapping Tables

The migration script will maintain several mapping tables to track old → new ID relationships:

```sql
-- Temporary mapping tables (can be dropped after migration)
CREATE TABLE migration_user_map (
    old_id INT PRIMARY KEY,
    new_id INT NOT NULL,
    discord_user_id BIGINT,
    migrated_at DATETIME
);

CREATE TABLE migration_tournament_map (
    old_id INT PRIMARY KEY,
    new_id INT NOT NULL,
    old_guild_id BIGINT,
    new_organization_id INT,
    migrated_at DATETIME
);

CREATE TABLE migration_guild_org_map (
    guild_id BIGINT PRIMARY KEY,
    organization_id INT NOT NULL,
    guild_name VARCHAR(255),
    migrated_at DATETIME
);

CREATE TABLE migration_pool_map (
    old_id INT PRIMARY KEY,
    new_id INT NOT NULL,
    migrated_at DATETIME
);

CREATE TABLE migration_permalink_map (
    old_id INT PRIMARY KEY,
    new_id INT NOT NULL,
    migrated_at DATETIME
);

CREATE TABLE migration_race_map (
    old_id INT PRIMARY KEY,
    new_id INT NOT NULL,
    migrated_at DATETIME
);
```

---

## Migration Script Structure

```python
# tools/data_migration.py

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from tortoise import Tortoise
from tortoise.transactions import in_transaction

# Import both old and new models
# (will need to structure imports carefully to avoid conflicts)

logger = logging.getLogger(__name__)

class DataMigration:
    """Migrates data from SahasrahBot to SahaBot2."""
    
    def __init__(self, source_db_url: str, target_db_url: str):
        self.source_db = source_db_url
        self.target_db = target_db_url
        
        # ID mapping dictionaries
        self.user_map: Dict[int, int] = {}
        self.tournament_map: Dict[int, int] = {}
        self.guild_org_map: Dict[int, int] = {}
        self.pool_map: Dict[int, int] = {}
        self.permalink_map: Dict[int, int] = {}
        self.race_map: Dict[int, int] = {}
    
    async def initialize_connections(self):
        """Connect to both databases."""
        # Initialize connections to source and target
        pass
    
    async def migrate_users(self):
        """Phase 2: Migrate users."""
        logger.info("Starting user migration...")
        # Implementation
        pass
    
    async def migrate_organizations(self):
        """Phase 3: Create organizations from guilds."""
        logger.info("Starting organization creation...")
        # Implementation
        pass
    
    async def migrate_tournaments(self):
        """Phase 4: Migrate async tournaments."""
        logger.info("Starting tournament migration...")
        # Implementation
        pass
    
    async def migrate_racer_verification(self):
        """Phase 5: Migrate racer verification."""
        logger.info("Starting racer verification migration...")
        # Implementation
        pass
    
    async def migrate_presets(self):
        """Phase 6: Migrate presets and namespaces."""
        logger.info("Starting preset migration...")
        # Implementation
        pass
    
    async def run_full_migration(self):
        """Execute complete migration."""
        try:
            await self.initialize_connections()
            
            # Execute phases in order
            await self.migrate_users()
            await self.migrate_organizations()
            await self.migrate_tournaments()
            await self.migrate_racer_verification()
            await self.migrate_presets()
            
            logger.info("Migration completed successfully")
        except Exception as e:
            logger.error("Migration failed: %s", e)
            raise
        finally:
            # Close connections
            pass

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate data from SahasrahBot to SahaBot2")
    parser.add_argument("--source-db", required=True, help="Source database URL")
    parser.add_argument("--target-db", required=True, help="Target database URL")
    parser.add_argument("--phase", choices=["users", "orgs", "tournaments", "verification", "presets", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true", help="Test migration without committing")
    
    args = parser.parse_args()
    
    migration = DataMigration(args.source_db, args.target_db)
    asyncio.run(migration.run_full_migration())
```

---

## Pre-Migration Checklist

Before running the migration:

- [ ] **Backup both databases** (source and target)
- [ ] **Test migration on copy of production data**
- [ ] **Verify all SahaBot2 models are finalized** (especially async tournament models)
- [ ] **Ensure Discord bot is in all source guilds** (to fetch guild names)
- [ ] **Create migration mapping tables** in target database
- [ ] **Review data quality** in source database (duplicate users, orphaned records, etc.)
- [ ] **Plan downtime window** (if needed for production migration)
- [ ] **Document rollback procedure** (in case migration fails)

---

## Post-Migration Validation

After migration:

- [ ] **Verify row counts** (source vs target for each table)
- [ ] **Spot-check migrated data** (random sampling)
- [ ] **Validate foreign key relationships** (no orphaned records)
- [ ] **Test core functionality** (tournament creation, race submission, etc.)
- [ ] **Verify user logins** (Discord OAuth2 works for migrated users)
- [ ] **Check organization memberships** (users correctly associated with orgs)
- [ ] **Validate permissions** (migrated permissions work as expected)
- [ ] **Review audit logs** (migration events logged)
- [ ] **Performance testing** (ensure new database performs adequately)
- [ ] **Export mapping tables** for reference (keep old_id → new_id mappings)

---

## Rollback Plan

If migration fails or data integrity issues are discovered:

1. **Stop SahaBot2 application**
2. **Restore target database from pre-migration backup**
3. **Document failure reason** (for post-mortem)
4. **Fix migration script** (address identified issues)
5. **Re-test on copy of production data**
6. **Retry migration** when ready

---

## Migration Timeline

**Estimated Duration**: 4-6 hours (depending on data volume)

**Phases**:
1. **Preparation**: 1 hour (backups, validation, setup)
2. **User Migration**: 30 minutes
3. **Organization Creation**: 30 minutes
4. **Tournament Migration**: 2-3 hours (largest dataset)
5. **Racer Verification**: 30 minutes
6. **Preset Migration**: 30 minutes
7. **Validation**: 1 hour
8. **Contingency**: 1 hour (buffer for issues)

---

## Missing Models/Fields Needed in SahaBot2

### High Priority (Async Tournaments)
- [ ] `async_tournament_permalink_pool` model
- [ ] `async_tournament_permalink` model
- [ ] `async_tournament_race` model
- [ ] `race_review_notes` model
- [ ] Tournament-level permissions (if needed)
- [ ] Additional fields on `async_tournament`:
  - [ ] `report_channel_id` (optional)
  - [ ] `runs_per_pool` (optional)
  - [ ] `customization` (optional)

### Medium Priority (Features)
- [ ] Multi-category support for `racer_verification` (✅ already implemented)
- [ ] Custom organization settings table (for migrated guild configs)

### Low Priority (Analytics/Historical)
- [ ] Game generation audit table (if analytics needed)
- [ ] Triforce texts table (if feature ported)

---

## Notes and Considerations

### Discord Guild Access
- Migration requires Discord bot to still be in source guilds to fetch names
- If bot is no longer in guild, organization name will be generic ("Guild {guild_id}")
- Consider manual review of organization names after migration

### User Authentication
- Migrated users will authenticate via Discord OAuth2 on first login
- User profile data will be updated from Discord on each login

### Organization Ownership
- Original SahasrahBot didn't have explicit organization owners
- Options for determining owner:
  1. Use first tournament creator in guild
  2. Use guild owner (requires Discord API fetch)
  3. Manual assignment after migration

### Tournament Creator Attribution
- Original uses `owner_id` (Discord user ID)
- Need to map to SahaBot2 user record
- If user doesn't exist, create placeholder or set to NULL

### Data Gaps
- Some SahasrahBot features may not have equivalents in SahaBot2
- Document which data is intentionally not migrated
- Provide export of non-migrated data for reference

### Testing Strategy
1. **Unit tests**: Test each migration phase independently
2. **Integration tests**: Test full migration on small dataset
3. **Production-like test**: Full migration on copy of production data
4. **Dry run**: Execute migration without committing (rollback at end)

---

## References

- **Original SahasrahBot**: https://github.com/tcprescott/sahasrahbot
- **SahasrahBot Models**: https://github.com/tcprescott/sahasrahbot/blob/main/alttprbot/models/models.py
- **SahaBot2 Architecture**: [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)
- **SahaBot2 Database Models**: `models/` directory

---

**Last Updated**: November 5, 2025  
**Status**: Planning Phase - Document will be updated as migration progresses
