"""
Mock Discord data for testing.

Provides mock Discord API responses and objects.
"""

from typing import Dict, Any


def mock_discord_user_data(
    user_id: str = "123456789012345678",
    username: str = "testuser",
    discriminator: str = "0001",
    avatar: str = "test_avatar_hash",
    email: str = "testuser@example.com"
) -> Dict[str, Any]:
    """
    Create mock Discord user data.
    
    Args:
        user_id: Discord user ID
        username: Discord username
        discriminator: Discord discriminator
        avatar: Avatar hash
        email: Email address
        
    Returns:
        Mock Discord user data dict
    """
    return {
        "id": user_id,
        "username": username,
        "discriminator": discriminator,
        "avatar": avatar,
        "email": email,
        "verified": True,
        "locale": "en-US",
        "mfa_enabled": False,
        "flags": 0,
        "premium_type": 0,
    }


def mock_discord_guild_data(
    guild_id: str = "987654321098765432",
    name: str = "Test Guild"
) -> Dict[str, Any]:
    """
    Create mock Discord guild data.
    
    Args:
        guild_id: Discord guild ID
        name: Guild name
        
    Returns:
        Mock Discord guild data dict
    """
    return {
        "id": guild_id,
        "name": name,
        "icon": "guild_icon_hash",
        "owner_id": "123456789012345678",
        "permissions": "8",  # Administrator
    }


def mock_oauth_token_response(
    access_token: str = "mock_access_token",
    token_type: str = "Bearer",
    expires_in: int = 604800,
    refresh_token: str = "mock_refresh_token",
    scope: str = "identify email"
) -> Dict[str, Any]:
    """
    Create mock OAuth2 token response.
    
    Args:
        access_token: Access token
        token_type: Token type
        expires_in: Token expiration in seconds
        refresh_token: Refresh token
        scope: OAuth scopes
        
    Returns:
        Mock OAuth token response dict
    """
    return {
        "access_token": access_token,
        "token_type": token_type,
        "expires_in": expires_in,
        "refresh_token": refresh_token,
        "scope": scope,
    }
