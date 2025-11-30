# Plugin Implementation Guide

## Executive Summary

This guide provides step-by-step instructions for developers creating new plugins for SahaBot2. It includes code examples, best practices, and common patterns.

## Quick Start: Creating a New Plugin

### Step 1: Create Plugin Directory

```bash
# For built-in plugins
mkdir -p plugins/builtin/my_plugin

# For external plugins
mkdir -p plugins/external/my_plugin
```

### Step 2: Create Manifest

```yaml
# plugins/builtin/my_plugin/manifest.yaml

id: my_plugin
name: My Plugin
version: 1.0.0
description: A sample plugin demonstrating plugin development
author: Your Name
type: builtin  # or "external"
category: utility

requires:
  sahabot2: ">=1.0.0"
  python: ">=3.11"
  plugins: []

provides:
  models:
    - MyModel
  pages:
    - path: /org/{org_id}/my-plugin
      name: My Plugin Page
  api_routes:
    prefix: /my-plugin
    tags: [my_plugin]

permissions:
  actions:
    - my_plugin:read
    - my_plugin:write

config_schema:
  type: object
  properties:
    feature_enabled:
      type: boolean
      default: true
      description: Enable the main feature
```

### Step 3: Create Plugin Class

```python
# plugins/builtin/my_plugin/__init__.py

from plugins.builtin.my_plugin.plugin import MyPlugin

__all__ = ["MyPlugin"]
```

```python
# plugins/builtin/my_plugin/plugin.py

import logging
from typing import List, Type, Optional
from tortoise.models import Model
from fastapi import APIRouter
from discord.ext import commands

from application.plugins.base import BasePlugin, PluginManifest, PluginConfig
from application.events.base import BaseEvent

logger = logging.getLogger(__name__)


class MyPlugin(BasePlugin):
    """
    My Plugin - A sample plugin implementation.

    This plugin demonstrates the complete plugin development workflow.
    """

    @property
    def plugin_id(self) -> str:
        return "my_plugin"

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            id="my_plugin",
            name="My Plugin",
            version="1.0.0",
            description="A sample plugin demonstrating plugin development",
            author="Your Name",
            type="builtin",
            category="utility",
        )

    # ─────────────────────────────────────────────────────────────
    # Lifecycle Hooks
    # ─────────────────────────────────────────────────────────────

    async def on_load(self) -> None:
        """Called when plugin is loaded at startup."""
        logger.info("MyPlugin loaded")

    async def on_enable(self, organization_id: int, config: PluginConfig) -> None:
        """Called when plugin is enabled for an organization."""
        logger.info("MyPlugin enabled for org %s with config: %s",
                    organization_id, config.settings)

    async def on_disable(self, organization_id: int) -> None:
        """Called when plugin is disabled for an organization."""
        logger.info("MyPlugin disabled for org %s", organization_id)

    async def on_unload(self) -> None:
        """Called when plugin is unloaded at shutdown."""
        logger.info("MyPlugin unloaded")

    # ─────────────────────────────────────────────────────────────
    # Contribution Methods
    # ─────────────────────────────────────────────────────────────

    def get_models(self) -> List[Type[Model]]:
        """Return database models."""
        from plugins.builtin.my_plugin.models import MyModel
        return [MyModel]

    def get_api_router(self) -> Optional[APIRouter]:
        """Return API router."""
        from plugins.builtin.my_plugin.api.routes import router
        return router

    def get_pages(self):
        """Return page registrations."""
        from plugins.builtin.my_plugin.pages import get_page_registrations
        return get_page_registrations()

    def get_discord_cog(self) -> Optional[Type[commands.Cog]]:
        """Return Discord cog."""
        from plugins.builtin.my_plugin.commands import MyPluginCog
        return MyPluginCog

    def get_event_types(self) -> List[Type[BaseEvent]]:
        """Return event types."""
        from plugins.builtin.my_plugin.events.types import (
            MyPluginCreatedEvent,
            MyPluginUpdatedEvent,
        )
        return [MyPluginCreatedEvent, MyPluginUpdatedEvent]

    def get_event_listeners(self):
        """Return event listeners."""
        from plugins.builtin.my_plugin.events.listeners import get_listeners
        return get_listeners()

    def get_scheduled_tasks(self):
        """Return scheduled tasks."""
        from plugins.builtin.my_plugin.tasks import get_tasks
        return get_tasks()

    def get_authorization_actions(self) -> List[str]:
        """Return authorization actions."""
        return [
            "my_plugin:read",
            "my_plugin:write",
            "my_plugin:delete",
        ]

    def get_menu_items(self):
        """Return navigation menu items."""
        return [
            {
                "label": "My Plugin",
                "path": "/org/{org_id}/my-plugin",
                "icon": "extension",
                "position": "sidebar",
                "order": 100,
                "requires_permission": "my_plugin:read",
            }
        ]
```

## Creating Plugin Components

### 1. Database Models

```python
# plugins/builtin/my_plugin/models/__init__.py

from plugins.builtin.my_plugin.models.my_model import MyModel

__all__ = ["MyModel"]
```

```python
# plugins/builtin/my_plugin/models/my_model.py

from tortoise import fields
from tortoise.models import Model


class MyModel(Model):
    """
    Example model for my plugin.

    Follows SahaBot2 model conventions:
    - Always has organization reference for multi-tenancy
    - Has created_at and updated_at timestamps
    - Uses descriptive field names
    """

    id = fields.IntField(pk=True)

    # Organization reference for multi-tenancy
    organization = fields.ForeignKeyField(
        "models.Organization",
        related_name="my_plugin_items"
    )

    # Plugin-specific fields
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    config = fields.JSONField(null=True)

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # Related fields
    created_by = fields.ForeignKeyField(
        "models.User",
        related_name="my_plugin_items_created",
        null=True
    )

    class Meta:
        table = "my_plugin_items"

    def __str__(self):
        return f"MyModel({self.id}, {self.name})"
```

### 2. Repositories

```python
# plugins/builtin/my_plugin/repositories/__init__.py

from plugins.builtin.my_plugin.repositories.my_repository import MyRepository

__all__ = ["MyRepository"]
```

```python
# plugins/builtin/my_plugin/repositories/my_repository.py

import logging
from typing import Optional, List
from plugins.builtin.my_plugin.models import MyModel

logger = logging.getLogger(__name__)


class MyRepository:
    """
    Data access layer for MyModel.

    Follows SahaBot2 repository conventions:
    - All methods are async
    - Always filter by organization_id for multi-tenancy
    - Return None for not found, don't raise
    - Log important operations
    """

    async def get_by_id(
        self,
        item_id: int,
        organization_id: int
    ) -> Optional[MyModel]:
        """
        Get item by ID for organization.

        Args:
            item_id: Item ID
            organization_id: Organization ID

        Returns:
            MyModel if found, None otherwise
        """
        return await MyModel.filter(
            id=item_id,
            organization_id=organization_id
        ).first()

    async def list_by_org(
        self,
        organization_id: int,
        active_only: bool = False
    ) -> List[MyModel]:
        """
        List items for organization.

        Args:
            organization_id: Organization ID
            active_only: If True, only return active items

        Returns:
            List of MyModel instances
        """
        query = MyModel.filter(organization_id=organization_id)
        if active_only:
            query = query.filter(is_active=True)
        return await query.all()

    async def create(
        self,
        organization_id: int,
        name: str,
        description: Optional[str] = None,
        created_by_id: Optional[int] = None,
        **kwargs
    ) -> MyModel:
        """
        Create a new item.

        Args:
            organization_id: Organization ID
            name: Item name
            description: Optional description
            created_by_id: User who created the item
            **kwargs: Additional fields

        Returns:
            Created MyModel instance
        """
        item = await MyModel.create(
            organization_id=organization_id,
            name=name,
            description=description,
            created_by_id=created_by_id,
            **kwargs
        )
        logger.info("Created MyModel %s in org %s", item.id, organization_id)
        return item

    async def update(
        self,
        item_id: int,
        organization_id: int,
        **fields
    ) -> Optional[MyModel]:
        """
        Update an item.

        Args:
            item_id: Item ID
            organization_id: Organization ID
            **fields: Fields to update

        Returns:
            Updated MyModel if found, None otherwise
        """
        item = await self.get_by_id(item_id, organization_id)
        if not item:
            return None

        for field, value in fields.items():
            if hasattr(item, field):
                setattr(item, field, value)

        await item.save()
        logger.info("Updated MyModel %s in org %s", item_id, organization_id)
        return item

    async def delete(
        self,
        item_id: int,
        organization_id: int
    ) -> bool:
        """
        Delete an item.

        Args:
            item_id: Item ID
            organization_id: Organization ID

        Returns:
            True if deleted, False if not found
        """
        item = await self.get_by_id(item_id, organization_id)
        if not item:
            return False

        await item.delete()
        logger.info("Deleted MyModel %s from org %s", item_id, organization_id)
        return True
```

### 3. Services

```python
# plugins/builtin/my_plugin/services/__init__.py

from plugins.builtin.my_plugin.services.my_service import MyService

__all__ = ["MyService"]
```

```python
# plugins/builtin/my_plugin/services/my_service.py

import logging
from typing import Optional, List
from models import User
from plugins.builtin.my_plugin.models import MyModel
from plugins.builtin.my_plugin.repositories import MyRepository
from application.services.organizations.organization_service import OrganizationService
from application.services.authorization.authorization_service_v2 import (
    AuthorizationServiceV2,
)
from application.events import EventBus
from plugins.builtin.my_plugin.events.types import (
    MyPluginCreatedEvent,
    MyPluginUpdatedEvent,
)

logger = logging.getLogger(__name__)


class MyService:
    """
    Business logic for my plugin.

    Follows SahaBot2 service conventions:
    - All business logic here, not in UI or repository
    - Authorization checks before operations
    - Event emission after successful operations
    - Proper logging
    """

    def __init__(self):
        self.repo = MyRepository()
        self.org_service = OrganizationService()
        self.auth = AuthorizationServiceV2()

    async def list_items(
        self,
        user: Optional[User],
        organization_id: int,
        active_only: bool = False
    ) -> List[MyModel]:
        """
        List items for organization.

        Args:
            user: Current user
            organization_id: Organization ID
            active_only: If True, only return active items

        Returns:
            List of items, empty if unauthorized
        """
        if not user:
            logger.warning(
                "Unauthenticated list_items attempt for org %s",
                organization_id
            )
            return []

        # Check authorization
        allowed = await self.auth.can(
            user,
            action="my_plugin:read",
            resource=f"my_plugin:*",
            organization_id=organization_id,
        )

        if not allowed:
            logger.warning(
                "Unauthorized list_items by user %s for org %s",
                user.id,
                organization_id,
            )
            return []

        return await self.repo.list_by_org(organization_id, active_only)

    async def get_item(
        self,
        user: Optional[User],
        organization_id: int,
        item_id: int
    ) -> Optional[MyModel]:
        """
        Get item by ID.

        Args:
            user: Current user
            organization_id: Organization ID
            item_id: Item ID

        Returns:
            Item if found and authorized, None otherwise
        """
        if not user:
            return None

        # Check authorization
        allowed = await self.auth.can(
            user,
            action="my_plugin:read",
            resource=f"my_plugin:{item_id}",
            organization_id=organization_id,
        )

        if not allowed:
            logger.warning(
                "Unauthorized get_item by user %s for item %s",
                user.id,
                item_id,
            )
            return None

        return await self.repo.get_by_id(item_id, organization_id)

    async def create_item(
        self,
        user: Optional[User],
        organization_id: int,
        name: str,
        description: Optional[str] = None,
    ) -> Optional[MyModel]:
        """
        Create a new item.

        Args:
            user: Current user
            organization_id: Organization ID
            name: Item name
            description: Optional description

        Returns:
            Created item if authorized, None otherwise
        """
        if not user:
            logger.warning(
                "Unauthenticated create_item attempt for org %s",
                organization_id
            )
            return None

        # Check authorization
        allowed = await self.auth.can(
            user,
            action="my_plugin:write",
            resource=f"my_plugin:*",
            organization_id=organization_id,
        )

        if not allowed:
            logger.warning(
                "Unauthorized create_item by user %s for org %s",
                user.id,
                organization_id,
            )
            return None

        # Create item
        item = await self.repo.create(
            organization_id=organization_id,
            name=name,
            description=description,
            created_by_id=user.id,
        )

        # Emit event
        await EventBus.emit(
            MyPluginCreatedEvent(
                user_id=user.id,
                organization_id=organization_id,
                entity_id=item.id,
                item_name=name,
            )
        )

        return item

    async def update_item(
        self,
        user: Optional[User],
        organization_id: int,
        item_id: int,
        **fields
    ) -> Optional[MyModel]:
        """
        Update an item.

        Args:
            user: Current user
            organization_id: Organization ID
            item_id: Item ID
            **fields: Fields to update

        Returns:
            Updated item if authorized, None otherwise
        """
        if not user:
            return None

        # Check authorization
        allowed = await self.auth.can(
            user,
            action="my_plugin:write",
            resource=f"my_plugin:{item_id}",
            organization_id=organization_id,
        )

        if not allowed:
            logger.warning(
                "Unauthorized update_item by user %s for item %s",
                user.id,
                item_id,
            )
            return None

        # Update item
        item = await self.repo.update(item_id, organization_id, **fields)

        if item:
            # Emit event
            await EventBus.emit(
                MyPluginUpdatedEvent(
                    user_id=user.id,
                    organization_id=organization_id,
                    entity_id=item_id,
                    updated_fields=list(fields.keys()),
                )
            )

        return item

    async def delete_item(
        self,
        user: Optional[User],
        organization_id: int,
        item_id: int
    ) -> bool:
        """
        Delete an item.

        Args:
            user: Current user
            organization_id: Organization ID
            item_id: Item ID

        Returns:
            True if deleted, False otherwise
        """
        if not user:
            return False

        # Check authorization
        allowed = await self.auth.can(
            user,
            action="my_plugin:delete",
            resource=f"my_plugin:{item_id}",
            organization_id=organization_id,
        )

        if not allowed:
            logger.warning(
                "Unauthorized delete_item by user %s for item %s",
                user.id,
                item_id,
            )
            return False

        return await self.repo.delete(item_id, organization_id)
```

### 4. API Routes

```python
# plugins/builtin/my_plugin/api/__init__.py

from plugins.builtin.my_plugin.api.routes import router

__all__ = ["router"]
```

```python
# plugins/builtin/my_plugin/api/routes.py

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from api.deps import get_current_user, enforce_rate_limit
from models import User
from plugins.builtin.my_plugin.services import MyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/my-plugin", tags=["my_plugin"])


# ─────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────

class ItemCreate(BaseModel):
    """Schema for creating an item."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ItemUpdate(BaseModel):
    """Schema for updating an item."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ItemResponse(BaseModel):
    """Schema for item response."""
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ItemListResponse(BaseModel):
    """Schema for item list response."""
    items: List[ItemResponse]
    count: int


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────

@router.get(
    "/organizations/{organization_id}/items",
    response_model=ItemListResponse,
    dependencies=[Depends(enforce_rate_limit)]
)
async def list_items(
    organization_id: int,
    active_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    List items for organization.

    Authorization handled by service layer.
    """
    service = MyService()
    items = await service.list_items(
        current_user,
        organization_id,
        active_only=active_only
    )
    return ItemListResponse(
        items=[ItemResponse.model_validate(item) for item in items],
        count=len(items)
    )


@router.get(
    "/organizations/{organization_id}/items/{item_id}",
    response_model=ItemResponse,
    dependencies=[Depends(enforce_rate_limit)]
)
async def get_item(
    organization_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get item by ID.

    Authorization handled by service layer.
    """
    service = MyService()
    item = await service.get_item(current_user, organization_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemResponse.model_validate(item)


@router.post(
    "/organizations/{organization_id}/items",
    response_model=ItemResponse,
    status_code=201,
    dependencies=[Depends(enforce_rate_limit)]
)
async def create_item(
    organization_id: int,
    data: ItemCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new item.

    Authorization handled by service layer.
    """
    service = MyService()
    item = await service.create_item(
        current_user,
        organization_id,
        name=data.name,
        description=data.description
    )
    if not item:
        raise HTTPException(status_code=403, detail="Not authorized")
    return ItemResponse.model_validate(item)


@router.patch(
    "/organizations/{organization_id}/items/{item_id}",
    response_model=ItemResponse,
    dependencies=[Depends(enforce_rate_limit)]
)
async def update_item(
    organization_id: int,
    item_id: int,
    data: ItemUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update an item.

    Authorization handled by service layer.
    """
    service = MyService()
    update_data = data.model_dump(exclude_unset=True)
    item = await service.update_item(
        current_user,
        organization_id,
        item_id,
        **update_data
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found or not authorized")
    return ItemResponse.model_validate(item)


@router.delete(
    "/organizations/{organization_id}/items/{item_id}",
    status_code=204,
    dependencies=[Depends(enforce_rate_limit)]
)
async def delete_item(
    organization_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Delete an item.

    Authorization handled by service layer.
    """
    service = MyService()
    success = await service.delete_item(current_user, organization_id, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found or not authorized")
```

### 5. Pages

```python
# plugins/builtin/my_plugin/pages/__init__.py

from plugins.builtin.my_plugin.pages.main import get_page_registrations

__all__ = ["get_page_registrations"]
```

```python
# plugins/builtin/my_plugin/pages/main.py

from nicegui import ui
from components.base_page import BasePage
from plugins.builtin.my_plugin.services import MyService


def get_page_registrations():
    """Return page registration definitions."""
    return [
        {
            "path": "/org/{org_id}/my-plugin",
            "handler": my_plugin_page,
            "title": "My Plugin",
            "requires_auth": True,
            "requires_org": True,
            "active_nav": "my_plugin",
        },
        {
            "path": "/org/{org_id}/my-plugin/{item_id}",
            "handler": my_plugin_item_page,
            "title": "My Plugin Item",
            "requires_auth": True,
            "requires_org": True,
            "active_nav": "my_plugin",
        },
    ]


def register():
    """Register pages with NiceGUI."""

    @ui.page('/org/{org_id}/my-plugin')
    async def my_plugin_page(org_id: int):
        """My Plugin main page."""
        base = BasePage.authenticated_page(
            title="My Plugin",
            active_nav="my_plugin"
        )

        async def content(page: BasePage):
            service = MyService()
            items = await service.list_items(page.user, org_id)

            with ui.element('div').classes('content-section'):
                with ui.element('div').classes('section-header'):
                    ui.label('My Plugin Items').classes('section-title')
                    ui.button('Add Item', on_click=lambda: show_add_dialog(org_id))

                if not items:
                    ui.label('No items found').classes('text-secondary')
                else:
                    with ui.element('div').classes('item-grid'):
                        for item in items:
                            with ui.card().classes('item-card'):
                                ui.label(item.name).classes('card-title')
                                if item.description:
                                    ui.label(item.description).classes('card-description')

        await base.render(content)()

    @ui.page('/org/{org_id}/my-plugin/{item_id}')
    async def my_plugin_item_page(org_id: int, item_id: int):
        """My Plugin item detail page."""
        base = BasePage.authenticated_page(
            title="Item Details",
            active_nav="my_plugin"
        )

        async def content(page: BasePage):
            service = MyService()
            item = await service.get_item(page.user, org_id, item_id)

            if not item:
                ui.label('Item not found').classes('error')
                return

            with ui.element('div').classes('content-section'):
                ui.label(item.name).classes('page-title')
                if item.description:
                    ui.label(item.description).classes('description')

                # Item details...

        await base.render(content)()


async def show_add_dialog(org_id: int):
    """Show dialog to add new item."""
    # Implementation...
    pass
```

### 6. Events

```python
# plugins/builtin/my_plugin/events/__init__.py

from plugins.builtin.my_plugin.events.types import (
    MyPluginCreatedEvent,
    MyPluginUpdatedEvent,
)
from plugins.builtin.my_plugin.events.listeners import get_listeners

__all__ = [
    "MyPluginCreatedEvent",
    "MyPluginUpdatedEvent",
    "get_listeners",
]
```

```python
# plugins/builtin/my_plugin/events/types.py

from dataclasses import dataclass, field
from typing import Optional, List
from application.events.base import BaseEvent


@dataclass
class MyPluginCreatedEvent(BaseEvent):
    """Emitted when a plugin item is created."""

    item_name: str = ""

    @property
    def event_type(self) -> str:
        return "my_plugin.created"


@dataclass
class MyPluginUpdatedEvent(BaseEvent):
    """Emitted when a plugin item is updated."""

    updated_fields: List[str] = field(default_factory=list)

    @property
    def event_type(self) -> str:
        return "my_plugin.updated"
```

```python
# plugins/builtin/my_plugin/events/listeners.py

import logging
from application.events import EventBus
from application.events.base import EventPriority
from plugins.builtin.my_plugin.events.types import (
    MyPluginCreatedEvent,
    MyPluginUpdatedEvent,
)

logger = logging.getLogger(__name__)


def get_listeners():
    """Return event listener registrations."""
    return [
        {
            "event_type": MyPluginCreatedEvent,
            "handler": on_item_created,
            "priority": EventPriority.NORMAL,
        },
        {
            "event_type": MyPluginUpdatedEvent,
            "handler": on_item_updated,
            "priority": EventPriority.NORMAL,
        },
    ]


async def on_item_created(event: MyPluginCreatedEvent):
    """Handle item created event."""
    logger.info(
        "Item '%s' created by user %s in org %s",
        event.item_name,
        event.user_id,
        event.organization_id
    )
    # Additional processing...


async def on_item_updated(event: MyPluginUpdatedEvent):
    """Handle item updated event."""
    logger.info(
        "Item %s updated by user %s (fields: %s)",
        event.entity_id,
        event.user_id,
        ", ".join(event.updated_fields)
    )
    # Additional processing...
```

### 7. Discord Commands

```python
# plugins/builtin/my_plugin/commands/__init__.py

from plugins.builtin.my_plugin.commands.cog import MyPluginCog

__all__ = ["MyPluginCog"]
```

```python
# plugins/builtin/my_plugin/commands/cog.py

import discord
from discord import app_commands
from discord.ext import commands
import logging
from plugins.builtin.my_plugin.services import MyService

logger = logging.getLogger(__name__)


class MyPluginCog(commands.Cog):
    """Discord commands for My Plugin."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.service = MyService()

    @app_commands.command(
        name="my-plugin-list",
        description="List plugin items"
    )
    @app_commands.describe(
        active_only="Only show active items"
    )
    async def list_items(
        self,
        interaction: discord.Interaction,
        active_only: bool = False
    ):
        """List items from the plugin."""
        await interaction.response.defer(ephemeral=True)

        # Get user from Discord ID
        from application.services.discord.discord_service import DiscordService
        user = await DiscordService.get_user_by_discord_id(interaction.user.id)

        if not user:
            await interaction.followup.send(
                "You need to link your account first.",
                ephemeral=True
            )
            return

        # Get organization from guild
        # (Implementation depends on your Discord guild -> org mapping)
        organization_id = await self._get_org_from_guild(interaction.guild_id)

        if not organization_id:
            await interaction.followup.send(
                "This server is not linked to an organization.",
                ephemeral=True
            )
            return

        items = await self.service.list_items(user, organization_id, active_only)

        if not items:
            await interaction.followup.send(
                "No items found.",
                ephemeral=True
            )
            return

        # Format response
        embed = discord.Embed(
            title="Plugin Items",
            color=discord.Color.blue()
        )

        for item in items[:10]:  # Limit to 10
            embed.add_field(
                name=item.name,
                value=item.description or "No description",
                inline=False
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    async def _get_org_from_guild(self, guild_id: int):
        """Get organization ID from Discord guild."""
        # Implementation...
        return None


async def setup(bot: commands.Bot):
    """Setup function for loading the cog."""
    await bot.add_cog(MyPluginCog(bot))
```

### 8. Scheduled Tasks

```python
# plugins/builtin/my_plugin/tasks/__init__.py

from plugins.builtin.my_plugin.tasks.sync_task import get_tasks

__all__ = ["get_tasks"]
```

```python
# plugins/builtin/my_plugin/tasks/sync_task.py

import logging
from models.scheduled_task import TaskType, ScheduleType

logger = logging.getLogger(__name__)


def get_tasks():
    """Return scheduled task registrations."""
    return [
        {
            "task_id": "my_plugin_cleanup",
            "name": "My Plugin Cleanup",
            "description": "Clean up old inactive items",
            "handler": cleanup_task,
            "task_type": TaskType.CLEANUP,
            "schedule_type": ScheduleType.CRON,
            "cron_expression": "0 3 * * *",  # Daily at 3 AM
            "is_active": True,
        },
    ]


async def cleanup_task(task):
    """
    Cleanup task handler.

    Args:
        task: ScheduledTask or PseudoTask instance
    """
    logger.info("Running my_plugin cleanup task")

    # Cleanup logic...
    from plugins.builtin.my_plugin.models import MyModel
    from datetime import datetime, timedelta, timezone

    # Example: Delete items inactive for 90 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    deleted = await MyModel.filter(
        is_active=False,
        updated_at__lt=cutoff
    ).delete()

    logger.info("Cleaned up %d inactive items", deleted)
```

## Testing Your Plugin

### Unit Tests

```python
# tests/plugins/my_plugin/test_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from plugins.builtin.my_plugin.services import MyService
from plugins.builtin.my_plugin.models import MyModel


@pytest.fixture
def service():
    return MyService()


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    return user


@pytest.mark.asyncio
async def test_create_item(service, mock_user, mocker):
    """Test item creation."""
    # Mock authorization
    mocker.patch.object(
        service.auth,
        'can',
        new=AsyncMock(return_value=True)
    )

    # Mock repository
    mock_item = MagicMock(spec=MyModel)
    mock_item.id = 1
    mock_item.name = "Test Item"
    mocker.patch.object(
        service.repo,
        'create',
        new=AsyncMock(return_value=mock_item)
    )

    # Mock event bus
    mock_emit = AsyncMock()
    mocker.patch(
        'plugins.builtin.my_plugin.services.my_service.EventBus.emit',
        mock_emit
    )

    # Execute
    result = await service.create_item(
        mock_user,
        organization_id=1,
        name="Test Item"
    )

    # Assert
    assert result is not None
    assert result.name == "Test Item"
    mock_emit.assert_called_once()
```

### Integration Tests

```python
# tests/plugins/my_plugin/test_integration.py

import pytest
from httpx import AsyncClient
from plugins.builtin.my_plugin.plugin import MyPlugin


@pytest.mark.asyncio
async def test_plugin_loads():
    """Test plugin loads correctly."""
    plugin = MyPlugin()
    await plugin.on_load()

    assert plugin.plugin_id == "my_plugin"
    assert len(plugin.get_models()) > 0
    assert plugin.get_api_router() is not None


@pytest.mark.asyncio
async def test_api_list_items(async_client: AsyncClient, auth_headers):
    """Test API list items endpoint."""
    response = await async_client.get(
        "/api/plugins/my-plugin/organizations/1/items",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "count" in data
```

## Best Practices

### Do's

1. **Follow SahaBot2 conventions** - Use the same patterns as core
2. **Always check authorization** - Use AuthorizationServiceV2
3. **Emit events** - Allow other components to react
4. **Log important operations** - Use lazy % formatting
5. **Handle errors gracefully** - Return None, don't raise
6. **Test thoroughly** - Unit and integration tests
7. **Document your plugin** - README, API docs

### Don'ts

1. **Don't access ORM from UI** - Always use services
2. **Don't skip authorization** - Even for read operations
3. **Don't hardcode organization IDs** - Use context
4. **Don't use inline imports** - Import at module level
5. **Don't use print()** - Use logging framework
6. **Don't use datetime.utcnow()** - Use datetime.now(timezone.utc)

## Troubleshooting

### Common Issues

**Plugin not loading**
- Check manifest.yaml syntax
- Verify plugin_id matches manifest id
- Check dependencies are installed

**Models not registering**
- Ensure models are returned from get_models()
- Check model import paths
- Verify Tortoise model syntax

**Routes not working**
- Check router prefix
- Verify route registration
- Check authentication dependencies

**Events not firing**
- Verify event import paths
- Check listener registration
- Ensure EventBus.emit() is awaited

---

**Last Updated**: November 30, 2025
