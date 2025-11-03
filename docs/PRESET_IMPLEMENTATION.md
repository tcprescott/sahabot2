# Randomizer Preset Implementation

## Overview

This implementation adds preset support to the randomizer service, allowing users to save and reuse randomizer configurations. The implementation is based on the original SahasrahBot's preset functionality but adapted to fit SahaBot2's multi-tenant architecture.

## Architecture

The implementation follows SahaBot2's layered architecture:

### 1. Database Model (`models/randomizer_preset.py`)

The `RandomizerPreset` model stores preset configurations:

- **Multi-tenant**: Scoped to organizations via `organization_id` FK
- **Fields**:
  - `id`: Primary key
  - `organization`: FK to Organization (tenant isolation)
  - `name`: Human-readable preset name (unique per organization)
  - `randomizer`: Type of randomizer (alttpr, sm, smz3, etc.)
  - `settings`: JSON field containing preset settings
  - `description`: Optional description
  - `is_active`: Soft delete flag
  - `created_at`, `updated_at`: Timestamps

### 2. Repository Layer (`application/repositories/preset_repository.py`)

The `PresetRepository` handles data access:

- `get_by_id(preset_id, organization_id)`: Get preset by ID
- `get_by_name(name, organization_id)`: Get preset by name
- `list_by_organization(organization_id, ...)`: List presets
- `create(organization_id, name, randomizer, settings, ...)`: Create preset
- `update(preset_id, organization_id, **kwargs)`: Update preset
- `delete(preset_id, organization_id)`: Soft delete preset

All methods enforce organization-based tenant isolation.

### 3. Service Layer (`application/services/preset_service.py`)

The `PresetService` handles business logic:

- Preset CRUD operations
- Validation (randomizer type, settings format, duplicate names)
- Convenience method `get_preset_settings()` for randomizer services
- Organization-scoped access control

### 4. Randomizer Integration

#### ALTTPR Service

The `ALTTPRService.generate_from_preset()` method:

```python
async def generate_from_preset(
    self,
    preset_name: str,
    organization_id: int,
    tournament: bool = True,
    spoilers: str = "off",
    allow_quickswap: bool = False
) -> RandomizerResult:
    """Generate an ALTTPR seed from a preset."""
```

This method:
1. Loads preset settings from the database using `PresetService`
2. Validates that the preset exists
3. Calls the existing `generate()` method with preset settings

## Usage Example

```python
from application.services.preset_service import PresetService
from application.services.randomizer.alttpr_service import ALTTPRService

# Create a preset
preset_service = PresetService()
preset = await preset_service.create_preset(
    organization_id=1,
    name="Open Standard",
    randomizer="alttpr",
    settings={
        "glitches": "none",
        "item_placement": "advanced",
        "dungeon_items": "standard",
        "accessibility": "items",
        # ... other ALTTPR settings
    },
    description="Standard open mode configuration"
)

# Generate a seed from the preset
alttpr_service = ALTTPRService()
result = await alttpr_service.generate_from_preset(
    preset_name="Open Standard",
    organization_id=1,
    tournament=True
)

print(f"Generated seed: {result.url}")
print(f"Hash: {result.hash_id}")
```

## Multi-Tenancy

All preset operations are scoped to organizations:

- Each organization has its own set of presets
- Preset names must be unique within an organization (but can overlap across organizations)
- All repository and service methods require `organization_id` parameter
- Database queries filter by `organization_id`

## Database Migration

To apply the database schema changes:

```bash
poetry run aerich migrate --name "add_randomizer_preset"
poetry run aerich upgrade
```

This will create the `randomizer_presets` table with appropriate indexes.

## Testing

Run the structure test to verify the implementation:

```bash
python3 tools/test_preset.py
```

This validates:
- File structure
- Model fields
- Repository methods
- Service methods
- ALTTPR integration
- Database configuration

## Future Enhancements

Potential improvements for future iterations:

1. **Other Randomizers**: Extend preset support to other randomizer services (SM, SMZ3, etc.)
2. **Preset Templates**: Add global preset templates that organizations can clone
3. **UI Integration**: Build admin UI for managing presets
4. **API Endpoints**: Add REST API endpoints for preset CRUD operations
5. **Import/Export**: Allow importing/exporting presets as JSON
6. **Validation**: Add schema validation for randomizer-specific settings
7. **Versioning**: Track preset version history

## References

- Original SahasrahBot preset implementation: https://github.com/tcprescott/sahasrahbot/blob/main/alttprbot/alttprgen/preset.py
- SahaBot2 Architecture: See `.github/copilot-instructions.md`
