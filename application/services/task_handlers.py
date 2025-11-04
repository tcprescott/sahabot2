"""
Task handlers for scheduled tasks.

This module contains handler functions for different task types.
Each handler is registered with the TaskSchedulerService and executed
when a task of that type is due to run.
"""
import logging
import discord
from datetime import datetime, timedelta, timezone
from models.scheduled_task import ScheduledTask, TaskType
from models.async_tournament import AsyncTournament, AsyncTournamentRace
from application.services.task_scheduler_service import TaskSchedulerService
from application.services.async_tournament_service import AsyncTournamentService
from discordbot.client import get_bot_instance

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
        message = task.task_config.get('message', 'No custom message')
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
    category = config.get('category')
    goal = config.get('goal', 'Beat the game')
    info = config.get('info', '')
    unlisted = config.get('unlisted', False)
    invitational = config.get('invitational', False)
    team_race = config.get('team_race', False)

    if not category:
        raise ValueError("category is required in task_config")

    # TODO: Implement actual racetime room opening logic
    # This will require integration with the racetime bot client
    # For now, we just log the intent
    logger.info(
        "Would open racetime room: category=%s, goal=%s, info=%s, unlisted=%s, invitational=%s, team_race=%s",
        category, goal, info, unlisted, invitational, team_race
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
    from application.services.tournament_usage_service import TournamentUsageService

    logger.info("Starting tournament usage cleanup task: %s", task.name)

    # Extract configuration
    config = task.task_config or {}
    days_to_keep = config.get('days_to_keep', 90)
    keep_per_user = config.get('keep_per_user', 10)
    cleanup_strategy = config.get('cleanup_strategy', 'both')

    usage_service = TournamentUsageService()
    total_deleted = 0

    try:
        # Clean up by age
        if cleanup_strategy in ('age', 'both'):
            age_deleted = await usage_service.cleanup_old_usage(days_to_keep)
            total_deleted += age_deleted
            logger.info("Cleaned up %d entries older than %d days", age_deleted, days_to_keep)

        # Clean up by count per user
        if cleanup_strategy in ('count', 'both'):
            count_deleted = await usage_service.cleanup_excess_usage(keep_per_user)
            total_deleted += count_deleted
            logger.info("Cleaned up %d excess entries (keeping %d per user)", count_deleted, keep_per_user)

        logger.info(
            "Tournament usage cleanup completed: %d total entries removed (strategy: %s)",
            total_deleted,
            cleanup_strategy
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
    warning_minutes = config.get('warning_minutes', 10)
    timeout_minutes = config.get('timeout_minutes', 20)

    try:
        pending_races = await AsyncTournamentRace.filter(
            status='pending',
            discord_thread_id__isnull=False
        ).prefetch_related('user')

        for race in pending_races:
            # Set default timeout if not set
            if not race.thread_timeout_time:
                if race.thread_open_time:
                    race.thread_timeout_time = race.thread_open_time + timedelta(minutes=timeout_minutes)
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
            if warning_time <= now < forfeit_time and not getattr(race, "warning_sent", False):
                await thread.send(
                    f"<@{race.user.discord_id}>, your race will be forfeited on "
                    f"{discord.utils.format_dt(forfeit_time, 'f')} "
                    f"({discord.utils.format_dt(forfeit_time, 'R')}) if you don't start it.",
                    allowed_mentions=discord.AllowedMentions(users=True)
                )
                race.warning_sent = True
                await race.save()

            # Auto-forfeit
            if forfeit_time <= now:
                await thread.send(
                    f"<@{race.user.discord_id}>, this race has been automatically forfeited due to timeout.",
                    allowed_mentions=discord.AllowedMentions(users=True)
                )
                race.status = 'forfeit'
                await race.save()

                # Create audit log
                tournament_service = AsyncTournamentService()
                await tournament_service.repo.create_audit_log(
                    tournament_id=race.tournament_id,
                    action="auto_forfeit",
                    details=f"Race {race.id} automatically forfeited (pending timeout)",
                    user_id=None,
                )

        logger.info("Completed async tournament pending race timeout task")
    except Exception as e:
        logger.error("Error during async tournament pending race timeout: %s", e, exc_info=True)
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
    logger.info("Starting async tournament in-progress race timeout task: %s", task.name)

    # Get Discord bot instance
    bot = get_bot_instance()
    if not bot:
        logger.warning("Discord bot not available, skipping timeout task")
        return

    # Extract configuration
    config = task.task_config or {}
    max_hours = config.get('max_hours', 12)

    try:
        in_progress = await AsyncTournamentRace.filter(
            status='in_progress',
            discord_thread_id__isnull=False
        ).prefetch_related('user')

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
                        allowed_mentions=discord.AllowedMentions(users=True)
                    )

                race.status = 'forfeit'
                await race.save()

                # Create audit log
                tournament_service = AsyncTournamentService()
                await tournament_service.repo.create_audit_log(
                    tournament_id=race.tournament_id,
                    action="auto_forfeit",
                    details=f"Race {race.id} automatically forfeited ({max_hours} hour timeout)",
                    user_id=None,
                )

        logger.info("Completed async tournament in-progress race timeout task")
    except Exception as e:
        logger.error("Error during async tournament in-progress race timeout: %s", e, exc_info=True)
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

    tournament_service = AsyncTournamentService()

    try:
        # Extract configuration
        config = task.task_config or {}
        specific_tournament_ids = config.get('tournament_ids')

        if specific_tournament_ids:
            # Recalculate for specific tournaments
            tournaments = await AsyncTournament.filter(id__in=specific_tournament_ids)
        else:
            # Recalculate for all active tournaments
            tournaments = await AsyncTournament.filter(is_active=True)

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
                logger.error("Error calculating scores for tournament %s: %s", tournament.id, e)

        logger.info("Completed async tournament score calculation task")
    except Exception as e:
        logger.error("Error during async tournament score calculation: %s", e, exc_info=True)
        raise


def register_task_handlers() -> None:
    """
    Register all task handlers with the TaskSchedulerService.

    This function should be called during application startup to ensure
    all task handlers are available when the scheduler runs.
    """
    TaskSchedulerService.register_task_handler(TaskType.EXAMPLE_LOG, handle_example_log)
    TaskSchedulerService.register_task_handler(TaskType.RACETIME_OPEN_ROOM, handle_racetime_open_room)
    TaskSchedulerService.register_task_handler(TaskType.CLEANUP_TOURNAMENT_USAGE, handle_cleanup_tournament_usage)
    TaskSchedulerService.register_task_handler(TaskType.ASYNC_TOURNAMENT_TIMEOUT_PENDING, handle_async_tournament_timeout_pending)
    TaskSchedulerService.register_task_handler(TaskType.ASYNC_TOURNAMENT_TIMEOUT_IN_PROGRESS, handle_async_tournament_timeout_in_progress)
    TaskSchedulerService.register_task_handler(TaskType.ASYNC_TOURNAMENT_SCORE_CALCULATION, handle_async_tournament_score_calculation)
    TaskSchedulerService.register_task_handler(TaskType.CUSTOM, handle_custom_task)
    logger.info("All task handlers registered")
