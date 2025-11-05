# Async Tournament Discord Bot Permission Analysis

## Overview
This document analyzes the actual Discord bot operations for async tournaments and identifies the required permissions.

## Bot Actions Summary

### 1. **Creating Private Threads** ✅ COVERED
**Location**: `discordbot/async_tournament_views.py:216`
```python
thread = await interaction.channel.create_thread(
    name=f"{slugify(interaction.user.name, lowercase=False, max_length=20)} - {self.selected_pool.name}",
    type=discord.ChannelType.private_thread
)
```
**Required Permission**: `create_private_threads` ✅

### 2. **Adding Users to Threads** ⚠️ NOT COVERED
**Location**: `discordbot/async_tournament_views.py:231`
```python
await thread.add_user(interaction.user)
```
**Required Permission**: `manage_threads` ✅ (This allows adding/removing users from threads)

### 3. **Sending Messages in Channel** ⚠️ NOT COVERED
**Location**: Multiple locations where bot posts embeds and views
- `discordbot/commands/async_tournament.py:74` - Posts tournament embed
- `discordbot/async_tournament_views.py:244` - Posts race info in thread
- `discordbot/async_tournament_views.py:334` - Sends countdown messages
- `discordbot/async_tournament_views.py:346` - Sends "GO!" message

**Required Permission**: `send_messages` ❌ **MISSING**

### 4. **Sending Messages in Threads** ⚠️ NOT COVERED
**Location**: `discordbot/async_tournament_views.py:244-261`
```python
await thread.send(content=message, embed=embed, view=RaceReadyView())
```
**Required Permission**: `send_messages_in_threads` ❌ **MISSING**

### 5. **Editing Messages** ⚠️ NOT COVERED
**Location**: `discordbot/async_tournament_views.py:329`
```python
await interaction.followup.edit_message(message_id=interaction.message.id, view=self)
```
**Required Permission**: Implicitly included with `send_messages`

### 6. **Embed Links** ⚠️ NOT COVERED
**Location**: Multiple - Bot sends rich embeds
**Required Permission**: `embed_links` ❌ **MISSING**

### 7. **Reading Message History** ⚠️ POSSIBLY NEEDED
**Location**: Not explicitly used but may be needed for thread operations
**Required Permission**: `read_message_history` ❌ **MISSING**

## Current Configuration Analysis

### Currently Checked Permissions ✅
```python
BOT_REQUIRED_PERMISSIONS: List[PermissionRequirement] = [
    manage_threads,           # ✅ Needed - add users to thread
    create_public_threads,    # ⚠️ Not used (only private threads created)
    create_private_threads,   # ✅ Needed - creates private threads
]
```

### Missing Critical Permissions ❌
```python
# These are REQUIRED but NOT checked:
send_messages               # ❌ CRITICAL - Bot sends messages in channel
send_messages_in_threads    # ❌ CRITICAL - Bot sends messages in threads
embed_links                 # ❌ CRITICAL - Bot sends embeds
read_message_history        # ⚠️ RECOMMENDED - May be needed for thread operations
view_channel                # ✅ Assumed to be present (bot must see channel)
```

### Potentially Unnecessary Permissions
```python
create_public_threads       # ⚠️ NOT USED - Only private threads are created
```

## @everyone Role Restrictions Analysis

### Currently Checked Restrictions ✅
```python
EVERYONE_RESTRICTIONS: List[PermissionRequirement] = [
    send_messages,              # ✅ Correct - prevents @everyone from posting
    create_public_threads,      # ✅ Correct - prevents public threads
    create_private_threads,     # ✅ Correct - prevents private threads
]
```

**Justification**: These restrictions make sense because:
1. Users should only interact via bot buttons (ephemeral messages)
2. All threads are created by the bot, not users
3. Prevents channel clutter and ensures controlled flow

### Additional Restrictions to Consider ⚠️
```python
# These might also be useful:
add_reactions              # Prevent @everyone from reacting to messages
attach_files               # Prevent @everyone from uploading files
```

## Recommendations

### CRITICAL: Update Bot Required Permissions
The configuration **MUST** be updated to include:

```python
BOT_REQUIRED_PERMISSIONS: List[PermissionRequirement] = [
    PermissionRequirement(
        permission_name="send_messages",
        description="Bot cannot send messages (required)",
        required=True
    ),
    PermissionRequirement(
        permission_name="send_messages_in_threads",
        description="Bot cannot send messages in threads (required)",
        required=True
    ),
    PermissionRequirement(
        permission_name="embed_links",
        description="Bot cannot embed links (required for rich embeds)",
        required=True
    ),
    PermissionRequirement(
        permission_name="manage_threads",
        description="Bot cannot manage threads (required)",
        required=True
    ),
    PermissionRequirement(
        permission_name="create_private_threads",
        description="Bot cannot create private threads (required)",
        required=True
    ),
    PermissionRequirement(
        permission_name="read_message_history",
        description="Bot cannot read message history (recommended)",
        required=False  # Not strictly required but recommended
    ),
]
```

### OPTIONAL: Remove Unnecessary Permission
Consider removing `create_public_threads` since the bot only creates **private** threads:
```python
# REMOVE THIS - not actually used:
create_public_threads
```

### OPTIONAL: Additional @everyone Restrictions
Consider adding these restrictions for better channel control:
```python
EVERYONE_RESTRICTIONS: List[PermissionRequirement] = [
    # ... existing restrictions ...
    PermissionRequirement(
        permission_name="add_reactions",
        description="@everyone role can add reactions (recommended to disable)",
        required=False  # Not critical, but cleaner
    ),
]
```

## Impact of Missing Permissions

### If `send_messages` is missing:
- ❌ Bot **CANNOT** post tournament embed via `/async_post_embed`
- ❌ Bot **CANNOT** send countdown messages (10, 9, 8...)
- ❌ Bot **CANNOT** send "GO!" message
- ⚠️ Users will see permission errors

### If `send_messages_in_threads` is missing:
- ❌ Bot **CANNOT** post race info in newly created thread
- ❌ Bot **CANNOT** send race instructions
- ⚠️ Threads will be created but empty/broken

### If `embed_links` is missing:
- ⚠️ Bot messages will be plain text (ugly, less functional)
- ⚠️ Race information will be harder to read

### If `manage_threads` is missing:
- ❌ Bot **CANNOT** add users to created threads
- ⚠️ Users won't be able to see their own race threads!

## Testing Checklist

To verify permissions are correct, test these scenarios:

- [ ] Bot can post embed with `/async_post_embed` command
- [ ] User can click "Start New Async Run" button
- [ ] Bot creates private thread successfully
- [ ] Bot adds user to the thread
- [ ] Bot posts race information in thread (embed + message)
- [ ] User can click "Ready" button
- [ ] Bot sends countdown messages (10, 9, 8...)
- [ ] Bot sends "GO!" message with action buttons
- [ ] User can finish/forfeit race
- [ ] Bot can edit messages (disable buttons)

## Summary

**Current Status**: ⚠️ **INCOMPLETE - Missing Critical Permissions**

**Missing Critical Permissions**:
1. ✅ `send_messages` - **MUST ADD**
2. ✅ `send_messages_in_threads` - **MUST ADD**
3. ✅ `embed_links` - **MUST ADD**

**Unnecessary Permissions**:
1. `create_public_threads` - **SHOULD REMOVE** (not used)

**@everyone Restrictions**: ✅ **Correct as-is** (or add optional reaction/file restrictions)
