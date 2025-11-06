# User Impersonation Feature Implementation

## Overview

This implementation adds a secure user impersonation feature that allows SUPERADMIN users to temporarily view the application as another user. All impersonation actions are fully audit logged.

## Architecture

### Security Model

- **Permission Requirement**: Only `SUPERADMIN` users can impersonate
- **Self-Impersonation Protection**: Users cannot impersonate themselves
- **Audit Logging**: All start/stop impersonation actions are logged with:
  - Admin user who initiated impersonation
  - Target user being impersonated
  - Timestamps
  - IP addresses (where available)

### Session Management

Impersonation works by maintaining both the original user and impersonated user in the session:

```python
# Session storage structure
app.storage.user = {
    'user_id': 123,              # Original logged-in user
    'discord_id': 456789,        # Original user's Discord ID
    'permission': 200,           # Original user's permission
    
    # Added during impersonation
    'impersonated_user_id': 789,      # User being impersonated
    'impersonated_discord_id': 987654, # Impersonated user's Discord ID
    'impersonated_permission': 0       # Impersonated user's permission
}
```

## Components

### 1. Service Layer (`application/services/core/user_service.py`)

**Methods Added:**

- `start_impersonation(admin_user, target_user_id, ip_address)` - Initiates impersonation with validation and audit logging
- `stop_impersonation(original_user, impersonated_user, ip_address)` - Ends impersonation with audit logging

**Business Logic:**
- Validates SUPERADMIN permission
- Prevents self-impersonation
- Verifies target user exists
- Creates audit log entries

### 2. Authentication Middleware (`middleware/auth.py`)

**Methods Modified:**

- `get_current_user()` - Returns impersonated user when active, falls back to original user
- `get_original_user()` - Always returns the actual logged-in user (bypasses impersonation)
- `is_impersonating()` - Check if impersonation is currently active

**Methods Added:**

- `start_impersonation(target_user)` - Sets impersonation data in session
- `stop_impersonation()` - Clears impersonation data from session

### 3. API Endpoints (`api/routes/users.py`)

**POST `/api/users/admin/impersonate/{user_id}`**
- Start impersonating a user
- Requires SUPERADMIN permission
- Returns the target user on success
- Returns 403 if unauthorized, 404 if user not found

**POST `/api/users/admin/stop-impersonation`**
- Stop impersonating and return to original user
- Returns the original user on success
- Returns 400 if not currently impersonating

### 4. Admin UI (`views/admin/admin_users.py`)

**Features Added:**

- "Impersonate" button in user list (person_search icon)
  - Only visible to SUPERADMIN users
  - Hidden for own user (can't impersonate yourself)
- `_impersonate_user(user)` method
  - Calls service layer to validate and start impersonation
  - Updates session
  - Redirects to home page to show banner

### 5. User Menu (`components/user_menu.py`)

**Features Added:**

- "Stop Impersonation" menu option
  - Only visible when impersonation is active
  - Appears at top of menu with separator
  - Calls service layer for audit logging
  - Clears session and redirects to home

### 6. Impersonation Banner (`components/base_page.py`)

**Visual Indicator:**

- Orange warning banner appears below header when impersonating
- Shows:
  - Warning icon
  - "IMPERSONATING: {impersonated_username} (Logged in as: {original_username})"
  - "Stop Impersonation" button
- Highly visible to prevent confusion
- Present on ALL pages when impersonating

## Usage Flow

### Starting Impersonation

1. SUPERADMIN navigates to Admin → User Management
2. Clicks "Impersonate" button (person_search icon) on target user
3. System validates permissions and user existence
4. Audit log entry created: `impersonation_started`
5. Session updated with impersonation data
6. User redirected to home page
7. Orange banner appears on all pages

### While Impersonating

- All UI interactions behave as the impersonated user
- Permissions are those of the impersonated user
- Organization memberships are those of the impersonated user
- Banner remains visible on all pages
- User menu shows "Stop Impersonation" option

### Stopping Impersonation

**Method 1: User Menu**
1. Click user menu in header
2. Click "Stop Impersonation"
3. Audit log entry created: `impersonation_stopped`
4. Session cleared of impersonation data
5. Redirected to home page as original user

**Method 2: Banner Button**
1. Click "Stop Impersonation" in orange banner
2. Same flow as Method 1

## Audit Log Entries

### Impersonation Started
```json
{
  "user_id": 123,  // Admin who started impersonation
  "action": "impersonation_started",
  "details": {
    "target_user_id": 789,
    "target_username": "some_user",
    "target_permission": "USER"
  },
  "ip_address": "192.168.1.1",
  "timestamp": "2025-11-06T12:00:00Z"
}
```

### Impersonation Stopped
```json
{
  "user_id": 123,  // Admin who stopped impersonation
  "action": "impersonation_stopped",
  "details": {
    "impersonated_user_id": 789,
    "impersonated_username": "some_user"
  },
  "ip_address": "192.168.1.1",
  "timestamp": "2025-11-06T12:30:00Z"
}
```

## Security Considerations

### Authentication & Authorization

- **SUPERADMIN Only**: Only the highest permission level can impersonate
- **Self-Protection**: Cannot impersonate yourself
- **Session Isolation**: Original user session preserved during impersonation
- **Audit Trail**: Complete logging of all impersonation actions

### Transparency

- **Visual Warning**: Orange banner prevents confusion about current identity
- **Easy Exit**: Multiple ways to stop impersonation (menu, banner)
- **Username Display**: Shows both impersonated and original usernames

### Data Protection

- **No Token Sharing**: Impersonation uses session, not OAuth tokens
- **Permission Enforcement**: All existing authorization checks still apply
- **Organization Scoping**: Multi-tenant isolation maintained

## Testing Checklist

- [ ] SUPERADMIN can impersonate regular users
- [ ] SUPERADMIN can impersonate ADMIN users
- [ ] SUPERADMIN cannot impersonate themselves
- [ ] ADMIN users cannot impersonate (permission denied)
- [ ] Regular users cannot impersonate (permission denied)
- [ ] Impersonation banner appears on all pages
- [ ] "Stop Impersonation" in user menu works
- [ ] "Stop Impersonation" in banner works
- [ ] Audit logs created for start impersonation
- [ ] Audit logs created for stop impersonation
- [ ] Permissions match impersonated user while active
- [ ] Session returns to original user after stopping
- [ ] Cannot access impersonation UI elements when not SUPERADMIN
- [ ] API endpoints enforce SUPERADMIN requirement
- [ ] Impersonating deleted user stops gracefully

## Future Enhancements

Potential improvements:

1. **Impersonation History**: View past impersonation sessions in admin panel
2. **Time Limits**: Auto-expire impersonation after X hours
3. **Reason Tracking**: Require reason when starting impersonation
4. **Enhanced Notifications**: Email/Discord notify user when impersonated
5. **Restrictions**: Configure which users can/cannot be impersonated
6. **Session Tracking**: Show impersonation status in all audit logs during session

## Files Modified

### Service Layer
- `application/services/core/user_service.py` - Added impersonation methods

### Middleware
- `middleware/auth.py` - Added session management for impersonation

### API
- `api/routes/users.py` - Added impersonation endpoints

### UI Components
- `components/base_page.py` - Added impersonation banner
- `components/user_menu.py` - Added stop impersonation option

### Views
- `views/admin/admin_users.py` - Added impersonate button to user list

## API Documentation

The impersonation endpoints are automatically documented in Swagger UI at `/docs`:

- `POST /api/users/admin/impersonate/{user_id}` - Start impersonation
- `POST /api/users/admin/stop-impersonation` - Stop impersonation

---

**Implementation Date**: November 6, 2025
**Author**: AI Assistant
**Status**: Complete - Ready for Testing
