# Environment Variables Reference

Complete reference for all environment variables and configuration options in SahaBot2.

**Last Updated**: November 4, 2025  
**Source**: `config.py` (Pydantic BaseSettings)

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Database Configuration](#database-configuration)
- [Discord Configuration](#discord-configuration)
- [RaceTime.gg Configuration](#racetimegg-configuration)
- [Application Configuration](#application-configuration)
- [Server Configuration](#server-configuration)
- [API Configuration](#api-configuration)
- [Randomizer Configuration](#randomizer-configuration)
- [Environment Profiles](#environment-profiles)
- [Validation & Defaults](#validation--defaults)
- [Troubleshooting](#troubleshooting)

---

## Overview

All configuration in SahaBot2 is managed through environment variables, loaded from `.env` file or system environment. This provides:

✅ **Security** - Secrets never committed to git (`.env` in `.gitignore`)  
✅ **Flexibility** - Different config per environment (dev, staging, prod)  
✅ **Clarity** - All config in one place  
✅ **Type Safety** - Pydantic validates types and required fields  

**Loading Order**:
1. `.env` file in project root (highest priority)
2. System environment variables
3. Built-in defaults (if defined)

---

## Quick Start

### Minimal Configuration (.env file)

```bash
# Database
DATABASE_URL=mysql://sahabot2:password123@localhost:3306/sahabot2
# OR individual fields:
DB_HOST=localhost
DB_PORT=3306
DB_USER=sahabot2
DB_PASSWORD=password123
DB_NAME=sahabot2

# Discord (required)
DISCORD_CLIENT_ID=123456789012345678
DISCORD_CLIENT_SECRET=your_discord_secret_key_here
DISCORD_REDIRECT_URI=http://localhost:8080/auth/callback
DISCORD_BOT_TOKEN=your_bot_token_here

# Application (required)
SECRET_KEY=your_secret_key_for_sessions_min_32_chars
ENVIRONMENT=development
```

### Production Configuration (.env file)

```bash
# Database (production instance)
DB_HOST=prod-db.example.com
DB_PORT=3306
DB_USER=prod_sahabot2
DB_PASSWORD=strong_password_here
DB_NAME=sahabot2_prod

# Discord
DISCORD_CLIENT_ID=production_client_id
DISCORD_CLIENT_SECRET=production_secret
DISCORD_REDIRECT_URI=https://yourapp.com/auth/callback
DISCORD_BOT_TOKEN=production_bot_token
DISCORD_GUILD_ID=your_discord_server_id  # Optional

# Application
SECRET_KEY=long_random_string_for_production_min_32_chars
ENVIRONMENT=production
DEBUG=False
BASE_URL=https://yourapp.com

# Server
HOST=0.0.0.0
PORT=80  # or 443 with reverse proxy
```

---

## Database Configuration

### DB_HOST
**Type**: `string`  
**Default**: `localhost`  
**Required**: No  
**Example**: `localhost`, `127.0.0.1`, `db.example.com`

Database server hostname or IP address.

```bash
DB_HOST=localhost
```

### DB_PORT
**Type**: `integer`  
**Default**: `3306`  
**Required**: No  
**Example**: `3306`, `3307`

MySQL server port number.

```bash
DB_PORT=3306
```

### DB_USER
**Type**: `string`  
**Default**: `sahabot2`  
**Required**: No  
**Example**: `sahabot2`, `prod_user`

MySQL database username.

```bash
DB_USER=sahabot2
```

### DB_PASSWORD
**Type**: `string`  
**Default**: *(none - required at startup)*  
**Required**: Yes  
**Example**: `mypassword123`

MySQL database password. **KEEP SECURE** - never commit to git.

```bash
DB_PASSWORD=your_secure_password_here
```

### DB_NAME
**Type**: `string`  
**Default**: `sahabot2`  
**Required**: No  
**Example**: `sahabot2`, `sahabot2_prod`

MySQL database name to use.

```bash
DB_NAME=sahabot2
```

### Generated: DATABASE_URL
**Type**: `property (read-only)`  
**Format**: `mysql://user:password@host:port/database`

Automatically generated from individual DB_* settings for Tortoise ORM.

```
mysql://sahabot2:password@localhost:3306/sahabot2
```

**Don't Set**: This is auto-generated. Set individual DB_* variables instead.

---

## Discord Configuration

### DISCORD_CLIENT_ID
**Type**: `string`  
**Default**: *(none - required)*  
**Required**: Yes  
**Example**: `123456789012345678`

OAuth2 application ID from Discord Developer Portal.

**How to Get**:
1. Go to https://discord.com/developers/applications
2. Create or select your application
3. Copy the "Client ID" from General Information

```bash
DISCORD_CLIENT_ID=123456789012345678
```

### DISCORD_CLIENT_SECRET
**Type**: `string`  
**Default**: *(none - required)*  
**Required**: Yes  
**Example**: `your_secret_key_here`

OAuth2 application secret from Discord Developer Portal.

**How to Get**:
1. Go to https://discord.com/developers/applications
2. Select your application
3. Click "Reset Secret" if needed
4. Copy the "Client Secret" (hidden by default)

**KEEP SECURE**: Never commit to git.

```bash
DISCORD_CLIENT_SECRET=your_secret_key_here
```

### DISCORD_REDIRECT_URI
**Type**: `string`  
**Default**: `http://localhost:8080/auth/callback`  
**Required**: No (has sensible default)  
**Example**: `http://localhost:8080/auth/callback`, `https://yourapp.com/auth/callback`

OAuth2 redirect URI after user authorizes.

**Must Match Discord Settings**:
1. Go to https://discord.com/developers/applications
2. Select your application
3. Go to OAuth2 → Redirects
4. Add your redirect URI exactly as configured here

```bash
# Development
DISCORD_REDIRECT_URI=http://localhost:8080/auth/callback

# Production
DISCORD_REDIRECT_URI=https://yourapp.com/auth/callback
```

### DISCORD_BOT_TOKEN
**Type**: `string`  
**Default**: *(none - required)*  
**Required**: Yes  
**Example**: `bot_token_here`

Discord bot token for bot authentication.

**How to Get**:
1. Go to https://discord.com/developers/applications
2. Select your application
3. Go to "Bot" section
4. Click "Reset Token" if needed
5. Copy the token (hidden by default)

**KEEP SECURE**: Never commit to git. Anyone with this token can control your bot.

```bash
DISCORD_BOT_TOKEN=your_bot_token_here
```

### DISCORD_BOT_ENABLED
**Type**: `boolean`  
**Default**: `true`  
**Required**: No  
**Example**: `true`, `false`

Whether to start the Discord bot on application startup.

Set to `false` to run application without bot (for development/testing).

```bash
DISCORD_BOT_ENABLED=true     # Run with bot
DISCORD_BOT_ENABLED=false    # Run without bot (dev/testing)
```

### DISCORD_GUILD_ID
**Type**: `string` (optional)  
**Default**: *(none)*  
**Required**: No  
**Example**: `123456789012345678`

Optional Discord server (guild) ID for guild-specific commands.

If set, application commands will be registered to this guild (faster updates during development).

```bash
DISCORD_GUILD_ID=123456789012345678
```

**Get Guild ID**:
1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click your server name
3. Select "Copy Server ID"

---

## RaceTime.gg Configuration

### RACETIME_CLIENT_ID
**Type**: `string`  
**Default**: *(empty)*  
**Required**: No (unless using RaceTime OAuth linking)  
**Example**: `your_client_id`

RaceTime.gg OAuth2 application ID for user account linking.

**How to Get**:
1. Go to https://racetime.gg/account/dev
2. Create or select your OAuth application
3. Copy the Client ID

```bash
RACETIME_CLIENT_ID=your_client_id
```

### RACETIME_CLIENT_SECRET
**Type**: `string`  
**Default**: *(empty)*  
**Required**: No (unless using RaceTime OAuth linking)  
**Example**: `your_client_secret`

RaceTime.gg OAuth2 application secret for user account linking.

**How to Get**:
1. Go to https://racetime.gg/account/dev
2. Select your OAuth application
3. Copy the Client Secret

**KEEP SECURE**: Never commit to git.

```bash
RACETIME_CLIENT_SECRET=your_client_secret
```

### RACETIME_OAUTH_REDIRECT_URI
**Type**: `string` (optional)  
**Default**: `{BASE_URL}/racetime/link/callback`  
**Required**: No  
**Example**: `https://yourapp.com/racetime/link/callback`

RaceTime.gg OAuth2 redirect URI after user authorizes.

**Defaults to**: `{BASE_URL}/racetime/link/callback` if not set.

**Must Match RaceTime Settings**:
1. Go to https://racetime.gg/account/dev
2. Select your OAuth application
3. Add your redirect URI in the settings

```bash
RACETIME_OAUTH_REDIRECT_URI=https://yourapp.com/racetime/link/callback
```

### RACETIME_URL
**Type**: `string`  
**Default**: `https://racetime.gg`  
**Required**: No  
**Example**: `https://racetime.gg`, `https://staging.racetime.gg`

Base URL for RaceTime.gg API and OAuth endpoints.

Use staging URL for testing if available.

```bash
# Production
RACETIME_URL=https://racetime.gg

# Staging (if available)
RACETIME_URL=https://staging.racetime.gg
```

### RACETIME_BOTS (DEPRECATED)
**Type**: `string`  
**Default**: *(empty)*  
**Required**: No (DEPRECATED)  
**Status**: ⚠️ DEPRECATED - Use database configuration instead

Legacy bot configuration format. Bot configurations are now managed through the database and admin UI.

**Old Format** (no longer recommended):
```bash
RACETIME_BOTS=alttpr:client1:secret1,ootr:client2:secret2
```

**New Way**: Configure bots through SahaBot2 admin UI after startup.

---

## Application Configuration

### SECRET_KEY
**Type**: `string`  
**Default**: *(none - required)*  
**Required**: Yes  
**Length**: Minimum 32 characters recommended  
**Example**: `your_secret_key_for_sessions_min_32_chars`

Secret key for session encryption and CSRF protection.

**Generate a Secure Key**:
```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using openssl
openssl rand -base64 32
```

**KEEP SECURE**: Never commit to git. Use different key per environment.

```bash
SECRET_KEY=your_secret_key_for_sessions_min_32_chars
```

### ENVIRONMENT
**Type**: `string`  
**Default**: `development`  
**Required**: No  
**Valid Values**: `development`, `staging`, `production`

Application environment indicator.

Used for conditional behavior and logging levels.

```bash
ENVIRONMENT=development   # Development/testing
ENVIRONMENT=staging       # Staging environment
ENVIRONMENT=production    # Production environment
```

### DEBUG
**Type**: `boolean`  
**Default**: `true`  
**Required**: No  
**Example**: `true`, `false`

Enable/disable debug mode.

**⚠️ IMPORTANT**: Set to `false` in production.

```bash
DEBUG=true      # Development: show detailed errors
DEBUG=false     # Production: hide sensitive information
```

### BASE_URL
**Type**: `string`  
**Default**: `http://localhost:8080`  
**Required**: No  
**Example**: `http://localhost:8080`, `https://yourapp.com`

Base URL where application is accessible from outside.

Used for OAuth redirects, email links, and API documentation.

```bash
# Development
BASE_URL=http://localhost:8080

# Staging
BASE_URL=https://staging.yourapp.com

# Production
BASE_URL=https://yourapp.com
```

---

## Server Configuration

### HOST
**Type**: `string`  
**Default**: `0.0.0.0`  
**Required**: No  
**Example**: `0.0.0.0`, `127.0.0.1`, `localhost`

Server bind address.

Use `0.0.0.0` to listen on all interfaces (recommended for containers).

```bash
HOST=0.0.0.0        # Listen on all interfaces
HOST=127.0.0.1      # Listen only on localhost
HOST=localhost      # Same as 127.0.0.1
```

### PORT
**Type**: `integer`  
**Default**: `8080`  
**Required**: No  
**Example**: `8080`, `3000`, `5000`, `80`, `443`

Server listening port.

```bash
PORT=8080           # Development (non-root)
PORT=80             # Production HTTP (requires root)
PORT=443            # Production HTTPS (requires root)
```

**Port Selection**:
- **1-1023**: Privileged ports, require root/admin
- **1024+**: Unprivileged ports, recommended for development
- **8080, 3000, 5000**: Common development ports

---

## API Configuration

### API_RATE_LIMIT_WINDOW_SECONDS
**Type**: `integer`  
**Default**: `60`  
**Required**: No  
**Example**: `60`, `120`

Time window (seconds) for rate limit calculations.

```bash
API_RATE_LIMIT_WINDOW_SECONDS=60     # 1 minute window
API_RATE_LIMIT_WINDOW_SECONDS=120    # 2 minute window
```

### API_DEFAULT_RATE_LIMIT_PER_MINUTE
**Type**: `integer`  
**Default**: `60`  
**Required**: No  
**Example**: `60`, `120`, `30`

Default API rate limit: requests per minute for standard users.

```bash
API_DEFAULT_RATE_LIMIT_PER_MINUTE=60      # 60 requests/minute
API_DEFAULT_RATE_LIMIT_PER_MINUTE=120     # 120 requests/minute
API_DEFAULT_RATE_LIMIT_PER_MINUTE=30      # 30 requests/minute (strict)
```

**Rate Limit Tiers**:
- **30/min**: Strict (admin operations)
- **60/min**: Standard (default)
- **120/min**: Relaxed (public endpoints)

---

## Randomizer Configuration

### ALTTPR_BASEURL
**Type**: `string`  
**Default**: `https://alttpr.com`  
**Required**: No  
**Example**: `https://alttpr.com`

Base URL for A Link to the Past Randomizer API.

```bash
ALTTPR_BASEURL=https://alttpr.com
```

### OOTR_API_KEY
**Type**: `string` (optional)  
**Default**: *(none)*  
**Required**: No (unless using OoTR API)  
**Example**: `your_api_key_here`

Optional API key for Ocarina of Time Randomizer API access.

**How to Get**:
1. Go to https://ootrandomizer.com
2. Create an account or contact admin
3. Request API key
4. Add to configuration

```bash
OOTR_API_KEY=your_api_key_here
```

---

## Environment Profiles

### Development Profile

```bash
# .env.development

# Database (local)
DB_HOST=localhost
DB_PORT=3306
DB_USER=sahabot2
DB_PASSWORD=dev_password
DB_NAME=sahabot2_dev

# Discord
DISCORD_CLIENT_ID=dev_client_id
DISCORD_CLIENT_SECRET=dev_client_secret
DISCORD_REDIRECT_URI=http://localhost:8080/auth/callback
DISCORD_BOT_TOKEN=dev_bot_token
DISCORD_BOT_ENABLED=true

# RaceTime
RACETIME_CLIENT_ID=dev_racetime_client
RACETIME_CLIENT_SECRET=dev_racetime_secret

# Application
SECRET_KEY=dev_secret_key_for_development
ENVIRONMENT=development
DEBUG=true
BASE_URL=http://localhost:8080

# Server
HOST=0.0.0.0
PORT=8080

# API
API_DEFAULT_RATE_LIMIT_PER_MINUTE=120  # Relaxed for testing
```

### Staging Profile

```bash
# .env.staging

# Database (staging instance)
DB_HOST=staging-db.internal
DB_PORT=3306
DB_USER=staging_sahabot2
DB_PASSWORD=staging_password
DB_NAME=sahabot2_staging

# Discord
DISCORD_CLIENT_ID=staging_client_id
DISCORD_CLIENT_SECRET=staging_client_secret
DISCORD_REDIRECT_URI=https://staging.yourapp.com/auth/callback
DISCORD_BOT_TOKEN=staging_bot_token

# RaceTime
RACETIME_CLIENT_ID=staging_racetime_client
RACETIME_CLIENT_SECRET=staging_racetime_secret
RACETIME_URL=https://racetime.gg  # or staging if available

# Application
SECRET_KEY=staging_secret_key_long_and_random
ENVIRONMENT=staging
DEBUG=false
BASE_URL=https://staging.yourapp.com

# Server
HOST=0.0.0.0
PORT=8080

# API
API_DEFAULT_RATE_LIMIT_PER_MINUTE=60
```

### Production Profile

```bash
# .env.production

# Database (production instance)
DB_HOST=prod-db.internal
DB_PORT=3306
DB_USER=prod_sahabot2
DB_PASSWORD=very_strong_password_here
DB_NAME=sahabot2_prod

# Discord
DISCORD_CLIENT_ID=prod_client_id
DISCORD_CLIENT_SECRET=prod_client_secret
DISCORD_REDIRECT_URI=https://yourapp.com/auth/callback
DISCORD_BOT_TOKEN=prod_bot_token

# RaceTime
RACETIME_CLIENT_ID=prod_racetime_client
RACETIME_CLIENT_SECRET=prod_racetime_secret

# Application
SECRET_KEY=production_secret_key_long_random_secure_string
ENVIRONMENT=production
DEBUG=false
BASE_URL=https://yourapp.com

# Server (behind reverse proxy)
HOST=0.0.0.0
PORT=8080

# API
API_DEFAULT_RATE_LIMIT_PER_MINUTE=60

# Randomizers
OOTR_API_KEY=production_ootr_api_key
```

---

## Validation & Defaults

### Required Variables

These variables **must** be set in .env or environment:

| Variable | Error Message | Solution |
|----------|---------------|----------|
| DB_PASSWORD | `value_error.missing` | Set DB_PASSWORD in .env |
| DISCORD_CLIENT_ID | `value_error.missing` | Add Discord OAuth credentials |
| DISCORD_CLIENT_SECRET | `value_error.missing` | Add Discord OAuth credentials |
| DISCORD_BOT_TOKEN | `value_error.missing` | Add Discord bot token |
| SECRET_KEY | `value_error.missing` | Generate a secure key |

### Optional Variables (with Defaults)

| Variable | Default | When to Override |
|----------|---------|------------------|
| DB_HOST | `localhost` | Different database server |
| DB_PORT | `3306` | Non-standard MySQL port |
| DB_USER | `sahabot2` | Different database user |
| DB_NAME | `sahabot2` | Different database name |
| ENVIRONMENT | `development` | Staging/production deployment |
| DEBUG | `true` | Production (set to false) |
| BASE_URL | `http://localhost:8080` | Custom domain |
| HOST | `0.0.0.0` | Security restrictions |
| PORT | `8080` | Port already in use |
| DISCORD_BOT_ENABLED | `true` | Testing without bot |
| DISCORD_REDIRECT_URI | `http://localhost:8080/auth/callback` | Custom domain |
| API_DEFAULT_RATE_LIMIT_PER_MINUTE | `60` | Performance tuning |

### Type Validation

All variables are validated by Pydantic:

```python
# Valid
PORT=8080           # Integer

# Invalid (will fail)
PORT=not_a_number   # Pydantic will raise ValueError
```

---

## Troubleshooting

### "Missing required field: DB_PASSWORD"

**Cause**: DB_PASSWORD not set in .env or environment

**Solution**:
```bash
# Add to .env file
DB_PASSWORD=your_database_password

# Or set in environment
export DB_PASSWORD=your_database_password
```

### "Invalid database URL"

**Cause**: Database connection parameters incorrect

**Solution**:
1. Check DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
2. Verify MySQL server is running
3. Test connection manually:
```bash
mysql -h localhost -u sahabot2 -p
# Enter password when prompted
```

### "Discord OAuth redirect URI mismatch"

**Cause**: DISCORD_REDIRECT_URI doesn't match Discord app settings

**Solution**:
1. Set DISCORD_REDIRECT_URI in .env
2. Go to https://discord.com/developers/applications
3. Select your application
4. Add the same URI to OAuth2 → Redirects
5. URIs must match exactly (protocol, domain, path)

### "Discord bot not responding"

**Cause**: DISCORD_BOT_TOKEN invalid or bot not enabled

**Solution**:
1. Check DISCORD_BOT_TOKEN is correct (reset if needed)
2. Check DISCORD_BOT_ENABLED=true
3. Check bot has proper permissions in Discord server
4. Check application logs for errors

### "Application won't start"

**Cause**: Missing required environment variables

**Solution**:
1. Check all required variables are set (see table above)
2. Check .env file syntax (use KEY=VALUE format)
3. Check for typos in variable names
4. Check file permissions on .env (should be readable)
5. Run with verbose logging to see which variable is missing

### "Port already in use"

**Cause**: Another process using the same port

**Solution**:
```bash
# Check what's using the port
lsof -i :8080          # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Use different port
PORT=3000
```

### "Cannot connect to RaceTime.gg"

**Cause**: RACETIME_URL incorrect or network issue

**Solution**:
1. Check RACETIME_URL is correct (should be https://racetime.gg)
2. Check network connectivity
3. Check firewall rules
4. Check RaceTime.gg status page

---

## Security Best Practices

### ✅ DO:

- ✅ Keep `.env` in `.gitignore` (never commit secrets)
- ✅ Use strong passwords (20+ characters, mixed case, numbers, symbols)
- ✅ Rotate secrets regularly
- ✅ Use different secrets per environment
- ✅ Restrict `.env` file permissions: `chmod 600 .env`
- ✅ Use environment variables in production (not .env files)

### ❌ DON'T:

- ❌ Commit `.env` to git
- ❌ Share secrets via email/chat
- ❌ Use same secrets across environments
- ❌ Use default or weak passwords
- ❌ Log sensitive values
- ❌ Pass secrets via command line (use .env or environment)

---

## See Also

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment setup and procedures
- [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md) - Common issues and solutions
- [config.py](../../config.py) - Configuration source code
- [.env.example](../../.env.example) - Example configuration template
- Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/

---

**Last Updated**: November 4, 2025
