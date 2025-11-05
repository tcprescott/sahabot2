# Troubleshooting Guide

Common issues, error messages, debugging procedures, and solutions for SahaBot2.

**Last Updated**: November 4, 2025  
**Scope**: Development, staging, and production troubleshooting

---

## Table of Contents

- [Getting Started](#getting-started)
- [Startup Issues](#startup-issues)
- [Database Issues](#database-issues)
- [Discord Integration Issues](#discord-integration-issues)
- [RaceTime Integration Issues](#racetime-integration-issues)
- [API Issues](#api-issues)
- [UI/Frontend Issues](#uifrontend-issues)
- [Performance Issues](#performance-issues)
- [Debugging Procedures](#debugging-procedures)
- [Log Analysis](#log-analysis)
- [Getting Help](#getting-help)

---

## Getting Started

### Before Troubleshooting

1. **Check application logs**: Most issues are logged with details
2. **Check environment variables**: Verify `.env` has required values
3. **Check dependencies**: Verify all services are running (database, Discord bot)
4. **Verify connectivity**: Test network access to external services
5. **Review recent changes**: Check what was changed before issue started

### Log Locations

**Development**:
```bash
# Console output (stdout/stderr)
# Set in terminal where application runs
# Use Ctrl+C to view recent logs

# Or check startup script output
./start.sh dev 2>&1 | tee app.log
```

**Production**:
```bash
# Depends on deployment method
# Systemd: journalctl -u sahabot2 -f
# Docker: docker logs -f container_name
# PM2: pm2 logs sahabot2
```

### Enable Debug Logging

Set environment variable:
```bash
# Add to .env
DEBUG=true

# Or in code to see verbose logs
LOGGING_LEVEL=DEBUG
```

---

## Startup Issues

### Application Won't Start

**Error**: Application exits immediately after `./start.sh dev`

**Debugging Steps**:

1. **Check Python installed**:
```bash
python --version
poetry --version
```

2. **Check dependencies installed**:
```bash
poetry install
```

3. **Check required environment variables**:
```bash
# Should output the values
echo $SECRET_KEY
echo $DISCORD_BOT_TOKEN
echo $DB_PASSWORD
```

4. **Check for .env file**:
```bash
ls -la .env
# If missing: cp .env.example .env
# Then edit with your values
```

5. **Run with verbose output**:
```bash
poetry run uvicorn main:app --reload 2>&1 | head -100
```

6. **Check Python syntax errors**:
```bash
python -m py_compile *.py
```

**Common Causes**:
- ❌ Missing .env file
- ❌ Missing required environment variables
- ❌ Python dependencies not installed
- ❌ Port already in use
- ❌ Syntax error in configuration

### "Module not found" Error

**Error**: `ModuleNotFoundError: No module named 'xyz'`

**Solution**:
```bash
# Reinstall dependencies
poetry install

# Or run with poetry
poetry run python main.py

# Clear Python cache if still fails
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete
```

### "Failed to connect to database"

**Error**: `pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")`

See [Database Issues](#database-issues) section below.

### Discord Bot Won't Start

**Error**: Application starts but Discord bot commands don't work

**Debugging**:
```bash
# Check if bot is enabled
echo $DISCORD_BOT_ENABLED  # Should be true

# Check bot token is set
echo $DISCORD_BOT_TOKEN  # Should show a value

# Check bot has permissions in Discord
# See Discord Integration Issues section
```

---

## Database Issues

### Can't Connect to Database

**Error**: 
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server on 'localhost'")
```

**Debugging Steps**:

1. **Check MySQL is running**:
```bash
# macOS (Homebrew)
brew services list | grep mysql

# Ubuntu/Linux
sudo systemctl status mysql

# Windows
services.msc (look for MySQL)

# Docker
docker ps | grep mysql
```

2. **Test connection manually**:
```bash
mysql -h localhost -u sahabot2 -p
# Enter password when prompted
# If successful, you'll see: mysql>
```

3. **Check database credentials in .env**:
```bash
cat .env | grep DB_
# Verify: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
```

4. **Verify database exists**:
```bash
mysql -u sahabot2 -p
> SHOW DATABASES;  # Should see 'sahabot2'
```

5. **Check database URL**:
```bash
python
>>> from config import settings
>>> print(settings.safe_database_url)
mysql://sahabot2:***@localhost:3306/sahabot2
```

**Solutions**:

| Problem | Solution |
|---------|----------|
| MySQL not running | Start MySQL service: `brew services start mysql` or equivalent |
| Database doesn't exist | Create database: `CREATE DATABASE sahabot2;` |
| Wrong credentials | Verify DB_USER, DB_PASSWORD, DB_HOST in .env |
| Wrong port | Check DB_PORT (default 3306), verify MySQL port with `mysql -h localhost -u sahabot2 -p -e "SELECT 1;"` |
| Connection refused | Check firewall, verify MySQL is listening on configured port |

### Database Migrations Failed

**Error**: `alembic.util.exc.CommandError: Can't find identifier`

**Solution**:

1. **Check migration files exist**:
```bash
ls migrations/models/
```

2. **Run migrations**:
```bash
poetry run aerich upgrade
```

3. **Check migration status**:
```bash
poetry run aerich heads
```

4. **See migration history**:
```bash
poetry run aerich history
```

5. **Rollback if needed**:
```bash
poetry run aerich downgrade  # Back one version
```

**Common Issues**:
- ❌ Migrations directory not initialized: `poetry run aerich init-db`
- ❌ Model files changed without creating migration
- ❌ Multiple migration heads (conflicting migrations)

### Table Does Not Exist

**Error**: `pymysql.err.ProgrammingError: (1146, "Table 'sahabot2.users' doesn't exist")`

**Solution**:

1. **Initialize database**:
```bash
poetry run aerich init-db
```

2. **Or run migrations if they exist**:
```bash
poetry run aerich upgrade
```

3. **Verify tables exist**:
```bash
mysql sahabot2
> SHOW TABLES;
```

---

## Discord Integration Issues

### Discord OAuth Won't Work

**Symptoms**: Login button doesn't work, redirect loop, "invalid redirect URI"

**Debugging**:

1. **Check Discord credentials in .env**:
```bash
echo $DISCORD_CLIENT_ID      # Should be numeric
echo $DISCORD_CLIENT_SECRET  # Should be a string
echo $DISCORD_REDIRECT_URI   # Should be your app URL
```

2. **Verify Discord app configuration**:
   - Go to https://discord.com/developers/applications
   - Select your application
   - Check OAuth2 settings match .env

3. **Test OAuth manually**:
```bash
# In browser console (F12 → Console)
// Check if auth endpoint is correct
const clientId = 'YOUR_CLIENT_ID';
const redirectUri = 'http://localhost:8080/auth/callback';
const scope = 'identify+email+guilds';
const authUrl = `https://discord.com/api/oauth2/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=${scope}`;
console.log(authUrl);  // Open this URL
```

**Common Issues**:

| Issue | Cause | Solution |
|-------|-------|----------|
| "Invalid redirect URI" | URI doesn't match Discord settings | Update Discord app settings to match DISCORD_REDIRECT_URI |
| Login loop | Session not persisting | Clear browser cookies: DevTools → Application → Cookies |
| 404 on callback | OAuth route not registered | Check pages/auth.py is imported in frontend.py |
| "Invalid client ID" | Credentials wrong | Verify DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET |

### Discord Bot Not Responding

**Symptoms**: Bot is in Discord server but commands don't work

**Debugging**:

1. **Check bot is online**:
   - In Discord, check if bot shows as online (next to its name)
   - If offline: Check application logs for connection errors

2. **Check bot has permissions**:
   - In Discord server: Right-click bot → View All Permissions
   - Required: Read Messages, Send Messages, Embed Links, Use Slash Commands
   - If missing: Re-invite bot with correct scopes

3. **Check bot token**:
```bash
echo $DISCORD_BOT_TOKEN  # Should be a token
```

4. **Check application logs**:
```bash
# Look for bot startup messages
./start.sh dev 2>&1 | grep -i "bot\|discord"
```

5. **Check command registration**:
```bash
# Discord may not have synced commands yet
# Try waiting 1 minute and typing `/` in Discord chat
# Commands should appear

# Or force sync (in dev console):
# /reload all  (if admin)
```

**Solutions**:

| Problem | Solution |
|---------|----------|
| Bot offline | Check logs for connection errors, verify DISCORD_BOT_TOKEN |
| Bot missing permissions | Re-invite with scopes: applications.commands, bot |
| Commands not showing | Wait 1 minute for Discord to sync, check DISCORD_GUILD_ID setting |
| Bot has permission but commands fail | Check error logs: `poetry run python main.py 2>&1 \| grep -i error` |

### Discord Webhooks Not Sending

**Symptoms**: Tournament notifications don't appear in Discord

**Debugging**:

1. **Check webhook URL configured**:
```bash
# In admin UI: Settings → Discord Webhooks
# Should show webhook URLs
```

2. **Verify webhook is still valid**:
```bash
# Webhooks can become invalid if:
# - Channel deleted
# - Webhook deleted
# - Bot doesn't have Send Messages permission in channel
```

3. **Check notification service logs**:
```bash
# Look for notification sending errors
poetry run python main.py 2>&1 | grep -i "webhook\|notification"
```

4. **Test webhook manually**:
```bash
curl -X POST https://discordapp.com/api/webhooks/YOUR_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"content": "Test message"}'
```

---

## RaceTime Integration Issues

### Can't Connect to RaceTime.gg

**Error**: `aiohttp.ClientError: Cannot connect to host racetime.gg`

**Debugging**:

1. **Check network connectivity**:
```bash
ping racetime.gg  # Should respond
curl https://racetime.gg  # Should return HTML
```

2. **Check RaceTime URL in config**:
```bash
echo $RACETIME_URL  # Should be https://racetime.gg
```

3. **Check firewall/proxy**:
```bash
# Test with curl (verbose output)
curl -v https://racetime.gg 2>&1 | head -20
```

4. **Check if RaceTime is down**:
   - Go to https://racetime.gg in browser
   - If you can't access it, service is down

**Solutions**:
- ❌ Network issues: Check internet connection, firewall rules
- ❌ RaceTime down: Check their status page, try again later
- ❌ Wrong URL: Verify RACETIME_URL is correct

### RaceTime Bot Registration Issues

**Symptoms**: Can't register or authorize RaceTime bot

**Debugging**:

1. **Check bot is registered in database**:
```bash
# In MySQL
mysql sahabot2
> SELECT * FROM racetime_bot;
> SELECT * FROM racetime_bot_organization;
```

2. **Check RaceTime OAuth credentials**:
```bash
echo $RACETIME_CLIENT_ID      # Should be set
echo $RACETIME_CLIENT_SECRET  # Should be set
```

3. **Check OAuth redirect URI**:
```bash
echo $RACETIME_OAUTH_REDIRECT_URI
# Or it defaults to: {BASE_URL}/racetime/link/callback
```

4. **Verify bot on RaceTime.gg**:
   - Go to https://racetime.gg/account/dev
   - Check bot is listed and credentials are correct

**Solutions**:
- ❌ Bot not registered: Use admin UI to register new bot
- ❌ Wrong credentials: Update in RaceTime.gg dev dashboard
- ❌ OAuth mismatch: Update RACETIME_OAUTH_REDIRECT_URI

### Chat Commands Not Working

**Error**: RaceTime chat commands registered but don't execute

**Debugging**:

1. **Check commands are registered**:
   - Join a race on RaceTime.gg
   - Look in race chat for available commands

2. **Check bot has chat command permission**:
   - Go to https://racetime.gg/account/dev
   - Select your bot
   - Verify "Chat Commands" permission is enabled

3. **Check database has commands**:
```bash
mysql sahabot2
> SELECT * FROM racetime_chat_command;
```

4. **Check chat command handlers**:
```bash
# Look for logs
poetry run python main.py 2>&1 | grep -i "chat.*command"
```

---

## API Issues

### API Endpoint Returns 401 Unauthorized

**Cause**: Authentication token missing or invalid

**Solution**:

1. **Check Authorization header**:
```bash
# Request should include:
Authorization: Bearer YOUR_TOKEN

# Or use API token endpoint first to get token
curl -X GET http://localhost:8080/api/users/@me \
  -H "Authorization: Bearer $(cat token.txt)"
```

2. **Get valid token**:
```bash
# Via API
curl -X POST http://localhost:8080/api/tokens \
  -H "Content-Type: application/json" \
  -d '{"name": "test_token"}'

# Via UI: Login → Profile → API Tokens → Create Token
```

3. **Check token hasn't expired**:
```bash
# Tokens may have expiration
# Check in database or request new one
```

### API Endpoint Returns 403 Forbidden

**Cause**: User lacks permission for operation

**Solution**:

1. **Check user permissions**:
```bash
# In admin UI or database
mysql sahabot2
> SELECT * FROM user WHERE id = USER_ID;
# Check 'permission' field
```

2. **Check organization membership**:
   - For org-scoped operations, user must be member
   - Check in admin UI: Organizations → Members

3. **Check specific permission required**:
   - Read API documentation for specific endpoint
   - See [API_ENDPOINTS_REFERENCE.md](../reference/API_ENDPOINTS_REFERENCE.md)

### API Endpoint Returns 404 Not Found

**Cause**: Resource doesn't exist or endpoint is wrong

**Solution**:

1. **Check endpoint path**:
```bash
# Correct: /api/users/123
# Wrong: /api/user/123
curl -X GET http://localhost:8080/api/users/123 \
  -H "Authorization: Bearer TOKEN"
```

2. **Check resource exists**:
```bash
# Via database
mysql sahabot2
> SELECT * FROM user WHERE id = 123;
```

3. **Check if deleted**:
   - Deleted resources return 404
   - Check database for deletion_date

### API Rate Limited

**Error**: HTTP 429 Too Many Requests

**Solution**:

1. **Check rate limits**:
```bash
# Response headers show limits
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1234567890
```

2. **Wait for reset**:
   - Calculate reset time from X-RateLimit-Reset
   - Implement exponential backoff in client

3. **Adjust rate limit if needed**:
```bash
# In .env
API_DEFAULT_RATE_LIMIT_PER_MINUTE=120
```

---

## UI/Frontend Issues

### Page Won't Load / Blank Screen

**Symptoms**: Page loads but shows nothing

**Debugging**:

1. **Check browser console** (F12 → Console):
   - Look for red error messages
   - Note the exact error

2. **Check browser network tab** (F12 → Network):
   - Look for failed requests
   - Check response status codes

3. **Check application logs**:
```bash
poetry run python main.py 2>&1 | tail -50
```

4. **Common frontend errors**:

| Error | Cause | Solution |
|-------|-------|----------|
| `GET /static/css/main.css 404` | CSS file missing | Run `npm run build` or check static/ dir |
| `Cannot read property 'name' of undefined` | JavaScript error | Check browser console for full error |
| `TypeError in render()` | NiceGUI render function error | Check page function syntax |
| `websocket connection failed` | NiceGUI bridge connection issue | Check network tab, firewall rules |

### Dark Mode Not Working

**Symptoms**: Dark mode toggle doesn't work or doesn't persist

**Debugging**:

1. **Check JavaScript file loaded**:
```bash
# In browser console (F12)
typeof window.DarkMode  # Should be 'object'
```

2. **Check localStorage**:
```javascript
// In browser console
localStorage.getItem('dark_mode_enabled')  // Should show 'true' or 'false'
```

3. **Check CSS file**:
```bash
# Should exist
ls static/css/main.css

# Should contain dark mode classes
grep -i "q-dark\|dark" static/css/main.css
```

### Navigation Not Working

**Symptoms**: Clicking links doesn't navigate

**Debugging**:

1. **Check link format**:
```python
# ✅ Correct
ui.link('Home', '/')
ui.link('External', 'https://example.com', new_tab=True)

# ❌ Wrong
ui.link('External', 'https://example.com')  # Missing new_tab=True
```

2. **Check page registered**:
   - Page function must use `@ui.page()` decorator
   - Page must be imported in `frontend.py`

3. **Check route exists**:
```bash
# Should see route listed
grep "@ui.page" pages/*.py
```

---

## Performance Issues

### Slow API Response Times

**Symptoms**: API endpoints take 5+ seconds to respond

**Debugging**:

1. **Check database query time**:
```bash
# Enable slow query log in MySQL
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;

# Then check
tail -f /var/log/mysql/slow.log
```

2. **Check for N+1 queries**:
   - Use `prefetch_related()` in repositories
   - Example: `Tournament.filter(...).prefetch_related('pools')`

3. **Check indexes**:
```bash
# In MySQL
mysql sahabot2
> SHOW INDEXES FROM tournament;
> SHOW INDEXES FROM async_tournament;
```

4. **Profile code**:
```python
# Add timing to service methods
import time
start = time.time()
result = await repository.list_by_organization(1)
elapsed = time.time() - start
logger.info("Query took %.2f seconds", elapsed)
```

### High Memory Usage

**Symptoms**: Application uses excessive RAM, eventually crashes

**Debugging**:

1. **Check memory with top/htop**:
```bash
top           # macOS
htop          # Linux (if installed)
# Look for python process memory usage
```

2. **Check for memory leaks**:
   - Look for large objects created but not deleted
   - Check event listeners registered but not removed

3. **Check connection pools**:
```bash
# Verify database connections are closed properly
# Check connection pool size in logs
```

4. **Profile memory usage**:
```bash
# Add to main.py temporarily
import tracemalloc
tracemalloc.start()
# ... run code ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

### High CPU Usage

**Symptoms**: Application uses 100% CPU, system slow

**Debugging**:

1. **Check for infinite loops**:
```bash
# Look in logs for repeated messages
poetry run python main.py 2>&1 | sort | uniq -c | sort -rn
```

2. **Check task scheduler**:
   - Background tasks may be running frequently
   - Check task configuration

3. **Check database activity**:
```bash
# In MySQL
SHOW PROCESSLIST;  # See running queries
```

4. **Profile with cProfile**:
```python
# Wrap code section
import cProfile
import pstats
from io import StringIO

pr = cProfile.Profile()
pr.enable()
# ... code to profile ...
pr.disable()
ps = pstats.Stats(pr, stream=StringIO())
ps.sort_stats('cumulative')
ps.print_stats(20)  # Top 20 functions
```

---

## Debugging Procedures

### Enable Verbose Logging

**Add to .env**:
```bash
DEBUG=true
LOGGING_LEVEL=DEBUG
```

**Or run directly**:
```bash
export DEBUG=true
poetry run python main.py
```

### View Application Logs

**Development**:
```bash
# Terminal where app is running shows logs
# Press Ctrl+C to stop app and see recent logs

# Or save to file
./start.sh dev 2>&1 | tee app.log
tail -f app.log  # Follow logs
```

**Production**:
```bash
# Docker
docker logs -f sahabot2

# Systemd
journalctl -u sahabot2 -f

# PM2
pm2 logs sahabot2 --lines 100
```

### Check Specific Component

**Database**:
```bash
# Test connection
python -c "from database import init; import asyncio; asyncio.run(init())"

# Check models
mysql sahabot2
> DESCRIBE user;
```

**Discord Bot**:
```bash
# Check bot status in Discord app
# Look in @mention list for your bot

# Check logs
poetry run python main.py 2>&1 | grep -i "bot\|discord"
```

**API**:
```bash
# Test endpoint
curl -v http://localhost:8080/api/health

# Check with auth
curl -v -H "Authorization: Bearer TOKEN" http://localhost:8080/api/users/@me
```

### Check Service Health

```bash
# Health endpoint (no auth required)
curl http://localhost:8080/health

# Expected response
{
  "status": "ok",
  "timestamp": "2025-11-04T12:34:56Z"
}
```

### Interactive Debugging

**Python REPL with app context**:
```bash
# Start interactive Python with app loaded
poetry run python

>>> from config import settings
>>> print(settings.database_url)

>>> import asyncio
>>> from database import init
>>> asyncio.run(init())

>>> from models import User
>>> users = asyncio.run(User.all())
```

---

## Log Analysis

### Finding Errors in Logs

```bash
# Find all errors
poetry run python main.py 2>&1 | grep -i "error\|exception\|traceback"

# Find specific error type
poetry run python main.py 2>&1 | grep "ValueError"

# Find and show context (3 lines before/after)
poetry run python main.py 2>&1 | grep -B 3 -A 3 "ERROR"

# Save error log
poetry run python main.py 2>&1 | grep -i "error" > errors.log
```

### Finding Performance Issues

```bash
# Find slow operations (if logged)
poetry run python main.py 2>&1 | grep -i "took.*seconds"

# Find database connection issues
poetry run python main.py 2>&1 | grep -i "database\|connection"

# Find Discord issues
poetry run python main.py 2>&1 | grep -i "discord"
```

### Timestamp-based Analysis

```bash
# Find all logs in last 5 minutes
# (requires timestamps in logs)
poetry run python main.py 2>&1 | grep "12:3[0-5]"

# Events between specific times
poetry run python main.py 2>&1 | awk '/12:30:00/,/12:35:00/'
```

---

## Getting Help

### When Reporting Issues

Include:

1. **Error message** (exact text)
2. **Steps to reproduce** (clear steps)
3. **Environment**:
   - Python version
   - OS (macOS, Ubuntu, Windows)
   - Database version
   - Application version

4. **Logs**:
   - Application logs (last 50 lines)
   - Error logs if available
   - Database logs if database issue

5. **Configuration** (sanitized):
   - ENVIRONMENT setting (dev/staging/prod)
   - DEBUG setting (true/false)
   - Which features are enabled

### Example Issue Report

```
## Error: Discord OAuth won't work

### Steps to reproduce
1. Start app: ./start.sh dev
2. Click "Login with Discord"
3. Get redirected back with error

### Error message
"redirect_uri_mismatch"

### Environment
- Python 3.11
- macOS Sonoma
- MySQL 8.0
- SahaBot2 main branch

### Logs
[timestamp] ERROR in auth: redirect_uri_mismatch
[timestamp] Expected: http://localhost:8080/auth/callback
[timestamp] Got: http://localhost:8080/auth

### Config (sanitized)
DEBUG=true
DISCORD_REDIRECT_URI=http://localhost:8080/auth/callback
```

---

## See Also

- [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) - Configuration reference
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production setup
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- Application logs: Check stderr/stdout when running
- Database logs: MySQL error log usually at `/var/log/mysql/error.log`
- Discord bot developer portal: https://discord.com/developers/applications

---

**Last Updated**: November 4, 2025
