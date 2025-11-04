# Separation of Concerns Fixes

## Overview

This document describes the fixes applied to enforce proper separation of concerns in the codebase, specifically addressing violations where the UI layer (pages/views) was directly accessing ORM models instead of using the service layer.

## Architecture Principles

The application follows a three-layer architecture:

1. **Presentation Layer** (pages/, views/, components/) - UI only, no business logic or data access
2. **Service Layer** (application/services/) - Business logic, authorization, and orchestration
3. **Data Access Layer** (application/repositories/) - Database queries and ORM access

**Golden Rule**: Pages and views should NEVER import or directly query ORM models. All data access must go through the service layer.

## Issues Found and Fixed

### 1. Direct ORM Access in Pages

**File**: `pages/tournaments.py`

**Issues**:
- Direct queries to `OrganizationMember.filter()` for membership checks
- Direct queries to `AsyncTournament.filter()` for active tournaments
- Direct queries to `Tournament.filter()` for active tournaments

**Fixes**:
- Replaced `OrganizationMember.filter()` with `org_service.is_member()`
- Replaced `AsyncTournament.filter()` with `async_tournament_service.list_active_org_tournaments()`
- Replaced `Tournament.filter()` with `tournament_service.list_active_org_tournaments()`
- Added `tournament_service.get_tournament()` for single tournament retrieval

### 2. Direct ORM Access in Views

**File**: `views/organization/org_overview.py`

**Issues**:
- Direct queries to `OrganizationMember.filter().count()` for member count
- Direct queries to `Tournament.filter()` for active tournaments
- Direct queries to `AsyncTournament.filter()` for active async tournaments

**Fixes**:
- Replaced `OrganizationMember.filter().count()` with `org_service.count_members()`
- Replaced tournament queries with service layer calls

**File**: `views/user_profile/user_organizations.py`

**Issues**:
- Direct queries to `OrganizationMember.filter()` for user memberships
- Direct queries to `OrganizationRequest.filter()` for pending requests

**Fixes**:
- Replaced `OrganizationMember.filter()` with `org_service.list_user_memberships()`
- Replaced `OrganizationRequest.filter()` with `request_service.list_user_pending_requests()`

**File**: `views/admin/org_requests.py`

**Issues**:
- Direct queries to `OrganizationRequest.filter()` for pending and reviewed requests

**Fixes**:
- Created new `OrganizationRequestService` with authorization checks
- Replaced direct queries with service layer calls

## New Service Layer Components

### 1. Repository Methods Added

**TournamentRepository**:
```python
async def list_active_by_org(self, organization_id: int) -> List[Tournament]:
    """List active tournaments for a specific organization."""
```

**AsyncTournamentRepository**:
```python
async def list_active_by_org(self, organization_id: int) -> List[AsyncTournament]:
    """List active async tournaments for an organization."""
```

**OrganizationRepository**:
```python
async def count_members(self, organization_id: int) -> int:
    """Count the number of members in an organization."""
```

**OrganizationRequestRepository** (New):
```python
async def list_pending_requests(self) -> List[OrganizationRequest]:
    """List all pending organization requests."""

async def list_reviewed_requests(self) -> List[OrganizationRequest]:
    """List all reviewed organization requests."""

async def list_user_pending_requests(self, user_id: int) -> List[OrganizationRequest]:
    """List pending requests submitted by a specific user."""
```

### 2. Service Methods Added

**TournamentService**:
```python
async def list_active_org_tournaments(
    self, user: Optional[User], organization_id: int
) -> List[Tournament]:
    """
    List active tournaments for an organization.
    Accessible to all organization members.
    """

async def get_tournament(
    self, user: Optional[User], organization_id: int, tournament_id: int
) -> Optional[Tournament]:
    """
    Get a tournament by ID for an organization.
    Accessible to all organization members.
    """
```

**AsyncTournamentService**:
```python
async def list_active_org_tournaments(
    self, user: Optional[User], organization_id: int
) -> List[AsyncTournament]:
    """
    List active async tournaments for an organization.
    Accessible to all organization members.
    """
```

**OrganizationService**:
```python
async def count_members(self, organization_id: int) -> int:
    """Count the number of members in an organization."""
```

**OrganizationRequestService** (New):
```python
async def list_pending_requests(self, user: Optional[User]) -> List[OrganizationRequest]:
    """List pending organization requests (SUPERADMIN only)."""

async def list_reviewed_requests(self, user: Optional[User]) -> List[OrganizationRequest]:
    """List reviewed organization requests (SUPERADMIN only)."""

async def list_user_pending_requests(self, user: User) -> List[OrganizationRequest]:
    """List pending requests submitted by the current user."""
```

## Best Practices Going Forward

### DO ✅

1. **Import services in pages/views**:
   ```python
   from application.services.organization_service import OrganizationService
   from application.services.tournament_service import TournamentService
   ```

2. **Use service methods for all data access**:
   ```python
   org_service = OrganizationService()
   member_count = await org_service.count_members(organization_id)
   ```

3. **Add new service methods when needed**:
   - If you need data in a page/view that isn't available via services
   - Add repository method first (if needed)
   - Add service method with proper authorization
   - Use service method in page/view

4. **Include authorization in services**:
   ```python
   async def list_active_org_tournaments(self, user: Optional[User], organization_id: int):
       # Check membership
       is_member = await self.org_service.is_member(user, organization_id)
       if not is_member:
           logger.warning("Unauthorized access attempt...")
           return []
       # Fetch data
       return await self.repo.list_active_by_org(organization_id)
   ```

### DON'T ❌

1. **Import ORM models in pages/views**:
   ```python
   # ❌ Wrong
   from models.async_tournament import AsyncTournament
   tournaments = await AsyncTournament.filter(organization_id=org_id).all()
   ```

2. **Direct database queries in pages/views**:
   ```python
   # ❌ Wrong
   member_count = await OrganizationMember.filter(organization_id=org_id).count()
   ```

3. **Business logic in pages/views**:
   ```python
   # ❌ Wrong - authorization check in page
   if user.permission >= Permission.ADMIN:
       # ... admin stuff
   ```

4. **Skip the service layer**:
   ```python
   # ❌ Wrong - going directly to repository from page
   from application.repositories.tournament_repository import TournamentRepository
   repo = TournamentRepository()
   tournaments = await repo.list_by_org(org_id)  # No authorization!
   ```

## Migration Checklist

When adding new features or modifying existing ones, follow this checklist:

- [ ] Does my page/view need data from the database?
- [ ] Is there a service method that provides this data?
  - [ ] If yes, use it
  - [ ] If no, create one:
    - [ ] Add repository method if needed
    - [ ] Add service method with authorization
    - [ ] Document the authorization requirements
- [ ] Did I import any ORM models in pages/views? (Remove them!)
- [ ] Did I use any `.filter()`, `.all()`, `.first()`, `.create()` in pages/views? (Move to service!)
- [ ] Are my service methods checking authorization?
- [ ] Did I add proper logging for unauthorized access attempts?

## Benefits of This Approach

1. **Security**: All data access goes through authorization checks in services
2. **Testability**: Services can be unit tested independently
3. **Maintainability**: Business logic changes only need to happen in one place
4. **Consistency**: All parts of the application use the same data access patterns
5. **Documentation**: Service methods are self-documenting about what data is available and who can access it
6. **Performance**: Services can add caching, optimize queries, etc. without changing UI
7. **Multi-tenancy**: Organization scoping is enforced consistently in services

## Examples

### Example 1: Fetching Active Tournaments

**Before** (❌ Direct ORM Access):
```python
# In pages/tournaments.py
active_tournaments = await Tournament.filter(
    organization_id=organization_id,
    is_active=True
).all()
```

**After** (✅ Service Layer):
```python
# In pages/tournaments.py
tournament_service = TournamentService()
active_tournaments = await tournament_service.list_active_org_tournaments(user, organization_id)
```

### Example 2: Checking Membership

**Before** (❌ Direct ORM Access):
```python
# In pages/tournaments.py
member = await OrganizationMember.filter(
    user_id=user.id,
    organization_id=organization_id
).first()
is_member = member is not None
```

**After** (✅ Service Layer):
```python
# In pages/tournaments.py
org_service = OrganizationService()
is_member = await org_service.is_member(user, organization_id)
```

### Example 3: Counting Members

**Before** (❌ Direct ORM Access):
```python
# In views/organization/org_overview.py
member_count = await OrganizationMember.filter(organization_id=self.organization.id).count()
```

**After** (✅ Service Layer):
```python
# In views/organization/org_overview.py
org_service = OrganizationService()
member_count = await org_service.count_members(self.organization.id)
```

## Verification

To verify no direct ORM access exists in pages/views, run:

```bash
grep -rn "await.*\.filter\|await.*\.all\|await.*\.first" pages/ views/ | \
  grep -E "AsyncTournament\.|Tournament\.|OrganizationMember\.|OrganizationRequest\.|Match\.|User\."
```

This should return no results (exit code 1).

## References

- Architecture documentation: `docs/COPILOT_INSTRUCTIONS.md` (Separation of Concerns section)
- Service layer examples: `application/services/`
- Repository layer examples: `application/repositories/`
