"""
Repository for RaceTime Chat Command data access.

Handles database operations for racetime chat commands.
"""

import logging
from typing import Optional
from models import RacetimeChatCommand, CommandScope, CommandResponseType

logger = logging.getLogger(__name__)


class RacetimeChatCommandRepository:
    """Repository for RaceTime chat command data access."""

    async def get_all_commands(self) -> list[RacetimeChatCommand]:
        """
        Get all chat commands.

        Returns:
            List of all commands
        """
        return await RacetimeChatCommand.all().prefetch_related(
            "racetime_bot", "tournament", "async_tournament"
        )

    async def get_active_commands(self) -> list[RacetimeChatCommand]:
        """
        Get all active chat commands.

        Returns:
            List of active commands
        """
        return await RacetimeChatCommand.filter(is_active=True).prefetch_related(
            "racetime_bot", "tournament", "async_tournament"
        )

    async def get_command_by_id(self, command_id: int) -> Optional[RacetimeChatCommand]:
        """
        Get a command by ID.

        Args:
            command_id: Command ID

        Returns:
            Command or None if not found
        """
        return await RacetimeChatCommand.get_or_none(id=command_id).prefetch_related(
            "racetime_bot", "tournament", "async_tournament"
        )

    async def get_bot_commands(
        self, bot_id: int, active_only: bool = True
    ) -> list[RacetimeChatCommand]:
        """
        Get all commands for a specific bot.

        Args:
            bot_id: Bot ID
            active_only: Whether to return only active commands

        Returns:
            List of commands for the bot
        """
        filters = {"scope": CommandScope.BOT, "racetime_bot_id": bot_id}
        if active_only:
            filters["is_active"] = True

        return await RacetimeChatCommand.filter(**filters).all()

    async def get_tournament_commands(
        self, tournament_id: int, active_only: bool = True
    ) -> list[RacetimeChatCommand]:
        """
        Get all commands for a specific tournament.

        Args:
            tournament_id: Tournament ID
            active_only: Whether to return only active commands

        Returns:
            List of commands for the tournament
        """
        filters = {"scope": CommandScope.TOURNAMENT, "tournament_id": tournament_id}
        if active_only:
            filters["is_active"] = True

        return await RacetimeChatCommand.filter(**filters).all()

    async def get_async_tournament_commands(
        self, async_tournament_id: int, active_only: bool = True
    ) -> list[RacetimeChatCommand]:
        """
        Get all commands for a specific async tournament.

        Args:
            async_tournament_id: Async tournament ID
            active_only: Whether to return only active commands

        Returns:
            List of commands for the async tournament
        """
        filters = {
            "scope": CommandScope.ASYNC_TOURNAMENT,
            "async_tournament_id": async_tournament_id,
        }
        if active_only:
            filters["is_active"] = True

        return await RacetimeChatCommand.filter(**filters).all()

    async def create_command(
        self,
        command: str,
        scope: CommandScope,
        response_type: CommandResponseType,
        response_text: Optional[str] = None,
        handler_name: Optional[str] = None,
        description: Optional[str] = None,
        racetime_bot_id: Optional[int] = None,
        tournament_id: Optional[int] = None,
        async_tournament_id: Optional[int] = None,
        require_linked_account: bool = False,
        cooldown_seconds: int = 0,
        is_active: bool = True,
    ) -> RacetimeChatCommand:
        """
        Create a new chat command.

        Args:
            command: Command name (without ! prefix)
            scope: Command scope (BOT, TOURNAMENT, or ASYNC_TOURNAMENT)
            response_type: Response type (TEXT or DYNAMIC)
            response_text: Response text (for TEXT type)
            handler_name: Handler function name (for DYNAMIC type)
            description: Command description
            racetime_bot_id: Bot ID (for BOT scope)
            tournament_id: Tournament ID (for TOURNAMENT scope)
            async_tournament_id: Async tournament ID (for ASYNC_TOURNAMENT scope)
            require_linked_account: Whether user must have linked racetime account
            cooldown_seconds: Cooldown in seconds
            is_active: Whether command is active

        Returns:
            Created command
        """
        cmd = await RacetimeChatCommand.create(
            command=command.lower(),  # Normalize to lowercase
            scope=scope,
            response_type=response_type,
            response_text=response_text,
            handler_name=handler_name,
            description=description,
            racetime_bot_id=racetime_bot_id,
            tournament_id=tournament_id,
            async_tournament_id=async_tournament_id,
            require_linked_account=require_linked_account,
            cooldown_seconds=cooldown_seconds,
            is_active=is_active,
        )
        logger.info("Created chat command: !%s (scope: %s)", command, scope)
        return cmd

    async def update_command(
        self, command_id: int, **updates
    ) -> Optional[RacetimeChatCommand]:
        """
        Update a chat command.

        Args:
            command_id: Command ID
            **updates: Fields to update

        Returns:
            Updated command or None if not found
        """
        cmd = await self.get_command_by_id(command_id)
        if not cmd:
            return None

        # Normalize command name to lowercase if updating
        if "command" in updates:
            updates["command"] = updates["command"].lower()

        for key, value in updates.items():
            setattr(cmd, key, value)

        await cmd.save()
        logger.info("Updated chat command %s: %s", command_id, updates.keys())
        return cmd

    async def delete_command(self, command_id: int) -> bool:
        """
        Delete a chat command.

        Args:
            command_id: Command ID

        Returns:
            True if deleted, False if not found
        """
        cmd = await self.get_command_by_id(command_id)
        if not cmd:
            return False

        await cmd.delete()
        logger.info("Deleted chat command %s", command_id)
        return True

    async def get_command_by_name(
        self, command: str, bot_id: Optional[int] = None
    ) -> Optional[RacetimeChatCommand]:
        """
        Get a command by name and bot.

        Args:
            command: Command name (without ! prefix)
            bot_id: Bot ID (optional)

        Returns:
            Command or None if not found
        """
        filters = {"command": command.lower(), "is_active": True}
        if bot_id:
            filters["racetime_bot_id"] = bot_id
            filters["scope"] = CommandScope.BOT

        return await RacetimeChatCommand.get_or_none(**filters)
