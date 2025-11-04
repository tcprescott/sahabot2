# RaceTime Bot Database Migration

## Overview
Converted RaceTime bot configuration from environment-based settings to a database-driven system with full UI management capabilities.

## What Changed

### 1. Database Models
- **`models/racetime_bot.py`**: New models for RaceTime bot management
  - `RacetimeBot`: Stores bot OAuth2 credentials and configuration
  - `RacetimeBotOrganization`: Links bots to organizations (many-to-many)

### 2. Data Layer
- **`application/repositories/racetime_bot_repository.py`**: Data access methods
  - CRUD operations for bots
  - Organization assignment management
  - Query methods for active bots, organization-specific bots, etc.

### 3. Service Layer
- **`application/services/racetime_bot_service.py`**: Business logic and authorization
  - All operations require ADMIN permission (SUPERADMIN for delete)
  - Organization membership checks for viewing org-assigned bots
  - Event emission for audit trail
- **`application/services/racetime_service.py`**: Updated to load from database
  - Now queries active bots from database instead of settings
  - Falls back gracefully if no bots configured

### 4. Event System
- **`application/events/types.py`**: Added three new event types
  - `RacetimeBotCreatedEvent`
  - `RacetimeBotUpdatedEvent`
  - `RacetimeBotDeletedEvent`

### 5. Admin UI
- **`views/admin/admin_racetime_bots.py`**: Full CRUD interface
  - List all bots with search/filter
  - Add, edit, delete bots
  - Manage organization assignments
- **`components/dialogs/admin/`**: Three new dialogs
  - `racetime_bot_add_dialog.py`: Create new bots
  - `racetime_bot_edit_dialog.py`: Edit existing bots
  - `racetime_bot_organizations_dialog.py`: Assign bots to organizations
- **`pages/admin.py`**: Added "RaceTime Bots" section to admin sidebar

### 6. API Routes
- **`api/routes/racetime_bots.py`**: RESTful API endpoints
  - `GET /api/racetime-bots` - List all bots
  - `GET /api/racetime-bots/{id}` - Get bot details
  - `POST /api/racetime-bots` - Create bot
  - `PATCH /api/racetime-bots/{id}` - Update bot
  - `DELETE /api/racetime-bots/{id}` - Delete bot
  - `GET /api/racetime-bots/{id}/organizations` - List assigned orgs
  - `POST /api/racetime-bots/{id}/organizations/{org_id}` - Assign to org
  - `DELETE /api/racetime-bots/{id}/organizations/{org_id}` - Unassign from org
- **`api/schemas/racetime_bot.py`**: Pydantic schemas for requests/responses

### 7. Database Changes
- **Migration**: `25_20251103194524_add_racetime_bot_models.py`
  - Creates `racetime_bots` table
  - Creates `racetime_bot_organizations` table with foreign keys
  - Unique constraint on (bot_id, organization_id)

### 8. Configuration
- **`config.py`**: Deprecated old settings with clear warnings
  - `RACETIME_BOTS` - marked as deprecated
  - `RACETIME_BOTS_ENABLED` - marked as deprecated
- **`.env.example`**: Updated with migration instructions
- **`main.py`**: Removed conditional checks for `RACETIME_BOTS_ENABLED`

## How to Use

### Admin UI (Recommended)
1. Log in as ADMIN or SUPERADMIN
2. Navigate to **Admin > RaceTime Bots**
3. Click **Add Bot** button
4. Fill in:
   - Category (e.g., `alttpr`, `smz3`)
   - Name (friendly display name)
   - Client ID (from RaceTime.gg OAuth2 app)
   - Client Secret (from RaceTime.gg OAuth2 app)
   - Optional description
   - Active status
5. Click **Manage Organizations** to assign bot to organizations
6. Select organizations that should be able to use this bot

### API
Use the RESTful API endpoints with a valid API token (requires ADMIN permission):

```bash
# List all bots
curl -H "Authorization: Bearer YOUR_TOKEN" https://yourapp.com/api/racetime-bots

# Create a bot
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category":"alttpr","name":"ALttPR Bot","client_id":"...","client_secret":"..."}' \
  https://yourapp.com/api/racetime-bots

# Assign to organization
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  https://yourapp.com/api/racetime-bots/1/organizations/1
```

### Programmatic Access
```python
from application.services.racetime_bot_service import RacetimeBotService

service = RacetimeBotService()

# Create bot
bot = await service.create_bot(
    category="alttpr",
    client_id="...",
    client_secret="...",
    name="ALttPR Bot",
    description="Bot for ALttPR races",
    is_active=True,
    current_user=admin_user
)

# Assign to organization
await service.assign_bot_to_organization(bot.id, org_id, admin_user)
```

## Migration Path

### For Existing Deployments
If you have existing bots configured via `RACETIME_BOTS` environment variable:

1. **Apply database migration**: `poetry run aerich upgrade`
2. **Transfer bots to database** (one-time):
   - Note down your current `RACETIME_BOTS` value
   - Parse each `category:client_id:client_secret` entry
   - Use admin UI or API to create corresponding bot entries
3. **Remove deprecated settings** from `.env` file
4. **Restart application** - bots will now load from database

### Example Migration Script
```python
# One-time migration helper (run manually if needed)
import os
from application.services.racetime_bot_service import RacetimeBotService

async def migrate_env_bots():
    service = RacetimeBotService()
    
    # Parse old RACETIME_BOTS format
    old_config = os.getenv('RACETIME_BOTS', '')
    if not old_config:
        return
    
    for entry in old_config.split(','):
        parts = entry.strip().split(':')
        if len(parts) != 3:
            continue
        
        category, client_id, client_secret = parts
        
        # Create in database
        await service.create_bot(
            category=category.strip(),
            client_id=client_id.strip(),
            client_secret=client_secret.strip(),
            name=f"{category.upper()} Bot",
            description=f"Migrated from environment config",
            is_active=True,
            current_user=superadmin_user  # Must be superadmin
        )
        
    print("Migration complete! You can now remove RACETIME_BOTS from .env")
```

## Benefits

1. **No Restart Required**: Add/update/remove bots without restarting the application
2. **Per-Organization**: Assign specific bots to specific organizations
3. **Audit Trail**: All changes tracked via event system
4. **Better Security**: Credentials stored in database, not in environment files
5. **UI Management**: Non-technical users can manage bots via web interface
6. **Multi-Tenant**: Each organization can have different bot configurations
7. **API-Driven**: Integrate with external tools and automation

## Security Considerations

- Bot credentials (client secrets) are stored in the database
- Ensure database backups are encrypted
- Only ADMIN and SUPERADMIN users can view/manage bots
- API token required for programmatic access
- All operations logged via audit events

## Files Changed

### New Files (15)
- `models/racetime_bot.py`
- `application/repositories/racetime_bot_repository.py`
- `application/services/racetime_bot_service.py`
- `views/admin/admin_racetime_bots.py`
- `components/dialogs/admin/racetime_bot_add_dialog.py`
- `components/dialogs/admin/racetime_bot_edit_dialog.py`
- `components/dialogs/admin/racetime_bot_organizations_dialog.py`
- `api/routes/racetime_bots.py`
- `api/schemas/racetime_bot.py`
- `migrations/models/25_20251103194524_add_racetime_bot_models.py`

### Modified Files (12)
- `models/__init__.py` - Export new models
- `application/events/types.py` - Add bot events
- `application/events/__init__.py` - Export bot events
- `application/services/racetime_service.py` - Load from database
- `views/admin/__init__.py` - Export new view
- `components/dialogs/admin/__init__.py` - Export new dialogs
- `pages/admin.py` - Add RaceTime Bots section
- `database.py` - Include new models
- `migrations/tortoise_config.py` - Include new models
- `config.py` - Deprecate old settings
- `.env.example` - Update documentation
- `main.py` - Remove RACETIME_BOTS_ENABLED check

## Testing Checklist

- [ ] Database migration applies successfully
- [ ] Admin UI loads RaceTime Bots page
- [ ] Can create new bot via UI
- [ ] Can edit existing bot via UI
- [ ] Can assign/unassign bot to organizations
- [ ] Can delete bot (SUPERADMIN only)
- [ ] API endpoints return correct data
- [ ] API requires proper authentication
- [ ] Bots start on application launch
- [ ] Events are emitted for all operations
- [ ] Organization members can see their org's bots
- [ ] Non-admins cannot access bot management

## Future Enhancements

Potential future improvements:
- Bot status monitoring (online/offline)
- Per-bot activity logs
- Bot performance metrics
- Automatic bot credential rotation
- Bot failover/redundancy configuration
