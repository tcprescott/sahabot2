# Plugin API Specification

## Executive Summary

This document defines the interfaces, contracts, and lifecycle hooks that plugins must implement to integrate with SahaBot2. It serves as the technical specification for plugin developers.

## Plugin Interface Contracts

### 1. BasePlugin Abstract Class

All plugins must extend the `BasePlugin` abstract class:

```python
# application/plugins/base/plugin.py

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Type
from pydantic import BaseModel
from tortoise.models import Model
from fastapi import APIRouter
from discord.ext import commands


class PluginManifest(BaseModel):
    """Plugin manifest schema."""
    id: str
    name: str
    version: str
    description: str
    author: str
    type: str  # "builtin" or "external"
    category: str
    enabled_by_default: bool = True  # Whether enabled for new organizations
    private: bool = False  # If true, requires global admin to grant org access
    global_plugin: bool = False  # If true, always enabled, not organization-scoped
    requires: Dict[str, Any] = {}
    provides: Dict[str, Any] = {}
    permissions: Dict[str, Any] = {}
    feature_flags: List[str] = []
    config_schema: Dict[str, Any] = {}


class PluginConfig(BaseModel):
    """Plugin configuration."""
    enabled: bool = True
    settings: Dict[str, Any] = {}


class BasePlugin(ABC):
    """
    Abstract base class for all plugins.

    Plugins must implement the abstract methods to contribute
    functionality to SahaBot2.
    """

    # ─────────────────────────────────────────────────────────────
    # Required Properties
    # ─────────────────────────────────────────────────────────────

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest:
        """
        Return the plugin manifest.

        The manifest contains metadata about the plugin including
        its ID, version, dependencies, and contributions.
        """
        pass

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """
        Return the unique plugin identifier.

        Convention: lowercase, alphanumeric with underscores.
        Examples: "tournament", "async_qualifier", "smz3_support"
        """
        pass

    # ─────────────────────────────────────────────────────────────
    # Lifecycle Methods
    # ─────────────────────────────────────────────────────────────

    async def on_load(self) -> None:
        """
        Called when the plugin is loaded into memory.

        Use this for one-time initialization that doesn't require
        database access or organization context.
        """
        pass

    async def on_enable(self, organization_id: int, config: PluginConfig) -> None:
        """
        Called when the plugin is enabled for an organization.

        Args:
            organization_id: The organization enabling the plugin
            config: Organization-specific configuration

        Use this to initialize organization-specific resources.
        """
        pass

    async def on_disable(self, organization_id: int) -> None:
        """
        Called when the plugin is disabled for an organization.

        Args:
            organization_id: The organization disabling the plugin

        Use this to clean up organization-specific resources.
        """
        pass

    async def on_unload(self) -> None:
        """
        Called when the plugin is being unloaded.

        Use this for cleanup before the plugin is removed from memory.
        """
        pass

    async def on_install(self) -> None:
        """
        Called when the plugin is first installed.

        Use this for one-time setup like database migrations.
        Only called for external plugins.
        """
        pass

    async def on_uninstall(self) -> None:
        """
        Called when the plugin is being uninstalled.

        Use this for cleanup like removing database tables.
        Only called for external plugins.
        """
        pass

    async def on_upgrade(self, old_version: str, new_version: str) -> None:
        """
        Called when the plugin is upgraded.

        Args:
            old_version: Previous version string
            new_version: New version string

        Use this for migration logic between versions.
        """
        pass

    # ─────────────────────────────────────────────────────────────
    # Contribution Methods
    # ─────────────────────────────────────────────────────────────

    def get_models(self) -> List[Type[Model]]:
        """
        Return Tortoise ORM models contributed by this plugin.

        Returns:
            List of Model classes to register with Tortoise ORM
        """
        return []

    def get_api_router(self) -> Optional[APIRouter]:
        """
        Return FastAPI router for API endpoints.

        Returns:
            APIRouter with plugin endpoints, or None
        """
        return None

    def get_pages(self) -> List[Dict[str, Any]]:
        """
        Return page registration definitions.

        Returns:
            List of dicts with keys:
            - path: URL path pattern
            - handler: Async function to render the page
            - title: Page title
            - requires_auth: Whether auth is required
            - requires_org: Whether org context is required
        """
        return []

    def get_discord_cog(self) -> Optional[Type[commands.Cog]]:
        """
        Return Discord cog class for bot commands.

        Returns:
            Cog class to load, or None
        """
        return None

    def get_event_types(self) -> List[Type]:
        """
        Return event types defined by this plugin.

        Returns:
            List of BaseEvent subclasses
        """
        return []

    def get_event_listeners(self) -> List[Dict[str, Any]]:
        """
        Return event listeners to register.

        Returns:
            List of dicts with keys:
            - event_type: The event class to listen for
            - handler: Async function to handle the event
            - priority: EventPriority enum value
        """
        return []

    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        Return scheduled tasks to register.

        Returns:
            List of dicts with keys:
            - task_id: Unique task identifier
            - name: Display name
            - handler: Async function to execute
            - schedule_type: ScheduleType enum
            - interval_seconds: For INTERVAL type
            - cron_expression: For CRON type
            - is_active: Default active state
        """
        return []

    def get_authorization_actions(self) -> List[str]:
        """
        Return authorization actions defined by this plugin.

        Returns:
            List of action strings like "tournament:create"
        """
        return []

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """
        Return navigation menu items to add.

        Returns:
            List of dicts with keys:
            - label: Menu item text
            - path: URL path
            - icon: Icon name
            - position: Menu position (e.g., "sidebar", "admin")
            - order: Sort order
            - requires_permission: Permission action required
        """
        return []

    # ─────────────────────────────────────────────────────────────
    # Context Methods
    # ─────────────────────────────────────────────────────────────

    def is_enabled_for_org(self, organization_id: int) -> bool:
        """
        Check if plugin is enabled for an organization.

        Args:
            organization_id: Organization to check

        Returns:
            True if enabled, False otherwise

        Note: This is typically called by the PluginRegistry, not
        directly by the plugin implementation.
        """
        # Default implementation - override if needed
        from application.plugins.registry import PluginRegistry
        return PluginRegistry.is_enabled(self.plugin_id, organization_id)

    def get_config(self, organization_id: int) -> PluginConfig:
        """
        Get configuration for an organization.

        Args:
            organization_id: Organization to get config for

        Returns:
            PluginConfig with merged settings
        """
        from application.plugins.registry import PluginRegistry
        return PluginRegistry.get_config(self.plugin_id, organization_id)
```

### 2. Provider Interfaces

Each contribution type has a specific provider interface:

#### ModelProvider

```python
# application/plugins/base/model_provider.py

from abc import ABC, abstractmethod
from typing import List, Type, Optional
from tortoise.models import Model


class ModelProvider(ABC):
    """Interface for plugins that provide database models."""

    @abstractmethod
    def get_models(self) -> List[Type[Model]]:
        """
        Return list of Tortoise ORM models.

        Returns:
            List of Model classes
        """
        pass

    def get_model_module(self) -> str:
        """
        Return the module path for models.

        Used by Tortoise ORM for model discovery.
        Override if models are in a non-standard location.

        Returns:
            Module path string (e.g., "plugins.builtin.tournament.models")
        """
        return f"plugins.builtin.{self.plugin_id}.models"

    def get_migrations_path(self) -> Optional[str]:
        """
        Return the filesystem path to migrations.

        Returns:
            Path string or None if no migrations
        """
        return None
```

#### RouteProvider

```python
# application/plugins/base/route_provider.py

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from fastapi import APIRouter


class RouteProvider(ABC):
    """Interface for plugins that provide API routes."""

    @abstractmethod
    def get_api_router(self) -> Optional[APIRouter]:
        """
        Return FastAPI router with endpoints.

        The router will be mounted at /api/plugins/{plugin_id}/

        Returns:
            APIRouter instance or None
        """
        pass

    def get_route_prefix(self) -> str:
        """
        Return the route prefix for this plugin.

        Override to customize the mount point.

        Returns:
            Route prefix string (default: plugin_id)
        """
        return self.plugin_id

    def get_route_tags(self) -> List[str]:
        """
        Return OpenAPI tags for routes.

        Returns:
            List of tag strings
        """
        return [self.plugin_id]

    def get_route_dependencies(self) -> List[Any]:
        """
        Return dependencies to apply to all routes.

        Returns:
            List of FastAPI Depends instances
        """
        return []
```

#### PageProvider

```python
# application/plugins/base/page_provider.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable


class PageRegistration:
    """Page registration definition."""

    def __init__(
        self,
        path: str,
        handler: Callable,
        title: str,
        requires_auth: bool = True,
        requires_org: bool = True,
        active_nav: str = None,
        permission: str = None,
    ):
        self.path = path
        self.handler = handler
        self.title = title
        self.requires_auth = requires_auth
        self.requires_org = requires_org
        self.active_nav = active_nav
        self.permission = permission


class PageProvider(ABC):
    """Interface for plugins that provide UI pages."""

    @abstractmethod
    def get_pages(self) -> List[PageRegistration]:
        """
        Return page registration definitions.

        Returns:
            List of PageRegistration instances
        """
        pass

    def register_pages(self) -> None:
        """
        Register pages with NiceGUI.

        Called by PluginRegistry during page registration.
        Default implementation uses get_pages().
        """
        from nicegui import ui

        for page in self.get_pages():
            @ui.page(page.path)
            async def page_handler(p=page):
                # Standard page wrapper logic
                await p.handler()
```

#### CommandProvider

```python
# application/plugins/base/command_provider.py

from abc import ABC, abstractmethod
from typing import Optional, Type, List
from discord.ext import commands


class CommandProvider(ABC):
    """Interface for plugins that provide Discord commands."""

    @abstractmethod
    def get_discord_cog(self) -> Optional[Type[commands.Cog]]:
        """
        Return Discord cog class.

        Returns:
            Cog class to load, or None
        """
        pass

    def get_extension_name(self) -> str:
        """
        Return the extension module name for load_extension().

        Returns:
            Module path string
        """
        return f"plugins.builtin.{self.plugin_id}.commands"

    def get_required_intents(self) -> List[str]:
        """
        Return Discord intents required by this plugin.

        Returns:
            List of intent names (e.g., ["guilds", "members"])
        """
        return []
```

#### EventProvider

```python
# application/plugins/base/event_provider.py

from abc import ABC, abstractmethod
from typing import List, Type, Dict, Any, Callable
from application.events.base import BaseEvent, EventPriority


class EventListenerRegistration:
    """Event listener registration."""

    def __init__(
        self,
        event_type: Type[BaseEvent],
        handler: Callable,
        priority: EventPriority = EventPriority.NORMAL,
    ):
        self.event_type = event_type
        self.handler = handler
        self.priority = priority


class EventProvider(ABC):
    """Interface for plugins that provide events."""

    @abstractmethod
    def get_event_types(self) -> List[Type[BaseEvent]]:
        """
        Return event types defined by this plugin.

        Returns:
            List of BaseEvent subclasses
        """
        pass

    @abstractmethod
    def get_event_listeners(self) -> List[EventListenerRegistration]:
        """
        Return event listeners to register.

        Returns:
            List of EventListenerRegistration instances
        """
        pass

    def register_events(self) -> None:
        """
        Register events and listeners with EventBus.

        Called by PluginRegistry during event registration.
        """
        from application.events import EventBus

        for listener in self.get_event_listeners():
            EventBus.register(
                listener.event_type,
                listener.handler,
                listener.priority
            )
```

#### TaskProvider

```python
# application/plugins/base/task_provider.py

from abc import ABC, abstractmethod
from typing import List, Callable, Optional
from dataclasses import dataclass
from models.scheduled_task import TaskType, ScheduleType


@dataclass
class TaskRegistration:
    """Scheduled task registration."""
    task_id: str
    name: str
    description: str
    handler: Callable
    task_type: TaskType
    schedule_type: ScheduleType
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    is_active: bool = True
    task_config: Optional[dict] = None


class TaskProvider(ABC):
    """Interface for plugins that provide scheduled tasks."""

    @abstractmethod
    def get_scheduled_tasks(self) -> List[TaskRegistration]:
        """
        Return scheduled tasks to register.

        Returns:
            List of TaskRegistration instances
        """
        pass

    def get_task_prefix(self) -> str:
        """
        Return prefix for task IDs.

        Used to namespace task IDs: {prefix}_{task_id}

        Returns:
            Task ID prefix (default: plugin_id)
        """
        return self.plugin_id
```

## Plugin Lifecycle

### Lifecycle State Diagram

```
                    ┌─────────────────┐
                    │   DISCOVERED    │
                    │ (manifest read) │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
          ┌────────│   VALIDATED     │────────┐
          │        │ (deps checked)  │        │
          │        └────────┬────────┘        │
          │                 │                 │
          │ (validation     │                 │ (validation
          │  failed)        │ (success)       │  failed)
          │                 ▼                 │
          │        ┌─────────────────┐        │
          │        │    LOADING      │        │
          │        │ (on_load)       │        │
          │        └────────┬────────┘        │
          │                 │                 │
          │                 ▼                 │
          │        ┌─────────────────┐        │
          └───────>│     FAILED      │<───────┘
                   │ (error state)   │
                   └─────────────────┘
                             ▲
                             │
                             │ (error during
                             │  any phase)
                             │
                    ┌────────┴────────┐
                    │    LOADED       │
                    │ (ready to use)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌─────────────┐  ┌───────────┐  ┌─────────────┐
     │  ENABLING   │  │  RUNNING  │  │  DISABLING  │
     │ (per org)   │  │ (active)  │  │ (per org)   │
     └──────┬──────┘  └───────────┘  └──────┬──────┘
            │                               │
            └───────────────────────────────┘
```

### Lifecycle Hook Sequence

#### Plugin Installation (External Plugins Only)

```
1. Download/Extract plugin package
2. Validate manifest
3. Check dependencies
4. Call on_install()
5. Run database migrations
6. Add to plugins table
7. Call on_load()
8. Plugin is LOADED
```

#### Plugin Loading (Startup)

```
1. Discover all plugins (builtin + installed)
2. For each plugin:
   a. Read manifest
   b. Validate dependencies
   c. Create plugin instance
   d. Call on_load()
   e. Register models
   f. Register routes
   g. Register pages
   h. Register commands
   i. Register events
   j. Register tasks
3. All plugins are LOADED
```

#### Plugin Enable (Per-Organization)

```
1. Check plugin is LOADED
2. Check dependencies enabled
3. Get organization config
4. Call on_enable(org_id, config)
5. Add to organization_plugins table
6. Plugin is ENABLED for org
```

#### Plugin Disable (Per-Organization)

```
1. Check plugin is ENABLED for org
2. Check no dependencies require this
3. Call on_disable(org_id)
4. Update organization_plugins table
5. Plugin is DISABLED for org
```

#### Plugin Unload (Shutdown)

```
1. For each loaded plugin:
   a. Call on_disable() for each enabled org
   b. Call on_unload()
   c. Unregister routes
   d. Unregister events
   e. Unregister tasks
2. All plugins are UNLOADED
```

#### Plugin Upgrade

```
1. Get current version
2. Validate new version
3. Call on_disable() for all orgs
4. Call on_unload()
5. Update plugin files
6. Run upgrade migrations
7. Call on_upgrade(old_version, new_version)
8. Call on_load()
9. Re-enable for previous orgs
```

## Manifest Schema (YAML)

```yaml
# Complete manifest schema with all options

# Required fields
id: string                    # Unique plugin identifier (alphanumeric + underscore)
name: string                  # Display name
version: string               # Semantic version (e.g., "1.0.0")
description: string           # Short description

# Optional metadata
author: string                # Author name or organization
website: string               # Plugin website or repo URL
license: string               # License identifier (e.g., "MIT")

# Plugin classification
type: enum                    # "builtin" or "external"
  - builtin
  - external
category: enum                # Plugin category
  - competition               # Tournament/race functionality
  - integration               # External service integration
  - utility                   # General utilities
  - automation                # Automation features

# Dependencies
requires:
  sahabot2: string            # Required SahaBot2 version (semver range)
  python: string              # Required Python version (semver range)
  plugins:                    # Required plugins
    - plugin_id: string
      version: string         # Version range

# Optional dependencies (enhance functionality if present)
optional:
  plugins:
    - plugin_id: string
      version: string

# Incompatibilities
conflicts:
  plugins:                    # Cannot be enabled with these plugins
    - plugin_id: string

# Feature contributions
provides:
  models:                     # Database models
    - string                  # Model class name
  pages:                      # UI pages
    - path: string            # URL path pattern
      name: string            # Page name
      auth_required: bool     # Requires authentication
      org_required: bool      # Requires organization context
  api_routes:
    prefix: string            # Route prefix
    tags:                     # OpenAPI tags
      - string
  discord_commands:
    - name: string            # Command name
      description: string     # Command description
  events:
    - string                  # Event class name
  tasks:
    - string                  # Task ID

# Authorization
permissions:
  actions:                    # Authorization actions
    - string                  # Action identifier
  roles:                      # Role requirements
    - string                  # Role name

# Feature flags required
feature_flags:
  - string                    # Flag name

# Configuration schema (JSON Schema)
config_schema:
  type: object
  properties:
    setting_name:
      type: string            # JSON Schema type
      default: any            # Default value
      description: string     # Setting description
```

## Error Handling

### Plugin Exceptions

```python
# application/plugins/exceptions.py

class PluginError(Exception):
    """Base exception for plugin errors."""
    pass


class PluginNotFoundError(PluginError):
    """Plugin not found in registry."""
    pass


class PluginLoadError(PluginError):
    """Error during plugin loading."""
    pass


class PluginDependencyError(PluginError):
    """Missing or incompatible dependency."""
    pass


class PluginConfigurationError(PluginError):
    """Invalid plugin configuration."""
    pass


class PluginLifecycleError(PluginError):
    """Error during lifecycle transition."""
    pass


class PluginAlreadyEnabledError(PluginError):
    """Plugin already enabled for organization."""
    pass


class PluginNotEnabledError(PluginError):
    """Plugin not enabled for organization."""
    pass


class BuiltinPluginError(PluginError):
    """Cannot perform action on builtin plugin."""
    pass
```

### Error Recovery

```python
# Lifecycle error recovery patterns

async def safe_on_enable(plugin: BasePlugin, org_id: int, config: PluginConfig):
    """Safely enable a plugin with rollback on failure."""
    try:
        await plugin.on_enable(org_id, config)
    except Exception as e:
        logger.error("Failed to enable plugin %s for org %s: %s",
                     plugin.plugin_id, org_id, e)
        # Attempt rollback
        try:
            await plugin.on_disable(org_id)
        except Exception:
            pass  # Best effort cleanup
        raise PluginLifecycleError(f"Failed to enable: {e}") from e
```

## Configuration API

### Configuration Service

```python
# application/plugins/config_service.py

from typing import Any, Dict, Optional
from pydantic import BaseModel, ValidationError
import jsonschema


class PluginConfigService:
    """Service for managing plugin configuration."""

    async def get_config(
        self,
        plugin_id: str,
        organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get merged configuration for a plugin.

        Priority (highest first):
        1. Organization-specific settings
        2. Global plugin settings
        3. Manifest defaults
        4. Code defaults

        Args:
            plugin_id: Plugin identifier
            organization_id: Optional org for org-specific config

        Returns:
            Merged configuration dictionary
        """
        pass

    async def set_config(
        self,
        plugin_id: str,
        settings: Dict[str, Any],
        organization_id: Optional[int] = None,
        user_id: int = None
    ) -> None:
        """
        Update plugin configuration.

        Args:
            plugin_id: Plugin identifier
            settings: Settings to update
            organization_id: Optional org for org-specific config
            user_id: User making the change (for audit)

        Raises:
            PluginConfigurationError: If validation fails
        """
        pass

    def validate_config(
        self,
        plugin_id: str,
        settings: Dict[str, Any]
    ) -> None:
        """
        Validate settings against plugin's config schema.

        Args:
            plugin_id: Plugin identifier
            settings: Settings to validate

        Raises:
            PluginConfigurationError: If validation fails
        """
        pass
```

## Testing Utilities

### Plugin Test Helpers

```python
# application/plugins/testing.py

from typing import Type
from unittest.mock import AsyncMock


class PluginTestContext:
    """Context manager for testing plugins."""

    def __init__(self, plugin_class: Type[BasePlugin], config: dict = None):
        self.plugin_class = plugin_class
        self.config = config or {}
        self.plugin = None

    async def __aenter__(self):
        # Create plugin instance
        self.plugin = self.plugin_class()

        # Mock registry
        self._mock_registry()

        # Load plugin
        await self.plugin.on_load()

        return self.plugin

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Unload plugin
        await self.plugin.on_unload()

        # Restore mocks
        self._restore_mocks()

    def _mock_registry(self):
        """Set up mock registry for testing."""
        pass

    def _restore_mocks(self):
        """Restore original registry."""
        pass


# Usage:
async def test_tournament_plugin():
    async with PluginTestContext(TournamentPlugin) as plugin:
        # Plugin is loaded and ready for testing
        assert plugin.plugin_id == "tournament"
        models = plugin.get_models()
        assert len(models) > 0
```

## API Versioning

### Version Compatibility

```python
# Plugin API version compatibility

PLUGIN_API_VERSION = "1.0"

# Minimum compatible versions
COMPATIBLE_VERSIONS = {
    "1.0": ["1.0", "1.1"],  # 1.0 plugins work with 1.0 and 1.1 core
}

def check_api_compatibility(plugin_api_version: str) -> bool:
    """Check if plugin API version is compatible with current core."""
    current = PLUGIN_API_VERSION
    if current in COMPATIBLE_VERSIONS:
        return plugin_api_version in COMPATIBLE_VERSIONS[current]
    return plugin_api_version == current
```

## Best Practices

### Do's

1. **Always validate manifest** before loading plugin
2. **Use provided lifecycle hooks** for initialization/cleanup
3. **Handle errors gracefully** with proper rollback
4. **Log important events** at appropriate levels
5. **Respect organization boundaries** in multi-tenant context
6. **Use the config service** for plugin settings
7. **Test plugins in isolation** before integration

### Don'ts

1. **Don't bypass the registry** for plugin operations
2. **Don't access other plugins directly** - use events
3. **Don't store global state** - use plugin config
4. **Don't modify core models** - extend with relationships
5. **Don't skip authorization checks** in plugin code
6. **Don't hardcode organization IDs** - use context

## Next Steps

- Review **PLUGIN_MIGRATION_PLAN.md** for migration steps
- Review **PLUGIN_IMPLEMENTATION_GUIDE.md** for examples
- Review **PLUGIN_SECURITY_MODEL.md** for trust model and best practices

---

**Last Updated**: November 30, 2025
