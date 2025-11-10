# Adding Features to SahaBot2

Step-by-step guides for common development tasks.

## Table of Contents

1. [New Page](#new-page)
2. [New Dialog](#new-dialog)
3. [New View Component](#new-view-component)
4. [New UI Component](#new-ui-component)
5. [New Service & Repository](#new-service--repository)
6. [New Database Model](#new-database-model)
7. [New Authorization Check](#new-authorization-check)
8. [New Discord Bot Command](#new-discord-bot-command)
9. [New API Endpoint](#new-api-endpoint)

## New Page

### Step 1: Create Page File

Create a new file in `pages/` directory:

```python
# pages/my_feature.py
"""My Feature page."""

from nicegui import ui
from components.base_page import BasePage

def register():
    """Register my feature page routes."""
    
    @ui.page('/my-feature')
    async def my_feature_page():
        """My feature landing page."""
        # Choose appropriate page type
        base = BasePage.authenticated_page(
            title="My Feature",
            active_nav="my_feature"
        )
        
        async def content(page: BasePage):
            """Render page content."""
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-header'):
                    ui.label('My Feature').classes('text-xl')
                
                with ui.element('div').classes('card-body'):
                    ui.label(f'Welcome, {page.user.discord_username}!')
        
        await base.render(content)()
```

### Step 2: Register in frontend.py

```python
# frontend.py
def init_frontend():
    # ... existing imports ...
    from pages import my_feature  # Add import
    
    # ... existing registrations ...
    my_feature.register()  # Add registration
```

### Step 3: Add to Navigation (Optional)

If the page should appear in navigation, update `components/sidebar.py` or `components/header.py`.

### Step 4: Update Route Documentation

**Always update `docs/ROUTE_HIERARCHY.md`** when adding a new page:

```markdown
# In docs/ROUTE_HIERARCHY.md

## UI Routes (NiceGUI Pages)

### [Appropriate Section]

| Route | Description | File |
|-------|-------------|------|
| `/my-feature` | My feature landing page | `pages/my_feature.py` |
```

If the page supports dynamic views (uses `/{view}` pattern), document all available views.

### Step 5: Test

1. Start the application: `./start.sh dev`
2. Navigate to `/my-feature`
3. Verify authentication works
4. Check navbar highlighting

**See**: [`docs/core/BASEPAGE_GUIDE.md`](core/BASEPAGE_GUIDE.md) for advanced page patterns.

## New Dialog

### Step 1: Determine Organization

Which views will use this dialog?
- Admin views → `components/dialogs/admin/`
- Organization views → `components/dialogs/organization/`
- Tournament views → `components/dialogs/tournaments/`
- User profile → `components/dialogs/user_profile/`
- Multiple/shared → `components/dialogs/common/`

### Step 2: Create Dialog File

```python
# components/dialogs/admin/my_dialog.py
"""My custom dialog."""

from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from application.services.my_service import MyService

class MyDialog(BaseDialog):
    """Dialog for managing my feature."""
    
    def __init__(self, item=None, on_save=None):
        """
        Initialize dialog.
        
        Args:
            item: Item to edit (None for create)
            on_save: Callback after successful save
        """
        super().__init__()
        self.item = item
        self.on_save = on_save
        self.service = MyService()
        
        # Form fields (will be created in _render_body)
        self.name_input = None
        self.description_input = None
    
    async def show(self):
        """Display the dialog."""
        title = f'Edit {self.item.name}' if self.item else 'Create New'
        icon = 'edit' if self.item else 'add'
        
        self.create_dialog(
            title=title,
            icon=icon,
            max_width='600px'  # Optional custom width
        )
        
        await super().show()  # Don't forget await!
    
    def _render_body(self):
        """Render dialog content."""
        # Form grid for responsive layout
        with self.create_form_grid(columns=2):
            with ui.element('div'):
                self.name_input = ui.input(
                    label='Name',
                    value=self.item.name if self.item else ''
                ).classes('w-full')
            
            with ui.element('div'):
                self.description_input = ui.input(
                    label='Description',
                    value=self.item.description if self.item else ''
                ).classes('w-full')
        
        ui.separator()
        
        # Action buttons at root level
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button(
                'Save',
                on_click=self._save
            ).classes('btn').props('color=positive')
    
    async def _save(self):
        """Save and close."""
        # Validation
        if not self.name_input.value:
            ui.notify('Name is required', type='negative')
            return
        
        # Call service
        try:
            if self.item:
                await self.service.update(
                    self.item.id,
                    name=self.name_input.value,
                    description=self.description_input.value
                )
            else:
                await self.service.create(
                    name=self.name_input.value,
                    description=self.description_input.value
                )
            
            ui.notify('Saved successfully', type='positive')
            
            # Call callback
            if self.on_save:
                await self.on_save()
            
            await self.close()
        except Exception as e:
            ui.notify(f'Error: {str(e)}', type='negative')
```

### Step 3: Export Dialog

```python
# components/dialogs/admin/__init__.py
from .my_dialog import MyDialog

__all__ = [..., 'MyDialog']
```

```python
# components/dialogs/__init__.py
from .admin import MyDialog

__all__ = [..., 'MyDialog']
```

### Step 4: Use in View

```python
# In your view
from components.dialogs import MyDialog

async def _open_dialog(self, item=None):
    """Open dialog."""
    dialog = MyDialog(item=item, on_save=self._refresh_data)
    await dialog.show()
```

**See**: [`docs/core/DIALOG_ACTION_ROW_PATTERN.md`](core/DIALOG_ACTION_ROW_PATTERN.md)

## New View Component

### Step 1: Determine Page

Which page will use this view?
- Home page → `views/home/`
- Admin page → `views/admin/`
- Organization admin → `views/organization/`
- Tournaments → `views/tournaments/`
- New page → Create `views/newpage/` directory

### Step 2: Create View File

```python
# views/tournaments/my_view.py
"""My tournament view."""

from nicegui import ui
from components.data_table import ResponsiveTable, TableColumn
from application.services.tournament_service import TournamentService

class MyTournamentView:
    """View for displaying tournament data."""
    
    def __init__(self, tournament, user):
        """
        Initialize view.
        
        Args:
            tournament: Tournament instance
            user: Current user
        """
        self.tournament = tournament
        self.user = user
        self.service = TournamentService()
    
    async def render(self):
        """Render the view."""
        # Fetch data
        data = await self.service.get_tournament_data(
            self.tournament.id,
            self.user
        )
        
        # Render UI
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                ui.label('My Tournament View').classes('text-lg')
            
            with ui.element('div').classes('card-body'):
                # Use ResponsiveTable for tabular data
                columns = [
                    TableColumn(label='Name', key='name'),
                    TableColumn(label='Status', cell_render=self._render_status),
                    TableColumn(label='Actions', cell_render=self._render_actions),
                ]
                
                table = ResponsiveTable(columns=columns, rows=data)
                await table.render()
    
    def _render_status(self, row):
        """Render status badge."""
        if row.status == 'active':
            ui.label('Active').classes('badge badge-success')
        else:
            ui.label('Inactive').classes('badge badge-secondary')
    
    def _render_actions(self, row):
        """Render action buttons."""
        with ui.row().classes('gap-1'):
            ui.button(
                icon='visibility',
                on_click=lambda r=row: self._view_detail(r)
            ).classes('btn btn-sm').tooltip('View')
            ui.button(
                icon='edit',
                on_click=lambda r=row: self._edit(r)
            ).classes('btn btn-sm').tooltip('Edit')
    
    async def _view_detail(self, row):
        """View item details."""
        # Implementation
        pass
    
    async def _edit(self, row):
        """Edit item."""
        # Implementation
        pass
```

### Step 3: Export View

```python
# views/tournaments/__init__.py
from .my_view import MyTournamentView

__all__ = [..., 'MyTournamentView']
```

```python
# views/__init__.py  
from .tournaments import MyTournamentView

__all__ = [..., 'MyTournamentView']
```

### Step 4: Use in Page

```python
# pages/tournaments.py
from views.tournaments import MyTournamentView

async def content(page: BasePage):
    view = MyTournamentView(tournament=tournament, user=page.user)
    await view.render()
```

## New UI Component

For reusable components used across multiple pages.

### Step 1: Create Component File

```python
# components/my_component.py
"""My reusable component."""

from nicegui import ui

class MyComponent:
    """Reusable component for X."""
    
    @staticmethod
    def create(data, on_click=None):
        """
        Create component instance.
        
        Args:
            data: Component data
            on_click: Optional click handler
        """
        with ui.element('div').classes('my-component'):
            ui.label(data.title).classes('component-title')
            
            if data.description:
                ui.label(data.description).classes('component-description')
            
            if on_click:
                ui.button(
                    'Action',
                    on_click=lambda: on_click(data)
                ).classes('btn btn-primary')
```

### Step 2: Add CSS

```css
/* static/css/main.css */

/* My Component */
.my-component {
    padding: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
}

.my-component .component-title {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.my-component .component-description {
    color: var(--text-secondary);
}
```

### Step 3: Export Component

```python
# components/__init__.py
from .my_component import MyComponent

__all__ = [..., 'MyComponent']
```

### Step 4: Use in Pages

```python
from components import MyComponent

# In page content
MyComponent.create(data=my_data, on_click=handle_click)
```

## New Service & Repository

### Step 1: Create Model (if needed)

```python
# models/my_model.py
from tortoise import fields
from tortoise.models import Model

class MyModel(Model):
    """My model description."""
    
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField(
        'models.Organization',
        related_name='my_models'
    )
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "my_models"
```

### Step 2: Create Repository

```python
# application/repositories/my_repository.py
"""My model data access."""

from typing import Optional
from models.my_model import MyModel

class MyRepository:
    """Data access for MyModel."""
    
    async def get_by_id(self, item_id: int) -> Optional[MyModel]:
        """Get item by ID."""
        return await MyModel.filter(id=item_id).first()
    
    async def list_by_organization(
        self,
        organization_id: int
    ) -> list[MyModel]:
        """List items for organization."""
        return await MyModel.filter(
            organization_id=organization_id
        ).order_by('-created_at').all()
    
    async def create(self, **kwargs) -> MyModel:
        """Create new item."""
        return await MyModel.create(**kwargs)
    
    async def update(
        self,
        item_id: int,
        **updates
    ) -> Optional[MyModel]:
        """Update item."""
        item = await self.get_by_id(item_id)
        if not item:
            return None
        
        await item.update_from_dict(updates).save()
        return item
    
    async def delete(self, item_id: int) -> bool:
        """Delete item."""
        item = await self.get_by_id(item_id)
        if not item:
            return False
        
        await item.delete()
        return True
```

### Step 3: Create Service

```python
# application/services/my_service.py
"""My model business logic."""

import logging
from typing import Optional
from models import User, MyModel, SYSTEM_USER_ID
from application.repositories.my_repository import MyRepository
from application.services.authorization_service import AuthorizationService
from application.services.audit_service import AuditService
from application.events import EventBus, MyModelCreatedEvent, MyModelUpdatedEvent

logger = logging.getLogger(__name__)

class MyService:
    """Business logic for MyModel."""
    
    def __init__(self):
        self.repository = MyRepository()
        self.auth_service = AuthorizationService()
        self.audit = AuditService()
    
    async def get_items_for_org(
        self,
        organization_id: int,
        current_user: User
    ) -> list[MyModel]:
        """
        Get items for organization.
        
        Args:
            organization_id: Organization ID
            current_user: Current user
        
        Returns:
            List of items (empty if unauthorized)
        """
        # Check membership
        if not self.auth_service.is_member(current_user, organization_id):
            logger.warning(
                "User %s attempted to access org %s items without membership",
                current_user.id,
                organization_id
            )
            return []
        
        # Fetch data
        return await self.repository.list_by_organization(organization_id)
    
    async def create_item(
        self,
        organization_id: int,
        name: str,
        description: str,
        current_user: User
    ) -> Optional[MyModel]:
        """
        Create new item.
        
        Args:
            organization_id: Organization ID
            name: Item name
            description: Item description
            current_user: User creating item
        
        Returns:
            Created item (None if unauthorized)
        """
        # Check permissions
        if not self.auth_service.can_manage_items(current_user, organization_id):
            logger.warning(
                "User %s attempted to create item in org %s without permission",
                current_user.id,
                organization_id
            )
            return None
        
        # Create item
        item = await self.repository.create(
            organization_id=organization_id,
            name=name,
            description=description
        )
        
        # Audit log
        await self.audit.log_action(
            user=current_user,
            action="item_created",
            details={"item_id": item.id, "name": name}
        )
        
        # Emit event
        await EventBus.emit(MyModelCreatedEvent(
            user_id=current_user.id,
            organization_id=organization_id,
            entity_id=item.id,
            item_name=name
        ))
        
        return item
    
    async def update_item(
        self,
        item_id: int,
        current_user: User,
        **updates
    ) -> Optional[MyModel]:
        """
        Update item.
        
        Args:
            item_id: Item ID
            current_user: User updating item
            **updates: Fields to update
        
        Returns:
            Updated item (None if unauthorized or not found)
        """
        # Get item
        item = await self.repository.get_by_id(item_id)
        if not item:
            return None
        
        # Check permissions
        if not self.auth_service.can_manage_items(
            current_user,
            item.organization_id
        ):
            logger.warning(
                "User %s attempted to update item %s without permission",
                current_user.id,
                item_id
            )
            return None
        
        # Update
        updated_item = await self.repository.update(item_id, **updates)
        
        # Audit log
        await self.audit.log_action(
            user=current_user,
            action="item_updated",
            details={"item_id": item_id, "updates": list(updates.keys())}
        )
        
        # Emit event
        await EventBus.emit(MyModelUpdatedEvent(
            user_id=current_user.id,
            organization_id=item.organization_id,
            entity_id=item_id,
            changed_fields=list(updates.keys())
        ))
        
        return updated_item
```

### Step 4: Export Service

```python
# application/services/__init__.py
from .my_service import MyService

__all__ = [..., 'MyService']
```

## New Database Model

### Step 1: Create Model File

```python
# models/my_model.py
from tortoise import fields
from tortoise.models import Model

class MyModel(Model):
    """My model description."""
    
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField(
        'models.Organization',
        related_name='my_models'
    )
    name = fields.CharField(max_length=255)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "my_models"
        indexes = [
            ('organization', 'name'),  # Composite index
        ]
```

### Step 2: Export from models/__init__.py

```python
# models/__init__.py
from .my_model import MyModel

__all__ = [..., 'MyModel']
```

### Step 3: Update Tortoise Config

```python
# migrations/tortoise_config.py
TORTOISE_ORM = {
    "connections": {...},
    "apps": {
        "models": {
            "models": [
                # ... existing models ...
                "models.my_model",  # Add new model
            ],
        }
    },
}
```

### Step 4: Update database.py

```python
# database.py
TORTOISE_ORM = {
    "apps": {
        "models": {
            "models": [
                # ... existing models ...
                "models.my_model",  # Add new model
            ]
        }
    }
}
```

### Step 5: Create and Apply Migration

```bash
# Create migration
poetry run aerich migrate --name "add_my_model"

# Review the generated migration file
# migrations/models/XX_add_my_model.py

# Apply migration
poetry run aerich upgrade
```

### Step 6: Create Repository and Service

Follow steps in [New Service & Repository](#new-service--repository).

## New Authorization Check

### Step 1: Add Method to AuthorizationService

```python
# application/services/authorization_service.py

class AuthorizationService:
    # ... existing methods ...
    
    def can_manage_items(
        self,
        user: User,
        organization_id: int
    ) -> bool:
        """
        Check if user can manage items in organization.
        
        Args:
            user: User to check
            organization_id: Organization ID
        
        Returns:
            True if user can manage items
        """
        # Global admins can manage anywhere
        if self.is_superadmin(user) or self.is_admin(user):
            return True
        
        # Check organization membership
        if not self.is_member(user, organization_id):
            return False
        
        # Check organization-specific permissions
        # (implement based on your permission model)
        return self.has_org_role(user, organization_id, 'manager')
```

### Step 2: Use in Service

```python
# In your service method
if not self.auth_service.can_manage_items(current_user, organization_id):
    logger.warning("Unauthorized access attempt")
    return None
```

### Step 3: Use in Pages for UI

```python
# In page content
if auth_service.can_manage_items(page.user, org_id):
    ui.button('Manage Items', on_click=open_management)
else:
    ui.label('You do not have permission to manage items')
```

## New Discord Bot Command

### Step 1: Create Command Module

```python
# discordbot/commands/my_commands.py
"""My Discord commands."""

import logging
from discord import app_commands
import discord
from application.services.my_service import MyService

logger = logging.getLogger(__name__)

@app_commands.command(
    name="mycommand",
    description="My command description"
)
@app_commands.describe(
    item_id="Item ID to retrieve"
)
async def my_command(
    interaction: discord.Interaction,
    item_id: int
):
    """
    Get item information.
    
    Args:
        interaction: Discord interaction
        item_id: Item ID
    """
    # Delegate to service (NO business logic here)
    service = MyService()
    item = await service.get_item_by_id(item_id)
    
    if not item:
        await interaction.response.send_message(
            "Item not found",
            ephemeral=True
        )
        return
    
    # Format response (presentation only)
    embed = discord.Embed(
        title=item.name,
        description=item.description or "No description",
        color=discord.Color.blue()
    )
    embed.add_field(name="Status", value="Active" if item.is_active else "Inactive")
    
    await interaction.response.send_message(embed=embed)

async def setup(bot):
    """Register commands."""
    bot.tree.add_command(my_command)
```

### Step 2: Load Command Extension

```python
# discordbot/client.py

class SahaBot(commands.Bot):
    async def setup_hook(self):
        """Load command extensions."""
        # ... existing extensions ...
        await self.load_extension('discordbot.commands.my_commands')
```

### Step 3: Test Command

1. Restart the bot
2. In Discord, type `/mycommand` and verify autocomplete works
3. Test the command with valid and invalid data

## New API Endpoint

### Step 1: Create Route Module

```python
# api/routes/my_routes.py
"""My API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.deps import get_current_user, enforce_rate_limit
from application.services.my_service import MyService
from models import User

router = APIRouter(prefix="/my-items", tags=["my-items"])

# Request/Response schemas
class ItemCreate(BaseModel):
    name: str
    description: str | None = None

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str | None
    organization_id: int
    is_active: bool

@router.get(
    "/",
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Items"
)
async def list_items(
    organization_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    List items for organization.
    
    Authorization enforced at service layer.
    """
    service = MyService()
    items = await service.get_items_for_org(organization_id, current_user)
    
    return {
        "items": [ItemResponse.model_validate(item) for item in items],
        "count": len(items)
    }

@router.post(
    "/",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Item"
)
async def create_item(
    organization_id: int,
    data: ItemCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create new item.
    
    Authorization enforced at service layer.
    """
    service = MyService()
    item = await service.create_item(
        organization_id=organization_id,
        name=data.name,
        description=data.description,
        current_user=current_user
    )
    
    if not item:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return ItemResponse.model_validate(item)
```

### Step 2: Register Routes

Routes are auto-registered if using `auto_register.py`. Otherwise:

```python
# api/__init__.py
from .routes import my_routes

def register_routes(app):
    # ... existing routes ...
    app.include_router(my_routes.router)
```

### Step 3: Update Route Documentation

**Always update `docs/ROUTE_HIERARCHY.md`** when adding API endpoints:

```markdown
# In docs/ROUTE_HIERARCHY.md

## REST API Routes (FastAPI)

### [Appropriate Section]

Base path: `/api/my-items`

| Method | Route | Description | Auth Required | File |
|--------|-------|-------------|---------------|------|
| GET | `/` | List items for organization | Yes | `api/routes/my_routes.py` |
| POST | `/` | Create new item | Yes | `api/routes/my_routes.py` |
| GET | `/{item_id}` | Get item details | Yes | `api/routes/my_routes.py` |
```

### Step 4: Test API

1. Start application
2. Navigate to `/docs` (Swagger UI)
3. Test the endpoints
4. Verify authorization works

**See**: [`docs/reference/API_SWAGGER_GUIDE.md`](reference/API_SWAGGER_GUIDE.md)

---

## Further Reading

- **[Architecture Guide](ARCHITECTURE.md)** - System architecture
- **[Patterns & Conventions](PATTERNS.md)** - Code patterns
- **[Event System](systems/EVENT_SYSTEM.md)** - Event bus
- **[Task Scheduler](systems/TASK_SCHEDULER.md)** - Background tasks

---

**Last Updated**: November 4, 2025
