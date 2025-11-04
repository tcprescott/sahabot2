# RaceTime Chat Commands UI Implementation

## Overview

This document describes the user interface for managing racetime.gg chat commands across three different scopes: global bot-level, tournament-level, and async tournament-level.

## Architecture

### Components

#### Dialog
- **Location**: `components/dialogs/racetime/chat_command_dialog.py`
- **Class**: `RacetimeChatCommandDialog`
- **Purpose**: Reusable dialog for adding/editing commands at any scope
- **Features**:
  - Scope detection (BOT, TOURNAMENT, ASYNC_TOURNAMENT)
  - Response type selection (TEXT for static, DYNAMIC for handler-based)
  - Cooldown configuration
  - Linked account requirement toggle
  - Enable/disable toggle
  - Built-in handler selection for DYNAMIC commands
  - Validation for command names and response configuration

#### Views

##### 1. Admin View (Global BOT-level)
- **Location**: `views/admin/admin_racetime_chat_commands.py`
- **Class**: `AdminRacetimeChatCommandsView`
- **Access**: Admin page → Chat Commands (sidebar)
- **URL**: `/admin?view=racetime-chat-commands`
- **Features**:
  - Bot selector dropdown (multi-bot support)
  - Command list table with search and filters
  - Add/Edit/Delete commands
  - Shows command type (Static/Dynamic)
  - Shows handler name for dynamic commands
  - Shows cooldown and linked account requirements

##### 2. Tournament Admin View
- **Location**: `views/tournament_admin/tournament_racetime_chat_commands.py`
- **Class**: `TournamentRacetimeChatCommandsView`
- **Access**: Organization Admin → Tournaments → Select Tournament → Chat Commands
- **URL**: `/org/{org_id}/tournament/{tournament_id}/admin?view=chat-commands`
- **Features**:
  - Tournament-scoped command management
  - Inherits all features from admin view
  - Context-aware (automatically scopes to tournament)

##### 3. Async Tournament Admin View
- **Location**: `views/organization/org_async_tournament_chat_commands.py`
- **Class**: `AsyncTournamentRacetimeChatCommandsView`
- **Access**: Organization Admin → Async Tournaments → Admin button → Chat Commands
- **URL**: `/org/{org_id}/async/{tournament_id}/admin?view=chat-commands`
- **Features**:
  - Async tournament-scoped command management
  - Inherits all features from admin view
  - Context-aware (automatically scopes to async tournament)

### Pages

#### Async Tournament Admin Page
- **Location**: `pages/async_tournament_admin.py`
- **URL**: `/org/{organization_id}/async/{tournament_id}/admin`
- **Purpose**: Dedicated admin page for async tournaments (similar to regular tournament admin)
- **Sections**:
  - Overview (dashboard)
  - Chat Commands
  - Settings (placeholder for future expansion)

## Navigation Flow

### Global Bot Commands
1. Navigate to `/admin`
2. Click "Chat Commands" in sidebar
3. Select bot from dropdown
4. View/manage commands for that bot

### Tournament Commands
1. Navigate to organization admin: `/orgs/{org_id}/admin`
2. Click "Tournaments" in sidebar
3. Select a tournament
4. Click "Admin" button
5. Click "Chat Commands" in sidebar
6. View/manage commands for that tournament

### Async Tournament Commands
1. Navigate to organization admin: `/orgs/{org_id}/admin`
2. Click "Async Tournaments" in sidebar
3. Click "Admin" button for a tournament
4. Click "Chat Commands" in sidebar
5. View/manage commands for that async tournament

## Table Display

All three views use a consistent table layout with these columns:

| Column | Description |
|--------|-------------|
| Command | Shows `!command_name` with link icon if requires linked account |
| Type | Static (text icon) or Dynamic (code icon) |
| Response | Preview of static text OR handler function name |
| Cooldown | Displays cooldown in seconds or "None" |
| Status | Enabled (green badge) or Disabled (yellow badge) |
| Actions | Edit and Delete buttons |

### Mobile Responsiveness
- Uses `ResponsiveTable` component
- Automatically stacks on small screens
- Maintains all functionality on mobile

## Dialog Workflow

### Adding a Command
1. Click "Add Command" button
2. Dialog opens with empty form
3. Enter command name (without ! prefix)
4. Select response type:
   - **Static Text**: Enter text to respond with
   - **Dynamic Handler**: Select handler from dropdown
5. Configure settings:
   - Cooldown (0 = no cooldown)
   - Require linked account (checkbox)
   - Enabled (checkbox, default: true)
6. Click "Save"
7. Command created, table refreshes

### Editing a Command
1. Click edit icon for a command
2. Dialog opens with pre-filled form
3. **Note**: Command name is read-only (cannot change)
4. Modify response type, settings, etc.
5. Click "Save"
6. Command updated, table refreshes

### Deleting a Command
1. Click delete icon for a command
2. Confirmation dialog appears
3. Confirm deletion
4. Command deleted, table refreshes

## Authorization

### Admin View (BOT scope)
- Requires: `SUPERADMIN` or `ADMIN` permission
- Enforced at page level and service level

### Tournament Admin View (TOURNAMENT scope)
- Requires: Organization membership + tournament management permission
- Pre-checked in page loader
- Enforced at service level

### Async Tournament Admin View (ASYNC_TOURNAMENT scope)
- Requires: Organization membership + tournament management permission
- Pre-checked in page loader
- Enforced at service level

## Service Integration

All views use `RacetimeChatCommandService` for:
- `list_bot_commands(user, bot_id)` - Admin view
- `list_tournament_commands(user, tournament_id)` - Tournament view
- `list_async_tournament_commands(user, tournament_id)` - Async tournament view
- `create_command(user, **data)` - All views
- `update_command(user, command_id, **data)` - All views
- `delete_command(user, command_id)` - All views

Authorization is enforced in the service layer, not the UI.

## Built-in Handlers

The dialog displays available handlers from `racetime.command_handlers.BUILTIN_HANDLERS`:
- `handle_help` - Shows help text
- `handle_status` - Shows race status
- `handle_race_info` - Shows race goal/info
- `handle_time` - Shows user's finish time
- `handle_entrants` - Lists entrants by status

Custom handlers can be registered via `RacetimeChatCommandService.register_handler()`.

## Search and Filtering

All views support:
- **Search**: Filter by command name (case-insensitive)
- **Show disabled**: Toggle to include/exclude disabled commands

Filtering is client-side for performance (small datasets).

## Error Handling

### Validation Errors
- Empty command name → "Command name is required"
- Invalid characters → "Command name can only contain letters, numbers, and underscores"
- Missing response text → "Response text is required for static text commands"
- Missing handler → "Handler function is required for dynamic commands"

### Service Errors
- Duplicate command name → ValueError from service
- Authorization failure → Empty list returned (not 403 error)
- Database errors → Caught and displayed as notification

## Future Enhancements

### Possible Additions
1. **Command testing**: Test button to simulate command execution
2. **Usage statistics**: Show how often commands are used
3. **Command categories**: Group related commands
4. **Bulk operations**: Enable/disable/delete multiple commands
5. **Import/Export**: Share command sets between tournaments
6. **Template commands**: Pre-built command templates for common use cases

### Admin Page Enhancements
The async tournament admin page currently has minimal views:
- Overview (dashboard)
- Chat Commands
- Settings (placeholder)

Future sections could include:
- Players/Participants management
- Pool management (currently via "Manage" button)
- Live race monitoring
- Results/Leaderboard configuration

## Testing Checklist

- [ ] Admin view: Create/edit/delete BOT-scoped command
- [ ] Tournament view: Create/edit/delete TOURNAMENT-scoped command
- [ ] Async tournament view: Create/edit/delete ASYNC_TOURNAMENT-scoped command
- [ ] Test static text response type
- [ ] Test dynamic handler response type
- [ ] Test cooldown functionality
- [ ] Test linked account requirement
- [ ] Test enable/disable toggle
- [ ] Test search filtering
- [ ] Test "Show disabled" filter
- [ ] Test mobile responsiveness
- [ ] Verify authorization checks (non-admin cannot access)
- [ ] Verify command name validation
- [ ] Verify duplicate command handling

## Related Documentation
- [RaceTime Chat Commands](RACETIME_CHAT_COMMANDS.md) - System overview
- [RaceTime Chat Commands Implementation](RACETIME_CHAT_COMMANDS_IMPLEMENTATION.md) - Technical details
- [RaceTime Chat Commands Quick Start](RACETIME_CHAT_COMMANDS_QUICKSTART.md) - Getting started guide
