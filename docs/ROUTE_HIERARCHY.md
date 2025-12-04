# SahaBot2 Route Hierarchy

This document provides a comprehensive overview of all routes in the SahaBot2 application, including both UI pages (NiceGUI) and REST API endpoints (FastAPI).

**Last Updated**: December 4, 2025 (Dedicated routes, no dynamic view parameters)

> **⚠️ Important**: This document must be kept up-to-date whenever routes are added, removed, or modified. When making changes to routes:
> - **Adding routes**: Add the new route to the appropriate section
> - **Removing routes**: Remove the route from this document
> - **Changing paths**: Update the path in the corresponding table
> - **Update the "Last Updated" date** at the top of this file

---

## Table of Contents

- [UI Routes (NiceGUI Pages)](#ui-routes-nicegui-pages)
  - [Public Routes](#public-routes)
  - [Authentication Routes](#authentication-routes)
  - [User Routes](#user-routes)
  - [Admin Routes](#admin-routes)
  - [Organization Routes](#organization-routes)
  - [Tournament Routes](#tournament-routes)
  - [Async Qualifier Routes](#async-tournament-routes)
  - [OAuth Callback Routes](#oauth-callback-routes)
- [REST API Routes (FastAPI)](#rest-api-routes-fastapi)
  - [Health & Monitoring](#health--monitoring)
  - [Users](#users)
  - [Organizations](#organizations)
  - [Tournaments](#tournaments)
  - [Async Qualifiers](#async-tournaments)
  - [Settings & Configuration](#settings--configuration)
  - [External Integrations](#external-integrations)
  - [System Administration](#system-administration)

---

## UI Routes (NiceGUI Pages)

### Public Routes

Routes accessible without authentication.

| Route | Description | File |
|-------|-------------|------|
| `/` | Home page - shows welcome for guests, dashboard for authenticated users | `pages/home.py` |
| `/presets` | Public presets view | `pages/home.py` |
| `/organizations` | Organizations landing (public view) | `pages/home.py` |
| `/privacy` | Privacy policy page | `pages/privacy.py` |
| `/invite/{slug}` | Organization invitation acceptance page | `pages/invite.py` |

### Authentication Routes

Routes for OAuth2 authentication flow.

| Route | Description | File |
|-------|-------------|------|
| `/auth/login` | Initiate Discord OAuth2 login | `pages/auth.py` |
| `/auth/callback` | Discord OAuth2 callback handler | `pages/auth.py` |
| `/auth/logout` | Logout and clear session | `pages/auth.py` |

### User Routes

Routes for authenticated users to manage their profile and settings.

| Route | Description | File |
|-------|-------------|------|
| `/profile` | Profile overview | `pages/user_profile.py` |
| `/profile/settings` | Profile settings | `pages/user_profile.py` |
| `/profile/notifications` | Notification preferences | `pages/user_profile.py` |
| `/profile/api-keys` | API key management | `pages/user_profile.py` |
| `/profile/organizations` | Organization memberships | `pages/user_profile.py` |
| `/profile/preset-namespaces` | Preset namespace management | `pages/user_profile.py` |
| `/profile/racetime` | RaceTime.gg account linking | `pages/user_profile.py` |
| `/profile/twitch` | Twitch account linking | `pages/user_profile.py` |
| `/profile/racer-verification` | Racer verification status | `pages/user_profile.py` |

### Admin Routes

Routes for system administrators (requires ADMIN or SUPERADMIN permission).

| Route | Description | File |
|-------|-------------|------|
| `/admin` | Admin overview | `pages/admin.py` |
| `/admin/users` | User management | `pages/admin.py` |
| `/admin/organizations` | Organization management | `pages/admin.py` |
| `/admin/org-requests` | Organization creation requests | `pages/admin.py` |
| `/admin/racetime-bots` | RaceTime bot management | `pages/admin.py` |
| `/admin/presets` | Randomizer preset management | `pages/admin.py` |
| `/admin/namespaces` | Preset namespace management | `pages/admin.py` |
| `/admin/scheduled-tasks` | Global scheduled tasks | `pages/admin.py` |
| `/admin/audit-logs` | System-wide audit logs | `pages/admin.py` |
| `/admin/logs` | Application logs viewer | `pages/admin.py` |
| `/admin/settings` | Application settings | `pages/admin.py` |

### Organization Routes

Routes for organization members and administrators.

| Route | Description | File |
|-------|-------------|------|
| `/org/{organization_id}` | Organization overview page | `pages/tournaments.py` |
| `/org/{organization_id}/tournament` | Organization tournament list | `pages/tournaments.py` |
| `/org/{organization_id}/tournament/my-matches` | Player matches in organization | `pages/tournaments.py` |
| `/org/{organization_id}/tournament/my-settings` | Tournament settings for player | `pages/tournaments.py` |

**Organization Administration**:

| Route | Description | File |
|-------|-------------|------|
| `/orgs/{organization_id}/admin` | Organization admin overview | `pages/organization_admin.py` |
| `/orgs/{organization_id}/admin/members` | Member management | `pages/organization_admin.py` |
| `/orgs/{organization_id}/admin/permissions` | Permission management | `pages/organization_admin.py` |
| `/orgs/{organization_id}/admin/settings` | Organization settings | `pages/organization_admin.py` |
| `/orgs/{organization_id}/admin/tournaments` | Tournament management | `pages/organization_admin.py` |
| `/orgs/{organization_id}/admin/async-qualifiers` | Async qualifier management | `pages/organization_admin.py` |
| `/orgs/{organization_id}/admin/stream-channels` | Stream channel configuration | `pages/organization_admin.py` |
| `/orgs/{organization_id}/admin/scheduled-tasks` | Organization scheduled tasks | `pages/organization_admin.py` |
| `/orgs/{organization_id}/admin/discord-servers` | Discord server integration | `pages/organization_admin.py` |
| `/orgs/{organization_id}/admin/race-room-profiles` | RaceTime room profile management | `pages/organization_admin.py` |
| `/orgs/{organization_id}/admin/racer-verification` | Racer verification configuration | `pages/organization_admin.py` |
| `/orgs/{organization_id}/admin/audit-logs` | Organization audit logs | `pages/organization_admin.py` |

### Tournament Routes

Routes for tournament management and viewing.

| Route | Description | File |
|-------|-------------|------|
| `/org/{organization_id}/tournament/{tournament_id}/admin` | Tournament admin overview | `pages/tournament_admin.py` |
| `/org/{organization_id}/tournament/{tournament_id}/admin/players` | Player management | `pages/tournament_admin.py` |
| `/org/{organization_id}/tournament/{tournament_id}/admin/racetime` | RaceTime settings | `pages/tournament_admin.py` |
| `/org/{organization_id}/tournament/{tournament_id}/admin/discord-events` | Discord event integration | `pages/tournament_admin.py` |
| `/org/{organization_id}/tournament/{tournament_id}/admin/randomizer-settings` | Randomizer configuration | `pages/tournament_admin.py` |
| `/org/{organization_id}/tournament/{tournament_id}/admin/preset-rules` | Preset selection rules | `pages/tournament_admin.py` |
| `/org/{organization_id}/tournament/{tournament_id}/admin/settings` | Tournament settings | `pages/tournament_admin.py` |
| `/tournaments/matches/{match_id}/submit` | Match settings submission page | `pages/tournament_match_settings.py` |

### Async Qualifier Routes

Routes for asynchronous qualifier management.

**Async Qualifier List**:

| Route | Description | File |
|-------|-------------|------|
| `/org/{organization_id}/async` | Organization async qualifier list | `pages/async_qualifiers.py` |
| `/org/{organization_id}/async/{tournament_id}` | Async qualifier dashboard | `pages/async_qualifiers.py` |
| `/org/{organization_id}/async/{tournament_id}/leaderboard` | Qualifier leaderboard | `pages/async_qualifiers.py` |
| `/org/{organization_id}/async/{tournament_id}/pools` | Qualifier pools | `pages/async_qualifiers.py` |
| `/org/{organization_id}/async/{tournament_id}/player/{player_id}` | Player profile in qualifier | `pages/async_qualifiers.py` |
| `/org/{organization_id}/async/{tournament_id}/permalink/{permalink_id}` | Permalink to specific race result | `pages/async_qualifiers.py` |
| `/org/{organization_id}/async/{tournament_id}/review` | Race review interface | `pages/async_qualifiers.py` |

**Async Qualifier Administration**:

| Route | Description | File |
|-------|-------------|------|
| `/org/{organization_id}/async/{qualifier_id}/admin` | Async qualifier admin overview | `pages/async_qualifier_admin.py` |
| `/org/{organization_id}/async/{qualifier_id}/admin/{view}` | Async qualifier admin view | `pages/async_qualifier_admin.py` |

### OAuth Callback Routes

Routes for external OAuth2 integrations.

| Route | Description | File |
|-------|-------------|------|
| `/racetime/link/initiate` | Initiate RaceTime.gg OAuth2 flow | `pages/racetime_oauth.py` |
| `/racetime/link/callback` | RaceTime.gg OAuth2 callback | `pages/racetime_oauth.py` |
| `/twitch/link/initiate` | Initiate Twitch OAuth2 flow | `pages/twitch_oauth.py` |
| `/twitch/link/callback` | Twitch OAuth2 callback | `pages/twitch_oauth.py` |
| `/discord-guild/callback` | Discord guild OAuth2 callback | `pages/discord_guild_callback.py` |

---

## REST API Routes (FastAPI)

All API routes are prefixed with `/api` and return JSON responses.

### Health & Monitoring

| Method | Route | Description | File |
|--------|-------|-------------|------|
| GET | `/api/health` | Health check endpoint | `api/routes/health.py` |

### Users

Base path: `/api/users`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List all users (admin only) | Yes | `api/routes/users.py` |
| GET | `/me` | Get current user profile | Yes | `api/routes/users.py` |
| GET | `/{user_id}` | Get specific user by ID | Yes | `api/routes/users.py` |
| POST | `/{user_id}/impersonate` | Start impersonating a user (superadmin only) | Yes | `api/routes/users.py` |
| POST | `/stop-impersonation` | Stop impersonating | Yes | `api/routes/users.py` |

### Organizations

Base path: `/api/organizations`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List all organizations | Yes | `api/routes/organizations.py` |
| POST | `/` | Create new organization | Yes | `api/routes/organizations.py` |
| GET | `/{organization_id}` | Get organization details | Yes | `api/routes/organizations.py` |
| PATCH | `/{organization_id}` | Update organization | Yes | `api/routes/organizations.py` |
| DELETE | `/{organization_id}` | Delete organization | Yes | `api/routes/organizations.py` |
| GET | `/{organization_id}/members` | List organization members | Yes | `api/routes/organizations.py` |
| POST | `/{organization_id}/members` | Add member to organization | Yes | `api/routes/organizations.py` |
| DELETE | `/{organization_id}/members/{user_id}` | Remove member | Yes | `api/routes/organizations.py` |

### Tournaments

Base path: `/api/tournaments`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List tournaments | Yes | `api/routes/tournaments.py` |
| POST | `/` | Create tournament | Yes | `api/routes/tournaments.py` |
| GET | `/{tournament_id}` | Get tournament details | Yes | `api/routes/tournaments.py` |
| PATCH | `/{tournament_id}` | Update tournament | Yes | `api/routes/tournaments.py` |
| DELETE | `/{tournament_id}` | Delete tournament | Yes | `api/routes/tournaments.py` |
| GET | `/{tournament_id}/players` | List tournament players | Yes | `api/routes/tournaments.py` |
| POST | `/{tournament_id}/players` | Add player to tournament | Yes | `api/routes/tournaments.py` |

**Tournament Settings**:

Base path: `/api/tournaments/settings`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/{tournament_id}` | Get tournament settings | Yes | `api/routes/tournament_match_settings.py` |
| PUT | `/{tournament_id}` | Update tournament settings | Yes | `api/routes/tournament_match_settings.py` |

### Async Qualifiers

Base path: `/api/async-tournaments`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List Async Qualifiers | Yes | `api/routes/async_tournaments.py` |
| POST | `/` | Create Async Qualifier | Yes | `api/routes/async_tournaments.py` |
| GET | `/{tournament_id}` | Get Async Qualifier details | Yes | `api/routes/async_tournaments.py` |
| PATCH | `/{tournament_id}` | Update Async Qualifier | Yes | `api/routes/async_tournaments.py` |
| DELETE | `/{tournament_id}` | Delete Async Qualifier | Yes | `api/routes/async_tournaments.py` |

**Async Qualifiers**:

Base path: `/api/async-qualifiers`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List async qualifiers | Yes | `api/routes/async_tournaments.py` |
| POST | `/` | Create async qualifier | Yes | `api/routes/async_tournaments.py` |
| GET | `/{qualifier_id}` | Get qualifier details | Yes | `api/routes/async_tournaments.py` |
| PATCH | `/{qualifier_id}` | Update qualifier | Yes | `api/routes/async_tournaments.py` |

**Async Live Races**:

Base path: `/api/async-live-races`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List live races | Yes | `api/routes/async_live_races.py` |
| GET | `/{race_id}` | Get race details | Yes | `api/routes/async_live_races.py` |
| POST | `/{race_id}/submit` | Submit race result | Yes | `api/routes/async_live_races.py` |

### Settings & Configuration

**Application Settings**:

Base path: `/api/settings`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | Get application settings | Yes (Admin) | `api/routes/settings.py` |
| PATCH | `/` | Update application settings | Yes (Admin) | `api/routes/settings.py` |

**Randomizer Presets**:

Base path: `/api/presets`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List presets | Yes | `api/routes/presets.py` |
| POST | `/` | Create preset | Yes | `api/routes/presets.py` |
| GET | `/{preset_id}` | Get preset details | Yes | `api/routes/presets.py` |
| PATCH | `/{preset_id}` | Update preset | Yes | `api/routes/presets.py` |
| DELETE | `/{preset_id}` | Delete preset | Yes | `api/routes/presets.py` |

**Stream Channels**:

Base path: `/api/stream-channels`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List stream channels | Yes | `api/routes/stream_channels.py` |
| POST | `/` | Create stream channel | Yes | `api/routes/stream_channels.py` |
| GET | `/{channel_id}` | Get channel details | Yes | `api/routes/stream_channels.py` |
| PATCH | `/{channel_id}` | Update channel | Yes | `api/routes/stream_channels.py` |
| DELETE | `/{channel_id}` | Delete channel | Yes | `api/routes/stream_channels.py` |

**Race Room Profiles**:

Base path: `/api/race-room-profiles` (defined in `api/routes/race_room_profiles.py`)

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List race room profiles | Yes | `api/routes/race_room_profiles.py` |
| POST | `/` | Create race room profile | Yes | `api/routes/race_room_profiles.py` |
| GET | `/{profile_id}` | Get profile details | Yes | `api/routes/race_room_profiles.py` |
| PATCH | `/{profile_id}` | Update profile | Yes | `api/routes/race_room_profiles.py` |
| DELETE | `/{profile_id}` | Delete profile | Yes | `api/routes/race_room_profiles.py` |

### External Integrations

**RaceTime.gg**:

Base path: `/api/racetime`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | Get RaceTime integration status | Yes | `api/routes/racetime.py` |
| POST | `/link` | Link RaceTime account | Yes | `api/routes/racetime.py` |
| DELETE | `/unlink` | Unlink RaceTime account | Yes | `api/routes/racetime.py` |

**RaceTime Bots**:

Base path: `/api/racetime-bots`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List RaceTime bots | Yes (Admin) | `api/routes/racetime.py` |
| POST | `/` | Register RaceTime bot | Yes (Admin) | `api/routes/racetime.py` |

**Twitch**:

Base path: `/api/twitch`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | Get Twitch integration status | Yes | `api/routes/twitch.py` |
| POST | `/link` | Link Twitch account | Yes | `api/routes/twitch.py` |
| DELETE | `/unlink` | Unlink Twitch account | Yes | `api/routes/twitch.py` |

**Discord Guilds**:

Base path: `/api/discord-guilds`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List Discord guilds | Yes | `api/routes/discord_guilds.py` |
| POST | `/` | Link Discord guild | Yes | `api/routes/discord_guilds.py` |
| GET | `/{guild_id}` | Get guild details | Yes | `api/routes/discord_guilds.py` |
| DELETE | `/{guild_id}` | Unlink guild | Yes | `api/routes/discord_guilds.py` |

**Discord Scheduled Events**:

Base path: `/api/discord-events`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List Discord events | Yes | `api/routes/discord_scheduled_events.py` |
| POST | `/` | Create Discord event | Yes | `api/routes/discord_scheduled_events.py` |
| GET | `/{event_id}` | Get event details | Yes | `api/routes/discord_scheduled_events.py` |
| PATCH | `/{event_id}` | Update event | Yes | `api/routes/discord_scheduled_events.py` |
| DELETE | `/{event_id}` | Delete event | Yes | `api/routes/discord_scheduled_events.py` |

### System Administration

**API Tokens**:

Base path: `/api/tokens`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List user's API tokens | Yes | `api/routes/tokens.py` |
| POST | `/` | Create API token | Yes | `api/routes/tokens.py` |
| DELETE | `/{token_id}` | Revoke API token | Yes | `api/routes/tokens.py` |

**Scheduled Tasks**:

Base path: `/api/scheduled-tasks`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List scheduled tasks | Yes | `api/routes/scheduled_tasks.py` |
| POST | `/` | Create scheduled task | Yes | `api/routes/scheduled_tasks.py` |
| GET | `/{task_id}` | Get task details | Yes | `api/routes/scheduled_tasks.py` |
| PATCH | `/{task_id}` | Update task | Yes | `api/routes/scheduled_tasks.py` |
| DELETE | `/{task_id}` | Delete task | Yes | `api/routes/scheduled_tasks.py` |

**Audit Logs**:

Base path: `/api/audit-logs`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List audit logs | Yes | `api/routes/audit_logs.py` |
| GET | `/{log_id}` | Get specific audit log entry | Yes | `api/routes/audit_logs.py` |

**Invites**:

Base path: `/api/invites`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List invites | Yes | `api/routes/invites.py` |
| POST | `/` | Create invite | Yes | `api/routes/invites.py` |
| GET | `/{invite_id}` | Get invite details | Yes | `api/routes/invites.py` |
| DELETE | `/{invite_id}` | Revoke invite | Yes | `api/routes/invites.py` |

**UI Authorization**:

Base path: `/api/ui-auth`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/permissions` | Get current user's UI permissions | Yes | `api/routes/ui_authorization.py` |

---

## Route Conventions

### UI Routes (NiceGUI)

1. **View-based routing**: Pages with multiple sections use path-based view routing:
   - Base route: `/page`
   - With view: `/page/{view}`
   - Example: `/admin` (default view) vs `/admin/users` (specific view)

2. **Organization scoping**: Organization-specific routes use `/org/{organization_id}` or `/orgs/{organization_id}` prefix
   - `/org/{id}` - Public organization pages
   - `/orgs/{id}/admin` - Organization administration

3. **Tournament routing**: Follows organization hierarchy
   - Regular tournaments: `/org/{org_id}/tournament/{tournament_id}`
   - Async Qualifiers: `/org/{org_id}/async/{tournament_id}`

### API Routes (FastAPI)

1. **RESTful conventions**: Standard REST verbs for CRUD operations
   - GET - Retrieve resource(s)
   - POST - Create resource
   - PATCH - Partial update
   - PUT - Full update
   - DELETE - Remove resource

2. **Nested resources**: Related resources follow hierarchical paths
   - Example: `/api/organizations/{org_id}/members`

3. **Authentication**: Most API endpoints require authentication via:
   - Session cookie (for web UI)
   - API token (for programmatic access)

4. **Authorization**: Permission checks enforced in service layer, not at route level

---

## Notes

- All routes are case-sensitive
- API routes return JSON responses with consistent error formatting
- UI routes may redirect to login if authentication is required
- Path parameters are always integers for IDs
- View parameters are string slugs (kebab-case)

For more information on routing patterns and conventions, see [PATTERNS.md](PATTERNS.md).
