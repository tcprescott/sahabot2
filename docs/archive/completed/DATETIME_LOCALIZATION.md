# DateTime Localization Guide

## Overview
The `DateTimeLabel` component automatically formats datetime values using the user's browser locale and timezone. This provides a better user experience by showing dates and times in the user's preferred format and local timezone.

## How It Works
- **Server-side**: Datetimes are stored in UTC in the database
- **Client-side**: JavaScript's `Intl.DateTimeFormat` and `Intl.RelativeTimeFormat` APIs format the datetime based on the user's browser settings
- **No configuration needed**: The component automatically detects the user's locale and timezone

## Basic Usage

### Import
```python
from components.datetime_label import DateTimeLabel
```

### Available Methods

#### 1. `DateTimeLabel.datetime(dt)` - Date and Time
Displays both date and time in medium format (e.g., "Oct 31, 2025, 2:45 PM")
```python
DateTimeLabel.datetime(match.scheduled_at)
```

#### 2. `DateTimeLabel.date(dt)` - Date Only
Displays only the date (e.g., "Oct 31, 2025")
```python
DateTimeLabel.date(user.created_at)
```

#### 3. `DateTimeLabel.time(dt)` - Time Only
Displays only the time (e.g., "2:45 PM")
```python
DateTimeLabel.time(event.start_time)
```

#### 4. `DateTimeLabel.full(dt)` - Full Verbose Format
Displays full verbose format (e.g., "Thursday, October 31, 2025 at 2:45:30 PM EDT")
```python
DateTimeLabel.full(important_event.datetime)
```

#### 5. `DateTimeLabel.short(dt)` - Short Format
Displays short format (e.g., "10/31/25, 2:45 PM")
```python
DateTimeLabel.short(log_entry.timestamp)
```

#### 6. `DateTimeLabel.relative(dt)` - Relative Time
Displays relative time (e.g., "2 hours ago", "in 3 days")
```python
DateTimeLabel.relative(comment.created_at)
```

### Optional Parameters
All methods accept optional parameters:
- `classes`: CSS classes to apply (default: '')
- `fallback`: Text to display if datetime is None (default: 'N/A')

```python
DateTimeLabel.datetime(match.scheduled_at, classes='text-sm text-secondary', fallback='TBD')
```

## Examples

### Tournament Match Schedule
```python
def render_scheduled_time(match: Match):
    if match.scheduled_at:
        DateTimeLabel.datetime(match.scheduled_at)
    else:
        ui.label('TBD').classes('text-secondary')
```

### User Registration Date
```python
with ui.row().classes('items-center gap-1'):
    ui.label('Registered:').classes('text-sm')
    DateTimeLabel.date(registration.created_at, classes='text-sm')
```

### Last Activity (Relative)
```python
with ui.column():
    ui.label('Last Active').classes('text-secondary')
    DateTimeLabel.relative(user.last_login_at)
```

### API Key Creation
```python
def render_created(token):
    return DateTimeLabel.datetime(token.created_at)
```

## Localization Examples

The same datetime will be displayed differently based on the user's locale:

### English (US)
- `datetime`: "Oct 31, 2025, 2:45 PM"
- `date`: "Oct 31, 2025"
- `full`: "Thursday, October 31, 2025 at 2:45:30 PM EDT"

### Spanish (ES)
- `datetime`: "31 oct 2025, 14:45"
- `date`: "31 oct 2025"
- `full`: "jueves, 31 de octubre de 2025, 14:45:30 EDT"

### Japanese (JP)
- `datetime`: "2025/10/31 14:45"
- `date`: "2025/10/31"
- `full`: "2025年10月31日木曜日 14:45:30 EDT"

### German (DE)
- `datetime`: "31.10.2025, 14:45"
- `date`: "31.10.2025"
- `full`: "Donnerstag, 31. Oktober 2025 um 14:45:30 EDT"

## Best Practices

1. **Always store datetimes in UTC** in the database
2. **Use the appropriate format** for the context:
   - `datetime` for most cases (schedules, logs)
   - `date` for birthdays, registration dates
   - `relative` for recent activity, comments
   - `full` for important events requiring full context
3. **Provide fallback values** for optional datetimes
4. **Apply consistent styling** using the classes parameter

## Migration from strftime

### Before
```python
ui.label(match.scheduled_at.strftime('%Y-%m-%d %H:%M'))
```

### After
```python
DateTimeLabel.datetime(match.scheduled_at)
```

### Before (with styling)
```python
ui.label(user.created_at.strftime('%B %d, %Y')).classes('text-sm')
```

### After (with styling)
```python
DateTimeLabel.date(user.created_at, classes='text-sm')
```

## Browser Support
- **Intl.DateTimeFormat**: Supported in all modern browsers (Chrome, Firefox, Safari, Edge)
- **Intl.RelativeTimeFormat**: Supported in Chrome 71+, Firefox 65+, Safari 14+, Edge 79+
- **Fallback**: For older browsers, a simple date string will be displayed

## Troubleshooting

### DateTime shows "Loading..."
- Check that the datetime object is valid
- Ensure the datetime can be converted to ISO format

### Wrong timezone displayed
- Datetimes should be stored in UTC in the database
- The component will automatically convert to the user's local timezone

### Format doesn't match expectations
- The format is determined by the user's browser locale settings
- Users can change their browser language settings to see different formats
