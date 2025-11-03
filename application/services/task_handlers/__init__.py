"""
Task handlers for scheduled tasks.

This package contains handler functions for different task types.
Each handler is registered with the TaskSchedulerService and executed
when a task of that type is due to run.
"""
import logging
from models.scheduled_task import TaskType
from application.services.task_scheduler_service import TaskSchedulerService
from .example_log_handler import handle_example_log
from .racetime_open_room_handler import handle_racetime_open_room
from .custom_task_handler import handle_custom_task

logger = logging.getLogger(__name__)


def register_task_handlers() -> None:
    """
    Register all task handlers with the TaskSchedulerService.

    This function should be called during application startup to ensure
    all task handlers are available when the scheduler runs.
    """
    TaskSchedulerService.register_task_handler(TaskType.EXAMPLE_LOG, handle_example_log)
    TaskSchedulerService.register_task_handler(TaskType.RACETIME_OPEN_ROOM, handle_racetime_open_room)
    TaskSchedulerService.register_task_handler(TaskType.CUSTOM, handle_custom_task)
    logger.info("All task handlers registered")


__all__ = [
    'register_task_handlers',
    'handle_example_log',
    'handle_racetime_open_room',
    'handle_custom_task',
]
