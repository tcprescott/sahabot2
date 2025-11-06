"""
RaceTime Chat Command Service.

Business logic for managing and executing racetime chat commands.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable
from models import (
    User,
    Permission,
    RacetimeChatCommand,
    CommandScope,
    CommandResponseType,
)
from application.repositories.racetime_chat_command_repository import (
    RacetimeChatCommandRepository,
)

logger = logging.getLogger(__name__)


class RacetimeChatCommandService:
    """Service for managing RaceTime chat commands."""

    def __init__(self):
        self.repository = RacetimeChatCommandRepository()
        # Command cooldown tracking: {command_id: {user_id: last_use_timestamp}}
        self._cooldowns: dict[int, dict[str, datetime]] = {}
        # Registry of dynamic command handlers
        self._dynamic_handlers: dict[str, Callable] = {}

    def register_handler(
        self, handler_name: str, handler: Callable[..., Awaitable[str]]
    ) -> None:
        """
        Register a dynamic command handler.

        Args:
            handler_name: Name of the handler (must match handler_name in command)
            handler: Async callable that returns response text
                     Signature: async def handler(command: RacetimeChatCommand,
                                                  args: list[str],
                                                  user_id: Optional[str],
                                                  race_data: dict) -> str
        """
        self._dynamic_handlers[handler_name] = handler
        logger.info("Registered dynamic command handler: %s", handler_name)

    async def get_all_commands(
        self, current_user: Optional[User]
    ) -> list[RacetimeChatCommand]:
        """
        Get all commands (requires admin permission).

        Args:
            current_user: Current user

        Returns:
            List of commands or empty list if unauthorized
        """
        if not current_user or not current_user.has_permission(Permission.ADMIN):
            logger.warning(
                "Unauthorized access to get all commands by user %s",
                current_user.id if current_user else None,
            )
            return []

        return await self.repository.get_all_commands()

    async def get_commands_for_bot(
        self, bot_id: int, active_only: bool = True
    ) -> list[RacetimeChatCommand]:
        """
        Get all commands for a specific bot.

        Args:
            bot_id: Bot ID
            active_only: Whether to return only active commands

        Returns:
            List of commands
        """
        return await self.repository.get_bot_commands(bot_id, active_only)

    async def get_commands_for_tournament(
        self, tournament_id: int, active_only: bool = True
    ) -> list[RacetimeChatCommand]:
        """
        Get all commands for a specific tournament.

        Args:
            tournament_id: Tournament ID
            active_only: Whether to return only active commands

        Returns:
            List of commands
        """
        return await self.repository.get_tournament_commands(tournament_id, active_only)

    async def get_commands_for_async_tournament(
        self, async_tournament_id: int, active_only: bool = True
    ) -> list[RacetimeChatCommand]:
        """
        Get all commands for a specific async tournament.

        Args:
            async_tournament_id: Async tournament ID
            active_only: Whether to return only active commands

        Returns:
            List of commands
        """
        return await self.repository.get_async_tournament_commands(
            async_tournament_id, active_only
        )

    async def create_command(
        self,
        current_user: User,
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
    ) -> Optional[RacetimeChatCommand]:
        """
        Create a new chat command.

        Authorization: ADMIN or SUPERADMIN required.

        Args:
            current_user: User creating the command
            command: Command name (without ! prefix)
            scope: Command scope
            response_type: Response type
            response_text: Response text (for TEXT type)
            handler_name: Handler name (for DYNAMIC type)
            description: Command description
            racetime_bot_id: Bot ID (for BOT scope)
            tournament_id: Tournament ID (for TOURNAMENT scope)
            async_tournament_id: Async tournament ID (for ASYNC_TOURNAMENT scope)
            require_linked_account: Whether user must have linked account
            cooldown_seconds: Cooldown in seconds
            is_active: Whether command is active

        Returns:
            Created command or None if unauthorized
        """
        if not current_user or not current_user.has_permission(Permission.ADMIN):
            logger.warning(
                "Unauthorized attempt to create command by user %s",
                getattr(current_user, 'id', None)
            )
            return None

        # Validate scope matches provided IDs
        if scope == CommandScope.BOT and not racetime_bot_id:
            logger.error("BOT scope requires racetime_bot_id")
            return None
        if scope == CommandScope.TOURNAMENT and not tournament_id:
            logger.error("TOURNAMENT scope requires tournament_id")
            return None
        if scope == CommandScope.ASYNC_TOURNAMENT and not async_tournament_id:
            logger.error("ASYNC_TOURNAMENT scope requires async_tournament_id")
            return None

        # Validate response type matches provided data
        if response_type == CommandResponseType.TEXT and not response_text:
            logger.error("TEXT response type requires response_text")
            return None
        if response_type == CommandResponseType.DYNAMIC and not handler_name:
            logger.error("DYNAMIC response type requires handler_name")
            return None

        return await self.repository.create_command(
            command=command,
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

    async def update_command(
        self, current_user: User, command_id: int, **updates
    ) -> Optional[RacetimeChatCommand]:
        """
        Update a chat command.

        Authorization: ADMIN or SUPERADMIN required.

        Args:
            current_user: User updating the command
            command_id: Command ID
            **updates: Fields to update

        Returns:
            Updated command or None if unauthorized/not found
        """
        if not current_user or not current_user.has_permission(Permission.ADMIN):
            logger.warning(
                "Unauthorized attempt to update command %s by user %s",
                command_id,
                getattr(current_user, 'id', None),
            )
            return None

        return await self.repository.update_command(command_id, **updates)

    async def delete_command(self, current_user: User, command_id: int) -> bool:
        """
        Delete a chat command.

        Authorization: ADMIN or SUPERADMIN required.

        Args:
            current_user: User deleting the command
            command_id: Command ID

        Returns:
            True if deleted, False if unauthorized/not found
        """
        if not current_user or not current_user.has_permission(Permission.ADMIN):
            logger.warning(
                "Unauthorized attempt to delete command %s by user %s",
                command_id,
                getattr(current_user, 'id', None),
            )
            return False

        return await self.repository.delete_command(command_id)

    def _check_cooldown(
        self, command: RacetimeChatCommand, user_id: str
    ) -> tuple[bool, int]:
        """
        Check if command is on cooldown for user.

        Args:
            command: Command to check
            user_id: Racetime user ID

        Returns:
            Tuple of (can_use, remaining_seconds)
        """
        if command.cooldown_seconds <= 0:
            return True, 0

        if command.id not in self._cooldowns:
            self._cooldowns[command.id] = {}

        last_use = self._cooldowns[command.id].get(user_id)
        if not last_use:
            return True, 0

        now = datetime.now(timezone.utc)
        elapsed = (now - last_use).total_seconds()
        remaining = command.cooldown_seconds - elapsed

        if remaining <= 0:
            return True, 0

        return False, int(remaining)

    def _update_cooldown(self, command: RacetimeChatCommand, user_id: str) -> None:
        """
        Update cooldown timestamp for user.

        Args:
            command: Command being used
            user_id: Racetime user ID
        """
        if command.cooldown_seconds <= 0:
            return

        if command.id not in self._cooldowns:
            self._cooldowns[command.id] = {}

        self._cooldowns[command.id][user_id] = datetime.now(timezone.utc)

    async def execute_command(
        self,
        command_name: str,
        args: list[str],
        racetime_user_id: str,
        race_data: dict,
        bot_id: Optional[int] = None,
        tournament_id: Optional[int] = None,
        async_tournament_id: Optional[int] = None,
        user: Optional[User] = None,
    ) -> Optional[str]:
        """
        Execute a chat command and return the response.

        Args:
            command_name: Command name (without ! prefix)
            args: Command arguments
            racetime_user_id: Racetime user ID of command invoker
            race_data: Race data from racetime.gg
            bot_id: Bot ID (for matching bot-level commands)
            tournament_id: Tournament ID (for matching tournament commands)
            async_tournament_id: Async tournament ID (for matching async tournament commands)
            user: Application user (if racetime account is linked)

        Returns:
            Response text or None if command not found/executable
        """
        # Find matching command (priority: async_tournament > tournament > bot)
        command = None

        if async_tournament_id:
            commands = await self.repository.get_async_tournament_commands(
                async_tournament_id, active_only=True
            )
            command = next((c for c in commands if c.command == command_name.lower()), None)

        if not command and tournament_id:
            commands = await self.repository.get_tournament_commands(
                tournament_id, active_only=True
            )
            command = next((c for c in commands if c.command == command_name.lower()), None)

        if not command and bot_id:
            commands = await self.repository.get_bot_commands(bot_id, active_only=True)
            command = next((c for c in commands if c.command == command_name.lower()), None)

        if not command:
            logger.debug("No command found for !%s", command_name)
            return None

        # Check if linked account required
        if command.require_linked_account and not user:
            logger.debug(
                "Command !%s requires linked account, user not linked", command_name
            )
            return "This command requires a linked racetime account. Visit the website to link your account."

        # Check cooldown
        can_use, remaining = self._check_cooldown(command, racetime_user_id)
        if not can_use:
            logger.debug(
                "Command !%s on cooldown for user %s (%d seconds remaining)",
                command_name,
                racetime_user_id,
                remaining,
            )
            return f"Command on cooldown. Try again in {remaining} seconds."

        # Execute command
        response = None
        if command.response_type == CommandResponseType.TEXT:
            response = command.response_text
        elif command.response_type == CommandResponseType.DYNAMIC:
            handler = self._dynamic_handlers.get(command.handler_name)
            if not handler:
                logger.error(
                    "No handler registered for %s (command: !%s)",
                    command.handler_name,
                    command_name,
                )
                return "Command handler not available."

            try:
                response = await handler(command, args, racetime_user_id, race_data, user)
            except Exception as e:
                logger.error(
                    "Error executing handler %s: %s",
                    command.handler_name,
                    e,
                    exc_info=True,
                )
                return "An error occurred while executing the command."

        # Update cooldown
        if response:
            self._update_cooldown(command, racetime_user_id)

        return response
