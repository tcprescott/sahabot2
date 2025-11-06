# SMZ3 Randomizer Support

SahaBot2 includes full support for the **SMZ3 (Super Metroid + A Link to the Past Combo Randomizer)**.

## Overview

SMZ3 is a combo randomizer that combines Super Metroid and A Link to the Past into a single randomized experience. Items from both games can be found in either game, creating a unique cross-game adventure.

## Features

### Discord Commands

#### `/smz3 [preset] [spoiler]`
Generate an SMZ3 randomizer seed.

**Parameters:**
- `preset` (optional): Name of a preset to use for seed generation
- `spoiler` (optional): Generate seed with spoiler log (default: False)

**Examples:**
```
/smz3
/smz3 preset:normal spoiler:true
/smz3 preset:hard-mode
```

**Output:**
- Seed URL
- Preset information (if used)
- Configuration details (logic, mode, goal)
- Spoiler log URL (if requested)

#### `/smz3_presets`
List all available public SMZ3 presets.

**Output:**
- List of preset names with descriptions
- Up to 25 presets displayed (Discord embed limit)

### RaceTime.gg Commands

These commands are available in SMZ3 category race rooms on RaceTime.gg:

#### `!race [preset]`
Generate an SMZ3 seed for the race.

**Usage:**
```
!race                    # Generate with default settings
!race normal             # Generate with "normal" preset
!race hard-mode          # Generate with "hard-mode" preset
```

**Output:**
```
SMZ3 Seed Generated! | Beat the games | https://samus.link/seed/abc123 | Preset: normal
```

#### `!preset [name]`
Generate a seed using a specific preset. Alias for `!race [preset]`.

**Usage:**
```
!preset normal
!preset tournament
```

#### `!spoiler [preset]`
Generate a seed with spoiler log access.

**Usage:**
```
!spoiler                 # Generate with default settings and spoiler
!spoiler normal          # Generate with preset and spoiler
```

**Output:**
```
SMZ3 Seed with Spoiler | https://samus.link/seed/abc123 | Spoiler: https://samus.link/api/spoiler/guid?key=spoiler
```

## Preset System

SMZ3 presets allow you to define custom randomizer settings that can be reused across multiple seed generations.

### Preset Structure

SMZ3 presets are stored as JSON in the database with the following structure:

```json
{
  "logic": "normal",
  "mode": "normal",
  "goal": "defeatBoth",
  "itemPlacement": "major",
  "swordLocation": "randomized",
  "morphLocation": "original"
}
```

### Common Preset Settings

#### Logic
- `normal` - Standard logic
- `hard` - Expert logic requiring advanced techniques

#### Mode
- `normal` - Normal difficulty
- `hard` - Harder difficulty

#### Goal
- `defeatBoth` - Defeat both Ganon and Mother Brain
- `fast` - Fast completion goal
- `allBosses` - All bosses must be defeated

#### Item Placement
- `major` - Major items only
- `full` - All items randomized

#### Sword Location
- `randomized` - Sword can be anywhere
- `early` - Sword will be found early
- `uncle` - Sword guaranteed from Uncle

#### Morph Location
- `original` - Morph ball in original location
- `randomized` - Morph ball can be anywhere
- `early` - Morph ball will be found early

### Creating Presets

Presets can be created via the web interface:

1. Navigate to **Organization → Presets**
2. Click **Create New Preset**
3. Select **SMZ3** as the randomizer
4. Enter preset name and description
5. Configure settings using JSON or form
6. Save preset

### Example Presets

#### Normal Preset
```json
{
  "logic": "normal",
  "mode": "normal",
  "goal": "defeatBoth",
  "itemPlacement": "major",
  "swordLocation": "randomized",
  "morphLocation": "original"
}
```

#### Hard Mode Preset
```json
{
  "logic": "hard",
  "mode": "hard",
  "goal": "defeatBoth",
  "itemPlacement": "full",
  "swordLocation": "randomized",
  "morphLocation": "randomized"
}
```

#### Fast Completion
```json
{
  "logic": "normal",
  "mode": "normal",
  "goal": "fast",
  "itemPlacement": "major",
  "swordLocation": "early",
  "morphLocation": "early"
}
```

## API Integration

SMZ3 seed generation uses the **samus.link** API:

- **Endpoint:** `https://samus.link/api/randomize`
- **Method:** POST
- **Request Body:** JSON with settings
- **Response:** Seed information including slug and GUID

### Tournament Mode

When generating seeds for races/tournaments, the `race` parameter is set to `true`:

```json
{
  "race": "true",
  "logic": "normal",
  "mode": "normal",
  "goal": "defeatBoth"
}
```

This ensures:
- No spoiler information is included in the response
- Seed is suitable for competitive play

### Spoiler Mode

For practice seeds, set `race` to `false` and include a `spoilerKey`:

```json
{
  "race": "false",
  "spoilerKey": "myspoilerkey",
  "logic": "normal",
  "mode": "normal",
  "goal": "defeatBoth"
}
```

Spoiler log URL format:
```
https://samus.link/api/spoiler/{guid}?key={spoilerKey}&yaml=true
```

## Tournament Support

SMZ3 is fully supported in tournament configurations:

### Async Tournaments
- SMZ3 presets can be configured per tournament
- Seeds are automatically generated when races start
- Results are tracked and recorded

### Live Tournaments
- Race rooms can be created with SMZ3 seeds
- Commands available during race setup
- Automatic seed distribution

### Tournament Setup

1. Create tournament via web interface
2. Set **Randomizer** to **SMZ3**
3. Select preset or use custom settings
4. Configure race parameters
5. Schedule matches

## RaceTime.gg Category

SMZ3 races use the `smz3` category on RaceTime.gg.

**Category URL:** https://racetime.gg/smz3

**Common Goals:**
- Beat the games
- Beat the games (Normal)
- Beat the games (Hard)
- All Bosses

## Database Schema

SMZ3 uses the existing preset system. No additional database tables required.

### Relevant Models

- `RandomizerPreset` - Stores SMZ3 presets
- `PresetNamespace` - Organizes presets by namespace
- `RacetimeBot` - Bot configuration for SMZ3 category

### Adding SMZ3 Bot

To enable SMZ3 commands on RaceTime.gg:

1. Navigate to **Admin → RaceTime Bots**
2. Click **Add Bot**
3. Enter bot configuration:
   - **Category:** `smz3`
   - **Name:** SMZ3 Bot
   - **Client ID:** (from racetime.gg bot settings)
   - **Client Secret:** (from racetime.gg bot settings)
4. Save configuration

Once configured, the bot will respond to commands in SMZ3 race rooms.

## Troubleshooting

### Seed Generation Fails

**Problem:** `/smz3` command returns an error

**Solutions:**
1. Check samus.link API is accessible
2. Verify preset settings are valid JSON
3. Check logs for detailed error messages

### Preset Not Found

**Problem:** `!race [preset]` says "Preset not found"

**Solutions:**
1. Verify preset exists in database
2. Check preset name spelling
3. Ensure preset is marked as public (for non-owners)

### Commands Not Responding

**Problem:** RaceTime.gg commands don't work

**Solutions:**
1. Verify bot is connected (Admin → RaceTime Bots)
2. Check bot status is "Connected"
3. Ensure bot is assigned to an organization
4. Verify commands are active in database

## Development

### Adding New Commands

To add new SMZ3 commands:

1. Add handler function to `racetime/smz3_handler.py`
2. Register handler in `SMZ3_HANDLERS` dictionary
3. Handler will be automatically available after bot restart

### Testing

Run SMZ3 tests:

```bash
python3 -m pytest tests/test_smz3.py -v
```

### Service Layer

The SMZ3 service is located at:
```
application/services/randomizer/smz3_service.py
```

Main method: `generate(settings, tournament, spoilers, spoiler_key)`

## Links

- **SMZ3 Website:** https://samus.link
- **SMZ3 Discord:** https://discord.gg/smz3randos
- **RaceTime.gg Category:** https://racetime.gg/smz3
- **GitHub (Original Bot):** https://github.com/tcprescott/sahasrahbot

## Support

For issues or questions:

1. Check this documentation
2. Review logs for error messages
3. Open an issue on GitHub
4. Ask in Discord support channels

---

**Last Updated:** November 6, 2025
