# Database Models Reference

Complete reference for all 30+ database models in SahaBot2, organized by domain.

**Last Updated**: November 4, 2025  
**Database**: MySQL via Tortoise ORM  
**Coverage**: 30+ models documented

---

## Table of Contents

- [User Management (3)](#user-management)
- [Organizations (4)](#organizations)
- [Tournaments (7)](#tournaments)
- [Async Qualifiers (6)](#async-tournaments)
- [Discord Integration (3)](#discord-integration)
- [RaceTime Integration (4)](#racetime-integration)
- [Settings & Configuration (5)](#settings--configuration)
- [Notifications (2)](#notifications)
- [Infrastructure (3)](#infrastructure)

---

## User Management

### User
**File**: `models/user.py`

**Purpose**: Represents a user account authenticated via Discord.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Unique user ID |
| `discord_id` | BigIntField | Unique, Indexed | Discord user ID (snowflake) |
| `discord_username` | CharField(255) | - | Discord username at signup |
| `discord_email` | CharField(255) | Unique | Discord email address (PII) |
| `permission` | IntEnumField | Default: USER | Global permission level (USER, MODERATOR, ADMIN, SUPERADMIN) |
| `racetime_id` | CharField(255) | Unique, Nullable | RaceTime.gg user ID if linked |
| `racetime_name` | CharField(255) | Nullable | RaceTime.gg username |
| `racetime_access_token` | LongTextField | Nullable | OAuth2 token for RaceTime API |
| `created_at` | DatetimeField | auto_now_add | Account creation timestamp |
| `updated_at` | DatetimeField | auto_now | Last update timestamp |

**Relationships**:
- `organizations` (reverse) - Organizations user is member of
- `tokens` (reverse) - API tokens owned by user
- `audit_logs` (reverse) - Actions performed by user

**Enums**:
```python
class Permission(IntEnum):
    USER = 1
    MODERATOR = 2
    ADMIN = 3
    SUPERADMIN = 4
```

**Indexes**:
- discord_id (unique)
- racetime_id (unique)
- permission

**Notes**:
- Email address is sensitive PII - only superadmins should access
- RaceTime fields only populated if user has linked account
- Discord info synced on each login

---

### ApiToken
**File**: `models/api_token.py`

**Purpose**: API authentication tokens for programmatic access.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Token ID |
| `user` | ForeignKeyField(User) | - | Token owner |
| `token_hash` | CharField(255) | Unique, Indexed | Hashed token (never store plaintext) |
| `name` | CharField(255) | - | Human-readable token name |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |
| `last_used_at` | DatetimeField | Nullable | Last usage timestamp |
| `expires_at` | DatetimeField | Nullable | Expiration date (null = never) |
| `is_active` | BooleanField | Default: True | Token active status |

**Relationships**:
- `user` (ForeignKey) - Token owner

**Indexes**:
- token_hash (unique)
- (user_id, is_active)
- expires_at

**Notes**:
- Tokens are hashed with bcrypt before storage
- Plaintext token only returned once at creation
- Tokens checked against expiration and active status

---

### AuditLog
**File**: `models/audit_log.py`

**Purpose**: Log of all significant user actions for compliance and debugging.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Log entry ID |
| `user` | ForeignKeyField(User) | - | User who performed action |
| `organization` | ForeignKeyField(Organization) | Nullable | Org context (if applicable) |
| `action` | CharField(255) | Indexed | Action type (user_created, tournament_updated, etc.) |
| `resource_type` | CharField(255) | - | What was acted upon (User, Tournament, etc.) |
| `resource_id` | IntField | - | ID of resource |
| `details` | JSONField | Default: {} | Additional context/changes |
| `ip_address` | CharField(45) | Nullable | Client IP address |
| `created_at` | DatetimeField | auto_now_add, Indexed | Action timestamp |

**Relationships**:
- `user` (ForeignKey) - User who performed action
- `organization` (ForeignKey) - Organization context

**Indexes**:
- (user_id, created_at) - "Who did what when"
- (resource_type, resource_id) - "What happened to resource"
- (organization_id, created_at) - "Org activity"
- action - "Count by action type"

**Notes**:
- Created by event listeners after operations succeed
- Retention: Keep indefinitely for compliance
- Example details: `{"old_value": 1, "new_value": 3, "field": "permission"}`

---

## Organizations

### Organization
**File**: `models/organizations.py`

**Purpose**: A tenant/workspace for users to collaborate and manage tournaments.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Organization ID |
| `name` | CharField(255) | - | Org name (not unique) |
| `description` | TextField | Nullable | Org description |
| `owner` | ForeignKeyField(User) | - | User who created org |
| `discord_guild_id` | BigIntField | Nullable, Unique | Linked Discord server ID |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |
| `updated_at` | DatetimeField | auto_now | Last update timestamp |

**Relationships**:
- `owner` (ForeignKey) - Creator/owner
- `members` (reverse via OrganizationMember) - Members in org
- `tournaments` (reverse) - Tournaments in org
- `settings` (reverse) - Configuration keys
- `presets` (reverse) - Randomizer presets

**Notes**:
- Multi-tenant isolation: All org data filtered by this ID
- Owner can transfer ownership
- Discord guild can only be linked to one org

---

### OrganizationMember
**File**: `models/organizations.py`

**Purpose**: Join table for Users and Organizations with permission grants.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Member relationship ID |
| `organization` | ForeignKeyField(Organization) | - | Organization |
| `user` | ForeignKeyField(User) | - | User member |
| `permission` | IntEnumField | Default: USER | Org-specific permission level |
| `joined_at` | DatetimeField | auto_now_add | Join timestamp |
| `invited_by` | ForeignKeyField(User) | Nullable | Who invited them |

**Relationships**:
- `organization` (ForeignKey) - Org they're in
- `user` (ForeignKey) - User account
- `invited_by` (ForeignKey) - Inviter (optional)

**Constraints**:
- Unique: (organization_id, user_id) - User can't be member twice

**Indexes**:
- (organization_id, permission) - "Managers in org"
- (user_id, organization_id) - "What orgs is user in"

**Notes**:
- Permission overwrites global permission within org
- Role hierarchy: USER < MEMBER < MANAGER < ADMIN < OWNER
- Leaving org: Delete this record

---

### OrganizationInvite
**File**: `models/organizations.py`

**Purpose**: Shareable invitation links for joining organizations.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Invite ID |
| `organization` | ForeignKeyField(Organization) | - | Target org |
| `code` | CharField(32) | Unique, Indexed | Shareable invite code |
| `created_by` | ForeignKeyField(User) | - | Who created invite |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |
| `expires_at` | DatetimeField | Indexed | When invite expires |
| `max_uses` | IntField | Nullable | Max uses before expiration (null = unlimited) |
| `uses` | IntField | Default: 0 | Current use count |

**Relationships**:
- `organization` (ForeignKey) - Target org
- `created_by` (ForeignKey) - Creator

**Indexes**:
- code (unique)
- expires_at - "Find expired invites for cleanup"
- (organization_id, expires_at)

**Notes**:
- Code generated as `secrets.token_urlsafe(16)` (URL-safe base64)
- Invites auto-expire after 30 days (default)
- Cleanup task: delete expired invites periodically

---

### Setting
**File**: `models/settings.py`

**Purpose**: Key-value store for global and org-scoped configuration.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Setting ID |
| `organization` | ForeignKeyField(Organization) | Nullable | Org (null = global) |
| `key` | CharField(255) | Indexed | Setting key |
| `value` | TextField | - | Setting value (JSON or string) |
| `value_type` | CharField(50) | Default: string | Type hint (string, int, bool, json) |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |
| `updated_at` | DatetimeField | auto_now | Last update timestamp |

**Constraints**:
- Unique: (organization_id, key) - One value per key per org

**Indexes**:
- (organization_id, key)
- (key) - for global lookups

**Example Settings**:
```
max_tournaments_per_org: 50
tournament_timeout_minutes: 1440
enable_racetime_integration: true
```

---

## Tournaments

### Tournament
**File**: `models/tournament.py`

**Purpose**: Traditional synchronous tournament with scheduled races and crews.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Tournament ID |
| `organization` | ForeignKeyField(Organization) | - | Owning org |
| `name` | CharField(255) | - | Tournament name |
| `description` | TextField | Nullable | Description |
| `status` | CharField(50) | Default: planning | Status (planning, active, completed, cancelled) |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |
| `updated_at` | DatetimeField | auto_now | Last update |
| `starts_at` | DatetimeField | Nullable | Tournament start time |
| `ends_at` | DatetimeField | Nullable | Tournament end time |
| `discord_channel_id` | BigIntField | Nullable | Discord channel for tournament |

**Relationships**:
- `organization` (ForeignKey) - Owning org
- `crews` (reverse via TournamentCrew) - Crew members
- `matches` (reverse) - Scheduled matches
- `races` (reverse) - Individual races

**Indexes**:
- (organization_id, status) - "Get active tournaments"
- created_at

**Notes**:
- Designed for live/scheduled tournaments
- Crews are assigned specific roles (commentator, organizer, etc.)
- Discord channel for announcements/results

---

### TournamentCrew
**File**: `models/tournament.py`

**Purpose**: Crew members assigned to tournament roles.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Crew assignment ID |
| `tournament` | ForeignKeyField(Tournament) | - | Tournament |
| `user` | ForeignKeyField(User) | - | Crew member |
| `role` | CharField(255) | - | Role (commentator, organizer, tracker, etc.) |
| `assigned_at` | DatetimeField | auto_now_add | Assignment timestamp |

**Relationships**:
- `tournament` (ForeignKey) - Tournament
- `user` (ForeignKey) - Crew member

**Constraints**:
- Unique: (tournament_id, user_id, role) - One role per user per tournament

---

### Match
**File**: `models/tournament.py`

**Purpose**: Scheduled race/match in a tournament.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Match ID |
| `tournament` | ForeignKeyField(Tournament) | - | Tournament |
| `title` | CharField(255) | - | Match title |
| `scheduled_at` | DatetimeField | - | When match occurs |
| `status` | CharField(50) | Default: scheduled | Status (scheduled, active, completed, cancelled) |
| `racetime_room_url` | CharField(500) | Nullable | RaceTime.gg room URL |
| `discord_thread_id` | BigIntField | Nullable | Discord thread for results |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |

**Relationships**:
- `tournament` (ForeignKey) - Tournament
- `players` (reverse via MatchPlayers) - Participants

**Indexes**:
- (tournament_id, scheduled_at)
- scheduled_at - "Upcoming matches"

---

### MatchPlayers
**File**: `models/tournament.py`

**Purpose**: Join table for match participants and their results.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Participation record |
| `match` | ForeignKeyField(Match) | - | Match |
| `user` | ForeignKeyField(User) | - | Participant |
| `seed_url` | CharField(500) | - | ROM seed URL for player |
| `result` | CharField(50) | Default: pending | Result (pending, finished, disqualified, forfeit) |
| `place` | IntField | Nullable | Placement (1st, 2nd, etc.) |
| `time` | TimeField | Nullable | Completion time |

**Relationships**:
- `match` (ForeignKey) - Match
- `user` (ForeignKey) - Participant

**Constraints**:
- Unique: (match_id, user_id) - User participates once per match

---

### Race
**File**: `models/tournament.py`

**Purpose**: Individual race result (used in both tournament and async contexts).

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Race ID |
| `seed_url` | CharField(500) | - | ROM seed URL |
| `seed_hash` | CharField(255) | - | Seed hash (e.g., "Triforce-Agh-Agahnim") |
| `status` | CharField(50) | Default: pending | Status (pending, approved, rejected, submitted) |
| `submitted_by` | ForeignKeyField(User) | - | Who submitted result |
| `submitted_at` | DatetimeField | - | Submission timestamp |
| `approved_by` | ForeignKeyField(User) | Nullable | Who reviewed result |
| `approved_at` | DatetimeField | Nullable | Approval timestamp |
| `comment` | TextField | Nullable | Reviewer comment/vod link |

**Relationships**:
- `submitted_by` (ForeignKey) - Race completer
- `approved_by` (ForeignKey) - Reviewer
- `tournament` (ForeignKey) - Tournament (if applicable)

**Indexes**:
- (status, approved_by) - "Pending reviews"
- submitted_at

---

## Async Qualifiers

### AsyncTournament
**File**: `models/async_qualifier.py`

**Purpose**: Self-paced tournament where participants race on their own schedule.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Tournament ID |
| `organization` | ForeignKeyField(Organization) | - | Owning org |
| `name` | CharField(255) | - | Tournament name |
| `description` | TextField | Nullable | Description |
| `status` | CharField(50) | Default: registration | Status (registration, active, completed, cancelled) |
| `start_date` | DatetimeField | - | When tournament starts |
| `end_date` | DatetimeField | Nullable | When tournament ends (null = ongoing) |
| `min_participants` | IntField | Default: 2 | Minimum racers |
| `max_participants` | IntField | Nullable | Max participants (null = unlimited) |
| `created_by` | ForeignKeyField(User) | - | Tournament organizer |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |
| `updated_at` | DatetimeField | auto_now | Last update |

**Relationships**:
- `organization` (ForeignKey) - Owning org
- `pools` (reverse) - Race pools
- `participants` (reverse) - Registered racers
- `live_races` (reverse) - Scheduled live races

**Indexes**:
- (organization_id, status)
- start_date

**Notes**:
- Participants register themselves
- Multiple pools can exist for different weeks/rounds
- Start/end dates control registration window

---

### AsyncTournamentPool
**File**: `models/async_qualifier.py`

**Purpose**: Grouping of races within an async qualifier (e.g., "Week 1", "Quarterfinals").

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Pool ID |
| `tournament` | ForeignKeyField(AsyncTournament) | - | Parent tournament |
| `name` | CharField(255) | - | Pool name (e.g., "Week 1") |
| `description` | TextField | Nullable | Pool description |
| `round_number` | IntField | - | Round number (1, 2, etc.) |
| `start_date` | DatetimeField | - | Pool start date |
| `end_date` | DatetimeField | Nullable | Pool end date |
| `is_active` | BooleanField | Default: True | Whether pool is accepting races |

**Relationships**:
- `tournament` (ForeignKey) - Parent tournament
- `races` (reverse) - Races in pool
- `live_races` (reverse) - Scheduled live races

---

### AsyncTournamentParticipant
**File**: `models/async_qualifier.py`

**Purpose**: Participant registration in an async qualifier.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Registration ID |
| `tournament` | ForeignKeyField(AsyncTournament) | - | Tournament |
| `user` | ForeignKeyField(User) | - | Participant |
| `status` | CharField(50) | Default: registered | Status (registered, disqualified, withdrawn) |
| `registered_at` | DatetimeField | auto_now_add | Registration timestamp |

**Relationships**:
- `tournament` (ForeignKey) - Tournament
- `user` (ForeignKey) - Participant
- `race_submissions` (reverse) - Races submitted by participant

**Constraints**:
- Unique: (tournament_id, user_id) - Can't register twice

---

### AsyncRaceSubmission
**File**: `models/async_qualifier.py`

**Purpose**: A participant's submitted race result in async qualifier.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Submission ID |
| `pool` | ForeignKeyField(AsyncTournamentPool) | - | Pool race was in |
| `participant` | ForeignKeyField(AsyncTournamentParticipant) | - | Participant |
| `seed_url` | CharField(500) | - | ROM seed URL |
| `seed_hash` | CharField(255) | - | Seed hash |
| `time` | TimeField | - | Race completion time |
| `vod_url` | CharField(500) | Nullable | Video proof URL |
| `status` | CharField(50) | Default: pending | Status (pending, approved, rejected, resubmitted) |
| `submitted_at` | DatetimeField | - | When submitted |
| `reviewed_by` | ForeignKeyField(User) | Nullable | Reviewer |
| `reviewed_at` | DatetimeField | Nullable | Review timestamp |
| `review_comment` | TextField | Nullable | Reviewer's comment |

**Relationships**:
- `pool` (ForeignKey) - Pool this race belongs to
- `participant` (ForeignKey) - Racer
- `reviewed_by` (ForeignKey) - Reviewer

**Indexes**:
- (status, reviewed_by) - "Pending reviews"
- (participant_id, status)

**Notes**:
- Participant can resubmit if rejected
- Leaderboard calculated from approved submissions

---

### AsyncLiveRace
**File**: `models/async_qualifier.py`

**Purpose**: Scheduled live race within async qualifier (on RaceTime.gg).

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Race ID |
| `pool` | ForeignKeyField(AsyncTournamentPool) | - | Pool this race is in |
| `scheduled_at` | DatetimeField | - | When live race is scheduled |
| `category` | CharField(255) | - | RaceTime category (alttpr, sm, etc.) |
| `goal` | CharField(255) | - | Race goal |
| `info_text` | TextField | Nullable | Description/rules |
| `racetime_room_url` | CharField(500) | Nullable | RaceTime.gg room URL (set when opened) |
| `racetime_room_id` | CharField(255) | Nullable | RaceTime room ID |
| `status` | CharField(50) | Default: scheduled | Status (scheduled, opened, completed, cancelled) |
| `opened_at` | DatetimeField | Nullable | When room was created |
| `completed_at` | DatetimeField | Nullable | When race finished |
| `created_by` | ForeignKeyField(User) | - | Organizer who created |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |

**Relationships**:
- `pool` (ForeignKeyField) - Parent pool
- `created_by` (ForeignKeyField) - Organizer
- `participants` (reverse via AsyncLiveRaceParticipant) - Who's racing

**Indexes**:
- (pool_id, scheduled_at) - "Upcoming races"
- scheduled_at

**Notes**:
- Tasks can automatically open rooms at scheduled_at
- Can be cancelled/rescheduled before opening
- Results pulled from RaceTime after room closes

---

## Discord Integration

### DiscordGuild
**File**: `models/discord.py`

**Purpose**: Discord server configuration linked to organization.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Config ID |
| `organization` | ForeignKeyField(Organization) | - | Linked organization |
| `guild_id` | BigIntField | Unique, Indexed | Discord server ID (snowflake) |
| `guild_name` | CharField(255) | - | Server name (cached) |
| `notification_channel_id` | BigIntField | Nullable | Channel for notifications |
| `default_role_id` | BigIntField | Nullable | Role assigned to members |
| `created_at` | DatetimeField | auto_now_add | Configuration timestamp |
| `updated_at` | DatetimeField | auto_now | Last update |

**Relationships**:
- `organization` (ForeignKey) - Linked org

**Constraints**:
- guild_id is unique (server can only link to one org)

---

### DiscordScheduledEvent
**File**: `models/discord.py`

**Purpose**: Discord scheduled event for tournament announcements.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Event ID |
| `guild` | ForeignKeyField(DiscordGuild) | - | Guild |
| `discord_event_id` | BigIntField | Nullable | Discord event snowflake |
| `tournament` | ForeignKeyField(Tournament) | Nullable | Linked tournament |
| `title` | CharField(255) | - | Event title |
| `description` | TextField | Nullable | Event description |
| `scheduled_at` | DatetimeField | - | When event occurs |
| `location` | CharField(255) | Nullable | Event location (URL usually) |
| `status` | CharField(50) | Default: scheduled | Status (scheduled, active, completed, cancelled) |

**Relationships**:
- `guild` (ForeignKey) - Discord guild
- `tournament` (ForeignKey) - Tournament (if applicable)

---

### DiscordUser
**File**: `models/discord.py`

**Purpose**: Cached Discord user info for permission checking.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Record ID |
| `user` | ForeignKeyField(User) | - | Linked SahaBot2 user |
| `discord_id` | BigIntField | Unique | Discord snowflake |
| `avatar_url` | CharField(500) | Nullable | Discord avatar URL |
| `accent_color` | CharField(10) | Nullable | User's Discord accent color |
| `verified` | BooleanField | Default: False | Email verified on Discord |
| `last_sync_at` | DatetimeField | auto_now | Last time info refreshed |

**Relationships**:
- `user` (ForeignKey) - SahaBot2 user

---

## RaceTime Integration

### RacetimeBot
**File**: `models/racetime.py`

**Purpose**: Registered RaceTime.gg bot configuration.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Bot ID |
| `username` | CharField(255) | Unique, Indexed | RaceTime username |
| `category_slug` | CharField(255) | - | Category bot operates in |
| `access_token` | TextField | - | OAuth2 access token |
| `refresh_token` | TextField | - | OAuth2 refresh token |
| `created_by` | ForeignKeyField(User) | - | Who registered bot |
| `created_at` | DatetimeField | auto_now_add | Registration timestamp |
| `last_verified_at` | DatetimeField | Nullable | Last verification check |

**Relationships**:
- `created_by` (ForeignKey) - Registrant
- `org_assignments` (reverse) - Organizations using this bot

**Notes**:
- Tokens refreshed automatically when needed
- Stored encrypted at rest
- One bot per category

---

### RacetimeBotOrganization
**File**: `models/racetime.py`

**Purpose**: Assignment of bot to organization for use.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Assignment ID |
| `bot` | ForeignKeyField(RacetimeBot) | - | Bot |
| `organization` | ForeignKeyField(Organization) | - | Organization |
| `assigned_at` | DatetimeField | auto_now_add | Assignment timestamp |
| `assigned_by` | ForeignKeyField(User) | - | Who assigned |

**Constraints**:
- Unique: (bot_id, organization_id) - Bot assigned to org once

---

### RacetimeChatCommand
**File**: `models/racetime.py`

**Purpose**: Custom chat command for RaceTime rooms.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Command ID |
| `organization` | ForeignKeyField(Organization) | - | Owning organization |
| `name` | CharField(255) | - | Command name (without !) |
| `response` | TextField | - | Command response text |
| `scope` | CharField(50) | Default: ORGANIZATION | Scope (GLOBAL, ORGANIZATION, TOURNAMENT) |
| `enabled` | BooleanField | Default: True | Active status |
| `created_by` | ForeignKeyField(User) | - | Creator |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |

**Relationships**:
- `organization` (ForeignKey) - Owner org
- `created_by` (ForeignKey) - Creator

---

### RacetimeRoomProfile
**File**: `models/racetime.py`

**Purpose**: Template for creating RaceTime rooms with preset configuration.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Profile ID |
| `organization` | ForeignKeyField(Organization) | - | Owning organization |
| `name` | CharField(255) | - | Profile name |
| `category` | CharField(255) | - | RaceTime category |
| `goal` | CharField(500) | - | Race goal |
| `info_text` | TextField | Nullable | Room info/rules |
| `invitees_json` | JSONField | Default: {} | Preset invitees |
| `created_by` | ForeignKeyField(User) | - | Creator |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |

**Relationships**:
- `organization` (ForeignKey) - Owner org
- `created_by` (ForeignKey) - Creator

---

## Settings & Configuration

### PresetNamespace
**File**: `models/presets.py`

**Purpose**: Organizational namespace for grouping randomizer presets.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Namespace ID |
| `organization` | ForeignKeyField(Organization) | - | Owning organization |
| `name` | CharField(255) | - | Namespace name |
| `description` | TextField | Nullable | Namespace description |
| `owner` | ForeignKeyField(User) | - | Namespace owner |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |

**Relationships**:
- `organization` (ForeignKey) - Owner org
- `owner` (ForeignKey) - Primary owner
- `presets` (reverse) - Presets in namespace
- `members` (reverse via NamespaceMember) - Users with access

---

### RandomizerPreset
**File**: `models/presets.py`

**Purpose**: Saved randomizer seed generator configuration.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Preset ID |
| `namespace` | ForeignKeyField(PresetNamespace) | - | Parent namespace |
| `name` | CharField(255) | - | Preset name |
| `randomizer_type` | CharField(255) | - | Randomizer (alttpr, ootr, sm, etc.) |
| `configuration` | JSONField | - | Randomizer settings JSON |
| `created_by` | ForeignKeyField(User) | - | Creator |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |
| `updated_at` | DatetimeField | auto_now | Last update |

**Relationships**:
- `namespace` (ForeignKey) - Parent namespace
- `created_by` (ForeignKey) - Creator

**Example configuration**:
```json
{
  "difficulty": "hard",
  "item_placement": "advanced",
  "dungeon_items": "standard"
}
```

---

### StreamChannel
**File**: `models/streams.py`

**Purpose**: Stream channel configuration (Twitch, YouTube, etc.).

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Channel ID |
| `organization` | ForeignKeyField(Organization) | - | Owning organization |
| `name` | CharField(255) | - | Channel name |
| `platform` | CharField(50) | - | Platform (twitch, youtube, etc.) |
| `channel_url` | CharField(500) | - | Stream URL |
| `channel_handle` | CharField(255) | - | Channel username/handle |
| `is_active` | BooleanField | Default: True | Active status |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |

**Relationships**:
- `organization` (ForeignKey) - Owner org

---

## Notifications

### NotificationSubscription
**File**: `models/notifications.py`

**Purpose**: User's notification preferences for a specific event type.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Subscription ID |
| `user` | ForeignKeyField(User) | - | Subscriber |
| `event_type` | CharField(255) | - | Event type (MATCH_SCHEDULED, TOURNAMENT_CREATED, etc.) |
| `delivery_method` | CharField(50) | - | How to deliver (DISCORD_DM, EMAIL, WEBHOOK) |
| `is_enabled` | BooleanField | Default: True | Subscription active |
| `created_at` | DatetimeField | auto_now_add | Subscription timestamp |

**Relationships**:
- `user` (ForeignKey) - Subscriber

**Constraints**:
- Unique: (user_id, event_type, delivery_method) - One sub per combo

---

### NotificationLog
**File**: `models/notifications.py`

**Purpose**: Audit trail of notification delivery attempts.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Log ID |
| `user` | ForeignKeyField(User) | - | Recipient |
| `event_type` | CharField(255) | - | Event that triggered notification |
| `delivery_method` | CharField(50) | - | How it was sent |
| `delivery_status` | CharField(50) | Default: PENDING | PENDING, SENT, FAILED, RETRYING |
| `recipient_id` | CharField(255) | - | Recipient identifier (Discord ID, email, etc.) |
| `error_message` | TextField | Nullable | Error if failed |
| `attempts` | IntField | Default: 0 | Number of delivery attempts |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |
| `updated_at` | DatetimeField | auto_now | Last update |

**Relationships**:
- `user` (ForeignKey) - Recipient

**Indexes**:
- (delivery_status, updated_at) - "Pending and retry-ready"
- (user_id, created_at) - "User's notification history"

---

## Infrastructure

### ScheduledTask
**File**: `models/scheduled_task.py`

**Purpose**: Background task execution configuration (interval, cron, or one-time).

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Task ID |
| `organization` | ForeignKeyField(Organization) | - | Owning organization |
| `name` | CharField(255) | - | Task name |
| `description` | TextField | Nullable | Task description |
| `task_type` | IntEnumField | - | Task type (RACETIME_OPEN_ROOM = 1, CUSTOM = 99) |
| `schedule_type` | IntEnumField | - | Schedule type (INTERVAL = 1, CRON = 2, ONE_TIME = 3) |
| `interval_seconds` | IntField | Nullable | Repeat interval (for INTERVAL) |
| `cron_expression` | CharField(255) | Nullable | Cron expression (for CRON) |
| `scheduled_time` | DatetimeField | Nullable | One-time execution (for ONE_TIME) |
| `task_config` | JSONField | - | Task-specific configuration |
| `is_active` | BooleanField | Default: True | Task enabled status |
| `last_run_at` | DatetimeField | Nullable | Last execution time |
| `next_run_at` | DatetimeField | - | Next scheduled execution |
| `last_run_status` | CharField(50) | Nullable | Last result (success, failed, running) |
| `last_run_error` | TextField | Nullable | Last error message |
| `created_by` | ForeignKeyField(User) | - | Creator |
| `created_at` | DatetimeField | auto_now_add | Creation timestamp |

**Relationships**:
- `organization` (ForeignKey) - Owner org
- `created_by` (ForeignKey) - Creator

**Indexes**:
- (organization_id, is_active)
- (next_run_at, is_active) - "Find due tasks"

**Example task_config**:
```json
{
  "category": "alttpr",
  "goal": "Beat the game",
  "info": "Weekly race"
}
```

---

### TaskExecution
**File**: `models/scheduled_task.py`

**Purpose**: Historical log of task executions.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | IntField | Primary Key | Execution ID |
| `task` | ForeignKeyField(ScheduledTask) | - | Task that executed |
| `start_time` | DatetimeField | - | Execution start |
| `end_time` | DatetimeField | Nullable | Execution end |
| `status` | CharField(50) | - | Result (success, failed, timeout) |
| `error_message` | TextField | Nullable | Error if failed |
| `output_data` | JSONField | Nullable | Execution results/output |

**Relationships**:
- `task` (ForeignKey) - Task that executed

**Indexes**:
- (task_id, start_time) - "Task execution history"

---

## Data Model Diagram

```
User (1) ──┬── (M) OrganizationMember
           ├── (M) ApiToken
           ├── (M) AuditLog
           └── (M) Organization (owner)

Organization (1) ─┬── (M) OrganizationMember
                  ├── (M) OrganizationInvite
                  ├── (M) Tournament
                  ├── (M) AsyncTournament
                  ├── (M) Setting
                  ├── (M) PresetNamespace
                  ├── (M) ScheduledTask
                  ├── (M) RacetimeBotOrganization
                  └── (M) DiscordGuild

Tournament (1) ──┬── (M) TournamentCrew
                 ├── (M) Match
                 └── (M) Race

Match (1) ─── (M) MatchPlayers
AsyncTournament (1) ─┬── (M) AsyncTournamentPool
                     ├── (M) AsyncTournamentParticipant
                     └── (M) AsyncLiveRace

AsyncTournamentPool (1) ─┬── (M) AsyncRaceSubmission
                         └── (M) AsyncLiveRace

RacetimeBot (1) ─── (M) RacetimeBotOrganization
PresetNamespace (1) ─── (M) RandomizerPreset

NotificationSubscription (many-to-1) User
ScheduledTask (many-to-1) Organization
```

---

## Quick Lookup by Entity

| Use Case | Model(s) |
|----------|----------|
| User authentication | User, ApiToken |
| Organization management | Organization, OrganizationMember, OrganizationInvite |
| Tournament data | Tournament, TournamentCrew, Match, MatchPlayers, Race |
| Async tournament data | AsyncTournament, AsyncTournamentPool, AsyncTournamentParticipant, AsyncRaceSubmission, AsyncLiveRace |
| Discord integration | DiscordGuild, DiscordScheduledEvent, DiscordUser |
| RaceTime integration | RacetimeBot, RacetimeBotOrganization, RacetimeChatCommand, RacetimeRoomProfile |
| Randomizer presets | PresetNamespace, RandomizerPreset |
| Stream channels | StreamChannel |
| Notifications | NotificationSubscription, NotificationLog |
| Background tasks | ScheduledTask, TaskExecution |
| Settings/config | Setting |
| Audit/compliance | AuditLog |

---

## See Also

- [SERVICES_REFERENCE.md](SERVICES_REFERENCE.md) - Service layer that uses these models
- [API_ENDPOINTS_REFERENCE.md](API_ENDPOINTS_REFERENCE.md) - API routes that expose models
- [database.py](../../database.py) - Database initialization code
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
