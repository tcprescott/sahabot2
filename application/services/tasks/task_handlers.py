"""
Task handlers for scheduled tasks.

This module contains handler functions for different task types.
Each handler is registered with the TaskSchedulerService and executed
when a task of that type is due to run.
"""

import logging
import discord
import httpx
from datetime import datetime, timedelta, timezone
from models.scheduled_task import ScheduledTask, TaskType
from models.async_tournament import AsyncQualifier, AsyncQualifierRace
from models import SYSTEM_USER_ID
from application.services.tasks.task_scheduler_service import TaskSchedulerService
from application.services.tournaments.async_qualifier_service import (
    AsyncQualifierService,
)
from application.services.tournaments.async_live_race_service import (
    AsyncLiveRaceService,
)
from discordbot.client import get_bot_instance
from racetime.client import get_all_racetime_bot_instances

logger = logging.getLogger(__name__)


async def handle_example_log(task: ScheduledTask) -> None:
    """
    Example task handler that writes a log message.

    This is a simple example task demonstrating how to create a scheduled task handler.
    It logs basic task information and a custom message from the task configuration.

    Expected task_config:
    {
        "message": "Custom message to log"  # optional
    }

    Args:
        task: ScheduledTask to execute
    """
    logger.info("Example task executed! Task ID: %s, Name: %s", task.id, task.name)

    if task.task_config:
        message = task.task_config.get("message", "No custom message")
        logger.info("Custom message: %s", message)
    else:
        logger.info("No custom message configured")


async def handle_racetime_open_room(task: ScheduledTask) -> None:
    """
    Handler for opening a racetime.gg race room.

    This task handler opens a race room on racetime.gg using the configured
    bot for the specified category.

    Expected task_config:
    {
        "category": "alttpr",  # racetime category
        "goal": "Beat the game",  # race goal
        "info": "Additional race info",  # optional
        "unlisted": false,  # whether race is unlisted
        "invitational": false,  # whether race is invitational
        "team_race": false,  # whether this is a team race
    }

    Args:
        task: ScheduledTask to execute
    """
    logger.info("Opening racetime room for task: %s", task.name)

    # Extract configuration
    config = task.task_config or {}
    category = config.get("category")
    goal = config.get("goal", "Beat the game")
    info = config.get("info", "")
    unlisted = config.get("unlisted", False)
    invitational = config.get("invitational", False)
    team_race = config.get("team_race", False)

    if not category:
        raise ValueError("category is required in task_config")

    # TODO: Implement actual racetime room opening logic
    # This will require integration with the racetime bot client
    # For now, we just log the intent
    logger.info(
        "Would open racetime room: category=%s, goal=%s, info=%s, unlisted=%s, invitational=%s, team_race=%s",
        category,
        goal,
        info,
        unlisted,
        invitational,
        team_race,
    )

    # Future implementation will use the racetime bot to create a room:
    # from racetime.client import get_racetime_bot_instance
    # bot = get_racetime_bot_instance(category)
    # if not bot:
    #     raise RuntimeError(f"Racetime bot for category {category} is not running")
    # await bot.create_race(goal=goal, info=info, unlisted=unlisted, ...)


async def handle_custom_task(task: ScheduledTask) -> None:
    """
    Handler for custom tasks.

    This is a placeholder handler for custom task types.
    Custom tasks can be used for organization-specific automation.

    Args:
        task: ScheduledTask to execute
    """
    logger.info("Executing custom task: %s", task.name)
    logger.info("Task config: %s", task.task_config)

    # Custom task logic would go here
    # This can be extended based on specific requirements


async def handle_cleanup_tournament_usage(task: ScheduledTask) -> None:
    """
    Handler for cleaning up old tournament usage tracking data.

    This task prevents the tournament_usage table from growing indefinitely
    by removing old entries based on configured retention policies.

    Expected task_config:
    {
        "days_to_keep": 90,  # Keep entries from last N days (default: 90)
        "keep_per_user": 10,  # Keep at most N entries per user (default: 10)
        "cleanup_strategy": "both"  # "age", "count", or "both" (default: "both")
    }

    Args:
        task: ScheduledTask to execute
    """
    from application.services.tournaments.tournament_usage_service import (
        TournamentUsageService,
    )

    logger.info("Starting tournament usage cleanup task: %s", task.name)

    # Extract configuration
    config = task.task_config or {}
    days_to_keep = config.get("days_to_keep", 90)
    keep_per_user = config.get("keep_per_user", 10)
    cleanup_strategy = config.get("cleanup_strategy", "both")

    usage_service = TournamentUsageService()
    total_deleted = 0

    try:
        # Clean up by age
        if cleanup_strategy in ("age", "both"):
            age_deleted = await usage_service.cleanup_old_usage(days_to_keep)
            total_deleted += age_deleted
            logger.info(
                "Cleaned up %d entries older than %d days", age_deleted, days_to_keep
            )

        # Clean up by count per user
        if cleanup_strategy in ("count", "both"):
            count_deleted = await usage_service.cleanup_excess_usage(keep_per_user)
            total_deleted += count_deleted
            logger.info(
                "Cleaned up %d excess entries (keeping %d per user)",
                count_deleted,
                keep_per_user,
            )

        logger.info(
            "Tournament usage cleanup completed: %d total entries removed (strategy: %s)",
            total_deleted,
            cleanup_strategy,
        )
    except Exception as e:
        logger.error("Error during tournament usage cleanup: %s", e, exc_info=True)
        raise


async def handle_async_tournament_timeout_pending(task: ScheduledTask) -> None:
    """
    Handler for timing out pending async tournament races.

    This task checks all pending races with Discord threads and sends warnings
    or auto-forfeits races that have exceeded their timeout period.

    Expected task_config:
    {
        "warning_minutes": 10,  # Minutes before forfeit to send warning (default: 10)
        "timeout_minutes": 20,  # Minutes until forfeit (default: 20)
    }

    Args:
        task: ScheduledTask to execute
    """
    logger.info("Starting async tournament pending race timeout task: %s", task.name)

    # Get Discord bot instance
    bot = get_bot_instance()
    if not bot:
        logger.warning("Discord bot not available, skipping timeout task")
        return

    # Extract configuration
    config = task.task_config or {}
    warning_minutes = config.get("warning_minutes", 10)
    timeout_minutes = config.get("timeout_minutes", 20)

    try:
        pending_races = await AsyncQualifierRace.filter(
            status="pending", discord_thread_id__isnull=False
        ).prefetch_related("user")

        for race in pending_races:
            # Set default timeout if not set
            if not race.thread_timeout_time:
                if race.thread_open_time:
                    race.thread_timeout_time = race.thread_open_time + timedelta(
                        minutes=timeout_minutes
                    )
                    await race.save()

            if not race.thread_timeout_time:
                continue

            warning_time = race.thread_timeout_time - timedelta(minutes=warning_minutes)
            forfeit_time = race.thread_timeout_time

            thread = bot.get_channel(race.discord_thread_id)
            if not thread:
                logger.warning("Cannot access thread for race %s", race.id)
                continue

            now = datetime.now(timezone.utc)

            # Send warning only if not already sent
            if warning_time <= now < forfeit_time and not getattr(
                race, "warning_sent", False
            ):
                await thread.send(
                    f"<@{race.user.discord_id}>, your race will be forfeited on "
                    f"{discord.utils.format_dt(forfeit_time, 'f')} "
                    f"({discord.utils.format_dt(forfeit_time, 'R')}) if you don't start it.",
                    allowed_mentions=discord.AllowedMentions(users=True),
                )
                race.warning_sent = True
                await race.save()

            # Auto-forfeit
            if forfeit_time <= now:
                await thread.send(
                    f"<@{race.user.discord_id}>, this race has been automatically forfeited due to timeout.",
                    allowed_mentions=discord.AllowedMentions(users=True),
                )
                race.status = "forfeit"
                await race.save()

                # Create audit log
                tournament_service = AsyncQualifierService()
                await tournament_service.repo.create_audit_log(
                    tournament_id=race.tournament_id,
                    action="auto_forfeit",
                    details=f"Race {race.id} automatically forfeited (pending timeout)",
                    user_id=SYSTEM_USER_ID,
                )

        logger.info("Completed async tournament pending race timeout task")
    except Exception as e:
        logger.error(
            "Error during async tournament pending race timeout: %s", e, exc_info=True
        )
        raise


async def handle_async_tournament_timeout_in_progress(task: ScheduledTask) -> None:
    """
    Handler for timing out in-progress async tournament races.

    This task checks all in-progress races and auto-forfeits those that have
    exceeded the maximum allowed time.

    Expected task_config:
    {
        "max_hours": 12,  # Maximum hours allowed (default: 12)
    }

    Args:
        task: ScheduledTask to execute
    """
    logger.info(
        "Starting async tournament in-progress race timeout task: %s", task.name
    )

    # Get Discord bot instance
    bot = get_bot_instance()
    if not bot:
        logger.warning("Discord bot not available, skipping timeout task")
        return

    # Extract configuration
    config = task.task_config or {}
    max_hours = config.get("max_hours", 12)

    try:
        in_progress = await AsyncQualifierRace.filter(
            status="in_progress", discord_thread_id__isnull=False
        ).prefetch_related("user")

        for race in in_progress:
            if not race.start_time:
                continue

            # Calculate timeout time
            timeout_time = race.start_time + timedelta(hours=max_hours)

            if datetime.now(timezone.utc) >= timeout_time:
                thread = bot.get_channel(race.discord_thread_id)
                if thread:
                    await thread.send(
                        f"<@{race.user.discord_id}>, this race has exceeded {max_hours} hours and has been forfeited.",
                        allowed_mentions=discord.AllowedMentions(users=True),
                    )

                race.status = "forfeit"
                await race.save()

                # Create audit log
                tournament_service = AsyncQualifierService()
                await tournament_service.repo.create_audit_log(
                    tournament_id=race.tournament_id,
                    action="auto_forfeit",
                    details=f"Race {race.id} automatically forfeited ({max_hours} hour timeout)",
                    user_id=SYSTEM_USER_ID,
                )

        logger.info("Completed async tournament in-progress race timeout task")
    except Exception as e:
        logger.error(
            "Error during async tournament in-progress race timeout: %s",
            e,
            exc_info=True,
        )
        raise


async def handle_async_tournament_score_calculation(task: ScheduledTask) -> None:
    """
    Handler for recalculating async tournament scores.

    This task recalculates scores for all active async tournaments.

    Expected task_config:
    {
        "tournament_ids": [1, 2, 3],  # Optional: Specific tournament IDs to recalculate
    }

    Args:
        task: ScheduledTask to execute
    """
    logger.info("Starting async tournament score calculation task: %s", task.name)

    tournament_service = AsyncQualifierService()

    try:
        # Extract configuration
        config = task.task_config or {}
        specific_tournament_ids = config.get("tournament_ids")

        if specific_tournament_ids:
            # Recalculate for specific tournaments
            tournaments = await AsyncQualifier.filter(id__in=specific_tournament_ids)
        else:
            # Recalculate for all active tournaments
            tournaments = await AsyncQualifier.filter(is_active=True)

        for tournament in tournaments:
            logger.info("Recalculating scores for tournament %s", tournament.id)
            try:
                await tournament_service.calculate_tournament_scores(
                    user=None,  # System task, no user
                    organization_id=tournament.organization_id,
                    tournament_id=tournament.id,
                    system_task=True,  # Bypass authorization for automated task
                )
            except Exception as e:
                logger.error(
                    "Error calculating scores for tournament %s: %s", tournament.id, e
                )

        logger.info("Completed async tournament score calculation task")
    except Exception as e:
        logger.error(
            "Error during async tournament score calculation: %s", e, exc_info=True
        )
        raise


async def handle_async_live_race_open(task: ScheduledTask) -> None:
    """
    Handler for opening a RaceTime.gg room for a scheduled live race.

    This task handler opens a race room on RaceTime.gg for an async tournament live race.
    It should be triggered 30-60 minutes before the scheduled race time.

    Expected task_config:
    {
        "live_race_id": 123,  # ID of AsyncQualifierLiveRace
        "organization_id": 1,  # Organization ID for context
    }

    Args:
        task: ScheduledTask to execute

    Raises:
        ValueError: If required configuration is missing
        RuntimeError: If room opening fails
    """
    logger.info("Opening RaceTime.gg room for live race task: %s", task.name)

    try:
        # Extract configuration
        config = task.task_config or {}
        live_race_id = config.get("live_race_id")
        organization_id = config.get("organization_id")

        if not live_race_id:
            raise ValueError("live_race_id is required in task_config")
        if not organization_id:
            raise ValueError("organization_id is required in task_config")

        # Use service to open race room
        service = AsyncLiveRaceService()
        live_race = await service.open_race_room(live_race_id)

        logger.info(
            "Successfully opened race room for live race %s: %s",
            live_race_id,
            live_race.racetime_url,
        )

    except Exception as e:
        logger.error(
            "Error opening race room for live race (task %s): %s",
            task.id,
            e,
            exc_info=True,
        )
        raise


async def handle_speedgaming_import(task: ScheduledTask) -> None:
    """
    Handler for importing SpeedGaming episodes into matches.

    This task imports upcoming SpeedGaming episodes for all tournaments
    with SpeedGaming integration enabled. Also handles update and deletion
    detection.

    Expected task_config:
    {
        # No configuration required - imports for all enabled tournaments
    }

    Args:
        task: ScheduledTask to execute
    """
    from application.services.speedgaming.speedgaming_etl_service import (
        SpeedGamingETLService,
    )

    logger.info("Starting SpeedGaming episode import task: %s", task.name)

    try:
        etl_service = SpeedGamingETLService()
        imported, updated, deleted = await etl_service.import_all_enabled_tournaments()

        logger.info(
            "Completed SpeedGaming import: %s episodes imported, "
            "%s updated, %s deleted",
            imported,
            updated,
            deleted,
        )

    except Exception as e:
        logger.error("Error during SpeedGaming import: %s", e, exc_info=True)
        raise


async def handle_cleanup_placeholder_users(task: ScheduledTask) -> None:
    """
    Handler for cleaning up abandoned placeholder users.

    This task removes placeholder users that:
    - Have no associated matches (as players)
    - Have no crew assignments (as commentators/trackers)
    - Have not been updated in X days (configurable)

    Expected task_config:
    {
        "days_inactive": 30,  # Remove placeholders unused for 30+ days
    }

    Args:
        task: ScheduledTask to execute
    """
    logger.info("Starting placeholder user cleanup task: %s", task.name)

    # Extract configuration
    config = task.task_config or {}
    days_inactive = config.get("days_inactive", 30)

    try:
        from datetime import datetime, timezone, timedelta
        from models import User
        from models.match_schedule import MatchPlayers, Crew

        # Calculate cutoff date
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_inactive)

        # Find placeholder users
        placeholder_users = await User.filter(
            is_placeholder=True, updated_at__lt=cutoff_date
        ).all()

        deleted_count = 0

        for user in placeholder_users:
            # Check if user has any associated match players
            has_matches = await MatchPlayers.filter(user_id=user.id).exists()

            # Check if user has any crew assignments
            has_crew = await Crew.filter(user_id=user.id).exists()

            # If no associations, delete the user
            if not has_matches and not has_crew:
                logger.info(
                    "Deleting abandoned placeholder user %s (%s)",
                    user.id,
                    user.discord_username,
                )
                await user.delete()
                deleted_count += 1

        logger.info(
            "Completed placeholder user cleanup: %s users deleted "
            "(out of %s placeholders older than %s days)",
            deleted_count,
            len(placeholder_users),
            days_inactive,
        )

    except Exception as e:
        logger.error("Error during placeholder user cleanup: %s", e, exc_info=True)
        raise


async def handle_racetime_poll_open_rooms(task: ScheduledTask) -> None:
    """
    Handler for polling RaceTime.gg for open race rooms and joining them.

    This task scans active RaceTime.gg categories for open race rooms and creates
    handlers based on the bot's default handler configuration. This replaces the
    library's built-in refresh_races() functionality with our own scheduler-based
    approach.

    Expected task_config:
    {
        "enabled_statuses": ["open", "invitational"],  # Race statuses to join
    }

    Args:
        task: ScheduledTask to execute
    """
    logger.info("Starting RaceTime race room polling task: %s", task.name)

    # Extract configuration
    config = task.task_config or {}
    enabled_statuses = config.get("enabled_statuses", ["open", "invitational"])

    try:
        # Get all running bot instances
        bot_instances = get_all_racetime_bot_instances()

        if not bot_instances:
            logger.debug("No RaceTime bots running, skipping polling")
            return

        joined_count = 0
        scanned_count = 0

        for category, bot in bot_instances.items():
            logger.debug("Polling category: %s", category)

            try:
                # Fetch race list for this category using bot's HTTP methods
                # RaceTime.gg API endpoint: /{category}/races/data
                # Note: category is validated by bot initialization and comes from database
                url = bot.http_uri(f"/{category}/races/data")

                # Use bot's HTTP session if available, otherwise create temporary one
                if bot.http and not bot.http.closed:
                    async with bot.http.get(url, ssl=bot.ssl_context) as resp:
                        resp.raise_for_status()
                        data = await resp.json()
                else:
                    # Fallback to creating a temporary session
                    async with httpx.AsyncClient() as client:
                        resp = await client.get(url)
                        resp.raise_for_status()
                        data = await resp.json()

                races = data.get("races", [])
                scanned_count += len(races)

                for race_data in races:
                    try:
                        race_name = race_data.get("name", "")
                        race_status = race_data.get("status", {}).get("value", "")

                        # Skip if not in enabled statuses
                        if race_status not in enabled_statuses:
                            continue

                        # Note: We force join because should_handle() always returns False
                        # by design (automatic polling is disabled).
                        # The bot's handler configuration determines actual handling.

                        # Check if we're already handling this race
                        # Bot.handlers is a dict created by the racetime-bot library
                        if hasattr(bot, "handlers") and race_name in getattr(
                            bot, "handlers", {}
                        ):
                            logger.debug(
                                "Already handling race %s, skipping", race_name
                            )
                            continue

                        # Join the race room with force=True to bypass should_handle()
                        logger.info(
                            "Joining race room: %s (status: %s)", race_name, race_status
                        )
                        handler = await bot.join_race_room(race_name, force=True)

                        if handler:
                            joined_count += 1
                            logger.info(
                                "Successfully joined and created handler for race %s",
                                race_name,
                            )
                        else:
                            logger.warning(
                                "Failed to create handler for race %s", race_name
                            )

                    except Exception as e:
                        logger.error(
                            "Error processing race %s in category %s: %s",
                            race_data.get("name", "unknown"),
                            category,
                            e,
                        )
                        # Continue with next race

            except Exception as e:
                logger.error(
                    "Error polling category %s: %s", category, e, exc_info=True
                )
                # Continue with next category

        logger.info(
            "Completed RaceTime race room polling: scanned %s races, joined %s rooms",
            scanned_count,
            joined_count,
        )

    except Exception as e:
        logger.error("Error during RaceTime race room polling: %s", e, exc_info=True)
        raise


def register_task_handlers() -> None:
    """
    Register all task handlers with the TaskSchedulerService.

    This function should be called during application startup to ensure
    all task handlers are available when the scheduler runs.
    """
    TaskSchedulerService.register_task_handler(TaskType.EXAMPLE_LOG, handle_example_log)
    TaskSchedulerService.register_task_handler(
        TaskType.RACETIME_OPEN_ROOM, handle_racetime_open_room
    )
    TaskSchedulerService.register_task_handler(
        TaskType.CLEANUP_TOURNAMENT_USAGE, handle_cleanup_tournament_usage
    )
    TaskSchedulerService.register_task_handler(
        TaskType.ASYNC_TOURNAMENT_TIMEOUT_PENDING,
        handle_async_tournament_timeout_pending,
    )
    TaskSchedulerService.register_task_handler(
        TaskType.ASYNC_TOURNAMENT_TIMEOUT_IN_PROGRESS,
        handle_async_tournament_timeout_in_progress,
    )
    TaskSchedulerService.register_task_handler(
        TaskType.ASYNC_TOURNAMENT_SCORE_CALCULATION,
        handle_async_tournament_score_calculation,
    )
    TaskSchedulerService.register_task_handler(
        TaskType.ASYNC_LIVE_RACE_OPEN, handle_async_live_race_open
    )
    TaskSchedulerService.register_task_handler(
        TaskType.SPEEDGAMING_IMPORT, handle_speedgaming_import
    )
    TaskSchedulerService.register_task_handler(
        TaskType.CLEANUP_PLACEHOLDER_USERS, handle_cleanup_placeholder_users
    )
    TaskSchedulerService.register_task_handler(
        TaskType.RACETIME_POLL_OPEN_ROOMS, handle_racetime_poll_open_rooms
    )
    TaskSchedulerService.register_task_handler(TaskType.CUSTOM, handle_custom_task)
    logger.info("All task handlers registered")
