# Security Policy

## Overview

SahaBot2 takes security seriously. This document outlines our security practices, reporting procedures, and implemented security measures.

## Supported Versions

We currently support security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in SahaBot2, please report it responsibly:

1. **DO NOT** open a public issue
2. Email the maintainers directly at: [INSERT SECURITY EMAIL]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

You can expect:
- Acknowledgment within 48 hours
- Regular updates on the status
- Credit in the security advisory (unless you prefer to remain anonymous)

## Security Measures

### Authentication & Authorization

#### Discord OAuth2
- **OAuth2 Flow**: Secure authentication via Discord's OAuth2 implementation
- **CSRF Protection**: State parameter validation with cryptographically secure random tokens
- **State Management**: 10-minute expiration window for OAuth state tokens
- **Session Security**: Sessions encrypted with `SECRET_KEY` stored securely
- **Token Storage**: Browser storage only for non-sensitive state data

#### API Token Authentication
- **Token Generation**: Cryptographically secure random tokens using `secrets.token_urlsafe(32)`
- **Token Storage**: Only SHA256 hashes stored in database, plaintext shown once on creation
- **Constant-Time Comparison**: Protected against timing attacks using `hmac.compare_digest()`
- **Token Expiration**: Optional expiration dates supported
- **Rate Limiting**: Per-user rate limits enforced (default 60 requests/minute)

#### Authorization
- **Database-Driven Permissions**: Four permission levels (USER, MODERATOR, ADMIN, SUPERADMIN)
- **Server-Side Enforcement**: All permissions checked server-side, never trusted from client
- **Service Layer Authorization**: Authorization logic centralized in `AuthorizationService`
- **Multi-Tenant Isolation**: Organization-scoped data access with membership validation

### Transport Security

#### HTTPS Enforcement
- **Production Mode**: Automatic HTTP to HTTPS redirect in production
- **HSTS Header**: Strict-Transport-Security header with 1-year duration in production
- **Proxy Support**: Respects `X-Forwarded-Proto` header for reverse proxy scenarios

#### Security Headers
All responses include the following security headers:

- **X-Content-Type-Options**: `nosniff` - Prevents MIME type sniffing
- **X-Frame-Options**: `DENY` - Prevents clickjacking attacks
- **X-XSS-Protection**: `1; mode=block` - Legacy XSS protection (defense in depth)
- **Referrer-Policy**: `strict-origin-when-cross-origin` - Controls referrer information
- **Permissions-Policy**: Restricts browser features (geolocation, microphone, camera)
- **Content-Security-Policy**: Restricts resource loading and inline scripts
  - Default-src: self
  - Script-src: self, unsafe-inline, unsafe-eval (required for NiceGUI), CDN
  - Style-src: self, unsafe-inline, Google Fonts
  - Connect-src: self, Discord API, RaceTime.gg API
  - Frame-ancestors: none

### Data Protection

#### Password Storage
- **No Password Storage**: Application uses OAuth2 only, no passwords stored
- **API Tokens**: Hashed using SHA256 before storage
- **Secret Keys**: All secrets stored in environment variables, never in code

#### Sensitive Data Handling
- **Database Credentials**: Never logged or exposed in error messages
- **OAuth Tokens**: Access tokens not persisted, only used during authentication flow
- **User Emails**: Treated as PII, only visible to SUPERADMIN users
- **Audit Logging**: All authentication events and permission changes logged

#### Data Validation
- **ORM Protection**: Tortoise ORM with parameterized queries prevents SQL injection
- **Input Validation**: Pydantic schemas validate all API inputs
- **Type Safety**: Full type hints throughout codebase
- **No Raw SQL**: All database access through ORM, no raw SQL execution

### Application Security

#### Rate Limiting
- **API Endpoints**: Per-user rate limiting with sliding window (60 requests/60 seconds)
- **Customizable Limits**: Per-user limits can be adjusted by administrators
- **429 Response**: Rate limit exceeded returns HTTP 429 with Retry-After header

#### Session Management
- **Session Encryption**: Sessions encrypted with `SECRET_KEY`
- **Session Timeout**: Automatic logout after inactivity (configurable)
- **CSRF Protection**: State tokens for OAuth flows prevent CSRF attacks

#### Error Handling
- **No Information Disclosure**: Error messages don't reveal sensitive system information
- **Logging**: Security events logged without exposing sensitive data
- **Stack Traces**: Only shown in development mode, hidden in production

### Code Security

#### Dependencies
- **Poetry**: Dependency management with lockfile for reproducible builds
- **Regular Updates**: Dependencies reviewed and updated regularly
- **Known Vulnerabilities**: Dependencies scanned for known vulnerabilities

#### Secure Coding Practices
- **No eval/exec**: No dynamic code execution functions used
- **Input Sanitization**: All user inputs validated and sanitized
- **Async/Await**: Modern async patterns throughout (prevents blocking attacks)
- **Type Safety**: Comprehensive type hints catch type-related bugs

### Infrastructure Security

#### Environment Variables
- **Secrets Management**: All secrets in `.env` file, never committed to git
- **Example File**: `.env.example` provided without real credentials
- **Config Validation**: Pydantic validates all configuration on startup

#### Database Security
- **Connection Security**: MySQL connections with credentials from environment
- **User Permissions**: Database user has minimum required privileges
- **Migrations**: Schema changes through Aerich migrations only

## Security Configuration

### Production Deployment Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Set `DEBUG=False` in `.env`
- [ ] Generate strong `SECRET_KEY` (at least 32 random characters)
- [ ] Use HTTPS (configure reverse proxy or load balancer)
- [ ] Set secure Discord OAuth2 redirect URI (HTTPS)
- [ ] Configure firewall to restrict database access
- [ ] Enable database backups
- [ ] Review and adjust rate limits as needed
- [ ] Monitor logs for security events
- [ ] Keep dependencies updated

### Environment Variables Security

**Required Secrets** (keep secure, never commit):
- `SECRET_KEY` - Session encryption key
- `DB_PASSWORD` - Database password
- `DISCORD_CLIENT_SECRET` - Discord OAuth2 secret
- `DISCORD_BOT_TOKEN` - Discord bot token
- `RACETIME_CLIENT_SECRET` - RaceTime.gg OAuth2 secret (if using)

**Configuration** (can be less sensitive but still protect):
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_NAME` - Database connection info
- `DISCORD_CLIENT_ID` - Discord OAuth2 client ID
- `BASE_URL` - Your application's public URL

### Security Headers Configuration

The default CSP is relatively permissive to allow NiceGUI to function. You may want to tighten it based on your specific deployment:

```python
# In middleware/security.py, adjust CSP as needed:
"Content-Security-Policy": (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
    # ... customize other directives
)
```

## Security Best Practices

### For Developers

1. **Never commit secrets** - Use `.env` file, check `.gitignore`
2. **Validate all inputs** - Use Pydantic schemas for API inputs
3. **Use parameterized queries** - Always use ORM, never raw SQL
4. **Log security events** - But never log sensitive data (passwords, tokens)
5. **Test authorization** - Verify permission checks work correctly
6. **Review dependencies** - Check for known vulnerabilities before adding
7. **Use type hints** - Helps catch bugs before runtime
8. **Follow separation of concerns** - Keep authorization in service layer

### For Administrators

1. **Strong SECRET_KEY** - Use at least 32 random characters
2. **Database security** - Restrict network access, use strong passwords
3. **HTTPS only** - Configure reverse proxy for HTTPS in production
4. **Monitor logs** - Watch for suspicious authentication attempts
5. **Regular updates** - Keep dependencies and system packages updated
6. **Backup data** - Regular database backups with secure storage
7. **Rate limits** - Adjust per-user limits based on usage patterns
8. **Audit logs** - Review audit logs periodically

### For Users

1. **Discord account security** - Use 2FA on your Discord account
2. **API tokens** - Treat them like passwords, never share
3. **Token rotation** - Regenerate tokens if compromised
4. **Browser security** - Use updated browser, enable security features

## Security Features Roadmap

Future security enhancements planned:

- [ ] Two-factor authentication (2FA) support
- [ ] IP-based rate limiting in addition to user-based
- [ ] Account lockout after failed authentication attempts
- [ ] Security event notifications (Discord/email)
- [ ] Automated dependency vulnerability scanning
- [ ] Content Security Policy report-only mode for testing
- [ ] API request signing for webhook endpoints
- [ ] Session activity logging and management UI

## Compliance

### Data Protection
- User emails treated as PII
- Audit logging for user actions
- Data retention policies (to be defined)
- User data export/deletion (to be implemented)

### Standards
- OWASP Top 10 considerations applied
- OAuth2 best practices followed
- Rate limiting prevents abuse
- Security headers per industry standards

## Contact

For security concerns or questions:
- Security issues: [INSERT SECURITY EMAIL]
- General questions: GitHub Issues (for non-security matters)

## Acknowledgments

We appreciate the security research community and will acknowledge reporters of valid security issues in our security advisories (unless anonymity is requested).

---

**Last Updated**: 2025-11-04  
**Version**: 0.1.0
