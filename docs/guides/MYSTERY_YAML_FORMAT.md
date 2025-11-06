# ALTTPR Mystery Weightset YAML Format

This document describes the YAML format for ALTTPR mystery weightsets. Mystery weightsets allow you to create randomized seeds where the settings are chosen probabilistically based on configured weights.

## Overview

Mystery seeds use weighted selection to randomly choose:
- **Presets**: Main randomizer settings
- **Subweights**: Conditional/nested settings based on the rolled preset
- **Entrance Shuffle**: Entrance randomization options
- **Customizer Settings**: Custom item pool and gameplay modifications

## Basic Structure

A mystery weightset YAML has the following optional top-level keys:

```yaml
preset_type: mystery  # Optional - auto-detected if 'weights' is present

weights:              # Required - Main preset weights
  preset_name_1: weight_value
  preset_name_2: weight_value

subweights:           # Optional - Nested weights per preset
  preset_name_1:
    subweight_1: weight_value
    subweight_2: weight_value

entrance_weights:     # Optional - Entrance shuffle randomization
  none: weight_value
  simple: weight_value
  restricted: weight_value

customizer:           # Optional - Customizer settings
  section_name:
    option_1: weight_value
    option_2: weight_value
```

## Weights Section

The `weights` section defines the main presets that can be rolled. Each preset can have:
1. A numeric weight (simple format)
2. A settings dictionary with embedded weight (advanced format)

### Simple Format (Numeric Weights)

```yaml
weights:
  open: 10          # 10/18 chance (~55.5%)
  standard: 5       # 5/18 chance (~27.8%)
  inverted: 3       # 3/18 chance (~16.7%)
```

### Advanced Format (Settings with Weight)

```yaml
weights:
  open:
    weight: 10
    mode: open
    goal: ganon
    weapons: randomized
  standard:
    weight: 5
    mode: standard
    goal: ganon
    weapons: assured
```

## Subweights Section

Subweights allow you to define conditional settings that apply only when a specific preset is rolled.

```yaml
weights:
  open: 10
  standard: 5

subweights:
  open:                    # Only applies when 'open' is rolled
    normal: 5              # Normal difficulty
    hard: 3                # Hard difficulty
    expert: 1              # Expert difficulty
  standard:                # Only applies when 'standard' is rolled
    keysanity: 4
    no-keysanity: 6
```

**Workflow:**
1. Roll preset from `weights` → Let's say "open" is chosen
2. If "open" has subweights, roll from its subweights → e.g., "hard" is chosen
3. Apply both preset and subweight settings to the seed

## Entrance Shuffle Weights

Control entrance randomization probability:

```yaml
entrance_weights:
  none: 5              # No entrance shuffle
  simple: 3            # Simple entrance shuffle
  restricted: 1        # Restricted entrance shuffle
  full: 1              # Full entrance shuffle
  crossed: 1           # Crossed entrance shuffle
  insanity: 1          # Insanity entrance shuffle
```

## Customizer Section

The customizer section allows randomizing various custom settings:

```yaml
customizer:
  eq:                    # Equipment settings
    progressive: 5       # Progressive equipment
    basic: 3             # Basic equipment
    none: 1              # No special equipment
    
  item_pool:             # Item pool modifications
    normal: 7            # Normal item pool
    hard: 2              # Hard item pool
    expert: 1            # Expert item pool
    
  custom:                # Custom item settings
    on: 1
    off: 4
    
  timed-ohko:            # Timed OHKO mode
    on: 1
    off: 9
    
  triforce-hunt:         # Triforce hunt mode
    on: 2
    off: 8
```

## Complete Example

Here's a complete example mystery weightset:

```yaml
preset_type: mystery

# Main preset weights
weights:
  open: 10
  standard: 5
  inverted: 3

# Subweights for each preset
subweights:
  open:
    normal: 5
    hard: 3
  standard:
    keysanity: 4
    no-keysanity: 6

# Entrance randomization
entrance_weights:
  none: 6
  simple: 3
  restricted: 1

# Customizer settings
customizer:
  eq:
    progressive: 7
    basic: 3
  item_pool:
    normal: 8
    hard: 2
  triforce-hunt:
    on: 1
    off: 9
```

## Mystery Generation Workflow

When a mystery seed is generated:

1. **Roll Preset**: Select from `weights` based on probability
   - Example: "open" is selected

2. **Roll Subweight** (if exists): Select from preset's subweights
   - Example: "hard" is selected from `open` subweights

3. **Roll Entrance Shuffle** (if `entrance_weights` exists):
   - Example: "simple" is selected

4. **Roll Customizer Settings** (if `customizer` exists):
   - Roll each section independently
   - Example: `eq: progressive`, `item_pool: normal`

5. **Generate Seed**: Create seed with all rolled settings combined

## Weight Calculation

Weights are relative probabilities. Higher weights = higher chance.

Example:
```yaml
weights:
  option_a: 10    # 10/(10+5+1) = 62.5% chance
  option_b: 5     # 5/(10+5+1) = 31.25% chance
  option_c: 1     # 1/(10+5+1) = 6.25% chance
```

## SahasrahBot Format Compatibility

The system also supports the original SahasrahBot format with `settings` wrapper:

```yaml
settings:
  weights:
    open: 10
    standard: 5
  subweights:
    open:
      normal: 5
      hard: 3
```

Both formats are equivalent. The service auto-detects the format.

## Validation

Mystery presets are validated when uploaded:

✅ **Valid:**
- Has at least one of: `weights`, `entrance_weights`, `customizer`
- All weight values are numeric
- Weight structures are properly formatted dictionaries

❌ **Invalid:**
- Empty mystery preset (no weights at all)
- Non-dictionary weight structures
- All weights are zero or negative

## Usage

### Via Web UI
1. Navigate to `/presets`
2. Click "Upload Preset"
3. Select randomizer: "alttpr"
4. Paste your mystery YAML
5. Set name, description, and visibility
6. Click "Create"

### Via Discord
```
/mystery preset_name
```

### Via RaceTime.gg
```
!mystery preset_name
```

## Examples from Community

### PogChampionship Mystery
```yaml
weights:
  open: 1
  standard: 1
  inverted: 1
entrance_weights:
  none: 1
  simple: 1
  restricted: 1
  full: 1
```

### Ladder Mystery (Example)
```yaml
weights:
  open: 5
  standard: 5
subweights:
  open:
    normal: 3
    hard: 2
  standard:
    keysanity: 1
    no-keysanity: 4
entrance_weights:
  none: 3
  simple: 2
```

## Tips

1. **Start Simple**: Begin with just `weights` and add complexity gradually
2. **Balance Weights**: Use weights that reflect your desired probability distribution
3. **Test First**: Create a few test seeds to verify the mystery behaves as expected
4. **Document Your Mystery**: Add a clear description explaining the mystery's theme
5. **Public Sharing**: Make mysteries public if you want others to use them

## Technical Details

- Weights are processed by `ALTTPRMysteryService`
- Selection uses Python's `random.choices()` with weights
- Mystery presets are stored in `randomizer_presets` table
- Settings are stored as JSON in the database
- Auto-detection: presence of `weights` key triggers mystery mode

## References

- Original SahasrahBot documentation: (see old bot's mysteryyaml.md)
- ALTTPR API documentation: https://alttpr.com/api
- SahaBot2 source: `application/services/randomizer/alttpr_mystery_service.py`
