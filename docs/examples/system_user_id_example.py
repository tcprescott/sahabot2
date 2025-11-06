"""
Example: Using SYSTEM_USER_ID for authorization in event handlers.

This example demonstrates how to handle different user_id types when
processing RaceTime events with proper authorization checks.
"""

from application.events import EventBus, RacetimeEntrantStatusChangedEvent
from application.services.tournaments.tournament_service import TournamentService
from models import SYSTEM_USER_ID, Permission, is_system_user_id, is_authenticated_user_id, get_user_id_description
import logging

logger = logging.getLogger(__name__)


@EventBus.on(RacetimeEntrantStatusChangedEvent)
async def handle_race_finish(event: RacetimeEntrantStatusChangedEvent):
    """
    Handle race finish events with proper user identification and authorization.
    
    Demonstrates the three user_id states:
    1. Authenticated user (positive ID) - perform authorization checks
    2. System action (SYSTEM_USER_ID) - shouldn't happen for entrant events
    3. Unknown user (None) - log and skip
    """
    if event.new_status != 'done':
        return  # Only process finish events
    
    # Log who triggered the event
    logger.info(
        "Race finish event: %s finished %s (actor: %s)",
        event.racetime_user_name,
        event.room_slug,
        get_user_id_description(event.user_id)
    )
    
    # Initialize services
    tournament_service = TournamentService()
    
    # Handle based on user_id type
    if is_authenticated_user_id(event.user_id):
        # Real authenticated user - perform full authorization
        logger.info("Processing finish for authenticated user %s", event.user_id)
        
        # Check if this is part of a tournament match
        if event.match_id:
            # Verify user has permission to update this match
            # (In practice, finishing a race you're in is always allowed,
            #  but this demonstrates the authorization pattern)
            try:
                await tournament_service.record_race_result(
                    user_id=event.user_id,
                    match_id=event.match_id,
                    racetime_user_id=event.racetime_user_id,
                    finish_time=event.finish_time,
                    place=event.place,
                )
                logger.info(
                    "Recorded result for user %s in match %s (place %s, time %s)",
                    event.user_id,
                    event.match_id,
                    event.place,
                    event.finish_time
                )
            except Exception as e:
                logger.error(
                    "Failed to record result for user %s: %s",
                    event.user_id,
                    e
                )
        else:
            # Not a tournament match - just casual race
            logger.info("Casual race finish by user %s", event.user_id)
    
    elif is_system_user_id(event.user_id):
        # System action - this shouldn't happen for entrant status changes
        # but we handle it gracefully
        logger.warning(
            "Unexpected system action for entrant status change: %s",
            event.racetime_user_id
        )
        # System events shouldn't trigger user-specific updates
    
    else:  # user_id is None
        # Unknown/unauthenticated user - racetime account not linked
        logger.warning(
            "Race finish by unlinked racetime user %s (name: %s)",
            event.racetime_user_id,
            event.racetime_user_name
        )
        
        if event.match_id:
            # This is problematic - they finished a tournament match but
            # we can't update their record because they haven't linked
            logger.error(
                "Cannot record match %s result - user %s has not linked racetime account",
                event.match_id,
                event.racetime_user_id
            )
            # Optionally: Send notification to race room encouraging linking
            # await send_racetime_message(
            #     event.room_slug,
            #     f"{event.racetime_user_name}: Please link your racetime account "
            #     f"at https://sahabot.example.com/settings/racetime to record tournament results"
            # )


@EventBus.on(RacetimeEntrantStatusChangedEvent)
async def send_discord_notification(event: RacetimeEntrantStatusChangedEvent):
    """
    Send Discord notifications for race events.
    
    Only sends notifications for authenticated users with linked accounts.
    """
    if event.new_status != 'done':
        return
    
    # Only send notifications for authenticated users
    if not is_authenticated_user_id(event.user_id):
        logger.info(
            "Skipping Discord notification for %s (user_id: %s)",
            event.racetime_user_name,
            get_user_id_description(event.user_id)
        )
        return
    
    # Send Discord DM to user
    logger.info(
        "Sending Discord notification to user %s for race finish",
        event.user_id
    )
    # Implementation would go here...
    # await discord_service.send_dm(
    #     event.user_id,
    #     f"You finished in place {event.place} with time {event.finish_time}!"
    # )


# Example: Bot command handler
async def handle_racetime_bot_command(racetime_user_id: str, command: str, race_room: str):
    """
    Handle a bot command from racetime chat.
    
    Demonstrates authorization for commands triggered via racetime.
    """
    from application.repositories.user_repository import UserRepository
    
    # Look up application user from racetime ID
    user_repo = UserRepository()
    user = await user_repo.get_by_racetime_id(racetime_user_id)
    user_id = user.id if user else None
    
    logger.info(
        "Bot command '%s' from %s (user_id: %s)",
        command,
        racetime_user_id,
        get_user_id_description(user_id)
    )
    
    # Check authentication
    if not is_authenticated_user_id(user_id):
        return (
            "Please link your racetime account at https://sahabot.example.com/settings/racetime "
            "to use bot commands"
        )
    
    # Example: Privileged command that requires organization admin
    if command.startswith("!forceforfeit"):
        # Get organization context (would come from race room metadata)
        org_id = 1  # Example
        
        # Note: In practice, you would fetch the user and check permissions
        # using AuthorizationServiceV2 or UIAuthorizationHelper
        # For this example, we'll just show the pattern:
        
        # Get user object
        from application.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        user = await user_repo.get_by_id(user_id)
        
        if user and user.has_permission(Permission.ADMIN):
            # User has permission - execute command
            logger.info("User %s executing privileged command", user_id)
            # Implementation...
            return "Forfeit recorded"
        else:
            logger.warning(
                "User %s attempted privileged command without permission",
                user_id
            )
            return "You don't have permission to use this command"
    
    # Example: Non-privileged command
    if command.startswith("!mystats"):
        # Anyone with a linked account can view their stats
        # Implementation...
        return f"Stats for user {user_id}"
    
    return "Unknown command"
