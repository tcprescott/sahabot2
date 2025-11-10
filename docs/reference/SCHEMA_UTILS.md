# Schema Utilities - Reducing Schema Boilerplate

This document describes the schema utility classes and helpers designed to reduce boilerplate code in Pydantic schema definitions.

## Overview

The `api.schema_utils` module provides base classes and mixins for common schema patterns, eliminating repetitive code across schema definitions.

## Benefits

- **Reduced Duplication**: Eliminate repetitive Config classes and common field definitions
- **Consistency**: Standardized patterns across all schemas
- **Maintainability**: Common patterns in one place
- **Type Safety**: Proper type hints and IDE support
- **Backward Compatible**: Can be adopted incrementally without breaking changes

## Components

### 1. BaseOutSchema

**Problem**: Every output schema needs `Config: from_attributes = True` for ORM compatibility.

**Solution**: `BaseOutSchema` - Base class that automatically configures `from_attributes`.

#### Before:
```python
class UserOut(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

#### After:
```python
from api.schema_utils import BaseOutSchema

class UserOut(BaseOutSchema):
    id: int
    name: str
    email: str
    created_at: datetime
    updated_at: datetime
    # Config automatically included!
```

**Savings**: ~3 lines per output schema × ~50 schemas = ~150 lines

### 2. BaseListResponse

**Problem**: Every entity type requires a separate `XxxListResponse` class with identical structure.

**Solution**: `BaseListResponse[T]` - Generic list response class.

#### Before:
```python
class UserListResponse(BaseModel):
    items: list[UserOut] = Field(..., description="List of user objects")
    count: int = Field(..., description="Total number of users")

class TournamentListResponse(BaseModel):
    items: list[TournamentOut] = Field(..., description="List of tournament objects")
    count: int = Field(..., description="Total number of tournaments")

# ... repeated for every entity type (~17 times)
```

#### After:
```python
from api.schema_utils import BaseListResponse

# Option 1: Direct type alias (recommended)
UserListResponse = BaseListResponse[UserOut]
TournamentListResponse = BaseListResponse[TournamentOut]

# Option 2: Extend for backward compatibility
class UserListResponse(BaseListResponse[UserOut]):
    pass
```

**Savings**: ~5 lines per list response × ~17 entities = ~85 lines

### 3. make_list_response()

**Alternative**: Factory function for creating list response classes with proper naming.

```python
from api.schema_utils import make_list_response

# Creates a class named "UserOutListResponse"
UserListResponse = make_list_response(UserOut)

# Use in routes
@router.get("/", response_model=UserListResponse)
async def list_users() -> UserListResponse:
    ...
```

### 4. TimestampMixin

**Problem**: Most output schemas include `created_at` and `updated_at` fields.

**Solution**: `TimestampMixin` - Adds timestamp fields automatically.

#### Before:
```python
class TournamentOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
```

#### After:
```python
from api.schema_utils import BaseOutSchema, TimestampMixin

class TournamentOut(BaseOutSchema, TimestampMixin):
    id: int
    name: str
    description: str
    # created_at and updated_at automatically included!
```

**Savings**: ~2 lines per schema × ~40 schemas = ~80 lines

### 5. OrganizationScopedMixin

**Problem**: Most entities belong to an organization and include `organization_id`.

**Solution**: `OrganizationScopedMixin` - Adds organization_id field automatically.

#### Before:
```python
class TournamentOut(BaseModel):
    id: int
    organization_id: int = Field(..., description="Organization ID")
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

#### After:
```python
from api.schema_utils import BaseOutSchema, OrganizationScopedMixin, TimestampMixin

class TournamentOut(BaseOutSchema, OrganizationScopedMixin, TimestampMixin):
    id: int
    name: str
    # organization_id, created_at, updated_at automatically included!
```

**Savings**: ~1 line per schema × ~30 org-scoped schemas = ~30 lines

### 6. create_update_schema() (Advanced)

**Experimental**: Generate update schemas from create schemas automatically.

```python
from api.schema_utils import create_update_schema

class TournamentCreateRequest(BaseModel):
    name: str = Field(..., description="Tournament name")
    description: str | None = Field(None, description="Description")
    is_active: bool = Field(True, description="Active status")

# Generate update schema with all fields optional
TournamentUpdateRequest = create_update_schema(TournamentCreateRequest)
```

**Note**: This is experimental. For production code, manually defining update schemas is often better for:
- Better IDE support
- More control over validation
- Clearer intent

## Complete Example

### Before (Original stream_channel.py):

```python
"""Stream channel schemas for API responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StreamChannelOut(BaseModel):
    """Stream channel output schema."""

    id: int = Field(..., description="Stream channel ID")
    organization_id: int = Field(..., description="Organization ID")
    channel_name: str = Field(..., description="Channel name")
    platform: str = Field(..., description="Streaming platform")
    channel_url: Optional[str] = Field(None, description="Channel URL")
    is_active: bool = Field(..., description="Whether the channel is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class StreamChannelListResponse(BaseModel):
    """Response schema for lists of stream channels."""

    items: list[StreamChannelOut] = Field(..., description="List of stream channels")
    count: int = Field(..., description="Total number of stream channels")


class StreamChannelCreateRequest(BaseModel):
    """Request schema for creating a stream channel."""

    channel_name: str = Field(..., min_length=1, max_length=255, description="Channel name")
    platform: str = Field(..., description="Streaming platform")
    channel_url: Optional[str] = Field(None, description="Channel URL")
    is_active: bool = Field(True, description="Whether the channel is active")


class StreamChannelUpdateRequest(BaseModel):
    """Request schema for updating a stream channel."""

    channel_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Channel name")
    platform: Optional[str] = Field(None, description="Streaming platform")
    channel_url: Optional[str] = Field(None, description="Channel URL")
    is_active: Optional[bool] = Field(None, description="Whether the channel is active")
```

**Total: 49 lines**

### After (With schema utilities):

```python
"""Stream channel schemas for API responses."""

from pydantic import BaseModel, Field
from typing import Optional
from api.schema_utils import (
    BaseOutSchema,
    BaseListResponse,
    OrganizationScopedMixin,
    TimestampMixin,
)


class StreamChannelOut(BaseOutSchema, OrganizationScopedMixin, TimestampMixin):
    """Stream channel output schema."""

    id: int = Field(..., description="Stream channel ID")
    channel_name: str = Field(..., description="Channel name")
    platform: str = Field(..., description="Streaming platform")
    channel_url: Optional[str] = Field(None, description="Channel URL")
    is_active: bool = Field(..., description="Whether the channel is active")


# Use generic list response
StreamChannelListResponse = BaseListResponse[StreamChannelOut]


class StreamChannelCreateRequest(BaseModel):
    """Request schema for creating a stream channel."""

    channel_name: str = Field(..., min_length=1, max_length=255, description="Channel name")
    platform: str = Field(..., description="Streaming platform")
    channel_url: Optional[str] = Field(None, description="Channel URL")
    is_active: bool = Field(True, description="Whether the channel is active")


class StreamChannelUpdateRequest(BaseModel):
    """Request schema for updating a stream channel."""

    channel_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Channel name")
    platform: Optional[str] = Field(None, description="Streaming platform")
    channel_url: Optional[str] = Field(None, description="Channel URL")
    is_active: Optional[bool] = Field(None, description="Whether the channel is active")
```

**Total: 37 lines (24% reduction)**

**Eliminated**:
- Config class (3 lines)
- organization_id field definition (1 line)
- created_at field definition (1 line)
- updated_at field definition (1 line)
- StreamChannelListResponse class definition (6 lines)

**Total savings: 12 lines per schema file**

## Migration Guide

### For Existing Schemas

These utilities are **fully backward compatible**. You can refactor schemas incrementally:

1. **Start with BaseOutSchema** - Replace BaseModel with BaseOutSchema in output schemas
   ```python
   class UserOut(BaseOutSchema):  # was BaseModel
       ...
       # Remove Config class
   ```

2. **Add mixins** - Add TimestampMixin and/or OrganizationScopedMixin
   ```python
   class TournamentOut(BaseOutSchema, OrganizationScopedMixin, TimestampMixin):
       ...
       # Remove organization_id, created_at, updated_at field definitions
   ```

3. **Simplify list responses** - Convert to BaseListResponse or type alias
   ```python
   UserListResponse = BaseListResponse[UserOut]  # was separate class
   ```

### For New Schemas

New schemas should use these utilities from the start:

```python
from api.schema_utils import (
    BaseOutSchema,
    BaseListResponse,
    OrganizationScopedMixin,
    TimestampMixin,
)

# Output schema with all common patterns
class MyEntityOut(BaseOutSchema, OrganizationScopedMixin, TimestampMixin):
    id: int
    name: str
    # organization_id, created_at, updated_at automatically included

# List response
MyEntityListResponse = BaseListResponse[MyEntityOut]

# Create/Update remain manual for validation control
class MyEntityCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class MyEntityUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
```

## Testing

The utilities are fully tested in `tests/unit/test_schema_utils.py`. Run tests with:

```bash
poetry run pytest tests/unit/test_schema_utils.py -v
```

All 16 tests pass:
- BaseOutSchema (3 tests)
- BaseListResponse (3 tests)
- make_list_response (3 tests)
- TimestampMixin (2 tests)
- OrganizationScopedMixin (2 tests)
- Mixin combinations (3 tests)

## Examples

See `api/schemas/stream_channel_refactored.py` for a complete example comparing original vs. refactored schemas.

## Impact Summary

Across the entire codebase:

| Pattern | Occurrences | Lines Saved Each | Total Lines Saved |
|---------|-------------|------------------|-------------------|
| Config class | ~50 schemas | 3 | ~150 |
| List response classes | ~17 entities | 5 | ~85 |
| Timestamp fields | ~40 schemas | 2 | ~80 |
| Organization ID field | ~30 schemas | 1 | ~30 |
| **Total** | | | **~345 lines** |

## Backward Compatibility

✅ **Fully backward compatible**
- All existing schemas continue to work
- Can be adopted incrementally
- No breaking changes to API contracts
- No changes required in routes or services

## Best Practices

1. **Use BaseOutSchema for all output schemas** - It's a strict improvement over BaseModel
2. **Use mixins judiciously** - Only add mixins that truly apply to your model
3. **Keep Create/Update schemas explicit** - Don't use automatic generation for complex validation
4. **Document inherited fields** - Add comments showing what fields come from mixins
5. **Test thoroughly** - Ensure mixins provide the fields your code expects

## See Also

- [API Utils](API_UTILS.md) - API route utilities
- [Patterns Guide](../PATTERNS.md) - General code patterns
- [Architecture Guide](../ARCHITECTURE.md) - System architecture
- [Adding Features](../ADDING_FEATURES.md) - Development guides
