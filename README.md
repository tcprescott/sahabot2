# SahaBot2

**SahasrahBot2** (SahaBot2) is a modern web application built with NiceGUI and Tortoise ORM, featuring Discord OAuth2 authentication and database-driven authorization.

## Features

- 🎨 **Mobile-First Responsive Design** - Fully functional on all device sizes
- 🔐 **Discord OAuth2 Authentication** - Secure login via Discord
- 🗄️ **Database-Driven Authorization** - Flexible permission system
- 🏗️ **Clean Architecture** - Separation of concerns with service and repository layers
- 💅 **External CSS** - No inline styling, human-friendly class names
- ⚡ **Async/Await** - Modern asynchronous Python throughout
- 📝 **High Code Quality** - Comprehensive docstrings and type hints

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

6. **Initialize database migrations**
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

## Permission Levels

The application uses the following permission hierarchy:

- **USER** (0) - Default permission for all authenticated users
- **MODERATOR** (50) - Can perform moderation actions
- **ADMIN** (100) - Can access admin panel and manage users
- **SUPERADMIN** (200) - Can change user permissions

## API Documentation

When running in development mode, API documentation is available at:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## Testing

Run tests with pytest:
```bash
poetry run pytest
```

## Contributing

1. Follow the established architecture patterns
2. Write docstrings for all public functions
3. Use async/await consistently
4. Add CSS classes to external stylesheet
5. Test on mobile viewport sizes
6. Update documentation as needed

## License

[Your License Here]

## Support

For issues and questions, please use the GitHub issue tracker.
