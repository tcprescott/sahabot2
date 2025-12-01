# Plugin Migration Plan

## Executive Summary

This document provides a detailed step-by-step plan for migrating the Tournament, AsyncQualifier, and Randomizer systems to the plugin architecture. The migration is designed to be incremental, backwards-compatible, and reversible at each phase.

## Migration Overview

### Goals

1. **Zero Downtime**: No service interruption during migration
2. **Backwards Compatible**: Existing functionality works identically
3. **Incremental**: Can pause/resume at any phase
4. **Reversible**: Can roll back to previous state
5. **Testable**: Each phase can be verified independently

### Timeline Estimate

| Phase | Description | Duration | Risk |
|-------|-------------|----------|------|
| Phase 1 | Foundation & Core Infrastructure | 2-3 weeks | Low |
| Phase 2 | Tournament Plugin Creation | 2-3 weeks | Medium |
| Phase 3 | AsyncQualifier Plugin Creation | 2 weeks | Medium |
| Phase 4 | Presets & Randomizer Plugins | 3-4 weeks | Medium |
| Phase 5 | Integration Plugins (RaceTime, SpeedGaming, DiscordEvents) | 2-3 weeks | Medium |
| Phase 6 | Utility Plugins (RacerVerification, Notifications) | 1-2 weeks | Low |
| Phase 7 | Integration & Testing | 1-2 weeks | Low |
| Phase 8 | Cleanup & Documentation | 1 week | Low |

**Total Estimated Duration**: 14-20 weeks

## Phase 1: Foundation & Core Infrastructure

### 1.1 Create Plugin Core Package

**Duration**: 3-4 days
**Risk**: Low

Create the core plugin infrastructure:

```
application/
└── plugins/
    ├── __init__.py
    ├── registry.py
    ├── manifest.py
    ├── loader.py
    ├── lifecycle.py
    ├── config_service.py
    ├── exceptions.py
    └── base/
        ├── __init__.py
        ├── plugin.py
        ├── model_provider.py
        ├── route_provider.py
        ├── page_provider.py
        ├── command_provider.py
        ├── event_provider.py
        └── task_provider.py
```

**Tasks**:

1. [ ] Create `application/plugins/__init__.py`
2. [ ] Implement `PluginManifest` pydantic model
3. [ ] Implement `BasePlugin` abstract class
4. [ ] Implement provider interfaces
5. [ ] Implement `PluginRegistry` singleton
6. [ ] Implement `PluginLifecycleManager`
7. [ ] Implement `PluginConfigService`
8. [ ] Create exception classes
9. [ ] Write unit tests for core infrastructure

**Verification**:
```python
# Test that core infrastructure works
from application.plugins import PluginRegistry, BasePlugin

class TestPlugin(BasePlugin):
    @property
    def plugin_id(self):
        return "test"
    
    @property
    def manifest(self):
        return PluginManifest(id="test", name="Test", version="1.0.0", ...)

# Should register without error
PluginRegistry.register(TestPlugin())
```

### 1.2 Create Database Models

**Duration**: 2 days
**Risk**: Low

Add plugin-related database models:

```python
# models/plugin.py

class PluginType(str, Enum):
    BUILTIN = "builtin"
    EXTERNAL = "external"


class Plugin(Model):
    """Plugin installation record."""
    id = fields.IntField(pk=True)
    plugin_id = fields.CharField(max_length=100, unique=True)
    name = fields.CharField(max_length=255)
    version = fields.CharField(max_length=50)
    type = fields.CharEnumField(PluginType)
    is_installed = fields.BooleanField(default=True)
    installed_at = fields.DatetimeField(null=True)
    installed_by = fields.ForeignKeyField("models.User", null=True)
    config = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "plugins"


class OrganizationPlugin(Model):
    """Organization-level plugin enablement."""
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField(
        "models.Organization", related_name="plugins"
    )
    plugin_id = fields.CharField(max_length=100)
    enabled = fields.BooleanField(default=True)
    enabled_at = fields.DatetimeField(null=True)
    enabled_by = fields.ForeignKeyField("models.User", null=True)
    config = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "organization_plugins"
        unique_together = (("organization", "plugin_id"),)


class PluginMigration(Model):
    """Plugin migration tracking."""
    id = fields.IntField(pk=True)
    plugin_id = fields.CharField(max_length=100)
    version = fields.CharField(max_length=50)
    migration_name = fields.CharField(max_length=255)
    applied_at = fields.DatetimeField(auto_now_add=True)
    success = fields.BooleanField(default=True)
    error_message = fields.TextField(null=True)

    class Meta:
        table = "plugin_migrations"
        unique_together = (("plugin_id", "migration_name"),)
```

**Tasks**:

1. [ ] Create `models/plugin.py` with models
2. [ ] Add models to `models/__init__.py`
3. [ ] Run `poetry run aerich migrate --name "add_plugin_models"`
4. [ ] Apply migration with `poetry run aerich upgrade`
5. [ ] Create `PluginRepository` for data access
6. [ ] Write tests for new models

**Verification**:
```python
# Verify migration applied
from models.plugin import Plugin, OrganizationPlugin

# Should create without error
plugin = await Plugin.create(
    plugin_id="test",
    name="Test Plugin",
    version="1.0.0",
    type=PluginType.BUILTIN
)

org_plugin = await OrganizationPlugin.create(
    organization_id=1,
    plugin_id="test",
    enabled=True
)
```

### 1.3 Integrate with Application Startup

**Duration**: 2-3 days
**Risk**: Medium

Modify `main.py` to initialize plugin system:

```python
# main.py additions

from application.plugins.registry import PluginRegistry
from application.plugins.loader import PluginLoader

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing startup code ...

    # Initialize plugin system
    await PluginLoader.discover_plugins()
    await PluginLoader.load_all_plugins()
    await PluginRegistry.register_all()
    logger.info("Plugin system initialized with %d plugins",
                PluginRegistry.get_plugin_count())

    yield

    # Shutdown
    await PluginRegistry.unload_all()
    # ... existing shutdown code ...
```

**Tasks**:

1. [ ] Create `PluginLoader` class for discovery
2. [ ] Modify `main.py` to initialize plugins
3. [ ] Modify `frontend.py` to register plugin pages
4. [ ] Modify `api/__init__.py` to mount plugin routes
5. [ ] Modify `discordbot/client.py` to load plugin commands
6. [ ] Add plugin task registration in `task_scheduler_service.py`
7. [ ] Integration tests for startup/shutdown

**Verification**:
```bash
# Start application and verify in logs
poetry run python main.py

# Should see:
# INFO - Plugin system initialized with 0 plugins
```

### 1.4 Create Plugin Directory Structure

**Duration**: 1 day
**Risk**: Low

Create filesystem structure for plugins:

```
plugins/
├── __init__.py
├── builtin/
│   ├── __init__.py
│   ├── tournament/          # Will be created in Phase 2
│   └── async_qualifier/     # Will be created in Phase 3
└── external/
    └── __init__.py          # Empty initially
```

**Tasks**:

1. [ ] Create `plugins/` directory
2. [ ] Create `plugins/builtin/` directory
3. [ ] Create `plugins/external/` directory
4. [ ] Add `__init__.py` files
5. [ ] Update `.gitignore` for `plugins/external/`

### 1.5 Create Admin UI for Plugin Management

**Duration**: 3-4 days
**Risk**: Low

Add plugin management pages to admin panel:

```python
# pages/admin.py additions

# New view for plugin management
from views.admin.admin_plugins import AdminPluginsView

# In admin page content:
if view == "plugins":
    plugins_view = AdminPluginsView(user)
    await plugins_view.render()
```

**Tasks**:

1. [ ] Create `views/admin/admin_plugins.py`
2. [ ] Add plugin list view (installed, enabled status)
3. [ ] Add plugin enable/disable per-organization
4. [ ] Add plugin configuration dialog
5. [ ] Add plugin management to sidebar
6. [ ] Create `components/dialogs/admin/plugin_config.py`

**Verification**:
- Navigate to `/admin?view=plugins`
- Should see empty plugin list (no plugins yet)
- Can enable/disable plugins per org (once plugins exist)

### 1.6 Create DiscordBot Global Plugin

**Duration**: 2-3 days
**Risk**: Low

Create the core Discord bot infrastructure as a global plugin. This is a special plugin that is always enabled and provides the bot infrastructure for other plugins.

```
plugins/builtin/discordbot/
├── manifest.yaml
├── __init__.py
├── plugin.py               # DiscordBotPlugin(BasePlugin)
├── client.py               # DiscordBot class (migrated from discordbot/client.py)
├── lifecycle.py            # Bot start/stop management
└── events/
    ├── __init__.py
    └── types.py            # BotReady, BotDisconnected events
```

**manifest.yaml**:
```yaml
id: discordbot
name: Discord Bot
version: 1.0.0
description: Core Discord bot infrastructure for command handling and Discord API access
author: SahaBot2 Team
type: builtin
category: global
enabled_by_default: true
private: false
global_plugin: true  # Special flag: always enabled, not organization-scoped

requires:
  sahabot2: ">=1.0.0"
  plugins: []  # No plugin dependencies

provides:
  services:
    - DiscordBotService
  
  exports:
    - get_bot_instance()
    - DiscordBot class
  
  events:
    - BotReadyEvent
    - BotDisconnectedEvent
```

**Tasks**:

1. [ ] Create plugin directory structure
2. [ ] Create manifest.yaml with `global_plugin: true` flag
3. [ ] Migrate `discordbot/client.py` to plugin
4. [ ] Create bot lifecycle management service
5. [ ] Update main.py to use plugin's bot startup
6. [ ] Create BotReady and BotDisconnected events
7. [ ] Implement DiscordBotPlugin class
8. [ ] Register plugin with registry
9. [ ] Integration testing

**Verification**:
```python
# Test that DiscordBot plugin provides bot access
from application.plugins import PluginRegistry

discordbot = PluginRegistry.get('discordbot')
bot = discordbot.get_bot_instance()
assert bot is not None
assert bot.is_ready
```

## Phase 2: Tournament Plugin Creation

### 2.1 Create Plugin Structure

**Duration**: 2 days
**Risk**: Low

Create the Tournament plugin directory structure:

```
plugins/builtin/tournament/
├── __init__.py
├── manifest.yaml
├── plugin.py
├── models/
│   ├── __init__.py
│   └── tournament.py
├── services/
│   ├── __init__.py
│   └── tournament_service.py
├── repositories/
│   ├── __init__.py
│   └── tournament_repository.py
├── pages/
│   ├── __init__.py
│   ├── tournaments.py
│   └── tournament_admin.py
├── views/
│   ├── __init__.py
│   └── ... (copy from views/tournaments/)
├── dialogs/
│   ├── __init__.py
│   └── ... (copy from components/dialogs/tournaments/)
├── api/
│   ├── __init__.py
│   └── routes.py
├── events/
│   ├── __init__.py
│   ├── types.py
│   └── listeners.py
└── tasks/
    ├── __init__.py
    └── sync_tasks.py
```

**Tasks**:

1. [ ] Create directory structure
2. [ ] Create `manifest.yaml` with full manifest
3. [ ] Create `plugin.py` with `TournamentPlugin` class

### 2.2 Migrate Models

**Duration**: 2-3 days
**Risk**: Medium

Move Tournament models to plugin:

**Current Location**:
- `models/match_schedule.py`

**New Location**:
- `plugins/builtin/tournament/models/tournament.py`

**Strategy**: Create wrapper imports for backwards compatibility

```python
# plugins/builtin/tournament/models/tournament.py
from tortoise import fields
from tortoise.models import Model

# ... (copy model definitions from match_schedule.py)

class Tournament(Model):
    # ... existing definition
    pass

class Match(Model):
    # ... existing definition
    pass

# etc.


# models/match_schedule.py (backwards compatibility)
"""
DEPRECATED: Import from plugins.builtin.tournament.models instead.

This module exists for backwards compatibility only.
"""
import warnings
warnings.warn(
    "models.match_schedule is deprecated. "
    "Import from plugins.builtin.tournament.models instead.",
    DeprecationWarning,
    stacklevel=2
)

from plugins.builtin.tournament.models.tournament import (
    Tournament,
    Match,
    MatchPlayers,
    TournamentPlayers,
    StreamChannel,
    Crew,
    MatchSeed,
)

__all__ = [
    "Tournament",
    "Match",
    "MatchPlayers",
    "TournamentPlayers",
    "StreamChannel",
    "Crew",
    "MatchSeed",
]
```

**Tasks**:

1. [ ] Copy models to plugin location
2. [ ] Update import paths in models
3. [ ] Create backwards-compatible wrapper
4. [ ] Update `models/__init__.py`
5. [ ] Test model imports from both locations
6. [ ] Run existing tests to verify no breakage

**Verification**:
```python
# Both should work:
from models.match_schedule import Tournament  # Deprecated warning
from plugins.builtin.tournament.models import Tournament  # Preferred
```

### 2.3 Migrate Services

**Duration**: 2-3 days
**Risk**: Medium

Move Tournament services to plugin:

**Current Location**:
- `application/services/tournaments/tournament_service.py`
- `application/services/tournaments/preset_selection_service.py`
- etc.

**New Location**:
- `plugins/builtin/tournament/services/`

**Strategy**: Same wrapper approach as models

```python
# application/services/tournaments/__init__.py (backwards compatibility)
"""
DEPRECATED: Import from plugins.builtin.tournament.services instead.
"""
import warnings
warnings.warn(
    "application.services.tournaments is deprecated. "
    "Import from plugins.builtin.tournament.services instead.",
    DeprecationWarning,
    stacklevel=2
)

from plugins.builtin.tournament.services import (
    TournamentService,
    PresetSelectionService,
    # ... etc
)
```

**Tasks**:

1. [ ] Copy services to plugin location
2. [ ] Update import paths in services
3. [ ] Create backwards-compatible wrappers
4. [ ] Test service imports
5. [ ] Run existing tests

### 2.4 Migrate Repositories

**Duration**: 1-2 days
**Risk**: Medium

Move Tournament repository to plugin.

**Tasks**:

1. [ ] Copy repository to plugin location
2. [ ] Update import paths
3. [ ] Create backwards-compatible wrapper
4. [ ] Test repository imports

### 2.5 Migrate Pages and Views

**Duration**: 2-3 days
**Risk**: Medium

Move Tournament pages and views to plugin.

**Current Locations**:
- `pages/tournaments.py`
- `pages/tournament_admin.py`
- `pages/tournament_match_settings.py`
- `views/tournaments/`
- `views/tournament_admin/`

**Tasks**:

1. [ ] Copy pages to plugin location
2. [ ] Update to use plugin page registration pattern
3. [ ] Copy views to plugin location
4. [ ] Copy dialogs to plugin location
5. [ ] Update all import paths
6. [ ] Create backwards-compatible wrappers in original locations
7. [ ] Test all pages render correctly

### 2.6 Migrate API Routes

**Duration**: 1-2 days
**Risk**: Medium

Move Tournament API routes to plugin.

**Current Location**:
- `api/routes/tournaments.py`
- `api/routes/tournament_match_settings.py`

**Tasks**:

1. [ ] Copy routes to plugin location
2. [ ] Update to use plugin route registration
3. [ ] Create backwards-compatible wrapper
4. [ ] Test all API endpoints

### 2.7 Migrate Events

**Duration**: 1-2 days
**Risk**: Low

Move Tournament events to plugin.

**Tasks**:

1. [ ] Create `events/types.py` with Tournament events
2. [ ] Create `events/listeners.py` with Tournament listeners
3. [ ] Extract Tournament events from `application/events/types.py`
4. [ ] Update event imports
5. [ ] Test event emission and handling

### 2.8 Migrate Tasks

**Duration**: 1 day
**Risk**: Low

Move Tournament scheduled tasks to plugin.

**Tasks**:

1. [ ] Identify Tournament-specific tasks
2. [ ] Create `tasks/sync_tasks.py`
3. [ ] Register tasks through plugin interface
4. [ ] Test task execution

### 2.9 Implement Plugin Class

**Duration**: 2-3 days
**Risk**: Low

Implement the full `TournamentPlugin` class:

```python
# plugins/builtin/tournament/plugin.py

from application.plugins.base import BasePlugin, PluginManifest
from plugins.builtin.tournament.models import (
    Tournament, Match, MatchPlayers, TournamentPlayers,
    StreamChannel, Crew, MatchSeed
)
from plugins.builtin.tournament.services import TournamentService
from plugins.builtin.tournament.api.routes import router
from plugins.builtin.tournament.events.types import (
    TournamentCreatedEvent, MatchScheduledEvent, ...
)
from plugins.builtin.tournament.events.listeners import register_listeners
from plugins.builtin.tournament.tasks.sync_tasks import get_tasks


class TournamentPlugin(BasePlugin):
    """Tournament system plugin."""

    @property
    def plugin_id(self) -> str:
        return "tournament"

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            id="tournament",
            name="Tournament System",
            version="1.0.0",
            description="Live tournament management with RaceTime.gg integration",
            author="SahaBot2 Team",
            type="builtin",
            category="competition",
            # ... full manifest
        )

    def get_models(self):
        return [
            Tournament, Match, MatchPlayers, TournamentPlayers,
            StreamChannel, Crew, MatchSeed
        ]

    def get_api_router(self):
        return router

    def get_pages(self):
        from plugins.builtin.tournament.pages import get_page_registrations
        return get_page_registrations()

    def get_event_types(self):
        return [
            TournamentCreatedEvent,
            MatchScheduledEvent,
            # ... etc
        ]

    def get_event_listeners(self):
        return register_listeners()

    def get_scheduled_tasks(self):
        return get_tasks()

    async def on_load(self):
        logger.info("Tournament plugin loaded")

    async def on_enable(self, organization_id, config):
        logger.info("Tournament plugin enabled for org %s", organization_id)

    async def on_disable(self, organization_id):
        logger.info("Tournament plugin disabled for org %s", organization_id)
```

**Tasks**:

1. [ ] Implement all provider methods
2. [ ] Test plugin loading
3. [ ] Test plugin enable/disable
4. [ ] Integration test full functionality

### 2.10 Register Plugin

**Duration**: 1 day
**Risk**: Low

Register Tournament plugin as built-in:

```python
# plugins/builtin/__init__.py

from plugins.builtin.tournament import TournamentPlugin

BUILTIN_PLUGINS = [
    TournamentPlugin,
]
```

**Tasks**:

1. [ ] Add to `BUILTIN_PLUGINS` list
2. [ ] Test plugin discovery
3. [ ] Test plugin auto-loading at startup
4. [ ] Verify all Tournament functionality works

## Phase 3: AsyncQualifier Plugin Creation

### 3.1 - 3.10: Repeat Phase 2 for AsyncQualifier

Follow the same process as Phase 2, but for the AsyncQualifier system.

**Current Locations**:
- `models/async_tournament.py`
- `application/services/async_qualifiers/`
- `application/repositories/async_qualifier_repository.py`
- `pages/async_qualifiers.py`
- `pages/async_qualifier_admin.py`
- `views/async_qualifiers/`
- `components/dialogs/async_qualifiers/`
- `api/routes/async_qualifiers.py`
- `api/routes/async_live_races.py`
- `discordbot/commands/async_qualifier.py`

**Plugin Structure**:
```
plugins/builtin/async_qualifier/
├── __init__.py
├── manifest.yaml
├── plugin.py
├── models/
├── services/
├── repositories/
├── pages/
├── views/
├── dialogs/
├── api/
├── commands/          # Discord commands
├── events/
└── tasks/
```

**Key Differences from Tournament**:

1. **Discord Commands**: AsyncQualifier has Discord commands that Tournament doesn't
2. **Live Races**: Additional model and service for live races
3. **Scoring System**: Complex scoring logic

**Tasks** (abbreviated, same pattern as Phase 2):

1. [ ] Create plugin directory structure
2. [ ] Create manifest.yaml
3. [ ] Migrate models
4. [ ] Migrate services
5. [ ] Migrate repository
6. [ ] Migrate pages and views
7. [ ] Migrate API routes
8. [ ] Migrate Discord commands (cog)
9. [ ] Migrate events
10. [ ] Migrate tasks
11. [ ] Implement AsyncQualifierPlugin class
12. [ ] Register plugin
13. [ ] Full integration testing

## Phase 4: Presets & Randomizer Plugins Creation (SUBSTANTIALLY COMPLETE)

**Duration**: 3-4 weeks
**Risk**: Medium
**Status**: Core plugin structure created. Discord commands and API routes still pending.

### 4.1 Overview

The Presets plugin provides the core preset management system that all randomizer plugins depend on. Each randomizer plugin extends this with randomizer-specific functionality.

**Plugin Creation Order**:
1. **Presets Plugin** (first - no dependencies) ✅
2. **Randomizer Plugins** (depend on Presets) ✅

**Created Plugins (14 total)**:
- Presets (core preset management)
- ALTTPR (A Link to the Past Randomizer)
- SM (Super Metroid Randomizer)
- SMZ3 (SMZ3 Combo Randomizer)
- OOTR (Ocarina of Time Randomizer)
- AOSR (Aria of Sorrow Randomizer)
- Z1R (Zelda 1 Randomizer)
- FFR (Final Fantasy Randomizer)
- SMB3R (Super Mario Bros 3 Randomizer)
- CTJets (Chrono Trigger Jets of Time)
- Bingosync
- Avianart (Door Randomizer)

### 4.2 Presets Plugin (Priority: Critical)

**Duration**: 3-4 days
**Dependencies**: Phase 1 (Core Infrastructure)

The Presets plugin provides core preset functionality without any randomizer-specific logic.

```
plugins/builtin/presets/
├── manifest.yaml
├── __init__.py
├── plugin.py               # PresetsPlugin(BasePlugin)
├── models/
│   ├── __init__.py
│   ├── preset_namespace.py # PresetNamespace model
│   └── preset.py           # Base Preset model (randomizer-agnostic)
├── services/
│   ├── __init__.py
│   ├── preset_namespace_service.py
│   └── preset_service.py   # Core preset CRUD
├── repositories/
│   ├── __init__.py
│   ├── preset_namespace_repository.py
│   └── preset_repository.py
├── pages/
│   ├── __init__.py
│   └── presets.py          # Preset management UI
├── api/
│   ├── __init__.py
│   └── routes.py           # /api/plugins/presets/...
└── events/
    ├── __init__.py
    └── types.py            # PresetCreated, PresetUpdated, etc.
```

**manifest.yaml**:
```yaml
id: presets
name: Preset Management System
version: 1.0.0
description: Core preset storage, namespaces, and sharing functionality
author: SahaBot2 Team
type: builtin
category: core
enabled_by_default: true
private: false

requires:
  sahabot2: ">=1.0.0"
  plugins: []  # No plugin dependencies

provides:
  models:
    - PresetNamespace
    - Preset
  
  services:
    - PresetNamespaceService
    - PresetService
  
  pages:
    - path: /org/{org_id}/presets
      name: Preset Management
  
  api_routes:
    prefix: /presets
    tags: [presets, namespaces]
  
  events:
    - PresetCreatedEvent
    - PresetUpdatedEvent
    - PresetDeletedEvent
    - NamespaceCreatedEvent
```

**Tasks**:

1. [x] Create plugin directory structure
2. [x] Create manifest.yaml
3. [x] Migrate `PresetNamespace` model to plugin (re-exported)
4. [x] Create base `Preset` model (re-exported from RandomizerPreset)
5. [x] Migrate `preset_namespace_service.py` to plugin (re-exported)
6. [x] Create core `preset_service.py` (re-exported as RandomizerPresetService)
7. [ ] Create preset management UI page
8. [ ] Create API routes
9. [x] Define preset events
10. [x] Implement PresetsPlugin class
11. [x] Register plugin with registry
12. [x] Integration testing

### 4.3 Randomizer Plugin List

| Plugin | Priority | Complexity | RaceTime Handler | Depends On |
|--------|----------|------------|------------------|------------|
| **ALTTPR** | High | High | Yes (alttpr_handler.py) | Presets |
| **SM** | High | High | Yes (sm_race_handler.py) | Presets |
| **SMZ3** | High | Medium | Yes (smz3_race_handler.py) | Presets |
| **OOTR** | Medium | Medium | No | Presets |
| **AOSR** | Low | Low | No | Presets |
| **Z1R** | Low | Low | No | Presets |
| **FFR** | Low | Low | No | Presets |
| **SMB3R** | Low | Low | No | Presets |
| **CTJets** | Low | Low | No | Presets |
| **Bingosync** | Medium | Low | No | None |

### 4.4 ALTTPR Plugin (Priority: High)

**Duration**: 4-5 days
**Dependencies**: Phase 1, Phase 2 (Tournament plugin for RaceTime integration)

```
plugins/builtin/alttpr/
├── manifest.yaml
├── __init__.py
├── plugin.py               # ALTTPRPlugin(BasePlugin)
├── services/
│   ├── __init__.py
│   ├── alttpr_service.py   # Seed generation
│   └── mystery_service.py  # Mystery mode weights
├── handlers/
│   ├── __init__.py
│   └── alttpr_handler.py   # RaceTime.gg race handler
├── commands/
│   ├── __init__.py
│   └── alttpr_commands.py  # Discord !seed, !preset commands
├── api/
│   ├── __init__.py
│   └── routes.py           # /api/plugins/alttpr/generate
└── presets/                # Default preset configurations
    └── defaults.yaml
```

**Tasks**:

1. [x] Create plugin directory structure
2. [x] Create manifest.yaml with ALTTPR metadata
3. [x] Migrate `alttpr_service.py` to plugin (re-exported)
4. [x] Migrate `alttpr_mystery_service.py` to plugin (re-exported)
5. [x] Migrate `alttpr_handler.py` to plugin (re-exported)
6. [ ] Create ALTTPR-specific Discord commands
7. [ ] Create API routes for seed generation
8. [x] Implement ALTTPRPlugin class with lifecycle hooks
9. [x] Register plugin with registry
10. [x] Integration testing

### 4.4 SM Plugin (Priority: High)

**Duration**: 3-4 days
**Dependencies**: Phase 1

```
plugins/builtin/sm/
├── manifest.yaml
├── plugin.py               # SMPlugin(BasePlugin)
├── services/
│   ├── __init__.py
│   ├── sm_service.py       # VARIA/DASH seed generation
│   └── sm_defaults.py      # Default configurations
├── handlers/
│   └── sm_race_handler.py  # RaceTime.gg race handler
├── commands/
│   └── sm_commands.py
└── api/
    └── routes.py
```

**Tasks**:

1. [x] Create plugin directory structure
2. [x] Migrate `sm_service.py` to plugin (re-exported)
3. [x] Migrate `sm_defaults.py` to plugin (re-exported)
4. [x] Migrate `sm_race_handler.py` to plugin (re-exported)
5. [ ] Create SM-specific Discord commands
6. [ ] Create API routes
7. [x] Implement SMPlugin class
8. [x] Integration testing

### 4.5 SMZ3 Plugin (Priority: High)

**Duration**: 2-3 days
**Dependencies**: Phase 1

```
plugins/builtin/smz3/
├── manifest.yaml
├── plugin.py               # SMZ3Plugin(BasePlugin)
├── services/
│   └── smz3_service.py
├── handlers/
│   └── smz3_race_handler.py
├── commands/
│   └── smz3_commands.py
└── api/
    └── routes.py
```

**Tasks**:

1. [x] Create plugin directory structure
2. [x] Migrate `smz3_service.py` to plugin (re-exported)
3. [x] Migrate `smz3_race_handler.py` to plugin (re-exported)
4. [ ] Create SMZ3-specific Discord commands
5. [ ] Create API routes
6. [x] Implement SMZ3Plugin class
7. [x] Integration testing

### 4.6 OOTR Plugin (Priority: Medium)

**Duration**: 2 days

```
plugins/builtin/ootr/
├── manifest.yaml
├── plugin.py
├── services/
│   └── ootr_service.py
├── commands/
│   └── ootr_commands.py
└── api/
    └── routes.py
```

**Tasks**:

1. [x] Create plugin directory structure
2. [x] Migrate `ootr_service.py` to plugin (re-exported)
3. [ ] Create OOTR-specific Discord commands
4. [ ] Create API routes
5. [x] Implement OOTRPlugin class
6. [x] Integration testing

### 4.7 Other Randomizer Plugins (Priority: Low)

**Duration**: 1 day each

The following randomizers follow a simpler pattern (no RaceTime handlers):

| Plugin | Source Service |
|--------|----------------|
| **AOSR** | `aosr_service.py` |
| **Z1R** | `z1r_service.py` |
| **FFR** | `ffr_service.py` |
| **SMB3R** | `smb3r_service.py` |
| **CTJets** | `ctjets_service.py` |
| **Bingosync** | `bingosync_service.py` |

**Standard structure for simple plugins**:

```
plugins/builtin/<randomizer>/
├── manifest.yaml
├── plugin.py
├── services/
│   └── <randomizer>_service.py
├── commands/
│   └── <randomizer>_commands.py
└── api/
    └── routes.py
```

**Tasks per plugin**:

1. [x] Create plugin directory structure
2. [x] Migrate service to plugin (re-exported)
3. [ ] Create Discord commands (if applicable)
4. [ ] Create API routes
5. [x] Implement plugin class
6. [x] Integration testing

**Completed Plugins**:
- [x] AOSR (Aria of Sorrow Randomizer)
- [x] Z1R (Zelda 1 Randomizer)
- [x] FFR (Final Fantasy Randomizer)
- [x] SMB3R (Super Mario Bros 3 Randomizer)
- [x] CTJets (Chrono Trigger Jets of Time)
- [x] Bingosync
- [x] Avianart (Door Randomizer)

### 4.8 Shared Randomizer Infrastructure

**Duration**: 2 days

Create shared infrastructure that randomizer plugins can use:

```
plugins/builtin/_randomizer_base/
├── __init__.py
├── base_randomizer_plugin.py  # BaseRandomizerPlugin(BasePlugin)
├── result.py                  # RandomizerResult dataclass
├── preset_mixin.py            # Preset management mixin
└── command_mixin.py           # Common Discord command patterns
```

**Tasks**:

1. [x] Create `BaseRandomizerPlugin` abstract class
2. [x] Create `RandomizerResult` dataclass (re-exported from core)
3. [ ] Create preset management mixin
4. [ ] Create common Discord command patterns
5. [x] Update randomizer plugins to use shared base
6. [ ] Documentation for creating new randomizer plugins

### 4.9 Migration of Existing RandomizerService

**Duration**: 1 day

Update the `RandomizerService` factory to use plugins:

```python
# Before (current)
from application.services.randomizer import RandomizerService

service = RandomizerService()
alttpr = service.get_randomizer('alttpr')

# After (plugin-based)
from application.plugins import PluginRegistry

alttpr_plugin = PluginRegistry.get('alttpr')
alttpr = alttpr_plugin.get_service()
```

**Tasks**:

1. [ ] Update `RandomizerService` to use plugin registry
2. [ ] Add backwards-compatible wrapper
3. [ ] Add deprecation warnings
4. [ ] Update all callers to use new pattern
5. [ ] Integration testing

### 4.10 Verification

**Before Phase 5**:

1. [x] All 10+ randomizer plugins created and registered (12 plugins total)
2. [x] Each plugin can instantiate services independently
3. [x] RaceTime handlers accessible through plugin exports (ALTTPR, SM, SMZ3)
4. [ ] Discord commands work for each randomizer
5. [ ] API routes accessible for each randomizer
6. [x] Presets work with plugin-based system
7. [x] No performance degradation
8. [x] Backwards compatibility maintained

## Phase 5: Integration Plugins Creation

**Duration**: 2-3 weeks
**Risk**: Medium

### 5.1 RaceTime Plugin

**Duration**: 4-5 days
**Dependencies**: Phase 1

The RaceTime plugin encapsulates all RaceTime.gg integration functionality.

```
plugins/builtin/racetime/
├── manifest.yaml
├── __init__.py
├── plugin.py               # RaceTimePlugin(BasePlugin)
├── models/
│   ├── __init__.py
│   ├── racetime_bot.py     # RacetimeBot, RacetimeBotOrganization
│   ├── racetime_room.py    # RacetimeRoom
│   └── race_room_profile.py # RaceRoomProfile
├── services/
│   ├── __init__.py
│   ├── racetime_api_service.py
│   ├── racetime_bot_service.py
│   ├── racetime_room_service.py
│   └── race_room_profile_service.py
├── handlers/
│   ├── __init__.py
│   └── base_handler.py     # BaseRaceHandler infrastructure
├── pages/
│   ├── __init__.py
│   └── racetime_admin.py   # Bot management UI
├── api/
│   └── routes.py
└── events/
    └── types.py            # RaceStarted, RaceFinished, etc.
```

**Tasks**:
1. [ ] Create plugin directory structure
2. [ ] Migrate RaceTime models
3. [ ] Migrate RaceTime services
4. [ ] Migrate base race handler infrastructure
5. [ ] Create RaceTime admin UI
6. [ ] Create API routes
7. [ ] Integration testing

### 5.2 SpeedGaming Plugin

**Duration**: 2-3 days
**Dependencies**: Phase 1

```
plugins/builtin/speedgaming/
├── manifest.yaml
├── plugin.py               # SpeedGamingPlugin(BasePlugin)
├── services/
│   ├── speedgaming_service.py
│   └── speedgaming_etl_service.py
├── tasks/
│   └── schedule_sync.py    # Scheduled sync task
└── api/
    └── routes.py
```

**Tasks**:
1. [ ] Create plugin directory structure
2. [ ] Migrate SpeedGaming services
3. [ ] Migrate sync task
4. [ ] Create API routes
5. [ ] Integration testing

### 5.3 DiscordEvents Plugin

**Duration**: 2-3 days
**Dependencies**: Phase 1

```
plugins/builtin/discord_events/
├── manifest.yaml
├── plugin.py               # DiscordEventsPlugin(BasePlugin)
├── models/
│   └── discord_scheduled_event.py
├── services/
│   └── discord_scheduled_event_service.py
├── tasks/
│   ├── scheduled_events_sync.py
│   └── orphaned_events_cleanup.py
└── api/
    └── routes.py
```

**Tasks**:
1. [ ] Create plugin directory structure
2. [ ] Migrate DiscordScheduledEvent model
3. [ ] Migrate event service
4. [ ] Migrate sync and cleanup tasks
5. [ ] Integration testing

### 5.4 Verification

**Before Phase 6**:

1. [ ] RaceTime plugin can manage bots
2. [ ] RaceTime plugin can create race rooms
3. [ ] SpeedGaming plugin can sync schedules
4. [ ] DiscordEvents plugin can create/update events
5. [ ] All integration plugins work independently

## Phase 6: Utility Plugins Creation

**Duration**: 1-2 weeks
**Risk**: Low

### 6.1 RacerVerification Plugin

**Duration**: 2-3 days
**Dependencies**: Phase 1, RaceTime Plugin

```
plugins/builtin/racer_verification/
├── manifest.yaml
├── plugin.py               # RacerVerificationPlugin(BasePlugin)
├── models/
│   ├── racer_verification.py
│   └── user_racer_verification.py
├── services/
│   └── racer_verification_service.py
├── pages/
│   └── verification_admin.py
├── tasks/
│   └── verification_check.py  # Periodic verification task
└── api/
    └── routes.py
```

**manifest.yaml** (example of dependency):
```yaml
id: racer_verification
name: Racer Verification
requires:
  plugins:
    - racetime  # Depends on RaceTime plugin for race data
```

**Tasks**:
1. [ ] Create plugin directory structure
2. [ ] Migrate verification models
3. [ ] Migrate verification service
4. [ ] Create admin UI
5. [ ] Migrate/create verification task
6. [ ] Integration testing

### 6.2 Notifications Plugin

**Duration**: 2-3 days
**Dependencies**: Phase 1

```
plugins/builtin/notifications/
├── manifest.yaml
├── plugin.py               # NotificationsPlugin(BasePlugin)
├── models/
│   ├── notification_subscription.py
│   └── notification_log.py
├── services/
│   └── notification_service.py
├── handlers/
│   ├── __init__.py
│   ├── base_handler.py
│   └── discord_handler.py
├── pages/
│   └── subscription_settings.py  # User notification preferences
└── api/
    └── routes.py
```

**Tasks**:
1. [ ] Create plugin directory structure
2. [ ] Migrate notification models
3. [ ] Migrate notification service
4. [ ] Migrate notification handlers
5. [ ] Create subscription settings UI
6. [ ] Integration testing

### 6.3 Verification

**Before Phase 7**:

1. [ ] RacerVerification plugin can verify users
2. [ ] RacerVerification plugin can grant Discord roles
3. [ ] Notifications plugin can send Discord DMs
4. [ ] Notifications plugin can manage subscriptions
5. [ ] All utility plugins work with their dependencies

## Phase 7: Integration & Testing

### 7.1 Integration Testing

**Duration**: 3-4 days
**Risk**: Low

Comprehensive testing of the plugin system:

**Test Categories**:

1. **Plugin Loading Tests**
   - [ ] All built-in plugins discovered
   - [ ] Plugins load in correct order
   - [ ] Dependencies resolved correctly
   - [ ] Invalid plugins rejected

2. **Plugin Lifecycle Tests**
   - [ ] on_load called at startup
   - [ ] on_enable called when enabled for org
   - [ ] on_disable called when disabled for org
   - [ ] on_unload called at shutdown

3. **Model Integration Tests**
   - [ ] Plugin models registered with Tortoise
   - [ ] Relationships work across plugins
   - [ ] Migrations apply correctly

4. **Page/Route Integration Tests**
   - [ ] Plugin pages render correctly
   - [ ] Plugin API routes work
   - [ ] Authorization enforced

5. **Event Integration Tests**
   - [ ] Plugin events emitted correctly
   - [ ] Cross-plugin event listening works

6. **Backwards Compatibility Tests**
   - [ ] Old import paths still work
   - [ ] Deprecation warnings shown
   - [ ] No breaking changes

### 7.2 Performance Testing

**Duration**: 1-2 days
**Risk**: Low

Verify no performance regression:

**Metrics to Measure**:

1. **Startup Time**
   - Measure time to load all plugins
   - Should be < 5 seconds

2. **Request Latency**
   - Measure API response times
   - Should not increase by > 5%

3. **Memory Usage**
   - Measure memory with plugins
   - Should not increase by > 10%

**Tasks**:

1. [ ] Create performance benchmarks
2. [ ] Run benchmarks before migration
3. [ ] Run benchmarks after migration
4. [ ] Document results

### 7.3 Migration Data Verification

**Duration**: 1 day
**Risk**: Low

Verify all data accessible through plugins:

**Tasks**:

1. [ ] Verify existing Tournament data accessible
2. [ ] Verify existing AsyncQualifier data accessible
3. [ ] Verify existing Randomizer functionality works
4. [ ] Verify RaceTime integration works
5. [ ] Verify SpeedGaming sync works
6. [ ] Verify DiscordEvents work
7. [ ] Verify RacerVerification works
8. [ ] Verify Notifications work
9. [ ] Verify no data loss or corruption
10. [ ] Verify queries perform correctly

## Phase 8: Cleanup & Documentation

### 8.1 Remove Deprecated Code

**Duration**: 2-3 days
**Risk**: Medium

**Note**: Only after confirmation that migration is successful and stable.

**Tasks**:

1. [ ] Remove deprecated model imports (after 1 release cycle)
2. [ ] Remove deprecated service imports
3. [ ] Remove deprecated repository imports
4. [ ] Update all remaining imports in codebase
5. [ ] Remove old page/view/dialog files
6. [ ] Remove old API route files
7. [ ] Clean up `models/__init__.py`
8. [ ] Clean up `application/services/__init__.py`
9. [ ] Remove backwards compatibility wrappers

**Verification**:
```bash
# Search for deprecated imports
grep -r "from models.match_schedule" .
grep -r "from application.services.tournaments" .
# Should return no results
```

### 8.2 Remove Feature Flag System

**Duration**: 1-2 days
**Risk**: Low

Replace the feature flag system with plugin enablement:

**Tasks**:

1. [ ] Migrate feature flag data to plugin enablement records
2. [ ] Update UI to use plugin enablement instead of feature flags
3. [ ] Remove `OrganizationFeatureFlag` model
4. [ ] Remove `FeatureFlagService`
5. [ ] Remove feature flag API routes
6. [ ] Update documentation to reference plugin enablement
7. [ ] Remove feature flag migration files (keep in archive)

**Migration Script**:

```python
# Migrate feature flags to plugin enablement
async def migrate_feature_flags():
    """Convert feature flags to plugin enablement."""
    from models import OrganizationFeatureFlag, FeatureFlag
    from application.plugins import PluginRegistry
    
    # Mapping from feature flags to plugins
    flag_to_plugin = {
        FeatureFlag.LIVE_RACES: 'racetime',
        FeatureFlag.RACETIME_BOT: 'racetime',
        FeatureFlag.DISCORD_EVENTS: 'discord_events',
        FeatureFlag.ADVANCED_PRESETS: 'presets',
        FeatureFlag.SCHEDULED_TASKS: None,   # Core feature, always enabled
    }
    
    flags = await OrganizationFeatureFlag.all()
    for flag in flags:
        plugin_id = flag_to_plugin.get(flag.feature_key)
        if plugin_id:
            await PluginRegistry.set_enabled(
                plugin_id=plugin_id,
                organization_id=flag.organization_id,
                enabled=flag.enabled,
                enabled_by_id=flag.enabled_by_id
            )
```

### 8.3 Update Documentation

**Duration**: 2-3 days
**Risk**: Low

**Tasks**:

1. [ ] Update `docs/ARCHITECTURE.md`
2. [ ] Update `docs/ADDING_FEATURES.md`
3. [ ] Update `docs/PATTERNS.md`
4. [ ] Create `docs/plugins/PLUGIN_DEVELOPMENT.md`
5. [ ] Create `docs/plugins/TOURNAMENT_PLUGIN.md`
6. [ ] Create `docs/plugins/ASYNC_QUALIFIER_PLUGIN.md`
7. [ ] Create `docs/plugins/RANDOMIZER_PLUGINS.md`
8. [ ] Create `docs/plugins/INTEGRATION_PLUGINS.md`
9. [ ] Create `docs/plugins/UTILITY_PLUGINS.md`
10. [ ] Remove feature flag documentation
11. [ ] Update Copilot instructions
12. [ ] Update README.md

### 8.4 Update Copilot Instructions

**Duration**: 1 day
**Risk**: Low

Update `.github/copilot-instructions.md` with plugin architecture:

**Tasks**:

1. [ ] Add plugin architecture overview
2. [ ] Add plugin development guidelines
3. [ ] Add randomizer plugin development guidelines
4. [ ] Add integration plugin guidelines
5. [ ] Update file organization section
6. [ ] Update import conventions
7. [ ] Remove feature flag references

## Rollback Plan

### Phase Rollback Procedures

Each phase can be rolled back independently:

#### Phase 1 Rollback (Core Infrastructure)

```bash
# Revert migration
poetry run aerich downgrade

# Remove plugin files
rm -rf application/plugins/
rm -rf plugins/

# Revert main.py changes
git checkout main.py
```

#### Phase 2 Rollback (Tournament Plugin)

```bash
# Remove plugin
rm -rf plugins/builtin/tournament/

# Restore original files
git checkout models/match_schedule.py
git checkout application/services/tournaments/
# etc.

# Update imports
# (reverting deprecated wrappers)
```

#### Phase 3 Rollback (AsyncQualifier Plugin)

```bash
# Same process as Phase 2
rm -rf plugins/builtin/async_qualifier/
git checkout models/async_tournament.py
# etc.
```

## Risk Mitigation

### High-Risk Areas

1. **Model Migration**: Potential for data access issues
   - **Mitigation**: Backwards-compatible wrappers, extensive testing

2. **Import Path Changes**: Breaking changes for external code
   - **Mitigation**: Deprecation warnings, transition period

3. **Event System Changes**: Event handlers might break
   - **Mitigation**: Keep events in core until Phase 5

4. **Performance Regression**: Plugin loading overhead
   - **Mitigation**: Performance benchmarks, optimization

### Monitoring During Migration

1. **Error Rate**: Monitor for increased errors
2. **Latency**: Monitor for increased response times
3. **Memory**: Monitor for increased memory usage
4. **Logs**: Watch for deprecation warnings or errors

## Success Criteria

### Phase 1 Complete

- [ ] Plugin core infrastructure working
- [ ] Plugin database models created
- [ ] Admin UI for plugin management
- [ ] All existing tests pass

### Phase 2 Complete

- [ ] Tournament plugin loads successfully
- [ ] All Tournament features work identically
- [ ] Backwards compatibility maintained
- [ ] No performance regression

### Phase 3 Complete

- [ ] AsyncQualifier plugin loads successfully
- [ ] All AsyncQualifier features work identically
- [ ] Backwards compatibility maintained
- [ ] No performance regression

### Phase 4 Complete

- [ ] All integration tests pass
- [ ] Performance benchmarks acceptable
- [ ] No data loss or corruption

### Phase 5 Complete

- [ ] Deprecated code removed
- [ ] Documentation updated
- [ ] Copilot instructions updated

## Next Steps

- Review **PLUGIN_IMPLEMENTATION_GUIDE.md** for development patterns
- Review **PLUGIN_SECURITY_MODEL.md** for security considerations

---

**Last Updated**: November 30, 2025
