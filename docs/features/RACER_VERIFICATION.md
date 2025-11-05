# Racer Verification Feature - Implementation Summary

## Overview

Implemented a racer verification system that allows organization administrators to configure Discord roles that are automatically granted to users based on their RaceTime.gg race completion statistics. This feature is accessed entirely through the web UI and API, with no Discord commands required.

## Feature Requirements (Completed)

✅ Web UI and API-based (no Discord commands)  
✅ Organization-scoped configuration by admins  
✅ Deep linking support for verification pages  
✅ RaceTime account linking prerequisite with instructions  
✅ Configurable race completion requirements  
✅ Optional counting of forfeits and DQs  
✅ Automatic Discord role granting  
✅ Multi-organization support

## Architecture

### Database Models

**File: `models/racer_verification.py`**

Two new models:

1. **RacerVerification** - Organization configuration
   - Links to: Organization, Discord Guild, Discord Role
   - Fields: category, minimum_races, count_forfeits, count_dq
   - One-to-many with UserRacerVerification

2. **UserRacerVerification** - User verification status
   - Links to: RacerVerification, User
   - Fields: is_verified, race_count, role_granted, verified_at, last_checked_at
   - Tracks verification status and role grant

### Repository Layer

**File: `application/repositories/racer_verification_repository.py`**

Two repository classes providing CRUD operations:

- **RacerVerificationRepository**: Manages verification configs
  - `create`, `get_by_id`, `get_by_organization_and_category`, `list_by_organization`, `list_by_guild`, `update`, `delete`

- **UserRacerVerificationRepository**: Manages user verification status
  - `create`, `get_by_id`, `get_by_verification_and_user`, `list_by_verification`, `list_by_user`, `update`, `delete`

### Service Layer

**File: `application/services/racer_verification_service.py`**

Business logic for verification system:

**Admin Methods**:
- `create_verification()` - Create new verification config (requires org admin)
- `get_verifications_for_organization()` - List configs for org (requires org membership)
- `update_verification()` - Update config (requires org admin)
- `delete_verification()` - Delete config (requires org admin)

**User Methods**:
- `check_user_eligibility()` - Check if user qualifies for verification
  - Fetches races from RaceTime API
  - Counts qualifying races based on config (finished, forfeits, DQs)
  - Returns eligibility status with race count

- `verify_user()` - Verify user and grant role
  - Checks eligibility
  - Creates/updates verification record
  - Grants Discord role via bot
  - Logs audit trail

- `get_user_verification_status()` - Get user's current verification status

**Internal Methods**:
- `_grant_discord_role()` - Discord integration for role granting

### UI Components

#### Admin Configuration View

**File: `views/organization/racer_verification_config.py`**

Organization admin interface for managing verification configs:
- Statistics dashboard (total verifications)
- Responsive table showing all configs with category, role, minimum races, rules
- Create/Edit/Delete actions
- Refresh on changes

#### Admin Configuration Dialog

**File: `components/dialogs/organization/racer_verification_dialog.py`**

Dialog for creating/editing verification configs:
- Discord server selection (auto-loads linked guilds)
- Discord role selection (auto-loads roles from selected guild)
- RaceTime category input
- Minimum races number input
- Counting rules checkboxes (forfeits, DQs)
- Validation before save
- Automatic role name capture

#### User Verification View

**File: `views/user_profile/racer_verification.py`**

User-facing verification interface:

**Features**:
- RaceTime account check with linking instructions
- Display all available verifications from user's organizations
- Verification card for each config showing:
  - Category and role name
  - Status badge (Verified, Eligible, Not Eligible)
  - Race count vs. minimum required
  - Counting rules explanation
  - Verification button (if eligible)
  - Already verified status with timestamp

**Deep Linking Support**:
- Can load specific verification by ID via `?verification_id=X`
- Standalone navigation: `/profile?view=racer-verification`

**Account Linking Flow**:
1. Check if user has linked RaceTime account
2. If not: Display instructions with steps
3. Provide "Go to Profile" button to link account
4. After linking: Return to verification page

### Page Integration

#### Organization Admin Page

**File: `pages/organization_admin.py`**

Added to organization admin sidebar:
- "Racer Verification" menu item with "verified" icon
- Content loader for `RacerVerificationConfigView`
- Available to organization admins only

#### User Profile Page

**File: `pages/user_profile.py`**

Added to profile sidebar:
- "Racer Verification" menu item with "verified" icon
- Content loader for `RacerVerificationView`
- Available to all authenticated users

## Database Migration

**Migration**: `43_20251104234838_add_racer_verification.py`

Creates two tables:
- `racer_verifications` - Verification configurations
- `user_racer_verifications` - User verification status

## User Workflows

### Admin Workflow: Create Verification

1. Navigate to Organization Admin → Racer Verification
2. Click "Create Verification"
3. Select Discord server (from linked guilds)
4. Select Discord role (from server roles)
5. Enter RaceTime category (e.g., "alttpr")
6. Set minimum races required
7. Choose counting rules (forfeits, DQs)
8. Save configuration

### User Workflow: Get Verified

**If RaceTime Account Not Linked**:
1. Navigate to Profile → Racer Verification
2. See "RaceTime Account Required" prompt
3. Follow instructions to link account
4. Return to verification page

**If RaceTime Account Linked**:
1. Navigate to Profile → Racer Verification
2. See all available verifications
3. Check eligibility status and race count
4. Click "Verify Now" if eligible
5. System checks RaceTime races
6. Discord role automatically granted
7. See "Verified" status with timestamp

### Deep Linking Example

Organization can share verification link:
```
https://yoursite.com/profile?view=racer-verification&verification_id=1
```

User clicks link → logs in → sees specific verification → verifies if eligible

## Security & Authorization

- **Admin Functions**: Require `can_manage_org_members` permission
- **User Functions**: Require organization membership
- **Role Granting**: Only via Discord bot (bot must be in guild)
- **Audit Logging**: All admin actions logged
- **Multi-Tenant**: Organization-scoped, no cross-org data leakage

## Integration Points

1. **RaceTime API** (`RacetimeApiService`)
   - Fetches user's race history
   - Filters by category
   - Parses race status (done, dnf, dq)

2. **Discord Bot** (`get_bot_instance()`)
   - Gets guild and role objects
   - Grants roles to users
   - Handles rate limits and errors

3. **Authorization Service** (`AuthorizationService`)
   - Checks org admin permissions
   - Validates org membership

4. **Organization Repository** (`OrganizationRepository`)
   - Lists user's organizations
   - Validates org membership

## Testing Checklist

- [ ] Admin can create verification config
- [ ] Admin can edit verification config
- [ ] Admin can delete verification config
- [ ] User without RaceTime account sees instructions
- [ ] User with RaceTime account sees verifications
- [ ] Eligible user can verify successfully
- [ ] Ineligible user cannot verify
- [ ] Discord role is granted on verification
- [ ] Verification status persists across sessions
- [ ] Deep linking to specific verification works
- [ ] Multiple verifications per organization work
- [ ] Multiple organizations per user work
- [ ] Forfeits/DQs counted correctly based on config
- [ ] Mobile responsive design works

## Future Enhancements

Potential improvements:
- Bulk verification for all eligible users
- Periodic re-verification (ensure users maintain race count)
- Verification expiry (role removed if races drop below minimum)
- Email notifications on verification
- Verification history/audit trail for users
- Support for multiple roles per verification
- Support for race time thresholds (not just completion count)
- Integration with tournament systems (require verification to enter)

## Files Created/Modified

### New Files (9)
1. `models/racer_verification.py` - Database models
2. `application/repositories/racer_verification_repository.py` - Data access
3. `application/services/racer_verification_service.py` - Business logic
4. `views/organization/racer_verification_config.py` - Admin UI view
5. `views/user_profile/racer_verification.py` - User UI view
6. `components/dialogs/organization/racer_verification_dialog.py` - Admin dialog
7. `migrations/models/43_20251104234838_add_racer_verification.py` - Migration
8. `docs/features/RACER_VERIFICATION.md` - This documentation

### Modified Files (5)
1. `models/__init__.py` - Added model imports
2. `views/organization/__init__.py` - Added view export
3. `views/user_profile/__init__.py` - Added view export
4. `components/dialogs/organization/__init__.py` - Added dialog export
5. `pages/organization_admin.py` - Added admin menu item and loader
6. `pages/user_profile.py` - Added user menu item and loader

## Related Documentation

- [Original SahasrahBot Implementation](https://github.com/tcprescott/sahasrahbot) - Reference for feature concept
- [RaceTime Integration Guide](../integrations/RACETIME_INTEGRATION.md) - RaceTime API usage
- [Authorization Patterns](../PATTERNS.md#authorization-patterns) - Permission checking patterns
- [Adding Features Guide](../ADDING_FEATURES.md) - Development patterns used

---

**Implementation Date**: November 4, 2025  
**Status**: Complete - Ready for testing and migration
