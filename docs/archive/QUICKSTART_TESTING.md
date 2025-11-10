# Quick Start Guide for GitHub Coding Agent

This is a condensed guide for the GitHub Coding Agent to quickly set up and test SahaBot2.

## One-Command Setup

```bash
# Install dependencies and set up test environment
pip3 install poetry && \
poetry install && \
poetry run python setup_test_env.py --skip-data
```

## Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test
poetry run pytest tests/test_example.py -v

# Run with coverage
poetry run pytest --cov=application --cov=models
```

## Starting the Application

```bash
# Development mode (port 8080)
poetry run python main.py

# Access at: http://localhost:8080
```

**Note**: Authentication won't work in test mode (uses mock Discord OAuth).

## Key Files

- **`.env.test`** - Test environment configuration (SQLite, mock credentials)
- **`setup_test_env.py`** - Automated test environment setup script
- **`GITHUB_AGENT_TESTING.md`** - Full testing guide
- **`tests/conftest.py`** - Test fixtures and configuration

## What Works in Test Mode

✅ **Database**: SQLite (no MySQL needed)  
✅ **Tests**: Full pytest suite  
✅ **Application**: Starts and runs  
✅ **UI**: Can navigate pages (without auth)

## What Doesn't Work

❌ **Discord OAuth**: Login redirects to Discord (mocked credentials)  
❌ **Discord Bot**: Disabled in test mode  
❌ **External APIs**: RaceTime.gg, Twitch (mocked)

## Common Commands

```bash
# Check environment
poetry run python setup_test_env.py --validate-only

# Run linters
poetry run black --check .
poetry run ruff check .

# View logs
tail -f *.log

# Clean up test database
rm -f test_*.db
```

## Troubleshooting

**Poetry not found**: `pip3 install poetry`  
**Import errors**: `poetry install`  
**DB errors**: Check `.env` has `DB_NAME=:memory:`  
**Test failures**: `poetry run pytest -v --tb=short`

## Architecture Quick Reference

```
UI/API (pages/, api/) 
  ↓ calls
Services (application/services/)
  ↓ uses  
Repositories (application/repositories/)
  ↓ accesses
Models (models/)
```

**Key Principle**: Never access ORM directly from UI/API. Always use services.

## Making Changes

1. **Make your changes** to the code
2. **Run tests**: `poetry run pytest`
3. **Test manually**: Start app and verify UI
4. **Take screenshots** if UI changed (save to `screenshots/`)
5. **Commit**: Git will track changes automatically

## Files to Never Commit

- `.env` (use `.env.test` as template)
- `test_*.db` (SQLite databases)
- `screenshots/` (for debugging only)
- `__pycache__/`, `.pytest_cache/`

---

**For detailed information**, see [GITHUB_AGENT_TESTING.md](GITHUB_AGENT_TESTING.md)
