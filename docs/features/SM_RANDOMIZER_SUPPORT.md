# Super Metroid Randomizer Support

SahaBot2 supports multiple Super Metroid randomizers, including VARIA and DASH variants. This document describes how to use SM randomizer features.

## Supported Randomizers

### VARIA Randomizer
- **API**: https://sm.samus.link
- **Features**:
  - Multiple logic difficulty levels (casual, master, expert)
  - Item progression settings
  - Morph ball placement options
  - Progression speed settings
  - Energy quantity settings
  - Spoiler log support

### DASH Randomizer
- **API**: https://dashrando.net
- **Features**:
  - Area randomization
  - Major/minor item split
  - Boss randomization
  - Item progression settings
  - Total randomization mode

### Total Randomization
- Combines all DASH features for maximum randomization
- Enables area rando, boss rando, and major/minor split

### Multiworld
- VARIA-based multiworld seeds for team races
- Support for 2+ players

## Discord Commands

### `/smvaria [preset] [spoilers]`
Generate a Super Metroid VARIA seed.

**Parameters**:
- `preset` (optional): Preset name (default: "standard")
- `spoilers` (optional): Generate spoiler log (default: False)

**Example**:
```
/smvaria preset:casual spoilers:False
```

**Response**:
- Embed with seed URL, hash, and preset information
- Spoiler log link (if enabled)

### `/smdash [preset] [area_rando] [spoilers]`
Generate a Super Metroid DASH seed.

**Parameters**:
- `preset` (optional): Preset name (default: "standard")
- `area_rando` (optional): Enable area randomization (default: False)
- `spoilers` (optional): Generate spoiler log (default: False)

**Example**:
```
/smdash preset:standard area_rando:True
```

**Response**:
- Embed with seed URL, hash, preset, and area rando status
- Spoiler log link (if enabled)

### `/smtotal [preset] [spoilers]`
Generate a Super Metroid total randomization seed.

**Parameters**:
- `preset` (optional): Preset name (default: "total")
- `spoilers` (optional): Generate spoiler log (default: False)

**Example**:
```
/smtotal preset:total
```

**Response**:
- Embed with seed URL, hash, and features enabled
- Total randomization includes area + boss + major/minor split

## RaceTime.gg Commands

These commands are available in SM race rooms (categories: smvaria, smdash, smtotal, sm).

### `!varia [preset]`
Generate a VARIA seed for the race.

**Example**:
```
!varia casual
```

**Response**:
```
VARIA seed generated! https://sm.samus.link/seed/abc123 (Hash: abc123)
```

### `!dash [preset]`
Generate a DASH seed for the race.

**Example**:
```
!dash area
```

**Response**:
```
DASH seed generated! https://dashrando.net/seed/def456 (Hash: hash789)
```

### `!total [preset]`
Generate a total randomization seed.

**Example**:
```
!total
```

**Response**:
```
Total randomization seed generated! https://dashrando.net/seed/xyz789 (Hash: hashxyz)
```

### `!multiworld [preset] [players]`
Generate a multiworld seed for team races.

**Parameters**:
- `preset` (optional): Preset name or player count
- `players` (optional): Number of players

**Examples**:
```
!multiworld 2
!multiworld casual 3
!multiworld expert
```

**Response**:
```
Multiworld seed generated for 2 players! https://sm.samus.link/seed/multi123
```

## Presets

### Global Presets

SahaBot2 includes several built-in presets for SM randomizers:

#### VARIA Presets
- **casual**: Casual difficulty, normal progression, early morph
- **master**: Master difficulty, fast progression, random morph
- **expert**: Expert difficulty, very fast progression, random morph, low energy

#### DASH Presets
- **standard**: Standard DASH without area randomization
- **area**: DASH with area randomization enabled
- **total**: Total randomization (area + boss + major/minor split)

### Custom Presets

Custom presets can be created via the web interface:

1. Navigate to Organization Settings → Presets
2. Click "Create Preset"
3. Select randomizer type: `sm-varia` or `sm-dash`
4. Name your preset
5. Configure settings (JSON format)
6. Save

**VARIA Settings Example**:
```json
{
  "logic": "casual",
  "itemProgression": "normal",
  "morphPlacement": "early",
  "progressionSpeed": "medium",
  "energyQty": "normal"
}
```

**DASH Settings Example**:
```json
{
  "area_rando": true,
  "major_minor_split": true,
  "boss_rando": false,
  "item_progression": "normal"
}
```

### Preset Namespaces

Presets are organized into namespaces:
- **Global**: System-wide presets available to all users
- **Organization**: Organization-specific presets
- **User**: Personal presets

## Service Layer Usage

For developers integrating SM randomizer support:

### Basic Usage

```python
from application.services.randomizer.sm_service import SMService

service = SMService()

# Generate VARIA seed
result = await service.generate_varia(
    settings={'logic': 'casual', 'itemProgression': 'normal'},
    tournament=True,
    spoilers=False
)

print(f"Seed URL: {result.url}")
print(f"Hash: {result.hash_id}")
```

### DASH Seed

```python
# Generate DASH seed
result = await service.generate_dash(
    settings={'area_rando': True, 'major_minor_split': True},
    tournament=True
)
```

### Using Main Generate Method

```python
# VARIA
result = await service.generate(
    settings={'logic': 'master'},
    randomizer_type='varia',
    tournament=True
)

# DASH
result = await service.generate(
    settings={'area_rando': True},
    randomizer_type='dash',
    tournament=True
)

# Total Randomization
result = await service.generate(
    settings={},
    randomizer_type='total',
    tournament=True
)

# Multiworld
result = await service.generate(
    settings={'player_count': 2},
    randomizer_type='multiworld',
    tournament=True
)
```

### Result Object

All methods return a `RandomizerResult` object:

```python
@dataclass
class RandomizerResult:
    url: str              # Seed URL
    hash_id: str          # Seed hash/identifier
    settings: dict        # Settings used
    randomizer: str       # Randomizer type (sm-varia, sm-dash)
    permalink: str        # Permalink (usually same as url)
    spoiler_url: str      # Spoiler log URL (if enabled)
    metadata: dict        # Additional metadata
```

## Setup

### Adding SM Support to a Bot

Run the setup tool to add SM commands and presets:

```bash
python3 tools/add_sm_support.py
```

This will:
1. Add SM chat commands (!varia, !dash, !total, !multiworld) to SM bots
2. Create example VARIA presets (casual, master, expert)
3. Create example DASH presets (standard, area, total)

### Manual Command Setup

To manually add SM commands to a RaceTime bot:

1. Navigate to Admin Panel → RaceTime Bots
2. Select an SM bot (category: smvaria, smdash, smtotal, or sm)
3. Add commands:
   - Command: `varia`, Handler: `handle_varia`, Scope: Bot
   - Command: `dash`, Handler: `handle_dash`, Scope: Bot
   - Command: `total`, Handler: `handle_total`, Scope: Bot
   - Command: `multiworld`, Handler: `handle_multiworld`, Scope: Bot

## Tournament Integration

SM randomizers can be integrated with tournaments:

### Async Tournaments

1. Create async tournament with randomizer type `sm-varia` or `sm-dash`
2. Configure preset pool
3. Set up Discord channel
4. Players can generate seeds using the tournament embed

### Live Tournaments

1. Create tournament with SM configuration
2. Configure race room profiles for SM categories
3. Set up scheduled tasks to create race rooms
4. Use chat commands in race rooms to generate seeds

## API Integration Details

### VARIA API

**Endpoint**: `POST https://sm.samus.link/api/randomize`

**Request**:
```json
{
  "logic": "casual",
  "itemProgression": "normal",
  "morphPlacement": "early",
  "race": "true",
  "spoilerKey": "optional-key"
}
```

**Response**:
```json
{
  "slug": "abc123",
  "guid": "guid-456",
  "...": "other fields"
}
```

### DASH API

**Endpoint**: `POST https://dashrando.net/api/generate`

**Request**:
```json
{
  "area_rando": true,
  "major_minor_split": true,
  "boss_rando": false,
  "race": true
}
```

**Response**:
```json
{
  "id": "def456",
  "seed": "seed-789",
  "hash": "hashxyz",
  "spoiler_url": "/api/spoiler/xyz"
}
```

## Testing

### Unit Tests

Run SM service unit tests:

```bash
python3 -m pytest tests/unit/test_services_sm.py -v
```

Tests cover:
- VARIA seed generation
- DASH seed generation
- Total randomization
- Multiworld generation
- URL construction
- Metadata handling

### Manual Testing

1. Start the development server: `./start.sh dev`
2. Join Discord server
3. Test commands:
   - `/smvaria preset:casual`
   - `/smdash preset:standard area_rando:True`
   - `/smtotal`
4. Check race rooms on RaceTime.gg
5. Test chat commands: `!varia casual`

## Troubleshooting

### Command Not Found

**Issue**: Discord command not appearing

**Solution**:
1. Restart the bot
2. Wait 5 minutes for Discord to sync commands
3. Check logs for command registration errors

### API Errors

**Issue**: "Failed to generate seed"

**Solution**:
1. Check API status (sm.samus.link, dashrando.net)
2. Verify settings are valid
3. Check logs for detailed error messages
4. Try with default settings

### Preset Not Found

**Issue**: "Preset not found" error

**Solution**:
1. Run `python3 tools/add_sm_support.py` to create example presets
2. Verify preset exists in database
3. Check namespace permissions
4. Use default preset by omitting preset parameter

## Future Enhancements

Planned features for SM support:

- **SMRL Integration**: SM Randomizer League tournament support
- **Submission Forms**: Web-based settings submission for tournaments
- **Playoff Brackets**: Tournament playoff system
- **Advanced Presets**: More complex preset configurations
- **Preset Import/Export**: Share presets between organizations
- **Multiworld Server**: Dedicated multiworld server support
- **Statistics Tracking**: Track popular presets and settings

## Related Documentation

- [Randomizer Services Overview](../application/services/randomizer/README.md)
- [RaceTime Integration](../systems/RACETIME_INTEGRATION.md)
- [Discord Bot Commands](../core/DISCORD_BOT_COMMANDS.md)
- [Preset Management](../features/PRESET_MANAGEMENT.md)
- [Tournament System](../features/TOURNAMENT_SYSTEM.md)

## External Resources

- [VARIA Randomizer](https://sm.samus.link)
- [DASH Randomizer](https://dashrando.net)
- [SM Randomizer Community](https://discord.gg/smrandomizer)
- [SMRL (SM Randomizer League)](https://smrl.example.com)
- [RaceTime.gg](https://racetime.gg)
