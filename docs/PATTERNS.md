# SahaBot2 Patterns & Conventions

This document contains detailed code patterns and conventions used throughout the SahaBot2 codebase.

## Table of Contents

1. [Async/Await Patterns](#asyncawait-patterns)
2. [Page Structure](#page-structure)
3. [Service Usage](#service-usage)
4. [Authorization Patterns](#authorization-patterns)
5. [API Routes](#api-routes)
6. [Event Emission](#event-emission)
7. [CSS Classes Reference](#css-classes-reference)
8. [Discord Bot Commands](#discord-bot-commands)
9. [Database Access](#database-access)

## Async/Await Patterns

**Rule**: Everything that touches the database or external APIs must be async.

### Async Function Declaration

```python
# ✅ Correct - async function
async def get_user(user_id: int) -> Optional[User]:
    """Fetch user by ID."""
    return await User.filter(id=user_id).first()

# ❌ Wrong - sync function calling async code
def get_user(user_id: int) -> Optional[User]:
    return User.filter(id=user_id).first()  # Won't work!
```

### Async Service Calls

```python
# ✅ Correct - await service methods
async def process_tournament(tournament_id: int):
    service = TournamentService()
    tournament = await service.get_tournament(tournament_id)
    await service.update_tournament(tournament_id, status="active")

# ❌ Wrong - forgetting await
async def process_tournament(tournament_id: int):
    service = TournamentService()
    tournament = service.get_tournament(tournament_id)  # Returns coroutine, not data!
```

### Async UI Event Handlers

```python
# ✅ Correct - async event handler
async def on_button_click():
    user_service = UserService()
    users = await user_service.get_all_users()
    # Update UI with users

ui.button('Load Users', on_click=on_button_click)

# ❌ Wrong - sync event handler
def on_button_click():  # Can't await inside sync function
    user_service = UserService()
    users = user_service.get_all_users()  # Won't work!
```

## Page Structure

All pages must use `BasePage` for consistent layout, authentication, and navigation.

### Basic Page Pattern

```python
from nicegui import ui
from components.base_page import BasePage

def register():
    \"\"\"Register page routes.\"\"\"
    
    @ui.page('/mypage')
    async def my_page():
        \"\"\"My page description.\"\"\"
        # Create base page
        base = BasePage.simple_page(
            title="My Page",
            active_nav="mypage"  # Highlights nav item
        )
        
        # Define content function
        async def content(page: BasePage):
            \"\"\"Render page content.\"\"\"
            with ui.element('div').classes('card'):
                ui.label(f'Hello, {page.user.discord_username}!')
        
        # Render page
        await base.render(content)()
```

### Page Types

#### Simple Page (No Authentication Required)

```python
base = BasePage.simple_page(
    title="Public Page",
    active_nav="home"
)
```

#### Authenticated Page (Login Required)

```python
base = BasePage.authenticated_page(
    title="User Page",
    active_nav="profile"
)

async def content(page: BasePage):
    # page.user is guaranteed to exist
    ui.label(f'Welcome, {page.user.discord_username}!')
```

#### Admin Page (Admin Permission Required)

```python
base = BasePage.admin_page(
    title="Admin Dashboard",
    active_nav="admin"
)

async def content(page: BasePage):
    # page.user is guaranteed to be admin
    ui.label('Admin controls')
```

#### Custom Permission Page

```python
from models import Permission

base = BasePage(
    title="Moderator Page",
    active_nav="moderator",
    require_permission=Permission.MODERATOR
)
```

### Query Parameter Notifications

BasePage automatically displays notifications from query parameters:

```python
# After successful action, redirect with success message
ui.navigate.to('/tournaments?success=tournament_created')
# Shows: "Tournament Created" (green)

# After error, redirect with error message
ui.navigate.to('/tournaments?error=permission_denied')
# Shows: "Permission Denied" (red)

# Info message
ui.navigate.to('/tournaments?message=changes_saved')
# Shows: "Changes Saved" (blue)
```

**Message Formatting**:
- Underscores converted to spaces
- Title-cased automatically
- `tournament_created` → "Tournament Created"

### Dynamic Content with Views

For pages that load different views dynamically:

```python
# Redirect to specific view
ui.navigate.to('/orgs/1/admin?view=members')

# Page loads the 'members' view automatically
# Based on view parameter
```

**See**: [`docs/core/BASEPAGE_GUIDE.md`](core/BASEPAGE_GUIDE.md) for complete examples.

## Service Usage

Services contain ALL business logic. Never access ORM directly from UI or API routes.

### Service Initialization and Usage

```python
from application.services.user_service import UserService
from application.services.authorization_service import AuthorizationService

async def my_page_handler():
    # Initialize services
    user_service = UserService()
    auth_service = AuthorizationService()
    
    # Get current user
    current_user = DiscordAuthService.get_current_user()
    
    # Check permissions (if needed)
    if not auth_service.can_manage_users(current_user):
        ui.notify('Permission denied', type='negative')
        return
    
    # Call service methods
    users = await user_service.get_all_users()
    
    # Update user
    updated_user = await user_service.update_user_permission(
        user_id=123,
        permission=Permission.ADMIN,
        current_user=current_user
    )
```

### Service Method Pattern

```python
class UserService:
    \"\"\"User management business logic.\"\"\"
    
    def __init__(self):
        self.repository = UserRepository()
        self.auth_service = AuthorizationService()
        self.audit = AuditService()
    
    async def create_user(
        self,
        discord_id: int,
        discord_username: str,
        current_user: User
    ) -> User:
        \"\"\"
        Create a new user.
        
        Args:
            discord_id: Discord user ID
            discord_username: Discord username
            current_user: User performing the action
        
        Returns:
            Created user instance
        
        Raises:
            ValueError: If user already exists
        \"\"\"
        # Business logic: Validation
        existing = await self.repository.get_by_discord_id(discord_id)
        if existing:
            raise ValueError("User already exists")
        
        # Business logic: Creation
        user = await self.repository.create(
            discord_id=discord_id,
            discord_username=discord_username
        )
        
        # Side effects: Audit logging
        await self.audit.log_action(
            user=current_user,
            action="user_created",
            details={"user_id": user.id}
        )
        
        # Side effects: Event emission
        await EventBus.emit(UserCreatedEvent(
            user_id=current_user.id,
            entity_id=user.id,
            discord_id=discord_id,
            username=discord_username
        ))
        
        return user
```

## Authorization Patterns

Authorization is handled by `AuthorizationService` - **separate from business logic**.

### Permission Checking

```python
from application.services.authorization_service import AuthorizationService

auth_z = AuthorizationService()

# Global permission checks
if auth_z.is_superadmin(user):
    # User is superadmin
    pass

if auth_z.is_admin(user):
    # User is admin or higher
    pass

if auth_z.can_access_admin_panel(user):
    # User can access admin panel
    pass

# Organization-scoped checks
if auth_z.is_member(user, organization_id):
    # User is member of organization
    pass

if auth_z.can_manage_users(user, organization_id):
    # User can manage users in this organization
    pass

if auth_z.can_manage_tournaments(user, organization_id):
    # User can manage tournaments in this organization
    pass
```

### Enforcing Authorization in Pages

```python
@ui.page('/admin')
async def admin_page():
    # Require admin permission
    user = DiscordAuthService.require_permission(
        Permission.ADMIN,
        redirect='/unauthorized'
    )
    if not user:
        return  # User redirected
    
    # Continue with page rendering
    base = BasePage.admin_page(...)
```

### Authorization in Services

```python
class TournamentService:
    async def get_tournaments_for_org(
        self,
        organization_id: int,
        current_user: User
    ) -> list[Tournament]:
        \"\"\"Get tournaments for organization.\"\"\"
        # Check membership
        if not self.auth_service.is_member(current_user, organization_id):
            logger.warning(
                "User %s attempted to access org %s tournaments without membership",
                current_user.id,
                organization_id
            )
            return []  # Return empty, don't raise
        
        # Fetch data with organization filter
        return await self.repository.list_by_organization(organization_id)
```

### Multi-Tenant Authorization

```python
async def update_tournament_in_org(
    self,
    organization_id: int,
    tournament_id: int,
    current_user: User,
    **updates
) -> Optional[Tournament]:
    \"\"\"Update tournament in organization.\"\"\"
    # Validate membership
    if not self.auth_service.is_member(current_user, organization_id):
        return None
    
    # Validate tournament belongs to organization
    tournament = await self.repository.get_by_id(tournament_id)
    if not tournament or tournament.organization_id != organization_id:
        logger.warning(
            "User %s attempted to access tournament %s in wrong org %s",
            current_user.id,
            tournament_id,
            organization_id
        )
        return None
    
    # Check permissions
    if not self.auth_service.can_manage_tournaments(current_user, organization_id):
        return None
    
    # Perform update
    return await self.repository.update(tournament_id, **updates)
```

## API Routes

API routes are **presentation layer only** - authorization happens in services.

### Standard API Route Pattern

```python
from fastapi import APIRouter, Depends
from api.deps import get_current_user, enforce_rate_limit
from application.services.tournament_service import TournamentService
from models import User

router = APIRouter(prefix="/tournaments", tags=["tournaments"])

@router.get(
    "/",
    dependencies=[Depends(enforce_rate_limit)],  # Only rate limiting
    summary="List Tournaments"
)
async def list_tournaments(
    organization_id: int,
    current_user: User = Depends(get_current_user)  # Extract user
):
    \"\"\"
    List tournaments for an organization.
    
    Authorization is enforced at the service layer.
    \"\"\"
    # Initialize service
    service = TournamentService()
    
    # Call service (authorization happens here)
    tournaments = await service.get_tournaments_for_org(
        organization_id=organization_id,
        current_user=current_user
    )
    
    # Return response
    return {
        "tournaments": [t.dict() for t in tournaments],
        "count": len(tournaments)
    }
```

### Service Layer Authorization (API)

```python
class TournamentService:
    async def get_tournaments_for_org(
        self,
        organization_id: int,
        current_user: Optional[User]
    ) -> list[Tournament]:
        \"\"\"
        Get tournaments for organization.
        
        Authorization enforced here - returns only tournaments user can access.
        \"\"\"
        # Check permissions
        if not current_user:
            return []
        
        if not self.auth_service.is_member(current_user, organization_id):
            logger.warning(
                "Unauthorized access attempt by user %s for org %s",
                current_user.id if current_user else None,
                organization_id
            )
            return []  # Return empty, don't raise
        
        # Fetch and return data
        return await self.repository.list_by_organization(organization_id)
```

**Why This Pattern:**
- ✅ Centralized authorization in services
- ✅ Consistent behavior across UI and API
- ✅ Services testable independently
- ✅ Graceful degradation (empty vs errors)

## Event Emission

All create/update/delete operations should emit events for notifications and side effects.

### Emitting Events

```python
from application.events import EventBus, TournamentCreatedEvent, TournamentUpdatedEvent
from models import SYSTEM_USER_ID

# User-initiated action
async def create_tournament(self, current_user: User, **data):
    tournament = await self.repository.create(**data)
    
    await EventBus.emit(TournamentCreatedEvent(
        user_id=current_user.id,  # User who performed action
        organization_id=tournament.organization_id,
        entity_id=tournament.id,
        tournament_name=tournament.name
    ))
    
    return tournament

# System-initiated action
async def auto_close_races(self):
    for race in await self.repository.get_finished_races():
        await self.repository.close_race(race.id)
        
        await EventBus.emit(RaceClosedEvent(
            user_id=SYSTEM_USER_ID,  # System action
            organization_id=race.organization_id,
            entity_id=race.id,
            reason="auto_close"
        ))
```

### Event Best Practices

1. **Emit AFTER successful operation** (not before)
2. **Include all relevant context** (user_id, org_id, entity_id, etc.)
3. **Use `current_user.id` for user actions**
4. **Use `SYSTEM_USER_ID` for system/automated actions**
5. **Never use `None` for user_id**
6. **Fire-and-forget** - don't await event handler results

**See**: [`docs/systems/EVENT_SYSTEM.md`](systems/EVENT_SYSTEM.md)

## CSS Classes Reference

All styles defined in `static/css/main.css`. **No inline styles allowed.**

### Layout Classes

```python
# Container
with ui.element('div').classes('page-container'):
    # Content wrapper
    with ui.element('div').classes('content-wrapper'):
        # Content here
        pass
```

### Card Classes

```python
# Card container
with ui.element('div').classes('card'):
    # Card header
    with ui.element('div').classes('card-header'):
        ui.label('Card Title')
    
    # Card body
    with ui.element('div').classes('card-body'):
        ui.label('Card content')
```

### Button Classes

```python
# Primary button
ui.button('Save', on_click=handler).classes('btn btn-primary')

# Secondary button
ui.button('Cancel', on_click=handler).classes('btn btn-secondary')

# Danger button
ui.button('Delete', on_click=handler).classes('btn btn-danger')

# Icon button
ui.button(icon='add', on_click=handler).classes('btn btn-sm')
```

### Badge Classes

```python
# Permission badges
ui.label('Admin').classes('badge badge-admin')
ui.label('Moderator').classes('badge badge-moderator')
ui.label('User').classes('badge badge-user')

# Status badges
ui.label('Success').classes('badge badge-success')
ui.label('Warning').classes('badge badge-warning')
ui.label('Error').classes('badge badge-danger')
ui.label('Info').classes('badge badge-info')
```

### Utility Classes

```python
# Spacing
ui.element('div').classes('mt-1')  # margin-top
ui.element('div').classes('mb-2')  # margin-bottom
ui.element('div').classes('gap-md')  # gap between flex items

# Text
ui.label('Text').classes('text-center')
ui.label('Text').classes('text-bold')
ui.label('Text').classes('text-secondary')

# Flexbox
with ui.row().classes('flex items-center gap-2'):
    ui.icon('check')
    ui.label('Item')
```

## Discord Bot Commands

Bot commands are **presentation layer** - delegate all logic to services.

### Command Pattern

```python
# discordbot/commands/tournaments.py
from discord import app_commands
import discord
from application.services.tournament_service import TournamentService

@app_commands.command(name="tournament", description="Get tournament info")
@app_commands.describe(tournament_id="Tournament ID")
async def tournament_info(
    interaction: discord.Interaction,
    tournament_id: int
):
    \"\"\"Display tournament information.\"\"\"
    # Delegate to service
    service = TournamentService()
    tournament = await service.get_tournament(tournament_id)
    
    if not tournament:
        await interaction.response.send_message(
            "Tournament not found",
            ephemeral=True
        )
        return
    
    # Format and respond (presentation only)
    embed = discord.Embed(
        title=tournament.name,
        description=tournament.description,
        color=discord.Color.blue()
    )
    embed.add_field(name="Status", value=tournament.status)
    
    await interaction.response.send_message(embed=embed)
```

### Bot Command Rules

1. **Use `@app_commands.command()`** - never prefix commands
2. **Delegate to services** - no business logic in commands
3. **No ORM access** - always use services
4. **Handle interaction only** - parsing input, formatting output
5. **Use `get_bot_instance()`** to access bot singleton

## Database Access

### Repository Pattern

All database access goes through repositories. **Never access ORM from services.**

```python
# ✅ Correct - service uses repository
class TournamentService:
    def __init__(self):
        self.repository = TournamentRepository()
    
    async def get_tournament(self, tournament_id: int):
        return await self.repository.get_by_id(tournament_id)

# ❌ Wrong - service accesses ORM directly
class TournamentService:
    async def get_tournament(self, tournament_id: int):
        return await Tournament.filter(id=tournament_id).first()  # Don't do this!
```

### Repository Method Pattern

```python
class TournamentRepository:
    \"\"\"Tournament data access.\"\"\"
    
    async def get_by_id(self, tournament_id: int) -> Optional[Tournament]:
        \"\"\"Get tournament by ID.\"\"\"
        return await Tournament.filter(id=tournament_id).first()
    
    async def list_by_organization(
        self,
        organization_id: int
    ) -> list[Tournament]:
        \"\"\"List tournaments for organization.\"\"\"
        return await Tournament.filter(
            organization_id=organization_id
        ).all()
    
    async def create(self, **kwargs) -> Tournament:
        \"\"\"Create new tournament.\"\"\"
        return await Tournament.create(**kwargs)
    
    async def update(
        self,
        tournament_id: int,
        **updates
    ) -> Optional[Tournament]:
        \"\"\"Update tournament.\"\"\"
        tournament = await self.get_by_id(tournament_id)
        if not tournament:
            return None
        
        await tournament.update_from_dict(updates).save()
        return tournament
```

## Further Reading

- **[Architecture Guide](ARCHITECTURE.md)** - System architecture
- **[Adding Features Guide](ADDING_FEATURES.md)** - Step-by-step development guides
- **[BasePage Guide](core/BASEPAGE_GUIDE.md)** - Page template details
- **[Components Guide](core/COMPONENTS_GUIDE.md)** - UI components
- **[Event System](systems/EVENT_SYSTEM.md)** - Event bus documentation

---

**Last Updated**: November 4, 2025
