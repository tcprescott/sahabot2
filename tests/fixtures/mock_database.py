"""
Mock database data for testing.

Provides factory functions for creating test database objects.
"""

from typing import Dict, Any
from models.user import Permission


def user_data(
    discord_id: int = 123456789012345678,
    discord_username: str = "testuser",
    discord_discriminator: str = "0001",
    discord_avatar: str = "test_avatar_hash",
    discord_email: str = "testuser@example.com",
    permission: Permission = Permission.USER,
    is_active: bool = True
) -> Dict[str, Any]:
    """
    Create user data dict for database insertion.
    
    Args:
        discord_id: Discord user ID
        discord_username: Discord username
        discord_discriminator: Discord discriminator
        discord_avatar: Avatar hash
        discord_email: Email address
        permission: User permission level
        is_active: Whether user is active
        
    Returns:
        User data dict
    """
    return {
        "discord_id": discord_id,
        "discord_username": discord_username,
        "discord_discriminator": discord_discriminator,
        "discord_avatar": discord_avatar,
        "discord_email": discord_email,
        "permission": permission,
        "is_active": is_active,
    }


def admin_user_data() -> Dict[str, Any]:
    """
    Create admin user data dict.
    
    Returns:
        Admin user data dict
    """
    return user_data(
        discord_id=987654321098765432,
        discord_username="admin",
        discord_discriminator="0002",
        discord_email="admin@example.com",
        permission=Permission.ADMIN
    )


def moderator_user_data() -> Dict[str, Any]:
    """
    Create moderator user data dict.
    
    Returns:
        Moderator user data dict
    """
    return user_data(
        discord_id=111222333444555666,
        discord_username="moderator",
        discord_discriminator="0003",
        discord_email="moderator@example.com",
        permission=Permission.MODERATOR
    )


def audit_log_data(
    user_id: int,
    action: str = "test_action",
    details: Dict[str, Any] = None,
    ip_address: str = "127.0.0.1"
) -> Dict[str, Any]:
    """
    Create audit log data dict.
    
    Args:
        user_id: User ID
        action: Action performed
        details: JSON details
        ip_address: IP address
        
    Returns:
        Audit log data dict
    """
    return {
        "user_id": user_id,
        "action": action,
        "details": details or {},
        "ip_address": ip_address,
    }
