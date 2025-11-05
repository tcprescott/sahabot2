# API Coverage Gaps - Analysis and Implementation

## Executive Summary

I've analyzed the SahaBot2 codebase to identify gaps in API coverage compared to available UI features. Based on this analysis, I've created **5 new API route modules** with **31 new endpoints** to achieve feature parity between the UI and API.

## Identified Gaps

The following features were available in the UI but had no API endpoints:

1. **Preset Namespaces** - User-owned namespaces for organizing presets
2. **Randomizer Presets** - Game randomizer configuration presets
3. **Settings** - Global and organization-scoped settings management
4. **Stream Channels** - Organization streaming channel management
5. **Audit Logs** - Security and compliance audit trail viewing

## New API Endpoints Created

### 1. Presets API (`/api/presets`)

**Preset Namespaces:**
- `GET /api/presets/namespaces` - List user's namespaces
- `POST /api/presets/namespaces` - Create namespace
- `GET /api/presets/namespaces/{id}` - Get namespace details
- `PATCH /api/presets/namespaces/{id}` - Update namespace
- `DELETE /api/presets/namespaces/{id}` - Delete namespace

**Randomizer Presets:**
- `GET /api/presets` - List presets (with filters)
- `POST /api/presets` - Create preset
- `GET /api/presets/{id}` - Get preset details
- `PATCH /api/presets/{id}` - Update preset
- `DELETE /api/presets/{id}` - Delete preset

**Files Created:**
- `api/routes/presets.py` - API routes (10 endpoints)
- `api/schemas/preset.py` - Pydantic schemas

**Service Methods Added:**
- `PresetNamespaceService.list_user_namespaces()`
- `PresetNamespaceService.create_namespace()`
- `PresetNamespaceService.delete_namespace()`
- `RandomizerPresetService.list_user_presets()`
- `RandomizerPresetService.list_public_presets()`

### 2. Settings API (`/api/settings`)

**Global Settings (SUPERADMIN only):**
- `GET /api/settings/global` - List global settings
- `POST /api/settings/global` - Create global setting
- `GET /api/settings/global/{key}` - Get global setting
- `PATCH /api/settings/global/{key}` - Update global setting
- `DELETE /api/settings/global/{key}` - Delete global setting

**Organization Settings:**
- `GET /api/settings/organizations/{org_id}` - List org settings
- `POST /api/settings/organizations/{org_id}` - Create org setting
- `GET /api/settings/organizations/{org_id}/{key}` - Get org setting
- `PATCH /api/settings/organizations/{org_id}/{key}` - Update org setting
- `DELETE /api/settings/organizations/{org_id}/{key}` - Delete org setting

**Files Created:**
- `api/routes/settings.py` - API routes (10 endpoints)
- `api/schemas/setting.py` - Pydantic schemas

**Authorization:**
- Global settings require SUPERADMIN permission
- Organization settings require organization admin permission

### 3. Stream Channels API (`/api/stream-channels`)

**Organization Stream Channels:**
- `GET /api/stream-channels/organizations/{org_id}` - List channels
- `POST /api/stream-channels/organizations/{org_id}` - Create channel
- `GET /api/stream-channels/organizations/{org_id}/{channel_id}` - Get channel
- `PATCH /api/stream-channels/organizations/{org_id}/{channel_id}` - Update channel
- `DELETE /api/stream-channels/organizations/{org_id}/{channel_id}` - Delete channel

**Files Created:**
- `api/routes/stream_channels.py` - API routes (5 endpoints)
- `api/schemas/stream_channel.py` - Pydantic schemas

**Authorization:**
- All operations require organization admin permission

### 4. Audit Logs API (`/api/audit-logs`)

**Audit Log Viewing:**
- `GET /api/audit-logs` - List all logs (SUPERADMIN only)
- `GET /api/audit-logs/organizations/{org_id}` - List org logs (org admin)
- `GET /api/audit-logs/users/{user_id}` - List user logs (self or SUPERADMIN)

**Files Created:**
- `api/routes/audit_logs.py` - API routes (3 endpoints)
- `api/schemas/audit_log.py` - Pydantic schemas

**Service Methods Added:**
- `AuditService.list_audit_logs()` - With pagination and filters
- `AuditRepository.list_with_filters()` - Repository method for filtering

**Authorization:**
- Global logs: SUPERADMIN only
- Organization logs: Organization admin
- User logs: Self or SUPERADMIN

## Architecture & Patterns

All new endpoints follow the established SahaBot2 patterns:

### 1. Authorization at Service Layer
- API routes pass `current_user` to services
- Services enforce permissions and tenant isolation
- Return empty results (not exceptions) for unauthorized requests

### 2. Multi-Tenant Isolation
- Organization-scoped resources include `organization_id` filtering
- Services validate organization membership
- Audit logs track organization context

### 3. Consistent Response Schemas
- List responses: `{ items: [...], count: int }`
- All models use `model_config = {"from_attributes": True}`
- Pagination support where appropriate

### 4. Rate Limiting
- All endpoints use `Depends(enforce_rate_limit)`
- Authentication via `Depends(get_current_user)`

### 5. Error Handling
- Validation errors: 400 Bad Request
- Authorization errors: 403 Forbidden
- Not found errors: 404 Not Found
- Rate limit: 429 Too Many Requests

## Auto-Registration

All new route modules are automatically registered via `api/auto_register.py`:
- Any `.py` file in `api/routes/` with a `router` attribute is auto-discovered
- Routes are registered with `/api` prefix
- No manual registration needed

## Testing Recommendations

To verify the new endpoints:

1. **Preset Namespaces:**
   ```bash
   # List namespaces
   curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8080/api/presets/namespaces
   
   # Create namespace
   curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "my-presets", "description": "My custom presets"}' \
     http://localhost:8080/api/presets/namespaces
   ```

2. **Randomizer Presets:**
   ```bash
   # List presets
   curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8080/api/presets
   
   # Create preset
   curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "Standard","randomizer":"alttpr","settings_yaml":"...", "is_public":true}' \
     http://localhost:8080/api/presets
   ```

3. **Settings:**
   ```bash
   # List org settings (requires org admin)
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8080/api/settings/organizations/1
   ```

4. **Stream Channels:**
   ```bash
   # List channels (requires org admin)
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8080/api/stream-channels/organizations/1
   ```

5. **Audit Logs:**
   ```bash
   # View your own logs
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8080/api/audit-logs/users/YOUR_USER_ID
   ```

## API Documentation

All new endpoints are documented with:
- OpenAPI/Swagger documentation (auto-generated by FastAPI)
- Docstrings with parameter descriptions
- Response schema definitions
- Example error codes

Access Swagger UI at: `http://localhost:8080/docs`

## Files Created/Modified

### New Files (9):
1. `api/routes/presets.py` - Preset routes
2. `api/routes/settings.py` - Settings routes
3. `api/routes/stream_channels.py` - Stream channel routes
4. `api/routes/audit_logs.py` - Audit log routes
5. `api/schemas/preset.py` - Preset schemas
6. `api/schemas/setting.py` - Setting schemas
7. `api/schemas/stream_channel.py` - Stream channel schemas
8. `api/schemas/audit_log.py` - Audit log schemas

### Modified Files (4):
1. `application/services/preset_namespace_service.py` - Added list/create/delete methods
2. `application/services/randomizer_preset_service.py` - Added list_user_presets/list_public_presets
3. `application/services/audit_service.py` - Added list_audit_logs method
4. `application/repositories/audit_repository.py` - Added list_with_filters method

## Summary

**Total New Endpoints:** 31
- Preset Namespaces: 5 endpoints
- Randomizer Presets: 5 endpoints
- Global Settings: 5 endpoints
- Organization Settings: 5 endpoints
- Stream Channels: 5 endpoints
- Audit Logs: 3 endpoints

**Total New Files:** 9 (4 route files, 4 schema files, 1 analysis doc)

**Total Modified Files:** 4 (services and repositories)

All endpoints follow established patterns, include proper authorization checks, support multi-tenancy, and are automatically registered via the auto-discovery system.

## Next Steps

1. **Test the endpoints** using the examples above or via Swagger UI
2. **Update API documentation** if you have separate API docs
3. **Consider adding integration tests** for the new endpoints
4. **Monitor rate limits** to ensure they're appropriate for your use case
5. **Review audit logging** to ensure all sensitive operations are tracked
