# Sentry.io Integration

SahaBot2 integrates with [Sentry.io](https://sentry.io) for error tracking and performance monitoring. This integration helps identify and debug issues in production environments.

## Features

- **Error Tracking**: Automatically captures and reports exceptions from both the web application and Discord bot
- **Performance Monitoring**: Tracks transaction performance and identifies slow operations
- **Profiling**: CPU profiling to identify performance bottlenecks
- **Request Context**: Captures request details, user information, and custom context
- **Breadcrumbs**: Logs leading up to errors for better debugging
- **Release Tracking**: Associates errors with specific application versions

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Sentry Configuration (optional)
SENTRY_DSN=https://your_key@sentry.io/your_project_id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=1.0
SENTRY_PROFILES_SAMPLE_RATE=1.0
```

### Configuration Options

- **SENTRY_DSN** (Optional): Your Sentry project DSN. If not set, Sentry will not be initialized.
  - Get this from: https://sentry.io/settings/projects/
  - Example: `https://examplePublicKey@o0.ingest.sentry.io/0`

- **SENTRY_ENVIRONMENT** (Optional): Environment name for error grouping
  - Defaults to the value of `ENVIRONMENT` if not set
  - Recommended values: `development`, `staging`, `production`

- **SENTRY_TRACES_SAMPLE_RATE** (Optional): Sample rate for performance monitoring (0.0 to 1.0)
  - Default: `1.0` (100% of transactions)
  - For high-traffic apps, use lower values like `0.1` (10%)

- **SENTRY_PROFILES_SAMPLE_RATE** (Optional): Sample rate for profiling (0.0 to 1.0)
  - Default: `1.0` (100% of transactions)
  - For high-traffic apps, use lower values like `0.1` (10%)

## How It Works

### Initialization

Sentry is initialized early in the application lifecycle in `main.py`:

```python
from application.utils.sentry_init import init_sentry
init_sentry()
```

This initialization:
1. Checks if `SENTRY_DSN` is configured
2. Sets up FastAPI, AsyncIO, and Logging integrations
3. Configures sample rates for performance monitoring
4. Gracefully skips if DSN is not provided

### Integrations

#### FastAPI Integration

- Automatically captures HTTP request errors
- Tracks request performance as transactions
- Includes request headers, body, and user information

#### Discord Bot Integration

The Discord bot includes Sentry error tracking in error handlers:

```python
async def on_error(self, event_method: str, *args, **kwargs):
    logger.error('Error in %s', event_method, exc_info=True)
    sentry_sdk.capture_exception()

async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
    with sentry_sdk.push_scope() as scope:
        scope.set_context("discord_command", {
            "command": str(ctx.command),
            "author": str(ctx.author),
            "guild": str(ctx.guild) if ctx.guild else None,
            "channel": str(ctx.channel),
        })
        sentry_sdk.capture_exception(error)
```

#### AsyncIO Integration

- Tracks async task errors
- Monitors performance of async operations
- Captures unhandled exceptions in async tasks

#### Logging Integration

- Captures log messages as breadcrumbs (INFO level and above)
- Sends ERROR level logs as events to Sentry
- Provides context for debugging issues

## Testing Sentry Integration

### Test Endpoint

A test endpoint is available at `/health/sentry-test` to verify Sentry is working:

```bash
curl http://localhost:8080/health/sentry-test
```

This endpoint:
- Intentionally raises an HTTP 500 error
- Includes custom tags and context
- Should appear in your Sentry dashboard within seconds

### Unit Tests

Run the Sentry integration tests:

```bash
poetry run pytest tests/unit/test_sentry_integration.py -v
```

## Best Practices

### Development vs Production

**Development:**
```bash
SENTRY_DSN=  # Leave empty to disable
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=1.0  # 100% sampling for testing
```

**Production:**
```bash
SENTRY_DSN=https://your_key@sentry.io/your_project_id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% sampling to reduce costs
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10% profiling
```

### Custom Context

Add custom context to errors in your code:

```python
import sentry_sdk

# Add tags for filtering
with sentry_sdk.push_scope() as scope:
    scope.set_tag("feature", "tournaments")
    scope.set_context("tournament", {
        "id": tournament.id,
        "name": tournament.name
    })
    # Your code that might raise an exception
    result = await some_operation()
```

### User Context

User information is automatically captured from FastAPI requests when `send_default_pii=True`. For additional user context:

```python
sentry_sdk.set_user({
    "id": user.id,
    "username": user.discord_username,
    "organization_id": org.id
})
```

### Breadcrumbs

Add custom breadcrumbs for debugging:

```python
sentry_sdk.add_breadcrumb(
    category='tournament',
    message='Creating new tournament',
    level='info',
    data={'name': tournament_name}
)
```

## Privacy Considerations

Sentry captures error information including:
- Stack traces and error messages
- Request headers and user information
- Performance data
- Custom context you provide

**Important:**
- Our privacy policy discloses Sentry data collection
- Sensitive data (passwords, tokens) should not be logged
- User PII is captured only when errors occur
- Configure `send_default_pii=False` if you want to disable automatic PII capture

## Troubleshooting

### Sentry Not Capturing Errors

1. **Check DSN Configuration**
   ```bash
   echo $SENTRY_DSN
   ```

2. **Check Logs**
   Look for initialization message:
   ```
   INFO - Sentry initialized successfully (environment=production, ...)
   ```
   
   Or if DSN not configured:
   ```
   INFO - Sentry DSN not configured, skipping Sentry initialization
   ```

3. **Test the Integration**
   ```bash
   curl http://localhost:8080/health/sentry-test
   ```
   
   Check your Sentry dashboard at https://sentry.io

4. **Check Sample Rates**
   If `SENTRY_TRACES_SAMPLE_RATE=0`, no events will be captured.

### Errors Not Appearing

- **Propagation Delay**: Errors may take 5-10 seconds to appear in Sentry
- **Filtered Errors**: Check your Sentry project's inbound filters
- **Rate Limits**: Free tier has monthly event limits
- **Sample Rate**: If set to less than 1.0, not all errors are captured

## Resources

- [Sentry Python SDK Documentation](https://docs.sentry.io/platforms/python/)
- [FastAPI Integration](https://docs.sentry.io/platforms/python/integrations/fastapi/)
- [AsyncIO Integration](https://docs.sentry.io/platforms/python/integrations/asyncio/)
- [Sentry Privacy Policy](https://sentry.io/privacy/)

## Related Files

- `application/utils/sentry_init.py` - Sentry initialization
- `config.py` - Configuration settings
- `main.py` - Application startup with Sentry init
- `discordbot/client.py` - Discord bot error handlers with Sentry
- `tests/unit/test_sentry_integration.py` - Integration tests
