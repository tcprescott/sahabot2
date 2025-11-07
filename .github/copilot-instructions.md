# Copilot Instructions for SahaBot2

## Project Overview

SahaBot2 is a **multi-tenant NiceGUI + FastAPI web application** with Discord OAuth2 authentication and Tortoise ORM for database access. The application emphasizes strict separation of concerns, mobile-first responsive design, and high code quality.

**Tech Stack**: FastAPI + NiceGUI + MySQL (Tortoise ORM) + Discord OAuth2 + Discord.py bot

**This is the successor to the original SahasrahBot**: https://github.com/tcprescott/sahasrahbot

When porting features from the original SahasrahBot, use the GitHub repository as reference for business logic and workflows. The new codebase has a completely different architecture (NiceGUI + FastAPI vs Flask), so adapt features to fit new patterns rather than directly copy.

**Multi-Tenant Architecture**: All user actions and data are scoped to Organizations. Every feature must preserve tenant isolation and enforce the security model.

**📚 For detailed architecture, patterns, and guides, see**:
- [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) - System architecture and components
- [`docs/PATTERNS.md`](../docs/PATTERNS.md) - Code patterns and conventions
- [`docs/ADDING_FEATURES.md`](../docs/ADDING_FEATURES.md) - Step-by-step development guides
- [`docs/README.md`](../docs/README.md) - Complete documentation index

## Architectural Layers

**Four-layer architecture** (never skip layers!):

```
UI/API (Presentation) → Services (Business Logic) → Repositories (Data Access) → Models (Database)
```

**Critical Rule**: Never access ORM from UI/API. Always: `UI → Service → Repository → Model`

**See**: [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) for detailed architecture

## Core Principles

### 1. Responsive Design for All Devices
- Design must work seamlessly on mobile and desktop
- Mobile-first approach with desktop optimizations
- Use CSS media queries in `static/css/main.css`
- Test on both mobile viewports and desktop resolutions
- Ensure feature parity across all devices

### 2. Separation of Concerns
- **UI pages** (`pages/`) - Presentation only, NO business logic
- **Services** (`application/services/`) - ALL business logic and validation
- **Repositories** (`application/repositories/`) - Data access only
- **Models** (`models/`) - Database structure
- **Never** access ORM from UI - always use services

### 3. Logging Standards
- **Always use logging framework** - Never `print()` in application code
- **Import at module level**: `logger = logging.getLogger(__name__)`
- **Use lazy % formatting** (not f-strings):
  ```python
  # ✅ Correct
  logger.info("User %s logged in", user.id)
  
  # ❌ Wrong
  logger.info(f"User {user.id} logged in")
  ```
- **Exceptions**: `print()` acceptable in test scripts, utility scripts, CLI tools

### 4. DateTime Standards
- **Always use timezone-aware datetimes** - Never use deprecated `datetime.utcnow()`
- **Use `datetime.now(timezone.utc)` for current UTC time**:
  ```python
  from datetime import datetime, timezone
  
  # ✅ Correct
  current_time = datetime.now(timezone.utc)
  
  # ❌ Wrong - deprecated and timezone-naive
  current_time = datetime.utcnow()
  ```
- **Why**: Database returns timezone-aware; mixing causes TypeErrors; utcnow() deprecated in Python 3.12+

### 5. Event System for Async Notifications
- **Always emit events** for create/update/delete operations in service layer
- **Emit AFTER successful operation** (not before)
- **Use `current_user.id` for user actions**, `SYSTEM_USER_ID` for system actions
- **Never use `None` for user_id** in events

```python
from application.events import EventBus, EntityCreatedEvent
from models import SYSTEM_USER_ID

# User action
await EventBus.emit(EntityCreatedEvent(
    user_id=current_user.id,
    organization_id=org_id,
    entity_id=entity.id
))

# System action
await EventBus.emit(EntityCreatedEvent(
    user_id=SYSTEM_USER_ID,
    organization_id=org_id,
    entity_id=entity.id
))
```

**See**: [`docs/systems/EVENT_SYSTEM.md`](../docs/systems/EVENT_SYSTEM.md)

### 6. External CSS & JavaScript Only
- **No inline styles** via `.style()` - all CSS in `static/css/main.css`
- **No inline JavaScript** - all JS in `static/js/`
- Use semantic class names (e.g., `card`, `btn-primary`, `navbar`)
- Load CSS: `ui.add_head_html('<link rel="stylesheet" href="/static/css/main.css">')`

**See**: [`docs/core/JAVASCRIPT_GUIDELINES.md`](../docs/core/JAVASCRIPT_GUIDELINES.md)

### 7. External Links Pattern
- **Links to external websites must open in new tabs**:
  ```python
  # ✅ Correct
  ui.link('GitHub', 'https://github.com/repo', new_tab=True)
  with ui.link(target='https://example.com', new_tab=True):
      ui.label('External Link')
  
  # ❌ Wrong
  ui.link('External', 'https://example.com')  # Missing new_tab=True
  ```
- **External** = other domains (RaceTime.gg, seed URLs, Discord, VODs, GitHub)
- **Internal** = application routes (`/org/1/async/2`, `/admin`)

### 8. Discord OAuth2 Authentication
- All users authenticate via Discord OAuth2
- OAuth flow handled in `middleware/auth.py` (`DiscordAuthService`)
- User info synced to database on login
- Session managed via NiceGUI `app.storage.user`

### 9. Database-Driven Authorization
- Authorization logic in `AuthorizationService` (separate from business logic)
- Permissions stored in database (`User.permission` field)
- Server-side enforcement via `require_permission()`
- UI can conditionally show elements, but must enforce server-side

### 10. High Code Quality
- **Always** use async/await for database/external API operations
- **All** public functions must have docstrings
- Type hints on function parameters and returns
- Descriptive variable names, comments for complex logic
- **No trailing whitespace** on any lines (including blank lines)
- **Module imports at top of file** (never inline imports)
- **NiceGUI elements don't have `.text()` method** - use `with` context and `ui.label()`

### 11. Discord Bot Architecture
- **Bot as Presentation Layer** - part of UI, not business logic
- **Never** access ORM from bot commands - always use services
- **Application commands only** (`@app_commands.command()`) - never prefix commands
- **Singleton pattern** - access via `get_bot_instance()` from `discordbot.client`
- Commands delegate ALL logic to services

### 12. Multi-Tenant Isolation and Security
- **All tenant-scoped data must reference organization** (FK or relation)
- **Never trust client-provided `organization_id`** - validate membership server-side
- **Service/repository methods accept explicit `organization_id` parameter**
- **Never return cross-tenant data** - always filter by organization
- **Audit with tenant context** - include `organization_id` in audit logs
- **User email addresses are sensitive PII** - only SUPERADMIN can view/edit

```python
# ✅ Correct - tenant-aware service method
async def get_tournaments(self, organization_id: int, current_user: User):
    if not self.auth_service.is_member(current_user, organization_id):
        return []  # Return empty, don't raise
    return await self.repository.list_by_organization(organization_id)
```

### 13. Authorization Patterns (Policy Framework)

**Use the new policy-based authorization system** - `AuthorizationService` is deprecated.

**Three authorization patterns** based on context:

#### Pattern 1: Organization-Scoped Permissions (UI Layer)
Use `UIAuthorizationHelper` for checking organization-specific permissions in UI components:

```python
from application.services.ui_authorization_helper import UIAuthorizationHelper

class MyView:
    def __init__(self):
        self.ui_auth = UIAuthorizationHelper()
    
    async def render(self):
        # Check organization-scoped permissions
        can_manage_members = await self.ui_auth.can_manage_members(user, org_id)
        can_manage_tournaments = await self.ui_auth.can_manage_tournaments(user, org_id)
        can_manage_org = await self.ui_auth.can_manage_organization(user, org_id)
```

**Available UIAuthorizationHelper methods**:
- `can_manage_organization()` - Organization settings
- `can_manage_members()` - Organization members
- `can_manage_tournaments()` - Tournament management
- `can_manage_async_tournaments()` - Async tournaments
- `can_review_async_races()` - Race review
- `can_manage_scheduled_tasks()` - Task scheduling
- `can_manage_race_room_profiles()` - RaceTime profiles
- `can_manage_live_races()` - Live race management

#### Pattern 2: Global Permissions (UI Layer)
Use inline `Permission` enum checks for global admin/moderator permissions:

```python
from models.user import Permission

# Check for global admin
if user.has_permission(Permission.ADMIN):
    # Show admin features
    pass

# Check for moderator (includes admin and superadmin)
if user.has_permission(Permission.MODERATOR):
    # Show moderator features
    pass

# Multiple permission check
if user.has_permission(Permission.MODERATOR) or user.has_permission(Permission.ADMIN):
    # User has moderator or admin permissions
    pass
```

**Permission Levels** (from highest to lowest):
- `Permission.SUPERADMIN` - Full system access
- `Permission.ADMIN` - Administrative access
- `Permission.MODERATOR` - Moderation capabilities
- `Permission.USER` - Standard user

#### Pattern 3: Service Layer Permissions
Use policy framework directly in service layer (NOT UIAuthorizationHelper):

```python
from application.policies.organization_permissions import OrganizationPermissions

class MyService:
    async def my_method(self, user, organization_id):
        # Use policy framework directly
        checker = OrganizationPermissions(organization_id)
        can_manage = await checker.can_manage_tournaments(user)
        
        if not can_manage:
            return None  # Graceful degradation
```

**Critical Rules**:
- ✅ **UI components**: Use `UIAuthorizationHelper` or inline `Permission` checks
- ✅ **Service layer**: Use policy framework directly
- ❌ **Never use** `AuthorizationService` (deprecated)
- ❌ **Never use** `UIAuthorizationHelper` in service layer
- ✅ **Always await** UIAuthorizationHelper methods (they're async)

**See**: [`docs/operations/AUTHORIZATION_MIGRATION.md`](../docs/operations/AUTHORIZATION_MIGRATION.md) for complete migration guide

### 14. Database Migrations with Aerich
- **NEVER manually create migration files** - Aerich requires special `models_state` tracking
- **Always use `poetry run aerich migrate --name "description"`** to generate migrations
- **Edit the generated migration SQL if needed** - but keep the file structure intact
- **Never delete or recreate migration files** - it breaks Aerich's tracking system
- **Migration workflow**:
  1. Update model in `models/`
  2. Run `poetry run aerich migrate --name "description"`
  3. Review/edit SQL in generated migration file (if needed)
  4. Run `poetry run aerich upgrade`
  5. Test the migration

```bash
# ✅ Correct - let Aerich generate the file
poetry run aerich migrate --name "add_new_field"
# Edit migrations/models/XX_*.py if SQL needs adjustment
poetry run aerich upgrade

# ❌ Wrong - manual file creation breaks tracking
cat > migrations/models/44_*.py << 'EOF'
# Manual migration content
EOF
```

### 15. CodeQL Security and Quality Checks
- **Automated scanning** - CodeQL runs on every PR and push to detect anti-patterns
- **Custom queries** - We have CodeQL queries for all major anti-patterns in this guide
- **Add queries for new anti-patterns** - When adding new "don't" rules, create a CodeQL query
- **Query location** - `.github/codeql/queries/` directory
- **Documentation** - Update `.github/codeql/README.md` when adding queries

**CodeQL queries detect**:
- `print()` in application code
- F-strings in logging statements
- `datetime.utcnow()` usage
- Direct ORM access from UI/API routes
- Inline imports (imports inside functions)
- Deprecated `AuthorizationService` usage
- `None` user_id in event emissions
- `UIAuthorizationHelper` in service layer

**When adding new anti-patterns**:
1. Add to "Common Pitfalls to Avoid" section
2. Create CodeQL query in `.github/codeql/queries/`
3. Update `.github/codeql/README.md` with query documentation
4. Test query if possible before committing

**See**: [`.github/codeql/README.md`](./codeql/README.md) for query documentation and examples

## Essential Patterns

### Page Structure with BasePage

All pages must use `BasePage` for consistent layout:

```python
from nicegui import ui
from components.base_page import BasePage

def register():
    @ui.page('/mypage')
    async def my_page():
        # Choose page type: simple_page, authenticated_page, admin_page
        base = BasePage.authenticated_page(title="My Page", active_nav="mypage")
        
        async def content(page: BasePage):
            # page.user is available
            with ui.element('div').classes('card'):
                ui.label(f'Hello, {page.user.discord_username}!')
        
        await base.render(content)()
```

**Query Parameter Notifications**:
- `?success=message` → Green notification
- `?error=message` → Red notification
- `?message=message` → Blue notification

**See**: [`docs/core/BASEPAGE_GUIDE.md`](../docs/core/BASEPAGE_GUIDE.md)

### Service Usage

Services contain ALL business logic. Never access ORM from UI/API:

```python
from application.services.user_service import UserService

# In page or API route
user_service = UserService()
users = await user_service.get_all_users()
updated = await user_service.update_user_permission(user_id, Permission.ADMIN, current_user)
```

**See**: [`docs/PATTERNS.md#service-usage`](../docs/PATTERNS.md#service-usage)

### Authorization

Authorization in `AuthorizationService` - separate from business logic:

```python
from application.services.authorization_service import AuthorizationService

auth_z = AuthorizationService()

# Check permissions
if auth_z.can_access_admin_panel(user):
    # Show admin features
    pass

# Enforce in pages
user = DiscordAuthService.require_permission(Permission.ADMIN, '/admin')
if not user:
    return  # Redirected
```

**See**: [`docs/PATTERNS.md#authorization-patterns`](../docs/PATTERNS.md#authorization-patterns)

### API Routes

Authorization enforced at **service layer only** - NOT in API routes:

```python
from fastapi import APIRouter, Depends
from api.deps import get_current_user, enforce_rate_limit

router = APIRouter(prefix="/resource", tags=["resource"])

@router.get("/", dependencies=[Depends(enforce_rate_limit)])  # Only rate limit
async def list_resources(
    current_user: User = Depends(get_current_user)  # Extract user
):
    service = ResourceService()
    # Authorization happens in service
    resources = await service.list_resources(current_user)
    return {"items": resources, "count": len(resources)}
```

**See**: [`docs/PATTERNS.md#api-routes`](../docs/PATTERNS.md#api-routes)

### Event Emission

Emit events for all create/update/delete operations:

```python
from application.events import EventBus, EntityCreatedEvent
from models import SYSTEM_USER_ID

# After successful create
entity = await self.repository.create(...)
await EventBus.emit(EntityCreatedEvent(
    user_id=current_user.id,  # User action
    organization_id=org_id,
    entity_id=entity.id
))

# System action
await EventBus.emit(EntityCreatedEvent(
    user_id=SYSTEM_USER_ID,  # System action
    organization_id=org_id,
    entity_id=entity.id
))
```

**See**: [`docs/systems/EVENT_SYSTEM.md`](../docs/systems/EVENT_SYSTEM.md)

### Discord Bot Commands

Commands are presentation layer - delegate to services:

```python
from discord import app_commands
from application.services.tournament_service import TournamentService

@app_commands.command(name="tournament", description="Get tournament info")
async def tournament_info(interaction: discord.Interaction, tournament_id: int):
    # Delegate to service
    service = TournamentService()
    tournament = await service.get_tournament(tournament_id)
    
    if not tournament:
        await interaction.response.send_message("Not found", ephemeral=True)
        return
    
    # Format and respond (presentation only)
    await interaction.response.send_message(f"Name: {tournament.name}")
```

**See**: [`docs/PATTERNS.md#discord-bot-commands`](../docs/PATTERNS.md#discord-bot-commands)

## Development Workflows

### Installation
```bash
poetry install
```

### Server Management
- Development server typically already running
- **Do NOT** attempt to start server in tool calls
- Use `./start.sh dev` (port 8080, auto-reload) or `./start.sh prod` (port 80) only when requested

### Database Migrations

**Critical**: NEVER manually create migration files. Always use `aerich migrate` to generate them.

```bash
# Initialize (first time only)
poetry run aerich init-db

# Create migration (Aerich generates the file with tracking data)
poetry run aerich migrate --name "description"

# Review and edit SQL in generated file if needed (keep file structure intact)
# migrations/models/XX_timestamp_description.py

# Apply migrations
poetry run aerich upgrade

# Rollback (if needed)
poetry run aerich downgrade
```

**Why this matters**: Aerich migration files contain a `models_state` constant that tracks schema state. Manually created files missing this data cause "Old format of migration file detected" errors and break migration tracking.

### Environment Variables
Required in `.env`:
- `DATABASE_URL` - MySQL connection string
- `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET` - OAuth2 credentials
- `DISCORD_BOT_TOKEN` - Bot authentication
- `SECRET_KEY` - Application secret

### Debugging & Screenshots
When using MCP Chrome DevTools or other screenshot tools:
- **Always save screenshots to `screenshots/` directory**
- Path: `/Users/tprescott/Library/CloudStorage/OneDrive-Personal/Documents/VSCode/sahabot2/screenshots/filename.png`
- This directory is excluded from git (in `.gitignore`)
- Use descriptive filenames (e.g., `checkbox_unchecked_state.png`, `dialog_error_message.png`)
- Screenshots are for debugging and documentation only, not committed to repository

## Quick Reference

### CSS Classes
- **Containers**: `page-container`, `content-wrapper`
- **Cards**: `card`, `card-header`, `card-body`
- **Buttons**: `btn`, `btn-primary`, `btn-secondary`, `btn-danger`
- **Badges**: `badge`, `badge-admin`, `badge-success`, `badge-warning`
- **Tables**: `data-table`
- **Utilities**: `text-center`, `mt-1`, `mb-2`, `flex`, `gap-md`

**See**: [`docs/PATTERNS.md#css-classes-reference`](../docs/PATTERNS.md#css-classes-reference)

### Component Usage

**ResponsiveTable** - Always prefer for tabular data:
```python
from components.data_table import ResponsiveTable, TableColumn

columns = [
    TableColumn(label='Name', key='name'),
    TableColumn(label='Status', cell_render=lambda row: ui.badge(row.status)),
]
table = ResponsiveTable(columns=columns, rows=data)
await table.render()
```

**DateTimeLabel** - Always use for datetime display:
```python
from components.datetime_label import DateTimeLabel

# Relative time (e.g., "2 hours ago")
DateTimeLabel.create(user.created_at, format_type='relative')

# Full datetime
DateTimeLabel.create(match.scheduled_at, format_type='datetime')
```

**See**: [`docs/core/COMPONENTS_GUIDE.md`](../docs/core/COMPONENTS_GUIDE.md)

### Organization Structure

**Views** organized by page:
- `views/home/` - Home page views
- `views/admin/` - Admin page views
- `views/organization/` - Organization admin views
- `views/tournaments/` - Tournament views

**Dialogs** organized by usage:
- `components/dialogs/admin/` - Admin dialogs
- `components/dialogs/organization/` - Organization dialogs
- `components/dialogs/tournaments/` - Tournament dialogs
- `components/dialogs/common/` - Shared dialogs

**When creating**:
- New view → Place in appropriate page subdirectory
- New dialog → Place in appropriate usage subdirectory
- New page → Create corresponding subdirectory in `views/`

## Common Pitfalls to Avoid

**Note**: Many of these anti-patterns are automatically detected by CodeQL queries. See [`.github/codeql/README.md`](./codeql/README.md) for details.

**❌ Don't:**
- Use `.style()` for inline CSS
- Use `.text()` on elements (use `with` context and `ui.label()`)
- Access ORM from UI pages or API routes
- Put business logic in UI or bot commands
- Forget `async`/`await`
- Skip docstrings
- Mix authorization with business logic
- Use `AuthorizationService` (deprecated - use UIAuthorizationHelper or Permission enum)
- Use UIAuthorizationHelper in service layer (use policy framework directly)
- Forget to `await` UIAuthorizationHelper methods (they're async)
- Use prefix (chat-based) commands in Discord bot
- Use `print()` for logging in application code
- Use f-strings in logging statements
- Use inline imports (import inside functions)
- Leave trailing whitespace on lines
- Create views in root `views/` directory
- Create dialogs in root `dialogs/` directory
- Forget `await` when calling `super().show()` in dialogs
- Use `datetime.utcnow()` - it's deprecated
- Use raw `<table>` for tabular data
- Use `None` for user_id in events
- Open external links in same tab
- Trust client-provided `organization_id` without validation
- Return cross-tenant data
- Display `discord_email` to non-superadmin users
- Manually create Aerich migration files - always use `aerich migrate`

**✅ Do:**
- Use external CSS classes
- Use `with ui.element('div').classes('header'):` then `ui.label('Text')`
- Use services for all business logic
- Use repositories for data access
- Use UIAuthorizationHelper for organization permissions in UI
- Use Permission enum for global permissions in UI
- Use policy framework directly in service layer
- Always `await` UIAuthorizationHelper methods
- Enforce permissions server-side
- Use `ResponsiveTable` for tabular data
- Test on mobile viewports
- Use application commands (slash commands) for Discord
- Use `await super().show()` in dialog `show()` methods
- Delegate bot logic to services
- Use logging framework: `logger = logging.getLogger(__name__)`
- Use lazy % formatting: `logger.info("User %s", user_id)`
- Import modules at top of file
- Keep lines clean (no trailing whitespace)
- Organize views by page subdirectory
- Organize dialogs by usage subdirectory
- Use `datetime.now(timezone.utc)` for current UTC time
- Use `new_tab=True` for external links
- Use `SYSTEM_USER_ID` for system/automated actions
- Validate organization membership server-side
- Filter all queries by organization
- Emit events after successful operations
- Use `aerich migrate` to generate migrations, then edit the SQL if needed

## Adding Features

For step-by-step guides on adding new features, see:

- **[New Page](../docs/ADDING_FEATURES.md#new-page)** - Create new page with BasePage
- **[New Dialog](../docs/ADDING_FEATURES.md#new-dialog)** - Extend BaseDialog
- **[New View](../docs/ADDING_FEATURES.md#new-view-component)** - Page-specific view
- **[New Component](../docs/ADDING_FEATURES.md#new-ui-component)** - Reusable UI component
- **[New Service](../docs/ADDING_FEATURES.md#new-service--repository)** - Business logic + data access
- **[New Model](../docs/ADDING_FEATURES.md#new-database-model)** - Database model + migration
- **[New Auth Check](../docs/ADDING_FEATURES.md#new-authorization-check)** - Permission checking
- **[New Bot Command](../docs/ADDING_FEATURES.md#new-discord-bot-command)** - Discord command
- **[New API Endpoint](../docs/ADDING_FEATURES.md#new-api-endpoint)** - REST API route

## Documentation

- **[Architecture Guide](../docs/ARCHITECTURE.md)** - System architecture and components
- **[Patterns & Conventions](../docs/PATTERNS.md)** - Code patterns and best practices
- **[Adding Features Guide](../docs/ADDING_FEATURES.md)** - Step-by-step development guides
- **[Documentation Index](../docs/README.md)** - Complete documentation listing
- **[BasePage Guide](../docs/core/BASEPAGE_GUIDE.md)** - Page template usage
- **[Components Guide](../docs/core/COMPONENTS_GUIDE.md)** - UI components reference
- **[Dialog Patterns](../docs/core/DIALOG_ACTION_ROW_PATTERN.md)** - Dialog styling standards
- **[JavaScript Guidelines](../docs/core/JAVASCRIPT_GUIDELINES.md)** - JS organization
- **[Event System](../docs/systems/EVENT_SYSTEM.md)** - Event bus documentation
- **[Notification System](../docs/systems/NOTIFICATION_SYSTEM.md)** - Discord notifications
- **[Task Scheduler](../docs/systems/TASK_SCHEDULER.md)** - Background tasks
- **[RaceTime Integration](../docs/integrations/RACETIME_INTEGRATION.md)** - RaceTime.gg API
- **[Discord Permissions](../docs/integrations/DISCORD_CHANNEL_PERMISSIONS.md)** - Required permissions

## References
- **NiceGUI**: https://nicegui.io
- **Tortoise ORM**: https://tortoise.github.io
- **FastAPI**: https://fastapi.tiangolo.com
- **Discord OAuth2**: https://discord.com/developers/docs/topics/oauth2
- **Original SahasrahBot**: https://github.com/tcprescott/sahasrahbot

---

**Keep this file focused on essential rules and patterns. For detailed examples and guides, see documentation in `docs/` directory.**

**Last Updated**: November 4, 2025
