# SahaBot2 Tools

This directory contains utility scripts and tools for development, testing, and administration.

## Available Tools

### Mock Data Generator

**File**: `generate_mock_data.py`

Generates realistic mock data for testing purposes, including users, organizations, tournaments, matches, and more.

#### Features

- **Users**: Creates users with different permission levels (SUPERADMIN, ADMIN, MODERATOR, USER)
- **Organizations**: Creates organizations with members and permission structures
- **Scheduled Tournaments**: Creates tournaments with matches, players, crew, and seeds
- **Async Tournaments**: Creates async tournaments with pools, permalinks, and race submissions
- **Realistic Data**: Uses realistic names, dates, and relationships
- **Flexible Configuration**: Presets or custom parameters
- **Safe by Default**: Requires explicit confirmation to delete existing data

#### Usage

```bash
# Quick start with small preset
poetry run python tools/generate_mock_data.py --preset small

# Use different presets
poetry run python tools/generate_mock_data.py --preset tiny    # Minimal data
poetry run python tools/generate_mock_data.py --preset medium  # Moderate data
poetry run python tools/generate_mock_data.py --preset large   # Extensive data

# Custom configuration
poetry run python tools/generate_mock_data.py --users 50 --orgs 5 --tournaments 10

# Clear existing data first (WARNING: destructive!)
poetry run python tools/generate_mock_data.py --preset small --clear-existing

# See all options
poetry run python tools/generate_mock_data.py --help
```

#### Presets

| Preset | Users | Orgs | Tournaments | Async Tournaments | Matches/Tournament |
|--------|-------|------|-------------|-------------------|-------------------|
| tiny   | 5     | 1    | 1           | 1                 | 3                 |
| small  | 20    | 3    | 5           | 3                 | 10                |
| medium | 50    | 5    | 10          | 5                 | 15                |
| large  | 100   | 10   | 20          | 10                | 20                |

#### Generated Data

The tool generates:

- **Users**: Discord-authenticated users with realistic usernames and IDs
- **Organizations**: Gaming organizations with members and permissions
- **Organization Memberships**: Users joined to organizations with varying permissions
- **Scheduled Tournaments**: Tournaments with matches scheduled across time
- **Matches**: Tournament matches with 2-4 players, some completed with results
- **Match Seeds**: Game seeds/ROMs for matches (70% of matches)
- **Crew Members**: Commentators, trackers, and restreamers for matches
- **Async Tournaments**: Asynchronous racing tournaments
- **Async Pools**: Collections of seeds within tournaments
- **Permalinks**: Race seeds with randomizer permalinks
- **Race Submissions**: Player race submissions with times and VODs

#### Example Output

```
MOCK DATA GENERATION SUMMARY
============================================================

USERS: 20 total
  - SUPERADMIN: 1
  - ADMIN: 2
  - MODERATOR: 2
  - USER: 15

ORGANIZATIONS: 3 total
  - Total memberships: 35
  - Total permissions: 24

TOURNAMENTS: 5 total (4 active)
  - Total matches: 50
  - Completed matches: 15

ASYNC TOURNAMENTS: 3 total (3 active)
  - Total pools: 10
  - Total permalinks: 58
  - Total races: 142
  - Approved races: 35

SAMPLE USERS (for testing):
------------------------------------------------------------
  AliceSmith123 (SUPERADMIN)
    Discord ID: 123456789012345678
    Email: alicesmith123@example.com

  BobJohnson456 (ADMIN)
    Discord ID: 234567890123456789
    Email: bobjohnson456@example.com
  ...
```

#### Safety Features

- **Confirmation Required**: Prompts for confirmation when using `--clear-existing`
- **No Silent Data Loss**: Existing data is preserved unless explicitly cleared
- **Logged Operations**: All operations are logged for visibility
- **Validation**: Uses proper Tortoise ORM validation
- **Transaction Safety**: Uses async/await properly for database operations

#### Testing Workflow

1. **Development Testing**:
   ```bash
   poetry run python tools/generate_mock_data.py --preset tiny
   ```

2. **UI/Feature Testing**:
   ```bash
   poetry run python tools/generate_mock_data.py --preset small
   ```

3. **Performance Testing**:
   ```bash
   poetry run python tools/generate_mock_data.py --preset large
   ```

4. **Clean Slate Testing**:
   ```bash
   poetry run python tools/generate_mock_data.py --preset small --clear-existing
   ```

#### Architecture Compliance

The tool follows SahaBot2 architectural principles:

✅ **Async/Await**: All database operations are async  
✅ **Type Hints**: Full type annotations  
✅ **Docstrings**: Comprehensive documentation  
✅ **Logging Standards**: Uses logging framework with lazy % formatting  
✅ **ORM Usage**: Uses Tortoise ORM properly  
✅ **Multi-Tenant**: Respects organization isolation  
✅ **Realistic Data**: Generates data matching production patterns  

#### Troubleshooting

**Error: "Database connection failed"**
- Ensure database is running and `.env` is configured
- Check `DATABASE_URL` in config

**Error: "Module not found"**
- Run from project root: `poetry run python tools/generate_mock_data.py`
- Ensure virtual environment is activated

**Too much/little data**
- Adjust preset or use custom parameters
- See `--help` for all options

## Future Tools

Planned tools for future development:

- **Database Migration Helper**: Migrate data from original SahasrahBot
- **Backup/Restore Tool**: Database backup and restore utilities
- **Data Cleanup Tool**: Remove old/invalid data
- **Performance Profiler**: Profile database queries and operations
- **Data Export Tool**: Export data to CSV/JSON for analysis

## Contributing

When adding new tools:

1. Create script in `tools/` directory
2. Add execute permissions: `chmod +x tools/your_tool.py`
3. Use Poetry for dependencies: `poetry run python tools/your_tool.py`
4. Follow async/await patterns for database operations
5. Include comprehensive `--help` documentation
6. Update this README with tool description
7. Add logging for visibility
8. Handle errors gracefully

## References

- **Architecture Guide**: [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)
- **Patterns & Conventions**: [`docs/PATTERNS.md`](../docs/PATTERNS.md)
- **Database Models**: [`docs/reference/DATABASE_MODELS_REFERENCE.md`](../docs/reference/DATABASE_MODELS_REFERENCE.md)
