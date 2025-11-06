# SMZ3 Preset Examples

This directory contains example presets for SMZ3 (Super Metroid + A Link to the Past Combo Randomizer).

## Normal Mode

Standard tournament settings with normal logic and randomization.

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

**Description:** Standard tournament preset with normal logic. Suitable for most races.

**Recommended For:** Weekly races, casual tournaments

---

## Hard Mode

Expert logic requiring advanced techniques in both games.

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

**Description:** Hard difficulty with full item randomization. Requires knowledge of advanced techniques.

**Recommended For:** Expert players, challenge races

---

## Fast Completion

Optimized for faster completion times with early key items.

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

**Description:** Fast-paced preset with key items available early. Shorter seed times.

**Recommended For:** Quick races, time trials

---

## All Bosses

Defeat all bosses in both games to complete.

```json
{
  "logic": "normal",
  "mode": "normal",
  "goal": "allBosses",
  "itemPlacement": "major",
  "swordLocation": "randomized",
  "morphLocation": "randomized"
}
```

**Description:** Extended gameplay requiring all boss defeats. Longer seed times.

**Recommended For:** Long-form races, marathon events

---

## Beginner Friendly

Easy mode with guaranteed early progression items.

```json
{
  "logic": "normal",
  "mode": "normal",
  "goal": "defeatBoth",
  "itemPlacement": "major",
  "swordLocation": "uncle",
  "morphLocation": "original"
}
```

**Description:** Beginner-friendly settings with sword from Uncle and Morph Ball in original location.

**Recommended For:** New players, introductory races

---

## Tournament Standard

Community-approved tournament standard settings.

```json
{
  "logic": "normal",
  "mode": "normal",
  "goal": "defeatBoth",
  "itemPlacement": "major",
  "swordLocation": "randomized",
  "morphLocation": "randomized",
  "bossShuffleMode": "none",
  "enemyDamage": "default"
}
```

**Description:** Official tournament preset used in major SMZ3 events.

**Recommended For:** Official tournaments, league play

---

## Using Presets

### Via Web Interface

1. Navigate to **Organization → Presets**
2. Click **Create New Preset**
3. Select **SMZ3** as the randomizer
4. Copy one of the JSON examples above
5. Paste into settings field
6. Give it a descriptive name
7. Save preset

### Via Discord Command

```
/smz3 preset:normal
```

### Via RaceTime.gg Command

```
!race normal
!preset tournament
```

## Custom Settings

You can customize any preset by modifying the JSON. Available options:

### Logic Options
- `normal` - Standard logic
- `hard` - Expert logic with advanced techniques

### Mode Options
- `normal` - Normal difficulty
- `hard` - Harder difficulty

### Goal Options
- `defeatBoth` - Defeat Ganon and Mother Brain
- `fast` - Fast completion
- `allBosses` - All bosses must be defeated

### Item Placement
- `major` - Major items only randomized
- `full` - All items randomized

### Sword Location
- `randomized` - Anywhere
- `early` - Guaranteed early
- `uncle` - From Uncle (ALTTP start)

### Morph Location
- `original` - Original location (morphing ball room)
- `randomized` - Anywhere
- `early` - Guaranteed early

## Additional Options

Advanced settings available in presets:

```json
{
  "logic": "normal",
  "mode": "normal",
  "goal": "defeatBoth",
  "itemPlacement": "major",
  "swordLocation": "randomized",
  "morphLocation": "randomized",
  "bossShuffleMode": "none",
  "enemyDamage": "default",
  "enemyShuffle": false,
  "keycards": "normal"
}
```

### Boss Shuffle
- `none` - Bosses in original locations
- `simple` - Simple boss shuffle
- `full` - Full boss randomization

### Enemy Options
- `enemyDamage`: `default`, `quarter`, `half`, `double`
- `enemyShuffle`: `true` or `false`

### Keycard Options
- `normal` - Standard keycard requirements
- `reduced` - Fewer keycards required

## Importing from Original SahasrahBot

If you have presets from the original SahasrahBot:

1. Locate preset YAML files in `presets/smz3/` directory
2. Convert YAML to JSON format
3. Upload via web interface
4. Test seed generation with new preset

## Contributing Presets

To contribute a preset to the community:

1. Create and test your preset
2. Mark as **Public** in preset settings
3. Add clear description
4. Share preset name with community

---

**Last Updated:** November 6, 2025
