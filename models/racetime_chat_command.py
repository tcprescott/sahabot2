"""
RaceTime Chat Command models.

Models for managing custom chat commands in racetime.gg race rooms.
Commands can be defined at the bot level (global) or tournament level (scoped).
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from enum import IntEnum
from tortoise import fields
from tortoise.models import Model

if TYPE_CHECKING:
    from .racetime_bot import RacetimeBot
    from .match_schedule import Tournament
    from .async_tournament import AsyncTournament


class CommandScope(IntEnum):
    """Scope of a racetime chat command."""

    BOT = 0  # Command available in all rooms for this bot
    TOURNAMENT = 1  # Command available only in rooms for a specific tournament
    ASYNC_TOURNAMENT = 2  # Command available only in async tournament rooms


class CommandResponseType(IntEnum):
    """Type of response for a command."""

    TEXT = 0  # Simple text response
    DYNAMIC = 1  # Dynamic response (calls handler function)


class RacetimeChatCommand(Model):
    """
    Custom chat command for racetime.gg rooms.

    Commands are prefixed with ! and can be scoped to:
    - BOT: Available in all rooms handled by a specific bot
    - TOURNAMENT: Available only in rooms for a specific tournament
    - ASYNC_TOURNAMENT: Available only in async tournament rooms

    For TEXT commands, the response_text is sent directly.
    For DYNAMIC commands, a handler function is called based on handler_name.
    """

    id = fields.IntField(pk=True)

    # Command details
    command = fields.CharField(
        max_length=50, description="Command name without prefix"
    )
    description = fields.TextField(null=True, description="Command description")
    response_type = fields.IntEnumField(
        CommandResponseType, default=CommandResponseType.TEXT, description="Response type"
    )
    response_text = fields.TextField(
        null=True, description="Response text for TEXT commands"
    )
    handler_name = fields.CharField(
        max_length=100,
        null=True,
        description="Handler function name for DYNAMIC commands",
    )

    # Scope and targeting
    scope = fields.IntEnumField(CommandScope, description="Command scope")
    racetime_bot = fields.ForeignKeyField(
        "models.RacetimeBot", related_name="chat_commands", null=True
    )
    tournament = fields.ForeignKeyField(
        "models.Tournament", related_name="chat_commands", null=True
    )
    async_tournament = fields.ForeignKeyField(
        "models.AsyncTournament", related_name="chat_commands", null=True
    )

    # Permissions and behavior
    require_linked_account = fields.BooleanField(
        default=False,
        description="Whether user must have linked racetime account",
    )
    cooldown_seconds = fields.IntField(
        default=0, description="Cooldown seconds before reuse"
    )
    is_active = fields.BooleanField(default=True, description="Whether command is enabled")

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "racetime_chat_commands"
        unique_together = (
            ("racetime_bot", "command"),  # Unique command per bot
            ("tournament", "command"),  # Unique command per tournament
            ("async_tournament", "command"),  # Unique command per async tournament
        )

    def __str__(self) -> str:
        scope_str = {
            CommandScope.BOT: "Bot",
            CommandScope.TOURNAMENT: "Tournament",
            CommandScope.ASYNC_TOURNAMENT: "Async Tournament",
        }.get(self.scope, "Unknown")
        return f"!{self.command} ({scope_str})"

    def get_scope_display(self) -> str:
        """Get human-readable scope."""
        return {
            CommandScope.BOT: "Bot-wide",
            CommandScope.TOURNAMENT: "Tournament",
            CommandScope.ASYNC_TOURNAMENT: "Async Tournament",
        }.get(self.scope, "Unknown")

    def get_response_type_display(self) -> str:
        """Get human-readable response type."""
        return {
            CommandResponseType.TEXT: "Text Response",
            CommandResponseType.DYNAMIC: "Dynamic Handler",
        }.get(self.response_type, "Unknown")
