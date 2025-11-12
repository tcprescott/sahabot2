"""
Racetime.gg bot client implementation.

This module provides a bot client for racetime.gg integration.

IMPORTANT: This implementation follows patterns from the original SahasrahBot, which used
a forked version of racetime-bot (https://github.com/tcprescott/racetime-bot) that adds
custom methods not present in the upstream library:

- Bot.startrace(**kwargs) - Creates a race room and returns a handler
- Bot.join_race_room(race_name, force=False) - Joins a race room and returns a handler
- Handler.invite_user(user) - Invites a user via websocket
- Handler.send_message(message, ...) - Sends messages via websocket

SahaBot2 uses the upstream racetime-bot library (v2.3.0), so we implement our own
simplified versions of the fork-specific methods (startrace, join_race_room) to maintain
compatibility with the original workflow.

We also create our own aiohttp.ClientSession (self.http) for efficient connection pooling,
rather than using aiohttp.request() directly like the base Bot class does.

RACE ROOM JOINING BEHAVIOR:
- The upstream racetime-bot library has automatic race room polling/joining via refresh_races()
- SahaBot2 DISABLES this automatic polling behavior (refresh_races() task is not started)
- Instead, race rooms are joined EXPLICITLY via:
  * Task scheduler system (scheduled race room creation/joining)
  * Manual commands (!startrace, etc.)
  * API calls (startrace, join_race_room methods)
- The should_handle() method always returns False to prevent automatic joining
- This gives us full control over when and how race rooms are joined
"""

import asyncio
import logging
from typing import Optional

import aiohttp
from racetime_bot import Bot

from config import settings
from models import BotStatus
from racetime.handlers.base_handler import SahaRaceHandler
from application.repositories.racetime_bot_repository import RacetimeBotRepository

# Configure logging
logger = logging.getLogger(__name__)

class RacetimeBot(Bot):
    """
    Custom racetime.gg bot client for SahaBot2.

    This bot integrates with racetime.gg to provide race management
    and monitoring functionality.
    """

    # Override the default racetime host and security settings with configured values
    # Extract just the hostname from the full URL (e.g., "http://localhost:8000" -> "localhost:8000")
    racetime_host = (
        settings.RACETIME_URL.replace("https://", "").replace("http://", "").rstrip("/")
    )
    # Determine if TLS/SSL should be used based on URL scheme
    racetime_secure = settings.RACETIME_URL.startswith("https://")

    def __init__(
        self,
        category_slug: str,
        client_id: str,
        client_secret: str,
        bot_id: Optional[int] = None,
        handler_class_name: str = "SahaRaceHandler",
    ):
        """
        Initialize the racetime bot with configuration.

        Args:
            category_slug: The racetime.gg category (e.g., 'alttpr')
            client_id: OAuth2 client ID for this category
            client_secret: OAuth2 client secret for this category
            bot_id: Optional database ID for status tracking
            handler_class_name: Name of the handler class to use (e.g., 'ALTTPRRaceHandler')
        """
        logger.info(
            "Initializing racetime bot with category=%s, client_id=%s, client_secret=%s..., handler=%s (host: %s, secure: %s)",
            category_slug,
            client_id,
            client_secret[:10] + "..." if len(client_secret) > 10 else "***",
            handler_class_name,
            self.racetime_host,
            self.racetime_secure,
        )
        try:
            super().__init__(
                category_slug=category_slug,
                client_id=client_id,
                client_secret=client_secret,
                logger=logger,
            )
        except Exception as e:
            logger.error(
                "Failed to initialize racetime bot for category %s: %s. "
                "Please verify that an OAuth2 application exists in your racetime instance "
                "with these credentials and uses the 'client_credentials' grant type.",
                category_slug,
                e,
            )
            raise
        self.category_slug = category_slug
        self.bot_id = bot_id
        self.handler_class_name = handler_class_name

        # Create our own aiohttp session for efficient connection pooling
        # (The base Bot class uses aiohttp.request() directly without a session)
        self.http: Optional[aiohttp.ClientSession] = None

        logger.info(
            "Racetime bot initialized successfully for category: %s with handler: %s",
            category_slug,
            handler_class_name,
        )

    def should_handle(self, race_data: dict) -> bool:
        """
        Determine if this bot should handle a specific race.

        NOTE: This method is not used in SahaBot2. We do NOT use automatic race
        room polling/joining. Instead, race rooms are joined explicitly via the
        task scheduler system or manual commands.

        This method is kept for compatibility with the base Bot class, but always
        returns False to prevent automatic joining.

        Args:
            race_data: Race data from racetime.gg

        Returns:
            bool: Always False - we don't auto-join races
        """
        # Always return False - we use explicit joining via scheduler, not automatic polling
        return False

    def get_handler_class(self):
        """
        Return the handler class to use for race rooms.

        Override of Bot.get_handler_class() to use our configured handler.

        The handler class is determined by the handler_class_name set during initialization.
        Supported handlers:
        - SahaRaceHandler (default - base handler with common commands)
        - ALTTPRRaceHandler (ALTTPR-specific commands)
        - SMRaceHandler (Super Metroid-specific commands)
        - SMZ3RaceHandler (SMZ3-specific commands)
        - AsyncLiveRaceHandler (async tournament live race handler)

        For tournament matches, use combined handlers that include MatchRaceMixin:
        - MatchALTTPRRaceHandler (ALTTPR commands + match processing)
        - MatchSMRaceHandler (SM commands + match processing)
        - MatchSMZ3RaceHandler (SMZ3 commands + match processing)
        - MatchSahaRaceHandler (base commands + match processing)

        Returns:
            Handler class to use for race rooms
        """
        # Map handler names to classes
        from racetime.handlers.alttpr_handler import ALTTPRRaceHandler
        from racetime.handlers.sm_race_handler import SMRaceHandler
        from racetime.handlers.smz3_race_handler import SMZ3RaceHandler
        from racetime.handlers.match_race_handler import create_match_handler_class
        from racetime.handlers.live_race_handler import AsyncLiveRaceHandler

        handler_map = {
            "SahaRaceHandler": SahaRaceHandler,
            "ALTTPRRaceHandler": ALTTPRRaceHandler,
            "SMRaceHandler": SMRaceHandler,
            "SMZ3RaceHandler": SMZ3RaceHandler,
            "AsyncLiveRaceHandler": AsyncLiveRaceHandler,
            # Combined match handlers
            "MatchSahaRaceHandler": create_match_handler_class(SahaRaceHandler),
            "MatchALTTPRRaceHandler": create_match_handler_class(ALTTPRRaceHandler),
            "MatchSMRaceHandler": create_match_handler_class(SMRaceHandler),
            "MatchSMZ3RaceHandler": create_match_handler_class(SMZ3RaceHandler),
        }

        handler_class = handler_map.get(self.handler_class_name)

        if not handler_class:
            logger.warning(
                "Unknown handler class %s, falling back to SahaRaceHandler",
                self.handler_class_name,
            )
            return SahaRaceHandler

        logger.debug("Using handler class: %s", self.handler_class_name)
        return handler_class

    def _setup_handler_connection(self, race_data: dict):
        """
        Set up websocket connection and handler kwargs for a race handler.

        This is a helper method to avoid code duplication between create_handler()
        and create_match_handler().

        Args:
            race_data: Race data from racetime.gg API

        Returns:
            Tuple of (handler_kwargs, race_name)
        """
        # Import websockets for connection setup
        import websockets

        # Set up websocket connection parameters
        connect_kwargs = {
            "additional_headers": {
                "Authorization": "Bearer " + self.access_token,
            },
        }

        # BC for websockets<14 (from upstream)
        try:
            ws_version = int(websockets.version.version.split(".")[0])
        except (AttributeError, TypeError, ValueError):
            ws_version = 14
        if ws_version < 14:
            connect_kwargs["extra_headers"] = connect_kwargs.pop("additional_headers")

        if self.ssl_context is not None and self.racetime_secure:
            connect_kwargs["ssl"] = self.ssl_context

        ws_conn = websockets.connect(
            self.ws_uri(race_data.get("websocket_bot_url")),
            **connect_kwargs,
        )

        race_name = race_data.get("name")
        if race_name not in self.state:
            self.state[race_name] = {}

        # Get handler kwargs
        kwargs = self.get_handler_kwargs(ws_conn, self.state[race_name])

        # Inject bot_instance for our custom handlers
        kwargs["bot_instance"] = self

        return kwargs, race_name

    def create_handler(self, race_data: dict):
        """
        Create a handler instance for a race.

        Override of Bot.create_handler() to inject bot_instance parameter
        that our custom handlers require.

        This follows the upstream library's pattern but adds bot_instance to kwargs.

        Args:
            race_data: Race data from racetime.gg API

        Returns:
            Handler instance for the race
        """
        kwargs, race_name = self._setup_handler_connection(race_data)

        # Get handler class
        handler_class = self.get_handler_class()

        # Create handler with all required parameters
        handler = handler_class(**kwargs)
        handler.data = race_data

        logger.info("Created handler for race %s", race_data.get("name"))

        return handler

    def create_match_handler(self, race_data: dict, match_id: int):
        """
        Create a match-specific handler instance for a race.

        This creates a handler that combines the bot's configured handler class
        with MatchRaceMixin to provide both category-specific commands and
        match processing functionality.

        Args:
            race_data: Race data from racetime.gg API
            match_id: ID of the match this race is for

        Returns:
            Handler instance for the match race
        """
        from racetime.handlers.match_race_handler import create_match_handler_class

        kwargs, race_name = self._setup_handler_connection(race_data)

        # Get the base handler class and create a match variant
        base_handler_class = self.get_handler_class()
        match_handler_class = create_match_handler_class(base_handler_class)

        # Inject match_id for the match handler
        kwargs["match_id"] = match_id

        # Create handler with all required parameters
        handler = match_handler_class(**kwargs)
        handler.data = race_data

        logger.info(
            "Created match handler for race %s (match_id=%s)",
            race_data.get("name"),
            match_id,
        )

        return handler

    async def join_race_room(
        self, race_name: str, force: bool = False
    ) -> Optional[SahaRaceHandler]:
        """
        Join a race room and create a handler for it.

        This is a simplified implementation of the fork's join_race_room() method.
        It fetches race data, creates a handler, and starts the handler task.

        If the room is associated with a match, automatically uses a match-aware handler
        that combines the bot's configured handler with MatchRaceMixin.

        Reference (fork implementation):
        https://github.com/tcprescott/racetime-bot/blob/main/racetime_bot/bot.py#L228-L283

        Args:
            race_name: Race slug (e.g., "alttpr/cool-doge-1234")
            force: If True, join even if should_handle() returns False

        Returns:
            SahaRaceHandler for the race, or None on failure
        """
        logger.info("Attempting to join race room: %s", race_name)

        # Validate race belongs to our category
        if not race_name.startswith(f"{self.category_slug}/"):
            logger.error(
                "Race %s is not for category %s", race_name, self.category_slug
            )
            return None

        # Ensure HTTP session is created
        if not self.http:
            logger.error("Bot not initialized - no HTTP session")
            return None

        # Fetch race data with retry logic
        race_data = None
        max_attempts = 5
        backoff_delay = 1.0

        for attempt in range(max_attempts):
            try:
                url = self.http_uri(f"/{race_name}/data")
                async with self.http.get(url, ssl=self.ssl_context) as resp:
                    resp.raise_for_status()
                    race_data = await resp.json()
                    break  # Success!

            except Exception as e:
                logger.warning(
                    "Failed to fetch race data for %s (attempt %d/%d): %s",
                    race_name,
                    attempt + 1,
                    max_attempts,
                    e,
                )
                if attempt < max_attempts - 1:
                    await asyncio.sleep(backoff_delay)
                    backoff_delay = min(
                        backoff_delay * 2, 10.0
                    )  # Exponential backoff, max 10s
                else:
                    logger.error(
                        "Failed to fetch race data after %d attempts", max_attempts
                    )
                    return None

        if not race_data:
            return None

        # Check if we should handle this race
        if not force and not self.should_handle(race_data):
            logger.info("Not handling race %s by configuration", race_name)
            return None

        # Check if we already have a handler for this race
        if hasattr(self, "handlers") and race_name in self.handlers:
            logger.info("Already have handler for race %s", race_name)
            existing_handler = self.handlers[race_name]
            # Return the handler object (fork stores in TaskHandler.handler)
            if hasattr(existing_handler, "handler"):
                return existing_handler.handler
            return existing_handler

        # Check if this room is associated with a match
        # If so, use a match-aware handler instead of the base handler
        match_id = await self._get_match_id_for_room(race_name)

        # Create handler for the race
        try:
            if match_id is not None:
                # Room is for a match - use match handler
                logger.info(
                    "Room %s is for match %s, using match handler",
                    race_name,
                    match_id,
                )
                handler = self.create_match_handler(race_data, match_id)
            else:
                # Regular room - use base handler
                handler = self.create_handler(race_data)

            # If force=True, this means the bot created the room (via startrace)
            # Set a public flag so begin() knows to emit RacetimeBotCreatedRaceEvent
            if force:
                setattr(handler, "bot_created_room", True)

            logger.info("Created handler for race %s", race_name)
            return handler

        except Exception as e:
            logger.error(
                "Failed to create handler for race %s: %s", race_name, e, exc_info=True
            )
            return None

    async def _get_match_id_for_room(self, room_slug: str) -> Optional[int]:
        """
        Check if a race room is associated with a match.

        Args:
            room_slug: The race room slug (e.g., "alttpr/cool-doge-1234")

        Returns:
            Match ID if room is for a match, None otherwise
        """
        from models.racetime_room import RacetimeRoom

        try:
            room = await RacetimeRoom.filter(slug=room_slug).first()
            if room and room.match_id:
                return room.match_id
            return None
        except Exception as e:
            logger.warning(
                "Failed to check match association for room %s: %s", room_slug, e
            )
            return None

    async def startrace(
        self,
        goal: Optional[str] = None,
        custom_goal: Optional[str] = None,
        invitational: bool = True,
        unlisted: bool = False,
        info_user: str = "",
        start_delay: int = 15,
        time_limit: int = 24,
        streaming_required: bool = True,
        auto_start: bool = True,
        allow_comments: bool = True,
        hide_comments: bool = True,
        allow_prerace_chat: bool = True,
        allow_midrace_chat: bool = True,
        allow_non_entrant_chat: bool = False,
        chat_message_delay: int = 0,
        team_race: bool = False,
    ) -> Optional[SahaRaceHandler]:
        """
        Create a race room on racetime.gg.

        This method mirrors the startrace() implementation from the tcprescott/racetime-bot
        fork used by the original SahasrahBot. The fork's implementation:
        1. Validates goal vs custom_goal (only one allowed)
        2. POSTs to /o/{category}/startrace with race configuration
        3. Extracts race slug from Location header
        4. Calls join_race_room() to create a handler for the new room
        5. Returns the handler object

        Reference: https://github.com/tcprescott/racetime-bot/blob/main/racetime_bot/bot.py#L285-L324

        Either goal OR custom_goal must be provided, but not both.

        Args:
            goal: Standard race goal from category goals list
            custom_goal: Custom race goal string (if not using a standard goal)
            invitational: Whether room is invite-only
            unlisted: Whether room is hidden from public lists
            info_user: Custom race information text
            start_delay: Countdown timer length in seconds
            time_limit: Maximum race duration in hours
            streaming_required: Whether streaming is required to join
            auto_start: Whether race starts automatically when ready
            allow_comments: Whether entrants can post comments
            hide_comments: Whether comments are hidden until race ends
            allow_prerace_chat: Whether chat is allowed before race starts
            allow_midrace_chat: Whether chat is allowed during race
            allow_non_entrant_chat: Whether non-entrants can chat
            chat_message_delay: Delay in seconds for chat messages
            team_race: Whether this is a team race

        Returns:
            SahaRaceHandler for the created race room, or None if creation failed
        """
        if not self.http or not self.access_token:
            logger.error("Bot not initialized - no HTTP session or access token")
            return None

        if not goal and not custom_goal:
            logger.error("Either goal or custom_goal must be provided")
            return None

        if goal and custom_goal:
            logger.error("Cannot specify both goal and custom_goal")
            return None

        try:
            # Build race creation payload
            payload = {
                "invitational": invitational,
                "unlisted": unlisted,
                "info_user": info_user,
                "start_delay": start_delay,
                "time_limit": time_limit,
                "streaming_required": streaming_required,
                "auto_start": auto_start,
                "allow_comments": allow_comments,
                "hide_comments": hide_comments,
                "allow_prerace_chat": allow_prerace_chat,
                "allow_midrace_chat": allow_midrace_chat,
                "allow_non_entrant_chat": allow_non_entrant_chat,
                "chat_message_delay": chat_message_delay,
                "team_race": team_race,
            }

            if goal:
                payload["goal"] = goal
            else:
                payload["custom_goal"] = custom_goal

            # Create race via HTTP API (following fork pattern)
            url = self.http_uri(f"/o/{self.category_slug}/startrace")
            headers = {"Authorization": f"Bearer {self.access_token}"}

            async with self.http.post(
                url, data=payload, headers=headers, ssl=self.ssl_context
            ) as resp:
                if resp.status not in (200, 201):
                    logger.error("Failed to create race room: HTTP %s", resp.status)
                    return None

                # Get the race location from response headers
                race_location = resp.headers.get("Location")
                if not race_location:
                    logger.error("No Location header in race creation response")
                    return None

            # Join the newly created race room and return handler
            race_name = race_location.lstrip("/")
            logger.info("Created race room: %s", race_name)

            # Use our join_race_room implementation to get a handler
            # This mirrors the fork's behavior: fetch race data, create handler, return it
            handler = await self.join_race_room(race_name, force=True)
            return handler

        except Exception as e:
            logger.error("Failed to create race room: %s", e, exc_info=True)
            return None

    async def invite_user_to_race(self, race_slug: str, racetime_user_id: str) -> bool:
        """
        Invite a user to a race room via HTTP API.

        This method uses the HTTP API to send an invitation, which doesn't require
        an active websocket connection like the handler's invite_user() method does.

        Args:
            race_slug: Full race slug (e.g., "alttpr/disco-stanley-3420")
            racetime_user_id: RaceTime.gg user ID to invite

        Returns:
            True if invite was sent successfully, False otherwise
        """
        if not self.http or not self.access_token:
            logger.error("Bot not initialized - no HTTP session or access token")
            return False

        try:
            url = self.http_uri(f"/{race_slug}/message")
            headers = {"Authorization": f"Bearer {self.access_token}"}
            payload = {
                "action": "invite",
                "user": racetime_user_id,
            }

            async with self.http.post(
                url, data=payload, headers=headers, ssl=self.ssl_context
            ) as resp:
                if resp.status == 204:
                    logger.info(
                        "Successfully invited user %s to race %s",
                        racetime_user_id,
                        race_slug,
                    )
                    return True
                else:
                    logger.error(
                        "Failed to invite user %s to race %s: HTTP %s",
                        racetime_user_id,
                        race_slug,
                        resp.status,
                    )
                    return False

        except Exception as e:
            logger.error(
                "Exception while inviting user %s to race %s: %s",
                racetime_user_id,
                race_slug,
                e,
                exc_info=True,
            )
            return False


# Map of category -> bot instance
_racetime_bots: dict[str, RacetimeBot] = {}
_racetime_bot_tasks: dict[str, asyncio.Task] = {}


async def rejoin_open_racetime_rooms(bot: RacetimeBot) -> int:
    """
    Rejoin all open RaceTime rooms for matches when bot restarts.

    Queries the database for all matches with active RaceTime rooms (not finished),
    and attempts to rejoin those rooms using match-aware handlers, syncing their status.

    Note: The join_race_room() method automatically detects if a room is associated
    with a match and uses the appropriate handler (match handler vs. base handler).

    Args:
        bot: The RacetimeBot instance to use for rejoining

    Returns:
        int: Number of rooms successfully rejoined
    """
    from models.racetime_room import RacetimeRoom
    from application.services.tournaments.tournament_service import TournamentService

    logger.info("Rejoining open RaceTime rooms for category: %s", bot.category_slug)

    try:
        # Find all RaceTime rooms for this category with unfinished matches
        rooms = (
            await RacetimeRoom.filter(
                category=bot.category_slug, match__finished_at__isnull=True
            )
            .select_related("match__tournament")
            .all()
        )

        logger.info(
            "Found %d open RaceTime rooms for category %s",
            len(rooms),
            bot.category_slug,
        )

        rejoined_count = 0
        service = TournamentService()

        for room in rooms:
            match = room.match
            if not match:
                logger.warning("Room %s has no match associated, skipping", room.slug)
                continue

            try:
                logger.info(
                    "Attempting to rejoin room %s for match %s", room.slug, match.id
                )

                # Try to join the race room
                # join_race_room will automatically detect the match association
                # and use a match-aware handler (combining MatchRaceMixin with
                # the bot's configured handler class)
                handler = await bot.join_race_room(room.slug, force=True)

                if handler:
                    rejoined_count += 1
                    logger.info("Successfully rejoined room %s with match handler", room.slug)

                    # Sync the room status to the match
                    try:
                        await service.sync_racetime_room_status(
                            user=None,  # System action
                            organization_id=match.tournament.organization_id,
                            match_id=match.id,
                        )
                        logger.info(
                            "Synced status for match %s from room %s",
                            match.id,
                            room.slug,
                        )
                    except Exception as sync_error:
                        logger.warning(
                            "Failed to sync status for match %s: %s",
                            match.id,
                            sync_error,
                        )
                else:
                    logger.warning("Failed to rejoin room %s", room.slug)

            except Exception as e:
                logger.error(
                    "Error rejoining room %s for match %s: %s", room.slug, match.id, e
                )
                continue

        logger.info(
            "Rejoined %d out of %d open RaceTime rooms for category %s",
            rejoined_count,
            len(rooms),
            bot.category_slug,
        )
        return rejoined_count

    except Exception as e:
        logger.error(
            "Failed to rejoin open RaceTime rooms for category %s: %s",
            bot.category_slug,
            e,
            exc_info=True,
        )
        return 0


async def start_racetime_bot(
    category: str,
    client_id: str,
    client_secret: str,
    bot_id: Optional[int] = None,
    handler_class_name: str = "SahaRaceHandler",
    max_retries: int = 5,
    initial_backoff: float = 5.0,
) -> RacetimeBot:
    """
    Start a racetime bot for a specific category with retry logic.

    The bot will automatically retry on connection failures with exponential backoff.
    Authentication failures will not be retried.

    Args:
        category: The racetime.gg category slug
        client_id: OAuth2 client ID for this category
        client_secret: OAuth2 client secret for this category
        bot_id: Optional database ID for status tracking
        handler_class_name: Name of the handler class to use (default: 'SahaRaceHandler')
        max_retries: Maximum number of retry attempts (default: 5)
        initial_backoff: Initial backoff delay in seconds (default: 5.0)

    Returns:
        RacetimeBot instance (bot runs in background task)

    Raises:
        Exception: If bot initialization or starting fails
    """
    logger.info(
        "Starting racetime bot for category: %s (bot_id=%s, handler=%s)",
        category,
        bot_id,
        handler_class_name,
    )

    try:
        # Create bot instance with category-specific credentials
        bot = RacetimeBot(
            category_slug=category,
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id,
            handler_class_name=handler_class_name,
        )

        # Store the bot instance
        _racetime_bots[category] = bot

        # Start the bot in a background task with error handling and retry logic
        async def run_with_status_tracking():
            """Run bot and track connection status with automatic retry on failure."""
            repository = RacetimeBotRepository()
            retry_count = 0
            backoff_delay = initial_backoff

            # Create HTTP session for the bot
            bot.http = aiohttp.ClientSession()

            try:
                while True:
                    try:
                        logger.info(
                            "Starting bot.run() for category: %s (attempt %d/%d)",
                            category,
                            retry_count + 1,
                            max_retries + 1,
                        )
                        logger.debug(
                            "Bot configuration - host: %s, secure: %s",
                            bot.racetime_host,
                            bot.racetime_secure,
                        )

                        # Update status to connected when starting
                        if bot_id:
                            await repository.record_connection_success(bot_id)

                        # Reset retry count on successful connection
                        retry_count = 0
                        backoff_delay = initial_backoff

                        # Rejoin any open RaceTime rooms from before bot restart
                        try:
                            rejoined_count = await rejoin_open_racetime_rooms(bot)
                            logger.info(
                                "Rejoined %d open RaceTime rooms for category %s",
                                rejoined_count,
                                category,
                            )
                        except Exception as rejoin_error:
                            logger.error(
                                "Failed to rejoin open RaceTime rooms for %s: %s",
                                category,
                                rejoin_error,
                                exc_info=True,
                            )

                        # Instead of calling bot.run() which tries to take over the event loop,
                        # we manually create the reauthorize task that run() would create.
                        # This allows the bot to work within our existing async context.
                        #
                        # NOTE: We do NOT create the refresh_races() task here. In the original
                        # racetime-bot library, refresh_races() polls for race rooms and automatically
                        # joins them based on should_handle(). We explicitly disable this behavior
                        # because SahaBot2 uses the task scheduler system to join race rooms at
                        # scheduled times instead of automatic polling.
                        #
                        # Race rooms are joined explicitly via:
                        # - Scheduled tasks (task scheduler system)
                        # - Manual commands (!startrace, etc.)
                        # - API calls (startrace, join_race_room)
                        reauth_task = asyncio.create_task(bot.reauthorize())

                        # Wait for the reauth task (runs forever until cancelled)
                        await reauth_task

                        logger.info(
                            "bot reauth task completed normally for category: %s",
                            category,
                        )
                        break  # Exit retry loop on normal completion

                    except asyncio.CancelledError:
                        # Bot was cancelled (stopped manually) - don't retry
                        logger.info(
                            "Racetime bot %s was cancelled (CancelledError caught)",
                            category,
                        )
                        if bot_id:
                            await repository.update_bot_status(
                                bot_id,
                                BotStatus.DISCONNECTED,
                                status_message="Bot stopped",
                            )
                        raise  # Re-raise to properly handle cancellation

                    except Exception as e:
                        # Always log the full exception with traceback
                        logger.error(
                            "Racetime bot error for %s (attempt %d/%d): %s",
                            category,
                            retry_count + 1,
                            max_retries + 1,
                            e,
                            exc_info=True,
                        )

                        # Check if this is an auth error (don't retry auth failures)
                        error_msg = str(e)
                        is_auth_error = (
                            "auth" in error_msg.lower()
                            or "unauthorized" in error_msg.lower()
                            or "401" in error_msg
                        )

                        # Update status based on error type
                        if bot_id:
                            if is_auth_error:
                                await repository.record_connection_failure(
                                    bot_id, error_msg, BotStatus.AUTH_FAILED
                                )
                            else:
                                await repository.record_connection_failure(
                                    bot_id, error_msg, BotStatus.CONNECTION_ERROR
                                )

                        # Don't retry on auth errors
                        if is_auth_error:
                            logger.error(
                                "Authentication failed for bot %s - not retrying",
                                category,
                            )
                            break

                        # Check if we should retry
                        retry_count += 1
                        if retry_count > max_retries:
                            logger.error(
                                "Max retries (%d) reached for bot %s - giving up",
                                max_retries,
                                category,
                            )
                            break

                        # Wait with exponential backoff before retrying
                        logger.info(
                            "Retrying bot %s in %.1f seconds (attempt %d/%d)...",
                            category,
                            backoff_delay,
                            retry_count + 1,
                            max_retries + 1,
                        )
                        await asyncio.sleep(backoff_delay)

                        # Exponential backoff (double the delay each time, max 5 minutes)
                        backoff_delay = min(backoff_delay * 2, 300.0)

            finally:
                # Clean up HTTP session
                if bot.http and not bot.http.closed:
                    await bot.http.close()
                    logger.info("Closed HTTP session for bot category: %s", category)

            # Cleanup happens in finally block below

        async def run_wrapper():
            """Wrapper to ensure cleanup happens."""
            try:
                await run_with_status_tracking()
            finally:
                # Clean up bot instance when task completes (for any reason)
                logger.info("Cleaning up racetime bot for category: %s", category)
                logger.debug("Removing from _racetime_bots: %s", category)
                _racetime_bots.pop(category, None)
                logger.debug("Removing from _racetime_bot_tasks: %s", category)
                _racetime_bot_tasks.pop(category, None)
                logger.info(
                    "Racetime bot task completed and cleaned up for category: %s",
                    category,
                )

        _racetime_bot_tasks[category] = asyncio.create_task(run_wrapper())

        logger.info("Racetime bot started successfully for category: %s", category)
        return bot

    except Exception as e:
        logger.error(
            "Failed to start racetime bot for %s: %s", category, e, exc_info=True
        )

        # Update status to connection error
        if bot_id:
            repository = RacetimeBotRepository()
            error_msg = str(e)
            if "auth" in error_msg.lower() or "unauthorized" in error_msg.lower():
                await repository.record_connection_failure(
                    bot_id, error_msg, BotStatus.AUTH_FAILED
                )
            else:
                await repository.record_connection_failure(
                    bot_id, error_msg, BotStatus.CONNECTION_ERROR
                )
        raise


async def stop_racetime_bot(category: str) -> None:
    """
    Stop the racetime bot for a specific category.

    Args:
        category: The racetime.gg category slug
    """
    logger.info("Attempting to stop racetime bot for category: %s", category)
    logger.debug("Current bots: %s", list(_racetime_bots.keys()))
    logger.debug("Current tasks: %s", list(_racetime_bot_tasks.keys()))

    # Check for the task (not the bot instance, which may already be cleaned up)
    task = _racetime_bot_tasks.get(category)
    if not task:
        logger.warning("No task found for racetime bot category %s", category)
        return

    if task.done():
        logger.info("Racetime bot task for category %s is already done", category)
        return

    logger.info("Cancelling racetime bot task for category: %s", category)

    try:
        # Cancel the bot task (cleanup happens in the task's finally block)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            # Expected when cancelling
            logger.info(
                "Racetime bot task cancelled successfully for category: %s", category
            )

        logger.info("Racetime bot stopped successfully for category: %s", category)

    except Exception as e:
        logger.error(
            "Error stopping racetime bot for category %s: %s",
            category,
            e,
            exc_info=True,
        )


async def stop_all_racetime_bots() -> None:
    """
    Stop all running racetime bots.

    Stops all bot instances gracefully and cleans up resources.
    """
    categories = list(_racetime_bots.keys())

    if not categories:
        logger.info("No racetime bots running")
        return

    logger.info("Stopping all racetime bots (%d instances)", len(categories))

    for category in categories:
        await stop_racetime_bot(category)


def get_racetime_bot_instance(category: str) -> Optional[RacetimeBot]:
    """
    Get the racetime bot instance for a specific category.

    Args:
        category: The racetime.gg category slug

    Returns:
        RacetimeBot instance or None if not running
    """
    return _racetime_bots.get(category)


def get_all_racetime_bot_instances() -> dict[str, RacetimeBot]:
    """
    Get all running racetime bot instances.

    Returns:
        Dictionary mapping category -> RacetimeBot instance
    """
    return _racetime_bots.copy()
