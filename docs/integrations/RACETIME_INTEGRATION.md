# RaceTime.gg Integration Guide

## Overview
This document covers SahaBot2's integration with RaceTime.gg, including OAuth2 account linking, bot client functionality, and race room management.

## Important: Automatic Polling Disabled

**SahaBot2 does NOT use automatic race room polling**. The RaceTime bot client explicitly disables the `refresh_races()` polling mechanism from the upstream library. Instead, race rooms are joined explicitly via:

- **Task Scheduler System** - Schedule race room creation/joining at specific times
- **Manual Commands** - Discord bot commands like `!startrace`
- **API Calls** - Programmatic race room creation via `bot.startrace()` or `bot.join_race_room()`

**See**: [`RACETIME_POLLING_DISABLED.md`](RACETIME_POLLING_DISABLED.md) for detailed explanation of this architectural decision.

---

## OAuth2 Account Linking

### Overview
This implementation adds RaceTime.gg OAuth2 account linking functionality to SahaBot2, allowing users to link their RaceTime.gg accounts to their Discord-authenticated profiles.

## Implementation Details

### Database Schema
Added fields to the `users` table:
- `racetime_id` (VARCHAR, unique, indexed) - RaceTime.gg user ID
- `racetime_name` (VARCHAR) - RaceTime.gg username
- `racetime_access_token` (LONGTEXT) - OAuth2 access token for API access
- `racetime_refresh_token` (LONGTEXT) - OAuth2 refresh token for token renewal
- `racetime_token_expires_at` (DATETIME) - Access token expiration timestamp

Migrations:
- Initial fields: `migrations/models/8_20251102185717_update.py`
- Token refresh: `migrations/models/38_20251104215452_add_racetime_token_refresh.py`

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
- `refresh_access_token(refresh_token)` - Refresh expired access tokens
- `calculate_token_expiry(expires_in)` - Calculate token expiration timestamp
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
- `link_racetime_account(user, racetime_id, racetime_name, access_token, refresh_token, expires_at)` - Link account
  - Validates account is not already linked to another user
  - Updates user record with RaceTime information
  - Stores access token, refresh token, and expiration
  - Returns updated user object

- `refresh_racetime_token(user)` - Refresh expired access token
  - Uses refresh token to obtain new access token
  - Updates token and expiration in database
  - Returns updated user object

- `unlink_racetime_account(user)` - Unlink account
  - Clears all RaceTime fields from user record
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

### RaceTime API Service
**File**: `application/services/racetime_api_service.py`

Service for making authenticated API calls to RaceTime.gg:
- `get_user_data(user)` - Get RaceTime user profile data
- `get_user_races(user, category, show_entrants)` - Get all races for a user
- `get_user_stats(user, category)` - Get user statistics for a category
- `get_race_data(user, race_name)` - Get detailed data for a specific race
- `get_past_races(user, category, limit)` - Get paginated past races

Features:
- Automatic token refresh when tokens are expired or expiring soon (5 minute buffer)
- Transparent error handling and logging
- Efficient connection pooling with httpx.AsyncClient
- Category filtering and pagination support

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

Updated to include RaceTime account linking in profile sidebar:
- "RaceTime Account" tab with link icon - Account linking/unlinking

Dynamic content loading for RaceTime account view.

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

1. **Race Management**
   - Create races from SahaBot2
   - Track race participants
   - Sync race results to database
   - Real-time race monitoring

2. **Race History Display**
   - Display user's race history from RaceTime.gg API
   - Category filtering and search
   - Detailed race statistics
   - Leaderboard comparisons
   - Personal best tracking

3. **Performance Optimizations**
   - Cache race data locally
   - More category filters
   - Advanced filtering options

## Admin Features

### Overview
Administrators can view and manage all RaceTime linked accounts through the admin panel. All admin operations are logged for audit purposes.

### Admin View
**File**: `views/admin/racetime_accounts.py`

The `RacetimeAccountsView` provides:
- Statistics dashboard showing:
  - Total users
  - Linked accounts count
  - Unlinked accounts count
  - Link percentage
- Search functionality by RaceTime username
- List of all linked accounts with:
  - Discord username and ID
  - RaceTime username and ID (with link to RaceTime.gg profile)
  - Account link date
  - Unlink action button

### Admin Dialog
**File**: `components/dialogs/admin/racetime_unlink_dialog.py`

The `RacetimeUnlinkDialog` provides:
- Confirmation dialog for administrative unlinking
- Display of user and RaceTime account details
- Warning about the action's consequences
- Audit logging of unlink action

### Service Layer Methods
**File**: `application/services/user_service.py`

Admin-specific methods:

```python
async def admin_unlink_racetime_account(user_id: int, admin_user: User) -> Optional[User]:
    """
    Administratively unlink RaceTime.gg account from a user.
    
    - Checks admin permissions
    - Validates user exists
    - Performs unlink
    - Logs action to audit log
    """

async def get_all_racetime_accounts(admin_user: User, limit: Optional[int], offset: int) -> list[User]:
    """
    Get all users with linked RaceTime accounts.
    
    - Checks admin permissions
    - Returns empty list if unauthorized
    - Supports pagination
    - Logs access to audit log
    """

async def search_racetime_accounts(admin_user: User, query: str) -> list[User]:
    """
    Search users by RaceTime username.
    
    - Checks admin permissions
    - Returns empty list if unauthorized
    - Case-insensitive search
    - Logs search to audit log
    """

async def get_racetime_link_statistics(admin_user: User) -> dict:
    """
    Get statistics about RaceTime account linking.
    
    Returns:
        dict with keys:
        - total_users: Total active users
        - linked_users: Users with linked accounts
        - unlinked_users: Users without linked accounts
        - link_percentage: Percentage of users with linked accounts
    """
```

### Repository Methods
**File**: `application/repositories/user_repository.py`

Data access methods for admin features:

```python
async def get_users_with_racetime(include_inactive: bool, limit: Optional[int], offset: int) -> list[User]:
    """Get all users with linked RaceTime accounts with pagination."""

async def count_racetime_linked_users(include_inactive: bool) -> int:
    """Count users with linked RaceTime accounts."""

async def search_by_racetime_name(query: str) -> list[User]:
    """Search users by RaceTime username (case-insensitive)."""
```

### API Endpoints
**File**: `api/routes/racetime.py`

Admin API endpoints:

#### GET /api/racetime/admin/accounts
Get all users with linked RaceTime accounts (admin only).

**Query Parameters:**
- `limit` (optional): Maximum number of accounts to return
- `offset` (optional): Number of accounts to skip (default: 0)

**Response:**
```json
{
  "accounts": [
    {
      "user_id": 1,
      "discord_username": "example_user",
      "discord_id": 123456789,
      "racetime_id": "abc123",
      "racetime_name": "ExampleRacer",
      "created_at": "2025-11-04T12:00:00Z",
      "racetime_linked_since": "2025-11-04T13:00:00Z"
    }
  ],
  "total": 42,
  "limit": null,
  "offset": 0
}
```

#### GET /api/racetime/admin/stats
Get statistics about RaceTime account linking (admin only).

**Response:**
```json
{
  "total_users": 100,
  "linked_users": 42,
  "unlinked_users": 58,
  "link_percentage": 42.0
}
```

#### POST /api/racetime/admin/unlink/{user_id}
Administratively unlink RaceTime account from a user (admin only).

**Path Parameters:**
- `user_id`: ID of user to unlink

**Response:**
```json
{
  "success": true,
  "message": "RaceTime account unlinked from user example_user"
}
```

### Authorization
All admin features require:
- User must be authenticated
- User must have admin permissions (`can_access_admin_panel()`)
- Unauthorized requests return empty results or error responses

### Audit Logging
All admin RaceTime operations are logged via `AuditService`:
- `admin_view_racetime_accounts` - Admin viewed linked accounts list
- `admin_search_racetime_accounts` - Admin searched for accounts
- `admin_view_racetime_stats` - Admin viewed statistics
- `admin_unlink_racetime_account` - Admin unlinked an account

Each log entry includes:
- Admin user ID
- Action performed
- Relevant details (search query, target user, etc.)
- Timestamp

### Usage

1. **View Linked Accounts:**
   - Navigate to Admin → RaceTime Accounts
   - View statistics dashboard
   - Browse list of linked accounts

2. **Search for Account:**
   - Enter RaceTime username in search field
   - Click "Search"
   - Results update automatically

3. **Unlink Account:**
   - Click "Unlink" button on account card
   - Review user details in confirmation dialog
   - Click "Unlink Account" to confirm
   - Action is logged to audit log

### Security Considerations
1. **Authorization:** All operations check admin permissions before execution
2. **Audit Trail:** All admin actions are logged for accountability
3. **Graceful Degradation:** Unauthorized requests return empty data rather than errors
4. **Data Protection:** Admin view shows user information in controlled, secure context

## References

- Original SahasrahBot implementation: https://github.com/tcprescott/sahasrahbot/blob/main/alttprbot_api/blueprints/racetime.py
- RaceTime.gg OAuth2 docs: https://github.com/racetimeGG/racetime-app/wiki/OAuth2-applications
- RaceTime.gg Developer Portal: https://racetime.gg/account/dev
