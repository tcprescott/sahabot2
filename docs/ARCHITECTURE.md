# SahaBot2 Architecture Guide

## Overview

SahaBot2 is a **multi-tenant NiceGUI + FastAPI web application** with Discord OAuth2 authentication and Tortoise ORM for database access. The application emphasizes strict separation of concerns, mobile-first responsive design, and high code quality.

**Technology Stack**:
- **Backend**: FastAPI (Python async web framework)
- **Frontend**: NiceGUI (Python-based reactive UI framework)
- **Database**: MySQL via Tortoise ORM (async ORM)
- **Authentication**: Discord OAuth2
- **Bot**: Discord.py (embedded within application)
- **Background Jobs**: APScheduler (task scheduling)

## Architectural Layers

The application follows a clean **four-layer architecture**:

```
┌─────────────────────────────────────┐
│     Presentation Layer              │
│  (UI Pages, API Routes, Discord)    │
├─────────────────────────────────────┤
│     Service Layer                   │
│  (Business Logic & Authorization)   │
├─────────────────────────────────────┤
│     Repository Layer                │
│  (Data Access)                      │
├─────────────────────────────────────┤
│     Model Layer                     │
│  (Database Models)                  │
└─────────────────────────────────────┘
```

### Layer Responsibilities

1. **Presentation Layer**: Accepts input, displays output, NO business logic
2. **Service Layer**: All business logic, validation, authorization
3. **Repository Layer**: Database queries, data access patterns
4. **Model Layer**: Data structure definitions

**Critical Rule**: Never skip layers! UI/API → Services → Repositories → Models

## Core Files & Entry Points

### Application Bootstrap

#### `main.py` - FastAPI Entry Point
**Responsibilities**:
- Initialize FastAPI application
- Configure NiceGUI integration
- Initialize database connection (Tortoise ORM)
- Manage application lifespan events
- Start/stop Discord bot
- Configure middleware and static files

**Key Functions**:
- `lifespan()`: Async context manager for app startup/shutdown
- Database initialization happens here
- Bot lifecycle management

#### `frontend.py` - Page Registration
**Responsibilities**:
- Import all page modules
- Call each page's `register()` function
- Central registry for all NiceGUI routes

**Usage**:
```python
def init_frontend():
    """Initialize all frontend pages."""
    from pages import home, auth, admin, tournaments
    
    home.register()
    auth.register()
    admin.register()
    tournaments.register()
```

#### `config.py` - Configuration Management
**Responsibilities**:
- Pydantic settings management
- Environment variable loading
- Type-safe configuration access

**Key Settings**:
- Database credentials
- Discord OAuth2 credentials
- Discord bot token
- Application secrets
- RaceTime.gg API credentials

#### `database.py` - Database Initialization
**Responsibilities**:
- Tortoise ORM initialization
- Database connection management
- Model registration

## Application Layer

### Services (`application/services/`)

**Purpose**: Contains ALL business logic for the application.

**Key Services**:

#### `user_service.py` - User Management
- User CRUD operations
- Permission management
- User search and filtering
- Audit logging for user actions

#### `authorization_service.py` - Authorization Logic
- **Separate from business logic** (not mixed with UserService)
- Permission checking (`can_manage_users()`, `can_access_admin()`, etc.)
- Multi-tenant authorization (`is_member()`, org-scoped checks)
- Global role checks (`is_superadmin()`, `is_admin()`)

#### `audit_service.py` - Audit Logging
- Log user actions
- Track changes with context
- IP address tracking
- Organization-scoped auditing

#### Other Services
- `tournament_service.py`: Tournament business logic
- `organization_service.py`: Organization management
- `async_qualifier_service.py`: Async tournament logic
- `racetime_service.py`: RaceTime.gg integration logic

**Service Pattern**:
```python
class UserService:
    """User management business logic."""
    
    def __init__(self):
        self.repository = UserRepository()
        self.audit = AuditService()
    
    async def create_user(self, discord_id: int, current_user: User) -> User:
        """Create a new user (business logic here)."""
        # Validation
        if await self.repository.get_by_discord_id(discord_id):
            raise ValueError("User already exists")
        
        # Business logic
        user = await self.repository.create(discord_id=discord_id)
        
        # Audit logging
        await self.audit.log_action(current_user, "user_created", {"user_id": user.id})
        
        # Event emission
        await EventBus.emit(UserCreatedEvent(...))
        
        return user
```

### Repositories (`application/repositories/`)

**Purpose**: Data access layer - handles all database queries.

**Key Repositories**:
- `user_repository.py`: User data access
- `audit_repository.py`: Audit log data access
- `tournament_repository.py`: Tournament data access
- `organization_repository.py`: Organization data access

**Repository Pattern**:
```python
class UserRepository:
    """User data access methods."""
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetch user by ID."""
        return await User.filter(id=user_id).first()
    
    async def get_by_discord_id(self, discord_id: int) -> Optional[User]:
        """Fetch user by Discord ID."""
        return await User.filter(discord_id=discord_id).first()
    
    async def create(self, **kwargs) -> User:
        """Create a new user."""
        return await User.create(**kwargs)
    
    async def list_all(self) -> list[User]:
        """List all users."""
        return await User.all()
```

### Utilities (`application/utils/`)

**Purpose**: Shared utility functions and helpers.

**Common Utilities**:
- Date/time formatting helpers
- Data transformation utilities
- Common validation functions

## Authentication & Authorization

### Discord OAuth2 (`middleware/auth.py`)

**`DiscordAuthService`** handles authentication:

**Responsibilities**:
- Generate OAuth2 authorization URLs
- Handle OAuth2 callback
- Exchange code for access token
- Fetch user info from Discord API
- Create/update user in database
- Manage user sessions via NiceGUI storage

**Key Methods**:
```python
class DiscordAuthService:
    @staticmethod
    def get_authorization_url() -> str:
        """Generate Discord OAuth2 URL."""
        
    @staticmethod
    async def handle_callback(code: str) -> User:
        """Handle OAuth2 callback and create/update user."""
        
    @staticmethod
    def require_auth(redirect: str = '/auth/login') -> Optional[User]:
        """Require authentication, redirect if not logged in."""
        
    @staticmethod
    def require_permission(permission: Permission, redirect: str = '/') -> Optional[User]:
        """Require specific permission level."""
```

### Authorization (`application/services/authorization_service.py`)

**`AuthorizationService`** handles permission checks:

**Responsibilities**:
- Check user permissions
- Validate organization membership
- Multi-tenant authorization
- Permission-based UI rendering

**Key Methods**:
```python
class AuthorizationService:
    def is_superadmin(self, user: User) -> bool:
        """Check if user is superadmin."""
        
    def is_admin(self, user: User) -> bool:
        """Check if user is admin."""
        
    def can_access_admin_panel(self, user: User) -> bool:
        """Check if user can access admin panel."""
        
    def is_member(self, user: User, organization_id: int) -> bool:
        """Check if user is member of organization."""
        
    def can_manage_users(self, user: User, organization_id: int) -> bool:
        """Check if user can manage users in organization."""
```

## UI Layer

### Pages (`pages/`)

**Purpose**: NiceGUI page modules that define routes.

**Structure**:
```
pages/
├── __init__.py
├── home.py            # Main landing page
├── auth.py            # Login, callback, logout
├── admin.py           # Admin dashboard
├── tournaments.py     # Tournament listing
├── organization_admin.py  # Org-specific admin
└── user_profile.py    # User profile page
```

**Page Pattern**:
```python
# pages/home.py
from nicegui import ui
from components.base_page import BasePage

def register():
    """Register page routes."""
    
    @ui.page('/')
    async def home():
        """Home page."""
        base = BasePage.simple_page(title="Home", active_nav="home")
        
        async def content(page: BasePage):
            # Page content here
            ui.label('Welcome!')
        
        await base.render(content)()
```

### Views (`views/`)

**Purpose**: Page-specific view components (presentation logic).

**Organization**: Views are organized into subdirectories based on which page uses them:

```
views/
├── __init__.py                      # Re-exports all views
├── home/                            # Home page views
│   ├── __init__.py
│   ├── overview.py
│   ├── schedule.py
│   └── recent_tournaments.py
├── admin/                           # Admin page views
│   ├── __init__.py
│   ├── admin_users.py
│   ├── admin_organizations.py
│   └── admin_settings.py
├── organization/                    # Organization admin views
│   ├── __init__.py
│   ├── org_overview.py
│   ├── org_members.py
│   └── org_permissions.py
└── tournaments/                     # Tournament views
    ├── __init__.py
    ├── async_dashboard.py
    ├── async_leaderboard.py
    └── event_schedule.py
```

**View Pattern**:
```python
# views/home/overview.py
from nicegui import ui

class OverviewView:
    """Homepage overview view."""
    
    def __init__(self, user, service):
        self.user = user
        self.service = service
    
    async def render(self):
        """Render the overview."""
        data = await self.service.get_overview_data()
        
        with ui.element('div').classes('card'):
            ui.label('Overview').classes('card-title')
            # Render content
```

### Components (`components/`)

**Purpose**: Reusable UI components used across multiple pages.

**Key Components**:

#### `base_page.py` - Page Template
Provides consistent layout, navbar, authentication, and notification display.

#### `header.py` - Header Bar
Application header with branding and user menu.

#### `sidebar.py` - Sidebar Navigation
Persistent/flyout navigation sidebar.

#### `data_table.py` - Responsive Table
Mobile-responsive table component (desktop = table, mobile = cards).

#### `datetime_label.py` - DateTime Display
Timezone-aware datetime formatting with locale support.

**See**: [`docs/core/COMPONENTS_GUIDE.md`](core/COMPONENTS_GUIDE.md)

### Dialogs (`components/dialogs/`)

**Purpose**: Modal dialog components (UI-only, delegate logic to services).

**Organization**: Dialogs are organized by which views use them:

```
components/dialogs/
├── __init__.py
├── common/
│   ├── base_dialog.py         # Base dialog class
│   └── confirm_dialog.py      # Confirmation dialogs
├── admin/
│   ├── user_edit.py
│   ├── user_add.py
│   └── organization_dialog.py
├── organization/
│   ├── member_permissions.py
│   ├── invite_member.py
│   └── stream_channel.py
├── tournaments/
│   ├── match_seed.py
│   ├── edit_match.py
│   └── race_review_dialog.py
└── user_profile/
    ├── api_key.py
    └── leave_organization.py
```

**Dialog Pattern**: Extend `BaseDialog` for consistent structure.

**See**: [`docs/core/DIALOG_ACTION_ROW_PATTERN.md`](core/DIALOG_ACTION_ROW_PATTERN.md)

### Static Assets (`static/`)

```
static/
├── css/
│   └── main.css      # All application styles
└── js/
    ├── core/         # Core JavaScript modules
    └── utils/        # Utility functions
```

**Critical Rule**: NO inline styles or JavaScript. All CSS in `main.css`, all JS in `static/js/`.

**See**: [`docs/core/JAVASCRIPT_GUIDELINES.md`](core/JAVASCRIPT_GUIDELINES.md)

## Discord Bot Layer

### Bot Architecture (`discordbot/`)

The Discord bot runs as a **singleton within the application**, not as a separate process.

**Structure**:
```
discordbot/
├── __init__.py
├── client.py                    # Bot singleton
├── async_qualifier_views.py   # Discord UI components
└── commands/
    ├── __init__.py
    ├── admin.py                 # Admin commands
    ├── tournaments.py           # Tournament commands
    └── racetime.py              # RaceTime integration commands
```

#### `client.py` - Bot Singleton

**Pattern**:
```python
_bot_instance: Optional[SahaBot] = None

def get_bot_instance() -> Optional[SahaBot]:
    """Get the bot singleton instance."""
    return _bot_instance

class SahaBot(commands.Bot):
    """Discord bot singleton."""
    
    async def setup_hook(self):
        """Initialize bot commands."""
        await self.load_extension('discordbot.commands.admin')
        await self.load_extension('discordbot.commands.tournaments')
```

**Lifecycle**:
- Started in `main.py` lifespan on app startup
- Stopped in `main.py` lifespan on app shutdown
- Accessed via `get_bot_instance()` from services or commands

#### Commands

**Critical Rules**:
1. **Application commands only** (`@app_commands.command()`) - never prefix commands
2. **No business logic** in commands - delegate to services
3. **No ORM access** - always use services

**Command Pattern**:
```python
# discordbot/commands/admin.py
from discord import app_commands
import discord
from application.services.user_service import UserService

@app_commands.command(name="ban", description="Ban a user")
async def ban_user(interaction: discord.Interaction, user: discord.User):
    """Ban a user."""
    # Delegate to service
    user_service = UserService()
    result = await user_service.ban_user(user.id)
    
    # Respond to interaction
    await interaction.response.send_message(
        f"User {user.mention} banned.",
        ephemeral=True
    )
```

## Multi-Tenancy & Organizations

### Tenant Isolation

**Every feature must preserve tenant (organization) isolation.**

**Organization Models** (`models/organizations.py`):
- `Organization`: Tenant entity
- `OrganizationMember`: User-to-organization membership
- `OrganizationPermission`: Per-organization permission grants

### Security Rules

1. **All tenant-scoped data must reference an organization** (FK or relation)
2. **Never trust client-provided `organization_id`** - validate membership server-side
3. **Service/repository methods accept explicit `organization_id` parameter**
4. **Never return cross-tenant data** - always filter by organization
5. **Audit with tenant context** - include `organization_id` in audit logs
6. **Cache by organization** - computed results keyed by organization
7. **Validate membership before any operation**

**Example Service Method**:
```python
async def get_tournaments_for_org(
    self,
    organization_id: int,
    current_user: User
) -> list[Tournament]:
    """Get tournaments for organization."""
    # Validate membership
    if not self.auth_service.is_member(current_user, organization_id):
        return []  # Return empty, don't raise
    
    # Query with organization filter
    return await self.repository.list_by_organization(organization_id)
```

### PII Protection

**User email addresses are sensitive PII**:
- Only SUPERADMIN users may view/edit email addresses
- Never display `discord_email` in organization views
- Never display `discord_email` in member lists or dialogs
- Hide from all non-superadmin contexts

## Database Layer

### Migrations (`migrations/`)

**Structure**:
```
migrations/
├── models/                  # Auto-generated migration files
│   ├── 0_initial.py
│   ├── 1_add_user_fields.py
│   └── ...
└── tortoise_config.py      # Aerich configuration
```

**Workflow**:
```bash
# Initialize (first time only)
poetry run aerich init-db

# Create migration after model changes
poetry run aerich migrate --name "description"

# Apply migrations
poetry run aerich upgrade

# Rollback if needed
poetry run aerich downgrade
```

### Models (`models/`)

**Purpose**: Database model definitions (Tortoise ORM).

**Organization**: Models organized by domain:

```
models/
├── __init__.py
├── user.py                     # User and permissions
├── audit_log.py                # Audit logging
├── organizations.py            # Organizations and membership
├── async_qualifier.py         # Async tournaments
├── match.py                    # Tournament matches
├── race_room_profile.py        # RaceTime.gg profiles
└── ...
```

**Model Pattern**:
```python
# models/user.py
from tortoise import fields
from tortoise.models import Model

class User(Model):
    """User model."""
    id = fields.IntField(pk=True)
    discord_id = fields.BigIntField(unique=True)
    discord_username = fields.CharField(max_length=255)
    permission = fields.IntEnumField(Permission, default=Permission.USER)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "users"
```

## Event System

The application uses an **async event bus** for decoupled notifications and side effects.

**Event Flow**:
```
Service Action → Event Emitted → Event Handlers Triggered → Side Effects
```

**Example**:
```python
# In service
await self.repository.create_tournament(...)
await EventBus.emit(TournamentCreatedEvent(
    user_id=current_user.id,
    organization_id=org_id,
    entity_id=tournament.id,
    tournament_name=tournament.name
))

# Event handler (separate module)
@EventBus.on(TournamentCreatedEvent)
async def notify_discord(event: TournamentCreatedEvent):
    """Send Discord notification."""
    # Send notification
```

**See**: [`docs/systems/EVENT_SYSTEM.md`](systems/EVENT_SYSTEM.md)

## Task Scheduling

Background tasks are managed by **APScheduler**.

**Task Types**:
- **Interval tasks**: Run periodically (e.g., every 5 minutes)
- **Cron tasks**: Run on schedule (e.g., daily at midnight)
- **One-time tasks**: Run once at specified time

**See**: [`docs/systems/TASK_SCHEDULER.md`](systems/TASK_SCHEDULER.md)

## API Layer

### API Routes (`api/routes/`)

**Purpose**: FastAPI REST API endpoints.

**Structure**:
```
api/
├── __init__.py
├── auto_register.py           # Auto-discover routes
├── deps.py                    # Dependency injection
└── routes/
    ├── __init__.py
    ├── users.py
    ├── organizations.py
    ├── tournaments.py
    └── async_qualifiers.py
```

**API Pattern**:
```python
# api/routes/users.py
from fastapi import APIRouter, Depends
from api.deps import get_current_user, enforce_rate_limit
from application.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", dependencies=[Depends(enforce_rate_limit)])
async def list_users(current_user: User = Depends(get_current_user)):
    """List users."""
    # Delegate to service (authorization happens there)
    service = UserService()
    users = await service.list_users(current_user)
    return {"users": users, "count": len(users)}
```

**Critical Rule**: Authorization happens in services, NOT in API routes.

## Integration Points

### RaceTime.gg

**Integration**: WebSocket client for live race data.

**Components**:
- `racetime/client.py`: WebSocket client
- `racetime/handlers.py`: Event handlers
- `application/services/racetime_service.py`: Business logic

**See**: [`docs/integrations/RACETIME_INTEGRATION.md`](integrations/RACETIME_INTEGRATION.md)

### Discord

**Integrations**:
1. **OAuth2**: User authentication
2. **Bot**: Commands and notifications
3. **Webhooks**: Notification delivery
4. **Scheduled Events**: Discord calendar integration

**See**: 
- [`docs/integrations/DISCORD_CHANNEL_PERMISSIONS.md`](integrations/DISCORD_CHANNEL_PERMISSIONS.md)
- [`docs/integrations/DISCORD_SCHEDULED_EVENTS.md`](integrations/DISCORD_SCHEDULED_EVENTS.md)

## Development Environment

### Required Environment Variables

```bash
# Database
DATABASE_URL=mysql://user:pass@localhost:3306/sahabot2

# Discord OAuth2
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_REDIRECT_URI=http://localhost:8080/auth/callback

# Discord Bot
DISCORD_BOT_TOKEN=your_bot_token

# Application
SECRET_KEY=your_secret_key
ENVIRONMENT=development

# RaceTime.gg (optional)
RACETIME_CLIENT_ID=your_racetime_client_id
RACETIME_CLIENT_SECRET=your_racetime_client_secret
```

### Running the Application

```bash
# Development (port 8080, auto-reload)
./start.sh dev

# Production (port 80, multi-worker)
./start.sh prod
```

## Further Reading

- **[Patterns & Conventions](PATTERNS.md)** - Detailed code patterns
- **[Adding Features Guide](ADDING_FEATURES.md)** - Step-by-step development guides
- **[Event System](systems/EVENT_SYSTEM.md)** - Event bus documentation
- **[Task Scheduler](systems/TASK_SCHEDULER.md)** - Background tasks
- **[BasePage Guide](core/BASEPAGE_GUIDE.md)** - Page template usage
- **[Components Guide](core/COMPONENTS_GUIDE.md)** - UI components reference

---

**Last Updated**: November 4, 2025
