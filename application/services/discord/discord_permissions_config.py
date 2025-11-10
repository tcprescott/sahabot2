"""
Discord permission requirements configuration.

This module centralizes Discord permission requirements for various features,
making it easy to adjust permission checks in one place.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class PermissionRequirement:
    """A permission requirement with description."""

    permission_name: str
    description: str
    required: bool = True  # If False, it's a warning but not strictly required


class AsyncQualifierChannelPermissions:
    """
    Permission requirements for async tournament Discord channels.

    Centralized configuration that can be easily modified to change
    permission requirements for async tournament channels.
    """

    # @everyone role restrictions (these should be DENIED for @everyone)
    EVERYONE_RESTRICTIONS: List[PermissionRequirement] = [
        PermissionRequirement(
            permission_name="send_messages",
            description="@everyone role can send messages (should be disabled)",
            required=True,
        ),
        PermissionRequirement(
            permission_name="create_public_threads",
            description="@everyone role can create public threads (should be disabled)",
            required=True,
        ),
        PermissionRequirement(
            permission_name="create_private_threads",
            description="@everyone role can create private threads (should be disabled)",
            required=True,
        ),
    ]

    # Bot required permissions (these must be ALLOWED for the bot)
    BOT_REQUIRED_PERMISSIONS: List[PermissionRequirement] = [
        PermissionRequirement(
            permission_name="send_messages",
            description="Bot cannot send messages (required for posting embeds and updates)",
            required=True,
        ),
        PermissionRequirement(
            permission_name="send_messages_in_threads",
            description="Bot cannot send messages in threads (required for race threads)",
            required=True,
        ),
        PermissionRequirement(
            permission_name="embed_links",
            description="Bot cannot embed links (required for rich embeds)",
            required=True,
        ),
        PermissionRequirement(
            permission_name="manage_threads",
            description="Bot cannot manage threads (required to add users to threads)",
            required=True,
        ),
        PermissionRequirement(
            permission_name="create_private_threads",
            description="Bot cannot create private threads (required for race threads)",
            required=True,
        ),
        PermissionRequirement(
            permission_name="read_message_history",
            description="Bot cannot read message history (required for thread operations)",
            required=True,
        ),
    ]

    @classmethod
    def get_everyone_restriction_names(cls) -> List[str]:
        """Get list of permission names that should be denied for @everyone."""
        return [req.permission_name for req in cls.EVERYONE_RESTRICTIONS]

    @classmethod
    def get_bot_permission_names(cls) -> List[str]:
        """Get list of permission names required for the bot."""
        return [req.permission_name for req in cls.BOT_REQUIRED_PERMISSIONS]

    @classmethod
    def get_everyone_restriction_description(cls, permission_name: str) -> str:
        """Get description for an @everyone restriction."""
        for req in cls.EVERYONE_RESTRICTIONS:
            if req.permission_name == permission_name:
                return req.description
        return f"@everyone has {permission_name} (should be disabled)"

    @classmethod
    def get_bot_permission_description(cls, permission_name: str) -> str:
        """Get description for a bot permission requirement."""
        for req in cls.BOT_REQUIRED_PERMISSIONS:
            if req.permission_name == permission_name:
                return req.description
        return f"Bot lacks {permission_name} (required)"
