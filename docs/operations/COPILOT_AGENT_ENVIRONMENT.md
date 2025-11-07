# GitHub Copilot Coding Agent Environment

This document describes the customized development environment for GitHub Copilot coding agent when working on SahaBot2.

## Overview

The GitHub Copilot coding agent operates in an isolated GitHub Actions environment that is automatically configured when the agent starts working on an issue or pull request. The environment setup is defined in `.github/workflows/copilot-setup-steps.yml`.

## Environment Configuration

### Workflow File

**Location**: `.github/workflows/copilot-setup-steps.yml`

This workflow is automatically triggered when Copilot coding agent begins work. It must be on the repository's default branch to be recognized by the agent.

### Setup Steps

The environment configuration includes:

1. **Python 3.12 Installation**
   - Uses `actions/setup-python@v5`
   - Includes pip caching for faster setup

2. **Poetry Package Manager**
   - Installed globally via pip
   - Version verification included

3. **Dependency Caching**
   - Poetry dependencies cached using `actions/cache@v4`
   - Cache key based on `poetry.lock` for version consistency

4. **Python Dependencies**
   - All project dependencies installed via `poetry install`
   - Installed in non-interactive mode for CI/CD compatibility

5. **Test Environment Setup**
   - SQLite database (no MySQL required)
   - Mock credentials for external services (Discord, RaceTime, Twitch)
   - Configured via `setup_test_env.py --preset tiny --skip-data`

6. **Environment Verification**
   - Python version check
   - Key dependency verification (NiceGUI, Tortoise ORM, FastAPI)
   - Status display for debugging

## Agent Configuration

### Custom Agent Profile

**Location**: `.github/agents/default.agent.md`

This profile defines custom behavior for the Copilot coding agent:

- **Name**: default
- **Description**: The default agent with baseline instructions
- **Special Rules**:
  - Does not generate database migrations (maintainer handles merges)

### Repository Instructions

**Location**: `.github/copilot-instructions.md`

Comprehensive instructions for the coding agent covering:

- Project architecture and principles
- Code patterns and conventions
- Security requirements
- Testing standards
- Multi-tenant isolation rules

## Testing the Configuration

### Local Testing

While the Copilot agent environment runs in GitHub Actions, you can verify the setup steps locally:

```bash
# Set up test environment
poetry run python setup_test_env.py --preset tiny --skip-data

# Run tests
poetry run pytest -v

# Verify configuration policies
poetry run python tools/check_config_policy.py
```

### GitHub Actions Testing

The workflow can be manually triggered or tested via:

- **Workflow Dispatch**: Manually trigger from GitHub Actions UI
- **Push**: Push changes to `.github/workflows/copilot-setup-steps.yml`
- **Pull Request**: Open PR modifying the workflow file

## Environment Variables

The test environment (`.env.test`) provides minimal configuration:

### Database
- **SQLite** in-memory database (`:memory:`)
- No MySQL server required

### External Services (Mocked)
- Discord OAuth2: Mock client credentials
- RaceTime.gg: Mock OAuth2 credentials
- Twitch: Mock OAuth2 credentials
- Discord Bot: Disabled for testing
- Sentry: Disabled for testing

### Application Settings
- **Environment**: `testing`
- **Debug Mode**: Enabled
- **API Rate Limiting**: Relaxed (1000/min)

## Development Workflow

When Copilot coding agent works on an issue:

1. **Environment Setup** (automatic)
   - Workflow runs `copilot-setup-steps` job
   - Dependencies installed from cache (fast)
   - Test environment configured

2. **Agent Access** (automatic)
   - Agent has access to Python 3.12
   - All project dependencies available
   - Can run tests, linters, builds

3. **Task Execution** (automatic)
   - Agent makes code changes
   - Runs tests to verify changes
   - Uses services layer (never direct ORM access)
   - Follows architecture patterns from instructions

4. **Verification** (automatic)
   - Tests pass
   - No lint/policy violations
   - Security checks pass (CodeQL)

## Troubleshooting

### Setup Step Failures

If the `copilot-setup-steps` workflow fails:

1. Check workflow logs in GitHub Actions
2. Verify `poetry.lock` is committed and up-to-date
3. Ensure `.env.test` has valid test configuration
4. Check for dependency conflicts in `pyproject.toml`

### Agent Not Using Configuration

If the agent doesn't seem to use the custom setup:

1. Verify workflow file is on the default branch
2. Check workflow file is named exactly `copilot-setup-steps.yml`
3. Ensure job is named exactly `copilot-setup-steps`
4. Review workflow logs to see if it ran

### Slow Environment Setup

The workflow includes caching for Poetry dependencies:

- First run: ~2-3 minutes (fresh install)
- Cached runs: ~30-60 seconds (cache hit)

If setup is consistently slow:
- Check cache hit rate in workflow logs
- Verify cache key matches `poetry.lock` hash
- Consider pruning unnecessary dependencies

## Best Practices

### Workflow Maintenance

1. **Keep Minimal**: Only include essential setup steps
2. **Use Caching**: Leverage GitHub Actions cache for dependencies
3. **Verify Steps**: Include verification steps to catch issues early
4. **Monitor Performance**: Track setup time and optimize as needed

### Security

1. **No Secrets**: Don't use real credentials in test environment
2. **Read-Only**: Workflow has minimal permissions (`contents: read`)
3. **Mock Services**: Use mock values for external service credentials

### Testing

1. **Run Locally**: Test setup steps on local machine first
2. **Manual Trigger**: Use workflow dispatch to test changes
3. **Monitor Logs**: Check agent session logs for setup issues

## References

- [GitHub Docs: Customize Agent Environment](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/customize-the-agent-environment)
- [GitHub Docs: Custom Agents Configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [Repository Instructions](.github/copilot-instructions.md)
- [Test Environment Setup](../../setup_test_env.py)

## Related Documentation

- [Architecture](../ARCHITECTURE.md) - System architecture and principles
- [Testing Guide](../GITHUB_AGENT_TESTING.md) - Automated testing for agents
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Production deployment
- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) - Common issues and solutions
