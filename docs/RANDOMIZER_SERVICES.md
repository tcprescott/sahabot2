# Randomizer Services Implementation

This document describes the implementation of randomizer services in SahaBot2.

## Overview

The randomizer services provide a unified interface for generating seeds across multiple game randomizers. This implementation is based on the original SahasrahBot's `alttprgen` module but has been modernized and adapted to the SahaBot2 architecture.

## Architecture

### Service Layer

All randomizer functionality is implemented in the service layer following SahaBot2's architectural patterns:

```
application/
  services/
    randomizer/
      __init__.py                  # Package exports
      randomizer_service.py        # Main coordinator/factory service
      alttpr_service.py           # A Link to the Past Randomizer
      aosr_service.py             # Aria of Sorrow Randomizer
      bingosync_service.py        # Bingosync integration
      ctjets_service.py           # Chrono Trigger Jets of Time
      ffr_service.py              # Final Fantasy Randomizer
      ootr_service.py             # Ocarina of Time Randomizer
      sm_service.py               # Super Metroid Randomizer
      smb3r_service.py            # Super Mario Bros 3 Randomizer
      smz3_service.py             # SMZ3 Combo Randomizer
      z1r_service.py              # Zelda 1 Randomizer
      README.md                   # Detailed usage documentation
```

### Key Components

1. **RandomizerService**: Main coordinator service that provides a factory pattern for accessing individual randomizer services.

2. **RandomizerResult**: Dataclass for consistent return values across all randomizers:
   - `url`: URL to access the generated seed
   - `hash_id`: Unique identifier for the seed
   - `settings`: Dictionary of settings used
   - `randomizer`: Name of the randomizer
   - `permalink`: Optional permalink (if different from url)
   - `spoiler_url`: Optional spoiler log URL
   - `metadata`: Additional randomizer-specific data

3. **Individual Service Classes**: Each randomizer has its own service implementing the specific API or generation logic for that randomizer.

## Implemented Randomizers

### API-Based Randomizers
These randomizers make HTTP requests to external APIs:

- **ALTTPR** (A Link to the Past Randomizer) - `alttpr.com`
- **OOTR** (Ocarina of Time Randomizer) - `ootrandomizer.com`
- **SM** (Super Metroid) - `sm.samus.link`
- **SMZ3** (Super Metroid/ALTTP Combo) - `samus.link`
- **CTJets** (Chrono Trigger Jets of Time) - `ctjot.com`
- **Bingosync** - `bingosync.com`

### URL-Based Randomizers
These randomizers generate URLs with parameters:

- **AOSR** (Aria of Sorrow Randomizer) - `aosrando.surge.sh`
- **Z1R** (Zelda 1 Randomizer)
- **FFR** (Final Fantasy Randomizer) - `finalfantasyrandomizer.com`
- **SMB3R** (Super Mario Bros 3 Randomizer)

## Usage Examples

### Basic Usage

```python
from application.services.randomizer import RandomizerService

# Get a randomizer instance
randomizer = RandomizerService()
alttpr = randomizer.get_randomizer('alttpr')

# Generate a seed
result = await alttpr.generate(
    settings={'mode': 'open', 'goal': 'ganon'},
    tournament=True
)

print(f"Seed URL: {result.url}")
print(f"Hash: {result.hash_id}")
```

### List Available Randomizers

```python
from application.services.randomizer import RandomizerService

randomizer = RandomizerService()
available = randomizer.list_randomizers()
# Returns: ['alttpr', 'aosr', 'z1r', 'ootr', 'ffr', 'smb3r', 'sm', 'smz3', 'ctjets', 'bingosync']
```

### Direct Service Import

```python
from application.services.randomizer import ALTTPRService

service = ALTTPRService()
result = await service.generate(settings={...})
```

## Configuration

Some randomizers require configuration via environment variables:

```bash
# .env file
ALTTPR_BASEURL=https://alttpr.com  # Optional, defaults to this
OOTR_API_KEY=your_api_key_here     # Required for OoTR
```

## Dependencies

New dependencies added for randomizer support:

- `httpx`: Already included, used for async HTTP requests
- `beautifulsoup4`: Added for HTML parsing (CTJets, Bingosync)

## Design Decisions

### Why Service Layer Only?

The initial implementation focuses solely on the service layer because:

1. **Separation of Concerns**: Services handle business logic independent of presentation
2. **Flexibility**: Services can be used by API routes, Discord bot commands, or UI without duplication
3. **Testability**: Services can be tested without UI/database dependencies
4. **Incremental Development**: Repository layer and UI can be added later as needed

### Factory Pattern

The `RandomizerService` uses a factory pattern with lazy imports to:

- Avoid circular dependencies
- Minimize memory footprint (only load what's used)
- Provide a clean, consistent interface
- Allow runtime selection of randomizers

### Async Throughout

All methods are async to:

- Match the existing SahaBot2 architecture
- Support non-blocking HTTP requests
- Enable concurrent seed generation if needed
- Integrate seamlessly with NiceGUI and FastAPI

## Not Implemented (Yet)

The following features from the original SahasrahBot were intentionally deferred:

1. **ALTTPR Door Randomizer**: Requires local ROM files and external tools (EnemizerCLI, flips)
2. **ALTTPR Mystery**: Complex weighted preset selection logic
3. **Database Persistence**: No models/repositories for storing generated seeds
4. **Preset Management**: No preset loading/saving functionality
5. **API Routes**: No REST API endpoints (can be added when needed)
6. **Discord Commands**: No Discord bot integration (can be added later)

These can be added incrementally as needed.

## Future Enhancements

Potential additions for the future:

1. **Database Models**: Add models for storing generated seeds, presets, etc.
2. **Repository Layer**: Add repositories for data access if persistence is needed
3. **API Routes**: Add REST API endpoints for web/mobile access
4. **Discord Commands**: Add Discord bot commands for seed generation
5. **Preset System**: Implement preset loading/saving/sharing
6. **Rate Limiting**: Add rate limiting for external API calls
7. **Caching**: Cache certain results to reduce API calls
8. **Webhook Support**: Support webhooks for async seed generation
9. **Statistics**: Track seed generation statistics

## Testing

A basic test script is provided in `tools/test_randomizers.py` that demonstrates:

- Factory pattern usage
- Individual randomizer instantiation
- Basic seed generation

Note: Full integration tests require a complete environment with all dependencies installed.

## Migration from Original SahasrahBot

Key differences from the original implementation:

| Original | SahaBot2 | Reason |
|----------|----------|--------|
| Flask app | NiceGUI + FastAPI | Modern async framework |
| Single-tenant | Multi-tenant | Organization-scoped data |
| Synchronous | Asynchronous | Better performance |
| Database models included | Service layer only | Incremental development |
| Preset files on disk | Not yet implemented | Will use database |
| Direct ORM access | Repository pattern | Separation of concerns |

## References

- Original SahasrahBot: https://github.com/tcprescott/sahasrahbot/tree/master/alttprbot/alttprgen
- SahaBot2 Architecture: See `COMPONENTS_GUIDE.md` and Copilot instructions
- Service Layer Pattern: See existing services in `application/services/`
