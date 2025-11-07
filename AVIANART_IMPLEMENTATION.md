# Avianart Randomizer Implementation Summary

## Overview

This implementation adds support for the Avianart door randomizer (Hi, I'm Cody's ALTTPR door randomizer) as a distinct randomizer in SahaBot2, separate from ALTTPR. The implementation includes both a service layer for seed generation and a RaceTime.gg command handler for race room integration.

## Implementation Based On

- **Original SahasrahBot**: https://github.com/tcprescott/sahasrahbot
  - Reference files:
    - `alttprbot/alttprgen/randomizer/avianart.py`
    - `alttprbot_discord/util/avianart_discord.py`
- **SahaBot2 Architecture**: Adapted to follow the new service/repository pattern and RaceTime integration

## Files Changed/Created

### New Files
1. **`application/services/randomizer/avianart_service.py`** (164 lines)
   - Core service for Avianart API integration
   - Implements async polling for seed generation
   - File select code extraction and normalization
   - Comprehensive error handling

2. **`tests/unit/test_avianart_service.py`** (287 lines)
   - 10 unit tests covering all scenarios
   - Tests success, failures, timeouts, edge cases
   - Mock-based testing without API calls

3. **`tests/unit/test_avianart_handler.py`** (219 lines)
   - 6 unit tests for RaceTime command
   - Tests all error conditions and user scenarios

4. **`tools/test_avianart_manual.py`** (161 lines)
   - Manual integration test script
   - Demonstrates proper integration
   - Usage examples and documentation

### Modified Files
1. **`application/services/randomizer/randomizer_service.py`**
   - Added Avianart to factory method
   - Added 'avianart' to list_randomizers()

2. **`application/services/randomizer/__init__.py`**
   - Added AvianartService export

3. **`racetime/command_handlers.py`**
   - Added handle_avianart() function
   - Registered in BUILTIN_HANDLERS

## Key Features

### AvianartService
- **API Integration**: Calls `https://avianart.games/api.php`
- **Preset-Based**: Uses API preset names (no database storage)
- **Async Polling**: Waits up to 2 minutes for seed generation
- **Error Handling**: Validates API responses, handles timeouts
- **File Select Codes**: Extracts and normalizes codes to SahasrahBot format
- **Standard Result**: Returns RandomizerResult compatible with other services

### !avianart Command
- **Usage**: `!avianart <preset_name>`
- **Integration**: Works in RaceTime.gg race rooms
- **No Auth Required**: Can be used by any race participant
- **Race Mode**: Always generates race seeds (race=True)
- **Response Format**: URL, file select code, and version info
- **Error Handling**: Graceful error messages for all failure modes

## API Details

### Avianart API Endpoints
1. **Generate**: `POST /api.php?action=generate&preset={preset}`
   - Payload: `[{"args": {"race": true}}]`
   - Returns: `{"response": {"hash": "..."}}`

2. **Poll Status**: `GET /api.php?action=permlink&hash={hash}`
   - Returns status until 'finished' or 'failure'
   - Contains spoiler data with file select code

### File Select Code Mapping
Maps Avianart names to SahasrahBot standard names:
- Bomb → Bombs
- Powder → Magic Powder
- Rod → Ice Rod
- Ocarina → Flute
- Bug Net → Bugnet
- Bottle → Empty Bottle
- Potion → Green Potion
- Cane → Somaria
- Pearl → Moon Pearl
- Key → Big Key

## Testing

### Unit Tests (16 tests total)
- **Service Tests (10)**:
  - Successful generation
  - Missing preset error
  - API failure handling
  - Timeout handling
  - Race mode parameter
  - Code extraction (basic, mapped, mixed)
  - Missing/invalid response data

- **Handler Tests (6)**:
  - Successful command
  - Missing arguments
  - ValueError handling
  - TimeoutError handling
  - Generic exception handling
  - No-auth usage

### Test Results
```
✓ 16 Avianart tests passing
✓ 268 total unit tests passing
✓ 0 CodeQL security alerts
✓ Manual integration test passing
```

## Usage Examples

### Python Service
```python
from application.services.randomizer import AvianartService

service = AvianartService()
result = await service.generate(preset='open', race=True)

print(f"URL: {result.url}")
print(f"Hash: {result.hash_id}")
print(f"Code: {result.metadata['file_select_code']}")
print(f"Version: {result.metadata['version']}")
```

### RandomizerService Factory
```python
from application.services.randomizer import RandomizerService

service = RandomizerService().get_randomizer('avianart')
result = await service.generate(preset='open', race=True)
```

### RaceTime.gg Command
```
!avianart open
```

Response:
```
Avianart seed generated! https://avianart.games/perm/ABC123 | 
Code: Bow/Bombs/Hookshot/Mushroom/Lamp | Version: 1.0.0
```

## Architecture Compliance

✓ **Separation of Concerns**: Service handles all business logic
✓ **Logging Standards**: Uses logging framework with % formatting
✓ **Async/Await**: All external calls are async
✓ **Type Hints**: Full type annotations on all functions
✓ **Docstrings**: Comprehensive documentation
✓ **Error Handling**: Robust validation and error messages
✓ **Testing**: Comprehensive unit test coverage
✓ **Security**: CodeQL scan clean, no vulnerabilities

## Design Decisions

1. **Distinct Randomizer**: Avianart is separate from ALTTPR (not a variant)
2. **No Database Presets**: Uses API preset names directly as specified in requirements
3. **Race Mode Default**: Always uses race=True for RaceTime integration
4. **No Authentication**: Command doesn't require Discord auth (unlike !mystery)
5. **File Select Code**: Maintains compatibility with original SahasrahBot format
6. **Polling Strategy**: 5-second intervals, max 2 minutes (24 attempts)
7. **Error Handling**: Comprehensive validation to prevent KeyError/TypeError

## Migration from Original SahasrahBot

If migrating from the original SahasrahBot:
- Avianart functionality is now a first-class randomizer
- No need to set `avianart=True` flag on ALTTPR generation
- Use `!avianart <preset>` command instead of flag-based generation
- File select codes maintain the same format and mapping

## Future Enhancements (Not Implemented)

- Database preset storage (currently not supported per requirements)
- Spoiler log support (Avianart API doesn't currently support)
- Custom preset YAML upload via web UI
- Discord bot integration (prefix commands vs RaceTime commands)

## References

- **Avianart Website**: https://avianart.games
- **Original SahasrahBot**: https://github.com/tcprescott/sahasrahbot
- **SahaBot2 Architecture**: See `docs/ARCHITECTURE.md`
- **SahaBot2 Patterns**: See `docs/PATTERNS.md`
