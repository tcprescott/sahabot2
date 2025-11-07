# CodeQL Security and Quality Checks

This directory contains custom CodeQL queries for detecting anti-patterns specific to SahaBot2, as defined in the [Copilot Instructions](../copilot-instructions.md).

## Overview

CodeQL is a semantic code analysis engine that helps identify security vulnerabilities and code quality issues. We use it to automatically detect violations of our coding standards and architectural patterns.

## Workflow

The CodeQL analysis runs:
- On every push to `main`
- On every pull request to `main`
- Weekly on Sunday at 00:00 UTC (scheduled scan)

Results are available in the **Security** tab of the GitHub repository.

## Custom Queries

We have implemented custom queries to detect the following anti-patterns:

### 1. Print in Application Code (`print-in-application-code.ql`)
**Severity**: Warning

Detects use of `print()` for logging in application code. The `print()` function should only be used in:
- Test scripts (`tests/`, `test_*.py`, `*_test.py`)
- Utility scripts (`tools/`)
- Demo scripts (`demo_*.py`)
- Check scripts (`check_*.py`)

**Recommended Fix**: Use the logging framework instead:
```python
# ❌ Wrong
print("User logged in")

# ✅ Correct
logger = logging.getLogger(__name__)
logger.info("User %s logged in", user_id)
```

### 2. F-String in Logging (`f-string-in-logging.ql`)
**Severity**: Warning

Detects use of f-strings in logging statements. F-strings are evaluated immediately, even if the log level is disabled, wasting CPU cycles.

**Recommended Fix**: Use lazy % formatting:
```python
# ❌ Wrong
logger.info(f"User {user.id} logged in")

# ✅ Correct
logger.info("User %s logged in", user.id)
```

### 3. Deprecated datetime.utcnow() (`deprecated-utcnow.ql`)
**Severity**: Warning

Detects use of deprecated `datetime.utcnow()`. This method is deprecated in Python 3.12+ and creates timezone-naive datetimes, which can cause TypeErrors when mixing with timezone-aware datetimes from the database.

**Recommended Fix**: Use timezone-aware datetime:
```python
# ❌ Wrong
from datetime import datetime
current_time = datetime.utcnow()

# ✅ Correct
from datetime import datetime, timezone
current_time = datetime.now(timezone.utc)
```

### 4. ORM in UI/API (`orm-in-ui-api.ql`)
**Severity**: Error

Detects direct ORM model queries in UI pages or API routes. This violates our separation of concerns architecture.

**Recommended Fix**: Use services for business logic and data access:
```python
# ❌ Wrong (in pages/ or api/routes/)
users = await User.filter(organization_id=org_id).all()

# ✅ Correct (use a service)
user_service = UserService()
users = await user_service.get_users_by_organization(org_id, current_user)
```

### 5. Inline Imports (`inline-imports.ql`)
**Severity**: Warning

Detects import statements inside functions. Imports should be at module level for better readability and performance.

**Recommended Fix**: Move imports to the top of the file:
```python
# ❌ Wrong
def my_function():
    import os
    return os.getcwd()

# ✅ Correct
import os

def my_function():
    return os.getcwd()
```

### 6. Deprecated AuthorizationService (`deprecated-authorization-service.ql`)
**Severity**: Warning

Detects use of deprecated `AuthorizationService`. The new policy-based authorization system should be used instead.

**Recommended Fix**: Use UIAuthorizationHelper or Permission enum:
```python
# ❌ Wrong
auth_z = AuthorizationService()
if auth_z.can_manage_tournaments(user, org_id):
    # ...

# ✅ Correct (UI layer)
ui_auth = UIAuthorizationHelper()
if await ui_auth.can_manage_tournaments(user, org_id):
    # ...

# ✅ Correct (Service layer)
from application.policies.organization_permissions import OrganizationPermissions
checker = OrganizationPermissions(org_id)
if await checker.can_manage_tournaments(user):
    # ...
```

### 7. None user_id in Events (`none-user-id-in-events.ql`)
**Severity**: Error

Detects use of `None` for `user_id` in event emissions. Events should always have a valid user ID.

**Recommended Fix**: Use current_user.id or SYSTEM_USER_ID:
```python
# ❌ Wrong
await EventBus.emit(EntityCreatedEvent(
    user_id=None,  # Wrong!
    organization_id=org_id,
    entity_id=entity.id
))

# ✅ Correct (user action)
await EventBus.emit(EntityCreatedEvent(
    user_id=current_user.id,
    organization_id=org_id,
    entity_id=entity.id
))

# ✅ Correct (system action)
from models import SYSTEM_USER_ID
await EventBus.emit(EntityCreatedEvent(
    user_id=SYSTEM_USER_ID,
    organization_id=org_id,
    entity_id=entity.id
))
```

### 8. UIAuthorizationHelper in Service Layer (`ui-auth-helper-in-service.ql`)
**Severity**: Warning

Detects use of `UIAuthorizationHelper` in service layer. Services should use the policy framework directly.

**Recommended Fix**: Use policy framework directly:
```python
# ❌ Wrong (in application/services/)
ui_auth = UIAuthorizationHelper()
if await ui_auth.can_manage_tournaments(user, org_id):
    # ...

# ✅ Correct (in application/services/)
from application.policies.organization_permissions import OrganizationPermissions
checker = OrganizationPermissions(org_id)
if await checker.can_manage_tournaments(user):
    # ...
```

## Configuration

### `codeql-config.yml`
Configures which paths to include/exclude from analysis:

**Included paths:**
- `api/**`
- `application/**`
- `components/**`
- `discordbot/**`
- `middleware/**`
- `models/**`
- `pages/**`
- `racetime/**`
- `views/**`

**Excluded paths:**
- `migrations/**` - Database migrations
- `tests/**` - Test files
- `tools/**` - Utility scripts
- `**/test_*.py`, `**/*_test.py` - Test files
- `setup_test_env.py`, `demo_*.py`, `check_*.py` - Utility scripts

### `qlpack.yml`
Defines the query pack metadata and dependencies on CodeQL's Python library.

## Running Locally

To run CodeQL locally (optional):

1. Install the CodeQL CLI: https://github.com/github/codeql-cli-binaries
2. Create a CodeQL database:
   ```bash
   codeql database create sahabot2-db --language=python --source-root .
   ```
3. Run the queries:
   ```bash
   codeql database analyze sahabot2-db .github/codeql/queries/ --format=sarif-latest --output=results.sarif
   ```
4. View results:
   ```bash
   codeql sarif print results.sarif
   ```

## Viewing Results

Results are available in:
1. **GitHub Security tab**: Navigate to **Security** → **Code scanning alerts**
2. **Pull Request checks**: CodeQL results appear as check annotations on PRs
3. **Workflow runs**: View detailed logs in the **Actions** tab

## Severity Levels

- **Error**: Must be fixed before merging (architectural violations)
- **Warning**: Should be fixed but may have exceptions (style and maintainability)

## Adding New Queries

To add a new custom query:

1. Create a `.ql` file in `.github/codeql/queries/`
2. Follow the CodeQL query structure (see existing queries)
3. Add appropriate metadata comments (name, description, severity, etc.)
4. Test the query locally if possible
5. Update this README with documentation

## Resources

- [CodeQL Documentation](https://codeql.github.com/docs/)
- [CodeQL for Python](https://codeql.github.com/docs/codeql-language-guides/codeql-for-python/)
- [Writing CodeQL Queries](https://codeql.github.com/docs/writing-codeql-queries/)
- [CodeQL Query Help](https://codeql.github.com/codeql-query-help/)

## Maintenance

- Review and update queries when coding standards change
- Adjust severity levels based on impact
- Add new queries for new anti-patterns
- Keep queries in sync with `.github/copilot-instructions.md`
