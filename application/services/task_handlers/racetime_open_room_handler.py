"""
RaceTime.gg room opening task handler.

This handler opens race rooms on racetime.gg at scheduled times.
"""
import logging
from models.scheduled_task import ScheduledTask

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

    # Future implementation will use the racetime bot to create a room
    logger.info(
        "Would open racetime room: category=%s, goal=%s, info=%s, unlisted=%s, invitational=%s, team_race=%s",
        category, goal, info, unlisted, invitational, team_race
    )

    # TODO: Implement actual racetime room opening logic
    # This will require integration with the racetime bot client
    # from racetime.client import get_racetime_bot_instance
    # bot = get_racetime_bot_instance(category)
    # if not bot:
    #     raise RuntimeError(f"Racetime bot for category {category} is not running")
    # await bot.create_race(goal=goal, info=info, unlisted=unlisted, ...)
