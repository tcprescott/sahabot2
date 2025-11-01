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


def register_task_handlers() -> None:
    """
    Register all task handlers with the TaskSchedulerService.

    This function should be called during application startup to ensure
    all task handlers are available when the scheduler runs.
    """
    TaskSchedulerService.register_task_handler(TaskType.RACETIME_OPEN_ROOM, handle_racetime_open_room)
    TaskSchedulerService.register_task_handler(TaskType.CUSTOM, handle_custom_task)
    logger.info("All task handlers registered")
