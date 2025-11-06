# Twitch Integration Guide

## Overview
This document covers SahaBot2's integration with Twitch, including OAuth2 account linking for user authentication and profile management.

## OAuth2 Account Linking

### Overview
This implementation adds Twitch OAuth2 account linking functionality to SahaBot2, allowing users to link their Twitch accounts to their Discord-authenticated profiles. This enables Twitch-based features such as stream integration, notifications, and broadcaster verification.

## Implementation Details

### Database Schema
Added fields to the `users` table:
- `twitch_id` (VARCHAR, unique, indexed) - Twitch user ID
- `twitch_name` (VARCHAR) - Twitch username (lowercase)
- `twitch_display_name` (VARCHAR) - Twitch display name (with capitalization)
- `twitch_access_token` (LONGTEXT) - OAuth2 access token for API access
- `twitch_refresh_token` (LONGTEXT) - OAuth2 refresh token for token renewal
- `twitch_token_expires_at` (DATETIME) - Access token expiration timestamp

**Note**: Database migrations are handled separately by maintainers.

### Configuration
Added new settings in `config.py`:
- `TWITCH_CLIENT_ID` - OAuth2 client ID for user account linking
- `TWITCH_CLIENT_SECRET` - OAuth2 client secret
- `TWITCH_OAUTH_REDIRECT_URI` - OAuth callback URL (defaults to `{BASE_URL}/twitch/link/callback`)

Environment variables (`.env`):
```bash
TWITCH_CLIENT_ID=your_twitch_client_id
TWITCH_CLIENT_SECRET=your_twitch_client_secret
TWITCH_OAUTH_REDIRECT_URI=http://localhost:8080/twitch/link/callback  # Optional
```

### OAuth Service Layer
**File**: `middleware/twitch_oauth.py`

Implements `TwitchOAuthService` class with:
- `get_authorization_url(state)` - Generate OAuth authorization URL
- `exchange_code_for_token(code)` - Exchange authorization code for access token
- `refresh_access_token(refresh_token)` - Refresh expired access tokens
- `calculate_token_expiry(expires_in)` - Calculate token expiration timestamp
- `get_user_info(access_token)` - Retrieve user information from Twitch

OAuth Configuration:
- **Authorization URL**: `https://id.twitch.tv/oauth2/authorize`
- **Token URL**: `https://id.twitch.tv/oauth2/token`
- **User Info URL**: `https://api.twitch.tv/helix/users`
- **Scopes**: No email scope (per requirements) - only basic user identification
- **Token Expiry**: 4 hours (Twitch default)

Security features:
- CSRF protection via state parameter
- Sanitized error logging (no sensitive info exposure)
- Proper error handling with HTTPStatusError
- Timezone-aware datetime handling

### Repository Layer
**File**: `application/repositories/user_repository.py`

Added methods:
- `get_by_twitch_id(twitch_id)` - Retrieve user by Twitch ID
- `get_users_with_twitch(include_inactive, limit, offset)` - Get users with linked Twitch accounts
- `count_twitch_linked_users(include_inactive)` - Count users with linked accounts
- `search_by_twitch_name(query)` - Search users by Twitch username

### Service Layer
**File**: `application/services/core/user_service.py`

Added methods:
- `link_twitch_account(user, twitch_id, twitch_name, twitch_display_name, access_token, refresh_token, expires_at)` - Link account
  - Validates account is not already linked to another user
  - Updates user record with Twitch information
  - Stores access token, refresh token, and expiration
  - Returns updated user object

- `refresh_twitch_token(user)` - Refresh expired access token
  - Uses refresh token to obtain new access token
  - Updates token and expiration in database
  - Returns updated user object

- `unlink_twitch_account(user)` - Unlink account
  - Removes all Twitch information from user record
  - Returns updated user object

Admin methods:
- `admin_unlink_twitch_account(user_id, admin_user)` - Admin force-unlink
  - Requires ADMIN permission
  - Logs audit trail
  - Returns None if unauthorized

- `get_all_twitch_accounts(admin_user, limit, offset)` - List linked accounts
  - Requires ADMIN permission
  - Returns empty list if unauthorized

- `search_twitch_accounts(admin_user, query)` - Search linked accounts
  - Requires ADMIN permission
  - Returns empty list if unauthorized

- `get_twitch_link_statistics(admin_user)` - Get linking statistics
  - Requires ADMIN permission
  - Returns empty dict if unauthorized

### NiceGUI Pages
**File**: `pages/twitch_oauth.py`

Implements OAuth flow pages:
- `/twitch/link/initiate` - Start OAuth flow
  - Requires authentication
  - Generates CSRF state token
  - Stores state in browser storage with timestamp
  - Redirects to Twitch authorization URL

- `/twitch/link/callback` - OAuth callback handler
  - Validates CSRF state token
  - Checks state expiration (10 minute timeout)
  - Exchanges code for tokens
  - Retrieves user info from Twitch
  - Links account via service layer
  - Displays success/error UI

CSRF Protection:
- State tokens generated with `secrets.token_urlsafe(32)`
- Stored in browser storage with timestamp
- 10-minute expiration window
- Automatically cleaned up after use

### User Profile View
**File**: `views/user_profile/twitch_account.py`

Implements `TwitchAccountView` class:
- Displays link status (linked/unlinked)
- Shows Twitch display name, username, and ID
- Provides link to Twitch profile (opens in new tab)
- Link/unlink buttons
- Integration benefits information

Features:
- Confirmation dialog before unlinking
- Success/error notifications
- Automatic page reload after unlink

### API Endpoints
**File**: `api/routes/twitch.py`

Public endpoints:
- `GET /api/twitch/link/status` - Get current user's link status
  - Returns: `linked`, `twitch_id`, `twitch_name`, `twitch_display_name`

- `POST /api/twitch/link/unlink` - Unlink current user's account
  - Requires authentication
  - Returns success message

Admin endpoints (require ADMIN permission):
- `GET /api/twitch/admin/accounts` - List all linked accounts
  - Parameters: `limit`, `offset` (pagination)
  - Returns list of accounts with user info

- `GET /api/twitch/admin/stats` - Get linking statistics
  - Returns: `total_users`, `linked_users`, `unlinked_users`, `link_percentage`

- `POST /api/twitch/admin/unlink/{user_id}` - Force-unlink user account
  - Requires ADMIN permission
  - Logs audit trail

### Testing
**File**: `tests/integration/test_twitch_oauth.py`

Comprehensive test coverage:
- OAuth flow initialization and URL generation
- Successful callback and account linking
- CSRF state validation
- Duplicate account prevention
- Account unlinking
- Token refresh
- Admin operations and authorization
- Statistics retrieval

All tests follow existing RaceTime OAuth test patterns for consistency.

## Usage

### For Users
1. Navigate to Profile → Twitch Account
2. Click "Link Twitch Account"
3. Authorize on Twitch
4. Redirected back with linked account

### For Administrators
Use API endpoints to:
- View all linked accounts
- Get statistics
- Force-unlink accounts if needed

## Security Considerations

1. **Token Storage**: Tokens stored in database (not logged or exposed)
2. **CSRF Protection**: State tokens with 10-minute expiration
3. **No Email Collection**: Per requirements, no email scope requested
4. **Authorization Checks**: Admin operations require ADMIN permission
5. **Audit Logging**: All admin actions logged
6. **Error Handling**: Sensitive info sanitized from logs

## Architecture Decisions

1. **Followed RaceTime Pattern**: Maintains consistency with existing OAuth implementation
2. **Service Layer**: All business logic in service layer (no ORM in pages/API)
3. **External Links**: Twitch profile links open in new tabs per coding standards
4. **Timezone-Aware**: All timestamps use timezone-aware datetimes
5. **Graceful Degradation**: Authorization failures return empty results, not errors
6. **Minimal Scopes**: Only request what's needed for basic user identification

## Future Enhancements

Potential features (not implemented):
- Stream status detection
- Twitch notifications
- Broadcaster verification
- VOD integration
- Clip management
- Chat integration

## Troubleshooting

### Common Issues

**OAuth fails with "Invalid state token"**:
- Cookies may be disabled in browser
- User took too long (>10 minutes)
- Browser storage cleared during flow

**"Account already linked" error**:
- Twitch account already linked to different user
- Admin must unlink first before re-linking

**Token refresh fails**:
- Refresh token may be expired or revoked
- User must re-link account

### Logging
All OAuth operations logged at INFO level:
- User initiating link
- Successful link
- Unlink operations
- Admin actions

Errors logged at ERROR level with sanitized details.

## References
- Twitch OAuth Documentation: https://dev.twitch.tv/docs/authentication
- RaceTime Integration: `docs/integrations/RACETIME_INTEGRATION.md`
- Architecture Guide: `docs/ARCHITECTURE.md`
- Patterns &amp; Conventions: `docs/PATTERNS.md`
