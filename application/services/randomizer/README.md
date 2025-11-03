# Randomizer Services

This package provides services for generating seeds for various game randomizers. Each randomizer has its own service class that handles the specifics of that randomizer's API.

## Architecture

- **RandomizerService**: Main coordinator service with factory pattern for getting randomizer instances
- **RandomizerResult**: Dataclass for consistent return values across all randomizers
- **Individual Services**: One service per randomizer (e.g., `ALTTPRService`, `SMService`, etc.)

## Available Randomizers

### ALTTPR - A Link to the Past Randomizer
```python
from application.services.randomizer import ALTTPRService

service = ALTTPRService()
result = await service.generate(
    settings={
        'mode': 'open',
        'goal': 'ganon',
        'weapons': 'randomized',
        # ... other settings
    },
    tournament=True,
    spoilers='off'
)

print(f"Seed URL: {result.url}")
print(f"Hash: {result.hash_id}")
```

### SM - Super Metroid Randomizer
```python
from application.services.randomizer import SMService

service = SMService()
result = await service.generate(
    settings={
        'mode': 'standard',
        'itemProgression': 'normal',
        # ... other settings
    },
    tournament=True,
    spoilers=False
)
```

### SMZ3 - Super Metroid/ALTTP Combo Randomizer
```python
from application.services.randomizer import SMZ3Service

service = SMZ3Service()
result = await service.generate(
    settings={
        'mode': 'normal',
        # ... combo settings
    },
    tournament=True
)
```

### OOTR - Ocarina of Time Randomizer
```python
from application.services.randomizer import OOTRService

service = OOTRService()
result = await service.generate(
    settings={
        'world_count': 1,
        'create_spoiler': True,
        # ... other settings
    },
    version='6.1.0',
    encrypt=True
)
```

### AOSR - Aria of Sorrow Randomizer
```python
from application.services.randomizer import AOSRService

service = AOSRService()
result = await service.generate(
    enemyRando='on',
    startingRoom='random',
    # ... other flags as kwargs
)
```

### Z1R - Zelda 1 Randomizer
```python
from application.services.randomizer import Z1RService

service = Z1RService()
result = await service.generate(flags='your_flags_here')
```

### FFR - Final Fantasy Randomizer
```python
from application.services.randomizer import FFRService

service = FFRService()
result = await service.generate(
    flags='your_flags_string',
    seed=12345  # optional
)
```

### SMB3R - Super Mario Bros 3 Randomizer
```python
from application.services.randomizer import SMB3RService

service = SMB3RService()
result = await service.generate()
```

### CTJets - Chrono Trigger Jets of Time
```python
from application.services.randomizer import CTJetsService

service = CTJetsService()
result = await service.generate(
    settings={
        'flag1': 'value1',
        # ... other settings
    },
    version='3_1_0'
)
```

### Bingosync - Bingo Card Generation
```python
from application.services.randomizer import BingosyncService

service = BingosyncService(nickname="MyBot")
result = await service.generate(
    room_name="My Bingo Room",
    passphrase="password123",
    game_type="ocarina-of-time",
    lockout_mode='1'
)

print(f"Room URL: {result.url}")
print(f"Room ID: {result.metadata['room_id']}")
```

## Using the Factory Pattern

You can also use the `RandomizerService` factory to get randomizers by name:

```python
from application.services.randomizer import RandomizerService

randomizer_service = RandomizerService()

# Get a specific randomizer
alttpr = randomizer_service.get_randomizer('alttpr')
result = await alttpr.generate(settings={...})

# List all available randomizers
available = randomizer_service.list_randomizers()
print(available)
# ['alttpr', 'aosr', 'z1r', 'ootr', 'ffr', 'smb3r', 'sm', 'smz3', 'ctjets', 'bingosync']
```

## Configuration

Some randomizers require configuration via environment variables:

```bash
# ALTTPR Base URL (optional, defaults to https://alttpr.com)
ALTTPR_BASEURL=https://alttpr.com

# OoTR API Key (required for OoTR)
OOTR_API_KEY=your_api_key_here
```

## Return Value Structure

All randomizer services return a `RandomizerResult` dataclass with the following fields:

```python
@dataclass
class RandomizerResult:
    url: str                          # URL to access the seed
    hash_id: str                      # Unique identifier for the seed
    settings: Dict[str, Any]          # Settings used to generate the seed
    randomizer: str                   # Name of the randomizer
    permalink: Optional[str] = None   # Permalink to the seed (if different from url)
    spoiler_url: Optional[str] = None # URL to spoiler log (if available)
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata
```

## Error Handling

All services may raise:
- `httpx.HTTPError`: If API requests fail
- `ValueError`: If required parameters are missing or invalid

Example error handling:

```python
import httpx
from application.services.randomizer import ALTTPRService

service = ALTTPRService()
try:
    result = await service.generate(settings={...})
except httpx.HTTPError as e:
    print(f"API request failed: {e}")
except ValueError as e:
    print(f"Invalid parameters: {e}")
```

## Notes

- All services use `httpx.AsyncClient` for HTTP requests
- All methods are async and should be awaited
- Services follow the same patterns as other application services
- No database persistence is implemented by default (can be added later)
- Services are stateless and can be instantiated as needed

## Future Enhancements

Potential future additions:
- ALTTPR Door Randomizer (requires local ROM processing)
- ALTTPR Mystery (weighted preset selection)
- Database models for storing generated seeds
- API routes for web/Discord bot access
- Preset management system
- Rate limiting for external API calls
