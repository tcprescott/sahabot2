# Plugin Migration Plan

## Executive Summary

This document provides a detailed step-by-step plan for migrating the Tournament and AsyncQualifier systems to the plugin architecture. The migration is designed to be incremental, backwards-compatible, and reversible at each phase.

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
| Phase 4 | Integration & Testing | 1-2 weeks | Low |
| Phase 5 | Cleanup & Documentation | 1 week | Low |

**Total Estimated Duration**: 8-11 weeks

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

## Phase 4: Integration & Testing

### 4.1 Integration Testing

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

### 4.2 Performance Testing

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

### 4.3 Migration Data Verification

**Duration**: 1 day
**Risk**: Low

Verify all data accessible through plugins:

**Tasks**:

1. [ ] Verify existing Tournament data accessible
2. [ ] Verify existing AsyncQualifier data accessible
3. [ ] Verify no data loss or corruption
4. [ ] Verify queries perform correctly

## Phase 5: Cleanup & Documentation

### 5.1 Remove Deprecated Code

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

**Verification**:
```bash
# Search for deprecated imports
grep -r "from models.match_schedule" .
grep -r "from application.services.tournaments" .
# Should return no results (except in deprecation warnings)
```

### 5.2 Update Documentation

**Duration**: 2-3 days
**Risk**: Low

**Tasks**:

1. [ ] Update `docs/ARCHITECTURE.md`
2. [ ] Update `docs/ADDING_FEATURES.md`
3. [ ] Update `docs/PATTERNS.md`
4. [ ] Create `docs/plugins/PLUGIN_DEVELOPMENT.md`
5. [ ] Create `docs/plugins/TOURNAMENT_PLUGIN.md`
6. [ ] Create `docs/plugins/ASYNC_QUALIFIER_PLUGIN.md`
7. [ ] Update Copilot instructions
8. [ ] Update README.md

### 5.3 Update Copilot Instructions

**Duration**: 1 day
**Risk**: Low

Update `.github/copilot-instructions.md` with plugin architecture:

**Tasks**:

1. [ ] Add plugin architecture overview
2. [ ] Add plugin development guidelines
3. [ ] Update file organization section
4. [ ] Update import conventions

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
