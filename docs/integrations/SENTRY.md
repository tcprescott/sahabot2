# Sentry.io Integration

SahaBot2 integrates with [Sentry.io](https://sentry.io) for error tracking and performance monitoring. This integration helps identify and debug issues in production environments.

## Features

- **Error Tracking**: Automatically captures and reports exceptions from both the web application and Discord bot
- **Frontend Monitoring**: Captures JavaScript errors and client-side issues in the browser
- **Performance Monitoring**: Tracks transaction performance and identifies slow operations (backend and frontend)
- **Profiling**: CPU profiling to identify performance bottlenecks
- **Request Context**: Captures request details, user information, and custom context
- **Breadcrumbs**: Logs leading up to errors for better debugging
- **Release Tracking**: Associates errors with specific application versions
- **Session Replay**: Optional recording of user sessions (disabled by default)

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
  - Default: `0.1` (10% of transactions)
  - Use `1.0` in development for full coverage
  - For high-traffic production apps, use lower values like `0.05` (5%)

- **SENTRY_PROFILES_SAMPLE_RATE** (Optional): Sample rate for profiling (0.0 to 1.0)
  - Default: `0.1` (10% of transactions)
  - Use `1.0` in development for full coverage
  - For high-traffic production apps, use lower values like `0.05` (5%)

- **SENTRY_RELEASE** (Optional): Release version identifier for error grouping
  - If not set, automatically uses git commit SHA if available
  - Falls back to `sahabot2@0.1.0` if git is not available
  - Format: `sahabot2@version` or `sahabot2@commit-sha`

## How It Works

### Initialization

Sentry is initialized in two places:

1. **Backend** - Early in the application lifecycle in `main.py`:
   ```python
   from application.utils.sentry_init import init_sentry
   init_sentry()
   ```

2. **Frontend** - Loaded on every page via `BasePage._load_sentry_browser()`:
   - Dynamically loads Sentry browser SDK from CDN
   - Configures with same DSN and environment as backend
   - Only loads if SENTRY_DSN is configured

This provides full-stack error tracking and performance monitoring.

### Integrations

#### FastAPI Integration

- Automatically captures HTTP request errors
- Tracks request performance as transactions
- Includes request headers, body, and user information

#### Browser/Frontend Integration

- Captures JavaScript errors and unhandled promise rejections
- Tracks client-side performance (page loads, user interactions)
- Captures user interaction breadcrumbs (clicks, navigation)
- Session replay (optional, disabled by default)
- Automatically loaded on all pages via BasePage

**Note**: Browser monitoring uses the same DSN and sample rates as backend monitoring. Frontend errors appear in Sentry with `platform: browser` and `framework: nicegui` tags.

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

A test endpoint is available at `/health/sentry-test` to verify Sentry is working.

**Note**: This endpoint is only available when `DEBUG=True` to prevent abuse in production.

```bash
# Development (DEBUG=True)
curl http://localhost:8080/health/sentry-test
# Returns: 500 error that should appear in Sentry

# Production (DEBUG=False)
curl http://localhost:8080/health/sentry-test
# Returns: 403 Forbidden
```

This endpoint:
- Only works in DEBUG mode
- Intentionally raises an HTTP 500 error
- Includes custom tags and context
- Should appear in your Sentry dashboard within seconds

### Testing Browser Monitoring

To test that frontend monitoring is working:

1. **Open browser developer console** (F12)
2. **Check for initialization message**:
   ```
   Sentry browser monitoring initialized {environment: "development", tracesSampleRate: 0.1}
   ```

3. **Trigger a test error in console**:
   ```javascript
   // This will be captured by Sentry
   throw new Error("Test frontend error for Sentry");
   ```

4. **Check Sentry dashboard** - Error should appear within seconds with:
   - `platform: browser` tag
   - `framework: nicegui` tag
   - Browser and device information
   - User session context

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
SENTRY_PROFILES_SAMPLE_RATE=1.0  # 100% profiling
```

**Production:**
```bash
SENTRY_DSN=https://your_key@sentry.io/your_project_id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% sampling to reduce costs (default)
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10% profiling (default)
SENTRY_RELEASE=sahabot2@v1.0.0  # Optional: explicit version
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

### DSN Security Model

The Sentry DSN is a **public client-side credential** by design:
- Frontend monitoring requires the DSN to be accessible in browser JavaScript
- DSNs are intentionally safe to expose in client-side code and HTML
- Security is enforced through:
  - **Rate limiting** on the Sentry project (prevents abuse)
  - **Allowed origins** configuration (restrict which domains can send events)
  - **Inbound filters** (filter unwanted data)
  - **Project settings** (control data retention, scrubbing rules)

**Best Practices:**
- Configure allowed origins in your Sentry project settings to restrict which domains can send events
- Set up rate limits to prevent quota exhaustion
- Use inbound filters to block spam or malicious events
- Never put secrets/passwords in error messages or custom context

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

- `application/utils/sentry_init.py` - Backend Sentry initialization
- `static/js/monitoring/sentry-browser.js` - Frontend Sentry initialization
- `components/base_page.py` - Loads Sentry browser monitoring on all pages
- `config.py` - Configuration settings
- `main.py` - Application startup with backend Sentry init
- `discordbot/client.py` - Discord bot error handlers with Sentry
- `tests/unit/test_sentry_integration.py` - Integration tests
