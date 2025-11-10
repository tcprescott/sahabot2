# Repository Pattern Guide

Complete guide to the repository layer in SahaBot2, with patterns, examples, and best practices.

**Last Updated**: November 4, 2025  
**Coverage**: 15+ repositories documented with patterns

---

## Table of Contents

- [Overview](#overview)
- [Repository Architecture](#repository-architecture)
- [Core Patterns](#core-patterns)
- [Common Methods](#common-methods)
- [Repository Examples](#repository-examples)
- [Query Patterns](#query-patterns)
- [Error Handling](#error-handling)
- [Testing Repositories](#testing-repositories)
- [Repository Directory](#repository-directory)

---

## Overview

The repository layer provides **data access abstraction** between the service layer and the database (Tortoise ORM). Repositories encapsulate all database queries and ensure:

✅ **Separation of Concerns** - Services don't touch ORM directly  
✅ **Testability** - Repositories can be mocked in tests  
✅ **Reusability** - Query logic used by multiple services  
✅ **Consistency** - All database access follows same patterns  
✅ **Maintainability** - Changes to queries in one place  

**Key Rule**: Services call repositories, repositories call ORM.

```
Service Layer → Repository Layer → Tortoise ORM → Database
```

---

## Repository Architecture

### Location

```
application/repositories/
├── __init__.py                          # Package exports
├── base_repository.py                   # Abstract base class
├── user_repository.py                   # User data access
├── organization_repository.py           # Organization data access
├── tournament_repository.py             # Tournament data access
├── async_qualifier_repository.py       # Async tournament data access
├── async_live_race_repository.py        # Live race data access
├── audit_repository.py                  # Audit log data access
├── preset_namespace_repository.py       # Preset namespace data access
├── randomizer_preset_repository.py      # Randomizer preset data access
├── racetime_bot_repository.py           # RaceTime bot data access
├── scheduled_task_repository.py         # Scheduled task data access
├── notification_repository.py           # Notification data access
├── discord_repository.py                # Discord configuration data access
├── stream_channel_repository.py         # Stream channel data access
└── settings_repository.py               # Settings/configuration data access
```

### Base Repository Class

All repositories extend `BaseRepository` for consistency:

```python
from application.repositories.base_repository import BaseRepository

class MyRepository(BaseRepository):
    """Data access for MyModel."""
    
    model = MyModel  # Set to the Tortoise model class
```

---

## Core Patterns

### 1. Get Single Item

**Pattern**: Query by ID, return single item or None

```python
async def get_by_id(self, item_id: int) -> Optional[MyModel]:
    """
    Get item by ID.
    
    Args:
        item_id: Item ID to fetch
    
    Returns:
        Model instance or None if not found
    """
    return await self.model.filter(id=item_id).first()

# Usage
item = await repo.get_by_id(123)
if item:
    print(f"Found: {item.name}")
```

**Why Optional?**: Graceful handling - service layer decides what to do if not found.

---

### 2. List Items with Filtering

**Pattern**: Query multiple items with optional filters, return list

```python
async def list_all(self) -> list[MyModel]:
    """Get all items."""
    return await self.model.all()

async def list_by_organization(self, org_id: int) -> list[MyModel]:
    """Get items for organization."""
    return await self.model.filter(organization_id=org_id).order_by('-created_at').all()

async def list_active(self, org_id: int) -> list[MyModel]:
    """Get active items for organization."""
    return await self.model.filter(
        organization_id=org_id,
        is_active=True
    ).order_by('-created_at').all()

# Usage
items = await repo.list_by_organization(org_id=1)
active = await repo.list_active(org_id=1)
```

**Return Type**: Always list (may be empty, never None).

---

### 3. Create Item

**Pattern**: Accept kwargs, create model, return instance

```python
async def create(self, **kwargs) -> MyModel:
    """
    Create new item.
    
    Args:
        **kwargs: Model fields (name, description, etc.)
    
    Returns:
        Created model instance
    
    Raises:
        IntegrityError: If unique constraint violated
    """
    return await self.model.create(**kwargs)

# Usage
item = await repo.create(
    organization_id=1,
    name="My Item",
    description="Description"
)
print(f"Created: {item.id}")
```

**Notes**:
- No validation here (validation in service layer)
- May raise IntegrityError (let it bubble up for service to handle)
- Return created instance (has generated ID)

---

### 4. Update Item

**Pattern**: Get, update, save, return updated instance or None

```python
async def update(self, item_id: int, **updates) -> Optional[MyModel]:
    """
    Update item.
    
    Args:
        item_id: Item to update
        **updates: Fields to update
    
    Returns:
        Updated instance or None if not found
    """
    item = await self.get_by_id(item_id)
    if not item:
        return None
    
    # Update from dict and save
    await item.update_from_dict(updates).save()
    return item

# Usage
item = await repo.update(
    item_id=123,
    name="New Name",
    status="active"
)
if item:
    print(f"Updated: {item.name}")
```

**Why get + update + save?**
- Ensures item exists before updating
- Only saves changed fields
- Returns updated instance for chaining

---

### 5. Delete Item

**Pattern**: Get, delete, return success boolean

```python
async def delete(self, item_id: int) -> bool:
    """
    Delete item.
    
    Args:
        item_id: Item to delete
    
    Returns:
        True if deleted, False if not found
    """
    item = await self.get_by_id(item_id)
    if not item:
        return False
    
    await item.delete()
    return True

# Usage
success = await repo.delete(123)
if success:
    print("Deleted")
else:
    print("Not found")
```

**Why boolean return?** - Service layer can log/notify appropriately.

---

### 6. Exists Check

**Pattern**: Quick boolean check for existence

```python
async def exists(self, **filters) -> bool:
    """
    Check if item exists.
    
    Args:
        **filters: Query filters
    
    Returns:
        True if exists, False otherwise
    """
    return await self.model.filter(**filters).exists()

# Usage
if await repo.exists(organization_id=1, name="My Item"):
    print("Already exists")
```

**Performance**: More efficient than get + check if None.

---

### 7. Count Items

**Pattern**: Count matching items

```python
async def count(self, **filters) -> int:
    """
    Count items matching filters.
    
    Args:
        **filters: Query filters
    
    Returns:
        Number of matching items
    """
    return await self.model.filter(**filters).count()

# Usage
active_count = await repo.count(organization_id=1, is_active=True)
print(f"{active_count} active items")
```

---

### 8. Paginated List

**Pattern**: Query with limit and offset for pagination

```python
async def list_paginated(
    self,
    org_id: int,
    limit: int = 20,
    offset: int = 0
) -> tuple[list[MyModel], int]:
    """
    Get paginated items.
    
    Args:
        org_id: Organization ID
        limit: Items per page
        offset: Number of items to skip
    
    Returns:
        Tuple of (items list, total count)
    """
    total = await self.count(organization_id=org_id)
    items = await self.model.filter(
        organization_id=org_id
    ).offset(offset).limit(limit).order_by('-created_at').all()
    
    return items, total

# Usage
items, total = await repo.list_paginated(org_id=1, limit=10, offset=0)
print(f"Page 1: {len(items)} of {total} items")
```

**Return Type**: Tuple of (items, total count) for UI pagination.

---

## Common Methods

### Standard CRUD Methods

Every repository should have:

```python
class MyRepository(BaseRepository):
    model = MyModel
    
    # Read
    async def get_by_id(self, item_id: int) -> Optional[MyModel]:
        """Get by ID."""
        return await self.model.filter(id=item_id).first()
    
    async def list_all(self) -> list[MyModel]:
        """Get all items."""
        return await self.model.all()
    
    # Create
    async def create(self, **kwargs) -> MyModel:
        """Create new item."""
        return await self.model.create(**kwargs)
    
    # Update
    async def update(self, item_id: int, **updates) -> Optional[MyModel]:
        """Update item."""
        item = await self.get_by_id(item_id)
        if not item:
            return None
        await item.update_from_dict(updates).save()
        return item
    
    # Delete
    async def delete(self, item_id: int) -> bool:
        """Delete item."""
        item = await self.get_by_id(item_id)
        if not item:
            return False
        await item.delete()
        return True
```

---

## Repository Examples

### Example 1: UserRepository

```python
from typing import Optional
from models import User
from application.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository):
    """User data access."""
    
    model = User
    
    # Standard CRUD
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return await User.filter(id=user_id).first()
    
    async def list_all(self) -> list[User]:
        """Get all users."""
        return await User.all()
    
    async def create(self, **kwargs) -> User:
        """Create new user."""
        return await User.create(**kwargs)
    
    async def update(self, user_id: int, **updates) -> Optional[User]:
        """Update user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        await user.update_from_dict(updates).save()
        return user
    
    async def delete(self, user_id: int) -> bool:
        """Delete user."""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        await user.delete()
        return True
    
    # Custom queries
    async def get_by_discord_id(self, discord_id: int) -> Optional[User]:
        """Get user by Discord ID."""
        return await User.filter(discord_id=discord_id).first()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return await User.filter(discord_email=email).first()
    
    async def list_by_permission(self, permission: int) -> list[User]:
        """Get users with specific permission level."""
        return await User.filter(permission=permission).all()
    
    async def get_racetime_linked(self, user_id: int) -> Optional[User]:
        """Get user if they have RaceTime account linked."""
        return await User.filter(
            id=user_id,
            racetime_id__not_null=True
        ).first()
```

### Example 2: AsyncTournamentRepository

```python
from typing import Optional
from models import AsyncTournament
from application.repositories.base_repository import BaseRepository

class AsyncTournamentRepository(BaseRepository):
    """Async tournament data access."""
    
    model = AsyncTournament
    
    async def get_by_id(self, tournament_id: int) -> Optional[AsyncTournament]:
        """Get tournament by ID."""
        return await AsyncTournament.filter(id=tournament_id).first()
    
    async def list_by_organization(self, org_id: int) -> list[AsyncTournament]:
        """Get all tournaments for organization."""
        return await AsyncTournament.filter(
            organization_id=org_id
        ).order_by('-created_at').all()
    
    async def list_active_by_organization(self, org_id: int) -> list[AsyncTournament]:
        """Get active tournaments for organization."""
        return await AsyncTournament.filter(
            organization_id=org_id,
            status='active'
        ).order_by('-start_date').all()
    
    async def create(self, **kwargs) -> AsyncTournament:
        """Create new tournament."""
        return await AsyncTournament.create(**kwargs)
    
    async def update(
        self,
        tournament_id: int,
        **updates
    ) -> Optional[AsyncTournament]:
        """Update tournament."""
        tournament = await self.get_by_id(tournament_id)
        if not tournament:
            return None
        await tournament.update_from_dict(updates).save()
        return tournament
    
    async def delete(self, tournament_id: int) -> bool:
        """Delete tournament."""
        tournament = await self.get_by_id(tournament_id)
        if not tournament:
            return False
        await tournament.delete()
        return True
    
    # Custom queries
    async def list_upcoming(self, org_id: int) -> list[AsyncTournament]:
        """Get upcoming tournaments for organization."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        return await AsyncTournament.filter(
            organization_id=org_id,
            start_date__gte=now,
            status__in=['registration', 'active']
        ).order_by('start_date').all()
    
    async def get_with_pools(self, tournament_id: int) -> Optional[AsyncTournament]:
        """Get tournament with related pools (prefetch)."""
        return await AsyncTournament.filter(
            id=tournament_id
        ).prefetch_related('pools').first()
```

### Example 3: OrganizationRepository

```python
from typing import Optional
from models import Organization
from application.repositories.base_repository import BaseRepository

class OrganizationRepository(BaseRepository):
    """Organization data access."""
    
    model = Organization
    
    async def get_by_id(self, org_id: int) -> Optional[Organization]:
        """Get organization by ID."""
        return await Organization.filter(id=org_id).first()
    
    async def list_by_owner(self, owner_id: int) -> list[Organization]:
        """Get organizations owned by user."""
        return await Organization.filter(
            owner_id=owner_id
        ).order_by('-created_at').all()
    
    async def create(self, **kwargs) -> Organization:
        """Create new organization."""
        return await Organization.create(**kwargs)
    
    async def update(
        self,
        org_id: int,
        **updates
    ) -> Optional[Organization]:
        """Update organization."""
        org = await self.get_by_id(org_id)
        if not org:
            return None
        await org.update_from_dict(updates).save()
        return org
    
    async def delete(self, org_id: int) -> bool:
        """Delete organization."""
        org = await self.get_by_id(org_id)
        if not org:
            return False
        await org.delete()
        return True
    
    # Custom queries
    async def get_by_discord_guild(self, guild_id: int) -> Optional[Organization]:
        """Get organization by Discord guild ID."""
        return await Organization.filter(
            discord_guild_id=guild_id
        ).first()
    
    async def list_user_organizations(self, user_id: int) -> list[Organization]:
        """Get all organizations user is member of."""
        # Via OrganizationMember join
        from models import OrganizationMember
        
        memberships = await OrganizationMember.filter(
            user_id=user_id
        ).all()
        
        org_ids = [m.organization_id for m in memberships]
        if not org_ids:
            return []
        
        return await Organization.filter(id__in=org_ids).all()
```

---

## Query Patterns

### Filtering with Multiple Conditions

```python
# AND conditions (default)
items = await MyModel.filter(
    organization_id=1,
    is_active=True,
    status='approved'
).all()
# WHERE organization_id = 1 AND is_active = TRUE AND status = 'approved'
```

### OR Conditions (Q objects)

```python
from tortoise.expressions import Q

items = await MyModel.filter(
    Q(status='approved') | Q(status='pending')
).all()
# WHERE status = 'approved' OR status = 'pending'
```

### NOT Conditions

```python
items = await MyModel.filter(
    status__not='draft',
    organization_id=1
).all()
# WHERE status != 'draft' AND organization_id = 1
```

### Null Checks

```python
# Not null
items = await MyModel.filter(
    racetime_id__not_null=True
).all()

# Is null
items = await MyModel.filter(
    racetime_id__isnull=True
).all()
```

### Range Queries

```python
from datetime import datetime, timedelta, timezone

# Greater than / Less than
now = datetime.now(timezone.utc)
week_ago = now - timedelta(days=7)

recent_items = await MyModel.filter(
    created_at__gte=week_ago  # >= 
).all()

# BETWEEN
items = await MyModel.filter(
    created_at__gte=start_date,
    created_at__lte=end_date
).all()
```

### Text Search

```python
# Exact match (case-sensitive)
items = await MyModel.filter(name='Exact Name').all()

# Case-insensitive contains
items = await MyModel.filter(
    name__icontains='partial'
).all()
# WHERE name LIKE '%partial%' (case-insensitive)

# Starts with
items = await MyModel.filter(
    name__istarts_with='prefix'
).all()
```

### IN Clause

```python
org_ids = [1, 2, 3]
items = await MyModel.filter(
    organization_id__in=org_ids
).all()
# WHERE organization_id IN (1, 2, 3)
```

### Ordering

```python
# Ascending
items = await MyModel.all().order_by('name')

# Descending
items = await MyModel.all().order_by('-created_at')

# Multiple fields
items = await MyModel.all().order_by('organization_id', '-created_at')
```

### Limiting Results

```python
# Get top 10
items = await MyModel.all().limit(10)

# Skip first 20, get next 10 (for pagination)
items = await MyModel.all().offset(20).limit(10)
```

### Distinct

```python
# Get unique values
statuses = await MyModel.filter(
    organization_id=1
).distinct().values_list('status', flat=True)
```

### Prefetch Related Data

```python
# Load related objects to avoid N+1 queries
tournaments = await AsyncTournament.filter(
    organization_id=1
).prefetch_related('pools', 'participants').all()

# Now accessing tournament.pools won't query database
for t in tournaments:
    print(f"{t.name}: {len(t.pools)} pools")
```

---

## Error Handling

### IntegrityError (Unique Constraint)

```python
from tortoise.exceptions import IntegrityError

async def create_with_unique_check(self, **kwargs):
    """Create item, handling duplicate unique values."""
    try:
        return await self.create(**kwargs)
    except IntegrityError as e:
        # Unique constraint violated
        # Let service layer decide what to do
        raise ValueError(f"Duplicate: {str(e)}") from e
```

**Service Layer Handling**:
```python
try:
    user = await repo.create(discord_id=discord_id, ...)
except ValueError as e:
    logger.warning("User already exists: %s", discord_id)
    return None  # Fail gracefully
```

### DoesNotExist

```python
from tortoise.exceptions import DoesNotExist

# Tortoise methods that raise DoesNotExist
user = await User.get(id=999)  # Raises if not found

# Better: use filter() instead
user = await User.filter(id=999).first()  # Returns None if not found
```

**Rule**: Use `.filter().first()` instead of `.get()` for None-safe queries.

---

## Testing Repositories

### Unit Test Pattern

```python
import pytest
from application.repositories.user_repository import UserRepository
from models import User

@pytest.mark.asyncio
async def test_get_by_discord_id():
    """Test getting user by Discord ID."""
    # Setup: Create test user
    user = await User.create(
        discord_id=123456789,
        discord_username="testuser",
        discord_email="test@example.com"
    )
    
    # Test
    repo = UserRepository()
    result = await repo.get_by_discord_id(123456789)
    
    # Verify
    assert result is not None
    assert result.discord_username == "testuser"
    
    # Cleanup
    await user.delete()

@pytest.mark.asyncio
async def test_get_by_discord_id_not_found():
    """Test getting non-existent user returns None."""
    repo = UserRepository()
    result = await repo.get_by_discord_id(999999999)
    assert result is None
```

### Mock Pattern for Services

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_service_uses_repository():
    """Test service delegates to repository."""
    # Mock the repository
    with patch('application.repositories.user_repository.UserRepository') as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = Mock(id=1, name="Test")
        mock_repo_class.return_value = mock_repo
        
        # Import and test service
        from application.services.user_service import UserService
        service = UserService()
        
        # Call service
        result = await service.get_user(1)
        
        # Verify repository was called
        mock_repo.get_by_id.assert_called_once_with(1)
        assert result.name == "Test"
```

---

## Repository Directory

### Current Repositories (15+)

| Repository | Model(s) | File |
|------------|---------|------|
| UserRepository | User | `user_repository.py` |
| OrganizationRepository | Organization | `organization_repository.py` |
| OrganizationMemberRepository | OrganizationMember | `organization_repository.py` |
| OrganizationInviteRepository | OrganizationInvite | `organization_repository.py` |
| TournamentRepository | Tournament | `tournament_repository.py` |
| TournamentCrewRepository | TournamentCrew | `tournament_repository.py` |
| MatchRepository | Match | `tournament_repository.py` |
| AsyncTournamentRepository | AsyncTournament | `async_qualifier_repository.py` |
| AsyncTournamentPoolRepository | AsyncTournamentPool | `async_qualifier_repository.py` |
| AsyncTournamentParticipantRepository | AsyncTournamentParticipant | `async_qualifier_repository.py` |
| AsyncRaceSubmissionRepository | AsyncRaceSubmission | `async_qualifier_repository.py` |
| AsyncLiveRaceRepository | AsyncLiveRace | `async_live_race_repository.py` |
| AuditRepository | AuditLog | `audit_repository.py` |
| NotificationRepository | NotificationSubscription, NotificationLog | `notification_repository.py` |
| SettingsRepository | Setting | `settings_repository.py` |

---

## Design Principles

### 1. Single Responsibility
Repository handles **one model** (or closely related models).

```python
# ✅ Good
class UserRepository:
    model = User
    # Methods for User only

# ❌ Bad
class UserRepository:
    # Methods for User, Organization, and everything else
```

### 2. Data Access Only
Repository handles queries, **never business logic**.

```python
# ✅ Good
async def get_active_users(self) -> list[User]:
    """Get all active users."""
    return await User.filter(is_active=True).all()

# ❌ Bad
async def create_user(self, discord_id, username):
    """Create user with validation."""
    if len(username) < 3:  # ❌ Validation logic!
        raise ValueError()
    return await User.create(...)
```

### 3. Fail Gracefully
Return `None` or empty list on not found, let service decide error handling.

```python
# ✅ Good
async def get_by_id(self, item_id: int) -> Optional[MyModel]:
    return await MyModel.filter(id=item_id).first()  # None if not found

# ❌ Bad
async def get_by_id(self, item_id: int) -> MyModel:
    result = await MyModel.filter(id=item_id).first()
    if not result:
        raise ItemNotFound()  # ❌ Exception handling is service's job
    return result
```

### 4. Consistent Naming
Use predictable method names for discoverability.

```python
# Standard methods
get_by_id()
list_all()
create()
update()
delete()

# Custom methods (start with verb or describe filter)
list_by_organization()
get_by_discord_id()
list_active()
get_with_related()
```

### 5. Async Always
All repository methods are async (database I/O).

```python
# ✅ Correct
async def create(self, **kwargs) -> MyModel:
    return await MyModel.create(**kwargs)

# ❌ Wrong
def create(self, **kwargs) -> MyModel:  # Should be async!
    return await MyModel.create(**kwargs)
```

---

## When to Create Repository Methods

### Create a method when:
✅ Query used in multiple services  
✅ Complex filter logic (multiple conditions)  
✅ Optimization needed (prefetch_related, distinct)  
✅ Custom sorting or ordering  
✅ Specialized counting or aggregation  

### Don't create a method when:
❌ Simple get-by-id (use generic method)  
❌ One-time query only  
❌ Better handled in service (validation, transformation)  

---

## Common Mistakes to Avoid

| ❌ Don't | ✅ Do |
|---------|--------|
| Raise exceptions for not found | Return None |
| Put validation in repository | Keep validation in service |
| Mix multiple models in one repo | One model per repository |
| Sync methods with async data access | All methods async |
| Logic beyond queries | Queries only |
| Return ORM instances to controller | Data is OK, models are OK |
| Raw SQL queries | Use Tortoise QuerySet |
| Trust client input | No validation here |
| Ignore database errors | Let them bubble up |

---

## See Also

- [SERVICES_REFERENCE.md](SERVICES_REFERENCE.md) - Service layer that uses repositories
- [DATABASE_MODELS_REFERENCE.md](DATABASE_MODELS_REFERENCE.md) - Models accessed by repositories
- [PATTERNS.md](../PATTERNS.md#database-access) - Database access patterns
- [ARCHITECTURE.md](../ARCHITECTURE.md#repository-layer) - Architecture overview
- Tortoise ORM Docs: https://tortoise.github.io/

---

**Last Updated**: November 4, 2025
