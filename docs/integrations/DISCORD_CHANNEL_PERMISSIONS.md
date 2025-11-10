# Discord Channel Permission Checking for Async Qualifiers

## Overview

This implementation adds automatic permission checking for Discord channels when creating or editing async qualifiers. The system verifies that the selected Discord channel has the correct permissions and displays warnings if issues are found.

## Features

1. **Permission Validation**: Checks channel permissions when creating or updating async qualifiers
2. **Warning System**: Displays warnings to users if permissions are not correctly configured
3. **Non-Blocking**: Tournaments can still be created even with permission warnings
4. **Centralized Configuration**: All permission requirements are defined in one place for easy modification

## Permission Requirements

### @everyone Role Restrictions
The following permissions should be **denied** for the @everyone role:
- `send_messages` - Prevents @everyone from creating messages
- `create_public_threads` - Prevents @everyone from creating public threads
- `create_private_threads` - Prevents @everyone from creating private threads

### Bot Required Permissions
The bot must have the following permissions **allowed**:
- `send_messages` - Allows bot to post messages in the channel (for embeds, countdown messages)
- `send_messages_in_threads` - Allows bot to post messages in race threads (critical for race flow)
- `embed_links` - Allows bot to send rich embeds with tournament and race information
- `manage_threads` - Allows bot to manage threads and add users to them
- `create_private_threads` - Allows bot to create private threads for individual races
- `read_message_history` - Recommended for thread operations (not strictly required)

## Implementation Details

### Core Components

#### 1. Configuration (`application/services/discord_permissions_config.py`)
Central configuration file that defines all permission requirements:
- `AsyncTournamentChannelPermissions` class contains all requirements
- Easy to modify permission requirements in one place
- Provides helper methods to get permission names and descriptions

#### 2. Permission Checker (`application/services/discord_guild_service.py`)
- `ChannelPermissionCheck` dataclass - Result of permission check
- `check_async_qualifier_channel_permissions()` method - Performs the actual check
- Uses Discord.py to fetch channel and check permissions
- Returns warnings list for any permission issues found

#### 3. Service Layer (`application/services/async_qualifier_service.py`)
- `create_tournament()` - Returns tuple of (tournament, warnings)
- `update_tournament()` - Returns tuple of (tournament, warnings)
- Calls permission checker when Discord channel is specified
- Logs permission warnings but still creates/updates tournament

#### 4. API Layer (`api/routes/async_qualifiers.py`, `api/schemas/async_qualifier.py`)
- `AsyncTournamentCreateResponse` schema includes warnings field
- Both create and update endpoints return tournament + warnings
- API consumers receive warnings in response

#### 5. UI Layer (`views/organization/org_async_qualifiers.py`)
- Create and edit dialogs display warnings to user
- Warnings shown as individual notifications with 'warning' type
- Tournament creation/update proceeds even with warnings

## How to Change Permission Requirements

To modify the permission requirements, edit `application/services/discord_permissions_config.py`:

### Example: Add a new bot permission requirement

```python
BOT_REQUIRED_PERMISSIONS: List[PermissionRequirement] = [
    # ... existing permissions ...
    PermissionRequirement(
        permission_name="attach_files",
        description="Bot cannot attach files (required for image uploads)",
        required=True
    ),
]
```

### Example: Make a permission optional instead of required

Set `required=False` in the `PermissionRequirement`:

```python
PermissionRequirement(
    permission_name="read_message_history",
    description="Bot cannot read message history (recommended)",
    required=False  # Now just a warning, not critical
),
```

## User Experience

### Creating a Tournament with Correct Permissions
1. User selects Discord channel with correct permissions
2. Tournament is created successfully
3. Success notification is displayed
4. No warnings shown

### Creating a Tournament with Permission Issues
1. User selects Discord channel with incorrect permissions
2. Tournament is still created (not blocked)
3. Success notification is displayed
4. Warning notifications are shown for each permission issue:
   - "Warning: @everyone role can send messages (should be disabled)"
   - "Warning: Bot cannot manage threads (required)"
   - etc.

### Updating Tournament Channel
Same behavior as creation - warnings displayed if new channel has permission issues.

## Technical Notes

### Permission Check Flow
1. Service receives discord_channel_id
2. Service calls `DiscordGuildService.check_async_qualifier_channel_permissions()`
3. Permission checker:
   - Gets bot instance (via `get_bot_instance()`)
   - Fetches Discord channel
   - Checks @everyone role permissions
   - Checks bot member permissions
   - Returns result with warnings list
4. Service logs warnings and returns them with tournament
5. API/UI displays warnings to user

### Error Handling
- If bot is not running: Warning added, tournament still created
- If channel not found: Warning added, tournament still created
- If permission check fails: Warning added, tournament still created
- All permission check errors are logged

### Thread Channels
For Discord Thread channels:
- Cannot check @everyone overwrites (threads inherit from parent)
- Only bot permissions are checked
- Warning mentions "thread's parent channel"

## Testing Considerations

To test this implementation:

1. **Correct Permissions**: Create tournament with properly configured channel - should succeed with no warnings
2. **@everyone Can Post**: Allow @everyone to send messages - should show warning but create tournament
3. **Bot Missing Permissions**: Remove manage_threads from bot - should show warning but create tournament
4. **Invalid Channel**: Use non-existent channel ID - should show warning but create tournament
5. **Bot Offline**: Stop bot before creating tournament - should show "Bot is not running" warning

## Future Enhancements

Possible improvements:
1. Add permission check for existing tournaments (bulk validation)
2. Add API endpoint to check channel permissions without creating tournament
3. Add UI element to show permission status in tournament list
4. Make warnings blockable (make tournament creation fail if critical permissions missing)
5. Add automatic permission setup feature (bot sets correct permissions when channel is selected)
