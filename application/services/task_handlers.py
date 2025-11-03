"""
Task handlers for scheduled tasks.

This module contains handler functions for different task types.
Each handler is registered with the TaskSchedulerService and executed
when a task of that type is due to run.
"""
import logging
from models.scheduled_task import ScheduledTask, TaskType
from application.services.task_scheduler_service import TaskSchedulerService

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


def register_task_handlers() -> None:
    """
    Register all task handlers with the TaskSchedulerService.

    This function should be called during application startup to ensure
    all task handlers are available when the scheduler runs.
    """
    TaskSchedulerService.register_task_handler(TaskType.EXAMPLE_LOG, handle_example_log)
    TaskSchedulerService.register_task_handler(TaskType.RACETIME_OPEN_ROOM, handle_racetime_open_room)
    TaskSchedulerService.register_task_handler(TaskType.CLEANUP_TOURNAMENT_USAGE, handle_cleanup_tournament_usage)
    TaskSchedulerService.register_task_handler(TaskType.CUSTOM, handle_custom_task)
    logger.info("All task handlers registered")
