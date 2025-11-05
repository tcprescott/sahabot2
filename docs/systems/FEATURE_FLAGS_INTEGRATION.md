# Feature Flag Integration Examples

This guide shows how to integrate feature flag checking into existing SahaBot2 code.

## Pattern: Conditional UI Elements

### Before (No Feature Flags)
```python
# pages/organization_admin.py
async def content(page: BasePage):
    with ui.element('div').classes('card'):
        ui.label('Organization Admin').classes('card-title')
        
        # All features always visible
        with ui.tabs() as tabs:
            ui.tab('overview', label='Overview', icon='dashboard')
            ui.tab('members', label='Members', icon='group')
            ui.tab('tournaments', label='Tournaments', icon='emoji_events')
            ui.tab('live_races', label='Live Races', icon='sports_score')  # Always shown
            ui.tab('presets', label='Presets', icon='settings')  # Always shown
            ui.tab('bot', label='RaceTime Bot', icon='smart_toy')  # Always shown
```

### After (With Feature Flags)
```python
# pages/organization_admin.py
from application.utils.feature_flags import is_enabled
from models import FeatureFlag

async def content(page: BasePage):
    with ui.element('div').classes('card'):
        ui.label('Organization Admin').classes('card-title')
        
        # Conditionally show features based on flags
        with ui.tabs() as tabs:
            ui.tab('overview', label='Overview', icon='dashboard')
            ui.tab('members', label='Members', icon='group')
            ui.tab('tournaments', label='Tournaments', icon='emoji_events')
            
            # Only show if feature is enabled
            if await is_enabled(org_id, FeatureFlag.LIVE_RACES):
                ui.tab('live_races', label='Live Races', icon='sports_score')
            
            if await is_enabled(org_id, FeatureFlag.ADVANCED_PRESETS):
                ui.tab('presets', label='Presets', icon='settings')
            
            if await is_enabled(org_id, FeatureFlag.RACETIME_BOT):
                ui.tab('bot', label='RaceTime Bot', icon='smart_toy')
```

## Pattern: Conditional Service Methods

### Before (No Feature Flags)
```python
# application/services/race_service.py
class RaceService:
    async def get_live_races(self, organization_id: int):
        """Get all live races for an organization."""
        # Always returns live races
        return await self.repository.get_live_races(organization_id)
```

### After (With Feature Flags)
```python
# application/services/race_service.py
from application.utils.feature_flags import is_enabled
from models import FeatureFlag

class RaceService:
    async def get_live_races(self, organization_id: int):
        """Get all live races for an organization."""
        # Check if feature is enabled
        if not await is_enabled(organization_id, FeatureFlag.LIVE_RACES):
            logger.info(
                "Live races feature not enabled for organization %s",
                organization_id
            )
            return []  # Return empty list if feature disabled
        
        return await self.repository.get_live_races(organization_id)
```

## Pattern: Conditional API Endpoints

### Before (No Feature Flags)
```python
# api/routes/races.py
@router.get("/organizations/{org_id}/live-races")
async def list_live_races(
    org_id: int,
    current_user: User = Depends(get_current_user)
):
    """List live races for organization."""
    # Always returns data
    service = RaceService()
    races = await service.get_live_races(org_id)
    return {"races": races}
```

### After (With Feature Flags)
```python
# api/routes/races.py
from application.utils.feature_flags import is_enabled
from models import FeatureFlag

@router.get("/organizations/{org_id}/live-races")
async def list_live_races(
    org_id: int,
    current_user: User = Depends(get_current_user)
):
    """List live races for organization."""
    # Check feature flag
    if not await is_enabled(org_id, FeatureFlag.LIVE_RACES):
        raise HTTPException(
            status_code=403,
            detail="Live races feature not enabled for this organization"
        )
    
    service = RaceService()
    races = await service.get_live_races(org_id)
    return {"races": races}
```

## Pattern: Batch Feature Checking

### Efficient Multi-Feature Check
```python
from application.utils.feature_flags import get_enabled_features
from models import FeatureFlag

async def render_organization_dashboard(org_id: int):
    """Render dashboard with only enabled features."""
    # Get all enabled features at once (single DB query)
    enabled = await get_enabled_features(org_id)
    
    # Check multiple features efficiently
    show_live_races = FeatureFlag.LIVE_RACES in enabled
    show_presets = FeatureFlag.ADVANCED_PRESETS in enabled
    show_bot = FeatureFlag.RACETIME_BOT in enabled
    show_tasks = FeatureFlag.SCHEDULED_TASKS in enabled
    
    # Render conditionally
    with ui.element('div').classes('dashboard'):
        # Always show basic features
        await render_overview()
        await render_members()
        
        # Conditional advanced features
        if show_live_races:
            await render_live_races()
        
        if show_presets:
            await render_presets()
        
        if show_bot:
            await render_racetime_bot()
        
        if show_tasks:
            await render_scheduled_tasks()
```

## Pattern: Discord Bot Commands

### Before (No Feature Flags)
```python
# discordbot/commands/races.py
@app_commands.command(name="startrace")
async def start_race(interaction: discord.Interaction):
    """Start a live race."""
    # Always available
    service = RaceService()
    race = await service.create_live_race(guild_id=interaction.guild_id)
    await interaction.response.send_message(f"Race started: {race.name}")
```

### After (With Feature Flags)
```python
# discordbot/commands/races.py
from application.utils.feature_flags import is_enabled
from models import FeatureFlag

@app_commands.command(name="startrace")
async def start_race(interaction: discord.Interaction):
    """Start a live race."""
    # Get organization for this guild
    from application.services.organization_service import OrganizationService
    
    org_service = OrganizationService()
    org = await org_service.get_by_discord_guild_id(interaction.guild_id)
    
    if not org:
        await interaction.response.send_message(
            "This server is not associated with an organization.",
            ephemeral=True
        )
        return
    
    # Check if feature is enabled
    if not await is_enabled(org.id, FeatureFlag.LIVE_RACES):
        await interaction.response.send_message(
            "Live races feature is not enabled for this organization. "
            "Contact a SUPERADMIN to enable it.",
            ephemeral=True
        )
        return
    
    # Feature enabled, proceed
    service = RaceService()
    race = await service.create_live_race(organization_id=org.id)
    await interaction.response.send_message(f"Race started: {race.name}")
```

## Pattern: View Component Conditional Rendering

### Before (No Feature Flags)
```python
# views/organization/org_dashboard.py
class OrgDashboardView:
    async def render(self):
        """Render organization dashboard."""
        with ui.element('div').classes('dashboard'):
            # All widgets always shown
            await self._render_stats()
            await self._render_recent_activity()
            await self._render_live_races()  # Always shown
            await self._render_scheduled_tasks()  # Always shown
```

### After (With Feature Flags)
```python
# views/organization/org_dashboard.py
from application.utils.feature_flags import get_enabled_features, FeatureFlags

class OrgDashboardView:
    def __init__(self, organization_id: int, user):
        self.organization_id = organization_id
        self.user = user
    
    async def render(self):
        """Render organization dashboard."""
        # Get enabled features once
        enabled = await get_enabled_features(self.organization_id)
        
        with ui.element('div').classes('dashboard'):
            # Always show basic widgets
            await self._render_stats()
            await self._render_recent_activity()
            
            # Conditional widgets based on features
            if FeatureFlag.LIVE_RACES in enabled:
                await self._render_live_races()
            
            if FeatureFlag.SCHEDULED_TASKS in enabled:
                await self._render_scheduled_tasks()
```

## Pattern: Feature-Specific Sidebar Items

### Dynamic Navigation Based on Features
```python
# components/sidebar.py
from application.utils.feature_flags import get_enabled_features, FeatureFlags

async def get_org_sidebar_items(organization_id: int) -> list[dict]:
    """Get sidebar items for organization admin page."""
    # Get enabled features
    enabled = await get_enabled_features(organization_id)
    
    # Base items (always shown)
    items = [
        {'label': 'Overview', 'icon': 'dashboard', 'view': 'overview'},
        {'label': 'Members', 'icon': 'group', 'view': 'members'},
        {'label': 'Tournaments', 'icon': 'emoji_events', 'view': 'tournaments'},
    ]
    
    # Conditional items based on features
    if FeatureFlag.LIVE_RACES in enabled:
        items.append({
            'label': 'Live Races',
            'icon': 'sports_score',
            'view': 'live_races'
        })
    
    if FeatureFlag.ADVANCED_PRESETS in enabled:
        items.append({
            'label': 'Presets',
            'icon': 'settings',
            'view': 'presets'
        })
    
    if FeatureFlag.RACETIME_BOT in enabled:
        items.append({
            'label': 'RaceTime Bot',
            'icon': 'smart_toy',
            'view': 'bot'
        })
    
    if FeatureFlag.SCHEDULED_TASKS in enabled:
        items.append({
            'label': 'Tasks',
            'icon': 'schedule',
            'view': 'tasks'
        })
    
    if FeatureFlag.DISCORD_EVENTS in enabled:
        items.append({
            'label': 'Discord Events',
            'icon': 'event',
            'view': 'events'
        })
    
    return items
```

## Best Practices

1. **Check at the Highest Level**: Check feature flags at the UI/API entry point, not deep in business logic
2. **Batch Checks**: Use `get_enabled_features()` when checking multiple flags
3. **Graceful Degradation**: Return empty results or show helpful messages when features are disabled
4. **Clear Messaging**: Tell users when features are disabled and how to enable them
5. **Log Feature Checks**: Log when features are accessed/blocked for monitoring
6. **Cache Results**: For page loads, cache the enabled features list to avoid multiple DB queries

## Anti-Patterns to Avoid

❌ **Don't check in loops**:
```python
# BAD - checks feature flag on every iteration
for race in races:
    if await is_enabled(org_id, FeatureFlag.LIVE_RACES):
        process_race(race)

# GOOD - check once before loop
if await is_enabled(org_id, FeatureFlag.LIVE_RACES):
    for race in races:
        process_race(race)
```

❌ **Don't check same feature multiple times**:
```python
# BAD - multiple checks for same feature
if await is_enabled(org_id, FeatureFlag.LIVE_RACES):
    show_ui()

if await is_enabled(org_id, FeatureFlag.LIVE_RACES):
    show_more_ui()

# GOOD - check once, store result
has_live_races = await is_enabled(org_id, FeatureFlag.LIVE_RACES)
if has_live_races:
    show_ui()
    show_more_ui()
```

❌ **Don't hardcode feature keys**:
```python
# BAD - hardcoded string
if await is_enabled(org_id, 'live_races'):
    ...

# GOOD - use constant
if await is_enabled(org_id, FeatureFlag.LIVE_RACES):
    ...
```

## Migration Example

If migrating existing code, use this pattern:

```python
# Step 1: Add feature flag check with logging
if await is_enabled(org_id, FeatureFlag.LIVE_RACES):
    # Existing code
    await show_live_races()
else:
    logger.info(
        "Live races feature not enabled for org %s - skipping display",
        org_id
    )
```

Then enable the feature for testing:
```python
# In Python console or migration script
from application.services.feature_flag_service import FeatureFlagService, FeatureFlags
from models import User

service = FeatureFlagService()
superadmin = await User.filter(permission=Permission.SUPERADMIN).first()

await service.enable_feature(
    organization_id=1,
    feature_key=FeatureFlag.LIVE_RACES,
    current_user=superadmin,
    notes="Enabled for testing"
)
```

---

**Created**: November 5, 2025
