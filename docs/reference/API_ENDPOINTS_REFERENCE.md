# API Endpoints Reference

Complete reference for all 65+ REST API endpoints in SahaBot2.

**Last Updated**: November 4, 2025  
**Coverage**: 65+ endpoints documented across 19 route modules

---

## Table of Contents

- [Health & Info (1)](#health--info)
- [Users (3)](#users)
- [Organizations (8)](#organizations)
- [Organization Invites (4)](#organization-invites)
- [Tournaments (8)](#tournaments)
- [Async Tournaments (12)](#async-tournaments)
- [Async Live Races (6)](#async-live-races)
- [RaceTime Integration (12)](#racetime-integration)
- [Discord Integration (4)](#discord-integration)
- [Streams (4)](#streams)
- [Settings (2)](#settings)
- [Presets (8)](#presets)
- [Race Room Profiles (4)](#race-room-profiles)
- [Scheduled Tasks (6)](#scheduled-tasks)
- [API Tokens (4)](#api-tokens)
- [Admin (5)](#admin)

---

## Health & Info

### GET /health
**Purpose**: Health check endpoint for monitoring

**Parameters**: None

**Response**:
```json
{
  "status": "ok",
  "timestamp": "2025-11-04T12:00:00Z",
  "version": "2.0.0"
}
```

**Rate Limit**: None (public)  
**Authentication**: None

---

## Users

### GET /api/users/@me
**Purpose**: Get current authenticated user's profile

**Parameters**: None

**Response**:
```json
{
  "id": 123,
  "discord_id": 987654321,
  "discord_username": "username",
  "discord_email": "user@discord.com",
  "permission": 1,
  "created_at": "2025-01-01T00:00:00Z"
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required (Bearer token)  
**Authorization**: User views own profile

---

### GET /api/users/{user_id}
**Purpose**: Get specific user's profile

**Parameters**:
- `user_id` (path, int): User ID

**Response**: Same as above

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Admins only

---

### PUT /api/users/{user_id}/permission
**Purpose**: Update user's global permission level

**Parameters**:
- `user_id` (path, int): User to update
- `permission` (body, int): New permission level

**Request Body**:
```json
{
  "permission": 2
}
```

**Response**:
```json
{
  "id": 123,
  "permission": 2,
  "updated_at": "2025-11-04T12:00:00Z"
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Superadmins only

---

## Organizations

### POST /api/organizations
**Purpose**: Create new organization

**Parameters**:
- `name` (body, string, required): Organization name
- `description` (body, string, optional): Organization description

**Request Body**:
```json
{
  "name": "My Racing League",
  "description": "A competitive racing community"
}
```

**Response**:
```json
{
  "id": 1,
  "name": "My Racing League",
  "description": "A competitive racing community",
  "owner_id": 123,
  "created_at": "2025-11-04T12:00:00Z"
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Any authenticated user can create

---

### GET /api/organizations
**Purpose**: List user's organizations

**Parameters**:
- `page` (query, int, default 1): Page number
- `per_page` (query, int, default 20): Items per page

**Response**:
```json
{
  "organizations": [
    {"id": 1, "name": "My Racing League", ...},
    {"id": 2, "name": "Another Org", ...}
  ],
  "total": 2,
  "page": 1,
  "per_page": 20
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: User's own organizations

---

### GET /api/organizations/{org_id}
**Purpose**: Get organization details

**Parameters**:
- `org_id` (path, int): Organization ID

**Response**:
```json
{
  "id": 1,
  "name": "My Racing League",
  "description": "...",
  "owner_id": 123,
  "member_count": 5,
  "created_at": "2025-01-01T00:00:00Z"
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization members only

---

### PATCH /api/organizations/{org_id}
**Purpose**: Update organization settings

**Parameters**:
- `org_id` (path, int): Organization ID
- `name` (body, string, optional): New name
- `description` (body, string, optional): New description

**Response**: Updated organization object

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers only

---

### DELETE /api/organizations/{org_id}
**Purpose**: Delete organization

**Parameters**:
- `org_id` (path, int): Organization ID

**Response**:
```json
{
  "success": true,
  "message": "Organization deleted"
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization owner only

---

### GET /api/organizations/{org_id}/members
**Purpose**: List organization members

**Parameters**:
- `org_id` (path, int): Organization ID
- `page` (query, int, default 1): Page number

**Response**:
```json
{
  "members": [
    {
      "id": 123,
      "discord_username": "user1",
      "permission": "MANAGER",
      "joined_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 5
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization members

---

### POST /api/organizations/{org_id}/members/{user_id}
**Purpose**: Add member to organization

**Parameters**:
- `org_id` (path, int): Organization ID
- `user_id` (path, int): User to add

**Response**:
```json
{
  "id": 123,
  "permission": "USER",
  "joined_at": "2025-11-04T12:00:00Z"
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### DELETE /api/organizations/{org_id}/members/{user_id}
**Purpose**: Remove member from organization

**Parameters**:
- `org_id` (path, int): Organization ID
- `user_id` (path, int): User to remove

**Response**:
```json
{
  "success": true,
  "message": "Member removed"
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

## Organization Invites

### POST /api/organizations/{org_id}/invites
**Purpose**: Create organization invitation

**Parameters**:
- `org_id` (path, int): Organization ID

**Response**:
```json
{
  "code": "ABC123DEF456",
  "organization_id": 1,
  "expires_at": "2025-12-04T12:00:00Z",
  "created_at": "2025-11-04T12:00:00Z"
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### GET /api/organizations/{org_id}/invites
**Purpose**: List organization's active invitations

**Parameters**:
- `org_id` (path, int): Organization ID

**Response**:
```json
{
  "invites": [
    {"code": "ABC123...", "expires_at": "2025-12-04T...", ...}
  ],
  "total": 2
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### POST /api/organizations/invites/{code}/accept
**Purpose**: Accept and join organization via invite

**Parameters**:
- `code` (path, string): Invitation code

**Response**:
```json
{
  "success": true,
  "organization_id": 1,
  "organization_name": "My Racing League"
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Any authenticated user

---

### DELETE /api/organizations/{org_id}/invites/{code}
**Purpose**: Revoke invitation

**Parameters**:
- `org_id` (path, int): Organization ID
- `code` (path, string): Invitation code to revoke

**Response**:
```json
{
  "success": true,
  "message": "Invite revoked"
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

## Tournaments

### POST /api/organizations/{org_id}/tournaments
**Purpose**: Create new tournament

**Parameters**:
- `org_id` (path, int): Organization ID
- `name` (body, string): Tournament name
- `description` (body, string, optional): Description

**Response**: Tournament object with ID, status, etc.

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### GET /api/organizations/{org_id}/tournaments
**Purpose**: List organization's tournaments

**Parameters**:
- `org_id` (path, int): Organization ID
- `status` (query, string, optional): Filter by status
- `page` (query, int): Pagination

**Response**:
```json
{
  "tournaments": [...],
  "total": 10,
  "page": 1
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization members

---

### GET /api/tournaments/{tournament_id}
**Purpose**: Get tournament details

**Response**: Tournament object

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament members

---

### PATCH /api/tournaments/{tournament_id}
**Purpose**: Update tournament

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament organizers

---

### DELETE /api/tournaments/{tournament_id}
**Purpose**: Delete tournament

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament organizers

---

### POST /api/tournaments/{tournament_id}/crew
**Purpose**: Add crew member to tournament

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament organizers

---

### DELETE /api/tournaments/{tournament_id}/crew/{crew_id}
**Purpose**: Remove crew member

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament organizers

---

### POST /api/tournaments/{tournament_id}/discord-channel
**Purpose**: Assign Discord channel to tournament

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament organizers

---

## Async Tournaments

### POST /api/organizations/{org_id}/async-tournaments
**Purpose**: Create async tournament

**Parameters**:
- `org_id` (path, int): Organization ID
- `name` (body, string): Tournament name
- `seed_url` (body, string, optional): Default seed URL

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### GET /api/organizations/{org_id}/async-tournaments
**Purpose**: List async tournaments

**Parameters**:
- `org_id` (path, int): Organization ID
- `status` (query, string, optional): Filter status

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization members

---

### GET /api/async-tournaments/{tournament_id}
**Purpose**: Get async tournament details

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament members

---

### PATCH /api/async-tournaments/{tournament_id}
**Purpose**: Update async tournament

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament managers

---

### DELETE /api/async-tournaments/{tournament_id}
**Purpose**: Delete async tournament

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament managers

---

### POST /api/async-tournaments/{tournament_id}/pools
**Purpose**: Create race pool

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament managers

---

### GET /api/async-tournaments/{tournament_id}/pools
**Purpose**: List pools in tournament

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament members

---

### POST /api/async-tournaments/{tournament_id}/participants
**Purpose**: Add participant

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament members (self) / managers (others)

---

### GET /api/async-tournaments/{tournament_id}/leaderboard
**Purpose**: Get tournament leaderboard/standings

**Parameters**:
- `tournament_id` (path, int): Tournament ID
- `sort_by` (query, string): Sort column (wins, times, points)

**Response**:
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "player": "Player1",
      "wins": 10,
      "times": 15,
      "points": 1500
    }
  ]
}
```

**Rate Limit**: 60/minute  
**Authentication**: Optional (public leaderboards)  
**Authorization**: Tournament members

---

### POST /api/async-tournaments/{tournament_id}/races
**Purpose**: Create race in pool

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament managers

---

### GET /api/async-tournaments/{tournament_id}/races
**Purpose**: List races in tournament

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament members

---

## Async Live Races

### POST /api/async-tournaments/{tournament_id}/live-races
**Purpose**: Schedule live race

**Parameters**:
- `tournament_id` (path, int): Tournament ID
- `pool_id` (body, int): Race pool ID
- `scheduled_at` (body, datetime): When race starts
- `racetime_category` (body, string): RaceTime category

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament managers

---

### GET /api/async-tournaments/{tournament_id}/live-races
**Purpose**: List scheduled live races

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament members

---

### GET /api/async-live-races/{race_id}
**Purpose**: Get live race details

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament members

---

### PATCH /api/async-live-races/{race_id}
**Purpose**: Update live race

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament managers

---

### DELETE /api/async-live-races/{race_id}
**Purpose**: Cancel live race

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament managers

---

### POST /api/async-live-races/{race_id}/open-room
**Purpose**: Open RaceTime room for race

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Tournament managers

---

## RaceTime Integration

### GET /api/racetime/link/status
**Purpose**: Check if user's RaceTime account is linked

**Response**:
```json
{
  "linked": true,
  "racetime_id": "abc123",
  "racetime_name": "username"
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: User's own status

---

### POST /api/racetime/link/unlink
**Purpose**: Unlink RaceTime account

**Response**:
```json
{
  "success": true,
  "message": "Account unlinked"
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: User's own account

---

### GET /api/organizations/{org_id}/racetime-bots
**Purpose**: List organization's RaceTime bots

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization members

---

### POST /api/organizations/{org_id}/racetime-bots
**Purpose**: Register new RaceTime bot

**Parameters**:
- `username` (body, string): Bot username
- `auth_code` (body, string): OAuth2 code from RaceTime

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### GET /api/racetime-bots/{bot_id}
**Purpose**: Get bot configuration

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization members

---

### PATCH /api/racetime-bots/{bot_id}
**Purpose**: Update bot settings

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### DELETE /api/racetime-bots/{bot_id}
**Purpose**: Remove/deregister bot

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### GET /api/organizations/{org_id}/racetime-chat-commands
**Purpose**: List organization's chat commands

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization members

---

### POST /api/organizations/{org_id}/racetime-chat-commands
**Purpose**: Create chat command

**Parameters**:
- `name` (body, string): Command name
- `response` (body, string): Command response
- `scope` (body, string): TOURNAMENT, ORGANIZATION, or GLOBAL

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### PATCH /api/racetime-chat-commands/{command_id}
**Purpose**: Update chat command

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### DELETE /api/racetime-chat-commands/{command_id}
**Purpose**: Delete chat command

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

## Discord Integration

### POST /api/organizations/{org_id}/discord-guild
**Purpose**: Link Discord server to organization

**Parameters**:
- `guild_id` (body, int): Discord server ID

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### GET /api/organizations/{org_id}/discord-guild
**Purpose**: Get Discord server configuration

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization members

---

### PATCH /api/organizations/{org_id}/discord-guild
**Purpose**: Update Discord configuration

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### DELETE /api/organizations/{org_id}/discord-guild
**Purpose**: Unlink Discord server

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

## Streams

### POST /api/organizations/{org_id}/stream-channels
**Purpose**: Add stream channel

**Parameters**:
- `name` (body, string): Channel name
- `url` (body, string): Stream URL (Twitch, YouTube, etc.)

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### GET /api/organizations/{org_id}/stream-channels
**Purpose**: List stream channels

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization members

---

### PATCH /api/stream-channels/{channel_id}
**Purpose**: Update stream channel

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### DELETE /api/stream-channels/{channel_id}
**Purpose**: Remove stream channel

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

## Settings

### GET /api/settings
**Purpose**: Get global application settings (public)

**Response**:
```json
{
  "app_name": "SahaBot2",
  "version": "2.0.0",
  "maintenance_mode": false
}
```

**Rate Limit**: 120/minute  
**Authentication**: None

---

### GET /api/organizations/{org_id}/settings
**Purpose**: Get organization-specific settings

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization members

---

## Presets

### POST /api/organizations/{org_id}/preset-namespaces
**Purpose**: Create preset namespace

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### GET /api/organizations/{org_id}/preset-namespaces
**Purpose**: List preset namespaces

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization members

---

### GET /api/preset-namespaces/{namespace_id}/presets
**Purpose**: List presets in namespace

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Namespace members

---

### POST /api/preset-namespaces/{namespace_id}/presets
**Purpose**: Create randomizer preset

**Parameters**:
- `name` (body, string): Preset name
- `randomizer` (body, string): Randomizer type (alttpr, ootr, sm, etc.)
- `config` (body, object): Randomizer configuration

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Namespace managers

---

### GET /api/presets/{preset_id}
**Purpose**: Get preset details

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Namespace members

---

### PATCH /api/presets/{preset_id}
**Purpose**: Update preset

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Namespace managers

---

### DELETE /api/presets/{preset_id}
**Purpose**: Delete preset

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Namespace managers

---

### POST /api/presets/{preset_id}/generate-seed
**Purpose**: Generate seed using preset

**Response**:
```json
{
  "seed_url": "https://alttpr.com/en/randomizer?seed=12345",
  "seed_hash": "Triforce-Agh-Agahnim",
  "generated_at": "2025-11-04T12:00:00Z"
}
```

**Rate Limit**: 120/minute  
**Authentication**: Required  
**Authorization**: Namespace members

---

## Race Room Profiles

### POST /api/organizations/{org_id}/race-room-profiles
**Purpose**: Create race room template

**Parameters**:
- `name` (body, string): Profile name
- `category` (body, string): RaceTime category
- `goal` (body, string): Race goal
- `settings` (body, object): Additional settings

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### GET /api/organizations/{org_id}/race-room-profiles
**Purpose**: List race room profiles

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization members

---

### PATCH /api/race-room-profiles/{profile_id}
**Purpose**: Update profile

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### DELETE /api/race-room-profiles/{profile_id}
**Purpose**: Delete profile

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

## Scheduled Tasks

### POST /api/organizations/{org_id}/scheduled-tasks
**Purpose**: Create scheduled task

**Parameters**:
- `name` (body, string): Task name
- `task_type` (body, int): Task type (RACETIME_OPEN_ROOM, etc.)
- `schedule_type` (body, int): INTERVAL, CRON, or ONE_TIME
- `task_config` (body, object): Task configuration

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### GET /api/organizations/{org_id}/scheduled-tasks
**Purpose**: List scheduled tasks

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### GET /api/scheduled-tasks/{task_id}
**Purpose**: Get task details

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### PATCH /api/scheduled-tasks/{task_id}
**Purpose**: Update task

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### DELETE /api/scheduled-tasks/{task_id}
**Purpose**: Delete task

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

### POST /api/scheduled-tasks/{task_id}/run-now
**Purpose**: Execute task immediately (bypass schedule)

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Organization managers

---

## API Tokens

### POST /api/tokens
**Purpose**: Create new API token

**Parameters**:
- `name` (body, string): Token name
- `expires_at` (body, datetime, optional): Expiration date

**Response**:
```json
{
  "token": "sk_live_abc123def456...",
  "name": "CI Pipeline",
  "created_at": "2025-11-04T12:00:00Z",
  "expires_at": "2026-11-04T12:00:00Z"
}
```

**Note**: Token string only shown once

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: User's own tokens

---

### GET /api/tokens
**Purpose**: List user's API tokens (metadata only, not plaintext)

**Response**:
```json
{
  "tokens": [
    {
      "id": 1,
      "name": "CI Pipeline",
      "created_at": "2025-11-04T12:00:00Z",
      "expires_at": "2026-11-04T12:00:00Z"
    }
  ]
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: User's own tokens

---

### GET /api/tokens/{token_id}
**Purpose**: Get token metadata

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: User's own tokens

---

### DELETE /api/tokens/{token_id}
**Purpose**: Revoke API token

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: User's own tokens

---

## Admin

### GET /api/admin/stats
**Purpose**: Application statistics (superadmin only)

**Response**:
```json
{
  "total_users": 150,
  "total_organizations": 25,
  "total_tournaments": 75,
  "api_calls_today": 5000,
  "active_tasks": 12
}
```

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Superadmins only

---

### GET /api/admin/users
**Purpose**: List all users (superadmin only)

**Parameters**:
- `page` (query, int): Pagination
- `search` (query, string, optional): Search by username

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Superadmins only

---

### POST /api/admin/maintenance
**Purpose**: Enable/disable maintenance mode

**Parameters**:
- `enabled` (body, bool): Maintenance mode state

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Superadmins only

---

### GET /api/admin/audit-logs
**Purpose**: View audit logs

**Parameters**:
- `days` (query, int, default 7): Days to look back
- `action` (query, string, optional): Filter by action

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Superadmins only

---

### POST /api/admin/backup
**Purpose**: Trigger database backup

**Rate Limit**: 60/minute  
**Authentication**: Required  
**Authorization**: Superadmins only

---

## Authentication

All authenticated endpoints accept Bearer tokens in the `Authorization` header:

```bash
curl -H "Authorization: Bearer sk_live_abc123..." https://api.example.com/api/users/@me
```

## Rate Limiting

**Default**: 60 requests/minute per user per endpoint  
**Public endpoints**: 120 requests/minute  
**Admin endpoints**: 30 requests/minute  
**High-traffic endpoints**: May have lower limits

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699099200
```

## Error Responses

All endpoints return consistent error format:

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "User does not have permission to access this resource",
    "details": {}
  }
}
```

**Common error codes**:
- `UNAUTHORIZED` (401) - Authentication required or permission denied
- `NOT_FOUND` (404) - Resource not found
- `VALIDATION_ERROR` (422) - Request data invalid
- `RATE_LIMIT_EXCEEDED` (429) - Too many requests
- `INTERNAL_ERROR` (500) - Server error

## Webhook Events

Some endpoints support webhooks for event notifications. See integration documentation for details.

---

## See Also

- [SERVICES_REFERENCE.md](SERVICES_REFERENCE.md) - Service layer documentation
- [DATABASE_MODELS_REFERENCE.md](DATABASE_MODELS_REFERENCE.md) - Data model documentation
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
