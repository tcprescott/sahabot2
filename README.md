# SahaBot2

Multi-tenant NiceGUI + FastAPI application with Discord OAuth2, RaceTime.gg integration, and a policy-based authorization system backed by Tortoise ORM.

## Tech Stack

- FastAPI (async) + NiceGUI (UI)
- Tortoise ORM + MySQL
- Discord OAuth2 + embedded Discord.py bot
- APScheduler task scheduler
- External CSS/JS only (no inline styles)

## Architecture

- Four layers: **UI/API/Bot → Services → Repositories → Models** (never skip layers).
- Multi-tenant: every action is scoped to an organization; server-side membership checks are mandatory.
- Authentication: Discord OAuth2; sessions via NiceGUI storage.
- Authorization: policy framework + `Permission` enum in UI, `UIAuthorizationHelper` for org-scoped checks (deprecated `AuthorizationService` is removed).
- Events: all create/update/delete operations emit events via `application.events.EventBus` with a real `user_id` (or `SYSTEM_USER_ID`).
- Time: always use timezone-aware datetimes (`datetime.now(timezone.utc)`), never `utcnow()`.
- Logging: `logging` with lazy `%` formatting, no `print()` in app code.

## Documentation

- Main index: `docs/README.md`
- Key guides: `docs/ARCHITECTURE.md`, `docs/PATTERNS.md`, `docs/ADDING_FEATURES.md`, `docs/core/BASEPAGE_GUIDE.md`
- Authorization migration: `docs/operations/AUTHORIZATION_MIGRATION.md`
- Event system: `docs/systems/EVENT_SYSTEM.md`
- Full route list: `docs/ROUTE_HIERARCHY.md`
- Historical project summaries moved to `docs/archive/root/`

## Quick Start

1) **Prerequisites**: Python 3.11+, Poetry, MySQL.
2) **Install**: `poetry install`
3) **Configure**: `cp .env.example .env` and fill required values (see `docs/reference/ENVIRONMENT_VARIABLES.md`).
4) **Database (first run)**: `poetry run aerich init-db`
5) **Migrations (after model changes)**: `poetry run aerich migrate --name "description"` then `poetry run aerich upgrade`

## Run

- Development (auto-reload): `./start.sh dev`
- Production: `./start.sh prod`
- Tests: `poetry run pytest`
- Policy/config check: `python tools/check_config_policy.py`
- Mock data (optional): `poetry run python tools/generate_mock_data.py --preset small`

## Conventions

- UI never touches ORM; all data flows through services and repositories.
- External links must use `new_tab=True` (NiceGUI links); external CSS/JS only.
- Emit events after successful writes; never emit with `user_id=None`.
- Follow component/layout patterns in `docs/core/COMPONENTS_GUIDE.md` and `docs/core/BASEPAGE_GUIDE.md`.
- Keep secrets in `.env`; use `config.settings` instead of `os.environ`.

## Support

- Security notes: see `SECURITY.md`.
- For architecture questions start with `docs/ARCHITECTURE.md`; for day-to-day patterns use `docs/PATTERNS.md`.
# Or manually
cp .env.test .env
poetry install
poetry run pytest
```

The test environment uses:
- **SQLite** instead of MySQL (no database server needed)
- **Mock credentials** for Discord, RaceTime, Twitch (no OAuth apps needed)
- **Disabled Discord bot** (no bot token needed)

See [GITHUB_AGENT_TESTING.md](GITHUB_AGENT_TESTING.md) for detailed testing guide, especially for:
- GitHub Coding Agent automated testing
- CI/CD pipeline setup
- Local development without external dependencies

See [docs/operations/COPILOT_AGENT_ENVIRONMENT.md](docs/operations/COPILOT_AGENT_ENVIRONMENT.md) for:
- GitHub Copilot coding agent environment configuration
- Custom agent profiles and instructions
- Development workflow with Copilot agent

## Deployment

For production deployment with Nginx reverse proxy, SSL/TLS, and systemd service management:

- 📋 **[Deployment Guide](docs/operations/DEPLOYMENT_GUIDE.md)** - Complete deployment guide for staging and production
- 🔧 **[nginx.conf.sample](nginx.conf.sample)** - Production-ready Nginx configuration with:
  - WebSocket support (required for NiceGUI)
  - SSL/TLS configuration
  - Rate limiting
  - Security headers
  - Static file serving
  - Gzip compression
- ⚙️ **[sahabot2.service](sahabot2.service)** - Systemd service unit file for Ubuntu/Debian with:
  - Automatic startup on boot
  - Automatic restart on failure
  - Security hardening (PrivateTmp, NoNewPrivileges, ProtectSystem)
  - Resource limits
  - Logging to systemd journal

Quick start for deployment:
```bash
# Copy Nginx configuration
sudo cp nginx.conf.sample /etc/nginx/sites-available/sahabot2
sudo nano /etc/nginx/sites-available/sahabot2  # Edit domain and SSL paths
sudo ln -s /etc/nginx/sites-available/sahabot2 /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Copy and enable systemd service
sudo cp sahabot2.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sahabot2
sudo systemctl start sahabot2
sudo systemctl status sahabot2
```

See the [Deployment Guide](docs/operations/DEPLOYMENT_GUIDE.md) for complete setup instructions including database, SSL certificates, and monitoring.

## Security

This application implements comprehensive security best practices. See [SECURITY.md](SECURITY.md) for details on:

- 🛡️ Security headers (HSTS, CSP, X-Frame-Options)
- 🔒 HTTPS enforcement in production
- 🔐 Secure OAuth2 implementation with CSRF protection
- 🚫 Input validation and sanitization
- 🔑 Cryptographically secure token generation
- 📝 Audit logging without sensitive data exposure
- 🚨 Vulnerability reporting process
- 🔍 Automated CodeQL security scanning with custom anti-pattern queries

**Security Scan Results**: CodeQL - 0 alerts ✅

**CodeQL Analysis**: Automated scanning runs on every PR/push with 8+ custom queries detecting anti-patterns and security issues. See [`.github/codeql/README.md`](.github/codeql/README.md) for details.

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
