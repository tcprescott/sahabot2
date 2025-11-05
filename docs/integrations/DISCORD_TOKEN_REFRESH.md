# Discord OAuth2 Automatic Token Refresh

## Overview

SahaBot2 implements automatic Discord OAuth2 token refresh to provide seamless user authentication without requiring manual re-login when access tokens expire. This feature improves user experience by transparently refreshing tokens in the background.

## Architecture

### Token Storage

Discord OAuth2 tokens are stored securely in the database:

**User Model Fields** (`models/user.py`):
- `discord_access_token` (TextField, nullable) - Current access token for Discord API calls
- `discord_refresh_token` (TextField, nullable) - Refresh token for obtaining new access tokens
- `discord_token_expires_at` (DatetimeField, nullable) - UTC timestamp when access token expires

### Token Lifecycle

```
User Login → Exchange Code for Tokens → Store Tokens in DB
                                              ↓
                                        Set Expiration
                                              ↓
User Request → Check Token Expiration → Expired?
                                              ↓
                                         Yes  |  No
                                              ↓
                                    Refresh Token → Update DB
                                              ↓
                                         Continue Request
```

### Automatic Refresh Flow

1. **On Login** (`middleware/auth.py::authenticate_user()`):
   - Exchange authorization code for tokens
   - Extract `access_token`, `refresh_token`, `expires_in`
   - Calculate expiration timestamp (UTC)
   - Store all token data in user record

2. **On Every Request** (`middleware/auth.py::get_current_user()`):
   - Fetch user from database
   - Check if token is expired or expiring soon (5-minute buffer)
   - If expired:
     - Call `refresh_discord_token()` to get new tokens
     - Update user record with new tokens and expiration
     - Return user with fresh tokens
   - If refresh fails:
     - Clear user session
     - Return None (forces re-login)

3. **Token Refresh** (`middleware/auth.py::refresh_discord_token()`):
   - POST to Discord OAuth2 token endpoint
   - Use `grant_type=refresh_token`
   - Receive new `access_token`, `refresh_token`, `expires_in`
   - Return token data for storage

## Implementation Details

### DiscordAuthService Methods

#### `refresh_discord_token(refresh_token: str) -> Dict[str, Any]`
Exchanges a refresh token for new access token and refresh token.

**Parameters**:
- `refresh_token`: Discord refresh token

**Returns**:
- Dictionary with `access_token`, `refresh_token`, `expires_in`

**Raises**:
- `httpx.HTTPStatusError`: If token refresh fails (invalid/revoked refresh token)

#### `calculate_token_expiry(expires_in: int) -> datetime`
Calculates token expiration timestamp from `expires_in` seconds.

**Parameters**:
- `expires_in`: Seconds until token expires

**Returns**:
- Timezone-aware UTC datetime of expiration

#### `is_discord_token_expired(user: User, buffer_minutes: int = 5) -> bool`
Checks if user's Discord token is expired or expiring soon.

**Parameters**:
- `user`: User to check token for
- `buffer_minutes`: Minutes before expiration to consider token expired (default: 5)

**Returns**:
- `True` if token is expired or will expire within buffer time
- `True` if no expiration time is set (needs refresh)
- `False` if token is still valid

**Why 5-minute buffer?**
- Prevents token from expiring mid-request
- Allows time for API calls to complete
- Reduces race conditions

### UserService Methods

#### `update_discord_tokens(user, access_token, refresh_token, expires_at) -> User`
Updates Discord OAuth2 tokens for a user.

**Called**: After initial login to store tokens

#### `refresh_discord_token(user: User) -> User`
Refreshes Discord access token for a user using their refresh token.

**Called**: Automatically by `get_current_user()` when token is expired

**Error Handling**:
- If user has no refresh token: raises `ValueError`
- If refresh fails: raises `httpx.HTTPError`

## Security Considerations

### Token Storage
- Tokens are stored as `TextField` in MySQL (supports large token strings)
- Database should be secured with proper access controls
- Consider encrypting tokens at rest in production environments

### Token Expiration
- 5-minute buffer prevents mid-request expiration
- Tokens are refreshed preemptively before they expire
- No user action required for refresh

### Refresh Token Rotation
Discord rotates refresh tokens on each refresh:
- New refresh token returned with each token refresh
- Old refresh token is invalidated
- Implementation automatically updates to new refresh token

### Session Management
- Session only stores `user_id`, not tokens
- Tokens fetched fresh from database on each request
- Expired/invalid refresh tokens clear session (forces re-login)

## Error Handling

### Token Refresh Failure
**Causes**:
- Refresh token revoked by user
- Refresh token expired (Discord revokes after ~30 days of non-use)
- Network/API errors

**Behavior**:
1. Log warning with user ID and error message
2. Clear user session (`app.storage.user.clear()`)
3. Return `None` from `get_current_user()`
4. User is redirected to login page on next request

### Token Not Stored
**Causes**:
- User logged in before token refresh feature was implemented
- Database migration not applied

**Behavior**:
- `is_discord_token_expired()` returns `True` (no expiration time)
- Token refresh is attempted
- If no refresh token: error logged, session cleared
- User must re-login to get new tokens

## Migration from Legacy

### For Existing Users
Users who logged in before this feature was implemented will not have tokens stored. On their next visit:

1. `get_current_user()` checks token expiration
2. No `discord_token_expires_at` → considered expired
3. Refresh attempted but no `discord_refresh_token`
4. Error logged, session cleared
5. User redirected to login page
6. New login stores tokens for future automatic refresh

### Database Migration
Migration `42_20251104223718_add_discord_oauth_token_fields.py`:
- Adds `discord_access_token` (nullable)
- Adds `discord_refresh_token` (nullable)
- Adds `discord_token_expires_at` (nullable)

All fields nullable to support existing users.

## Testing

### Test Scenarios

1. **Normal Login**:
   - User logs in via Discord OAuth2
   - Tokens stored in database
   - Expiration calculated and stored

2. **Automatic Refresh**:
   - User returns after token expiration
   - `get_current_user()` detects expired token
   - Refresh happens automatically
   - User continues without re-login

3. **Refresh Token Expiration**:
   - User returns after long absence (>30 days)
   - Refresh token is invalid/expired
   - Session cleared
   - User redirected to login

4. **Concurrent Requests**:
   - Multiple requests check same expired token
   - All refresh attempts should succeed (Discord allows this)
   - Last refresh wins (updates token)

### Manual Testing

```python
# Test token expiration check
from middleware.auth import DiscordAuthService
from models import User

user = await User.get(id=1)
is_expired = DiscordAuthService.is_discord_token_expired(user)
print(f"Token expired: {is_expired}")

# Test token refresh
from application.services.user_service import UserService

user_service = UserService()
try:
    refreshed_user = await user_service.refresh_discord_token(user)
    print(f"Refresh successful: {refreshed_user.discord_token_expires_at}")
except Exception as e:
    print(f"Refresh failed: {e}")
```

## Performance Impact

### Additional Database Queries
- Each request: 1 additional check for token expiration (in-memory datetime comparison)
- Token refresh: 1 update query (only when token expires)

### Network Requests
- Token refresh: 1 POST request to Discord OAuth2 endpoint (only when token expires)

### Frequency
- Initial token: ~7 days validity
- Refresh happens: ~every 7 days per user (with 5-minute buffer)
- Negligible performance impact

## Future Enhancements

Potential improvements:
1. **Token Encryption**: Encrypt tokens at rest in database
2. **Caching**: Cache valid tokens in Redis to reduce database queries
3. **Batch Refresh**: Background task to proactively refresh tokens before expiration
4. **Metrics**: Track refresh success/failure rates
5. **Admin UI**: View token status for users in admin panel

## References

- Discord OAuth2 Documentation: https://discord.com/developers/docs/topics/oauth2
- RFC 6749 (OAuth 2.0): https://tools.ietf.org/html/rfc6749
- Original Implementation: Similar to RaceTime.gg token refresh in `middleware/racetime_oauth.py`

---

**Last Updated**: November 4, 2025
