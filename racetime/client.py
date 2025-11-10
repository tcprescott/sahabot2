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
from racetime_bot import Bot, RaceHandler
from models import BotStatus, SYSTEM_USER_ID
from application.repositories.racetime_bot_repository import RacetimeBotRepository
from application.repositories.user_repository import UserRepository
from application.events import (
    EventBus,
    RacetimeRaceStatusChangedEvent,
    RacetimeEntrantStatusChangedEvent,
    RacetimeEntrantJoinedEvent,
    RacetimeEntrantLeftEvent,
    RacetimeEntrantInvitedEvent,
    RacetimeBotJoinedRaceEvent,
    RacetimeBotCreatedRaceEvent,
    RacetimeBotActionEvent,
)
from config import settings

# Configure logging
logger = logging.getLogger(__name__)


class SahaRaceHandler(RaceHandler):
    """
    Race handler for SahaBot2.

    Handles individual race rooms and commands.
    Emits events when race or entrant status changes.
    """

    def __init__(self, bot_instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store reference to bot instance
        self.bot = bot_instance
        # Track previous entrant statuses to detect changes
        self._previous_entrant_statuses: dict[str, str] = {}
        # Track all known entrants to detect joins/leaves
        self._previous_entrant_ids: set[str] = set()
        # Flag to track if this is the first data update (to avoid false join events on bot startup)
        self._first_data_update: bool = True
        # Flag to track if bot created this room (vs joining existing)
        self._bot_created_room: bool = False
        # Repository for user lookups
        self._user_repository = UserRepository()

    async def _get_user_id_from_racetime_id(
        self, racetime_user_id: str
    ) -> Optional[int]:
        """
        Look up application user ID from racetime user ID.

        Args:
            racetime_user_id: Racetime.gg user hash ID

        Returns:
            Optional[int]: Application user ID if found, None if racetime account not linked
        """
        try:
            user = await self._user_repository.get_by_racetime_id(racetime_user_id)
            return user.id if user else None
        except Exception as e:
            logger.warning(
                "Error looking up user by racetime_id %s: %s", racetime_user_id, e
            )
            return None

    def _extract_race_details(self) -> tuple[str, str, str]:
        """
        Extract race details from current race data.

        Returns:
            Tuple of (category, room_slug, room_name)
        """
        category = self.data.get("category", {}).get("slug", "") if self.data else ""
        room_slug = self.data.get("name", "") if self.data else ""
        room_name = room_slug.split("/")[-1] if "/" in room_slug else room_slug
        return category, room_slug, room_name

    async def _handle_join_request(
        self,
        racetime_user_id: str,
        racetime_user_name: str,
        room_slug: str,
    ) -> None:
        """
        Handle a join request for an invitational race.

        If the requesting player is listed as a player on the match associated with
        this race room, automatically accept their join request.

        Args:
            racetime_user_id: RaceTime.gg user ID making the request
            racetime_user_name: RaceTime.gg user name
            room_slug: Race room slug (e.g., "alttpr/cool-doge-1234")
        """
        try:
            # Use service to check if user is a match player (follows architectural layers)
            from application.services.racetime.racetime_room_service import (
                RacetimeRoomService,
            )

            service = RacetimeRoomService()
            is_match_player, match_id = await service.is_player_on_match(
                room_slug=room_slug, racetime_user_id=racetime_user_id
            )

            if match_id is None:
                logger.debug(
                    "No match found for room %s, not auto-accepting join request from %s",
                    room_slug,
                    racetime_user_name,
                )
                return

            if is_match_player:
                # Accept the join request
                await self.accept_request(racetime_user_id)
                logger.info(
                    "Auto-accepted join request from %s (%s) for match %s in room %s",
                    racetime_user_name,
                    racetime_user_id,
                    match_id,
                    room_slug,
                )
            else:
                logger.debug(
                    "User %s (%s) is not a player on match %s, not auto-accepting join request",
                    racetime_user_name,
                    racetime_user_id,
                    match_id,
                )

        except Exception as e:
            logger.error(
                "Error handling join request from %s in room %s: %s",
                racetime_user_name,
                room_slug,
                e,
                exc_info=True,
            )

    async def ex_test(self, _args, _message):
        """
        Test command for the racetime bot.

        Usage: !test
        """
        await self.send_message("Racetime bot test command received!")

    async def ex_help(self, _args, _message):
        """
        Show available commands.

        Usage: !help
        """
        await self.send_message(
            "Available commands: "
            "!help (show this message), "
            "!status (race status), "
            "!race (race info), "
            "!time (your finish time), "
            "!entrants (list entrants by status)"
        )

    async def ex_status(self, _args, _message):
        """
        Show current race status and entrant count.

        Usage: !status
        """
        if not self.data:
            await self.send_message("Race data not available yet.")
            return

        status_value = self.data.get("status", {}).get("value", "unknown")
        entrants = self.data.get("entrants", [])
        entrant_count = len(entrants)

        # Map status values to human-readable text
        status_text_map = {
            "open": "Open",
            "invitational": "Invitational",
            "pending": "Pending",
            "in_progress": "In Progress",
            "finished": "Finished",
            "cancelled": "Cancelled",
        }
        status_text = status_text_map.get(
            status_value, status_value.replace("_", " ").title()
        )

        await self.send_message(
            f"Race Status: {status_text} | Entrants: {entrant_count}"
        )

    async def ex_race(self, _args, _message):
        """
        Show race goal and info.

        Usage: !race
        """
        if not self.data:
            await self.send_message("Race data not available yet.")
            return

        goal_name = self.data.get("goal", {}).get("name", "No goal set")
        info_text = self.data.get("info", "")

        if info_text:
            await self.send_message(f"Goal: {goal_name} | Info: {info_text}")
        else:
            await self.send_message(f"Goal: {goal_name}")

    async def ex_time(self, _args, message):
        """
        Show your finish time or race time if still running.

        Usage: !time
        """
        if not self.data:
            await self.send_message("Race data not available yet.")
            return

        # Extract racetime user ID
        user_data = message.get("user", {})
        racetime_user_id = user_data.get("id", "")

        if not racetime_user_id:
            await self.send_message("Unable to identify user.")
            return

        entrants = self.data.get("entrants", [])

        # Find the user in entrants
        user_entrant = None
        for entrant in entrants:
            if entrant.get("user", {}).get("id") == racetime_user_id:
                user_entrant = entrant
                break

        if not user_entrant:
            await self.send_message("You are not in this race.")
            return

        # Check if user has finished
        finish_time = user_entrant.get("finish_time")
        if finish_time:
            # Format finish time (it's a timedelta in ISO format)
            await self.send_message(f"Your finish time: {finish_time}")
            return

        # User hasn't finished yet - show race time
        status_value = self.data.get("status", {}).get("value", "")
        if status_value == "in_progress":
            # Race is in progress
            started_at = self.data.get("started_at")
            if started_at:
                await self.send_message(
                    "Race is in progress. You haven't finished yet."
                )
                return

        await self.send_message("Race hasn't started yet.")

    async def ex_entrants(self, _args, _message):
        """
        List all entrants grouped by status.

        Usage: !entrants
        """
        if not self.data:
            await self.send_message("Race data not available yet.")
            return

        entrants = self.data.get("entrants", [])

        if not entrants:
            await self.send_message("No entrants in this race.")
            return

        # Group by status
        ready = []
        not_ready = []
        finished = []
        dnf = []

        for entrant in entrants:
            username = entrant.get("user", {}).get("name", "Unknown")
            status_value = entrant.get("status", {}).get("value", "")

            if status_value == "ready":
                ready.append(username)
            elif status_value == "not_ready":
                not_ready.append(username)
            elif status_value == "done":
                finished.append(username)
            elif status_value == "dnf":
                dnf.append(username)

        # Build response
        parts = []
        if ready:
            parts.append(f"Ready ({len(ready)}): {', '.join(ready)}")
        if not_ready:
            parts.append(f"Not Ready ({len(not_ready)}): {', '.join(not_ready)}")
        if finished:
            parts.append(f"Finished ({len(finished)}): {', '.join(finished)}")
        if dnf:
            parts.append(f"DNF ({len(dnf)}): {', '.join(dnf)}")

        if not parts:
            await self.send_message(f"Total entrants: {len(entrants)}")
            return

        await self.send_message(" | ".join(parts))

    async def begin(self):
        """
        Called when the handler is first created.

        Use this to perform initial setup for the race.
        Emits RacetimeBotJoinedRaceEvent or RacetimeBotCreatedRaceEvent.
        """
        race_name = self.data.get("name", "unknown")
        logger.info("Race handler started for race: %s", race_name)

        # Get bot ID from the bot instance (if available)
        if hasattr(self.bot, "bot_id"):
            self._bot_id = self.bot.bot_id

        # Extract race details
        category = self.data.get("category", {}).get("slug", "")
        room_slug = race_name
        room_name = room_slug.split("/")[-1] if "/" in room_slug else room_slug
        race_status = self.data.get("status", {}).get("value", "unknown")
        entrant_count = len(self.data.get("entrants", []))

        # Emit appropriate event based on whether bot created or joined the room
        if self._bot_created_room:
            logger.info("Bot created race room: %s", room_slug)
            await EventBus.emit(
                RacetimeBotCreatedRaceEvent(
                    user_id=SYSTEM_USER_ID,  # System automation action
                    entity_id=room_slug,
                    category=category,
                    room_slug=room_slug,
                    room_name=room_name,
                    goal=self.data.get("goal", {}).get("name", ""),
                    invitational=not self.data.get("unlisted", False),
                    bot_action="create",
                )
            )
        else:
            logger.info("Bot joined existing race room: %s", room_slug)
            await EventBus.emit(
                RacetimeBotJoinedRaceEvent(
                    user_id=SYSTEM_USER_ID,  # System automation action
                    entity_id=room_slug,
                    category=category,
                    room_slug=room_slug,
                    room_name=room_name,
                    race_status=race_status,
                    entrant_count=entrant_count,
                    bot_action="join",
                )
            )

    # Initial setup hook for race handler

    async def end(self):
        """
        Called when the handler is being tear down.

        Use this to perform cleanup.
        """
        logger.info("Race handler ended for race: %s", self.data.get("name"))

    # Cleanup hook for race handler

    async def race_data(self, data):
        """
        Called whenever race data is updated.

        Tracks race status changes, entrant status changes, joins, and leaves,
        emitting appropriate events for each.

        Args:
            data: Updated race data from racetime.gg
        """
        new_race_data = data.get("race", {})
        old_race_data = self.data if self.data else {}

        # Extract identifiers
        category = new_race_data.get("category", {}).get("slug", "")
        room_slug = new_race_data.get("name", "")
        room_name = room_slug.split("/")[-1] if "/" in room_slug else room_slug
        new_status = new_race_data.get("status", {}).get("value")

        # Check for race status changes
        old_status = (
            old_race_data.get("status", {}).get("value") if old_race_data else None
        )

        if old_status and new_status and old_status != new_status:
            logger.info(
                "Race %s status changed: %s -> %s", room_slug, old_status, new_status
            )

            # Emit race status changed event
            await EventBus.emit(
                RacetimeRaceStatusChangedEvent(
                    user_id=SYSTEM_USER_ID,  # System automation (race status changes are automated)
                    entity_id=room_slug,
                    category=category,
                    room_slug=room_slug,
                    room_name=room_name,
                    old_status=old_status,
                    new_status=new_status,
                    entrant_count=len(new_race_data.get("entrants", [])),
                    started_at=new_race_data.get("started_at"),
                    ended_at=new_race_data.get("ended_at"),
                )
            )

        # Process entrants
        new_entrants = new_race_data.get("entrants", [])
        current_entrant_statuses = {}
        current_entrant_ids = set()
        current_entrant_names = {}

        for entrant in new_entrants:
            user_id = entrant.get("user", {}).get("id", "")
            user_name = entrant.get("user", {}).get("name", "")
            entrant_status = entrant.get("status", {}).get("value", "")

            current_entrant_ids.add(user_id)
            current_entrant_statuses[user_id] = entrant_status
            current_entrant_names[user_id] = user_name

        # Detect joins (new entrants) - skip on first data update to avoid false positives
        if not self._first_data_update:
            new_entrants_ids = current_entrant_ids - self._previous_entrant_ids
            for user_id in new_entrants_ids:
                user_name = current_entrant_names.get(user_id, "")
                initial_status = current_entrant_statuses.get(user_id, "")

                # Look up application user ID
                app_user_id = await self._get_user_id_from_racetime_id(user_id)

                logger.info(
                    "Entrant %s (%s) joined race %s with status: %s",
                    user_name,
                    user_id,
                    room_slug,
                    initial_status,
                )

                await EventBus.emit(
                    RacetimeEntrantJoinedEvent(
                        user_id=app_user_id,  # Application user ID (None if not linked)
                        entity_id=f"{room_slug}/{user_id}",
                        category=category,
                        room_slug=room_slug,
                        room_name=room_name,
                        racetime_user_id=user_id,
                        racetime_user_name=user_name,
                        initial_status=initial_status,
                        race_status=new_status,
                    )
                )

        # Detect leaves (removed entrants) - skip on first data update
        if not self._first_data_update:
            left_entrant_ids = self._previous_entrant_ids - current_entrant_ids
            for user_id in left_entrant_ids:
                # Get name from previous data (no longer in current data)
                user_name = ""
                last_status = self._previous_entrant_statuses.get(user_id, "")

                # Try to find name from old data
                if old_race_data:
                    for old_entrant in old_race_data.get("entrants", []):
                        if old_entrant.get("user", {}).get("id") == user_id:
                            user_name = old_entrant.get("user", {}).get("name", "")
                            break

                # Look up application user ID
                app_user_id = await self._get_user_id_from_racetime_id(user_id)

                logger.info(
                    "Entrant %s (%s) left race %s (was %s)",
                    user_name,
                    user_id,
                    room_slug,
                    last_status,
                )

                await EventBus.emit(
                    RacetimeEntrantLeftEvent(
                        user_id=app_user_id,  # Application user ID (None if not linked)
                        entity_id=f"{room_slug}/{user_id}",
                        category=category,
                        room_slug=room_slug,
                        room_name=room_name,
                        racetime_user_id=user_id,
                        racetime_user_name=user_name,
                        last_status=last_status,
                        race_status=new_status,
                    )
                )

        # Detect status changes (for existing entrants)
        for user_id, entrant_status in current_entrant_statuses.items():
            old_entrant_status = self._previous_entrant_statuses.get(user_id)

            if old_entrant_status and old_entrant_status != entrant_status:
                user_name = current_entrant_names.get(user_id, "")

                # Find full entrant data for finish_time and place
                finish_time = None
                place = None
                for entrant in new_entrants:
                    if entrant.get("user", {}).get("id") == user_id:
                        finish_time = entrant.get("finish_time")
                        place = entrant.get("place")
                        break

                # Look up application user ID
                app_user_id = await self._get_user_id_from_racetime_id(user_id)

                logger.info(
                    "Entrant %s (%s) status changed in race %s: %s -> %s",
                    user_name,
                    user_id,
                    room_slug,
                    old_entrant_status,
                    entrant_status,
                )

                # Emit entrant status changed event
                await EventBus.emit(
                    RacetimeEntrantStatusChangedEvent(
                        user_id=app_user_id,  # Application user ID (None if not linked)
                        entity_id=f"{room_slug}/{user_id}",
                        category=category,
                        room_slug=room_slug,
                        room_name=room_name,
                        racetime_user_id=user_id,
                        racetime_user_name=user_name,
                        old_status=old_entrant_status,
                        new_status=entrant_status,
                        finish_time=finish_time,
                        place=place,
                        race_status=new_status,
                    )
                )

                # Auto-accept join requests for match players
                if entrant_status == "requested":
                    await self._handle_join_request(user_id, user_name, room_slug)

        # Update tracked state
        self._previous_entrant_statuses = current_entrant_statuses
        self._previous_entrant_ids = current_entrant_ids
        self._first_data_update = False

        # Call parent implementation to update self.data
        await super().race_data(data)

    async def invite_user(self, user_id: str):
        """
        Invite a user to the race.

        Overrides the base RaceHandler.invite_user() to emit an event
        when the bot invites a player.

        Args:
            user_id: The racetime.gg user ID to invite
        """
        # Extract race details
        category, room_slug, room_name = self._extract_race_details()
        race_status = self.data.get("status", {}).get("value", "") if self.data else ""

        # Look up application user ID
        app_user_id = await self._get_user_id_from_racetime_id(user_id)

        # Emit invite event
        logger.info("Bot inviting user %s to race %s", user_id, room_slug)
        await EventBus.emit(
            RacetimeEntrantInvitedEvent(
                user_id=app_user_id,  # Application user ID (None if not linked)
                entity_id=f"{room_slug}/{user_id}",
                category=category,
                room_slug=room_slug,
                room_name=room_name,
                racetime_user_id=user_id,
                race_status=race_status,
            )
        )

        # Call parent implementation to send the actual invite
        await super().invite_user(user_id)

    async def force_start(self):
        """
        Force start the race.

        Overrides the base RaceHandler.force_start() to emit an event
        when the bot force-starts a race.
        """
        # Extract race details
        category, room_slug, room_name = self._extract_race_details()

        # Emit action event
        logger.info("Bot force-starting race %s", room_slug)
        await EventBus.emit(
            RacetimeBotActionEvent(
                user_id=SYSTEM_USER_ID,
                entity_id=room_slug,
                category=category,
                room_slug=room_slug,
                room_name=room_name,
                action_type="force_start",
            )
        )

        # Call parent implementation
        await super().force_start()

    async def force_unready(self, user_id: str):
        """
        Force unready an entrant.

        Overrides the base RaceHandler.force_unready() to emit an event
        when the bot force-unreadies an entrant.

        Args:
            user_id: The racetime.gg user ID to unready
        """
        # Extract race details
        category, room_slug, room_name = self._extract_race_details()

        # Look up application user ID
        app_user_id = await self._get_user_id_from_racetime_id(user_id)

        # Emit action event
        logger.info("Bot force-unreadying user %s in race %s", user_id, room_slug)
        await EventBus.emit(
            RacetimeBotActionEvent(
                user_id=app_user_id,  # Application user ID (None if not linked)
                entity_id=f"{room_slug}/{user_id}",
                category=category,
                room_slug=room_slug,
                room_name=room_name,
                action_type="force_unready",
                target_user_id=user_id,
            )
        )

        # Call parent implementation
        await super().force_unready(user_id)

    async def remove_entrant(self, user_id: str):
        """
        Remove an entrant from the race.

        Overrides the base RaceHandler.remove_entrant() to emit an event
        when the bot removes an entrant.

        Args:
            user_id: The racetime.gg user ID to remove
        """
        # Extract race details
        category, room_slug, room_name = self._extract_race_details()

        # Look up application user ID
        app_user_id = await self._get_user_id_from_racetime_id(user_id)

        # Emit action event
        logger.info("Bot removing entrant %s from race %s", user_id, room_slug)
        await EventBus.emit(
            RacetimeBotActionEvent(
                user_id=app_user_id,  # Application user ID (None if not linked)
                entity_id=f"{room_slug}/{user_id}",
                category=category,
                room_slug=room_slug,
                room_name=room_name,
                action_type="remove_entrant",
                target_user_id=user_id,
            )
        )

        # Call parent implementation
        await super().remove_entrant(user_id)

    async def cancel_race(self):
        """
        Cancel the race.

        Overrides the base RaceHandler.cancel_race() to emit an event
        when the bot cancels a race.
        """
        # Extract race details
        category, room_slug, room_name = self._extract_race_details()

        # Emit action event
        logger.info("Bot cancelling race %s", room_slug)
        await EventBus.emit(
            RacetimeBotActionEvent(
                user_id=SYSTEM_USER_ID,
                entity_id=room_slug,
                category=category,
                room_slug=room_slug,
                room_name=room_name,
                action_type="cancel_race",
            )
        )

        # Call parent implementation
        await super().cancel_race()

    async def add_monitor(self, user_id: str):
        """
        Add a user as a race monitor.

        Overrides the base RaceHandler.add_monitor() to emit an event
        when the bot adds a monitor.

        Args:
            user_id: The racetime.gg user ID to add as monitor
        """
        # Extract race details
        category, room_slug, room_name = self._extract_race_details()

        # Look up application user ID
        app_user_id = await self._get_user_id_from_racetime_id(user_id)

        # Emit action event
        logger.info("Bot adding monitor %s to race %s", user_id, room_slug)
        await EventBus.emit(
            RacetimeBotActionEvent(
                user_id=app_user_id,  # Application user ID (None if not linked)
                entity_id=f"{room_slug}/{user_id}",
                category=category,
                room_slug=room_slug,
                room_name=room_name,
                action_type="add_monitor",
                target_user_id=user_id,
            )
        )

        # Call parent implementation
        await super().add_monitor(user_id)

    async def remove_monitor(self, user_id: str):
        """
        Remove a user as a race monitor.

        Overrides the base RaceHandler.remove_monitor() to emit an event
        when the bot removes a monitor.

        Args:
            user_id: The racetime.gg user ID to remove as monitor
        """
        # Extract race details
        category, room_slug, room_name = self._extract_race_details()

        # Look up application user ID
        app_user_id = await self._get_user_id_from_racetime_id(user_id)

        # Emit action event
        logger.info("Bot removing monitor %s from race %s", user_id, room_slug)
        await EventBus.emit(
            RacetimeBotActionEvent(
                user_id=app_user_id,  # Application user ID (None if not linked)
                entity_id=f"{room_slug}/{user_id}",
                category=category,
                room_slug=room_slug,
                room_name=room_name,
                action_type="remove_monitor",
                target_user_id=user_id,
            )
        )

        # Call parent implementation
        await super().remove_monitor(user_id)

    async def pin_message(self, message_id: str):
        """
        Pin a chat message.

        Overrides the base RaceHandler.pin_message() to emit an event
        when the bot pins a message.

        Args:
            message_id: The message ID (hash) to pin
        """
        # Extract race details
        category, room_slug, room_name = self._extract_race_details()

        # Emit action event
        logger.info("Bot pinning message %s in race %s", message_id, room_slug)
        await EventBus.emit(
            RacetimeBotActionEvent(
                user_id=SYSTEM_USER_ID,
                entity_id=f"{room_slug}/message/{message_id}",
                category=category,
                room_slug=room_slug,
                room_name=room_name,
                action_type="pin_message",
                details=message_id,
            )
        )

        # Call parent implementation
        await super().pin_message(message_id)

    async def unpin_message(self, message_id: str):
        """
        Unpin a chat message.

        Overrides the base RaceHandler.unpin_message() to emit an event
        when the bot unpins a message.

        Args:
            message_id: The message ID (hash) to unpin
        """
        # Extract race details
        category, room_slug, room_name = self._extract_race_details()

        # Emit action event
        logger.info("Bot unpinning message %s in race %s", message_id, room_slug)
        await EventBus.emit(
            RacetimeBotActionEvent(
                user_id=SYSTEM_USER_ID,
                entity_id=f"{room_slug}/message/{message_id}",
                category=category,
                room_slug=room_slug,
                room_name=room_name,
                action_type="unpin_message",
                details=message_id,
            )
        )

        # Call parent implementation
        await super().unpin_message(message_id)

    async def set_raceinfo(
        self, info: str, overwrite: bool = False, prefix: bool = True
    ):
        """
        Set the race info_user field.

        Overrides the base RaceHandler.set_raceinfo() to emit an event
        when the bot sets race info.

        Args:
            info: The info text to set
            overwrite: If True, replaces existing info. If False, appends.
            prefix: If True, prefixes the info with bot name
        """
        # Extract race details
        category, room_slug, room_name = self._extract_race_details()

        # Emit action event
        logger.info(
            "Bot setting race info for %s (overwrite=%s, prefix=%s)",
            room_slug,
            overwrite,
            prefix,
        )
        await EventBus.emit(
            RacetimeBotActionEvent(
                user_id=SYSTEM_USER_ID,
                entity_id=room_slug,
                category=category,
                room_slug=room_slug,
                room_name=room_name,
                action_type="set_raceinfo",
                details=f"overwrite={overwrite}, prefix={prefix}",
            )
        )

        # Call parent implementation
        await super().set_raceinfo(info, overwrite=overwrite, prefix=prefix)

    async def set_bot_raceinfo(self, info: str):
        """
        Set the race info_bot field.

        Overrides the base RaceHandler.set_bot_raceinfo() to emit an event
        when the bot sets race bot info.

        Args:
            info: The bot info text to set
        """
        # Extract race details
        category, room_slug, room_name = self._extract_race_details()

        # Emit action event
        logger.info("Bot setting bot race info for %s", room_slug)
        await EventBus.emit(
            RacetimeBotActionEvent(
                user_id=SYSTEM_USER_ID,
                entity_id=room_slug,
                category=category,
                room_slug=room_slug,
                room_name=room_name,
                action_type="set_bot_raceinfo",
            )
        )

        # Call parent implementation
        await super().set_bot_raceinfo(info)

    async def set_open(self):
        """
        Set the race room to open state.

        Overrides the base RaceHandler.set_open() to emit an event
        when the bot changes room to open.
        """
        # Extract race details
        category, room_slug, room_name = self._extract_race_details()

        # Emit action event
        logger.info("Bot setting race %s to open", room_slug)
        await EventBus.emit(
            RacetimeBotActionEvent(
                user_id=SYSTEM_USER_ID,
                entity_id=room_slug,
                category=category,
                room_slug=room_slug,
                room_name=room_name,
                action_type="set_open",
            )
        )

        # Call parent implementation
        await super().set_open()

    async def set_invitational(self):
        """
        Set the race room to invitational state.

        Overrides the base RaceHandler.set_invitational() to emit an event
        when the bot changes room to invitational.
        """
        # Extract race details
        category, room_slug, room_name = self._extract_race_details()

        # Emit action event
        logger.info("Bot setting race %s to invitational", room_slug)
        await EventBus.emit(
            RacetimeBotActionEvent(
                user_id=SYSTEM_USER_ID,
                entity_id=room_slug,
                category=category,
                room_slug=room_slug,
                room_name=room_name,
                action_type="set_invitational",
            )
        )

        # Call parent implementation
        await super().set_invitational()


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
        - MatchRaceHandler (tournament match handler)
        - AsyncLiveRaceHandler (async tournament live race handler)

        Returns:
            Handler class to use for race rooms
        """
        # Map handler names to classes
        from racetime.alttpr_handler import ALTTPRRaceHandler
        from racetime.sm_race_handler import SMRaceHandler
        from racetime.smz3_race_handler import SMZ3RaceHandler
        from racetime.match_race_handler import MatchRaceHandler
        from racetime.live_race_handler import AsyncLiveRaceHandler

        handler_map = {
            "SahaRaceHandler": SahaRaceHandler,
            "ALTTPRRaceHandler": ALTTPRRaceHandler,
            "SMRaceHandler": SMRaceHandler,
            "SMZ3RaceHandler": SMZ3RaceHandler,
            "MatchRaceHandler": MatchRaceHandler,
            "AsyncLiveRaceHandler": AsyncLiveRaceHandler,
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

    async def join_race_room(
        self, race_name: str, force: bool = False
    ) -> Optional[SahaRaceHandler]:
        """
        Join a race room and create a handler for it.

        This is a simplified implementation of the fork's join_race_room() method.
        It fetches race data, creates a handler, and starts the handler task.

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

        # Create handler for the race
        try:
            handler = self.create_handler(race_data)

            # If force=True, this means the bot created the room (via startrace)
            # Set flag so begin() knows to emit RacetimeBotCreatedRaceEvent
            if force:
                handler._bot_created_room = True

            logger.info("Created handler for race %s", race_name)
            return handler

        except Exception as e:
            logger.error(
                "Failed to create handler for race %s: %s", race_name, e, exc_info=True
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


# Map of category -> bot instance
_racetime_bots: dict[str, RacetimeBot] = {}
_racetime_bot_tasks: dict[str, asyncio.Task] = {}


async def rejoin_open_racetime_rooms(bot: RacetimeBot) -> int:
    """
    Rejoin all open RaceTime rooms for matches when bot restarts.

    Queries the database for all matches with active RaceTime rooms (not finished),
    and attempts to rejoin those rooms, syncing their status.

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
                handler = await bot.join_race_room(room.slug, force=True)

                if handler:
                    rejoined_count += 1
                    logger.info("Successfully rejoined room %s", room.slug)

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
