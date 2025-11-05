# Racer Verification - Multiple Categories Update

## Summary

Updated the Racer Verification feature to support multiple RaceTime.gg categories when calculating race eligibility. Previously, each verification configuration was limited to a single category. Now, administrators can specify multiple categories, and races from all categories will be counted toward the minimum requirement.

## Changes Made

### Database Schema

**Model Changes (`models/racer_verification.py`):**
- Changed `category` (VARCHAR) to `categories` (JSON array)
- Updated unique constraint from `(organization_id, guild_id, category)` to `(organization_id, guild_id, role_id)`
- This allows the same guild/org to have multiple verification configs with different role grants

**Migration (`migrations/models/44_20251104235925_update_racer_verification_multiple_categories.py`):**
- Add `categories` JSON column with default empty array
- Add new unique index on `(organization_id, guild_id, role_id)`
- Drop `category` column
- Note: Old unique index `uid_racer_verif_organiz_3ba91b` remains due to foreign key constraint, but new index takes precedence

### Repository Layer

**File: `application/repositories/racer_verification_repository.py`**

- Updated `create()` method to accept `categories: list[str]` instead of `category: str`
- Removed `get_by_organization_and_category()` method (no longer applicable with multiple categories)
- Updated docstrings to reflect category list parameter

### Service Layer

**File: `application/services/racer_verification_service.py`**

- Updated `create_verification()` to accept `categories: list[str]` parameter
- Updated `check_user_eligibility()` to fetch races from ALL categories in the list:
  ```python
  all_races = []
  for category in verification.categories:
      races = await self.racetime_api.get_user_races(
          user=user,
          category=category,
          show_entrants=False
      )
      all_races.extend(races)
  ```
- Updated audit logging to log `categories` array instead of single `category`
- `update_verification()` unchanged (uses **updates dict, works with any field)

### UI Layer

**Admin Configuration Dialog (`components/dialogs/organization/racer_verification_dialog.py`):**
- Changed input from single category to comma-separated categories:
  ```python
  self.categories_input = ui.input(
      label='RaceTime Categories (comma-separated)',
      value=', '.join(verification.categories) if verification else '',
      placeholder='e.g., alttpr, alttprbiweekly'
  )
  ```
- Added parsing logic to split comma-separated input and trim whitespace:
  ```python
  categories = [
      cat.strip()
      for cat in self.categories_input.value.split(',')
      if cat.strip()
  ]
  ```
- Updated validation to require at least one valid category
- Updated save logic to pass `categories` list to service

**Admin Configuration View (`views/organization/racer_verification_config.py`):**
- Changed table column from `'Category'` (key-based) to `'Categories'` (cell_render)
- Added `_render_categories()` method to display categories as comma-separated list:
  ```python
  def _render_categories(self, row):
      if row.categories:
          ui.label(', '.join(row.categories)).classes('text-sm')
      else:
          ui.label('None').classes('text-secondary text-sm')
  ```

**User Verification View (`views/user_profile/racer_verification.py`):**
- Updated `_render_verification_card()` to display all categories in header:
  ```python
  categories_str = ', '.join([cat.upper() for cat in verification.categories])
  ui.label(categories_str).classes('text-lg font-bold')
  ```

## Use Cases

### Example 1: ALTTPR Variations
An organization running both standard ALTTPR and biweekly races can now create a single verification:
- **Categories**: `['alttpr', 'alttprbiweekly']`
- **Minimum Races**: 10
- **Role**: "Verified Racer"

Users completing 5 standard races + 5 biweekly races = 10 total races = eligible for verification.

### Example 2: Multi-Game Community
A multi-game speedrunning community can verify racers who participate in any of their supported games:
- **Categories**: `['alttpr', 'ootr', 'smz3']`
- **Minimum Races**: 15
- **Role**: "Active Racer"

Users can participate in any mix of categories to reach the 15 race requirement.

### Example 3: Separate Tiers
With the new unique constraint on `role_id`, organizations can create tiered verification:
- **Beginner Role** (5 races): `['alttpr']`
- **Intermediate Role** (20 races): `['alttpr', 'alttprbiweekly']`
- **Expert Role** (50 races): `['alttpr', 'alttprbiweekly', 'alttprcustom']`

## Backwards Compatibility

**Not backwards compatible** - This is a breaking schema change:
- Old configurations with single `category` field cannot be directly migrated
- Database must be empty or manually migrated before applying changes
- Fresh install: No issues, starts with new schema

## Testing Checklist

- [ ] Create verification config with single category
- [ ] Create verification config with multiple categories
- [ ] Verify categories display correctly in admin table
- [ ] Edit existing config and change categories
- [ ] User verification with single-category config
- [ ] User verification with multi-category config
- [ ] Verify race counting across multiple categories
- [ ] Test with categories that have no races (count should be 0)
- [ ] Test with user who has races in only some categories
- [ ] Verify role granting works with multi-category configs
- [ ] Deep link to verification page
- [ ] Check that unique constraint prevents duplicate (org, guild, role) configs

## Migration Notes

The migration was applied manually due to unique index constraint conflicts. Steps taken:

1. Applied initial racer verification migration (43)
2. Modified racer_verifications table:
   - Added `categories` JSON column (default empty array)
   - Added new unique index `uid_racer_verif_organiz_0a1e57` on `(organization_id, guild_id, role_id)`
   - Dropped `category` column
3. Old unique index `uid_racer_verif_organiz_3ba91b` remains (needed for foreign key)
4. Marked migration 44 as complete in aerich table

## Future Enhancements

Potential improvements:
- Category selection dropdown (fetch from RaceTime API)
- Per-category minimum race requirements
- Visual breakdown showing races per category
- Category aliases/display names in UI
- Race count caching to reduce API calls
- Bulk verification status checks
