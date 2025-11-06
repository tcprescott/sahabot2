# UI Component Migration Guide

This guide helps developers migrate existing UI code to use the new shared components: Badge, EmptyState, and StatCard.

## Overview

Three new reusable components have been created to standardize UI patterns across the application:

1. **Badge** - Status indicators, permissions, visibility badges
2. **EmptyState** - Empty list/table displays with consistent messaging
3. **StatCard/StatGrid** - Statistics displays for dashboards and metrics

## Migration Examples

### 1. Badge Component Migration

#### Before (Manual Badge Creation):
```python
# Permission badge
badge_class = (
    'badge-admin' if u.is_admin() else
    'badge-moderator' if u.is_moderator() else
    'badge-user'
)
with ui.element('span').classes(f'badge {badge_class}'):
    ui.label(u.permission.name)

# Status badge
status_class = 'badge-success' if u.is_active else 'badge-danger'
with ui.element('span').classes(f'badge {status_class}'):
    ui.label('Active' if u.is_active else 'Inactive')

# Visibility badge
visibility_class = 'badge-success' if preset.is_public else 'badge-warning'
with ui.element('span').classes(f'badge {visibility_class}'):
    ui.label('Public' if preset.is_public else 'Private')
```

#### After (Using Badge Component):
```python
from components.badge import Badge

# Permission badge
Badge.permission(u.permission)

# Status badge
Badge.status(u.is_active)

# Visibility badge
Badge.visibility(preset.is_public)
```

**Benefits:**
- 12 lines reduced to 3 lines
- Consistent styling automatically applied
- No logic duplication for color selection

---

### 2. EmptyState Component Migration

#### Before (Manual Empty State):
```python
# Pattern 1: Card-based empty state
with ui.element('div').classes('card'):
    with ui.element('div').classes('card-body text-center'):
        ui.label('No users found').classes('text-secondary text-lg')
        ui.label('Try adjusting your search or filters').classes('text-sm text-secondary')

# Pattern 2: Empty state with icon and action
with ui.element('div').classes('text-center py-8'):
    ui.icon('people').classes('text-secondary icon-large')
    ui.label('No members yet').classes('text-secondary text-lg mt-4')
    ui.label('Add members to get started').classes('text-secondary mt-2')
    if can_manage:
        ui.button('Invite Member', on_click=self._open_invite).classes('btn btn-primary mt-4')
```

#### After (Using EmptyState Component):
```python
from components.empty_state import EmptyState

# Pattern 1: No results
EmptyState.no_results(in_card=True)

# Pattern 2: No items with action
EmptyState.no_items(
    item_name='members',
    action_text='Invite Member' if can_manage else None,
    action_callback=self._open_invite if can_manage else None,
    in_card=True
)
```

**Benefits:**
- Consistent empty state messaging
- Automatic icon and styling
- Optional action button handling
- Reduces 10+ lines to 1-5 lines

---

### 3. StatCard Component Migration

#### Before (Manual Stat Cards):
```python
with Card.create(title='My Statistics'):
    with ui.element('div').classes('grid grid-cols-2 md:grid-cols-4 gap-md'):
        # Completed
        with ui.element('div').classes('stat-card'):
            ui.label(str(len(completed_races))).classes('stat-value')
            ui.label('Completed').classes('stat-label')

        # Forfeited
        with ui.element('div').classes('stat-card'):
            ui.label(str(len(forfeited_races))).classes('stat-value text-danger')
            ui.label('Forfeited').classes('stat-label')

        # Active
        with ui.element('div').classes('stat-card'):
            ui.label(str(len(active_races))).classes('stat-value text-info')
            ui.label('Active').classes('stat-label')

        # Total Score
        with ui.element('div').classes('stat-card'):
            ui.label(f'{total_score:.1f}').classes('stat-value text-success')
            ui.label('Total Score').classes('stat-label')
```

#### After (Using StatGrid Component):
```python
from components.stat_card import StatGrid

with Card.create(title='My Statistics'):
    stats = [
        {'value': str(len(completed_races)), 'label': 'Completed'},
        {'value': str(len(forfeited_races)), 'label': 'Forfeited', 'color': 'danger'},
        {'value': str(len(active_races)), 'label': 'Active', 'color': 'info'},
        {'value': f'{total_score:.1f}', 'label': 'Total Score', 'color': 'success'},
    ]
    StatGrid.render(stats, columns=4)
```

**Benefits:**
- Cleaner data-driven approach
- Easier to add/remove stats
- Consistent responsive layout
- Reduces ~24 lines to ~8 lines

---

## Common Badge Patterns

### Race Status Badges:
```python
# Before
status_badge_class = {
    'finished': 'badge-success',
    'in_progress': 'badge-info',
    'pending': 'badge-warning',
    'forfeit': 'badge-danger',
    'disqualified': 'badge-danger',
}.get(race.status, 'badge')
ui.label(race.status.replace('_', ' ').title()).classes(f'badge {status_badge_class}')

# After
Badge.race_status(race.status)
```

### Enabled/Disabled Badges:
```python
# Before
badge_class = 'badge-success' if command.is_enabled else 'badge-warning'
ui.label('Enabled' if command.is_enabled else 'Disabled').classes(f'badge {badge_class}')

# After
Badge.enabled(command.is_enabled)
```

### Custom Text Badges:
```python
# Before
ui.label('Verified').classes('badge badge-success')

# After
Badge.custom('Verified', 'success')
```

---

## Common EmptyState Patterns

### Filtered List (No Results):
```python
# Before
with ui.element('div').classes('card'):
    with ui.element('div').classes('card-body text-center'):
        ui.label('No results found').classes('text-secondary')
        ui.label('Try adjusting filters').classes('text-sm text-secondary')

# After
EmptyState.no_results(in_card=True)
```

### Empty List with Add Button:
```python
# Before
with ui.element('div').classes('text-center py-8'):
    ui.icon('folder_open').classes('text-secondary icon-large')
    ui.label('No presets found').classes('text-secondary text-lg mt-4')
    ui.button('Create Preset', on_click=self._create).classes('btn btn-primary mt-4')

# After
EmptyState.no_items(
    item_name='presets',
    icon='folder_open',
    action_text='Create Preset',
    action_callback=self._create
)
```

### Hidden/Restricted Content:
```python
# Before
with ui.element('div').classes('text-center py-8'):
    ui.icon('visibility_off').classes('text-secondary icon-large')
    ui.label('Results Hidden').classes('text-secondary text-lg mt-4')
    ui.label('Results will be visible after tournament ends').classes('text-secondary mt-2')

# After
EmptyState.hidden(
    title='Results Hidden',
    message='Results will be visible after tournament ends'
)
```

---

## Migration Checklist

When migrating a view file:

1. **Add component imports** at the top of the file:
   ```python
   from components.badge import Badge
   from components.empty_state import EmptyState
   from components.stat_card import StatGrid
   ```

2. **Identify patterns** to migrate:
   - Search for `badge` class usage
   - Search for empty state patterns (`No .* found`, `text-center py-8`)
   - Search for `stat-card` usage

3. **Replace patterns** with component calls:
   - Replace badge creation with `Badge.*()` methods
   - Replace empty states with `EmptyState.*()` methods
   - Replace stat cards with `StatGrid.render()`

4. **Test the changes**:
   - Verify badges display correctly
   - Check empty states appear as expected
   - Ensure stats render in responsive grid

5. **Remove unused code**:
   - Delete badge color logic
   - Remove manual grid layout code
   - Clean up empty state markup

---

## Files Already Migrated

Example migrations for reference:

1. **views/admin/admin_users.py**
   - Badge.permission() for permission badges
   - Badge.status() for active/inactive badges
   - EmptyState.no_results() for empty user list

2. **views/tournaments/async_dashboard.py**
   - StatGrid.render() for player statistics
   - EmptyState.render() for no races message
   - Badge.race_status() for race status badges

---

## When NOT to Use Components

Components are designed for common patterns. Don't force-fit if:

1. **Highly custom styling needed** - If the badge/empty state needs unique styling that doesn't fit the variants
2. **Dynamic nested content** - If the empty state needs complex nested UI (use EmptyState.render() with in_card=False and add custom content after)
3. **Performance-critical rendering** - If rendering thousands of badges in a tight loop (though this is rare)

In these cases, document why custom markup is needed and consider proposing a new component variant.

---

## Getting Help

- See `docs/core/COMPONENTS_GUIDE.md` for complete component API documentation
- Check migrated files for examples: `views/admin/admin_users.py`, `views/tournaments/async_dashboard.py`
- Examine component source code: `components/badge.py`, `components/empty_state.py`, `components/stat_card.py`
