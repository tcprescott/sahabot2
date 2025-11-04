# Copilot Instructions for SahaBot2

## Project Overview
SahaBot2 (SahasrahBot2) is a NiceGUI + FastAPI web application with Discord OAuth2 authentication and Tortoise ORM for database access. The application follows strict architectural principles emphasizing separation of concerns, mobile-first design, and high code quality.

**This is the successor to the original SahasrahBot**: https://github.com/tcprescott/sahasrahbot

When porting features from the original SahasrahBot, use the GitHub repository as a reference for understanding existing functionality, business logic, and user workflows. The new codebase has a completely different architecture (NiceGUI + FastAPI vs Flask), so features should be adapted to fit the new patterns rather than directly copied.

## Architecture & Key Components

### Core Files
- **main.py**: FastAPI entry point; initializes database, configures NiceGUI, manages app lifespan, starts/stops Discord bot
- **frontend.py**: Registers all NiceGUI pages
- **config.py**: Pydantic settings for environment configuration
- **database.py**: Database initialization and connection management
- **models/**: Database models package
  - `user.py`: User model and Permission enum
  - `audit_log.py`: AuditLog model for tracking user actions
- **components/**: Reusable UI components and templates
  - `base_page.py`: Base page template with navbar and layout
- **discordbot/**: Discord bot integration
  - `client.py`: Discord bot singleton implementation with lifecycle management
  - Commands should be in separate files (e.g., `commands/admin.py`, `commands/user.py`)

### Application Layer
- **application/services/**: Business logic layer
  - `user_service.py`: User management business logic
  - `authorization_service.py`: Permission checking and authorization logic (separate from other business logic)
  - `audit_service.py`: Audit logging functionality
- **application/repositories/**: Data access layer
  - `user_repository.py`: User data access methods
  - `audit_repository.py`: Audit log data access methods

### Authentication & Authorization
- **middleware/auth.py**: Discord OAuth2 integration (`DiscordAuthService`)
  - Handles OAuth2 flow
  - Manages user sessions via NiceGUI storage
  - Provides `require_auth()` and `require_permission()` helpers

### UI Layer
- **pages/**: NiceGUI page modules
  - `home.py`: Main landing page
  - `auth.py`: Login, OAuth callback, logout pages
  - `admin.py`: Admin dashboard (requires ADMIN permission)
  - `organization_admin.py`: Organization-specific admin page
- **views/**: View components organized by page
  - Views are **organized into subdirectories** based on which pages use them
  - `views/home/`: Views used by the home page (overview, schedule, users, reports, settings, favorites, tools, help, about, welcome, archive, lorem_ipsum)
  - `views/admin/`: Views used by the admin page (admin_users, admin_organizations, admin_settings)
  - `views/organization/`: Views used by the organization admin page (org_overview, org_members, org_permissions, org_settings)
  - Each subdirectory has its own `__init__.py` that exports its views
  - The main `views/__init__.py` re-exports all views for backward compatibility
  - **When creating new views**, place them in the appropriate subdirectory based on which page will use them
  - **When creating new pages**, create a corresponding subdirectory in `views/` for that page's views
- **components/**: Reusable UI components and templates
  - `base_page.py`: Base page template with navbar and layout
  - `dialogs/`: Dialog components (UI-only) **organized by the views that use them**
    - `dialogs/admin/`: Dialogs used by admin views (user_edit, user_add, organization, global_setting)
    - `dialogs/organization/`: Dialogs used by organization views (member_permissions, invite_member, organization_invite, org_setting, stream_channel)
    - `dialogs/tournaments/`: Dialogs used by tournament views (match_seed, edit_match, submit_match, register_player)
    - `dialogs/user_profile/`: Dialogs used by user profile views (api_key, leave_organization)
    - `dialogs/common/`: Dialogs used across multiple views (base_dialog, tournament_dialogs with ConfirmDialog)
    - Each subdirectory has its own `__init__.py` that exports its dialogs
    - The main `dialogs/__init__.py` re-exports all dialogs for backward compatibility
    - **When creating new dialogs**, place them in the appropriate subdirectory based on which view will use them
- **static/css/main.css**: All application styles (no inline CSS allowed)

This application is multi-tenant. All user actions and data are scoped to Organizations (managed via the Organizations tab). Every feature we add or change must preserve tenant isolation and enforce the security model described below.

### Discord Bot Layer

  ### Multi-Tenancy & Organizations
  - **models/organizations.py**: Organization domain models
    - `Organization`: Tenant entity; parent for tenant-scoped data
    - `OrganizationMember`: Links users to organizations (membership and roles)
    - `OrganizationPermission`: Optional per-organization permission grants/roles
  - **pages/Admin > Organizations**: UI for managing organizations and memberships
  - All tenant-scoped resources must reference an organization (direct FK or via relation). Services and repositories are responsible for enforcing organization constraints in all reads and writes.
- **discordbot/**: Discord bot integration (runs as singleton within the application)
  - `client.py`: Core bot implementation extending `commands.Bot`
  - Lifecycle managed by `main.py` lifespan (starts on app startup, stops on shutdown)
  - Uses `get_bot_instance()` to access singleton from services or commands
  - **Commands should be in separate modules** organized by feature (e.g., `commands/admin.py`)

  ### 6. Multi-Tenant Isolation and Security
  - All data access and mutations must be scoped to a specific Organization (tenant).
  - Do not rely on client-provided organization identifiers without verification; validate membership and permissions server-side.
  - Service and repository methods should accept an explicit `organization_id` (or `Organization`) parameter and enforce it in queries.
  - Never return or operate on cross-tenant data. Filters must include the organization constraint for list/detail queries, updates, and deletes.
  - Audit everything with tenant context: include `organization_id` in `AuditLog` entries where applicable.
  - Caches and computed results must be keyed by organization.
  - Global roles (e.g., SUPERADMIN) may bypass tenant checks when explicitly intended; all other roles are tenant-bound.
  - **User email addresses are considered sensitive PII**: Only SUPERADMIN users may view or edit email addresses. Never display `discord_email` in organization views, member lists, dialogs, or any context accessible to non-superadmin users.

### Database
- **migrations/**: Aerich migration scripts and config
  - `tortoise_config.py`: Tortoise ORM configuration for Aerich

## Core Principles

### 1. Responsive Design for All Devices
- Design must work seamlessly on both mobile and desktop devices
- Use mobile-first approach but ensure desktop experience is polished and takes advantage of larger screens
- Use CSS media queries in `main.css` for responsive layouts
- Test all features on both mobile viewport sizes and desktop resolutions
- Ensure feature parity across all devices while optimizing layout for each form factor

### 2. Separation of Concerns
- **UI pages** (`pages/`) - Presentation only, no business logic
- **Services** (`application/services/`) - All business logic and rules
- **Repositories** (`application/repositories/`) - Data access only
- **Never** access ORM models directly from UI - always use services

### 3. Logging Standards
- **Always use the logging framework** - Never use `print()` for logging in application code
- **Import logging at module level**:
  ```python
  import logging

  logger = logging.getLogger(__name__)
  ```
- **Use lazy % formatting** in logging statements (not f-strings):
  ```python
  # ✅ Correct - lazy formatting
  logger.info("User %s logged in", user.id)
  logger.error("Failed to process %s: %s", item_id, error)

  # ❌ Wrong - f-strings or concatenation
  logger.info(f"User {user.id} logged in")  # Don't do this!
  logger.info("User " + user.id + " logged in")  # Don't do this!
  ```
- **Use appropriate log levels**:
  - `logger.debug()` - Detailed diagnostic information
  - `logger.info()` - General informational messages (app startup, route registration, etc.)
  - `logger.warning()` - Warning messages (deprecated features, recoverable issues)
  - `logger.error()` - Error messages (exceptions, failures)
  - `logger.critical()` - Critical issues (system failures)
- **Exceptions**: `print()` is acceptable in:
  - Test scripts (e.g., `test_*.py`)
  - Utility scripts (e.g., `check_*.py`, `tools/*.py`)
  - Interactive/CLI tools where user-facing output is needed
  - Code examples in docstrings

### 4. DateTime Standards
- **Always use timezone-aware datetimes** - Never use deprecated `datetime.utcnow()`
- **Use `datetime.now(timezone.utc)` for current UTC time**:
  ```python
  from datetime import datetime, timezone

  # ✅ Correct - timezone-aware UTC datetime
  current_time = datetime.now(timezone.utc)
  
  # ❌ Wrong - deprecated and timezone-naive
  current_time = datetime.utcnow()  # Don't do this!
  ```
- **Why this matters**:
  - Database `DatetimeField` returns timezone-aware datetimes
  - Mixing naive and aware datetimes causes `TypeError` when calculating deltas
  - `datetime.utcnow()` is deprecated in Python 3.12+
- **Import pattern**:
  ```python
  from datetime import datetime, timezone, timedelta
  ```

### 5. Event System for Async Notifications
- **Always emit events** for create, update, delete operations in service layer
- Events enable async notifications and decoupled side effects
- **Import EventBus and event types**:
  ```python
  from application.events import EventBus, UserCreatedEvent, UserPermissionChangedEvent
  ```
- **Emit events after successful operations**:
  ```python
  # After creating an entity
  user = await self.repository.create_user(...)
  await EventBus.emit(UserCreatedEvent(
      user_id=current_user.id,
      entity_id=user.id,
      discord_id=user.discord_id,
      username=user.discord_username,
  ))

  # After updating an entity
  updated_org = await self.repository.update(org_id, **updates)
  await EventBus.emit(OrganizationUpdatedEvent(
      user_id=current_user.id,
      organization_id=org_id,
      entity_id=org_id,
      changed_fields=list(updates.keys()),
  ))
  ```
- **Event categories available**:
  - User events: `UserCreatedEvent`, `UserUpdatedEvent`, `UserDeletedEvent`, `UserPermissionChangedEvent`
  - Organization events: `OrganizationCreatedEvent`, `OrganizationUpdatedEvent`, `OrganizationMemberAddedEvent`, `OrganizationMemberPermissionChangedEvent`, etc.
  - Tournament events: `TournamentCreatedEvent`, `TournamentUpdatedEvent`, `TournamentStartedEvent`, `TournamentEndedEvent`
  - Race/Match events: `RaceSubmittedEvent`, `RaceApprovedEvent`, `RaceRejectedEvent`, `MatchScheduledEvent`, `MatchCompletedEvent`
  - Invite events: `InviteCreatedEvent`, `InviteAcceptedEvent`, `InviteRejectedEvent`, `InviteExpiredEvent`
  - Other events: `DiscordGuildLinkedEvent`, `DiscordGuildUnlinkedEvent`, `PresetCreatedEvent`, `PresetUpdatedEvent`
- **Event best practices**:
  - Emit events AFTER successful database operations (not before)
  - Include all relevant context in the event (user_id, organization_id, entity_id, domain-specific fields)
  - Fire-and-forget pattern - don't await event handler results
  - Event handlers run async and errors are isolated (won't affect main operation)
- **See docs/EVENT_SYSTEM.md for full documentation**

  ### Tenant-aware Authorization
  ```python
  from application.services.authorization_service import AuthorizationService

  auth_z = AuthorizationService()

  # Resolve current org (from session, page context, or explicit parameter)
  organization_id = current_org_id()

  # Membership and permission checks MUST include organization context
  if not auth_z.is_member(user, organization_id):
      raise PermissionError("Not a member of this organization")

  # For privileged actions, evaluate tenant roles first, then global overrides
  if auth_z.can_manage_users(user, organization_id) or auth_z.is_superadmin(user):
      ...  # proceed
  ```

  Guidelines:
  - Pass `organization_id` through from UI → services → repositories.
  - In repositories, always include the organization filter (`.filter(organization_id=...)`).
  - Do not infer organization from arbitrary resource IDs without validating ownership.

### 4. External CSS Only & Color Scheme
- **No** inline styles via `.style()` method
- All CSS in `static/css/main.css`
- Use semantic, human-friendly class names (e.g., `card`, `btn-primary`, `navbar`)
- Include CSS in pages: `ui.add_head_html('<link rel="stylesheet" href="/static/css/main.css">')`

#### Official Color Palette
The application uses a five-color palette with automatic dark mode support. Light-to-dark order is preserved across modes.

**Light Mode Colors (Primary Palette):**

  ### Tenant-aware Service Usage
  ```python
  org_id = current_org_id()
  users = await user_service.get_users_for_org(org_id)
  user  = await user_service.update_user_permission_in_org(org_id, user_id, Permission.ADMIN)
  ```
  Service and repository method signatures should include the organization context for tenant-scoped data. Prefer explicit `org_id` parameters over implicit globals.
```css
--seasalt:  #f8f8f8;  /* Very light neutral: page backgrounds and muted surfaces */
--old-gold: #d0c040;  /* Primary actions: buttons, links, highlights */
--olive:    #988818;  /* Secondary accents: badges, tags, emphasis */
--olive-2:  #7c6f13;  /* Strong accent / warnings / borders emphasis */
   - Tenant scope: models that represent tenant data include an `organization` FK. Queries must filter by organization.
--black:    #000000;  /* Primary text and strong borders */
```

  Tenant context in pages:
  - Resolve/select the current organization (e.g., from session or a selector in the navbar/organizations tab).
  - Pass `organization_id` to all service calls.
  - Hide UI elements that cross tenant boundaries; always enforce on the server as well.

**Dark Mode Colors (Adjusted for Contrast):**
```css
--black-dark:   #0f0f0f; /* Dark backgrounds and surfaces */
--old-gold-dark:#e6d65a; /* Lightened primary for readability on dark */
  5. Ensure all reads/writes accept and enforce `organization_id`
--olive-dark:   #c0b339; /* Lightened secondary for dark mode accents */
--olive-2-dark: #b3952f; /* Lightened strong accent for visibility */
--seasalt-dark: #f2f2f2; /* Light text on dark backgrounds */
```
  4. For tenant-scoped actions, add `organization_id` to method signatures and checks

**Usage Guidelines:**
- **Backgrounds**: Use `seasalt` (light) or `black-dark` (dark)
- **Primary Actions**: Use `old-gold` for buttons, links, primary CTAs (use `old-gold-dark` on dark)
- **Secondary Elements**: Use `olive` for badges, tags, secondary accents (use `olive-dark` on dark)
- **Emphasis/Warnings**: Use `olive-2` (use `olive-2-dark` on dark)
- **Text/Borders**: Use `black` (light mode) or `seasalt-dark` (dark mode)

**Implementation:**
  9. If the model is tenant data, include an `organization` FK and add indexes on `(organization_id, ...)` where appropriate
- Define CSS variables in `:root` for light mode
- Override in `.body--dark` or `.q-dark` selectors for dark mode
- Map semantic tokens (e.g., `--primary-color`, `--background-color`) to the palette
- Ensure sufficient contrast ratios (WCAG AA minimum)
- Test both light and dark modes for readability

### 5. Discord OAuth2 Authentication
- All users authenticate via Discord
  - ❌ Don't forget tenant scoping in queries and service methods
  - ❌ Don't trust client-provided `organization_id` without validating membership
  - ❌ Don't leak cross-tenant data via joins, exports, or background jobs
- OAuth flow handled in `middleware/auth.py`
- User info synced to database on login
- Session managed via NiceGUI `app.storage.user`
  - ✅ Do ensure every tenant-scoped operation includes `organization_id`
  - ✅ Do record tenant context in audit logs and metrics
  - ✅ Do design caches and background tasks to be organization-aware

### 6. Database-Driven Authorization
- Authorization logic in `AuthorizationService` (separate from business logic)
- Permissions stored in database (User.permission field)
- Server-side enforcement via `require_permission()`
- UI can conditionally show elements based on permissions, but must enforce server-side

### 7. High Code Quality
- **Always** use async/await
- **All** public functions must have docstrings
- Type hints on function parameters and returns
- Descriptive variable names
- Comments for complex logic
- **No Trailing Whitespace**: Remove trailing whitespace from all lines, including blank lines
  - ✅ Clean lines with no trailing spaces or tabs
  - ❌ Lines ending with spaces, tabs, or other whitespace characters
  - Exception: Only when absolutely required by the language/format (rare)
- **Module Imports**: All imports at module level (top of file), never inline
  - ✅ `from components.sidebar import Sidebar` at top of file
  - ❌ `from components.sidebar import Sidebar` inside function
  - Inline imports can cause issues with class identity, state persistence, and NiceGUI bindings
- **Logging**: Use lazy % formatting in logging statements (not f-strings)
  - ✅ `logger.info("User %s logged in", user.id)`
  - ❌ `logger.info(f"User {user.id} logged in")`
- **NiceGUI Elements**: Elements don't have a `.text()` method
  - ✅ `with ui.element('div').classes('header'): ui.label('Text')`
  - ❌ `ui.element('div').classes('header').text('Text')`  # AttributeError!

### 8. Discord Bot Architecture
- **Bot as Presentation Layer**: Discord bot is part of the presentation layer (like UI pages)
- **Never** access ORM models directly from bot commands - always use services
- **Never** put business logic in bot commands - delegate to services
- **Application Commands Only**: Use Discord's native application commands (slash commands, context menus)
  - **Never** use chat-based (prefix) commands
  - All commands must be registered as application commands via `@app_commands.command()`
- **Singleton Pattern**: Bot runs as singleton, access via `get_bot_instance()` from `bot.client`
- **Separation**: Bot commands should only handle Discord interaction (parsing, responding), delegate all logic to services

### 9. Porting Features from Original SahasrahBot
When implementing features that existed in the original SahasrahBot (https://github.com/tcprescott/sahasrahbot), follow this workflow:

**Reference the Original Implementation:**
1. Use the GitHub repository link to review the original feature's implementation
2. Understand the business logic, user workflows, and data models used
3. Identify the core functionality that needs to be preserved
4. Note any Discord bot commands, API endpoints, or UI elements involved

**Adapt to New Architecture:**
1. **Don't copy-paste Flask code** - The original uses Flask, the new version uses NiceGUI + FastAPI
2. **Refactor into layers**: Break the feature into services (business logic), repositories (data access), and UI/API (presentation)
3. **Add multi-tenancy**: Most features should be organization-scoped (unless explicitly global like user management)
4. **Use new patterns**: Follow the established patterns in SahaBot2 (BasePage, service layer authorization, async/await, etc.)
5. **Modernize where appropriate**: Take the opportunity to improve UX, add validation, enhance error handling

**Example Porting Workflow:**
```
Original SahasrahBot Feature: Tournament Management
1. Review: alttpr/cogs/tournament.py for Discord commands
2. Review: alttprbot_api/api/tournament.py for API endpoints
3. Review: alttprbot/database/tournament.py for data models
4. Adapt: Create models/tournaments.py with Organization FK
5. Adapt: Create application/services/tournament_service.py with business logic
6. Adapt: Create api/routes/tournaments.py following established API patterns
7. Adapt: Create views/tournaments/ for UI components
8. Adapt: Port Discord commands to discordbot/commands/tournaments.py
```

**Key Differences to Remember:**
- Original: Flask web app + separate Discord bot process
- New: NiceGUI + FastAPI with embedded Discord bot
- Original: Single-tenant (one instance per community)
- New: Multi-tenant (organizations isolate communities)
- Original: Role-based permissions via Discord roles
- New: Database-driven permissions per organization
- Original: Synchronous database operations
- New: Async Tortoise ORM
- Original: Jinja2 templates
- New: NiceGUI component-based UI

**When in Doubt:**
- Preserve the core user experience and workflows
- Adapt the implementation to fit SahaBot2 architecture
- Ask for clarification if business logic is unclear
- Reference the original repo liberally via GitHub URL

## Development Workflows

### Installation
```bash
poetry install
```

### Server Management
- The development server is typically already running
- **Do NOT** attempt to start the server in tool calls or tests
- If server restart is needed, user will handle it manually
- Use `./start.sh dev` (port 8080, auto-reload) or `./start.sh prod` (port 80, multi-worker) only when explicitly requested

### Database Migrations
- **Init**: `poetry run aerich init-db`
- **Create**: `poetry run aerich migrate --name "description"`
- **Apply**: `poetry run aerich upgrade`
- **Rollback**: `poetry run aerich downgrade`

### Environment
- Configuration in `.env` (see `.env.example`)
- Settings loaded via Pydantic in `config.py`
- Discord credentials required for OAuth2 and bot
  - `DISCORD_CLIENT_ID`: OAuth2 application ID
  - `DISCORD_CLIENT_SECRET`: OAuth2 secret
  - `DISCORD_BOT_TOKEN`: Bot authentication token

## Patterns & Conventions

### Async/Await
- All database operations are async
- All service methods are async
- UI event handlers should be async functions
- Use `await` for service calls, repository calls, and ORM queries

### Page Structure (Using BasePage Template)
All pages should use the `BasePage` component for consistent layout:

```python
from components.base_page import BasePage

def register():
    """Register page routes."""

    @ui.page('/path')
    async def page_name():
        """Page docstring."""
        # Create base page (simple, authenticated, or admin)
        base = BasePage.simple_page(title="Page Title", active_nav="home")
        # or base = BasePage.authenticated_page(title="Page Title", active_nav="nav_item")
        # or base = BasePage.admin_page(title="Admin Page", active_nav="admin")

        async def content(page: BasePage):
            """Render page content - has access to page.user."""
            with ui.element('div').classes('card'):
                ui.label(f'Hello, {page.user.discord_username}!')

        await base.render(content)()
```

**BasePage Helper Methods:**
- `BasePage.simple_page()` - No auth required, navbar shown
- `BasePage.authenticated_page()` - Requires login
- `BasePage.admin_page()` - Requires admin permissions
- Custom: `BasePage(title, active_nav, require_permission=Permission.X)`

**Benefits:**
- Automatic CSS loading
- Consistent navbar across all pages
- Built-in authentication/authorization checks
- Access to current user via `page.user`
- Automatic logout handling
- **Automatic notification display from query parameters**

**Query Parameter Notifications:**
BasePage automatically displays notifications based on query parameters:
- `?success=message_text` - Shows positive (green) notification
- `?error=message_text` - Shows negative (red) notification
- `?message=message_text` - Shows info (blue) notification

Messages with underscores are automatically converted to spaces and title-cased.

**Example Usage:**
```python
# After successful operation, redirect with success message
ui.navigate.to('/orgs/1/admin?view=discord_servers&success=discord_server_linked')
# User sees: "Discord Server Linked" (green notification)

# After failed operation, redirect with error message
ui.navigate.to('/orgs/1/admin?view=members&error=failed_to_add_member')
# User sees: "Failed To Add Member" (red notification)

# For informational messages
ui.navigate.to('/org/123?view=matches&message=match_rescheduled')
# User sees: "Match Rescheduled" (blue notification)
```

**Dynamic Content with View Parameter:**
For pages using `use_dynamic_content=True`, use `?view=section_name` to load specific views:
```python
# Redirect to specific view within organization admin
ui.navigate.to('/orgs/1/admin?view=discord_servers')
# Loads the discord_servers view automatically
```

### Service Usage
```python
# Initialize service
user_service = UserService()

# Call async methods
users = await user_service.get_all_users()

# Services handle all business logic
user = await user_service.update_user_permission(user_id, Permission.ADMIN)
```

### Authorization
```python
# Check permissions in service
from application.services.authorization_service import AuthorizationService
auth_z = AuthorizationService()

# Check if user can perform action
if auth_z.can_access_admin_panel(user):
    # Show admin features
    pass

# Enforce permissions in pages
user = DiscordAuthService.require_permission(Permission.ADMIN, '/admin')
if not user:
    return  # Redirected to login or home
```

### API Routes & Authorization
All API routes follow a consistent pattern with authorization enforced at the service layer:

**Key Principles:**
- **Authorization at Service Layer Only**: API routes should NOT perform authorization checks
- **Pass current_user to services**: Routes extract the authenticated user via `Depends(get_current_user)` and pass to services
- **Services enforce permissions**: All authorization logic lives in service methods
- **Return empty results on unauthorized**: Services return empty lists/None rather than raising exceptions for unauthorized requests
- **Rate limiting only**: API routes should only have `Depends(enforce_rate_limit)` in dependencies

**API Route Pattern:**
```python
from fastapi import APIRouter, Depends
from api.deps import get_current_user, enforce_rate_limit
from application.services.user_service import UserService
from models import User

router = APIRouter(prefix="/resource", tags=["resource"])

@router.get(
    "/",
    dependencies=[Depends(enforce_rate_limit)],  # Only rate limit, NO permission check
    summary="List Resources",
)
async def list_resources(
    current_user: User = Depends(get_current_user)  # Extract authenticated user
) -> ResourceListResponse:
    """
    List resources.

    Authorization is enforced at the service layer.
    """
    service = ResourceService()
    # Pass current_user to service - authorization happens there
    resources = await service.list_resources(current_user)
    return ResourceListResponse(items=resources, count=len(resources))
```

**Service Layer Authorization:**
```python
class ResourceService:
    async def list_resources(self, current_user: Optional[User]) -> list[Resource]:
        """
        List resources visible to the user.

        Authorization is enforced here - only returns resources the user can access.
        """
        # Check permissions
        if not current_user or not current_user.has_permission(Permission.MODERATOR):
            logger.warning("Unauthorized access attempt by user %s", current_user.id if current_user else None)
            return []  # Return empty list, don't raise exception

        # Fetch and return data
        return await self.repository.list_all()
```

**Why This Pattern:**
- ✅ Centralized authorization logic in services (single source of truth)
- ✅ Consistent behavior across UI and API endpoints
- ✅ Services can be tested independently of FastAPI routing
- ✅ Multi-tenant checks happen in one place
- ✅ Graceful degradation (empty results vs errors)
- ❌ Don't use `Depends(require_permission())` in API routes
- ❌ Don't check permissions in API route handlers
- ❌ Don't raise 403 exceptions for authorization in services (return empty instead)

### CSS Classes
**Note**: All CSS must use the official color palette defined above. Use CSS variables for colors.

- Container: `page-container`, `content-wrapper`
- Cards: `card`, `card-header`, `card-body`
- Buttons: `btn`, `btn-primary`, `btn-secondary`, `btn-danger`
- Navigation: `navbar`, `navbar-brand`, `navbar-menu`, `navbar-link`
- Tables: `data-table`
- Badges: `badge`, `badge-admin`, `badge-moderator`, `badge-user`, `badge-success`, `badge-danger`, `badge-warning`, `badge-info`
- Utilities: `text-center`, `mt-1`, `mb-2`, `flex`, `gap-md`

**Color Usage in Classes:**
- Primary buttons/links: `steel-blue` / `steel-blue-dark`
- Secondary elements: `pomp-and-power` / `pomp-and-power-dark`
- Success/positive: Use `steel-blue` or custom success color
- Warning/attention: `brown-sugar` / `brown-sugar-dark`
- Error/danger: Adjust `eggplant` or use complementary red
- Text: `eggplant` (light) / `antique-white-dark` (dark)
- Backgrounds: `antique-white` (light) / `eggplant-dark` (dark)

### Discord Bot Commands
Bot commands follow the same separation of concerns as the rest of the application:

```python
# Example bot command (in discordbot/commands/user.py)
from discord import app_commands
from discordbot.client import get_bot_instance
from application.services.user_service import UserService

@app_commands.command(name="profile", description="View your profile")
async def profile(interaction: discord.Interaction):
    """Display user profile information."""
    # Get service instance
    user_service = UserService()

    # Fetch data via service (no direct ORM access)
    user = await user_service.get_user_by_discord_id(interaction.user.id)

    if not user:
        await interaction.response.send_message("User not found", ephemeral=True)
        return

    # Format and respond
    await interaction.response.send_message(
        f"Username: {user.discord_username}\nPermission: {user.permission.name}",
        ephemeral=True
    )

# Register command in bot setup
bot = get_bot_instance()
if bot:
    bot.tree.add_command(profile)
```

**Key Points:**
- Use `@app_commands.command()` for slash commands (never prefix commands)
- Delegate all business logic to services
- Never access ORM models directly
- Handle Discord interactions (parsing, responding) only
- Use `get_bot_instance()` to access bot singleton

## Models

### User
- **Fields**: discord_id, discord_username, discord_discriminator, discord_avatar, discord_email, permission, is_active
- **Methods**: `has_permission()`, `is_admin()`, `is_moderator()`
- **Permissions**: USER (0), MODERATOR (50), ADMIN (100), SUPERADMIN (200)

### AuditLog
- **Fields**: user (FK), action, details (JSON), ip_address, created_at
- **Purpose**: Track user actions for security and compliance

## Integration Points

### Discord OAuth2
- Authorization URL generated in `DiscordAuthService.get_authorization_url()`
- Callback handled at `/auth/callback`
- User info fetched from Discord API
- User created/updated in database

### Database
- MySQL via Tortoise ORM
- Connection configured in `config.py` via environment variables
- Migrations managed by Aerich

### NiceGUI Storage
- User session in `app.storage.user`
- OAuth state for CSRF protection
- Redirect URL after login

## Adding Features

### New Page
### UI Layer
- **pages/**: NiceGUI page modules
  - `home.py`: Main landing page
  - `auth.py`: Login, OAuth callback, logout pages
  - `admin.py`: Admin dashboard (requires ADMIN permission)
- **components/**: Reusable UI components
  - `header.py`: Header bar
  - `footer.py`: Footer bar (not fixed)
  - `sidebar.py`: Sidebar flyout/persistent navigation
  - `data_table.py`: Responsive table helper (desktop table, mobile grid)
  - `dialogs/`: Dialog components (UI-only)
    - `user_edit_dialog.py`: Edit User dialog
- **static/css/main.css**: All application styles (no inline CSS allowed)
5. Register in `frontend.py`

Example:
```python
from nicegui import ui
from components.base_page import BasePage
 - **Dialogs** (`components/dialogs/`) - UI-only modal components; delegate logic to services

def register():
    @ui.page('/mypage')
    async def my_page():
        base = BasePage.simple_page(title="My Page", active_nav="mypage")

        async def content(page: BasePage):
            with ui.element('div').classes('card'):
                ui.label('My content here')
### New Dialog
All dialogs should extend `BaseDialog` for consistent structure and behavior.

1. **Determine which view will use the dialog** (admin, organization, tournaments, user_profile, or multiple)
2. **Create dialog module in appropriate subdirectory**:
   - For admin views: `components/dialogs/admin/my_dialog.py`
   - For organization views: `components/dialogs/organization/my_dialog.py`
   - For tournament views: `components/dialogs/tournaments/my_dialog.py`
   - For user profile views: `components/dialogs/user_profile/my_dialog.py`
   - For shared/common: `components/dialogs/common/my_dialog.py`
3. Extend `BaseDialog` (from `components.dialogs.common.base_dialog`) and implement `_render_body()` method
4. Keep it presentation-only; call services for business logic
5. Use BaseDialog helper methods for common patterns
6. **Export from subdirectory's `__init__.py`** (e.g., `components/dialogs/admin/__init__.py`)
7. **Re-export from main `dialogs/__init__.py`** for backward compatibility

**BaseDialog provides:**
- `create_dialog(title, icon, max_width)` - Create dialog with standard card structure
- `create_form_grid(columns)` - Responsive form grid (1-2 columns)
- `create_actions_row()` - Standardized action buttons container
- `create_permission_select(...)` - Permission dropdown with proper enum handling
- `create_info_row(label, value)` - Read-only information display
- `create_section_title(text)` - Section header within dialog
- `show()` / `close()` - Display and dismiss dialog

Example:
```python
from components.dialogs.common.base_dialog import BaseDialog
from nicegui import ui
from models import User

class MyDialog(BaseDialog):
    """Custom dialog extending BaseDialog."""

    def __init__(self, user: User, on_save=None):
        super().__init__()
        self.user = user
        self.on_save = on_save

    async def show(self):
        """Display the dialog."""
        self.create_dialog(
            title=f'Edit {self.user.discord_username}',
            icon='edit',
        )
        super().show()

    def _render_body(self):
        """Render dialog content."""
        # Use form grid for responsive layout
        with self.create_form_grid(columns=2):
            with ui.element('div'):
                ui.input(label='Name').classes('w-full')
            with ui.element('div'):
                ui.input(label='Email').classes('w-full')

        ui.separator()

        # Use actions row for buttons (Convention: neutral/negative left, positive right)
        with self.create_actions_row():
            # Neutral/negative action on the far left
            ui.button('Cancel', on_click=self.close).classes('btn')
            # Positive action on the far right
            ui.button('Save', on_click=self._save).classes('btn').props('color=positive')

    async def _save(self):
        """Save and close."""
        # Business logic via services
        # ...
        if self.on_save:
            await self.on_save()
        await self.close()

# Usage in views:
dialog = MyDialog(user=user, on_save=refresh_callback)
await dialog.show()
```

**Key Benefits:**
- Consistent card styling and layout
- Built-in permission select with enum normalization
- Responsive form grids
- Standardized action button placement
- Reusable helper methods reduce boilerplate

### Dialog Styling Standards

All dialogs in the application must follow these styling conventions for consistency:

#### 1. **Use BaseDialog for All Dialogs**
- Extend `BaseDialog` from `components.dialogs.common.base_dialog`
- Call `create_dialog(title, icon, max_width)` in the `show()` method
- Implement `_render_body()` to add dialog content
- Use `await super().show()` after creating the dialog

#### 2. **Dialog Structure**
```python
async def show(self):
    """Display the dialog."""
    self.create_dialog(
        title='Dialog Title',
        icon='icon_name',           # Material icon
        max_width='dialog-card'     # Default width, or custom like '800px'
    )
    await super().show()            # Don't forget 'await'!

def _render_body(self):
    """Render dialog content."""
    # Wrap entire body in column for consistent spacing
    with ui.column().classes('full-width gap-md'):
        # Use section titles
        self.create_section_title('Section Name')
        
        # Use form grid for inputs
        with self.create_form_grid(columns=2):
            with ui.element('div'):
                ui.input(label='Field 1')
            with ui.element('div'):
                ui.input(label='Field 2')
        
        ui.separator()  # Use plain separator (no classes needed)
        
        # Actions at the bottom
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Save', on_click=self._save).classes('btn').props('color=positive')
```

#### 3. **Validation Messages**
Use consistent styling for validation feedback:
```python
# Success message
with ui.row().classes('items-center gap-2 p-3 rounded bg-positive text-white'):
    ui.icon('check_circle')
    ui.label('Success message')

# Error message
with ui.row().classes('items-center gap-2 p-3 rounded bg-negative text-white'):
    ui.icon('error')
    ui.label('Error message')

# Warning message
with ui.row().classes('items-center gap-2 p-3 rounded bg-warning text-white'):
    ui.icon('warning')
    ui.label('Warning message')
```

#### 4. **View-Only Dialogs (Not Using BaseDialog)**
For simple view dialogs in views (not reusable components), use this pattern:
```python
async def _view_item(self, item):
    """View item details in a dialog."""
    with ui.dialog() as dialog:
        with ui.element('div').classes('card dialog-card'):
            # Header
            with ui.element('div').classes('card-header'):
                with ui.row().classes('items-center justify-between w-full'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('visibility').classes('icon-medium')
                        ui.label(f'Item: {item.name}').classes('text-xl text-bold')
                    ui.button(icon='close', on_click=dialog.close).props('flat round dense')
            
            # Body
            with ui.element('div').classes('card-body'):
                # Metadata section with icons
                with ui.column().classes('gap-2 mb-4'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('category', size='sm')
                        ui.label('Category info').classes('text-sm')
                    
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('person', size='sm')
                        ui.label('Creator info').classes('text-sm')
                
                ui.separator()
                
                # Main content
                ui.label('Content Title').classes('font-bold mt-4 mb-2')
                ui.label('Content goes here...')
                
                # Action buttons
                with ui.row().classes('justify-end gap-2 mt-4'):
                    ui.button('Action', on_click=some_action).classes('btn').props('color=primary')
                    ui.button('Close', on_click=dialog.close).classes('btn')
    
    dialog.open()
```

#### 5. **Key CSS Classes**
- **Dialog container**: `card dialog-card`
- **Dialog header**: `card-header`
- **Dialog body**: `card-body`
- **Header icon**: `icon-medium` (2rem size)
- **Metadata icons**: `size='sm'` (small icons inline with text)
- **Row spacing**: `items-center gap-2` (for icon + text rows)
- **Button styling**: `.classes('btn')` with `.props('color=positive|primary|negative')`

#### 6. **Common Mistakes to Avoid**
- ❌ Don't use generic `ui.card()` - use `ui.element('div').classes('card dialog-card')`
- ❌ Don't forget `await super().show()` in dialog classes
- ❌ Don't use inline background colors - use `bg-positive`, `bg-negative`, `bg-warning`
- ❌ Don't mix dialog patterns - either extend BaseDialog OR use view-only pattern
- ❌ Don't forget to call `dialog.open()` for view-only dialogs
- ✅ Do use semantic icons with consistent sizing
- ✅ Do use `text-white` with colored backgrounds for contrast
- ✅ Do organize metadata with icon + label rows
- ✅ Do use `ui.separator()` without custom classes

        await base.render(content)()
```

### New UI Component
1. Create component file in `components/`
2. Define reusable component class or function
3. Export from `components/__init__.py`
4. Add component-specific CSS to `static/css/main.css`
5. Use in pages by importing from `components`

**Table Components**:
- **Always prefer `ResponsiveTable`** (from `components/data_table.py`) for displaying tabular data
- Only use raw HTML `<table>` elements when absolutely necessary (e.g., complex custom rendering that ResponsiveTable doesn't support)
- `ResponsiveTable` provides:
  - Automatic mobile-responsive layout (stacks on small screens)
  - Consistent styling via `.data-table` class
  - Support for custom cell rendering via `cell_render` callbacks
  - `data-label` attributes for mobile accessibility
- **Example usage**:
  ```python
  from components.data_table import ResponsiveTable, TableColumn
  
  columns = [
      TableColumn(label='Name', key='name'),
      TableColumn(label='Status', cell_render=lambda row: ui.badge(row.status)),
  ]
  
  table = ResponsiveTable(columns=columns, rows=data)
  await table.render()
  ```

**DateTime Display**:
- **Always use `DateTimeLabel.create()`** (from `components/datetime_label.py`) for displaying datetime values
- DateTimeLabel is a **static utility class**, not a constructor-based component
- Provides automatic timezone conversion and locale-aware formatting
- **CORRECT usage**:
  ```python
  from components.datetime_label import DateTimeLabel
  
  # Relative time (e.g., "2 hours ago")
  DateTimeLabel.create(user.created_at, format_type='relative')
  
  # Full datetime
  DateTimeLabel.create(match.scheduled_at, format_type='datetime', classes='text-bold')
  
  # Date only
  DateTimeLabel.create(event.start_date, format_type='date')
  ```
- **WRONG usage**:
  ```python
  DateTimeLabel(dt)  # ❌ TypeError - not a constructor!
  DateTimeLabel.create(dt, format='relative')  # ❌ Parameter is 'format_type' not 'format'
  dt.strftime('%Y-%m-%d')  # ❌ Use DateTimeLabel for consistent timezone handling
  ```

### New View
Views are page-specific content modules. They should be organized by which page uses them.

1. **Determine which page will use the view** (home, admin, organization_admin, or new page)
2. **Create view file in appropriate subdirectory**:
   - For home page: `views/home/my_view.py`
   - For admin page: `views/admin/my_view.py`
   - For organization page: `views/organization/my_view.py`
   - For new page: Create `views/newpage/` directory first
3. **Export from subdirectory's `__init__.py`**:
   ```python
   from views.home.my_view import MyView
   __all__ = [..., 'MyView']
   ```
4. **Re-export from main `views/__init__.py`** for backward compatibility:
   ```python
   from views.home import MyView
   __all__ = [..., 'MyView']
   ```
5. **Import in page** using subdirectory path:
   ```python
   from views.home import MyView
   # or
   from views import MyView  # backward compatible
   ```
6. **Keep views presentation-only** - delegate all business logic to services

**Example view structure:**
```python
"""
My view module.

Description of what this view displays.
"""
from nicegui import ui
from components.card import Card

class MyView:
    """View for displaying my content."""

    def __init__(self, user, service):
        self.user = user
        self.service = service

    async def render(self):
        """Render the view content."""
        data = await self.service.get_data()
        with Card.create(title='My Title'):
            ui.label(f'Hello {self.user.discord_username}')
```

### New Business Logic
1. Create service in `application/services/`
2. Create repository in `application/repositories/` for data access
3. **Import and emit events for all create/update/delete operations**:
   ```python
   from application.events import EventBus, EntityCreatedEvent, EntityUpdatedEvent
   
   # After successful create
   entity = await self.repository.create(...)
   await EventBus.emit(EntityCreatedEvent(
       user_id=current_user.id,
       organization_id=org_id,  # if tenant-scoped
       entity_id=entity.id,
       # ... domain-specific fields
   ))
   
   # After successful update
   updated = await self.repository.update(entity_id, **updates)
   await EventBus.emit(EntityUpdatedEvent(
       user_id=current_user.id,
       organization_id=org_id,
       entity_id=entity_id,
       changed_fields=list(updates.keys()),
   ))
   ```
4. Use service from UI pages
5. Add docstrings and type hints

### New Authorization Check
1. Add method to `AuthorizationService`
2. Use in pages for conditional rendering
3. Enforce server-side with `require_permission()`

### New Model
1. Define in `models/` directory (create new file or add to existing)
2. Export from `models/__init__.py`
3. Update `migrations/tortoise_config.py` to include new model module
4. Update `database.py` to include new model module
5. Create migration: `poetry run aerich migrate --name "add_model"`
6. Apply migration: `poetry run aerich upgrade`
7. Create repository in `application/repositories/`
8. Create service in `application/services/`

### New Discord Bot Command
1. Create command file in `discordbot/commands/` (e.g., `discordbot/commands/user_commands.py`)
2. Use `@app_commands.command()` decorator (never prefix commands)
3. Delegate all business logic to services
4. Handle only Discord interaction (parsing, responding)
5. Register commands with bot tree in bot setup
6. Add docstrings and type hints

Example:
```python
# discordbot/commands/admin_commands.py
from discord import app_commands
import discord
from application.services.user_service import UserService

@app_commands.command(name="ban", description="Ban a user")
@app_commands.describe(user="User to ban", reason="Reason for ban")
async def ban_user(interaction: discord.Interaction, user: discord.User, reason: str):
    """Ban a user from the system."""
    # Use service for business logic
    user_service = UserService()
    result = await user_service.ban_user(user.id, reason)

    # Respond to interaction
    await interaction.response.send_message(
        f"User {user.mention} has been banned.",
        ephemeral=True
    )
```

## Testing
- Use pytest for testing
- Test services independently of UI
- Mock repositories in service tests
- Test authorization logic thoroughly

## Common Pitfalls to Avoid
- ❌ Don't use `.style()` for inline CSS
- ❌ Don't use `.text()` on elements (use `with` context and `ui.label()` instead)
- ❌ Don't access ORM from UI pages
- ❌ Don't put business logic in UI
- ❌ Don't forget async/await
- ❌ Don't skip docstrings
- ❌ Don't mix authorization with business logic
- ❌ Don't use prefix (chat-based) commands in Discord bot
- ❌ Don't access ORM from bot commands
- ❌ Don't put business logic in bot commands
- ❌ Don't use `print()` for logging in application code (use logging framework)
- ❌ Don't use f-strings in logging statements (use lazy % formatting)
- ❌ Don't use inline imports (import inside functions) - always import at module level
- ❌ Don't leave trailing whitespace on any lines (including blank lines)
- ❌ Don't create views in the root `views/` directory - always use the appropriate subdirectory
- ❌ Don't create dialogs in the root `dialogs/` directory - always use the appropriate subdirectory
- ❌ Don't forget `await` when calling `super().show()` in dialog classes (causes RuntimeWarning)
- ❌ Don't use `datetime.utcnow()` - it's deprecated and timezone-naive (use `datetime.now(timezone.utc)`)
- ❌ Don't use raw HTML `<table>` elements for tabular data - use `ResponsiveTable` component instead
- ✅ Do use external CSS classes
- ✅ Do use `with ui.element('div').classes('header'):` and then `ui.label('Text')`
- ✅ Do use services for all business logic
- ✅ Do use repositories for data access
- ✅ Do enforce permissions server-side
- ✅ Do use `ResponsiveTable` for all tabular data displays
- ✅ Do test on mobile viewports
- ✅ Do use application commands (slash commands) for Discord bot
- ✅ Do always use `await super().show()` in dialog `show()` methods (not `super().show()`)
- ✅ Do delegate all bot logic to services
- ✅ Do use the logging framework with `logger = logging.getLogger(__name__)`
- ✅ Do use lazy % formatting in logging: `logger.info("User %s", user_id)`
- ✅ Do import all modules at the top of the file (module level)
- ✅ Do keep all lines clean with no trailing whitespace
- ✅ Do organize views into subdirectories by page (views/home/, views/admin/, views/organization/)
- ✅ Do organize dialogs into subdirectories by view usage (dialogs/admin/, dialogs/organization/, dialogs/tournaments/, dialogs/user_profile/, dialogs/common/)
- ✅ Do use timezone-aware datetimes: `datetime.now(timezone.utc)` for current UTC time

## References
- NiceGUI: https://nicegui.io
- Tortoise ORM: https://tortoise.github.io
- FastAPI: https://fastapi.tiangolo.com
- Discord OAuth2: https://discord.com/developers/docs/topics/oauth2

---
Keep this file updated as architecture evolves. When adding new patterns or conventions, document them here for future reference.
