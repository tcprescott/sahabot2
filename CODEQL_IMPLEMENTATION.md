# CodeQL Anti-Pattern Checks Implementation

## Summary

This document summarizes the implementation of CodeQL security and quality checks for SahaBot2, which automatically detect anti-patterns specified in the copilot instructions.

## Implementation Date
November 7, 2024

## What Was Added

### 1. CodeQL Workflow (`.github/workflows/codeql.yml`)
- Runs on every push and pull request to `main` branch
- Scheduled weekly scan every Sunday at 00:00 UTC
- Uses Python language analysis
- Includes custom queries in addition to standard security queries

### 2. Custom CodeQL Queries (8 total)

Located in `.github/codeql/queries/`:

1. **print-in-application-code.ql**
   - Detects: Use of `print()` for logging in application code
   - Severity: Warning
   - Excludes: Test files, tools, demo scripts

2. **f-string-in-logging.ql**
   - Detects: F-strings in logging statements (logger.info, etc.)
   - Severity: Warning
   - Reason: F-strings are evaluated immediately, wasting CPU

3. **deprecated-utcnow.ql**
   - Detects: Use of deprecated `datetime.utcnow()`
   - Severity: Warning
   - Reason: Deprecated in Python 3.12+, creates timezone-naive datetimes

4. **orm-in-ui-api.ql**
   - Detects: Direct ORM queries in UI pages or API routes
   - Severity: Error
   - Reason: Violates separation of concerns architecture

5. **inline-imports.ql**
   - Detects: Import statements inside functions
   - Severity: Warning
   - Reason: Hurts readability and performance

6. **deprecated-authorization-service.ql**
   - Detects: Use of deprecated `AuthorizationService`
   - Severity: Warning
   - Reason: Replaced by policy-based authorization system

7. **none-user-id-in-events.ql**
   - Detects: Event emissions with `user_id=None`
   - Severity: Error
   - Reason: Events must have valid user ID (current_user.id or SYSTEM_USER_ID)

8. **ui-auth-helper-in-service.ql**
   - Detects: UIAuthorizationHelper usage in service layer
   - Severity: Warning
   - Reason: Service layer should use policy framework directly

### 3. Configuration Files

- **codeql-config.yml**: Path filters for what to scan
- **qlpack.yml**: Query pack metadata and dependencies
- **anti-patterns.qls**: Query suite definition

### 4. Documentation

- **.github/codeql/README.md**: Comprehensive documentation of all queries with examples
- **Updated .github/copilot-instructions.md**: Added section on CodeQL and when to add queries
- **Updated SECURITY.md**: Added "Automated Code Analysis" section
- **Updated README.md**: Added CodeQL information to Security section

## Path Filters

### Included in Analysis
- `api/**`
- `application/**`
- `components/**`
- `discordbot/**`
- `middleware/**`
- `models/**`
- `pages/**`
- `racetime/**`
- `views/**`

### Excluded from Analysis
- `migrations/**`
- `tests/**`
- `tools/**`
- `**/test_*.py`, `**/*_test.py`
- `setup_test_env.py`, `demo_*.py`, `check_*.py`

## Integration with Development Workflow

1. **Pull Requests**: CodeQL runs automatically and reports results as check annotations
2. **Security Tab**: All results visible in GitHub Security → Code scanning alerts
3. **Weekly Scans**: Scheduled analysis ensures ongoing compliance
4. **CI/CD**: Integrated with existing GitHub Actions workflows

## Benefits

1. **Automated Enforcement**: Coding standards enforced automatically
2. **Early Detection**: Anti-patterns caught in PR review
3. **Consistent Quality**: Same standards applied to all contributors
4. **Documentation**: Each anti-pattern documented with correct examples
5. **Security**: Security scanning integrated with quality checks
6. **Maintainability**: New anti-patterns can be added as CodeQL queries

## Maintenance

### When to Add New Queries

When adding new "don't" rules to copilot instructions:
1. Create CodeQL query in `.github/codeql/queries/`
2. Add documentation to `.github/codeql/README.md`
3. Test locally if possible
4. Update this document

### Query Improvement

Queries were improved based on code review feedback:
- **inline-imports.ql**: Now catches all import-from statements, not just star imports
- **f-string-in-logging.ql**: Catches more logging patterns (log, LOG, logging module)
- **orm-in-ui-api.ql**: Better false positive reduction with type checking

## Testing

- Initial scan: **0 alerts** ✅
- All queries tested against codebase
- No false positives in current code
- Queries designed to be precise (high precision)

## Future Enhancements

Potential areas for expansion:
- Add queries for new anti-patterns as they're identified
- Create queries for performance anti-patterns
- Add queries for testing best practices
- Integration with other security tools

## References

- CodeQL Documentation: https://codeql.github.com/docs/
- CodeQL for Python: https://codeql.github.com/docs/codeql-language-guides/codeql-for-python/
- Custom Query Examples: `.github/codeql/queries/*.ql`
- Query Documentation: `.github/codeql/README.md`

---

**Implementation Status**: ✅ Complete
**Security Scan Results**: 0 alerts
**Code Review**: Passed with improvements implemented
