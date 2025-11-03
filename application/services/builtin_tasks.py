"""
Built-in scheduled tasks configuration.

This module defines tasks that are built into the application and loaded
at startup. These tasks don't need to be created in the database and can
be global (not scoped to any organization).
"""

from typing import Dict, Any
from models.scheduled_task import TaskType, ScheduleType


class BuiltInTask:
    """
    Definition of a built-in task.
    
    Built-in tasks are loaded at application startup and run automatically.
    They are not stored in the database but exist in memory during runtime.
    """
    
    def __init__(
        self,
        task_id: str,
        name: str,
        description: str,
        task_type: TaskType,
        schedule_type: ScheduleType,
        is_global: bool = True,
        interval_seconds: int | None = None,
        cron_expression: str | None = None,
        task_config: Dict[str, Any] | None = None,
        is_active: bool = True,
    ):
        """
        Initialize a built-in task definition.
        
        Args:
            task_id: Unique identifier for the task (used internally)
            name: Human-readable task name
            description: Task description
            task_type: Type of task (TaskType enum)
            schedule_type: How the task is scheduled (ScheduleType enum)
            is_global: If True, task is global; if False, requires organization
            interval_seconds: For INTERVAL schedule type
            cron_expression: For CRON schedule type
            task_config: Task-specific configuration
            is_active: Whether task is enabled by default
        """
        self.task_id = task_id
        self.name = name
        self.description = description
        self.task_type = task_type
        self.schedule_type = schedule_type
        self.is_global = is_global
        self.interval_seconds = interval_seconds
        self.cron_expression = cron_expression
        self.task_config = task_config or {}
        self.is_active = is_active
        self.organization_id = None  # Global tasks have no organization
    
    def __repr__(self) -> str:
        """String representation."""
        scope = "global" if self.is_global else "org-scoped"
        return f"<BuiltInTask {self.task_id} ({scope}): {self.name}>"


# Define built-in tasks
BUILTIN_TASKS: Dict[str, BuiltInTask] = {
    'cleanup_tournament_usage': BuiltInTask(
        task_id='cleanup_tournament_usage',
        name='Tournament Usage Cleanup',
        description='Automatically cleans up old tournament usage tracking data to prevent database bloat',
        task_type=TaskType.CLEANUP_TOURNAMENT_USAGE,
        schedule_type=ScheduleType.CRON,
        is_global=True,
        cron_expression='0 3 * * *',  # Daily at 3 AM UTC
        task_config={
            'days_to_keep': 90,
            'keep_per_user': 10,
            'cleanup_strategy': 'both',
        },
        is_active=True,
    ),
    
    # Example of a disabled built-in task
    'example_builtin_log': BuiltInTask(
        task_id='example_builtin_log',
        name='Example Built-in Log Task',
        description='Example built-in task that logs a message every hour (disabled by default)',
        task_type=TaskType.EXAMPLE_LOG,
        schedule_type=ScheduleType.INTERVAL,
        is_global=True,
        interval_seconds=3600,  # Every hour
        task_config={
            'message': 'This is a built-in task example',
        },
        is_active=False,  # Disabled by default
    ),
}


def get_builtin_task(task_id: str) -> BuiltInTask | None:
    """
    Get a built-in task by ID.
    
    Args:
        task_id: Task identifier
        
    Returns:
        BuiltInTask if found, None otherwise
    """
    return BUILTIN_TASKS.get(task_id)


def get_all_builtin_tasks() -> list[BuiltInTask]:
    """
    Get all built-in tasks.
    
    Returns:
        List of all built-in tasks
    """
    return list(BUILTIN_TASKS.values())


def get_active_builtin_tasks() -> list[BuiltInTask]:
    """
    Get all active built-in tasks.
    
    Returns:
        List of active built-in tasks
    """
    return [task for task in BUILTIN_TASKS.values() if task.is_active]
