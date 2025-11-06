# GitHub Coding Agent Testing Guide

This guide explains how to set up and run the SahaBot2 application within the GitHub Coding Agent environment for automated testing of changes.

## Overview

The GitHub Coding Agent can test changes to SahaBot2 by running the application in a lightweight testing environment that doesn't require external services like MySQL, Discord OAuth, or RaceTime.gg integration.

## Quick Start

```bash
# 1. Install Poetry (if not already installed)
pip3 install poetry

# 2. Install dependencies
poetry install

# 3. Set up test environment (creates SQLite DB, generates mock data)
poetry run python setup_test_env.py

# 4. Run tests
poetry run pytest

# 5. Start application (optional, for UI testing)
poetry run python main.py
```

## Prerequisites

The test environment requires:

- **Python 3.12+** - Available in GitHub Actions runners
- **Poetry** - Python package manager (auto-installed if needed)
- **SQLite** - Built into Python, no additional installation needed

**NOT required:**
- ❌ MySQL database
- ❌ Discord OAuth2 application
- ❌ Discord Bot token
- ❌ RaceTime.gg OAuth credentials
- ❌ Twitch OAuth credentials

## Environment Setup

### Automatic Setup (Recommended)

Use the provided setup script:

```bash
poetry run python setup_test_env.py
```

This script will:
1. ✅ Create `.env` from `.env.test` (if needed)
2. ✅ Initialize SQLite database
3. ✅ Run database migrations via Tortoise ORM schema generation
4. ✅ Generate mock data for testing
5. ✅ Validate the environment

### Manual Setup

If you need to set up manually:

```bash
# 1. Copy test environment configuration
cp .env.test .env

# 2. Install dependencies
poetry install

# 3. Initialize database (SQLite will be created automatically)
# The application will generate schemas on first run
```

## Mock Data Generation

The test environment can generate realistic mock data for testing:

```bash
# Tiny dataset (5 users, 1 org, 1 tournament) - fastest
poetry run python setup_test_env.py --preset tiny

# Small dataset (20 users, 3 orgs, 5 tournaments) - good for most tests
poetry run python setup_test_env.py --preset small

# Skip data generation
poetry run python setup_test_env.py --skip-data
```

See [`tools/README.md`](tools/README.md) for more details on mock data generation.

## Running Tests

### All Tests

```bash
poetry run pytest
```

### Specific Test Suites

```bash
# Unit tests only
poetry run pytest -m unit

# Integration tests only
poetry run pytest -m integration

# Specific test file
poetry run pytest tests/test_example.py

# Specific test function
poetry run pytest tests/test_example.py::test_basic_math

# With verbose output
poetry run pytest -v

# With coverage report
poetry run pytest --cov=application --cov=models
```

### Test Configuration

Tests are configured in `pytest.ini`:
- **Test discovery**: `tests/` directory
- **Async support**: Auto-enabled via `pytest-asyncio`
- **Markers**: `unit`, `integration`, `slow`, `asyncio`
- **Database**: SQLite in-memory (per-test isolation)

## Running the Application

### Development Mode

```bash
# Start with auto-reload
poetry run python main.py

# Or use the start script
./start.sh dev
```

The application will be available at http://localhost:8080

**Note**: In test mode with `.env.test`:
- Discord OAuth is mocked (login won't work)
- Discord bot is disabled
- External services are stubbed
- SQLite database is used

### Testing UI Changes

For UI changes, you can:

1. **Take screenshots** of the UI:
   - Use browser DevTools or screenshot tools
   - Save to `screenshots/` directory (git-ignored)

2. **Test responsive design**:
   - Use browser DevTools mobile emulation
   - Test on various viewport sizes

3. **Verify functionality**:
   - Navigate through pages
   - Test forms and interactions
   - Check error handling

## Database Management

### SQLite Database

The test environment uses SQLite instead of MySQL:

```bash
# View database file (if using file-based SQLite)
sqlite3 test_sahabot2.db

# List tables
.tables

# Query data
SELECT * FROM user;

# Exit SQLite
.exit
```

### Schema Generation

The test environment auto-generates database schemas using Tortoise ORM:

```python
# Automatic schema generation in test mode
await Tortoise.generate_schemas()
```

**Note**: In production, use Aerich migrations (`poetry run aerich upgrade`).

### Resetting the Database

```bash
# Clear and regenerate with fresh mock data
poetry run python setup_test_env.py --preset tiny

# Or manually delete the database
rm test_sahabot2.db
poetry run python setup_test_env.py
```

## CI/CD Integration

### GitHub Actions Workflow

Example workflow for automated testing:

```yaml
name: Test

on:
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install Poetry
        run: pip3 install poetry
      
      - name: Install dependencies
        run: poetry install
      
      - name: Set up test environment
        run: poetry run python setup_test_env.py --preset tiny
      
      - name: Run tests
        run: poetry run pytest -v
      
      - name: Run linters (optional)
        run: |
          poetry run black --check .
          poetry run ruff check .
```

### GitHub Copilot Workspace

The GitHub Copilot Coding Agent can:

1. **Read the codebase** to understand changes needed
2. **Run setup**: `poetry install && poetry run python setup_test_env.py`
3. **Make code changes** to implement features or fix bugs
4. **Run tests**: `poetry run pytest` to validate changes
5. **Start the app**: `poetry run python main.py` to verify UI changes
6. **Take screenshots** to document UI changes
7. **Commit changes** once validated

## Architecture Considerations

### Service Layer Testing

The application uses a clean architecture with separation of concerns:

```
UI/API → Services → Repositories → Models
```

When testing:
- **Unit tests**: Test services and repositories in isolation
- **Integration tests**: Test full stack with real database
- **UI tests**: Manual verification in browser or automated with Playwright

### Mock External Services

External services are disabled in test mode:

- **Discord Bot**: `DISCORD_BOT_ENABLED=False`
- **Discord OAuth**: Mock credentials (authentication won't work)
- **RaceTime.gg**: Mock credentials
- **Twitch**: Mock credentials

For integration testing with external services, use separate staging credentials.

### Multi-Tenant Isolation

The application is multi-tenant (organization-scoped). When testing:
- Use `sample_organization` fixture
- Ensure proper organization context in tests
- Validate tenant isolation

## Troubleshooting

### Poetry Not Found

```bash
pip3 install poetry
```

### Database Connection Error

Check that you're using the test environment:

```bash
# Verify .env is using SQLite
cat .env | grep DB_NAME
# Should show: DB_NAME=:memory:
```

### Import Errors

Ensure dependencies are installed:

```bash
poetry install
```

### Test Failures

Run with verbose output to see details:

```bash
poetry run pytest -v --tb=short
```

### Application Won't Start

Check for missing configuration:

```bash
poetry run python setup_test_env.py --validate-only
```

## Best Practices for GitHub Coding Agent

1. **Always set up test environment first**
   ```bash
   poetry run python setup_test_env.py --preset tiny
   ```

2. **Run tests frequently** during development
   ```bash
   poetry run pytest -v
   ```

3. **Take screenshots** of UI changes
   - Save to `screenshots/` directory
   - Include in PR description

4. **Validate changes end-to-end**
   - Run linters if available
   - Test affected features manually
   - Check for regressions

5. **Use minimal mock data** for speed
   - `tiny` preset for quick tests
   - `small` preset for comprehensive testing

6. **Clean up after testing**
   - Remove temporary files
   - Don't commit `.env` or `test_*.db`

## References

- **Main README**: [`README.md`](README.md) - Project overview and setup
- **Architecture**: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - System design
- **Patterns**: [`docs/PATTERNS.md`](docs/PATTERNS.md) - Code conventions
- **Testing**: [`tests/README.md`](tests/README.md) - Test suite documentation
- **Mock Data**: [`tools/README.md`](tools/README.md) - Data generation guide

## Support

For issues with the test environment:
1. Check this guide first
2. Review error messages carefully
3. Validate environment: `poetry run python setup_test_env.py --validate-only`
4. Check GitHub Actions logs for CI failures
5. Open an issue on GitHub with details

---

**Last Updated**: 2025-11-06
