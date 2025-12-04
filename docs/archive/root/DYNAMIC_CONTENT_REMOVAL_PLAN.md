# Dynamic Content Removal Plan

## Overview
This document tracks the refactoring effort to remove dynamic content loading from all pages and convert each view into its own dedicated page route.

## Status: In Progress

## Completed

### ✅ pages/user_profile.py
**Pattern**: Separate page for each profile section
- `/profile` → Profile Info
- `/profile/settings` → Profile Settings  
- `/profile/api-keys` → API Keys
- `/profile/organizations` → Organizations
- `/profile/racetime` → RaceTime Account
- `/profile/twitch` → Twitch Account
- `/profile/preset-namespaces` → Preset Namespaces
- `/profile/notifications` → Notifications
- `/profile/racer-verification` → Racer Verification

**Helper**: `_create_profile_sidebar(base, active)` - creates sidebar with active highlighting

### ✅ pages/tournament_admin.py
**Pattern**: Separate page for each tournament admin section
- `/org/{org_id}/tournament/{tournament_id}/admin` → Overview
- `/org/{org_id}/tournament/{tournament_id}/admin/players` → Players
- `/org/{org_id}/tournament/{tournament_id}/admin/racetime` → RaceTime Settings
- `/org/{org_id}/tournament/{tournament_id}/admin/discord-events` → Discord Events
- `/org/{org_id}/tournament/{tournament_id}/admin/randomizer-settings` → Randomizer Settings
- `/org/{org_id}/tournament/{tournament_id}/admin/preset-rules` → Preset Selection Rules
- `/org/{org_id}/tournament/{tournament_id}/admin/settings` → Settings

**Helpers**: 
- `_create_tournament_sidebar(base, org_id, tournament_id, active)` - creates sidebar with active highlighting
- `_get_tournament_context(organization_id, tournament_id)` - shared authorization and data loading

## Remaining Work

### 🔄 pages/organization_admin.py
**Views to Convert** (12 pages):
1. Overview
2. Members
3. Permissions
4. Settings
5. Tournaments
6. Async Qualifiers
7. Stream Channels
8. Scheduled Tasks
9. Discord Servers
10. Race Room Profiles
11. Racer Verification
12. Audit Logs

**Pattern**:
- `/orgs/{org_id}/admin` → Overview
- `/orgs/{org_id}/admin/members` → Members
- `/orgs/{org_id}/admin/permissions` → Permissions
- etc.

**Helpers Needed**:
- `_create_org_sidebar(base, org_id, active, can_admin, can_manage_tournaments)` - conditional based on permissions
- `_get_org_context(organization_id)` - shared authorization and data loading

### 🔄 pages/admin.py
**Views to Convert** (11 pages):
1. Overview
2. Users
3. Organizations
4. Org Requests
5. RaceTime Bots
6. Presets
7. Namespaces
8. Scheduled Tasks
9. Audit Logs
10. Application Logs
11. Settings

**Pattern**:
- `/admin` → Overview
- `/admin/users` → Users
- `/admin/organizations` → Organizations
- etc.

**Helper Needed**:
- `_create_admin_sidebar(base, active)` - creates sidebar with active highlighting

### 🔄 pages/tournaments.py
**Current State**: Minimal dynamic content (only overview view)

**Action**: Simplify to single page at `/org/{org_id}` with OrganizationOverviewView

## Changes to BasePage

### Methods to Remove
The following methods in `components/base_page.py` will be removed:

1. `use_dynamic_content` parameter in `render()` method
2. `_dynamic_content_container` instance variable
3. `get_dynamic_content_container()` method
4. `register_content_loader()` method
5. `load_view_into_container()` method
6. `create_instance_view_loader()` method
7. `register_instance_view()` method
8. `register_multiple_views()` method
9. `create_sidebar_item_with_loader()` method (replace with `create_nav_link` only)
10. `create_sidebar_items()` method (no longer needed with simple nav links)
11. `view` parameter in `authenticated_page()` and other factory methods
12. `initial_view` property

### Methods to Keep/Update
1. `create_nav_link()` - Already supports `active` parameter for highlighting
2. `create_separator()` - No changes needed
3. `render()` - Remove `use_dynamic_content` parameter, simplify implementation

## Documentation Updates

### docs/core/BASEPAGE_GUIDE.md
- Remove all sections about dynamic content loading
- Remove sections about `register_content_loader`, `load_view_into_container`, etc.
- Update examples to show only simple page patterns
- Remove "Dynamic Content & View Management" section entirely

### docs/PATTERNS.md
- Update page structure examples to remove dynamic content
- Show new pattern of separate pages for each view

### docs/ADDING_FEATURES.md
- Update "New Page" section to reflect simplified pattern
- Remove references to dynamic content loading

## Migration Pattern

For each page module refactoring, follow this pattern:

```python
# 1. Create sidebar helper function
def _create_SECTION_sidebar(base: BasePage, ..., active: str):
    """Create common sidebar for SECTION pages."""
    sidebar_items = [
        base.create_nav_link("Label", "icon", "/path", active=(active == "key")),
        # ... more items
    ]
    return sidebar_items

# 2. Create context helper (if needed for auth/data loading)
async def _get_SECTION_context(...):
    """Get data and check permissions."""
    # Auth checks
    # Data loading
    # Return tuple: (data..., error_message or None)

# 3. Register individual pages
def register():
    """Register SECTION page routes."""
    
    @ui.page("/path")
    async def page_name():
        """Page description."""
        base = BasePage.authenticated_page(title="Title")
        
        async def content(page: BasePage):
            """Render content."""
            # Get context if needed
            # Handle errors
            # Render view
            view = SomeView(...)
            await view.render()
        
        sidebar_items = _create_SECTION_sidebar(base, ..., "active_key")
        await base.render(content, sidebar_items)
    
    # ... more pages
```

## Benefits of This Refactoring

1. **Simpler Architecture**: No complex dynamic content loading system
2. **Better URLs**: Each view has its own dedicated URL
3. **Easier Testing**: Each page can be tested independently
4. **Better Browser History**: Back/forward buttons work intuitively
5. **Clearer Code**: Less indirection, easier to understand
6. **Better Performance**: No need to load/unload views dynamically
7. **Easier Debugging**: Stack traces point to specific pages
8. **Better SEO**: Each page has its own URL (if that matters in the future)

## Breaking Changes

### User-Facing
- URLs change from `/profile/{view}` to `/profile/{section}`
- Bookmarks with old URLs will no longer work
- Browser back button may behave slightly differently

### Developer-Facing
- `BasePage` API changes (removed methods)
- Page registration patterns change
- Sidebar creation patterns change
- No more dynamic view switching within a page

## Testing Plan

1. **Manual Testing**: Navigate to all new page routes and verify:
   - Content loads correctly
   - Sidebar highlights active page
   - Authorization checks work
   - Error handling works

2. **Integration Tests**: Update any tests that rely on dynamic content loading

3. **URL Migration**: Check if any links in code/docs point to old URL patterns

## Timeline

- ✅ Phase 1: user_profile.py (Completed)
- ✅ Phase 2: tournament_admin.py (Completed)
- 🔄 Phase 3: organization_admin.py (In Progress)
- ⏳ Phase 4: admin.py
- ⏳ Phase 5: tournaments.py
- ⏳ Phase 6: Remove BasePage dynamic content methods
- ⏳ Phase 7: Update documentation

## Notes

- Keep backward compatibility where possible (e.g., old URLs could redirect)
- Consider adding a migration guide for any external links
- Update any API documentation that references these URLs
- Check Discord bot commands for any hard-coded URLs
