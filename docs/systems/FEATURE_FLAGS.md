# Organization Feature Flags System

## Overview

The feature flag system allows SUPERADMIN users to enable/disable advanced features on a per-organization basis. This prevents cluttering the UI for organizations that only use basic features while still allowing advanced organizations to access all functionality.

## Architecture

### Database Model
**Table**: `organization_feature_flags`
- `organization_id` (FK) - The organization this flag applies to
- `feature_key` (SMALLINT) - Enum identifier for the feature (IntEnumField)
- `enabled` (BOOL) - Whether the feature is currently enabled
- `enabled_at` (DATETIME) - When the feature was enabled (null if disabled)
- `enabled_by_id` (FK) - User ID of SUPERADMIN who enabled the feature
- `notes` (TEXT) - Optional notes about why the feature was enabled/disabled
- Unique constraint on `(organization_id, feature_key)`
- Indexes on `(organization_id, feature_key)` and `(feature_key, enabled)`

### Code Structure
- **Model**: `models/organization_feature_flag.py`
  - `FeatureFlag` IntEnum - Defines all available feature flags
  - `OrganizationFeatureFlag` Model - Database model for feature flags
- **Repository**: `application/repositories/feature_flag_repository.py`
- **Service**: `application/services/feature_flag_service.py`
- **Utils**: `application/utils/feature_flags.py` - Convenience functions

## Available Feature Flags

All available feature flags are defined in the `FeatureFlag` IntEnum:

| Feature Flag | Value | Description |
|--------------|-------|-------------|
| `FeatureFlag.LIVE_RACES` | 1 | Live race monitoring and management |
| `FeatureFlag.ADVANCED_PRESETS` | 2 | Advanced randomizer preset management |
| `FeatureFlag.RACETIME_BOT` | 3 | RaceTime.gg bot integration |
| `FeatureFlag.SCHEDULED_TASKS` | 4 | Scheduled task automation |
| `FeatureFlag.DISCORD_EVENTS` | 5 | Discord scheduled event integration |

To add new feature flags:
1. Add a new value to the `FeatureFlag` enum in `models/organization_feature_flag.py`
2. Add a description to `DESCRIPTIONS` dict in `application/services/feature_flag_service.py`
3. Create a database migration to support the new value

## Usage

### Checking if a Feature is Enabled (Internal)

For internal feature checks (no authorization required):

```python
from application.services.feature_flag_service import FeatureFlagService
from models import FeatureFlag

service = FeatureFlagService()

# Check if feature is enabled
is_enabled = await service.is_feature_enabled(
    organization_id=org_id,
    feature_key=FeatureFlag.LIVE_RACES
)

if is_enabled:
    # Show live races UI
    pass
```

### Convenience Utility Functions

```python
from application.utils.feature_flags import is_enabled
from models import FeatureFlag

# Quick check without instantiating service
if await is_enabled(org_id, FeatureFlag.LIVE_RACES):
    # Show live races UI
    pass
```

### Getting Enabled Features for an Organization

```python
# Get list of enabled feature flags (returns FeatureFlag enums)
enabled_features = await service.get_enabled_features(organization_id)

# Check if specific feature is in list
if FeatureFlag.RACETIME_BOT in enabled_features:
    # Enable RaceTime bot features
    pass
```

### Enabling a Feature (SUPERADMIN Only)

```python
from application.services.feature_flag_service import FeatureFlagService
from models import FeatureFlag

service = FeatureFlagService()

# Enable a feature
flag = await service.enable_feature(
    organization_id=org_id,
    feature_key=FeatureFlag.LIVE_RACES,
    current_user=superadmin_user,
    notes="Organization requested live race tracking for their tournament"
)

if flag:
    # Feature enabled successfully
    pass
else:
    # Unauthorized (not SUPERADMIN)
    pass
```

### Disabling a Feature (SUPERADMIN Only)

```python
flag = await service.disable_feature(
    organization_id=org_id,
    feature_key=FeatureFlag.LIVE_RACES,
    current_user=superadmin_user,
    notes="Organization no longer needs this feature"
)
```

### Toggling a Feature (SUPERADMIN Only)

```python
# Enable if disabled, disable if enabled
flag = await service.toggle_feature(
    organization_id=org_id,
    feature_key=FeatureFlag.LIVE_RACES,
    current_user=superadmin_user
)
```

### Viewing Organization Features (SUPERADMIN Only)

```python
# Get all feature flags for an organization
flags = await service.get_organization_features(
    organization_id=org_id,
    current_user=superadmin_user
)

for flag in flags:
    print(f"{flag.feature_key}: {flag.enabled}")
```

## UI Implementation (TODO)

SUPERADMIN UI for managing feature flags needs to be created:

1. **Organization Admin Page Enhancement**:
   - Add "Feature Flags" tab to organization admin page
   - Only visible to SUPERADMIN users
   - Shows all available features with enable/disable toggles
   - Shows current status and who enabled each feature

2. **Global Feature Flag Management**:
   - Admin panel section for viewing feature usage across all organizations
   - See which organizations have each feature enabled
   - Bulk enable/disable capabilities

## API Implementation (TODO)

RESTful API endpoints for feature flag management:

```
GET    /api/organizations/{org_id}/features      - List feature flags
POST   /api/organizations/{org_id}/features      - Enable a feature
PATCH  /api/organizations/{org_id}/features/{key} - Update feature state
DELETE /api/organizations/{org_id}/features/{key} - Disable a feature
GET    /api/admin/features/{key}/organizations   - List orgs with feature
```

## Security

- **Authorization**: Only SUPERADMIN users can manage feature flags
- **Audit Logging**: All enable/disable actions are logged to audit log
- **Multi-Tenant Isolation**: Feature flags are organization-scoped
- **Immutable Keys**: Feature keys are hardcoded in `FeatureFlags` class

## Adding a New Feature Flag

1. **Add to FeatureFlags class**:
```python
class FeatureFlags:
    # ... existing flags ...
    MY_NEW_FEATURE = 'my_new_feature'

    @classmethod
    def all(cls) -> list[str]:
        return [
            # ... existing flags ...
            cls.MY_NEW_FEATURE,
        ]

    @classmethod
    def get_description(cls, feature_key: str) -> str:
        descriptions = {
            # ... existing descriptions ...
            cls.MY_NEW_FEATURE: 'Description of my new feature',
        }
        return descriptions.get(feature_key, 'Unknown feature')
```

2. **Check feature in code**:
```python
from application.services.feature_flag_service import FeatureFlagService, FeatureFlags

if await service.is_feature_enabled(org_id, FeatureFlags.MY_NEW_FEATURE):
    # Show/enable the new feature
    pass
```

3. **Update documentation**:
   - Add to "Available Feature Flags" table in this document

## Migration from Data Migration

During data migration from SahasrahBot, you may want to automatically enable certain features for organizations that were using them:

```python
# In data migration script
from application.services.feature_flag_service import FeatureFlagService, FeatureFlags

service = FeatureFlagService()

# If organization had racer verification, enable live races
if org_had_racer_verification:
    await service.enable_feature(
        organization_id=new_org.id,
        feature_key=FeatureFlags.LIVE_RACES,
        current_user=system_user,
        notes="Auto-enabled during migration - org was using racer verification"
    )
```

## Future Enhancements

Potential improvements:
1. **Feature Dependencies**: Some features may require others (e.g., live_races requires racetime_bot)
2. **Feature Limits**: Numeric limits per feature (e.g., max_scheduled_tasks=10)
3. **Feature Expiration**: Time-limited feature access (trial periods)
4. **Bulk Operations**: Enable/disable features for multiple organizations at once
5. **Feature Templates**: Preset combinations of features for different org types
6. **Usage Tracking**: Track which features are actually being used
7. **Cost Tracking**: Associate costs with features for billing purposes

---

**Created**: November 5, 2025  
**Last Updated**: November 5, 2025
