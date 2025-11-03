# RaceTime.gg OAuth2 Integration Implementation Summary

## Overview
This implementation adds RaceTime.gg OAuth2 account linking functionality to SahaBot2, allowing users to link their RaceTime.gg accounts to their Discord-authenticated profiles.

## Implementation Details

### Database Schema
Added three new fields to the `users` table:
- `racetime_id` (VARCHAR, unique, indexed) - RaceTime.gg user ID
- `racetime_name` (VARCHAR) - RaceTime.gg username
- `racetime_access_token` (LONGTEXT) - OAuth2 access token for API access

Migration: `migrations/models/8_20251102185717_update.py`

### Configuration
Added new settings in `config.py`:
- `RACETIME_CLIENT_ID` - OAuth2 client ID for user account linking
- `RACETIME_CLIENT_SECRET` - OAuth2 client secret
- `RACETIME_OAUTH_REDIRECT_URI` - OAuth callback URL
- `RACETIME_URL` - RaceTime.gg base URL (default: https://racetime.gg)

### OAuth Service Layer
**File**: `middleware/racetime_oauth.py`

Implements `RacetimeOAuthService` class with:
- `get_authorization_url(state)` - Generate OAuth authorization URL
- `exchange_code_for_token(code)` - Exchange authorization code for access token
- `get_user_info(access_token)` - Retrieve user information from RaceTime.gg

Security features:
- CSRF protection via state parameter
- Sanitized error logging (no sensitive info exposure)
- Proper error handling with HTTPStatusError

### Repository Layer
**File**: `application/repositories/user_repository.py`

Added method:
- `get_by_racetime_id(racetime_id)` - Retrieve user by RaceTime.gg ID

### Service Layer
**File**: `application/services/user_service.py`

Added methods:
- `link_racetime_account(user, racetime_id, racetime_name, access_token)` - Link account
  - Validates account is not already linked to another user
  - Updates user record with RaceTime information
  - Returns updated user object
  
- `unlink_racetime_account(user)` - Unlink account
  - Clears RaceTime fields from user record
  - Returns updated user object

### OAuth Pages
**File**: `pages/racetime_oauth.py`

Two NiceGUI pages for the OAuth flow:

1. **GET /racetime/link/initiate**
   - Starts OAuth flow
   - Requires Discord authentication (redirects to login if not authenticated)
   - Generates CSRF state token
   - Stores state in browser storage (with timestamp and user ID)
   - Redirects to RaceTime.gg authorization page

2. **GET /racetime/link/callback**
   - Handles OAuth callback from RaceTime.gg
   - Verifies CSRF state token
   - Exchanges authorization code for access token
   - Retrieves user info from RaceTime.gg
   - Links account via service layer
   - Displays success/error message
   - Provides button to navigate back to profile

### API Routes
**File**: `api/routes/racetime.py`

Two API endpoints for account status:

1. **GET /api/racetime/link/status**
   - Returns current user's link status
   - Requires authentication (Bearer token)
   - Rate limited

2. **POST /api/racetime/link/unlink**
   - Unlinks RaceTime account
   - Requires authentication (Bearer token)
   - Rate limited

OAuth flow is handled via NiceGUI pages (see OAuth Pages section above).

### UI Components
**File**: `views/user_profile/racetime_account.py`

Implements `RacetimeAccountView` class that displays:
- Account link status (linked/not linked)
- RaceTime username and ID (when linked)
- "Link Account" button with benefits list (when not linked)
- "Unlink Account" button with confirmation dialog (when linked)

Features:
- Mobile-responsive design using Card component
- Proper icon usage for visual feedback
- Service layer integration for unlinking
- User feedback via notifications

**File**: `pages/user_profile.py`

Updated to include RaceTime tab in profile sidebar:
- New sidebar item: "RaceTime.gg" with timer icon
- Dynamic content loading for the RaceTime view

### Tests
**File**: `tests/unit/test_racetime_oauth.py`

Unit tests for:
- OAuth URL generation
- Token exchange (success and failure)
- User info retrieval
- Account linking (success and duplicate detection)
- Account unlinking

**File**: `tests/integration/test_racetime_oauth.py`

Integration test placeholders for:
- Complete OAuth flow
- CSRF protection
- Authentication requirements
- Error handling

### Documentation
**File**: `README.md`

Added:
- RaceTime.gg integration feature in features list
- Configuration instructions for OAuth2 setup
- Instructions for creating OAuth application on RaceTime.gg

## Security Features

1. **CSRF Protection**
   - State parameter generated using `secrets.token_urlsafe(32)`
   - State stored in session during initiation
   - State verified on callback (both must be present and match)

2. **Authentication**
   - Session-based authentication for OAuth flow
   - User ID validated on callback
   - Service layer enforces business rules

3. **Error Handling**
   - Sanitized error messages (no sensitive data exposure)
   - Proper logging without OAuth provider error details
   - Generic error messages to users

4. **Data Validation**
   - Prevents duplicate account linking
   - Validates user existence before linking
   - Proper error propagation with meaningful messages

## Architecture Compliance

The implementation follows SahaBot2 architectural principles:

✅ **Separation of Concerns**
- OAuth logic in middleware
- Business logic in services
- Data access in repositories
- UI in views/pages

✅ **Async/Await**
- All async operations properly awaited
- Async context managers for HTTP clients

✅ **Type Hints & Docstrings**
- Comprehensive docstrings for all public methods
- Type hints on parameters and returns

✅ **Logging Standards**
- Lazy % formatting in all logging statements
- Appropriate log levels (info, warning, error)
- No print() statements in application code

✅ **Mobile-First Design**
- Responsive Card-based UI
- Works on all device sizes

✅ **External CSS**
- No inline styles
- Uses existing CSS classes

## OAuth Flow Diagram

```
User → /profile (RaceTime tab)
  ↓
User clicks "Link Account"
  ↓
/racetime/link/initiate (NiceGUI page)
  • Check Discord authentication
  • Generate state token
  • Store in browser storage (with user ID + timestamp)
  ↓
Redirect to RaceTime.gg
  ↓
User authorizes on RaceTime.gg
  ↓
/racetime/link/callback (NiceGUI page)
  • Verify state (CSRF)
  • Exchange code for token
  • Get user info
  • Link account via service
  ↓
Display success/error message
  ↓
User clicks "Go to Profile"
  ↓
/profile → Display linked account info
```

## Testing Checklist

For manual testing, verify:

- [ ] Link initiation redirects to RaceTime.gg
- [ ] OAuth callback successfully links account
- [ ] CSRF protection rejects mismatched state
- [ ] Duplicate linking is prevented
- [ ] Unlink functionality works correctly
- [ ] UI displays correct link status
- [ ] Mobile responsiveness
- [ ] Error handling for various failure scenarios
- [ ] Session persistence across OAuth flow
- [ ] Database correctly stores RaceTime data

## Future Enhancements

Potential improvements for future iterations:

1. **Token Refresh**
   - Implement OAuth2 token refresh flow
   - Store refresh tokens securely
   - Auto-refresh expired tokens

2. **RaceTime API Integration**
   - Use stored access tokens for RaceTime API calls
   - Fetch user's race history
   - Display race statistics in profile

3. **Race Management**
   - Create races from SahaBot2
   - Track race participants
   - Sync race results

4. **Admin Features**
   - View all linked accounts
   - Unlink accounts administratively
   - Link statistics/analytics

## References

- Original SahasrahBot implementation: https://github.com/tcprescott/sahasrahbot/blob/main/alttprbot_api/blueprints/racetime.py
- RaceTime.gg OAuth2 docs: https://github.com/racetimeGG/racetime-app/wiki/OAuth2-applications
- RaceTime.gg Developer Portal: https://racetime.gg/account/dev
