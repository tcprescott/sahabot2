# SpeedGaming Integration UI Guide

## Overview

This document provides guidance for implementing UI controls to enable and configure SpeedGaming integration for tournaments.

## API Support

The API already supports SpeedGaming configuration through the tournament endpoints:

### Tournament Schema

**TournamentOut** includes:
- `speedgaming_enabled`: bool - Whether SpeedGaming integration is enabled
- `speedgaming_event_slug`: Optional[str] - SpeedGaming event slug

**TournamentCreateRequest** and **TournamentUpdateRequest** support:
- `speedgaming_enabled`: bool - Enable/disable integration
- `speedgaming_event_slug`: Optional[str] - Event slug (required if enabled)

**MatchOut** includes:
- `speedgaming_episode_id`: Optional[int] - Episode ID for imported matches

## UI Implementation Requirements

### Tournament Configuration Page

Add a section for SpeedGaming Integration with the following controls:

#### 1. Enable/Disable Toggle

```python
# Example NiceGUI implementation
with ui.card().classes('mt-4'):
    ui.label('SpeedGaming Integration').classes('text-h6')
    
    speedgaming_enabled = ui.switch(
        'Enable SpeedGaming Integration',
        value=tournament.speedgaming_enabled
    )
    
    # Warning message when enabled
    with ui.row().classes('mt-2') as warning_row:
        ui.icon('warning', color='warning')
        with ui.column():
            ui.label('Important:').classes('text-bold')
            ui.label('• Match schedule will be READ-ONLY')
            ui.label('• Updates sync every 5 minutes from SpeedGaming')
            ui.label('• You cannot manually create or edit matches')
    
    # Show warning only when enabled
    warning_row.bind_visibility_from(speedgaming_enabled, 'value')
```

#### 2. Event Slug Input

```python
    speedgaming_event_slug = ui.input(
        'SpeedGaming Event Slug',
        placeholder='e.g., alttprleague',
        value=tournament.speedgaming_event_slug or ''
    ).classes('w-full')
    
    # Only show when enabled
    speedgaming_event_slug.bind_visibility_from(speedgaming_enabled, 'value')
    
    # Add help text
    ui.label(
        'The event slug from SpeedGaming.org (found in the event URL)'
    ).classes('text-caption').bind_visibility_from(speedgaming_enabled, 'value')
```

#### 3. Save Button with Validation

```python
    async def save_speedgaming_config():
        # Validate event slug is provided when enabled
        if speedgaming_enabled.value and not speedgaming_event_slug.value:
            ui.notify('Event slug is required when SpeedGaming is enabled', type='negative')
            return
        
        # Confirm if enabling for the first time
        if speedgaming_enabled.value and not tournament.speedgaming_enabled:
            # Show confirmation dialog
            confirmed = await show_confirmation_dialog(
                title='Enable SpeedGaming Integration?',
                message='This will make the tournament schedule READ-ONLY. '
                        'All matches must be managed through SpeedGaming. Continue?'
            )
            if not confirmed:
                return
        
        # Call API to update tournament
        from application.services.tournament_service import TournamentService
        service = TournamentService()
        
        updated = await service.update_tournament(
            user=current_user,
            organization_id=org_id,
            tournament_id=tournament.id,
            speedgaming_enabled=speedgaming_enabled.value,
            speedgaming_event_slug=speedgaming_event_slug.value if speedgaming_enabled.value else None,
        )
        
        if updated:
            ui.notify('SpeedGaming configuration saved', type='positive')
        else:
            ui.notify('Failed to save configuration', type='negative')
    
    ui.button('Save Configuration', on_click=save_speedgaming_config)
```

### Match List Page

#### Show SpeedGaming Import Status

```python
# In match list/table, add indicator for imported matches
for match in matches:
    with ui.row():
        ui.label(match.title)
        
        # Show SpeedGaming badge if imported
        if match.speedgaming_episode_id:
            ui.badge('SpeedGaming').classes('badge-info')
```

#### Disable Edit Controls for Read-Only Tournaments

```python
# Check if tournament has SpeedGaming enabled
tournament = await get_tournament(tournament_id)
is_read_only = tournament.speedgaming_enabled

# Conditionally show/hide edit buttons
if not is_read_only:
    ui.button('Create Match', on_click=create_match_dialog)
    ui.button('Edit', on_click=lambda: edit_match(match.id))
else:
    # Show info message instead
    with ui.row().classes('mt-2'):
        ui.icon('info', color='info')
        ui.label('Schedule managed by SpeedGaming (read-only)')
```

### Crew Signup Page

#### Disable Crew Signups for SpeedGaming Matches

```python
# Check if match is from SpeedGaming
if match.speedgaming_episode_id:
    # Show message instead of signup buttons
    with ui.card().classes('mt-4'):
        ui.icon('info', color='info')
        ui.label('Crew assignments managed by SpeedGaming')
        ui.label('Contact tournament organizers to update crew on SpeedGaming.org')
else:
    # Show normal signup buttons
    ui.button('Sign up as Commentator', on_click=signup_commentator)
    ui.button('Sign up as Tracker', on_click=signup_tracker)
```

## Confirmation Dialog Example

```python
async def show_confirmation_dialog(title: str, message: str) -> bool:
    """Show confirmation dialog and return user's choice."""
    result = {'confirmed': False}
    
    with ui.dialog() as dialog, ui.card():
        ui.label(title).classes('text-h6')
        ui.label(message).classes('mt-2')
        
        with ui.row().classes('mt-4 gap-md'):
            ui.button('Cancel', on_click=lambda: dialog.close()).classes('btn-secondary')
            ui.button('Confirm', on_click=lambda: (
                result.update({'confirmed': True}),
                dialog.close()
            )).classes('btn-primary')
    
    await dialog
    return result['confirmed']
```

## Warning Messages

### Key Points to Communicate

1. **Read-Only Schedule**: Once SpeedGaming is enabled, users cannot:
   - Create matches manually
   - Edit match details (title, schedule)
   - Add or remove players
   - Sign up for crew roles
   - Approve crew signups

2. **Sync Interval**: Updates from SpeedGaming happen every 5 minutes automatically

3. **Source of Truth**: SpeedGaming.org is the authoritative source for the schedule

4. **Reversibility**: Disabling SpeedGaming integration doesn't delete imported matches

### Suggested Warning Text

**When Enabling:**
```
⚠️ Important: Enabling SpeedGaming Integration

This will make your tournament schedule READ-ONLY:
• Matches will be imported automatically from SpeedGaming
• Updates sync every 5 minutes
• You cannot create or edit matches manually
• All schedule changes must be made on SpeedGaming.org

Are you sure you want to continue?
```

**On Configuration Page:**
```
ℹ️ SpeedGaming Integration Active

This tournament's schedule is managed by SpeedGaming.org and syncs every 5 minutes.
To make changes to the schedule, update the event on SpeedGaming.org.
```

**On Match List:**
```
ℹ️ Schedule is read-only (managed by SpeedGaming)

Matches are imported automatically from SpeedGaming every 5 minutes.
To add or modify matches, edit the event on SpeedGaming.org.
```

## Error Handling

### Validation Errors

```python
# Missing event slug
if speedgaming_enabled and not speedgaming_event_slug:
    ui.notify('Event slug is required when SpeedGaming is enabled', type='negative')

# Invalid event slug format (optional)
if speedgaming_event_slug and not is_valid_slug(speedgaming_event_slug):
    ui.notify('Event slug can only contain lowercase letters, numbers, and hyphens', type='negative')
```

### API Errors

```python
try:
    updated = await service.update_tournament(...)
except ValueError as e:
    # Service-level validation errors
    ui.notify(str(e), type='negative')
except Exception as e:
    logger.error("Failed to update SpeedGaming config: %s", e)
    ui.notify('An error occurred. Please try again.', type='negative')
```

## Testing Checklist

- [ ] Enable SpeedGaming shows warning dialog
- [ ] Event slug is required when enabled
- [ ] Confirmation dialog can be cancelled
- [ ] Configuration saves successfully
- [ ] Tournament list shows SpeedGaming status
- [ ] Match create button hidden when enabled
- [ ] Match edit button hidden when enabled
- [ ] Crew signup buttons hidden for SpeedGaming matches
- [ ] Info messages display when schedule is read-only
- [ ] SpeedGaming badge shows on imported matches
- [ ] Disabling SpeedGaming restores edit controls

## Example Pages

See the following files for implementation examples:
- `pages/tournaments.py` - Tournament configuration
- `views/tournaments/` - Tournament views
- `components/dialogs/tournaments/` - Tournament dialogs

## API Endpoints

**Update Tournament:**
```
PUT /api/organizations/{org_id}/tournaments/{tournament_id}
Content-Type: application/json

{
  "speedgaming_enabled": true,
  "speedgaming_event_slug": "alttprleague"
}
```

**Get Tournament:**
```
GET /api/organizations/{org_id}/tournaments/{tournament_id}

Response:
{
  "id": 5,
  "name": "ALTTPR League",
  "speedgaming_enabled": true,
  "speedgaming_event_slug": "alttprleague",
  ...
}
```

## Related Documentation

- `docs/integrations/SPEEDGAMING_INTEGRATION.md` - Integration architecture
- `docs/PATTERNS.md` - Code patterns and UI conventions
- `docs/core/BASEPAGE_GUIDE.md` - Page template usage
