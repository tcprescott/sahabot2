# Service Layer Authorization Checklist

## Quick Reference for Developers

This checklist helps ensure new service methods include proper authorization checks.

## When Adding a New Service Method

### 1. Identify the Authorization Pattern

Choose the pattern that fits your method:

#### Pattern A: Global Permission Check
Use when the operation requires a specific permission level (ADMIN, MODERATOR, SUPERADMIN).

```python
async def admin_operation(self, current_user: Optional[User]) -> ResultType:
    """Operation description.
    
    Authorization: Requires ADMIN permission.
    """
    if not AuthorizationService.can_access_admin_panel(current_user):
        logger.warning("Unauthorized admin_operation attempt by user %s", 
                      getattr(current_user, 'id', None))
        return []  # or None
    
    # Proceed with operation
    return await self.repository.do_thing()
```

**When to use:**
- Creating/updating organizations (SUPERADMIN)
- Viewing all users (ADMIN)
- Searching users (MODERATOR)
- Global settings management (ADMIN/SUPERADMIN)

#### Pattern B: Organization Membership Check
Use when the operation is scoped to an organization and requires membership.

```python
async def org_operation(
    self, 
    user: Optional[User], 
    organization_id: int
) -> ResultType:
    """Operation description.
    
    Authorization: Requires organization membership.
    """
    member = await self.org_service.get_member(organization_id, user.id)
    if not member:
        logger.warning(
            "Unauthorized org_operation by user %s for org %s",
            getattr(user, 'id', None),
            organization_id
        )
        return []  # or None
    
    # Proceed with operation
    return await self.repository.do_thing(organization_id)
```

**When to use:**
- Listing organization resources (tournaments, matches, etc.)
- Accessing organization settings
- Viewing organization members
- Creating org-scoped content

#### Pattern C: Resource Ownership Check
Use when the operation modifies a resource owned by a user.

```python
async def modify_resource(
    self,
    user: User,
    organization_id: int,
    resource_id: int
) -> Optional[Resource]:
    """Operation description.
    
    Authorization: User must own the resource.
    """
    resource = await self.repository.get_by_id(resource_id, organization_id)
    if not resource or resource.user_id != user.id:
        logger.warning(
            "Unauthorized modify_resource by user %s for resource %s",
            user.id,
            resource_id
        )
        return None
    
    # Proceed with modification
    return await self.repository.update(resource_id, ...)
```

**When to use:**
- Updating user-created content (races, presets, etc.)
- Deleting user-owned resources
- Modifying user settings
- Starting/finishing user-initiated actions

#### Pattern D: User-Scoped Operation (Implicit Authorization)
Use when the operation only affects the authenticated user's own data.

```python
async def user_operation(self, user: User) -> ResultType:
    """Operation description.
    
    Authorization: User can only access their own data
    (enforced by user parameter scoping in repository query).
    """
    # Query automatically scoped to user.id
    return await self.repository.get_user_data(user_id=user.id)
```

**When to use:**
- Getting user's own subscriptions/settings
- Creating user-owned resources
- Listing user's own content
- User profile operations

**Important:** Add explicit comment documenting the implicit authorization.

#### Pattern E: Public with User Context
Use when the operation returns different data based on user permissions but doesn't require authentication.

```python
async def get_resource(
    self,
    resource_id: int,
    user: Optional[User] = None
) -> Optional[Resource]:
    """Get resource by ID.
    
    Authorization: Public resources accessible to all, private resources
    require ownership or specific permissions.
    """
    resource = await self.repository.get_by_id(resource_id)
    if not resource:
        return None
    
    # Check if user can view this resource
    if not self._can_view_resource(resource, user):
        logger.warning(
            "User %s attempted to access private resource %s",
            user.id if user else None,
            resource_id
        )
        return None
    
    return resource
```

**When to use:**
- Public/private content (presets, namespaces)
- Read-only data with visibility rules
- Search/discovery features

### 2. Always Include These Elements

For **every** service method that accesses data:

- [ ] **Docstring** with "Authorization:" section explaining the rule
- [ ] **Authorization check** before data access (explicit or documented implicit)
- [ ] **Logging** for unauthorized attempts using `logger.warning()`
- [ ] **Graceful failure** - return empty list/None instead of raising exception
- [ ] **User parameter** - pass `user` or `current_user` to enable checks

### 3. Standard Logging Format

Use consistent logging for unauthorized access:

```python
logger.warning(
    "Unauthorized %s attempt by user %s for resource %s in org %s",
    "operation_name",
    user.id if user else None,
    resource_id,
    organization_id
)
```

### 4. Return Patterns

**Do ✅:**
```python
if not authorized:
    logger.warning("Unauthorized access...")
    return []  # for list methods
    return None  # for single-item methods
```

**Don't ❌:**
```python
if not authorized:
    raise PermissionError("Unauthorized")  # Forces exception handling
```

**Why:** Returning empty results provides better API ergonomics and consistent behavior.

## Testing Your Authorization

For each new service method, add tests for:

### 1. Positive Case - Authorized User
```python
async def test_operation_authorized(self):
    """Test that authorized user can perform operation."""
    service = MyService()
    authorized_user = User(..., permission=Permission.ADMIN)
    
    result = await service.my_operation(authorized_user)
    
    assert result is not None
```

### 2. Negative Case - Unauthorized User
```python
async def test_operation_unauthorized(self):
    """Test that unauthorized user gets empty result."""
    service = MyService()
    unauthorized_user = User(..., permission=Permission.USER)
    
    result = await service.my_operation(unauthorized_user)
    
    assert result == []  # or None
```

### 3. Repository Not Called When Unauthorized
```python
async def test_operation_unauthorized_no_repo_call(self):
    """Test that repository is not called for unauthorized users."""
    service = MyService()
    service.repository = AsyncMock()
    unauthorized_user = User(..., permission=Permission.USER)
    
    result = await service.my_operation(unauthorized_user)
    
    # Repository should NOT be called
    service.repository.get_data.assert_not_called()
```

## Common Pitfalls

### ❌ Missing User Parameter
```python
# Bad - no way to check authorization
async def get_tournaments(self, organization_id: int):
    return await self.repo.list_all(organization_id)
```

```python
# Good - user parameter enables authorization
async def get_tournaments(self, user: Optional[User], organization_id: int):
    if not await self.org_service.is_member(user, organization_id):
        return []
    return await self.repo.list_all(organization_id)
```

### ❌ Trusting Client-Provided User IDs
```python
# Bad - user_id from client isn't verified
async def get_user_data(self, user_id: int):
    return await self.repo.get_by_user(user_id)
```

```python
# Good - use authenticated user from session/token
async def get_user_data(self, user: User):
    return await self.repo.get_by_user(user.id)
```

### ❌ Inconsistent Authorization Checks
```python
# Bad - some branches check, others don't
async def update_resource(self, user: User, resource_id: int):
    if resource_id > 100:
        # Check authorization
        if not user.has_permission(Permission.ADMIN):
            return None
    # Missing check for resource_id <= 100!
    return await self.repo.update(resource_id)
```

```python
# Good - consistent check for all paths
async def update_resource(self, user: User, resource_id: int):
    if not user.has_permission(Permission.ADMIN):
        logger.warning("Unauthorized update by user %s", user.id)
        return None
    return await self.repo.update(resource_id)
```

### ❌ Forgetting to Log Unauthorized Attempts
```python
# Bad - silent failure makes debugging hard
async def get_data(self, user: User):
    if not user.has_permission(Permission.ADMIN):
        return []
    return await self.repo.get_all()
```

```python
# Good - log helps identify security issues
async def get_data(self, user: User):
    if not user.has_permission(Permission.ADMIN):
        logger.warning("Unauthorized get_data by user %s", user.id)
        return []
    return await self.repo.get_all()
```

## Quick Decision Tree

```
Does the operation access/modify data?
├─ Yes → Does it require a specific global permission (ADMIN/MODERATOR/SUPERADMIN)?
│  ├─ Yes → Use Pattern A (Global Permission Check)
│  └─ No → Is it scoped to an organization?
│     ├─ Yes → Does it require membership?
│     │  ├─ Yes → Use Pattern B (Organization Membership Check)
│     │  └─ No → Use Pattern E (Public with User Context)
│     └─ No → Does it modify user-owned resources?
│        ├─ Yes → Use Pattern C (Resource Ownership Check)
│        └─ No → Does it only access the user's own data?
│           ├─ Yes → Use Pattern D (User-Scoped Operation)
│           └─ No → Use Pattern E (Public with User Context)
└─ No → No authorization needed (helper methods, calculations)
```

## Related Documentation

- **Architecture**: `.github/copilot-instructions.md` - Overall patterns and principles
- **Analysis**: `docs/SERVICE_AUTHORIZATION_ANALYSIS.md` - Detailed findings and examples
- **Tests**: `tests/unit/test_service_authorization_patterns.py` - Test examples
- **Separation of Concerns**: `docs/SEPARATION_OF_CONCERNS_FIXES.md` - Service layer best practices

## Reviewing Existing Code

To check if a service method has proper authorization:

1. **Does it have a user parameter?** (Required for authorization)
2. **Does the docstring document authorization?** (Should have "Authorization:" section)
3. **Does it check permissions/membership/ownership?** (Or document implicit scoping)
4. **Does it log unauthorized attempts?** (Using `logger.warning()`)
5. **Does it return empty results for unauthorized?** (Not raise exceptions)

If any answer is "No", the method may need updates.

## Summary

**Golden Rules:**
1. Every data access method needs authorization (explicit or documented implicit)
2. Always pass `user` or `current_user` parameter
3. Log unauthorized access attempts
4. Return empty results instead of raising exceptions
5. Document authorization requirements in docstrings
6. Test both authorized and unauthorized cases

Following these patterns ensures consistent security across the application.
