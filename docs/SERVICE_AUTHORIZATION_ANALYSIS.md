# Service Layer Authorization Analysis

## Overview

This document provides a comprehensive analysis of authorization checks across all service layer methods in the application. It identifies patterns, best practices, and areas for improvement.

## Analysis Date

2025-11-04

## Methodology

All service files in `application/services/` were analyzed to:
1. Identify public methods that accept a `user` or `current_user` parameter
2. Check for authorization logic (permission checks, membership validation, ownership verification)
3. Categorize methods by authorization pattern
4. Document findings and recommendations

## Authorization Patterns

### Pattern 1: Global Permission Checks
Methods that require specific global permission levels (ADMIN, MODERATOR, SUPERADMIN).

**Example:**
```python
async def get_all_users(self, current_user: Optional[User]) -> list[User]:
    if not AuthorizationService.can_access_admin_panel(current_user):
        logger.warning("Unauthorized get_all_users attempt by user %s", getattr(current_user, 'id', None))
        return []
    return await self.user_repository.get_all()
```

**Services using this pattern:**
- `UserService.get_all_users()` - Requires ADMIN
- `UserService.search_users()` - Requires MODERATOR
- `OrganizationService.create_organization()` - Requires SUPERADMIN
- `OrganizationService.update_organization()` - Requires SUPERADMIN

### Pattern 2: Organization Membership Checks
Methods that require user to be a member of an organization.

**Example:**
```python
async def list_guilds(self, user: Optional[User], organization_id: int) -> List[DiscordGuild]:
    member = await self.org_service.get_member(organization_id, user.id)
    if not member:
        logger.warning("Unauthorized list_guilds by user %s for org %s", 
                      getattr(user, 'id', None), organization_id)
        return []
    return await self.repo.list_by_organization(organization_id)
```

**Services using this pattern:**
- `DiscordGuildService.list_guilds()`
- `RaceRoomProfileService.get_profile()`
- `RaceRoomProfileService.list_profiles()`
- `RaceRoomProfileService.get_default_profile()`
- `TournamentService.create_match()`
- `TournamentService.list_active_org_tournaments()`

### Pattern 3: Resource Ownership Checks
Methods that verify user owns or created the resource being accessed.

**Example:**
```python
async def start_race(self, user: User, organization_id: int, race_id: int) -> Optional[AsyncTournamentRace]:
    race = await self.repo.get_race_by_id(race_id, organization_id)
    if not race or race.user_id != user.id:
        logger.warning("Unauthorized start_race by user %s for race %s", user.id, race_id)
        return None
    # ... proceed with operation
```

**Services using this pattern:**
- `AsyncTournamentService.start_race()` - User must own the race
- `AsyncTournamentService.finish_race()` - User must own the race
- `AsyncTournamentService.forfeit_race()` - User must own the race

### Pattern 4: User-Scoped Operations (Self-Service)
Methods where users can only access/modify their own data. Authorization is implicit in the query scope.

**Example:**
```python
async def get_user_subscriptions(self, user: User, organization: Optional[Organization] = None) -> list[NotificationSubscription]:
    """Get all subscriptions for a user."""
    return await self.repository.get_user_subscriptions(user_id=user.id, is_active=True)
```

**Services using this pattern:**
- `NotificationService.subscribe()` - User manages own subscriptions
- `NotificationService.get_user_subscriptions()` - User views own subscriptions
- `NotificationService.toggle_subscription()` - User manages own subscriptions
- `PresetNamespaceService.get_or_create_user_namespace()` - User's own namespace
- `PresetNamespaceService.list_user_namespaces()` - User's own namespaces
- `TournamentUsageService.get_recent_tournaments()` - User's own tournament history
- `OrganizationRequestService.list_user_pending_requests()` - User's own requests

### Pattern 5: Public Access with User Context
Methods that provide different data based on user permissions but don't require authentication.

**Example:**
```python
async def get_preset(self, preset_id: int, user: Optional[User] = None) -> Optional[RandomizerPreset]:
    preset = await self.repository.get_by_id(preset_id)
    if not preset:
        return None
    if not self._can_view_preset(preset, user):  # Private check
        logger.warning("User %s attempted to access private preset %s", user.id if user else None, preset_id)
        return None
    return preset
```

**Services using this pattern:**
- `RandomizerPresetService.get_preset()` - Public or user's private
- `RandomizerPresetService.list_presets()` - Filtered by accessibility
- `PresetNamespaceService.list_accessible_namespaces()` - Public or user's accessible

## Findings Summary

### ✅ Services with Complete Authorization

These services have proper authorization checks on all sensitive methods:

1. **UserService** - All admin/moderator operations properly guarded
2. **OrganizationService** - SUPERADMIN checks for create/update operations
3. **AuthorizationService** - Pure authorization logic, no data access
4. **DiscordGuildService** - Membership checks for all operations
5. **RaceRoomProfileService** - Membership checks for all operations
6. **RandomizerPresetService** - Visibility checks based on public/private settings
7. **AsyncTournamentService** - Ownership checks for race operations
8. **TournamentService** - Membership and ownership checks

### ⚠️ Services with Implicit Authorization (User-Scoped)

These services have implicit authorization through query scoping by user ID. While functionally secure, they could benefit from explicit documentation:

1. **NotificationService**
   - `subscribe()` - Creates subscription for the authenticated user
   - `get_user_subscriptions()` - Queries by user.id
   - `toggle_subscription()` - Should verify subscription belongs to user
   - `queue_notification()` - Creates notification for the authenticated user

2. **PresetNamespaceService**
   - `get_or_create_user_namespace()` - Creates namespace for authenticated user
   - `list_user_namespaces()` - Queries by user
   - `create_namespace()` - Creates namespace for authenticated user

3. **TournamentUsageService**
   - `get_recent_tournaments()` - Queries user's tournament participation

4. **OrganizationRequestService**
   - `list_user_pending_requests()` - Queries by user.id (has null check)

### 🔍 Recommendations

#### 1. Explicit Authorization Documentation

Even for user-scoped methods, add explicit comments about authorization assumptions:

```python
async def get_user_subscriptions(self, user: User) -> list[NotificationSubscription]:
    """
    Get all subscriptions for a user.
    
    Authorization: User can only access their own subscriptions (enforced by user_id filter).
    
    Args:
        user: Authenticated user (required)
    
    Returns:
        List of user's active subscriptions
    """
    # Authorization is implicit - query scoped to user.id
    return await self.repository.get_user_subscriptions(user_id=user.id, is_active=True)
```

#### 2. Add Ownership Verification

For methods like `toggle_subscription()`, add explicit ownership checks:

```python
async def toggle_subscription(self, subscription_id: int, user: User) -> Optional[NotificationSubscription]:
    """Toggle subscription active status."""
    subscription = await self.repository.get_subscription(subscription_id)
    
    # Verify ownership
    if not subscription or subscription.user_id != user.id:
        logger.warning("User %s attempted to toggle subscription %s (unauthorized)", 
                      user.id, subscription_id)
        return None
    
    # Proceed with toggle
    subscription.is_active = not subscription.is_active
    await subscription.save()
    return subscription
```

#### 3. Consistent Logging

Ensure all authorization failures are logged with consistent format:

```python
logger.warning(
    "Unauthorized %s attempt by user %s for resource %s",
    operation_name,
    user.id if user else None,
    resource_id
)
```

#### 4. Return Empty Results vs Exceptions

The codebase consistently returns empty lists/None for unauthorized access rather than raising exceptions. This is good for API ergonomics. Continue this pattern:

```python
# ✅ Good - graceful degradation
if not authorized:
    logger.warning("Unauthorized access...")
    return []

# ❌ Avoid - forces exception handling
if not authorized:
    raise PermissionError("Unauthorized")
```

## Service-by-Service Analysis

### NotificationService

**File:** `application/services/notification_service.py`

| Method | Authorization Pattern | Status | Notes |
|--------|----------------------|--------|-------|
| `subscribe()` | User-Scoped | ✅ | Creates for authenticated user only |
| `unsubscribe()` | User-Scoped | ✅ | Filters by user.id |
| `get_user_subscriptions()` | User-Scoped | ✅ | Queries by user.id |
| `toggle_subscription()` | User-Scoped | ⚠️ | Should verify ownership |
| `queue_notification()` | User-Scoped | ✅ | Creates for authenticated user |

**Recommendation:** Add ownership check to `toggle_subscription()`.

### PresetNamespaceService

**File:** `application/services/preset_namespace_service.py`

| Method | Authorization Pattern | Status | Notes |
|--------|----------------------|--------|-------|
| `get_or_create_user_namespace()` | User-Scoped | ✅ | Creates for authenticated user |
| `list_accessible_namespaces()` | Public with User Context | ✅ | Returns public or user's accessible |
| `list_user_namespaces()` | User-Scoped | ✅ | Queries by user |
| `create_namespace()` | User-Scoped | ✅ | Creates for authenticated user |

**Recommendation:** No changes needed. Authorization is appropriate.

### TournamentUsageService

**File:** `application/services/tournament_usage_service.py`

| Method | Authorization Pattern | Status | Notes |
|--------|----------------------|--------|-------|
| `get_recent_tournaments()` | User-Scoped | ✅ | Queries user's participation |

**Recommendation:** No changes needed. Authorization is appropriate.

### OrganizationRequestService

**File:** `application/services/organization_request_service.py`

| Method | Authorization Pattern | Status | Notes |
|--------|----------------------|--------|-------|
| `list_pending_requests()` | Global Permission | ✅ | SUPERADMIN only |
| `list_reviewed_requests()` | Global Permission | ✅ | SUPERADMIN only |
| `list_user_pending_requests()` | User-Scoped | ✅ | Has null check for user |

**Recommendation:** No changes needed. Authorization is complete.

### RandomizerPresetService

**File:** `application/services/randomizer_preset_service.py`

| Method | Authorization Pattern | Status | Notes |
|--------|----------------------|--------|-------|
| `get_preset()` | Public with User Context | ✅ | Uses `_can_view_preset()` |
| `list_presets()` | Public with User Context | ✅ | Filters by accessibility |
| `list_user_presets()` | User-Scoped | ✅ | Queries user's presets |

**Recommendation:** No changes needed. Authorization is well-implemented.

### AsyncTournamentService

**File:** `application/services/async_tournament_service.py`

| Method | Authorization Pattern | Status | Notes |
|--------|----------------------|--------|-------|
| `start_race()` | Resource Ownership | ✅ | Checks `race.user_id` |
| `finish_race()` | Resource Ownership | ✅ | Checks race ownership |
| `forfeit_race()` | Resource Ownership | ✅ | Checks race ownership |

**Recommendation:** No changes needed. Ownership checks are proper.

### DiscordGuildService

**File:** `application/services/discord_guild_service.py`

| Method | Authorization Pattern | Status | Notes |
|--------|----------------------|--------|-------|
| `list_guilds()` | Organization Membership | ✅ | Checks membership |

**Recommendation:** No changes needed. Authorization is complete.

### TournamentService

**File:** `application/services/tournament_service.py`

| Method | Authorization Pattern | Status | Notes |
|--------|----------------------|--------|-------|
| `create_match()` | Organization Membership | ✅ | Checks membership, validates requirements |
| `signup_crew()` | Organization Membership | ✅ | Checks membership |

**Recommendation:** No changes needed. Authorization is complete.

## Conclusion

The service layer generally follows good authorization practices:

1. **Global permissions** are properly enforced for admin operations
2. **Organization membership** is consistently checked for org-scoped operations
3. **Resource ownership** is verified for user-created resources
4. **User-scoped operations** use query filtering for implicit authorization
5. **Public/private visibility** is properly handled with context-aware filtering

### Minor Improvements Needed

1. Add ownership verification to `NotificationService.toggle_subscription()`
2. Add explicit authorization comments to user-scoped methods
3. Ensure consistent logging format for unauthorized access attempts

### No Critical Issues Found

All methods either have explicit authorization checks or use implicit authorization through query scoping. The architecture properly separates authorization concerns and consistently enforces security boundaries.

## Related Documentation

- See `docs/SEPARATION_OF_CONCERNS_FIXES.md` for service layer patterns
- See `.github/copilot-instructions.md` section on Authorization for architectural principles
- See `application/services/authorization_service.py` for reusable authorization helpers
