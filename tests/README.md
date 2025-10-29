# Testing Guide for SahaBot2

This document provides comprehensive information about the testing infrastructure for SahaBot2.

## Overview

The test suite is organized into two main categories:

- **Unit Tests** (`tests/unit/`) - Test individual components in isolation
- **Integration Tests** (`tests/integration/`) - Test component interactions and workflows

## Directory Structure

```
tests/
├── __init__.py                       # Tests package
├── conftest.py                       # Shared pytest fixtures
├── fixtures/                         # Test data and mocks
│   ├── __init__.py
│   ├── mock_discord.py              # Discord API mocks
│   └── mock_database.py             # Database test data
├── unit/                            # Unit tests
│   ├── __init__.py
│   ├── test_models_user.py         # User model tests
│   ├── test_models_audit_log.py    # AuditLog model tests
│   ├── test_repositories_user.py   # UserRepository tests
│   ├── test_repositories_audit.py  # AuditRepository tests
│   ├── test_services_user.py       # UserService tests
│   ├── test_services_authorization.py  # AuthorizationService tests
│   ├── test_services_audit.py      # AuditService tests
│   ├── test_bot_commands.py        # Bot command tests
│   └── test_bot_client.py          # Bot client tests
└── integration/                     # Integration tests
    ├── __init__.py
    ├── test_auth_flow.py           # OAuth2 flow tests
    ├── test_user_workflows.py      # User management workflow tests
    ├── test_bot_workflows.py       # Bot workflow tests
    └── test_database.py            # Database integration tests
```

## Running Tests

### Run All Tests
```bash
poetry run pytest
```

### Run Unit Tests Only
```bash
poetry run pytest tests/unit/ -m unit
```

### Run Integration Tests Only
```bash
poetry run pytest tests/integration/ -m integration
```

### Run Specific Test File
```bash
poetry run pytest tests/unit/test_models_user.py
```

### Run Specific Test
```bash
poetry run pytest tests/unit/test_models_user.py::TestUserModel::test_create_user
```

### Run with Coverage
```bash
poetry run pytest --cov=. --cov-report=html
```

### Run with Verbose Output
```bash
poetry run pytest -v
```

## Test Fixtures

### Database Fixtures

- **`db`** - Initializes an in-memory SQLite database for testing
- **`clean_db`** - Provides a clean database state for each test
- **`sample_user`** - Creates a regular user for testing
- **`admin_user`** - Creates an admin user for testing

### Discord Fixtures

- **`mock_discord_user`** - Mock Discord user data
- **`mock_discord_interaction`** - Mock Discord interaction for bot command testing

### Usage Example

```python
import pytest
from models.user import User

@pytest.mark.asyncio
async def test_create_user(clean_db, mock_discord_user):
    """Test creating a user."""
    user = await User.create(
        discord_id=int(mock_discord_user["id"]),
        discord_username=mock_discord_user["username"],
        # ... other fields
    )
    
    assert user.discord_id == int(mock_discord_user["id"])
    assert user.discord_username == mock_discord_user["username"]
```

## Writing Tests

### Unit Tests

Unit tests should:
- Test a single component in isolation
- Use mocks for external dependencies
- Be fast and deterministic
- Not require database or network access (except for model/repository tests)

Example:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from application.services.user_service import UserService

@pytest.mark.unit
@pytest.mark.asyncio
class TestUserService:
    async def test_get_user_by_id(self):
        """Test retrieving user by ID."""
        # Create mock repository
        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_user)
        
        # Test service with mocked repository
        service = UserService(repository=mock_repo)
        user = await service.get_user_by_id(1)
        
        assert user.id == 1
        mock_repo.get_by_id.assert_called_once_with(1)
```

### Integration Tests

Integration tests should:
- Test interactions between components
- Use real database connections (test database)
- Test complete workflows
- Be marked with `@pytest.mark.integration`

Example:
```python
import pytest
from application.services.user_service import UserService
from models.user import Permission

@pytest.mark.integration
@pytest.mark.asyncio
class TestUserWorkflow:
    async def test_update_user_permission(self, sample_user):
        """Test updating user permission."""
        service = UserService()
        
        # Update permission
        updated = await service.update_user_permission(
            sample_user.id, 
            Permission.ADMIN
        )
        
        # Verify in database
        user = await User.get(id=sample_user.id)
        assert user.permission == Permission.ADMIN
```

## Test Markers

Use pytest markers to categorize tests:

- `@pytest.mark.unit` - Unit test
- `@pytest.mark.integration` - Integration test
- `@pytest.mark.slow` - Slow running test
- `@pytest.mark.asyncio` - Async test (required for async tests)

## Best Practices

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **One Assertion Per Test**: Focus tests on single behavior
3. **Use Descriptive Names**: Test names should describe what they test
4. **Mock External Dependencies**: Use mocks for external APIs, Discord, etc.
5. **Clean Up After Tests**: Use fixtures to ensure clean state
6. **Test Edge Cases**: Don't just test the happy path
7. **Use Type Hints**: Maintain type safety in tests
8. **Add Docstrings**: Document what each test is verifying

## Continuous Integration

Tests should be run automatically on:
- Every commit (pre-commit hook)
- Pull requests (GitHub Actions)
- Before deployment

## Coverage Goals

- **Overall Coverage**: > 80%
- **Services**: > 90%
- **Models**: > 85%
- **Repositories**: > 90%

## Future Enhancements

- [ ] Add performance benchmarking tests
- [ ] Add end-to-end UI tests
- [ ] Add load testing for bot commands
- [ ] Add mutation testing
- [ ] Set up automated test reporting
- [ ] Add contract tests for Discord API

## Troubleshooting

### Tests Not Found
- Ensure test files start with `test_`
- Ensure test functions start with `test_`
- Check pytest.ini configuration

### Async Tests Failing
- Ensure `@pytest.mark.asyncio` is present
- Check event loop configuration in conftest.py

### Database Tests Failing
- Ensure Tortoise ORM is properly initialized
- Check database fixture configuration
- Verify model imports are correct

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Tortoise ORM Testing](https://tortoise.github.io/contrib/unittest.html)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
