# Preset Usage Examples

This document provides practical examples of how to use the preset functionality in SahaBot2.

## Basic Preset Creation

### Via Service Layer

```python
from application.services.preset_service import PresetService

# Initialize service
preset_service = PresetService()

# Create a preset for ALTTPR
preset = await preset_service.create_preset(
    organization_id=1,
    name="Standard Open",
    randomizer="alttpr",
    settings={
        "glitches": "none",
        "item_placement": "advanced",
        "dungeon_items": "standard",
        "accessibility": "items",
        "goal": "ganon",
        "world_state": "open",
        "entrance_shuffle": "none",
        "boss_shuffle": "none",
        "enemy_shuffle": "none",
        "hints": "on",
        "weapons": "randomized",
        "item_pool": "normal",
        "item_functionality": "normal"
    },
    description="Standard open mode with hints enabled"
)

print(f"Created preset: {preset.name} (ID: {preset.id})")
```

## Generating Seeds from Presets

### ALTTPR Example

```python
from application.services.randomizer.alttpr_service import ALTTPRService

# Initialize service
alttpr = ALTTPRService()

# Generate a seed from a preset
result = await alttpr.generate_from_preset(
    preset_name="Standard Open",
    organization_id=1,
    tournament=True,
    spoilers="off"
)

# Access seed information
print(f"Seed URL: {result.url}")
print(f"Hash: {result.hash_id}")
print(f"Permalink: {result.permalink}")
```

## Managing Presets

### List All Presets

```python
# List all active presets for an organization
presets = await preset_service.list_presets(
    organization_id=1,
    active_only=True
)

for preset in presets:
    print(f"{preset.name} ({preset.randomizer}): {preset.description}")
```

### Filter by Randomizer

```python
# Get only ALTTPR presets
alttpr_presets = await preset_service.list_presets(
    organization_id=1,
    randomizer="alttpr"
)
```

### Get Preset by Name

```python
# Retrieve a specific preset
preset = await preset_service.get_preset_by_name(
    name="Standard Open",
    organization_id=1
)

if preset:
    print(f"Settings: {preset.settings}")
else:
    print("Preset not found")
```

### Update Preset

```python
# Update preset settings
updated = await preset_service.update_preset(
    preset_id=preset.id,
    organization_id=1,
    description="Updated description",
    settings={
        # New settings dictionary
        "glitches": "none",
        "item_placement": "advanced",
        # ... other settings
    }
)
```

### Delete Preset (Soft Delete)

```python
# Soft delete a preset (sets is_active=False)
deleted = await preset_service.delete_preset(
    preset_id=preset.id,
    organization_id=1
)

if deleted:
    print("Preset deleted successfully")
```

## Error Handling

### Invalid Randomizer Type

```python
try:
    preset = await preset_service.create_preset(
        organization_id=1,
        name="Invalid Preset",
        randomizer="invalid_randomizer",
        settings={}
    )
except ValueError as e:
    print(f"Error: {e}")
    # Output: Invalid randomizer type: invalid_randomizer. Must be one of: alttpr, aosr, ...
```

### Duplicate Preset Name

```python
try:
    # Try to create a preset with existing name
    preset = await preset_service.create_preset(
        organization_id=1,
        name="Standard Open",  # Already exists
        randomizer="alttpr",
        settings={}
    )
except ValueError as e:
    print(f"Error: {e}")
    # Output: Preset with name 'Standard Open' already exists in this organization
```

### Preset Not Found

```python
from application.services.randomizer.alttpr_service import ALTTPRService

alttpr = ALTTPRService()

try:
    result = await alttpr.generate_from_preset(
        preset_name="NonExistent",
        organization_id=1
    )
except ValueError as e:
    print(f"Error: {e}")
    # Output: Preset 'NonExistent' not found in organization 1
```

## Advanced Usage

### Creating Multiple Presets

```python
# Create a collection of presets
preset_configs = [
    {
        "name": "Beginner Friendly",
        "settings": {
            "item_placement": "basic",
            "accessibility": "items",
            "hints": "on"
        }
    },
    {
        "name": "Tournament Standard",
        "settings": {
            "item_placement": "advanced",
            "accessibility": "locations",
            "hints": "off"
        }
    },
    {
        "name": "Challenge Mode",
        "settings": {
            "item_placement": "advanced",
            "accessibility": "none",
            "entrance_shuffle": "full"
        }
    }
]

for config in preset_configs:
    preset = await preset_service.create_preset(
        organization_id=1,
        name=config["name"],
        randomizer="alttpr",
        settings=config["settings"]
    )
    print(f"Created: {preset.name}")
```

### Cloning a Preset

```python
# Get existing preset
original = await preset_service.get_preset_by_name(
    name="Standard Open",
    organization_id=1
)

# Create a modified clone
if original:
    cloned = await preset_service.create_preset(
        organization_id=1,
        name="Standard Open - Hard Mode",
        randomizer=original.randomizer,
        settings={
            **original.settings,  # Copy all settings
            "accessibility": "none",  # Override specific settings
            "item_placement": "advanced"
        },
        description=f"Based on {original.name} with harder settings"
    )
```

## Integration with Discord Bot

### Example Discord Command

```python
# In discordbot/commands/randomizer_commands.py
from discord import app_commands
import discord

@app_commands.command(name="seed", description="Generate a seed from a preset")
@app_commands.describe(
    preset="Name of the preset to use",
    spoilers="Enable spoilers (on/off)"
)
async def generate_seed(
    interaction: discord.Interaction,
    preset: str,
    spoilers: str = "off"
):
    """Generate a randomizer seed from a preset."""
    await interaction.response.defer()

    try:
        # Get user's organization (implementation depends on your setup)
        organization_id = await get_user_organization(interaction.user.id)

        # Generate seed
        from application.services.randomizer.alttpr_service import ALTTPRService
        alttpr = ALTTPRService()

        result = await alttpr.generate_from_preset(
            preset_name=preset,
            organization_id=organization_id,
            tournament=True,
            spoilers=spoilers
        )

        # Send result
        embed = discord.Embed(
            title=f"Seed Generated: {preset}",
            description=f"Hash: {result.hash_id}",
            color=discord.Color.green()
        )
        embed.add_field(name="URL", value=result.url)
        if result.spoiler_url:
            embed.add_field(name="Spoiler", value=result.spoiler_url)

        await interaction.followup.send(embed=embed)

    except ValueError as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)
```

## Best Practices

1. **Organization Scoping**: Always pass the correct `organization_id` to ensure proper tenant isolation.

2. **Error Handling**: Wrap preset operations in try-except blocks to handle validation errors gracefully.

3. **Naming Convention**: Use descriptive preset names that indicate the randomizer type and configuration.

4. **Settings Validation**: Validate settings before creating presets to ensure they work with the target randomizer.

5. **Documentation**: Use the `description` field to document what each preset does and when to use it.

6. **Testing**: Test presets by generating seeds before deploying them to production.

## Multi-Tenant Considerations

Presets are scoped to organizations. This means:

- Preset names only need to be unique within an organization
- Different organizations can have presets with the same name
- Always specify `organization_id` in all preset operations
- Users can only access presets from their own organization(s)

Example:

```python
# Organization 1 can have a "Standard" preset
preset_org1 = await preset_service.create_preset(
    organization_id=1,
    name="Standard",
    randomizer="alttpr",
    settings={...}
)

# Organization 2 can also have a "Standard" preset with different settings
preset_org2 = await preset_service.create_preset(
    organization_id=2,
    name="Standard",
    randomizer="alttpr",
    settings={...}  # Different settings
)

# These are completely independent presets
```
