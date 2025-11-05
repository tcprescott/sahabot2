# Services Reference

Complete reference for all 33 services in SahaBot2, organized by domain.

**Last Updated**: November 4, 2025  
**Coverage**: 33/33 services documented

---

## Table of Contents

- [User Management (3)](#user-management)
- [Organizations (5)](#organizations)
- [Tournaments (3)](#tournaments)
- [API & Tokens (2)](#api--tokens)
- [Discord Integration (3)](#discord-integration)
- [RaceTime Integration (3)](#racetime-integration)
- [Streams & Presets (4)](#streams--presets)
- [Notifications (3)](#notifications)
- [Randomizers (6)](#randomizers)
- [Infrastructure (1)](#infrastructure)

---

## User Management

### UserService
**File**: `application/services/user_service.py`

**Purpose**: User account management, authentication, and permission updates.

**Key Methods**:
- `get_user(user_id)` - Fetch user by ID
- `get_by_discord_id(discord_id)` - Find user by Discord ID
- `create_user(discord_id, username)` - Create new user
- `update_user_permission(user_id, permission)` - Change global permission
- `list_all_users()` - Get all users (admin only)

**Authorization**: Public methods check permissions; admins only for sensitive ops  
**Multi-tenant**: No (global user registry)  
**Events Emitted**: `UserCreatedEvent`, `UserPermissionChangedEvent`

**Usage Example**:
```python
from application.services.user_service import UserService

service = UserService()
user = await service.get_user(user_id=123)
updated = await service.update_user_permission(user_id=123, permission=Permission.ADMIN, current_user=admin)
```

---

### AuthorizationService
**File**: `application/services/authorization_service.py`

**Purpose**: Permission and authorization checking (separate from business logic).

**Key Methods**:
- `is_superadmin(user)` - Check global superadmin status
- `is_admin(user)` - Check admin or superadmin status
- `can_access_admin_panel(user)` - Admin panel access
- `is_member(user, organization_id)` - Org membership check
- `can_manage_users(user, org_id)` - User management permission
- `can_manage_tournaments(user, org_id)` - Tournament management permission

**Authorization**: N/A (this IS the authorization service)  
**Multi-tenant**: Yes (org-scoped checks)  
**Events Emitted**: None

**Usage Example**:
```python
from application.services.authorization_service import AuthorizationService

auth_z = AuthorizationService()
if auth_z.is_superadmin(user):
    # Allow access
    pass
if auth_z.is_member(user, org_id):
    # User is org member
    pass
```

---

### AuditService
**File**: `application/services/audit_service.py`

**Purpose**: Logging user actions and changes for compliance and debugging.

**Key Methods**:
- `log_action(user, action, details, org_id=None)` - Log user action
- `get_audit_logs(limit=100, offset=0, org_id=None)` - Retrieve logs
- `get_logs_by_user(user_id, limit=100)` - Logs for specific user
- `get_logs_by_action(action, limit=100)` - Logs of specific action type

**Authorization**: Admins/superadmins only  
**Multi-tenant**: Yes (logs scoped by org)  
**Events Emitted**: None (creates audit log entries directly)

**Usage Example**:
```python
from application.services.audit_service import AuditService

audit = AuditService()
await audit.log_action(
    user=current_user,
    action="user_created",
    details={"user_id": new_user.id, "email": new_user.discord_email},
    org_id=org_id
)
```

---

## Organizations

### OrganizationService
**File**: `application/services/organization_service.py`

**Purpose**: Organization (tenant) CRUD operations and permission management.

**Key Methods**:
- `create_organization(name, description, current_user)` - Create org
- `get_organization(org_id, current_user)` - Get org details
- `update_organization(org_id, updates, current_user)` - Update org
- `delete_organization(org_id, current_user)` - Delete org
- `add_member(org_id, user_id, current_user)` - Add org member
- `remove_member(org_id, user_id, current_user)` - Remove member
- `grant_permission(org_id, user_id, permission, current_user)` - Grant permission
- `list_organization_members(org_id, current_user)` - List members

**Authorization**: Create (any user), manage (org managers)  
**Multi-tenant**: Yes (each org is a tenant)  
**Events Emitted**: `OrganizationCreatedEvent`, `OrganizationUpdatedEvent`, `OrganizationMemberAddedEvent`, `OrganizationMemberPermissionChangedEvent`

**Usage Example**:
```python
service = OrganizationService()
org = await service.create_organization(
    name="My Racing League",
    description="We race games",
    current_user=user
)
await service.add_member(org_id=org.id, user_id=friend_id, current_user=user)
```

---

### OrganizationInviteService
**File**: `application/services/organization_invite_service.py`

**Purpose**: Generate and manage organization invitation links.

**Key Methods**:
- `create_invite(org_id, created_by)` - Generate new invite link
- `get_invite(code)` - Get invite details by code
- `accept_invite(code, current_user)` - Accept invite and join org
- `revoke_invite(code, current_user)` - Revoke invite link
- `list_invites(org_id, current_user)` - List org's invites

**Authorization**: Org managers can create/revoke; anyone can accept  
**Multi-tenant**: Yes (org-scoped)  
**Events Emitted**: `InviteCreatedEvent`, `InviteAcceptedEvent`

**Usage Example**:
```python
service = OrganizationInviteService()
invite = await service.create_invite(org_id=1, created_by=user)
print(f"Share this code: {invite.code}")
await service.accept_invite(code=invite.code, current_user=new_member)
```

---

### OrganizationRequestService
**File**: `application/services/organization_request_service.py`

**Purpose**: Handle organization creation requests (if org creation is gated).

**Key Methods**:
- `create_request(name, description, current_user)` - Submit org creation request
- `get_request(request_id)` - Get request details
- `approve_request(request_id, current_user)` - Approve (creates org)
- `reject_request(request_id, reason, current_user)` - Reject request
- `list_pending_requests(current_user)` - List pending requests

**Authorization**: Superadmins approve/reject  
**Multi-tenant**: No (global admin feature)  
**Events Emitted**: Organization events (when approved)

---

### SettingsService
**File**: `application/services/settings_service.py`

**Purpose**: Manage global and organization-scoped configuration settings.

**Key Methods**:
- `get_setting(key, default=None, org_id=None)` - Get setting value
- `set_setting(key, value, org_id=None, current_user)` - Update setting
- `delete_setting(key, org_id=None, current_user)` - Delete setting
- `list_settings(org_id=None)` - List all settings

**Authorization**: Superadmins (global), org managers (org-scoped)  
**Multi-tenant**: Yes (supports global and org-scoped)  
**Events Emitted**: None

**Usage Example**:
```python
service = SettingsService()
# Global setting
max_tournaments = await service.get_setting("max_tournaments_per_org", default=10)
# Org setting
await service.set_setting("tournament_timeout", 3600, org_id=1, current_user=admin)
```

---

### PresetNamespaceService
**File**: `application/services/preset_namespace_service.py`

**Purpose**: Manage preset namespaces (groupings for organizing presets).

**Key Methods**:
- `create_namespace(org_id, name, description, current_user)` - Create namespace
- `get_namespace(namespace_id, current_user)` - Get namespace
- `update_namespace(namespace_id, updates, current_user)` - Update
- `delete_namespace(namespace_id, current_user)` - Delete
- `list_namespaces(org_id, current_user)` - List org's namespaces
- `grant_namespace_permission(namespace_id, user_id, permission, current_user)` - Delegate access

**Authorization**: Org managers  
**Multi-tenant**: Yes (org-scoped)  
**Events Emitted**: None

---

## Tournaments

### TournamentService
**File**: `application/services/tournament_service.py`

**Purpose**: Traditional tournament management (races, crews, scheduling).

**Key Methods**:
- `create_tournament(org_id, name, description, current_user)` - Create tournament
- `get_tournament(tournament_id, current_user)` - Get details
- `update_tournament(tournament_id, updates, current_user)` - Update
- `delete_tournament(tournament_id, current_user)` - Delete
- `add_crew(tournament_id, user_id, role, current_user)` - Add crew member
- `remove_crew(tournament_id, user_id, current_user)` - Remove crew
- `assign_discord_channel(tournament_id, channel_id, current_user)` - Set Discord channel
- `list_tournaments(org_id, current_user)` - List org's tournaments

**Authorization**: Org members (view), managers (create/edit)  
**Multi-tenant**: Yes (org-scoped)  
**Events Emitted**: `TournamentCreatedEvent`, `CrewAddedEvent`, `MatchScheduledEvent`

**Usage Example**:
```python
service = TournamentService()
tournament = await service.create_tournament(
    org_id=1,
    name="Winter Classic 2025",
    description="Annual racing event",
    current_user=user
)
await service.add_crew(tournament_id=tournament.id, user_id=commentator_id, role="commentator", current_user=user)
```

---

### AsyncTournamentService
**File**: `application/services/async_tournament_service.py`

**Purpose**: Asynchronous tournament management (self-paced races).

**Key Methods**:
- `create_async_tournament(org_id, name, current_user)` - Create async tournament
- `get_async_tournament(tournament_id, current_user)` - Get details
- `update_async_tournament(tournament_id, updates, current_user)` - Update
- `add_pool(tournament_id, name, current_user)` - Create race pool
- `add_participant(tournament_id, user_id, current_user)` - Register participant
- `create_race(pool_id, seed_url, current_user)` - Create race
- `get_leaderboard(tournament_id)` - Get standings
- `list_async_tournaments(org_id, current_user)` - List org's async tournaments

**Authorization**: Org members (view), managers (create/edit)  
**Multi-tenant**: Yes (org-scoped)  
**Events Emitted**: Various race and tournament events

**Usage Example**:
```python
service = AsyncTournamentService()
tournament = await service.create_async_tournament(
    org_id=1,
    name="Spring Async League",
    current_user=user
)
pool = await service.add_pool(tournament_id=tournament.id, name="Week 1", current_user=user)
```

---

### AsyncLiveRaceService
**File**: `application/services/async_live_race_service.py`

**Purpose**: Manage live races within async tournaments (scheduled racetime rooms).

**Key Methods**:
- `create_live_race(tournament_id, pool_id, scheduled_at, current_user)` - Schedule live race
- `get_live_race(race_id, current_user)` - Get race details
- `update_live_race(race_id, updates, current_user)` - Update race
- `cancel_live_race(race_id, current_user)` - Cancel scheduled race
- `open_race_room(race_id)` - Create RaceTime room (background task)
- `get_eligible_participants(race_id)` - List who can race
- `list_live_races(tournament_id, current_user)` - List all live races

**Authorization**: Org managers  
**Multi-tenant**: Yes (tournament-scoped)  
**Events Emitted**: `RacetimeRoomCreatedEvent`, race completion events

---

## API & Tokens

### ApiTokenService
**File**: `application/services/api_token_service.py`

**Purpose**: Create and manage API tokens for programmatic authentication.

**Key Methods**:
- `create_token(user_id, name, expires_at)` - Generate new token
- `get_token(token_id, user_id)` - Get token metadata (not plaintext)
- `list_tokens(user_id)` - List user's tokens
- `revoke_token(token_id, user_id)` - Revoke token
- `validate_token(token_string)` - Verify token is valid

**Authorization**: Users manage their own tokens  
**Multi-tenant**: No (user-scoped)  
**Events Emitted**: None

**Usage Example**:
```python
service = ApiTokenService()
result = await service.create_token(
    user_id=user.id,
    name="CI/CD Pipeline",
    expires_at=datetime.now(timezone.utc) + timedelta(days=365)
)
print(f"Token: {result['token']}")  # Only shown once
```

---

### RateLimitService
**File**: `application/services/rate_limit_service.py`

**Purpose**: Enforce API rate limiting to prevent abuse.

**Key Methods**:
- `check_rate_limit(user_id, endpoint)` - Check if request allowed
- `get_limit_status(user_id, endpoint)` - Get current usage
- `reset_limit(user_id, endpoint)` - Manually reset limit

**Authorization**: System-wide  
**Multi-tenant**: Yes (limits per user per endpoint)  
**Events Emitted**: None

---

## Discord Integration

### DiscordService
**File**: `application/services/discord_service.py`

**Purpose**: Core Discord API interactions (messages, roles, channels).

**Key Methods**:
- `get_user_info(discord_id)` - Fetch user from Discord
- `send_dm(user_id, message)` - Send direct message
- `send_channel_message(channel_id, message)` - Send to channel
- `create_role(guild_id, name)` - Create Discord role
- `add_user_role(user_id, role_id)` - Assign role to user
- `get_guild_info(guild_id)` - Get server details

**Authorization**: System (bot account)  
**Multi-tenant**: No (operates on Discord side)  
**Events Emitted**: None

---

### DiscordGuildService
**File**: `application/services/discord_guild_service.py`

**Purpose**: Discord guild (server) configuration and permission management.

**Key Methods**:
- `register_guild(guild_id, org_id, current_user)` - Link guild to org
- `get_guild_config(guild_id)` - Get configuration
- `update_guild_config(guild_id, updates, current_user)` - Update settings
- `check_channel_permissions(channel_id)` - Verify bot permissions
- `set_event_channel(guild_id, channel_id, event_type, current_user)` - Assign event channel

**Authorization**: Guild admins  
**Multi-tenant**: Yes (guild can be linked to org)  
**Events Emitted**: None

**Usage Example**:
```python
service = DiscordGuildService()
warnings = await service.check_channel_permissions(channel_id)
if warnings:
    print(f"Permission issues: {warnings}")
```

---

### DiscordScheduledEventService
**File**: `application/services/discord_scheduled_event_service.py`

**Purpose**: Create and manage Discord scheduled events for tournaments.

**Key Methods**:
- `create_event(guild_id, name, scheduled_time, description, current_user)` - Create event
- `get_event(event_id)` - Get event details
- `update_event(event_id, updates, current_user)` - Update event
- `delete_event(event_id, current_user)` - Cancel event
- `list_events(guild_id)` - List guild's events

**Authorization**: Guild admins  
**Multi-tenant**: Yes (linked via guild)  
**Events Emitted**: None

---

## RaceTime Integration

### RacetimeBotService
**File**: `application/services/racetime_bot_service.py`

**Purpose**: Manage RaceTime.gg bot configurations and assignments.

**Key Methods**:
- `create_bot(username, auth_code, current_user)` - Register new bot
- `get_bot(bot_id)` - Get bot configuration
- `update_bot(bot_id, updates, current_user)` - Update settings
- `delete_bot(bot_id, current_user)` - Remove bot
- `assign_to_organization(bot_id, org_id, current_user)` - Link bot to org
- `list_bots(current_user)` - List all bots

**Authorization**: Superadmins  
**Multi-tenant**: No (bots can be assigned to orgs)  
**Events Emitted**: `RacetimeBotCreatedEvent`, `RacetimeBotDeletedEvent`

---

### RacetimeChatCommandService
**File**: `application/services/racetime_chat_command_service.py`

**Purpose**: Define and manage custom RaceTime chat commands.

**Key Methods**:
- `create_command(org_id, name, response, scope, current_user)` - Create command
- `get_command(command_id, current_user)` - Get details
- `update_command(command_id, updates, current_user)` - Update command
- `delete_command(command_id, current_user)` - Delete command
- `execute_command(command_name, context)` - Execute command in race
- `list_commands(org_id, scope)` - List org's commands

**Authorization**: Org managers  
**Multi-tenant**: Yes (org-scoped commands)  
**Events Emitted**: None

**Usage Example**:
```python
service = RacetimeChatCommandService()
cmd = await service.create_command(
    org_id=1,
    name="rules",
    response="Check our rules at: https://example.com/rules",
    scope=CommandScope.TOURNAMENT,
    current_user=user
)
```

---

### RacetimeRoomService
**File**: `application/services/racetime_room_service.py`

**Purpose**: Create and manage RaceTime.gg race rooms for tournaments.

**Key Methods**:
- `create_room(bot_id, category, goal, invitees, current_user)` - Create race room
- `get_room(room_id)` - Get room details
- `invite_user(room_id, user, current_user)` - Invite to room
- `send_room_message(room_id, message)` - Post in room chat
- `close_room(room_id, current_user)` - End race

**Authorization**: Org managers  
**Multi-tenant**: Yes (through bot assignment)  
**Events Emitted**: `RacetimeRoomCreatedEvent`

**Usage Example**:
```python
service = RacetimeRoomService()
room = await service.create_room(
    bot_id=bot.id,
    category="alttpr",
    goal="Beat the game",
    invitees=[user1_id, user2_id],
    current_user=organizer
)
print(f"Race room: {room.url}")
```

---

### RacetimeService
**File**: `application/services/racetime_service.py`

**Purpose**: General RaceTime.gg API client and utilities.

**Key Methods**:
- `get_race_info(room_url)` - Fetch race details
- `get_user_info(username)` - Get RaceTime user info
- `validate_category(category)` - Check if category exists
- `parse_seed_url(url)` - Extract seed info from URL

**Authorization**: Public (read-only mostly)  
**Multi-tenant**: No  
**Events Emitted**: None

---

## Streams & Presets

### StreamChannelService
**File**: `application/services/stream_channel_service.py`

**Purpose**: Manage stream channel configurations for tournaments.

**Key Methods**:
- `create_channel(org_id, name, twitch_url, current_user)` - Add stream channel
- `get_channel(channel_id, current_user)` - Get details
- `update_channel(channel_id, updates, current_user)` - Update
- `delete_channel(channel_id, current_user)` - Remove channel
- `list_channels(org_id, current_user)` - List org's channels
- `assign_to_tournament(channel_id, tournament_id, current_user)` - Link to tournament

**Authorization**: Org managers  
**Multi-tenant**: Yes (org-scoped)  
**Events Emitted**: None

---

### RaceRoomProfileService
**File**: `application/services/race_room_profile_service.py`

**Purpose**: Manage reusable RaceTime room configuration templates.

**Key Methods**:
- `create_profile(org_id, name, settings, current_user)` - Create template
- `get_profile(profile_id, current_user)` - Get template details
- `update_profile(profile_id, updates, current_user)` - Update template
- `delete_profile(profile_id, current_user)` - Delete template
- `use_profile(profile_id, current_user)` - Apply template to new room
- `list_profiles(org_id, current_user)` - List org's templates

**Authorization**: Org members (use), org managers (create/edit)  
**Multi-tenant**: Yes (org-scoped)  
**Events Emitted**: `PresetCreatedEvent`, `PresetUpdatedEvent`

**Usage Example**:
```python
service = RaceRoomProfileService()
profile = await service.create_profile(
    org_id=1,
    name="Standard ALTTPR",
    settings={"category": "alttpr", "goal": "Beat the game"},
    current_user=user
)
await service.use_profile(profile_id=profile.id, current_user=user)
```

---

### RandomizerPresetService
**File**: `application/services/randomizer_preset_service.py`

**Purpose**: Manage randomizer configuration presets.

**Key Methods**:
- `create_preset(namespace_id, name, randomizer, config, current_user)` - Create preset
- `get_preset(preset_id, current_user)` - Get details
- `update_preset(preset_id, updates, current_user)` - Update preset
- `delete_preset(preset_id, current_user)` - Delete preset
- `use_preset(preset_id, current_user)` - Apply preset
- `list_presets(namespace_id, current_user)` - List namespace's presets

**Authorization**: Namespace owner/delegates  
**Multi-tenant**: Yes (namespace-scoped)  
**Events Emitted**: None

---

### TournamentUsageService
**File**: `application/services/tournament_usage_service.py`

**Purpose**: Track and report tournament usage metrics and statistics.

**Key Methods**:
- `record_usage(tournament_id, metric, value)` - Log metric
- `get_usage_stats(tournament_id)` - Get tournament statistics
- `get_org_usage_summary(org_id)` - Organization-wide stats
- `export_usage_report(org_id, start_date, end_date)` - Generate report

**Authorization**: Org managers (their org), superadmins (all)  
**Multi-tenant**: Yes (org-scoped)  
**Events Emitted**: None

---

## Notifications

### NotificationService
**File**: `application/services/notification_service.py`

**Purpose**: Manage notification subscriptions and delivery.

**Key Methods**:
- `subscribe_user(user_id, event_type, method)` - Subscribe to event
- `unsubscribe_user(user_id, event_type, method)` - Unsubscribe
- `get_subscriptions(user_id)` - List user's subscriptions
- `queue_notification(user_id, event_type, data)` - Queue notification
- `get_notification_status(notification_id)` - Check delivery status

**Authorization**: Users manage their own subscriptions  
**Multi-tenant**: No (user-scoped)  
**Events Emitted**: None

**Usage Example**:
```python
service = NotificationService()
await service.subscribe_user(
    user_id=user.id,
    event_type=NotificationEventType.MATCH_SCHEDULED,
    method=NotificationMethod.DISCORD_DM
)
```

---

### NotificationProcessor
**File**: `application/services/notification_processor.py`

**Purpose**: Background service that processes and delivers queued notifications.

**Key Methods**:
- `start_processor()` - Begin background processing
- `stop_processor()` - Gracefully shut down
- `process_pending_notifications()` - Send queued notifications

**Authorization**: System (background service)  
**Multi-tenant**: Yes (processes all tenants)  
**Events Emitted**: None

---

### NotificationHandlers
**File**: `application/services/notification_handlers/`

**Purpose**: Per-channel notification delivery (Discord, Email, Webhook).

**Handlers**:
- `DiscordNotificationHandler` - Send Discord DM
- `EmailNotificationHandler` - Send email (placeholder)
- `WebhookNotificationHandler` - POST to webhook

**Methods** (per handler):
- `send(notification_id, recipient, message)` - Deliver notification
- `validate_recipient(recipient)` - Check recipient exists
- `on_error(error)` - Error handling/retry logic

---

## Randomizers

### RandomizerService
**File**: `application/services/randomizer/randomizer_service.py`

**Purpose**: Factory service for generating game seeds via various randomizer APIs.

**Key Methods**:
- `get_randomizer(name)` - Get randomizer instance
- `generate_seed(randomizer, config)` - Generate seed with config
- `list_available_randomizers()` - List supported games

**Supported Randomizers**: ALTTPR, ALTTPRShuffled, Z1R, OOTR, SM, FF, SMB3R, CTJets, Bingosync

**Authorization**: Public  
**Multi-tenant**: No  
**Events Emitted**: None

**Usage Example**:
```python
from application.services.randomizer import RandomizerService

service = RandomizerService()
alttpr_service = service.get_randomizer('alttpr')
result = await alttpr_service.generate(settings={'difficulty': 'hard'})
print(f"Seed: {result.seed_url}")
```

---

### ALTTPRService
**File**: `application/services/randomizer/alttpr_service.py`

**Purpose**: Generate A Link to the Past Randomizer seeds.

**Methods**:
- `generate(settings)` - Generate seed with settings
- `get_available_options()` - List configuration options

---

### SMService
**File**: `application/services/randomizer/sm_service.py`

**Purpose**: Generate Super Metroid randomizer seeds.

---

### OOTRService
**File**: `application/services/randomizer/ootr_service.py`

**Purpose**: Generate Ocarina of Time Randomizer seeds.

---

### BingosyncService
**File**: `application/services/randomizer/bingosync_service.py`

**Purpose**: Generate Bingosync bingo cards for various games.

**Methods**:
- `generate(room_name, passphrase, game_type, settings)` - Create bingo room
- `new_card(room_id, game_type)` - Generate new card in room

---

### CTJetsService
**File**: `application/services/randomizer/ctjets_service.py`

**Purpose**: Generate Chrono Trigger Jets of Time randomizer seeds.

---

### Other Randomizers
- `Z1RService`, `FFRService`, `SMB3RService`, `AOSRService` - Additional randomizers

---

## Infrastructure

### TaskSchedulerService
**File**: `application/services/task_scheduler_service.py`

**Purpose**: Schedule and execute background tasks (interval, cron, one-time).

**Key Methods**:
- `create_task(org_id, name, task_type, schedule_type, config, current_user)` - Schedule task
- `get_task(task_id, current_user)` - Get task details
- `update_task(task_id, updates, current_user)` - Update task
- `delete_task(task_id, current_user)` - Cancel task
- `list_tasks(org_id, current_user)` - List org's tasks
- `execute_builtin_task_now(task_id, current_user)` - Run task immediately

**Authorization**: Org managers  
**Multi-tenant**: Yes (org-scoped tasks)  
**Events Emitted**: Task execution events

**Usage Example**:
```python
service = TaskSchedulerService()
task = await service.create_task(
    org_id=1,
    name="Hourly Race",
    task_type=TaskType.RACETIME_OPEN_ROOM,
    schedule_type=ScheduleType.INTERVAL,
    config={"interval_seconds": 3600, "category": "alttpr"},
    current_user=user
)
```

---

## Service Layer Patterns

### Authorization Pattern
All services follow this pattern:
```python
async def do_something(self, param, current_user):
    # 1. Check permissions
    if not self.auth_service.can_do_something(current_user):
        return None  # Fail gracefully
    
    # 2. Business logic
    result = await self.repository.do_something(param)
    
    # 3. Audit & events
    await self.audit.log_action(...)
    await EventBus.emit(SomethingHappenedEvent(...))
    
    return result
```

### Multi-tenant Pattern
Organization-scoped services:
```python
async def get_items(self, org_id: int, current_user: User):
    # 1. Validate membership
    if not self.auth_service.is_member(current_user, org_id):
        return []
    
    # 2. Fetch with org filter
    return await self.repository.list_by_org(org_id)
```

### Error Handling
Services return `None` or empty list on authorization failure (fail gracefully, don't raise).

---

## Quick Lookup by Purpose

| Need | Service(s) |
|------|-----------|
| User management | UserService, AuthorizationService |
| Organization admin | OrganizationService, OrganizationInviteService |
| Tournaments | TournamentService, AsyncTournamentService, AsyncLiveRaceService |
| RaceTime integration | RacetimeRoomService, RacetimeBotService, RacetimeChatCommandService |
| Discord integration | DiscordService, DiscordGuildService, DiscordScheduledEventService |
| Seeds/randomizers | RandomizerService + individual randomizer services |
| Notifications | NotificationService, NotificationProcessor |
| Configuration | SettingsService, PresetNamespaceService, RaceRoomProfileService |
| Auditing | AuditService, TournamentUsageService |
| Background tasks | TaskSchedulerService |
| API authentication | ApiTokenService, RateLimitService |

---

## See Also

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Architecture overview
- [PATTERNS.md](../PATTERNS.md) - Service patterns and conventions
- [ADDING_FEATURES.md](../ADDING_FEATURES.md#new-service--repository) - Creating new services
