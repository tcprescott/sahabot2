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
├── display_name                  → display_name
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

### Phase 3: Selective Organization Creation
**Status**: Planned

**Strategy**: Create organizations **only** for guilds actively using racer verification

**Rationale**:
- SahaBot2 can exist in Discord guilds without requiring organizations
- Organizations only needed for organization-scoped features (racer verification, tournaments)
- Automatically create organizations for guilds with racer verification to preserve functionality
- Other guilds can use simple bot features without organization overhead

**Migration Process**:

1. **Identify Guilds with Racer Verification**
   - Query `racerverification` table for distinct guild_ids
   - These guilds need organizations to preserve racer verification functionality

2. **Check Bot Guild Membership**
   - Use Discord API to verify bot is still in each guild
   - Only create organization if bot has access to guild

3. **Create Organization**
   - Fetch guild information from Discord API (name, owner_id, etc.)
   - Create organization with guild name
   - Link organization to Discord guild via `discord_guild` table

4. **Set Organization Owner**
   - Fetch Discord guild owner information
   - Create or find user record for guild owner
   - Set as organization owner with ADMIN permissions

5. **Create Organization Memberships**
   - Add guild owner as organization member with admin role
   - Add users who have verified racer status in that guild

**Mapping**:
```
Discord Guild (with racer verification) → SahaBot2 Organization
├── guild_id                           → (store in discord_guild table)
├── guild name (from Discord API)      → name
├── description                        → "Migrated from SahasrahBot"
├── owner (from Discord guild)         → owner (user with admin permissions)
├── created_at                         → earliest racer verification date
└── members                            → verified racers + guild owner
```

**Challenges**:
- Bot may no longer be in some guilds → skip org creation, log for manual review
- Guild owner may not have Discord account linked → create user from Discord API data
- Multiple racer verifications per guild → migrate only the most recent one (skip older entries)

**Implementation Steps**:
1. Extract unique guild_ids from `racerverification` table (select most recent per guild by created date)
2. For each guild_id:
   - Check if bot is in guild (Discord API)
   - If yes: 
     - Verify verification message still exists in channel (Discord API)
     - If message exists: Fetch guild info, create organization, create/find owner user, set owner
     - If message missing: Skip org creation, log reason
   - If no: Log guild_id to `migration_guild_org_map` for manual review
3. Create discord_guild records linking org to Discord server
4. Create organization memberships for guild owner and verified racers
5. Log guild_id → organization_id mappings

**Guild Owner User Creation**:
- Use Discord API to fetch guild owner information (username, discriminator, ID)
- Create user record with Discord data if owner doesn't have SahaBot2 account
- Fields populated: discord_id, discord_username, discord_avatar
- Owner can complete profile on first login via Discord OAuth2

**Outcome**:
- Organizations auto-created for active racer verification guilds
- Only most recent racer verification per guild migrated
- Verification message existence verified before migration
- Guild owners have real user accounts (not placeholders)
- Racer verification data directly associated with organizations
- Guilds without bot access or missing verification messages documented for post-migration manual setup

### Phase 4: Async Tournament Migration
**Status**: ⛔ **SKIPPED** - Not migrating async tournament data

**Rationale**: 
- Async tournament system has been completely redesigned in SahaBot2
- Historical async tournament data would require significant model creation and adaptation
- Focus migration effort on active features (racer verification, presets)
- Async tournaments can be recreated fresh in the new system

**Skipped Tables**:
- `asynctournament` - Tournament core data
- `asynctournamentpermalinkpool` - Permalink pools
- `asynctournamentpermalink` - Individual permalinks
- `asynctournamentrace` - Race submissions
- `asynctournamentliverace` - Live race tracking
- `asynctournamentpermissions` - Tournament-specific permissions
- `asynctournamentwhitelist` - Tournament whitelists
- `asynctournamentauditlog` - Tournament audit logs
- `asynctournamentreviewnotes` - Review notes

**Impact**:
- No historical async tournament data in SahaBot2
- Users will need to create new async tournaments
- Organization creation focuses on racer verification guilds only

### Phase 4: Racer Verification Migration
**Status**: Planned (organizations created in Phase 3)

**Source Table**: `racerverification`, `verifiedracer`  
**Target Table**: `racer_verification`, `verified_racer`

**Prerequisites**:
- Organizations must exist from Phase 3 (auto-created for racer verification guilds)
- Guild ID → Organization ID mapping available from Phase 3

**Migration Strategy**:
- Only the most recent racer verification per guild migrated (by created date)
- Older racer verifications in the same guild skipped
- Verification message existence verified via Discord API before migration
- Racer verification data migrated with direct organization association
- Guild IDs mapped to organization IDs from Phase 3
- If organization doesn't exist (bot not in guild or message missing), skip and log for manual review

**Mapping**:
```
SahasrahBot racerverification         → SahaBot2 racer_verification
├── id                               → (new ID, log mapping)
├── guild_id                         → organization_id (via guild→org mapping from Phase 3)
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

**Note**: 
- SahaBot2 `racer_verification` supports **multiple categories** via many-to-many relationship
- Original data has comma-separated categories in single field
- **Only most recent racer verification per guild migrated** (older entries skipped)
- **Verification message must still exist** in Discord channel (checked via Discord API)
- Organization ID automatically set from Phase 3 guild→org mapping
- If no organization exists for guild (bot not in server or message missing), skip record and log for manual review

**Status**: ✅ **Model exists**, needs migration script with Phase 3 org mapping

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

### Phase 5: Preset/Randomizer Data Migration
**Status**: Planned (medium priority)

**Source Data**:
- **Database Tables**:
  - `presetnamespacescollaborators` → `preset_namespace_permission`
  - `presets` → `randomizer_preset`
  - `presetnamespacescollaborators` → `preset_namespace_permission`
- **Disk-based Presets** (Global Repository):
  - Filesystem directory tree containing global preset files
  - Migration script reads directory structure and files
  - Writes presets into database as global/system presets

**Migration Strategy**:

1. **Database Presets** (User-created):
   - Migrate from `presets` table
   - Associate with users via user ID mapping
   - Preserve namespace collaborator permissions
   - Guild-scoped presets can optionally be linked to organizations

2. **Global Presets** (Disk-based):
   - Read preset files from original SahasrahBot repository filesystem
   - Parse directory structure to determine namespaces/categories
   - Create preset records in database
   - Mark as global/system presets (no user ownership or org-specific)
   - Preserve file paths/structure as metadata if needed

**Mapping**:
```
SahasrahBot presets (DB)              → SahaBot2 randomizer_preset
├── id                               → (new ID, log mapping)
├── preset                           → preset_data (JSON)
├── user_id                          → user_id (via user mapping)
├── created                          → created_at
└── updated                          → updated_at

SahasrahBot presets (Filesystem)     → SahaBot2 randomizer_preset
├── file path                        → name (derived from filename)
├── directory structure              → namespace/category (derived from path)
├── file contents                    → preset_data (JSON)
├── user_id                          → NULL or SYSTEM_USER_ID (global preset)
├── created                          → migration timestamp
└── updated                          → migration timestamp
```

**Implementation Steps**:
1. Migrate database-stored presets with user ID mapping
2. Migrate namespace collaborator permissions
3. Scan filesystem directory tree for global preset files
4. Parse each preset file and create database record
5. Mark global presets appropriately (no user/org association)
6. Log all preset ID mappings

**Challenges**:
- Determining correct namespace/category from filesystem structure
- Handling preset file format parsing (YAML, JSON, etc.)
- Differentiating global vs user presets
- Preserving collaborator permissions for namespaces

**Status**: ✅ **Models exist**, needs migration script with:
- User ID mapping for database presets
- Filesystem traversal for global presets
- Preset file parsing logic

### Phase 6: Other Tables (Lower Priority)
**Status**: Deferred

**Tables to Evaluate**:
- `audit_generated_games` - Game generation history (analytics) - may skip
- `audit_messages` - Discord message audit (may not be needed) - may skip
- `config` - Guild configuration (migrate to organization settings) - **evaluate**
- `daily` - Daily challenges (deprecated?) - may skip
- `patch_distribution` - Patch usage tracking (analytics) - may skip
- `spoiler_races` - Spoiler race tracking (deprecated?) - may skip
- `triforcetexts` - Custom triforce texts (feature-specific) - may skip
- `voice_role` - Voice role automation (Discord-specific feature) - may skip

**Decision**: Evaluate which features are being ported to SahaBot2 before migrating.

**Note**: Since async tournaments are not being migrated, many of these auxiliary tables may not be relevant.

---

## Database Mapping Tables

The migration script will maintain mapping tables to track old → new ID relationships:

```sql
-- Temporary mapping tables (can be dropped after migration)
CREATE TABLE migration_user_map (
    old_id INT PRIMARY KEY,
    new_id INT NOT NULL,
    discord_user_id BIGINT,
    migrated_at DATETIME
);

CREATE TABLE migration_guild_org_map (
    guild_id BIGINT PRIMARY KEY,
    organization_id INT NULL,  -- NULL if bot not in guild or message missing
    guild_name VARCHAR(255),
    bot_in_guild BOOLEAN,
    verification_message_exists BOOLEAN,
    most_recent_verification_id INT,  -- ID of most recent racer_verification
    racer_verification_count INT DEFAULT 0,  -- Total count before filtering
    migrated_at DATETIME,
    notes TEXT  -- Reason for skip (bot not in guild, message missing, etc.)
);
```

**Note**: 
- Guild→org mapping tracks which guilds got organizations created
- `bot_in_guild` flag indicates if bot is still in Discord server
- `verification_message_exists` flag indicates if verification message is still on server
- `most_recent_verification_id` identifies which verification was selected for migration
- `racer_verification_count` shows total verifications before filtering to most recent
- Tournament/race mapping tables not needed since async tournaments are not being migrated

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
    
    def __init__(self, source_db_url: str, target_db_url: str, discord_bot, presets_path: str):
        self.source_db = source_db_url
        self.target_db = target_db_url
        self.bot = discord_bot  # Discord bot instance for guild API access
        self.presets_path = presets_path  # Path to SahasrahBot preset directory
        
        # ID mapping dictionaries
        self.user_map: Dict[int, int] = {}
        self.guild_org_map: Dict[int, int] = {}  # guild_id → organization_id
        self.preset_map: Dict[int, int] = {}  # old preset_id → new preset_id
    
    async def initialize_connections(self):
        """Connect to both databases."""
        # Initialize connections to source and target
        pass
    
    async def migrate_users(self):
        """Phase 2: Migrate users."""
        logger.info("Starting user migration...")
        # Implementation
        pass
    
    async def create_organizations_for_racer_verification(self):
        """Phase 3: Create organizations for guilds with racer verification."""
        logger.info("Creating organizations for racer verification guilds...")
        # 1. Get distinct guild_ids from racerverification table (most recent per guild)
        # 2. For each guild_id:
        #    - Check if bot is in guild (Discord API)
        #    - If yes: 
        #      - Verify verification message exists in channel (Discord API)
        #      - Fetch guild info (name, owner_id) from Discord API
        #      - Create/find user for guild owner using Discord API data
        #      - Create organization with guild name
        #      - Set guild owner as organization owner with admin permissions
        #    - If no or message missing: Log to migration_guild_org_map with bot_in_guild=false
        # 3. Create discord_guild records linking org to Discord server
        # 4. Create organization memberships for guild owners
        # 5. Log guild_id → organization_id mappings
        pass
    
    async def migrate_racer_verification(self):
        """Phase 4: Migrate racer verification (most recent per guild only)."""
        logger.info("Starting racer verification migration...")
        # Use guild_org_map to associate verification data with organizations
        # Skip guilds without organizations (no bot access or message missing)
        # Only migrate most recent racer_verification per guild
        pass
    
    async def migrate_presets(self):
        """Phase 5: Migrate presets and namespaces."""
        logger.info("Starting preset migration...")
        # 1. Migrate database-stored presets (user-created)
        #    - Map user IDs
        #    - Migrate namespace permissions
        # 2. Migrate global presets from filesystem
        #    - Scan preset directory tree
        #    - Parse preset files (YAML/JSON)
        #    - Create database records for global presets
        #    - Mark as system/global (no user/org association)
        # 3. Log preset ID mappings
        pass
    
    async def migrate_global_presets_from_disk(self):
        """Migrate global presets from SahasrahBot repository filesystem."""
        logger.info("Migrating global presets from disk...")
        # Walk directory tree at self.presets_path
        # For each preset file:
        #   - Parse file contents
        #   - Extract namespace/category from path
        #   - Create randomizer_preset record
        #   - Mark as global preset
        pass
    
    async def run_full_migration(self):
        """Execute complete migration with selective organization creation."""
        try:
            await self.initialize_connections()
            
            # Execute phases in order
            await self.migrate_users()
            await self.create_organizations_for_racer_verification()
            await self.migrate_racer_verification()
            await self.migrate_presets()
            await self.migrate_global_presets_from_disk()
            
            logger.info("Migration completed successfully")
            logger.info("Organizations created for guilds with racer verification where bot is present")
            logger.info("Guilds without bot access logged for manual review")
            logger.info("Global presets migrated from filesystem")
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
    parser.add_argument("--discord-token", required=True, help="Discord bot token for guild API access")
    parser.add_argument("--presets-path", required=True, help="Path to SahasrahBot preset directory (filesystem)")
    parser.add_argument("--phase", choices=["users", "organizations", "verification", "presets", "global-presets", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true", help="Test migration without committing")
    
    args = parser.parse_args()
    
    migration = DataMigration(args.source_db, args.target_db, discord_bot, args.presets_path)
    asyncio.run(migration.run_full_migration())
```

---

## Pre-Migration Checklist

Before running the migration:

- [ ] **Backup both databases** (source and target)
- [ ] **Clone SahasrahBot repository** (to access preset filesystem directory)
- [ ] **Test migration on copy of production data**
- [ ] **Verify SahaBot2 models are finalized** (racer verification, presets)
- [ ] **Create migration mapping tables** in target database
- [ ] **Review data quality** in source database (duplicate users, orphaned records, etc.)
- [ ] **Plan downtime window** (if needed for production migration)
- [ ] **Document rollback procedure** (in case migration fails)
- [ ] **Confirm organization strategy** (selective org creation for racer verification)
- [ ] **Confirm async tournament skip** (no tournament data will be migrated)
- [ ] **Verify preset directory path** (location of global presets in SahasrahBot repo)

---

## Post-Migration Validation

After migration:

- [ ] **Verify row counts** (source vs target for each table)
- [ ] **Spot-check migrated data** (random sampling)
- [ ] **Validate user data** (Discord IDs, RaceTime accounts, display names)
- [ ] **Verify organization creation** (guilds with racer verification)
- [ ] **Check guild owner permissions** (owners should have admin on created orgs)
- [ ] **Review guild_org_map** (verify bot_in_guild status and org mappings)
- [ ] **Test core functionality** (user authentication works)
- [ ] **Verify user logins** (Discord OAuth2 works for migrated users)
- [ ] **Verify racer verification** (linked to correct organizations)
- [ ] **Verify presets** (database presets and global presets from filesystem)
- [ ] **Spot-check global presets** (random sampling of migrated filesystem presets)
- [ ] **Export mapping tables** for reference (keep old_id → new_id mappings)
- [ ] **Document guilds without bot access** (manual review for org creation)

**Post-Migration Setup**:
- Review guilds where bot is no longer present (migration_guild_org_map with bot_in_guild=false)
- Create additional organizations for other guilds as needed via web interface
- Invite users to organizations as needed

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

**Estimated Duration**: 2-3 hours (includes Discord API calls and filesystem preset migration)

**Phases**:
1. **Preparation**: 30 minutes (backups, validation, setup, Discord bot login, clone SahasrahBot repo)
2. **User Migration**: 30 minutes
3. **Selective Org Creation**: 30-45 minutes (Discord API calls, org creation, owner setup)
4. **Racer Verification**: 30 minutes (with org association)
5. **Preset Migration**: 45-60 minutes (database presets + global filesystem presets)
6. **Validation**: 30 minutes
7. **Contingency**: 15 minutes (buffer for Discord API rate limits or filesystem parsing issues)

**Post-Migration Setup** (done separately via web interface):
- Review guilds without bot access: Manual review of migration_guild_org_map entries where bot_in_guild=false
- Create organizations for other guilds: Manual, as needed for additional communities
- Associate presets with organizations: Manual, using guild_id references

**Note**: Async tournaments skipped; organizations created selectively.

---

## Missing Models/Fields Needed in SahaBot2

### Phase 3 (Selective Organization Creation)
- [x] `organization` model exists
- [x] `organization_member` model exists
- [x] `discord_guild` model exists
- [x] Owner permission system exists
- [ ] Migration mapping table: `migration_guild_org_map` (guild_id, organization_id, bot_in_guild)

### Phase 4 (Racer Verification)
- [x] Multi-category support for `racer_verification` (✅ already implemented)
- [x] `racer_verification` model exists
- [x] `verified_racer` model exists
- [x] Organization_id field in racer_verification for org association

### Phase 5 (Presets)
- [x] `randomizer_preset` model exists
- [x] `preset_namespace` model exists
- [x] `preset_namespace_permission` model exists
- [ ] Preset file parser (YAML/JSON) for filesystem presets
- [ ] Filesystem traversal logic for preset directory tree

### Phase 6 (Optional Features)
- [ ] Custom organization settings table (for migrated guild configs) - if needed
- [ ] Triforce texts table (if feature ported) - low priority

**Note**: Most models exist; main work is selective organization creation with Discord API integration and preset filesystem migration.

---

## Notes and Considerations

### Selective Organization Creation Strategy
- **Organizations created automatically for guilds with racer verification** (if bot is present AND verification message exists)
- **Only most recent racer verification per guild migrated** (older ones skipped)
- **Verification message existence verified** before org creation (Discord API message fetch)
- Bot can exist in guilds without organizations (for simple, non-org-scoped features)
- Discord API used to check bot membership, fetch guild details, and verify messages
- Guild owners get real user accounts created from Discord API data (username, ID, avatar)
- Guild owners automatically become organization owners with admin permissions
- Guilds where bot is no longer present or message is missing logged to migration_guild_org_map for manual review
- Preserves racer verification functionality while maintaining flexible deployment model
- Organizations created during migration (Phase 3) before racer verification migration (Phase 4)

### User Authentication
- Migrated users will authenticate via Discord OAuth2 on first login
- User profile data will be updated from Discord on each login

### Organization-Scoped Data
- Racer verification directly linked to organizations created in Phase 3
- Database presets may remain guild-scoped or be linked to organizations post-migration
- Global presets from filesystem marked as system/global (no org association)
- Guild_id preserved in all migrated data for reference and manual association

### Preset Migration
- **Two sources**: Database-stored user presets AND filesystem-based global presets
- Database presets migrated with user ID mapping and namespace permissions
- Filesystem presets read from SahasrahBot repository directory tree
- Preset file parsing required (YAML/JSON format detection)
- Global presets marked as system presets (no user/org ownership)
- Directory structure used to determine namespace/category organization

### Discord API Integration
- Bot token required for migration (to access Discord API)
- Discord API rate limits must be respected (check bot presence, fetch guild info, fetch messages)
- Guild owner users created from Discord API data (username, discriminator, ID, avatar)
- Verification message existence checked via Discord API (channel.fetch_message)
- Bot must have sufficient permissions to access guild info and read messages in verification channels
- **Only most recent racer verification per guild processed** (reduces API calls)

### Data Gaps
- **Async tournaments and all related data are intentionally not migrated**
- **Organizations created selectively** - only for racer verification guilds with bot present AND verification message exists
- **Only most recent racer verification per guild migrated** - older verifications skipped
- Some SahasrahBot features may not have equivalents in SahaBot2
- Document which data is intentionally not migrated
- Provide export of non-migrated data for reference if needed

### Testing Strategy
1. **Unit tests**: Test each migration phase independently (especially Discord API mocking and preset parsing)
2. **Integration tests**: Test full migration on small dataset
3. **Production-like test**: Full migration on copy of production data
4. **Dry run**: Execute migration without committing (rollback at end)
5. **Discord API tests**: Verify bot presence checks, guild info fetching, and message existence checks
6. **Preset parsing tests**: Test YAML/JSON parsing with sample preset files from filesystem

---

## References

- **Original SahasrahBot**: https://github.com/tcprescott/sahasrahbot
- **SahasrahBot Models**: https://github.com/tcprescott/sahasrahbot/blob/main/alttprbot/models/models.py
- **SahaBot2 Architecture**: [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)
- **SahaBot2 Database Models**: `models/` directory

---

**Last Updated**: November 5, 2025  
**Status**: Planning Phase - Document will be updated as migration progresses
