#!/usr/bin/env python3
"""
Discord OAuth2 Configuration Checker

This script helps diagnose Discord OAuth2 configuration issues.
Run this to verify your Discord settings are correct.
"""

from config import settings
import sys


def check_discord_config():
    """Check Discord OAuth2 configuration."""
    print("=" * 70)
    print("Discord OAuth2 Configuration Check")
    print("=" * 70)
    print()

    issues = []
    warnings = []

    # Check Client ID
    print(
        f"✓ DISCORD_CLIENT_ID: {settings.DISCORD_CLIENT_ID[:10]}..."
        if len(settings.DISCORD_CLIENT_ID) > 10
        else f"✗ DISCORD_CLIENT_ID: {settings.DISCORD_CLIENT_ID}"
    )
    if (
        not settings.DISCORD_CLIENT_ID
        or settings.DISCORD_CLIENT_ID == "your_discord_client_id"
    ):
        issues.append("DISCORD_CLIENT_ID is not set or uses default value")

    # Check Client Secret
    has_secret = (
        settings.DISCORD_CLIENT_SECRET
        and settings.DISCORD_CLIENT_SECRET != "your_discord_client_secret"
    )
    print(
        f"✓ DISCORD_CLIENT_SECRET: {'*' * 10}..."
        if has_secret
        else "✗ DISCORD_CLIENT_SECRET: NOT SET"
    )
    if not has_secret:
        issues.append("DISCORD_CLIENT_SECRET is not set or uses default value")

    # Check Redirect URI
    print(f"✓ DISCORD_REDIRECT_URI: {settings.DISCORD_REDIRECT_URI}")
    if not settings.DISCORD_REDIRECT_URI:
        issues.append("DISCORD_REDIRECT_URI is not set")
    elif (
        "localhost" in settings.DISCORD_REDIRECT_URI
        and settings.ENVIRONMENT == "production"
    ):
        warnings.append("Using localhost redirect URI in production")

    # Validate redirect URI format
    if settings.DISCORD_REDIRECT_URI:
        if not settings.DISCORD_REDIRECT_URI.startswith(("http://", "https://")):
            issues.append("DISCORD_REDIRECT_URI must start with http:// or https://")
        if not settings.DISCORD_REDIRECT_URI.endswith("/auth/callback"):
            warnings.append("DISCORD_REDIRECT_URI should end with /auth/callback")

    # Check Bot Token
    has_bot_token = (
        settings.DISCORD_BOT_TOKEN
        and settings.DISCORD_BOT_TOKEN != "your_discord_bot_token_here"
    )
    print(
        f"✓ DISCORD_BOT_TOKEN: {'*' * 10}..."
        if has_bot_token
        else "⚠ DISCORD_BOT_TOKEN: NOT SET"
    )
    if not has_bot_token:
        warnings.append(
            "DISCORD_BOT_TOKEN is not set (needed for Discord bot features)"
        )

    print()
    print("=" * 70)

    # Report issues
    if issues:
        print("❌ CRITICAL ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print()

    if warnings:
        print("⚠️  WARNINGS:")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
        print()

    if not issues and not warnings:
        print("✅ All Discord OAuth2 settings appear to be configured correctly!")
        print()

    # Instructions
    print("=" * 70)
    print("DISCORD SETUP INSTRUCTIONS:")
    print("=" * 70)
    print()
    print("1. Go to: https://discord.com/developers/applications")
    print("2. Select your application")
    print("3. Go to 'OAuth2' → 'General'")
    print()
    print("4. Verify these settings:")
    print(f"   - Client ID matches: {settings.DISCORD_CLIENT_ID}")
    print(f"   - Redirects contains: {settings.DISCORD_REDIRECT_URI}")
    print()
    print("5. IMPORTANT: The redirect URI in Discord must EXACTLY match")
    print("   the one in your .env file (including http/https, port, path)")
    print()
    print("6. Copy the Client Secret from Discord and set it in your .env file")
    print()
    print("=" * 70)

    return len(issues) == 0


if __name__ == "__main__":
    success = check_discord_config()
    sys.exit(0 if success else 1)
