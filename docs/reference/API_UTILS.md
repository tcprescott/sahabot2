# API Utilities - Reducing Boilerplate Code

This document describes the API utility functions and patterns designed to reduce boilerplate code in API endpoint definitions.

## Overview

The `api.utils` module provides reusable components for common API patterns, eliminating repetitive code across endpoint definitions.

## Benefits

- **Reduced Code Duplication**: Eliminate repetitive patterns across 130+ API endpoints
- **Consistency**: Standardized response formats and error handling
- **Maintainability**: Changes to common patterns only need to be made in one place
- **Type Safety**: Generic types ensure type checking across the codebase

## Components

### 1. Generic List Response

**Problem**: Every entity type required a separate `XxxListResponse` class with identical structure.

**Solution**: `ListResponse[T]` - A generic class that works with any model type.

#### Before:
```python
class UserListResponse(BaseModel):
    items: list[UserOut] = Field(..., description="List of user objects")
    count: int = Field(..., description="Total number of users")

class TournamentListResponse(BaseModel):
    items: list[TournamentOut] = Field(..., description="List of tournament objects")
    count: int = Field(..., description="Total number of tournaments")

# ... repeated for every entity type
```

#### After:
```python
from api.utils import ListResponse, create_list_response

@router.get("/", response_model=ListResponse[UserOut])
async def list_users() -> ListResponse[UserOut]:
    users = await service.get_users()
    return create_list_response(users)
```

**Note**: For backward compatibility, existing `XxxListResponse` classes can remain in schemas, but new endpoints should use the generic version.

### 2. Common Response Documentation

**Problem**: Every endpoint repeats the same response documentation (200, 401, 403, 404, 429).

**Solution**: `api_responses()` - Generate common response docs with a function call.

#### Before:
```python
@router.get(
    "/",
    responses={
        200: {"description": "Request successful"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        429: {"description": "Rate limit exceeded"},
    },
)
```

#### After:
```python
from api.utils import api_responses

@router.get("/", responses=api_responses(200, 401, 403, 429))
```

**Available Status Codes**:
- `200`: Request successful
- `201`: Resource created successfully
- `204`: Resource deleted successfully
- `400`: Bad request
- `401`: Invalid or missing authentication token
- `403`: Insufficient permissions
- `404`: Resource not found
- `422`: Validation error
- `429`: Rate limit exceeded

### 3. Resource Not Found Handler

**Problem**: Repetitive `None` checks and `HTTPException` raising for 404 responses.

**Solution**: `handle_not_found()` - Raise 404 if resource is None, otherwise return it.

#### Before:
```python
tournament = await service.get_tournament(tournament_id)
if not tournament:
    raise HTTPException(status_code=404, detail="Tournament not found")
return TournamentOut.model_validate(tournament)
```

#### After:
```python
from api.utils import handle_not_found

tournament = await service.get_tournament(tournament_id)
return TournamentOut.model_validate(
    handle_not_found(tournament, "Tournament")
)
```

### 4. Unauthorized Handler

**Problem**: Services often return `None` for both "not found" and "insufficient permissions", requiring verbose error checking.

**Solution**: `handle_unauthorized()` - Raise 403 if resource is None.

#### Before:
```python
tournament = await service.create_tournament(...)
if not tournament:
    raise HTTPException(
        status_code=403,
        detail="Tournament not found or insufficient permissions"
    )
return TournamentOut.model_validate(tournament)
```

#### After:
```python
from api.utils import handle_unauthorized

tournament = await service.create_tournament(...)
return TournamentOut.model_validate(
    handle_unauthorized(tournament, "Tournament")
)
```

**Custom Messages**:
```python
tournament = await service.create_tournament(...)
return TournamentOut.model_validate(
    handle_unauthorized(
        tournament,
        "Tournament",
        "Insufficient permissions to create tournaments"
    )
)
```

### 5. Model List Validation

**Problem**: Repetitive list comprehensions for converting ORM objects to Pydantic models.

**Solution**: `validate_model_list()` - Convert a list of ORM objects to Pydantic models.

#### Before:
```python
users = await service.get_users()
items = [UserOut.model_validate(u) for u in users]
return UserListResponse(items=items, count=len(items))
```

#### After:
```python
from api.utils import validate_model_list, create_list_response

users = await service.get_users()
items = validate_model_list(users, UserOut)
return create_list_response(items)
```

Or even simpler:
```python
from api.utils import validate_model_list, create_list_response

users = await service.get_users()
return create_list_response(validate_model_list(users, UserOut))
```

### 6. Endpoint Error Handler (Decorator)

**Problem**: Repetitive try-catch blocks for error handling in endpoints.

**Solution**: `@endpoint_handler` - Decorator that adds standard error handling.

**Note**: This is available but not recommended for immediate use. The repository pattern is to handle errors at the service layer, not with decorators. This is provided for future consideration.

#### Example:
```python
from api.utils import endpoint_handler

@router.get("/")
@endpoint_handler
async def get_items():
    # Automatically catches and converts exceptions to appropriate HTTP responses
    return await service.get_items()
```

## Complete Example

Here's a full example showing the before/after for a typical CRUD endpoint:

### Before (84 lines):
```python
@router.get(
    "/",
    response_model=TournamentListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Tournaments",
    description="List all tournaments for an organization.",
    responses={
        200: {"description": "Tournaments retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_tournaments(
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> TournamentListResponse:
    service = TournamentService()
    tournaments = await service.list_org_tournaments(current_user, organization_id)
    items = [TournamentOut.model_validate(t) for t in tournaments]
    return TournamentListResponse(items=items, count=len(items))


@router.get(
    "/{tournament_id}",
    response_model=TournamentOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Tournament",
    description="Get a specific tournament by ID.",
    responses={
        200: {"description": "Tournament retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Tournament not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_tournament(
    tournament_id: int = Path(..., description="Tournament ID"),
    current_user: User = Depends(get_current_user),
) -> TournamentOut:
    service = TournamentService()
    tournament = await service.get_tournament(tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return TournamentOut.model_validate(tournament)


@router.post(
    "/",
    response_model=TournamentOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Tournament",
    description="Create a new tournament.",
    responses={
        201: {"description": "Tournament created successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def create_tournament(
    data: TournamentCreateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> TournamentOut:
    service = TournamentService()
    tournament = await service.create_tournament(
        user=current_user,
        organization_id=organization_id,
        name=data.name,
        description=data.description,
        is_active=data.is_active,
    )
    if not tournament:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to create tournaments"
        )
    return TournamentOut.model_validate(tournament)
```

### After (56 lines - 33% reduction):
```python
from api.utils import (
    api_responses,
    validate_model_list,
    create_list_response,
    handle_not_found,
    handle_unauthorized,
)

@router.get(
    "/",
    response_model=TournamentListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Tournaments",
    description="List all tournaments for an organization.",
    responses=api_responses(200, 401, 429),
)
async def list_tournaments(
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> TournamentListResponse:
    service = TournamentService()
    tournaments = await service.list_org_tournaments(current_user, organization_id)
    items = validate_model_list(tournaments, TournamentOut)
    return TournamentListResponse(items=items, count=len(items))


@router.get(
    "/{tournament_id}",
    response_model=TournamentOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Tournament",
    description="Get a specific tournament by ID.",
    responses=api_responses(200, 401, 404, 429),
)
async def get_tournament(
    tournament_id: int = Path(..., description="Tournament ID"),
    current_user: User = Depends(get_current_user),
) -> TournamentOut:
    service = TournamentService()
    tournament = await service.get_tournament(tournament_id)
    return TournamentOut.model_validate(
        handle_not_found(tournament, "Tournament")
    )


@router.post(
    "/",
    response_model=TournamentOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Tournament",
    description="Create a new tournament.",
    responses=api_responses(201, 401, 403, 422, 429),
    status_code=201,
)
async def create_tournament(
    data: TournamentCreateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> TournamentOut:
    service = TournamentService()
    tournament = await service.create_tournament(
        user=current_user,
        organization_id=organization_id,
        name=data.name,
        description=data.description,
        is_active=data.is_active,
    )
    return TournamentOut.model_validate(
        handle_unauthorized(
            tournament, "Tournament", "Insufficient permissions to create tournaments"
        )
    )
```

## Migration Guide

### For Existing Code

These utilities are **fully backward compatible**. You can refactor endpoints incrementally:

1. **Start with responses documentation** - Easy win, no behavior change
   ```python
   responses=api_responses(200, 401, 429)
   ```

2. **Add validation helpers** - Replace list comprehensions
   ```python
   items = validate_model_list(users, UserOut)
   ```

3. **Add error handlers** - Replace None checks
   ```python
   handle_not_found(resource, "ResourceName")
   ```

### For New Code

New endpoints should use these utilities from the start:
- Use `api_responses()` for all response documentation
- Use `validate_model_list()` for converting ORM lists to Pydantic
- Use `handle_not_found()` and `handle_unauthorized()` for error handling
- Consider using `ListResponse[T]` for new list endpoints (backward compatible)

## Testing

The utilities are fully tested in `tests/unit/test_api_utils.py`. Run tests with:

```bash
poetry run pytest tests/unit/test_api_utils.py -v
```

## Future Enhancements

Potential future improvements:
1. **Route decorators** for common patterns (e.g., `@crud_endpoint`)
2. **Schema factories** for generating CRUD schemas automatically
3. **Pagination helpers** for consistent pagination across endpoints
4. **Filter builders** for common query patterns

## See Also

- [API Patterns](../PATTERNS.md#api-routes) - General API endpoint patterns
- [Architecture Guide](../ARCHITECTURE.md) - Overall system architecture
- [Adding Features Guide](../ADDING_FEATURES.md) - Step-by-step development guides
