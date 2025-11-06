# Authorization System Migration Guide

## Overview

This guide documents the migration from the old `AuthorizationService` static methods to the new policy-based authorization system. The new system separates concerns more clearly and provides better support for organization-scoped permissions.

**Migration Status**: ✅ Complete (November 2025)

## Architecture Changes

### Old System (Deprecated)
- **Service**: `application/services/authorization_service.py`
- **Pattern**: Static methods for all permission checks
- **Usage**: `AuthorizationService.can_access_admin_panel(user)`
- **Issues**: 
  - Mixed global and organization-scoped permissions
  - No clear separation between UI and service layer authorization
  - Difficult to extend with new permission types

### New System (Current)
- **Policy Framework**: `application/policies/` - Core permission checking logic
- **UI Helper**: `application/services/ui_authorization_helper.py` - Organization-scoped UI permissions
- **Built-in Roles**: Pre-configured role groups in `application/policies/built_in_roles.py`
- **Pattern**: 
  - Global permissions → Inline `Permission` enum checks
  - Organization permissions → `UIAuthorizationHelper` methods
  - Service-specific checks → Service layer methods

## Migration Patterns

### Pattern 1: Organization-Scoped Permissions → UIAuthorizationHelper

**When to use**: Checking if a user has permission within a specific organization.

**Old Code**:
```python
from application.services.authorization_service import AuthorizationService

class MyView:
    def __init__(self):
        self.auth_service = AuthorizationService()
    
    async def render(self):
        can_manage = await self.auth_service.can_manage_org_members(
            self.user, 
            self.organization.id
        )
```

**New Code**:
```python
from application.services.ui_authorization_helper import UIAuthorizationHelper

class MyView:
    def __init__(self):
        self.ui_auth = UIAuthorizationHelper()
    
    async def render(self):
        can_manage = await self.ui_auth.can_manage_members(
            self.user, 
            self.organization.id
        )
```

**Available UIAuthorizationHelper Methods**:
- `can_manage_organization(user, org_id)` - Manage organization settings
- `can_manage_members(user, org_id)` - Manage organization members
- `can_manage_tournaments(user, org_id)` - Manage tournaments
- `can_manage_async_tournaments(user, org_id)` - Manage async tournaments
- `can_review_async_races(user, org_id)` - Review async race submissions
- `can_manage_scheduled_tasks(user, org_id)` - Manage scheduled tasks
- `can_manage_race_room_profiles(user, org_id)` - Manage RaceTime profiles
- `can_manage_live_races(user, org_id)` - Manage live races

### Pattern 2: Global Admin Permissions → Inline Permission Checks

**When to use**: Checking for SUPERADMIN or ADMIN global permissions.

**Old Code**:
```python
from application.services.authorization_service import AuthorizationService

class AdminView:
    def __init__(self):
        self.auth_service = AuthorizationService()
    
    async def render(self):
        if self.auth_service.can_access_admin_panel(self.user):
            # Show admin features
            pass
```

**New Code**:
```python
from models.user import Permission

class AdminView:
    async def render(self):
        if self.user.has_permission(Permission.ADMIN):
            # Show admin features
            pass
```

**Global Permission Checks**:
```python
# Check for SUPERADMIN
if user.has_permission(Permission.SUPERADMIN):
    # User is superadmin

# Check for ADMIN (includes SUPERADMIN)
if user.has_permission(Permission.ADMIN):
    # User is admin or higher

# Check for MODERATOR (includes ADMIN and SUPERADMIN)
if user.has_permission(Permission.MODERATOR):
    # User is moderator or higher

# Multiple permission check
if user.has_permission(Permission.MODERATOR) or user.has_permission(Permission.ADMIN):
    # User has moderator or admin permissions
```

### Pattern 3: Complex Permission Logic → Local Helper Methods

**When to use**: Complex permission checks with multiple conditions.

**Old Code**:
```python
from application.services.authorization_service import AuthorizationService

class UserEditDialog:
    def __init__(self):
        self.auth_service = AuthorizationService()
    
    def render(self):
        if self.auth_service.can_change_permissions(
            self.current_user, 
            self.target_user, 
            Permission.ADMIN
        ):
            # Show permission editor
            pass
```

**New Code**:
```python
from models.user import Permission

class UserEditDialog:
    def _can_change_permissions(self, new_permission: Permission) -> bool:
        """
        Check if current user can change target user's permissions.
        
        Only SUPERADMINs can change permissions.
        Can't change your own permissions.
        Can't elevate someone to your level or higher.
        """
        if not self.current_user.has_permission(Permission.SUPERADMIN):
            return False
        if self.current_user.id == self.target_user.id:
            return False
        if new_permission >= self.current_user.permission:
            return False
        return True
    
    def render(self):
        if self._can_change_permissions(Permission.ADMIN):
            # Show permission editor
            pass
```

### Pattern 4: Service-Specific Permissions → Service Layer Methods

**When to use**: Domain-specific permission checks that require business logic.

**Example**: Tournament management permissions (already migrated correctly).

```python
from application.services.async_tournament_service import AsyncTournamentService

class TournamentView:
    def __init__(self):
        self.service = AsyncTournamentService()
    
    async def render(self):
        # Service handles permission checking internally
        can_manage = await self.service.can_manage_async_tournaments(
            self.user,
            self.organization.id
        )
```

**Note**: Service layer methods internally use the policy framework, so no migration needed for these.

## Built-in Roles Reference

The policy framework includes pre-configured role groups for common organization roles:

### Available Built-in Roles

```python
from application.policies.built_in_roles import BuiltInRoles

# Organization Admin - Full organization control
roles = BuiltInRoles.ORGANIZATION_ADMIN
# Includes: ADMIN, MEMBER_MANAGER, TOURNAMENT_MANAGER, ASYNC_REVIEWER, 
#           CREW_APPROVER, SCHEDULED_TASK_MANAGER, RACE_ROOM_MANAGER, LIVE_RACE_MANAGER

# Tournament Manager - Tournament management only
roles = BuiltInRoles.TOURNAMENT_MANAGER
# Includes: TOURNAMENT_MANAGER

# Async Reviewer - Review async race submissions
roles = BuiltInRoles.ASYNC_REVIEWER
# Includes: ASYNC_REVIEWER

# Crew Approver - Approve crew members for async tournaments
roles = BuiltInRoles.CREW_APPROVER
# Includes: CREW_APPROVER
```

### Using Built-in Roles

```python
from application.policies.built_in_roles import BuiltInRoles
from application.services.organization_service import OrganizationService

# Grant organization admin role to user
service = OrganizationService()
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

## Migration Checklist

Use this checklist when migrating a component:

### UI Component Migration

- [ ] **Identify permission checks**: Search for `AuthorizationService` usage
- [ ] **Categorize checks**: Determine if global or organization-scoped
- [ ] **Update imports**:
  - Remove: `from application.services.authorization_service import AuthorizationService`
  - Add (if needed): `from application.services.ui_authorization_helper import UIAuthorizationHelper`
  - Add (if needed): `from models.user import Permission`
- [ ] **Update instance variables**:
  - Remove: `self.auth_service = AuthorizationService()`
  - Add (if needed): `self.ui_auth = UIAuthorizationHelper()`
- [ ] **Replace permission checks**:
  - Organization permissions → `ui_auth.can_*()` methods
  - Global permissions → `user.has_permission(Permission.*)`
  - Complex checks → Local helper methods
- [ ] **Verify no remaining references**: Search for `auth_service`
- [ ] **Check for compile errors**: Run linter/type checker
- [ ] **Test functionality**: Verify UI behavior with different permission levels

### Service Layer Migration

**Note**: Service layer should continue using policy framework directly, not UIAuthorizationHelper.

```python
from application.policies.organization_permissions import OrganizationPermissions

class MyService:
    async def my_method(self, user, organization_id):
        # Use policy framework directly
        checker = OrganizationPermissions(organization_id)
        can_manage = await checker.can_manage_tournaments(user)
```

## Migrated Components

### UI Components (6 total) ✅

1. **views/user_profile/user_organizations.py**
   - Pattern: Organization-scoped → UIAuthorizationHelper
   - Method: `can_manage_organization()`

2. **views/tournaments/async_pools.py**
   - Pattern: Cleanup only (already using service layer)
   - No permission check changes needed

3. **views/admin/admin_users.py**
   - Pattern: Global permission → Inline Permission checks
   - Logic: Can edit user if same user OR admin with higher permission level

4. **views/tournaments/event_schedule.py**
   - Pattern: Global permission → Inline Permission checks
   - Methods replaced: `can_moderate()`, `can_access_admin_panel()`

5. **views/organization/org_members.py**
   - Pattern: Organization-scoped → UIAuthorizationHelper
   - Method: `can_manage_members()`

6. **components/dialogs/admin/user_edit_dialog.py**
   - Pattern: Complex logic → Local helper method
   - Created: `_can_change_permissions()` helper

## Common Migration Issues

### Issue 1: Forgetting Permission Import

**Error**: `NameError: name 'Permission' is not defined`

**Solution**: Add import at top of file:
```python
from models.user import Permission
```

### Issue 2: Using UIAuthorizationHelper for Global Permissions

**Incorrect**:
```python
# ❌ Don't use UIAuthorizationHelper for global admin checks
if await self.ui_auth.can_access_admin_panel(self.user):
    pass
```

**Correct**:
```python
# ✅ Use Permission enum for global checks
if self.user.has_permission(Permission.ADMIN):
    pass
```

### Issue 3: Mixing Organization and Global Permissions

**Incorrect**:
```python
# ❌ Don't mix permission check types
can_edit = (self.ui_auth.can_manage_tournaments(user, org_id) or 
            self.auth_service.can_access_admin_panel(user))
```

**Correct**:
```python
# ✅ Use consistent approach
can_edit_tournaments = await self.ui_auth.can_manage_tournaments(user, org_id)
is_global_admin = user.has_permission(Permission.ADMIN)
can_edit = can_edit_tournaments or is_global_admin
```

### Issue 4: Not Awaiting Async Methods

**Incorrect**:
```python
# ❌ UIAuthorizationHelper methods are async
can_manage = self.ui_auth.can_manage_members(user, org_id)
```

**Correct**:
```python
# ✅ Always await UIAuthorizationHelper methods
can_manage = await self.ui_auth.can_manage_members(user, org_id)
```

## Testing Strategy

### Test Cases for Each Pattern

#### Organization-Scoped Permissions

Test with different user types:
- ✅ SUPERADMIN (should always have access)
- ✅ Organization admin (should have access)
- ✅ Organization member with specific role (should have access for that role)
- ✅ Organization member without role (should NOT have access)
- ✅ Non-member (should NOT have access)

#### Global Permissions

Test with different permission levels:
- ✅ SUPERADMIN (highest level)
- ✅ ADMIN (second level)
- ✅ MODERATOR (third level)
- ✅ USER (base level)

#### UI Element Visibility

Verify UI elements show/hide correctly:
- ✅ Admin panel links (only for ADMIN+)
- ✅ Organization admin buttons (only for org admins)
- ✅ Tournament management buttons (only for tournament managers)
- ✅ Edit/delete buttons (based on permission level)

## Debugging Guide

### Enable Debug Logging

Add logging to track permission checks:

```python
import logging
logger = logging.getLogger(__name__)

# In your component
can_manage = await self.ui_auth.can_manage_tournaments(user, org_id)
logger.debug(
    "Permission check: user=%s, org=%s, can_manage_tournaments=%s",
    user.id, org_id, can_manage
)
```

### Check User Permissions

```python
# Check user's global permission level
print(f"User permission: {user.permission.name}")
print(f"Has ADMIN: {user.has_permission(Permission.ADMIN)}")
print(f"Has MODERATOR: {user.has_permission(Permission.MODERATOR)}")

# Check user's organization memberships
from application.repositories.organization_repository import OrganizationRepository
repo = OrganizationRepository()
member = await repo.get_member(organization_id, user.id)
if member:
    await member.fetch_related('permissions')
    print(f"Org permissions: {[p.permission_name for p in member.permissions]}")
```

### Verify Policy Framework Configuration

```python
from application.policies.organization_permissions import OrganizationPermissions

# Check permission policy for organization
checker = OrganizationPermissions(organization_id)
can_manage = await checker.can_manage_tournaments(user)
print(f"Policy check result: {can_manage}")
```

## Related Documentation

- **[Policy Framework](../systems/POLICY_FRAMEWORK.md)** - Core policy system design
- **[Architecture Guide](../ARCHITECTURE.md)** - System architecture overview
- **[Patterns & Conventions](../PATTERNS.md)** - Code patterns and best practices
- **[UIAuthorizationHelper Tests](../../tests/unit/test_ui_authorization_helper.py)** - Test suite examples

## Migration Timeline

- **Phase 1**: Policy framework implementation ✅ (November 2025)
- **Phase 2**: Service layer migration ✅ (November 2025)
- **Phase 3**: UI Authorization Helper creation ✅ (November 2025)
- **Phase 4**: UI component migration ✅ (November 2025)
- **Phase 5**: Documentation ✅ (November 2025)

## Deprecation Notice

**`AuthorizationService` is deprecated** as of November 2025. All new code should use:
- `UIAuthorizationHelper` for organization-scoped UI permissions
- `Permission` enum for global permission checks
- Policy framework directly in service layer

The old `AuthorizationService` will be removed in a future release after all code has been migrated.

---

**Last Updated**: November 5, 2025
