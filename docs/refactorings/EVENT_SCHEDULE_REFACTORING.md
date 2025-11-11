# Event Schedule View Refactoring

**Date**: November 11, 2025  
**Issue**: The `EventScheduleView` class was very large (1667 lines) and difficult to maintain.  
**Goal**: Break down into smaller, reusable components and add spinner functionality to buttons.

## Summary

Refactored `EventScheduleView` by extracting reusable components into three new classes:
- Reduced code from **1666 lines to 988 lines** (40.7% reduction)
- Added loading spinners to "Generate Seed" and "Create Room" buttons
- Improved code organization and reusability

## New Components

### 1. MatchCellRenderers (`components/tournaments/match_cell_renderers.py`)

**Purpose**: Simple, stateless rendering functions for table cells.

**Methods**:
- `render_tournament(match)` - Tournament name
- `render_title(match)` - Match title with SpeedGaming badge
- `render_scheduled_time(match)` - Scheduled time or TBD
- `render_stream(match)` - Stream channel name
- `render_players(match)` - Player list with station numbers

**Usage**:
```python
renderers = MatchCellRenderers()
TableColumn("Tournament", cell_render=renderers.render_tournament)
```

### 2. MatchActions (`components/tournaments/match_actions.py`)

**Purpose**: Match action handlers with spinner support for async operations.

**Methods**:
- `generate_seed(match_id, match_title, button)` - Generate randomizer seed with spinner
- `open_seed_dialog(match_id, match_title, matches)` - Open seed edit dialog
- `render_seed(match, matches)` - Render seed cell with action buttons
- `create_racetime_room(match_id, button)` - Create RaceTime room with spinner
- `sync_racetime_status(match_id)` - Sync match status from RaceTime
- `render_racetime(match)` - Render RaceTime cell with controls
- `open_edit_match_dialog(match_id, matches)` - Open match edit dialog
- `render_actions(match, matches, can_edit_matches)` - Render action buttons

**Key Features**:
- **Spinner Support**: Buttons show loading state during async operations
- Button reference pattern using list to avoid closure issues
- Automatic enable/disable during operations

**Usage**:
```python
match_actions = MatchActions(
    user=user,
    organization=organization,
    service=tournament_service,
    can_manage_tournaments=True,
    on_refresh=refresh_callback
)
match_actions.render_seed(match, matches)
```

### 3. CrewManagement (`components/tournaments/crew_management.py`)

**Purpose**: Crew signup, approval, and rendering for commentators and trackers.

**Methods**:
- `signup_crew(match_id, role)` - Sign up for crew role
- `remove_crew(match_id, role)` - Remove crew signup
- `approve_crew_signup(crew_id, role)` - Approve crew
- `unapprove_crew_signup(crew_id, role)` - Remove approval
- `open_add_crew_dialog(match, default_role)` - Admin add crew dialog
- `render_commentator(match)` - Render commentator cell with controls
- `render_tracker(match)` - Render tracker cell with controls

**Usage**:
```python
crew_mgmt = CrewManagement(
    user=user,
    organization=organization,
    service=tournament_service,
    can_approve_crew=True,
    on_refresh=refresh_callback
)
crew_mgmt.render_commentator(match)
```

## Architecture Changes

### Before (Monolithic)
```
EventScheduleView (1666 lines)
├── Initialization
├── Filter management
├── Match rendering (nested functions)
│   ├── render_tournament()
│   ├── render_title()
│   ├── render_players()
│   ├── render_seed()
│   ├── render_racetime()
│   ├── render_commentator()
│   ├── render_tracker()
│   ├── generate_seed()
│   ├── create_racetime_room()
│   ├── signup_crew()
│   ├── approve_crew_signup()
│   └── ... (many more nested functions)
└── Create match dialogs
```

### After (Modular)
```
EventScheduleView (988 lines)
├── Initialization
├── Filter management
├── Component initialization
│   ├── MatchActions
│   ├── CrewManagement
│   └── MatchCellRenderers
├── Match rendering (delegated)
└── Create match dialogs

components/tournaments/
├── match_cell_renderers.py (88 lines)
├── match_actions.py (462 lines)
└── crew_management.py (421 lines)
```

## Button Spinner Implementation

### Generate Seed Button

**Before**:
```python
ui.button(
    icon="casino",
    on_click=lambda m=match: generate_seed(m.id, m.title),
)
```

**After**:
```python
button_ref = [None]  # Closure-safe reference
async def on_generate_click(m=match, btn_ref=button_ref):
    await self.generate_seed(m.id, m.title, btn_ref[0])

button_ref[0] = ui.button(
    icon="casino",
    on_click=on_generate_click,
)
```

**In generate_seed method**:
```python
async def generate_seed(self, match_id, match_title, button=None):
    if button:
        button.props("loading")  # Show spinner
        button.disable()          # Disable button
    
    try:
        # ... perform operation ...
    finally:
        if button:
            button.props(remove="loading")  # Remove spinner
            button.enable()                  # Re-enable button
```

### Create Room Button

Same pattern as Generate Seed - uses button reference and loading props.

## Reusability Benefits

These components can now be used in other parts of the application:

1. **MyMatchesView** - Can reuse match cell renderers
2. **Tournament Admin** - Can reuse match actions for bulk operations
3. **Other Views** - Any view displaying match data can use these components

## Testing Checklist

- [x] Syntax validation - All files compile without errors
- [x] Import validation - All components import correctly
- [x] Component structure - All expected methods present
- [ ] UI functionality - Manual testing required
- [ ] Button spinners - Visual verification required
- [ ] Crew management - Test signup/approval flow
- [ ] Seed generation - Test with/without randomizer
- [ ] RaceTime rooms - Test room creation

## Migration Notes

### For Developers

1. **Import Changes**: None required for external usage - `EventScheduleView` import remains the same
2. **New Components Available**: Import from `components.tournaments`
3. **Backward Compatible**: All existing functionality preserved

### Potential Future Improvements

1. Extract status management functions (advance/revert) if needed
2. Create base class for match renderers to reduce duplication
3. Add unit tests for individual components
4. Consider extracting filter management to separate component
5. Add more comprehensive error handling in components

## Files Changed

- `views/tournaments/event_schedule.py` - Refactored main view
- `components/tournaments/__init__.py` - New module exports
- `components/tournaments/match_cell_renderers.py` - New component
- `components/tournaments/match_actions.py` - New component
- `components/tournaments/crew_management.py` - New component

## References

- Original Issue: Breaking down large EventScheduleView class
- Repository Pattern: `docs/PATTERNS.md`
- Component Guidelines: `docs/core/COMPONENTS_GUIDE.md`
