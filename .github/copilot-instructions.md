# Copilot Instructions for SahaBot2

## Project Overview
SahaBot2 (SahasrahBot2) is a NiceGUI + FastAPI web application with Discord OAuth2 authentication and Tortoise ORM for database access. The application follows strict architectural principles emphasizing separation of concerns, mobile-first design, and high code quality.

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
- **static/css/main.css**: All application styles (no inline CSS allowed)

### Discord Bot Layer
- **discordbot/**: Discord bot integration (runs as singleton within the application)
  - `client.py`: Core bot implementation extending `commands.Bot`
  - Lifecycle managed by `main.py` lifespan (starts on app startup, stops on shutdown)
  - Uses `get_bot_instance()` to access singleton from services or commands
  - **Commands should be in separate modules** organized by feature (e.g., `commands/admin.py`)

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

### 3. External CSS Only
- **No** inline styles via `.style()` method
- All CSS in `static/css/main.css`
- Use semantic, human-friendly class names (e.g., `card`, `btn-primary`, `navbar`)
- Include CSS in pages: `ui.add_head_html('<link rel="stylesheet" href="/static/css/main.css">')`

### 4. Discord OAuth2 Authentication
- All users authenticate via Discord
- OAuth flow handled in `middleware/auth.py`
- User info synced to database on login
- Session managed via NiceGUI `app.storage.user`

### 5. Database-Driven Authorization
- Authorization logic in `AuthorizationService` (separate from business logic)
- Permissions stored in database (User.permission field)
- Server-side enforcement via `require_permission()`
- UI can conditionally show elements based on permissions, but must enforce server-side

### 6. High Code Quality
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

### 7. Discord Bot Architecture
- **Bot as Presentation Layer**: Discord bot is part of the presentation layer (like UI pages)
- **Never** access ORM models directly from bot commands - always use services
- **Never** put business logic in bot commands - delegate to services
- **Application Commands Only**: Use Discord's native application commands (slash commands, context menus)
  - **Never** use chat-based (prefix) commands
  - All commands must be registered as application commands via `@app_commands.command()`
- **Singleton Pattern**: Bot runs as singleton, access via `get_bot_instance()` from `bot.client`
- **Separation**: Bot commands should only handle Discord interaction (parsing, responding), delegate all logic to services

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

### CSS Classes
- Container: `page-container`, `content-wrapper`
- Cards: `card`, `card-header`, `card-body`
- Buttons: `btn`, `btn-primary`, `btn-secondary`, `btn-danger`
- Navigation: `navbar`, `navbar-brand`, `navbar-menu`, `navbar-link`
- Tables: `data-table`
- Badges: `badge`, `badge-admin`, `badge-moderator`, `badge-user`
- Utilities: `text-center`, `mt-1`, `mb-2`, `flex`, `gap-md`

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
1. Create file in `pages/` (e.g., `pages/new_page.py`)
2. Define `register()` function
3. Use `@ui.page('/path')` decorator with `BasePage` template
4. Add CSS classes to `static/css/main.css` (no inline styles!)
5. Register in `frontend.py`

Example:
```python
from nicegui import ui
from components.base_page import BasePage

def register():
    @ui.page('/mypage')
    async def my_page():
        base = BasePage.simple_page(title="My Page", active_nav="mypage")
        
        async def content(page: BasePage):
            with ui.element('div').classes('card'):
                ui.label('My content here')
        
        await base.render(content)()
```

### New UI Component
1. Create component file in `components/`
2. Define reusable component class or function
3. Export from `components/__init__.py`
4. Add component-specific CSS to `static/css/main.css`
5. Use in pages by importing from `components`

### New Business Logic
1. Create service in `application/services/`
2. Create repository in `application/repositories/` for data access
3. Use service from UI pages
4. Add docstrings and type hints

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
- ❌ Don't use f-strings in logging statements (use lazy % formatting)
- ❌ Don't use inline imports (import inside functions) - always import at module level
- ❌ Don't leave trailing whitespace on any lines (including blank lines)
- ✅ Do use external CSS classes
- ✅ Do use `with ui.element('div').classes('header'):` and then `ui.label('Text')`
- ✅ Do use services for all business logic
- ✅ Do use repositories for data access
- ✅ Do enforce permissions server-side
- ✅ Do test on mobile viewports
- ✅ Do use application commands (slash commands) for Discord bot
- ✅ Do delegate all bot logic to services
- ✅ Do use lazy % formatting in logging: `logger.info("User %s", user_id)`
- ✅ Do import all modules at the top of the file (module level)
- ✅ Do keep all lines clean with no trailing whitespace

## References
- NiceGUI: https://nicegui.io
- Tortoise ORM: https://tortoise.github.io
- FastAPI: https://fastapi.tiangolo.com
- Discord OAuth2: https://discord.com/developers/docs/topics/oauth2

---
Keep this file updated as architecture evolves. When adding new patterns or conventions, document them here for future reference.
