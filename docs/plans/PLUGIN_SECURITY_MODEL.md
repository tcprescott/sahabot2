# Plugin Security Model

## Executive Summary

This document defines the security model for the SahaBot2 plugin system. In the initial implementation, **all plugins are considered 100% trusted**. Advanced security features such as sandboxing, code scanning, and capability restrictions may be added in future releases as needed.

## Trust Model

### Current Approach: Full Trust

All plugins (built-in and external) have full access to:
- Database models and queries
- All application services
- Event bus (emit and listen)
- API route registration
- Discord bot integration
- File system access
- Network access

### Rationale

1. **Simplicity**: Reduces implementation complexity
2. **Performance**: No overhead from sandboxing or permission checks
3. **Developer Experience**: Plugin developers have full flexibility
4. **Incremental Security**: Security features can be added later as needed

### Implications

- Only install plugins from trusted sources
- Review plugin code before installation
- Built-in plugins are maintained by the core team
- External plugins should come from known developers

## Multi-Tenant Isolation

While plugins are fully trusted, **multi-tenant data isolation is still enforced**:

### Organization Scoping

Plugins must respect organization boundaries:

```python
# ✅ Correct: Always filter by organization
async def get_items(self, organization_id: int):
    return await MyModel.filter(organization_id=organization_id).all()

# ❌ Wrong: Never return cross-tenant data
async def get_all_items(self):
    return await MyModel.all()  # Security violation!
```

### Plugin Enablement

Plugins are enabled/disabled per-organization:

```python
# Check if plugin is enabled for organization
if await PluginRegistry.is_enabled('tournament', organization_id):
    # Show tournament features
    pass
```

### Authorization

Plugins must use the existing authorization system:

```python
from application.services.authorization.authorization_service_v2 import AuthorizationServiceV2

auth = AuthorizationServiceV2()

# Check permissions before performing actions
if await auth.can(user, action='tournament:create', organization_id=org_id):
    # Allow action
    pass
```

## Best Practices for Plugin Developers

### 1. Always Scope to Organization

```python
class MyPluginService:
    async def create_item(self, organization_id: int, data: dict, user: User):
        # Always include organization_id
        return await MyModel.create(
            organization_id=organization_id,
            created_by=user,
            **data
        )
```

### 2. Use Existing Authorization

```python
async def update_item(self, item_id: int, user: User, organization_id: int):
    # Check permissions
    if not await self.auth.can(user, 'my_plugin:update', organization_id=organization_id):
        return None
    
    # Verify item belongs to organization
    item = await MyModel.get_or_none(id=item_id, organization_id=organization_id)
    if not item:
        return None
    
    # Perform update
    ...
```

### 3. Emit Events for Auditing

```python
from application.events import EventBus, MyItemCreatedEvent

# Emit events for important actions
await EventBus.emit(MyItemCreatedEvent(
    user_id=user.id,
    organization_id=organization_id,
    entity_id=item.id
))
```

### 4. Use Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log important actions
logger.info("Created item %s in org %s by user %s", item.id, org_id, user.id)
```

## Future Security Enhancements

The following security features may be added in future releases:

### Potential Future Features

1. **Capability System**: Plugins declare required capabilities in manifest
2. **Resource Limits**: CPU, memory, and network limits per plugin
3. **Code Scanning**: Automated security scanning for external plugins
4. **Sandboxing**: Isolated execution environments
5. **Plugin Signing**: Cryptographic verification of plugin authenticity
6. **Permission Prompts**: User approval for sensitive operations
7. **Audit Logging**: Detailed logging of plugin actions
8. **Rate Limiting**: Per-plugin API rate limits

### When to Add Security Features

Consider adding security features when:
- External plugins become common
- Third-party developers contribute plugins
- Security incidents occur
- Regulatory requirements demand it

## Summary

| Aspect | Current State | Future State |
|--------|---------------|--------------|
| Trust Model | Full trust | Capability-based |
| Code Scanning | None | Automated scanning |
| Sandboxing | None | Optional isolation |
| Multi-tenant Isolation | Enforced | Enforced |
| Authorization | Via existing system | Enhanced per-plugin |

---

**Last Updated**: November 30, 2025
**Status**: Simplified for initial implementation
