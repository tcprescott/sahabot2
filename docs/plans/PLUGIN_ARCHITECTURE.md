# Plugin Architecture for SahaBot2

## Executive Summary

This document describes a comprehensive plugin architecture for SahaBot2 that will transform the Tournament and AsyncQualifier systems into modular, extensible plugins. The architecture enables:

- **Built-in Plugins**: Core features (Tournament, AsyncQualifier) that ship with the application
- **External Plugins**: Third-party or community-developed extensions
- **Per-Organization Enablement**: Plugins can be enabled/disabled per organization
- **Full Feature Contribution**: Plugins can add models, services, pages, API routes, Discord commands, events, and scheduled tasks

## Current State Analysis

### Existing Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                                │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────────────────┐  │
│  │   UI Pages    │ │  API Routes   │ │   Discord Bot Commands    │  │
│  │   (NiceGUI)   │ │   (FastAPI)   │ │      (discord.py)         │  │
│  └───────┬───────┘ └───────┬───────┘ └─────────────┬─────────────┘  │
├──────────┼─────────────────┼───────────────────────┼────────────────┤
│          ▼                 ▼                       ▼                 │
│                      Service Layer                                   │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ tournament_service.py │ async_qualifier_service.py │ ...      │  │
│  └───────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────┤
│                     Repository Layer                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ tournament_repository.py │ async_qualifier_repository.py │... │  │
│  └───────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────┤
│                      Model Layer                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ match_schedule.py │ async_tournament.py │ user.py │ ...       │  │
│  └───────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### Current Integration Points

| Component | Tournament System | AsyncQualifier System |
|-----------|------------------|----------------------|
| **Models** | `models/match_schedule.py` | `models/async_tournament.py` |
| **Services** | `application/services/tournaments/` | `application/services/async_qualifiers/` |
| **Repositories** | `tournament_repository.py` | `async_qualifier_repository.py` |
| **Pages** | `pages/tournaments.py`, `pages/tournament_admin.py` | `pages/async_qualifiers.py`, `pages/async_qualifier_admin.py` |
| **Views** | `views/tournaments/`, `views/tournament_admin/` | `views/async_qualifiers/` |
| **Dialogs** | `components/dialogs/tournaments/` | `components/dialogs/async_qualifiers/` |
| **API Routes** | `api/routes/tournaments.py` | `api/routes/async_qualifiers.py` |
| **Discord Commands** | - | `discordbot/commands/async_qualifier.py` |
| **Events** | Tournament events in `types.py` | Race events in `types.py` |
| **Tasks** | SpeedGaming sync task | Score calculation task |

## Proposed Plugin Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Plugin Management Layer                               │
│  ┌────────────────────┐  ┌────────────────────┐  ┌───────────────────────┐   │
│  │  Plugin Registry   │  │  Plugin Lifecycle  │  │  Plugin Configuration │   │
│  │    (Discovery)     │  │     Manager        │  │      Manager          │   │
│  └────────┬───────────┘  └────────┬───────────┘  └───────────┬───────────┘   │
├───────────┼────────────────────────┼──────────────────────────┼──────────────┤
│           ▼                        ▼                          ▼              │
│                          Plugin Integration Layer                             │
│  ┌───────────────┐  ┌──────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Model Loader  │  │ Route Loader │  │ Command Loader│  │ Event Loader  │   │
│  └───────────────┘  └──────────────┘  └───────────────┘  └───────────────┘   │
├──────────────────────────────────────────────────────────────────────────────┤
│                              Plugins                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                        Built-in Plugins                                 │  │
│  │  ┌─────────────────────┐  ┌──────────────────────────┐                 │  │
│  │  │ Tournament Plugin   │  │ AsyncQualifier Plugin    │                 │  │
│  │  │ (built-in, default) │  │ (built-in, optional)     │                 │  │
│  │  └─────────────────────┘  └──────────────────────────┘                 │  │
│  ├────────────────────────────────────────────────────────────────────────┤  │
│  │                        External Plugins                                 │  │
│  │  ┌─────────────────────┐  ┌──────────────────────────┐                 │  │
│  │  │ Community Plugin A  │  │ Community Plugin B       │                 │  │
│  │  │ (installable)       │  │ (installable)            │                 │  │
│  │  └─────────────────────┘  └──────────────────────────┘                 │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Core Application                                     │
│                (Authentication, Organizations, Users, Events)                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Plugin Core Package

The plugin core package manages discovery, registration, and lifecycle:

```
application/
└── plugins/
    ├── __init__.py
    ├── registry.py           # Plugin registry singleton
    ├── manifest.py           # Plugin manifest schema
    ├── loader.py             # Plugin loading utilities
    ├── lifecycle.py          # Lifecycle management
    ├── config_service.py     # Plugin configuration service
    ├── exceptions.py         # Plugin-specific exceptions
    └── base/                  # Base classes for plugin development
        ├── __init__.py
        ├── plugin.py          # BasePlugin abstract class
        ├── model_provider.py  # Model contribution interface
        ├── route_provider.py  # API route contribution interface
        ├── page_provider.py   # UI page contribution interface
        ├── command_provider.py # Discord command contribution interface
        ├── event_provider.py  # Event contribution interface
        └── task_provider.py   # Scheduled task contribution interface
```

#### 2. Plugin Storage

Database models and filesystem layout for plugin management.

```
plugins/                     # Filesystem location for external plugins
├── builtin/                 # Built-in plugins (part of codebase)
│   ├── tournament/
│   └── async_qualifier/
└── external/                # Installed external plugins
    └── <plugin_name>/

models/
└── plugin.py               # Plugin database models
```

### Plugin Types

#### Built-in Plugins

- **Location**: `plugins/builtin/`
- **Management**: Part of codebase, version-controlled
- **Installation**: Cannot be uninstalled
- **Updates**: Updated with application updates
- **Enablement**: Can be disabled per-organization

**Planned Built-in Plugins**:

| Plugin | Category | Description | Key Features |
|--------|----------|-------------|--------------|
| **DiscordBot** | Global | Core Discord bot infrastructure | Bot lifecycle, command loading, presence, error handling |
| **Tournament** | Competition | Live tournament management | Matches, scheduling, crew signups |
| **AsyncQualifier** | Competition | Asynchronous qualifier races | Pools, permalinks, scoring, leaderboards |
| **Presets** | Core | Preset management system | Namespaces, preset storage, permissions, sharing |
| **RaceTime** | Integration | RaceTime.gg integration | Bot management, room profiles, race handlers |
| **SpeedGaming** | Integration | SpeedGaming.org integration | Schedule sync, ETL, match import |
| **DiscordEvents** | Integration | Discord scheduled events | Event creation, match linking, status sync |
| **RacerVerification** | Utility | Discord role verification | Race count requirements, role granting |
| **Notifications** | Utility | Event notifications | Discord DM, subscriptions, delivery |
| **ALTTPR** | Randomizer | A Link to the Past Randomizer | Seed generation, ALTTPR-specific presets, mystery |
| **SM** | Randomizer | Super Metroid Randomizer | VARIA/DASH support, SM-specific presets |
| **SMZ3** | Randomizer | Super Metroid + ALTTP Combo | Combined randomizer, SMZ3-specific presets |
| **OOTR** | Randomizer | Ocarina of Time Randomizer | API integration, OOTR-specific presets |
| **AOSR** | Randomizer | Aria of Sorrow Randomizer | Enemy/room randomization, AOSR presets |
| **Z1R** | Randomizer | Zelda 1 Randomizer | Flag-based configuration, Z1R presets |
| **FFR** | Randomizer | Final Fantasy Randomizer | Flag-based seed generation, FFR presets |
| **SMB3R** | Randomizer | Super Mario Bros 3 Randomizer | Seed generation, SMB3R presets |
| **CTJets** | Randomizer | Chrono Trigger Jets of Time | Settings-based generation, CTJets presets |
| **Bingosync** | Utility | Bingo card generation | Room creation, game type support |

**Plugin Dependencies**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Plugin Dependency Graph                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Global Plugins (always enabled, no organization scope):                 │
│    - DiscordBot ─── required by all Discord-dependent plugins            │
│                                                                          │
│  Core Plugins (no dependencies):                                         │
│    - Presets                                                             │
│    - Notifications ─── requires: DiscordBot (for DM delivery)            │
│    - Bingosync                                                           │
│                                                                          │
│  Integration Plugins:                                                    │
│    - RaceTime (no deps)                                                  │
│    - SpeedGaming (no deps)                                               │
│    - DiscordEvents ─── requires: DiscordBot                              │
│    - RacerVerification ─── requires: RaceTime, DiscordBot                │
│                                                                          │
│  Competition Plugins:                                                    │
│    - Tournament ─────────── requires: RaceTime (optional)                │
│    - AsyncQualifier ──────── requires: RaceTime, Presets                 │
│                                                                          │
│  Randomizer Plugins:                                                     │
│    - ALTTPR  ──┐                                                         │
│    - SM      ──┼── requires: Presets                                     │
│    - SMZ3    ──┤   optional: RaceTime (for race handlers)                │
│    - OOTR    ──┤   optional: DiscordBot (for Discord commands)           │
│    - AOSR    ──┤                                                         │
│    - Z1R     ──┤                                                         │
│    - FFR     ──┤                                                         │
│    - SMB3R   ──┤                                                         │
│    - CTJets  ──┘                                                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Plugin Descriptions

#### Global Plugins

**DiscordBot Plugin** provides:
- Discord bot client singleton (`DiscordBot` class)
- Bot lifecycle management (start, stop, ready detection)
- Command tree and cog loading infrastructure
- Command syncing with Discord API
- Error handling and Sentry integration
- Bot presence management

The DiscordBot plugin is **global** (not organization-scoped) and is always enabled. Other plugins that need Discord functionality depend on this plugin.

#### Core Plugins

**Presets Plugin** provides:
- `PresetNamespace` model and repository
- `Preset` base model (without randomizer-specific fields)
- Preset CRUD services
- Preset sharing and permissions
- Namespace management

**Notifications Plugin** provides:
- `NotificationSubscription` model
- `NotificationLog` model
- Notification delivery (Discord DM, future: email, webhooks)
- Subscription management UI
- Event-to-notification mapping

#### Integration Plugins

**RaceTime Plugin** provides:
- `RacetimeBot`, `RacetimeBotOrganization` models
- `RacetimeRoom`, `RaceRoomProfile` models
- RaceTime API client service
- Bot lifecycle management
- Race room profile management
- Base race handler infrastructure

**SpeedGaming Plugin** provides:
- SpeedGaming API client
- Schedule ETL (Extract, Transform, Load)
- Match import from SpeedGaming.org
- Sync task for schedule updates

**DiscordEvents Plugin** provides:
- `DiscordScheduledEvent` model
- Discord API integration for events
- Match-to-event linking
- Event status synchronization
- Orphaned event cleanup task

**RacerVerification Plugin** provides:
- `RacerVerification`, `UserRacerVerification` models
- RaceTime race count verification
- Discord role granting
- Verification requirements configuration

#### Competition Plugins

**Tournament Plugin** (existing) extends with:
- Optional RaceTime integration for live rooms
- Optional SpeedGaming integration for schedule sync
- Optional DiscordEvents integration for event creation

**AsyncQualifier Plugin** (existing) extends with:
- Required Presets integration for preset selection
- Required RaceTime integration for live races

#### Randomizer Plugins

Each **Randomizer Plugin**:
- Depends on the Presets plugin
- Extends preset functionality with randomizer-specific validation
- Provides seed generation service
- Optionally provides RaceTime.gg race handlers
- Provides Discord commands for seed generation
- Provides API endpoints for external integrations

#### External Plugins

- **Location**: `plugins/external/`
- **Management**: Installed via admin panel or CLI
- **Installation**: Can be installed/uninstalled
- **Updates**: Independent update cycle
- **Enablement**: Can be enabled/disabled per-organization
- **Trust**: All plugins are trusted by default (no sandboxing)
- **Examples**: Community-developed plugins

### Feature Flag Replacement

The plugin enablement system replaces the existing `OrganizationFeatureFlag` system. This provides several advantages:

1. **Unified Model**: One system for both features and extensions
2. **Extensibility**: Plugins can contribute more than just a toggle
3. **Configuration**: Plugins can have organization-specific configuration
4. **Lifecycle**: Plugins have proper lifecycle hooks (enable/disable/upgrade)

**Migration**: See [PLUGIN_MIGRATION_PLAN.md](PLUGIN_MIGRATION_PLAN.md#62-remove-feature-flag-system) for the detailed feature flag to plugin mapping.

### Organization-Level Control

Organizations can enable/disable plugins based on their needs. For example, an ALTTPR community may only enable ALTTPR and SMZ3 randomizers, while a speedrunning community might enable all randomizers.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Organization: ALTTPR Community               │
├─────────────────────────────────────────────────────────────────┤
│  Plugin                 │  Status    │  Configuration           │
├─────────────────────────┼────────────┼──────────────────────────┤
│  Tournament (built-in)  │  Enabled   │  [Settings...]           │
│  AsyncQualifier (b-i)   │  Enabled   │  [Settings...]           │
│  ALTTPR (built-in)      │  Enabled   │  [Presets, Mystery...]   │
│  SMZ3 (built-in)        │  Enabled   │  [Presets...]            │
│  OOTR (built-in)        │  Disabled  │  -                       │
│  SM (built-in)          │  Disabled  │  -                       │
│  FFR (built-in)         │  Disabled  │  -                       │
│  Custom Tracker (ext)   │  Enabled   │  [Settings...]           │
└─────────────────────────────────────────────────────────────────┘
```

## Plugin Structure

### Directory Layout (Built-in Example)

```
plugins/builtin/tournament/
├── manifest.yaml              # Plugin metadata
├── __init__.py                # Plugin entry point
├── plugin.py                  # TournamentPlugin class
├── models/                    # Database models
│   ├── __init__.py
│   └── tournament.py          # Tournament, Match, etc.
├── services/                  # Business logic
│   ├── __init__.py
│   └── tournament_service.py
├── repositories/              # Data access
│   ├── __init__.py
│   └── tournament_repository.py
├── pages/                     # NiceGUI pages
│   ├── __init__.py
│   ├── tournaments.py
│   └── tournament_admin.py
├── views/                     # Page views
│   ├── __init__.py
│   └── ...
├── dialogs/                   # UI dialogs
│   ├── __init__.py
│   └── ...
├── api/                       # FastAPI routes
│   ├── __init__.py
│   └── routes.py
├── commands/                  # Discord commands
│   ├── __init__.py
│   └── tournament_commands.py
├── events/                    # Event types and listeners
│   ├── __init__.py
│   ├── types.py
│   └── listeners.py
├── tasks/                     # Scheduled tasks
│   ├── __init__.py
│   └── sync_tasks.py
└── migrations/                # Plugin-specific migrations
    └── 001_initial.py
```

### Manifest Schema (manifest.yaml)

```yaml
# Plugin manifest
id: tournament
name: Tournament System
version: 1.0.0
description: Live tournament management with RaceTime.gg integration
author: SahaBot2 Team
website: https://github.com/sahabot2

# Plugin classification
type: builtin  # or "external"
category: competition  # competition, integration, utility, etc.

# Organization defaults
enabled_by_default: true  # Whether plugin is enabled for new organizations
private: false            # If true, requires global admin to grant org access

# Dependencies
requires:
  sahabot2: ">=1.0.0"
  python: ">=3.11"
  plugins: []  # Other plugin dependencies

# Feature contributions
provides:
  models:
    - Tournament
    - Match
    - MatchPlayers
    - TournamentPlayers
    - Crew
    - StreamChannel
    - MatchSeed

  pages:
    - path: /org/{org_id}/tournaments
      name: Tournament List
    - path: /org/{org_id}/tournaments/{tournament_id}
      name: Tournament Detail
    - path: /org/{org_id}/tournament-admin
      name: Tournament Admin

  api_routes:
    prefix: /tournaments
    tags: [tournaments, matches]

  discord_commands:
    - name: tournament
      description: Tournament management commands

  events:
    - TournamentCreatedEvent
    - TournamentUpdatedEvent
    - MatchScheduledEvent
    - MatchFinishedEvent

  tasks:
    - speedgaming_sync
    - auto_room_creation

# Permissions required
permissions:
  actions:
    - tournament:create
    - tournament:read
    - tournament:update
    - tournament:delete
    - match:create
    - match:update
    - match:read

# Feature flags (for gradual rollout)
feature_flags:
  - RACETIME_BOT
  - DISCORD_EVENTS

# Configuration schema
config_schema:
  type: object
  properties:
    enable_racetime:
      type: boolean
      default: true
    enable_speedgaming:
      type: boolean
      default: false
```

## Integration Points

### 1. Model Integration

Plugins contribute models that are loaded dynamically at startup.

```
┌─────────────────────────────────────────────────────────────┐
│                    Tortoise ORM Init                         │
│                                                              │
│  1. Load core models (models/*.py)                          │
│  2. Discover plugins with models                             │
│  3. Load plugin models dynamically                           │
│  4. Register all models with Tortoise                        │
│  5. Run migrations (core + plugin)                           │
└─────────────────────────────────────────────────────────────┘
```

### 2. Page Integration

Plugins register NiceGUI pages through the page provider interface.

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Init                             │
│                                                              │
│  1. frontend.py calls register_routes()                      │
│  2. PluginRegistry.register_pages() called                   │
│  3. Each enabled plugin's pages registered                   │
│  4. Plugin pages scoped to organization                      │
└─────────────────────────────────────────────────────────────┘
```

### 3. API Route Integration

Plugins contribute FastAPI routers that are mounted dynamically.

```
┌─────────────────────────────────────────────────────────────┐
│                    API Init                                  │
│                                                              │
│  1. api/__init__.py calls register_api()                     │
│  2. auto_register_routes() discovers core routes             │
│  3. PluginRegistry.register_api_routes() called              │
│  4. Plugin routers mounted under /api/plugins/<plugin_id>/   │
└─────────────────────────────────────────────────────────────┘
```

### 4. Discord Command Integration

Plugins contribute Discord cogs/extensions.

```
┌─────────────────────────────────────────────────────────────┐
│                    Discord Bot Init                          │
│                                                              │
│  1. discordbot/client.py setup_hook()                        │
│  2. Load core extensions                                     │
│  3. PluginRegistry.register_commands() called                │
│  4. Plugin cogs loaded via load_extension()                  │
└─────────────────────────────────────────────────────────────┘
```

### 5. Event Integration

Plugins can emit and listen to events through the EventBus.

```
┌─────────────────────────────────────────────────────────────┐
│                    Event System                              │
│                                                              │
│  1. Plugin defines event types in events/types.py            │
│  2. Plugin defines listeners in events/listeners.py          │
│  3. PluginRegistry.register_events() called at startup       │
│  4. Event types registered with EventBus                     │
│  5. Listeners registered with @EventBus.on()                 │
└─────────────────────────────────────────────────────────────┘
```

### 6. Task Integration

Plugins can define scheduled tasks (built-in or database-stored).

```
┌─────────────────────────────────────────────────────────────┐
│                    Task Scheduler                            │
│                                                              │
│  1. Plugin defines tasks in tasks/                           │
│  2. PluginRegistry.register_tasks() called                   │
│  3. Tasks added to BuiltInTask registry                      │
│  4. TaskSchedulerService picks up plugin tasks               │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema Changes

### New Tables

```sql
-- Plugin installation records
CREATE TABLE plugins (
    id INT PRIMARY KEY AUTO_INCREMENT,
    plugin_id VARCHAR(100) UNIQUE NOT NULL,  -- e.g., "tournament"
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    type ENUM('builtin', 'external') NOT NULL,
    is_installed BOOLEAN DEFAULT TRUE,
    enabled_by_default BOOLEAN DEFAULT TRUE,  -- Default state for new organizations
    private BOOLEAN DEFAULT FALSE,            -- Requires admin to grant org access
    installed_at DATETIME,
    installed_by_id INT REFERENCES users(id),
    config JSON,  -- Plugin-specific configuration
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Organization-level plugin enablement
CREATE TABLE organization_plugins (
    id INT PRIMARY KEY AUTO_INCREMENT,
    organization_id INT NOT NULL REFERENCES organizations(id),
    plugin_id VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    has_access BOOLEAN DEFAULT TRUE,          -- For private plugins, admin must grant access
    access_granted_at DATETIME,               -- When access was granted
    access_granted_by_id INT REFERENCES users(id),  -- Global admin who granted access
    enabled_at DATETIME,
    enabled_by_id INT REFERENCES users(id),
    config JSON,  -- Organization-specific plugin config overrides
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE (organization_id, plugin_id)
);

-- Plugin migration tracking (separate from core Aerich)
CREATE TABLE plugin_migrations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    plugin_id VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    migration_name VARCHAR(255) NOT NULL,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    UNIQUE (plugin_id, migration_name)
);
```

### Model Changes

```python
# models/plugin.py

from tortoise import fields
from tortoise.models import Model

class Plugin(Model):
    """Plugin installation record."""
    id = fields.IntField(pk=True)
    plugin_id = fields.CharField(max_length=100, unique=True)
    name = fields.CharField(max_length=255)
    version = fields.CharField(max_length=50)
    type = fields.CharEnumField(PluginType)  # builtin, external
    is_installed = fields.BooleanField(default=True)
    enabled_by_default = fields.BooleanField(default=True)  # Default for new orgs
    private = fields.BooleanField(default=False)  # Requires admin to grant access
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
    has_access = fields.BooleanField(default=True)  # For private plugins
    access_granted_at = fields.DatetimeField(null=True)
    access_granted_by = fields.ForeignKeyField(
        "models.User", null=True, related_name="granted_plugin_access"
    )
    enabled_at = fields.DatetimeField(null=True)
    enabled_by = fields.ForeignKeyField("models.User", null=True)
    config = fields.JSONField(null=True)  # Overrides
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "organization_plugins"
        unique_together = (("organization", "plugin_id"),)
```

## Plugin Access Control

### Default Enablement

When a new organization is created, the system automatically creates `OrganizationPlugin` records for all installed plugins:

```python
async def initialize_org_plugins(organization_id: int):
    """Initialize plugin records for a new organization."""
    plugins = await Plugin.filter(is_installed=True).all()
    
    for plugin in plugins:
        # Skip private plugins - they need explicit admin access grant
        if plugin.private:
            continue
            
        await OrganizationPlugin.create(
            organization_id=organization_id,
            plugin_id=plugin.plugin_id,
            enabled=plugin.enabled_by_default,
            has_access=True,  # Non-private plugins have access by default
        )
```

### Private Plugin Access

Private plugins require a global admin (SUPERADMIN) to grant access:

```python
async def grant_plugin_access(
    plugin_id: str,
    organization_id: int,
    admin_user: User,
    enable_immediately: bool = False
) -> OrganizationPlugin:
    """Grant organization access to a private plugin (SUPERADMIN only)."""
    if admin_user.permission < Permission.SUPERADMIN:
        raise PermissionError("Only global admins can grant private plugin access")
    
    plugin = await Plugin.get(plugin_id=plugin_id)
    if not plugin.private:
        raise ValueError("Plugin is not private")
    
    org_plugin, created = await OrganizationPlugin.get_or_create(
        organization_id=organization_id,
        plugin_id=plugin_id,
        defaults={
            "has_access": True,
            "access_granted_at": datetime.now(timezone.utc),
            "access_granted_by": admin_user,
            "enabled": enable_immediately,
        }
    )
    
    if not created:
        org_plugin.has_access = True
        org_plugin.access_granted_at = datetime.now(timezone.utc)
        org_plugin.access_granted_by = admin_user
        if enable_immediately:
            org_plugin.enabled = True
        await org_plugin.save()
    
    return org_plugin
```

### Plugin Visibility Rules

```
┌─────────────────────────────────────────────────────────────────┐
│                     Plugin Visibility Matrix                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Plugin Type    │  Org Admins See?  │  Can Enable?              │
│  ───────────────┼───────────────────┼─────────────────────────  │
│  Public         │  Always           │  Yes                      │
│  Private        │  Only if granted  │  Only if has_access=True  │
│                                                                  │
│  enabled_by_default=true:  Auto-enabled for new orgs            │
│  enabled_by_default=false: Visible but disabled for new orgs    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration Flow

### Plugin Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│              Configuration Priority (highest first)              │
├─────────────────────────────────────────────────────────────────┤
│  1. Organization-specific config (organization_plugins.config)  │
│  2. Plugin installation config (plugins.config)                 │
│  3. Plugin manifest defaults (manifest.yaml)                    │
│  4. Code defaults (in plugin implementation)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Benefits of This Architecture

### For Maintainability

1. **Separation of Concerns**: Each plugin is self-contained
2. **Independent Testing**: Plugins can be tested in isolation
3. **Clear Boundaries**: Well-defined interfaces between plugins and core

### For Extensibility

1. **Third-Party Plugins**: External developers can contribute
2. **Feature Flags**: Plugins can have their own feature flags
3. **Gradual Rollout**: Enable plugins per-organization

### For Operations

1. **Independent Updates**: Plugins can be updated separately
2. **Rollback Support**: Disable plugins without affecting core
3. **Configuration Management**: Per-organization plugin configuration

## Alternatives Considered

### Alternative 1: Microservices

**Pros**: True isolation, independent scaling
**Cons**: Operational complexity, network overhead, distributed transactions
**Decision**: Rejected - overkill for this use case, adds significant complexity

### Alternative 2: Feature Flags Only

**Pros**: Simple implementation
**Cons**: All code still coupled, doesn't support external plugins
**Decision**: Rejected - doesn't meet extensibility requirements

### Alternative 3: Monolithic with Good Modularity

**Pros**: Simple deployment, no runtime loading
**Cons**: Can't add external plugins, all features always deployed
**Decision**: Current state - insufficient for future requirements

### Alternative 4: Plugin Architecture (Selected)

**Pros**: Balance of modularity and simplicity, supports external plugins
**Cons**: Initial implementation effort, migration complexity
**Decision**: Selected - best balance for current and future needs

## Success Metrics

1. **Migration Success**: Tournament and AsyncQualifier work identically after migration
2. **Performance**: No measurable performance degradation
3. **Developer Experience**: Creating a new plugin takes < 1 day
4. **Adoption**: At least 1 external plugin contributed within 6 months

## Next Steps

1. Review **PLUGIN_API_SPECIFICATION.md** for interface contracts
2. Review **PLUGIN_MIGRATION_PLAN.md** for migration steps
3. Review **PLUGIN_IMPLEMENTATION_GUIDE.md** for development guide
4. Review **PLUGIN_SECURITY_MODEL.md** for security considerations

---

**Last Updated**: November 30, 2025
