"""
Example log task handler.

This is a simple example task demonstrating how to create a scheduled task handler.
"""
import logging
from models.scheduled_task import ScheduledTask

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
