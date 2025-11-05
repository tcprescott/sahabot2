# SahaBot2

**SahasrahBot2** (SahaBot2) is a modern web application built with NiceGUI and Tortoise ORM, featuring Discord OAuth2 authentication and database-driven authorization.

## Features

- 🎨 **Mobile-First Responsive Design** - Fully functional on all device sizes
- 🔐 **Discord OAuth2 Authentication** - Secure login via Discord with automatic token refresh
- 🏁 **RaceTime.gg Integration** - Link your RaceTime.gg account for race tracking
- 🗄️ **Database-Driven Authorization** - Flexible permission system
- 🏗️ **Clean Architecture** - Separation of concerns with service and repository layers
- 💅 **External CSS** - No inline styling, human-friendly class names
- ⚡ **Async/Await** - Modern asynchronous Python throughout
- 📝 **High Code Quality** - Comprehensive docstrings and type hints
- 🛡️ **Enterprise Security** - HTTPS enforcement, security headers, CSRF protection, input validation

## Architecture

### Core Principles

1. **Mobile-First Responsive Design** - Application is fully functional on mobile with feature parity
2. **Separation of Concerns** - Business logic in services, data access in repositories, UI is presentation only
3. **External CSS** - All styling in external CSS files with semantic class names
4. **Discord OAuth2 Authentication** - All users authenticate via Discord
5. **Database-Driven Authorization** - Permissions stored and enforced server-side
6. **High Code Quality** - Consistent async/await usage, comprehensive documentation

### Project Structure

```
sahabot2/
├── main.py                 # Application entry point
├── frontend.py             # Frontend route registration
├── config.py               # Configuration management
├── database.py             # Database initialization
├── models/                 # Database models
│   ├── __init__.py
│   ├── user.py             # User model and Permission enum
│   └── audit_log.py        # Audit log model
├── components/             # Reusable UI components
│   ├── __init__.py
│   └── base_page.py        # Base page template
├── application/
│   ├── services/           # Business logic layer
│   │   ├── user_service.py
│   │   ├── authorization_service.py
│   │   └── audit_service.py
│   └── repositories/       # Data access layer
│       ├── user_repository.py
│       └── audit_repository.py
├── middleware/
│   └── auth.py             # Discord OAuth2 authentication
├── pages/                  # NiceGUI pages
│   ├── home.py
│   ├── auth.py
│   └── admin.py
├── static/
│   └── css/
│       └── main.css        # Application styles
└── migrations/             # Database migrations
    └── tortoise_config.py
```

## Installation

### Prerequisites

- Python 3.11+
- Poetry (Python package manager)
- MySQL database

### Setup

1. **Clone the repository**
   ```bash
   cd sahabot2
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up database**
   
   Create a MySQL database:
   ```sql
   CREATE DATABASE sahabot2;
   CREATE USER 'sahabot2'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON sahabot2.* TO 'sahabot2'@'localhost';
   ```

5. **Configure Discord OAuth2**

   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Add OAuth2 redirect URL: `http://localhost:8080/auth/callback`
   - Copy Client ID and Client Secret to `.env`

6. **Configure RaceTime.gg OAuth2 (Optional)**

   For users to link their RaceTime.gg accounts:
   - Go to [RaceTime.gg Developer Portal](https://racetime.gg/account/dev)
   - Create a new OAuth2 application
   - Set redirect URI to: `http://localhost:8080/api/racetime/link/callback`
   - Copy Client ID and Client Secret to `.env`:
     ```env
     RACETIME_CLIENT_ID=your_client_id
     RACETIME_CLIENT_SECRET=your_client_secret
     RACETIME_OAUTH_REDIRECT_URI=http://localhost:8080/api/racetime/link/callback
     ```

7. **Initialize database migrations**
   ```bash
   poetry run aerich init-db
   ```

## Development

### Running the Application

**Development mode** (auto-reload enabled):
```bash
./start.sh dev
# or
poetry run python main.py
```

**Production mode**:
```bash
./start.sh prod
```

The application will be available at:
- Development: http://localhost:8080
- Production: http://localhost:80

### Database Migrations

**Create a migration after model changes**:
```bash
poetry run aerich migrate --name "description_of_changes"
```

**Apply migrations**:
```bash
poetry run aerich upgrade
```

**Rollback migration**:
```bash
poetry run aerich downgrade
```

### Policy Checks

Run the configuration policy checks locally to ensure no direct environment access is used (all settings must come from `config.py`):

```bash
python tools/check_config_policy.py
```

These checks also run in CI for every push and pull request.

### Adding New Features

#### Adding a New Page

1. Create page module in `pages/` directory
2. Define page with `@ui.page('/path')` decorator
3. Register page in `frontend.py`
4. Add CSS classes to `static/css/main.css`

#### Adding Business Logic

1. Create service class in `application/services/`
2. Create repository class in `application/repositories/` for data access
3. Use services in UI pages, never access ORM directly from UI

#### Adding Authorization

1. Define permission checks in `AuthorizationService`
2. Use `DiscordAuthService.require_permission()` in pages
3. Conditionally render UI elements based on user permissions

## Configuration

Configuration is managed through environment variables in `.env`:

All configuration is loaded centrally via `config.py` using Pydantic Settings. Do not read environment variables directly in application code, and never hard-code secrets or tokens. Import values from `from config import settings` and use `settings.<FIELD>` instead.

### Database
- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 3306)
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `DB_NAME` - Database name

### Discord OAuth2
- `DISCORD_CLIENT_ID` - Discord application client ID
- `DISCORD_CLIENT_SECRET` - Discord application client secret
- `DISCORD_REDIRECT_URI` - OAuth2 redirect URI
- `DISCORD_GUILD_ID` - Optional Discord guild ID

### Application
- `SECRET_KEY` - Secret key for session encryption
- `ENVIRONMENT` - Environment (development/production)
- `DEBUG` - Debug mode (True/False)
- `HOST` - Server host
- `PORT` - Server port

## API Documentation

All API endpoints are mounted under `/api` and are part of the presentation layer. They must only call into the service layer and never access ORM models directly.

### Interactive Documentation

When running in development mode, interactive API documentation is available:
- **Swagger UI**: http://localhost:8080/docs (interactive, test endpoints directly)
- **ReDoc**: http://localhost:8080/redoc (detailed documentation with examples)

> **Note**: In production mode, API docs are disabled for security. Set `DEBUG=True` in `.env` to enable them.

### Authentication

API endpoints use **Bearer token authentication**. Tokens are associated with Discord users and inherit their permissions.

To authenticate API requests, include your token in the Authorization header:
```
Authorization: Bearer YOUR_TOKEN_HERE
```

You can test authentication directly in the Swagger UI by clicking the "Authorize" button and entering your token.

### Available Endpoints

#### Health
- `GET /api/health` — Health check (no authentication required)

#### Users
- `GET /api/users/me` — Get current authenticated user profile
- `GET /api/users` — List all users (requires ADMIN permission)
- `GET /api/users/search?q=<query>` — Search users by username (requires MODERATOR permission)

All user endpoints require Bearer token authentication and are rate limited.

### Rate Limiting

API requests are rate limited per-user using a sliding window (default 60 requests per 60 seconds). A user's limit can be customized via the `api_rate_limit_per_minute` field; otherwise, the default from settings is used. When exceeded, the API returns HTTP 429 with a `Retry-After` header indicating when to retry.

### Response Formats

All API responses use JSON format with consistent schemas:

**Success Response Example**:
```json
{
  "items": [...],
  "count": 10
}
```

**Error Response Example**:
```json
{
  "detail": "Error message here"
}
```

### Permission Levels

- **USER** (0) - Default permission; can access `/api/users/me`
- **MODERATOR** (50) - Can search users
- **ADMIN** (100) - Can list all users
- **SUPERADMIN** (200) - Full access (future endpoints)

## Testing

Run tests with pytest:
```bash
poetry run pytest
```

## Security

This application implements comprehensive security best practices. See [SECURITY.md](SECURITY.md) for details on:

- 🛡️ Security headers (HSTS, CSP, X-Frame-Options)
- 🔒 HTTPS enforcement in production
- 🔐 Secure OAuth2 implementation with CSRF protection
- 🚫 Input validation and sanitization
- 🔑 Cryptographically secure token generation
- 📝 Audit logging without sensitive data exposure
- 🚨 Vulnerability reporting process

**Security Scan Results**: CodeQL - 0 alerts ✅

To report a security vulnerability, please see our [Security Policy](SECURITY.md).

## Contributing

1. Follow the established architecture patterns
2. Write docstrings for all public functions
3. Use async/await consistently
4. Add CSS classes to external stylesheet
5. Test on mobile viewport sizes
6. Update documentation as needed
7. Follow security best practices (see SECURITY.md)

## License

[Your License Here]

## Support

For issues and questions, please use the GitHub issue tracker.
