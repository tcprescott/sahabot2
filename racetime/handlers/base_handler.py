"""
Base race handler for SahaBot2.

This module provides the default race handler with common commands and event tracking.
"""

import logging
from typing import Optional

from racetime_bot import RaceHandler

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
from models import SYSTEM_USER_ID
from models import Match

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

    async def end(self):
        """
        Called when the handler is being tear down.

        Use this to perform cleanup.
        """
        logger.info("Race handler ended for race: %s", self.data.get("name"))

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

            # Get match_id and tournament_id if this is a match handler (has MatchRaceMixin)
            match_id = getattr(self, "match_id", None)
            tournament_id = None
            if match_id:
                # Query tournament_id from match
                try:
                    match = await Match.filter(id=match_id).select_related("tournament").first()
                    if match:
                        tournament_id = match.tournament_id
                except Exception as e:
                    logger.warning(
                        "Failed to get tournament_id for match %s: %s", match_id, e
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
                    match_id=match_id,
                    tournament_id=tournament_id,
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
