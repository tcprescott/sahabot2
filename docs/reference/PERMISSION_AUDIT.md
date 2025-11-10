# Permission System Audit - SahaBot2

**Last Updated**: November 5, 2025

This document provides a comprehensive audit of the permission system in SahaBot2, including global permissions, organization roles, and permission matrices.

## Table of Contents

1. [Global Permission Levels](#global-permission-levels)
2. [Organization Roles](#organization-roles)
3. [Built-in Role Groups](#built-in-role-groups)
4. [Service Layer Permission Checks](#service-layer-permission-checks)
5. [API Endpoint Authorization](#api-endpoint-authorization)
6. [Permission Matrix](#permission-matrix)

---

## Global Permission Levels

Global permissions are assigned to users at the system level and grant access across all organizations.

### Permission Enum Values

Defined in `models/user.py`:

| Permission | Value | Description | Hierarchy |
|------------|-------|-------------|-----------|
| `SUPERADMIN` | 100 | Full system access, can manage all organizations | Highest |
| `ADMIN` | 75 | Administrative access, can manage organizations and users | High |
| `MODERATOR` | 50 | Moderation capabilities, can moderate content | Medium |
| `USER` | 25 | Standard user, default permission level | Base |

### Permission Hierarchy

Permissions follow a hierarchical model where higher permissions include all lower permissions:

```
SUPERADMIN (100)
  └─ includes ADMIN (75)
      └─ includes MODERATOR (50)
          └─ includes USER (25)
```

**Example**:
- A user with `Permission.ADMIN` also has `Permission.MODERATOR` and `Permission.USER`
- A user with `Permission.USER` only has `Permission.USER`

### Global Permission Capabilities

#### SUPERADMIN
- Full access to all features across all organizations
- Can manage organization creation requests
- Can view and edit all user email addresses (PII)
- Can manage feature flags for organizations
- Can access all admin panels and tools
- Bypasses all organization-specific permission checks

#### ADMIN
- Can access admin panel
- Can manage users (view all, search, link/unlink RaceTime accounts)
- Can manage organizations (create, update, delete)
- Can manage RaceTime bots
- Can manage chat commands
- Can view organization requests
- Has access to most features across all organizations

#### MODERATOR
- Can moderate content
- Can view users
- Limited administrative capabilities

#### USER
- Base access level
- Can access user profile
- Can join organizations (if invited)
- Organization-specific permissions determined by roles

---

## Organization Roles

Organization roles are assigned to members within specific organizations and grant permissions scoped to that organization only.

### Organization Member Roles

Defined in `models/organizations.py`:

| Role Name | Permission Scope | Description |
|-----------|------------------|-------------|
| `ADMIN` | Organization-wide | Full control over organization |
| `MEMBER_MANAGER` | Member management | Can invite, remove, and manage member permissions |
| `TOURNAMENT_MANAGER` | Tournament management | Can create and manage tournaments |
| `ASYNC_REVIEWER` | Async race review | Can review and approve async race submissions |
| `CREW_APPROVER` | Crew approval | Can approve crew members for async qualifiers |
| `SCHEDULED_TASK_MANAGER` | Task scheduling | Can create and manage scheduled tasks |
| `RACE_ROOM_MANAGER` | RaceTime profiles | Can manage RaceTime room profiles |
| `LIVE_RACE_MANAGER` | Live race management | Can manage live race monitoring |

### Role Capabilities

#### ADMIN (Organization)
- Full control over organization settings
- Can manage members (invite, remove, change permissions)
- Can manage all tournaments (regular and async)
- Can review async races
- Can manage scheduled tasks
- Can manage RaceTime profiles
- Can manage live races
- Can manage Discord events

#### MEMBER_MANAGER
- Can invite users to organization
- Can remove members
- Can change member permissions
- Cannot manage organization settings

#### TOURNAMENT_MANAGER
- Can create tournaments
- Can update tournament settings
- Can delete tournaments
- Can manage tournament matches
- Can schedule matches

#### ASYNC_REVIEWER
- Can review async race submissions
- Can approve/reject race results
- Can view race VODs and verification data

#### CREW_APPROVER
- Can approve crew members for async qualifiers
- Can manage crew assignments

#### SCHEDULED_TASK_MANAGER
- Can create scheduled tasks
- Can update/delete tasks
- Can manage task schedules

#### RACE_ROOM_MANAGER
- Can create RaceTime room profiles
- Can update profile settings
- Can manage room configurations

#### LIVE_RACE_MANAGER
- Can enable/disable live race monitoring
- Can manage race room tracking
- Can view live race status

---

## Built-in Role Groups

Defined in `application/policies/built_in_roles.py`:

Built-in role groups provide convenient collections of roles for common permission sets.

### Available Built-in Role Groups

```python
from application.policies.built_in_roles import BuiltInRoles

# Organization Admin - Full organization control
BuiltInRoles.ORGANIZATION_ADMIN = [
    'ADMIN',
    'MEMBER_MANAGER',
    'TOURNAMENT_MANAGER',
    'ASYNC_REVIEWER',
    'CREW_APPROVER',
    'SCHEDULED_TASK_MANAGER',
    'RACE_ROOM_MANAGER',
    'LIVE_RACE_MANAGER'
]

# Tournament Manager - Tournament management only
BuiltInRoles.TOURNAMENT_MANAGER = [
    'TOURNAMENT_MANAGER'
]

# Async Reviewer - Review async race submissions
BuiltInRoles.ASYNC_REVIEWER = [
    'ASYNC_REVIEWER'
]

# Crew Approver - Approve crew members
BuiltInRoles.CREW_APPROVER = [
    'CREW_APPROVER'
]
```

### Usage

```python
from application.services.organization_service import OrganizationService
from application.policies.built_in_roles import BuiltInRoles

service = OrganizationService()

# Grant organization admin role
await service.set_user_roles(
    user_id=user.id,
    organization_id=org.id,
    role_names=BuiltInRoles.ORGANIZATION_ADMIN
)

# Grant multiple role groups
await service.set_user_roles(
    user_id=user.id,
    organization_id=org.id,
    role_names=BuiltInRoles.TOURNAMENT_MANAGER + BuiltInRoles.ASYNC_REVIEWER
)
```

---

## Service Layer Permission Checks

This section documents all permission checks in the service layer.

### Global Permission Checks

Services that check global permissions using `user.has_permission()`:

#### OrganizationRequestService
- **`list_pending_requests()`**: Requires `Permission.SUPERADMIN`
- **`list_reviewed_requests()`**: Requires `Permission.SUPERADMIN`

#### UserService
- **`get_all_users()`**: Requires `Permission.ADMIN`
- **`search_users()`**: Requires `Permission.ADMIN`
- **`admin_unlink_racetime_account()`**: Requires `Permission.ADMIN`
- **`get_all_racetime_accounts()`**: Requires `Permission.ADMIN`
- **`search_racetime_accounts()`**: Requires `Permission.ADMIN`
- **`get_racetime_link_statistics()`**: Requires `Permission.ADMIN`

#### RacetimeBotService
All methods require `Permission.ADMIN`:
- `get_all_bots()`
- `get_bot_by_id()`
- `create_bot()`
- `update_bot()`
- `restart_bot()`
- `get_bots_for_organization()`
- `assign_bot_to_organization()`
- `unassign_bot_from_organization()`
- `get_organizations_for_bot()`

#### RacetimeChatCommandService
All methods require `Permission.ADMIN`:
- `get_all_commands()`
- `create_command()`
- `update_command()`
- `delete_command()`

### Organization-Scoped Permission Checks

Services that use AuthorizationServiceV2 for organization-scoped permissions:

#### RacerVerificationService
Uses `AuthorizationServiceV2.can()` with `"member:manage"` action:
- **`create_verification()`**: Requires member management permission
- **`update_verification()`**: Requires member management permission
- **`delete_verification()`**: Requires member management permission

#### AsyncTournamentService
Uses internal `can_manage_async_qualifiers()` method:
- **`create_tournament()`**: Requires SUPERADMIN or TOURNAMENT_MANAGER role
- **`update_tournament()`**: Requires SUPERADMIN or TOURNAMENT_MANAGER role
- **`delete_tournament()`**: Requires SUPERADMIN or TOURNAMENT_MANAGER role

#### TournamentService
Uses internal `can_manage_tournaments()` method:
- **`create_tournament()`**: Requires SUPERADMIN or TOURNAMENT_MANAGER role
- **`update_tournament()`**: Requires SUPERADMIN or TOURNAMENT_MANAGER role
- **`delete_tournament()`**: Requires SUPERADMIN or TOURNAMENT_MANAGER role

#### TaskSchedulerService
Uses AuthorizationServiceV2 with `"task:create"`, `"task:update"`, `"task:delete"` actions:
- **`create_task()`**: Requires SUPERADMIN or SCHEDULED_TASK_MANAGER role
- **`update_task()`**: Requires SUPERADMIN or SCHEDULED_TASK_MANAGER role
- **`delete_task()`**: Requires SUPERADMIN or SCHEDULED_TASK_MANAGER role

#### RaceRoomProfileService
Uses AuthorizationServiceV2 with `"race_room_profile:*"` actions:
- **`create_profile()`**: Requires SUPERADMIN or RACE_ROOM_MANAGER role
- **`update_profile()`**: Requires SUPERADMIN or RACE_ROOM_MANAGER role
- **`delete_profile()`**: Requires SUPERADMIN or RACE_ROOM_MANAGER role

#### AsyncLiveRaceService
Uses AuthorizationServiceV2 with `"live_race:*"` actions:
- **`enable_live_monitoring()`**: Requires SUPERADMIN or LIVE_RACE_MANAGER role
- **`disable_live_monitoring()`**: Requires SUPERADMIN or LIVE_RACE_MANAGER role

---

## API Endpoint Authorization

This section documents authorization for all API endpoints.

### Authentication

All API endpoints require authentication via Bearer token (except public endpoints).

**Dependency**: `get_current_user` from `api/deps.py`

### Global Permission Endpoints

Endpoints requiring global permissions:

#### User Management (`/api/users`)
- **GET `/`**: Requires `Permission.ADMIN` (list all users)
- **GET `/search`**: Requires `Permission.ADMIN` (search users)
- **GET `/racetime/admin/accounts`**: Requires `Permission.ADMIN` (list RaceTime accounts)
- **GET `/racetime/admin/stats`**: Requires `Permission.ADMIN` (RaceTime statistics)
- **POST `/racetime/admin/unlink/{user_id}`**: Requires `Permission.ADMIN` (admin unlink)

#### Organization Management (`/api/organizations`)
Most organization endpoints check permissions at service layer.

#### RaceTime Bots (`/api/racetime-bots`)
All endpoints require `Permission.ADMIN`:
- GET `/` - List all bots
- GET `/{bot_id}` - Get bot details
- POST `/` - Create bot
- PATCH `/{bot_id}` - Update bot
- POST `/{bot_id}/restart` - Restart bot
- GET `/organizations/{organization_id}/bots` - Get bots for org
- POST `/organizations/{organization_id}/bots/{bot_id}` - Assign bot to org
- DELETE `/organizations/{organization_id}/bots/{bot_id}` - Unassign bot from org

#### Chat Commands (`/api/chat-commands`)
All endpoints require `Permission.ADMIN`:
- GET `/` - List all commands
- POST `/` - Create command
- PATCH `/{command_id}` - Update command
- DELETE `/{command_id}` - Delete command

### Organization-Scoped Endpoints

Endpoints that check organization membership and roles at service layer:

#### Tournaments (`/api/tournaments/organizations/{organization_id}`)
- Authorization checked in `TournamentService`
- Requires SUPERADMIN or TOURNAMENT_MANAGER role in organization

#### Async Qualifiers (`/api/async-tournaments/organizations/{organization_id}`)
- Authorization checked in `AsyncTournamentService`
- Requires SUPERADMIN or TOURNAMENT_MANAGER role in organization

#### Scheduled Tasks (`/api/scheduled-tasks/organizations/{organization_id}`)
- Authorization checked in `TaskSchedulerService`
- Requires SUPERADMIN or SCHEDULED_TASK_MANAGER role in organization

#### Discord Events (`/api/discord-events/organizations/{organization_id}`)
- Custom authorization check: `_can_manage_discord_events()`
- Requires SUPERADMIN or ADMIN role in organization

### Rate Limiting

All API endpoints are rate-limited using `enforce_rate_limit` dependency:
- Default: 60 requests per minute per user
- Configurable per-user via `user.api_rate_limit_per_minute`
- Returns HTTP 429 when exceeded

---

## Permission Matrix

This matrix shows which roles can perform which actions.

### Legend
- ✅ = Can perform action
- ❌ = Cannot perform action
- 🌐 = Global permission (bypasses organization check)
- 🏢 = Organization-scoped permission

### System-Wide Actions

| Action | SUPERADMIN | ADMIN | MODERATOR | USER |
|--------|-----------|-------|-----------|------|
| Access Admin Panel | 🌐 ✅ | 🌐 ✅ | ❌ | ❌ |
| Manage All Users | 🌐 ✅ | 🌐 ✅ | ❌ | ❌ |
| View User Emails | 🌐 ✅ | ❌ | ❌ | ❌ |
| Manage Org Requests | 🌐 ✅ | ❌ | ❌ | ❌ |
| Manage RaceTime Bots | 🌐 ✅ | 🌐 ✅ | ❌ | ❌ |
| Manage Chat Commands | 🌐 ✅ | 🌐 ✅ | ❌ | ❌ |
| Manage Feature Flags | 🌐 ✅ | ❌ | ❌ | ❌ |

### Organization Management

| Action | SUPERADMIN | ADMIN | Org ADMIN | MEMBER_MANAGER | Regular Member |
|--------|-----------|-------|-----------|----------------|----------------|
| Manage Org Settings | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | ❌ | ❌ |
| Invite Members | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| Remove Members | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| Change Member Roles | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| View Members | ✅ | ✅ | ✅ | ✅ | ✅ |
| Leave Organization | ✅ | ✅ | ✅ | ✅ | ✅ |

### Tournament Management

| Action | SUPERADMIN | ADMIN | Org ADMIN | TOURNAMENT_MANAGER | Regular Member |
|--------|-----------|-------|-----------|-------------------|----------------|
| Create Tournament | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| Update Tournament | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| Delete Tournament | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| View Tournaments | ✅ | ✅ | ✅ | ✅ | ✅ |
| Participate in Tournament | ✅ | ✅ | ✅ | ✅ | ✅ |

### Async Qualifier Management

| Action | SUPERADMIN | ADMIN | Org ADMIN | TOURNAMENT_MANAGER | ASYNC_REVIEWER | Regular Member |
|--------|-----------|-------|-----------|-------------------|----------------|----------------|
| Create Async Qualifier | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ | ❌ |
| Update Async Qualifier | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ | ❌ |
| Delete Async Qualifier | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ | ❌ |
| Review Race Submissions | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| Approve Race Results | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| Submit Race Result | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Async Qualifiers | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### Task Management

| Action | SUPERADMIN | ADMIN | Org ADMIN | SCHEDULED_TASK_MANAGER | Regular Member |
|--------|-----------|-------|-----------|----------------------|----------------|
| Create Task | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| Update Task | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| Delete Task | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| View Tasks | 🌐 ✅ | 🌐 ✅ | ✅ | ✅ | ✅ |

### RaceTime Profile Management

| Action | SUPERADMIN | ADMIN | Org ADMIN | RACE_ROOM_MANAGER | Regular Member |
|--------|-----------|-------|-----------|-------------------|----------------|
| Create Profile | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| Update Profile | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| Delete Profile | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| View Profiles | ✅ | ✅ | ✅ | ✅ | ✅ |

### Live Race Management

| Action | SUPERADMIN | ADMIN | Org ADMIN | LIVE_RACE_MANAGER | Regular Member |
|--------|-----------|-------|-----------|-------------------|----------------|
| Enable Live Monitoring | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| Disable Live Monitoring | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | 🏢 ✅ | ❌ |
| View Live Races | ✅ | ✅ | ✅ | ✅ | ✅ |

### Discord Events

| Action | SUPERADMIN | ADMIN | Org ADMIN | Regular Member |
|--------|-----------|-------|-----------|----------------|
| Manage Discord Events | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | ❌ |
| Sync Events | 🌐 ✅ | 🌐 ✅ | 🏢 ✅ | ❌ |
| View Events | ✅ | ✅ | ✅ | ✅ |

---

## Permission Patterns

### Pattern 1: Global Permission Check

Used for system-wide administrative actions.

```python
from models import Permission

# In service method
if not user or not user.has_permission(Permission.ADMIN):
    logger.warning("Unauthorized access attempt")
    return []  # Graceful degradation
```

### Pattern 2: Organization Permission Check (Service Layer)

Used for organization-scoped actions in services.

```python
from application.services.authorization_service_v2 import AuthorizationServiceV2

class MyService:
    def __init__(self):
        self.auth = AuthorizationServiceV2()
    
    async def my_method(self, user, organization_id):
        # Check permission using policy framework
        if not await self.auth.can(
            user,
            action="resource:operation",
            resource=self.auth.get_resource_identifier("resource", "*"),
            organization_id=organization_id
        ):
            return None  # Graceful degradation
```

### Pattern 3: Organization Permission Check (UI Layer)

Used for UI components to show/hide elements.

```python
from application.services.ui_authorization_helper import UIAuthorizationHelper

class MyView:
    def __init__(self):
        self.ui_auth = UIAuthorizationHelper()
    
    async def render(self):
        # Check organization-scoped permission
        can_manage = await self.ui_auth.can_manage_tournaments(user, org_id)
        
        if can_manage:
            # Show management UI
            pass
```

### Pattern 4: API Permission Check

Used in API dependencies for endpoint protection.

```python
from fastapi import Depends
from api.deps import require_permission
from models import Permission

@router.get("/admin", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def admin_endpoint():
    # Only users with ADMIN permission can access
    pass
```

---

## Security Considerations

### 1. Tenant Isolation
- **All organization-scoped data must filter by organization_id**
- Never trust client-provided organization_id without validation
- Always verify user is member of organization before granting access

### 2. PII Protection
- User email addresses (`discord_email`) are sensitive PII
- Only SUPERADMIN users may view/edit email addresses
- Never display emails in organization views or member lists

### 3. Graceful Degradation
- Services return empty results (not exceptions) for unauthorized access
- Helps prevent information disclosure through error messages
- Log authorization failures for audit purposes

### 4. Permission Hierarchy
- Higher permissions include all lower permissions
- Always use `user.has_permission()` method (respects hierarchy)
- Never directly compare permission values

### 5. Server-Side Enforcement
- UI permission checks are for UX only
- Always enforce permissions on server-side (service/API layer)
- Never trust client-side permission checks

---

## Testing

Comprehensive permission tests are in:
- **Unit Tests**: Test individual permission methods
- **Integration Tests**: `tests/integration/test_ui_permissions.py`
  - Tests UIAuthorizationHelper with real database
  - Tests Permission enum hierarchy
  - Tests organization-scoped permissions
  - Tests graceful degradation

---

## References

- **[Authorization Migration Guide](AUTHORIZATION_MIGRATION.md)** - Migration from deprecated AuthorizationService
- **[Policy Framework](../systems/POLICY_FRAMEWORK.md)** - Core policy system design (if exists)
- **[Built-in Roles](../../application/policies/built_in_roles.py)** - Role group definitions
- **[Architecture Guide](../ARCHITECTURE.md)** - System architecture overview

---

**End of Permission Audit Document**
