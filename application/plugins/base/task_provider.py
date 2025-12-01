"""
Task provider interface.

This module defines the interface for plugins that contribute scheduled tasks.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class TaskType(str, Enum):
    """Type of scheduled task."""

    SYNC = "sync"
    CLEANUP = "cleanup"
    NOTIFICATION = "notification"
    CUSTOM = "custom"


class ScheduleType(str, Enum):
    """Schedule type for tasks."""

    INTERVAL = "interval"
    CRON = "cron"


@dataclass
class TaskRegistration:
    """Scheduled task registration."""

    task_id: str
    name: str
    description: str
    handler: Callable
    task_type: TaskType
    schedule_type: ScheduleType
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    is_active: bool = True
    task_config: Dict[str, Any] = field(default_factory=dict)


class TaskProvider(ABC):
    """Interface for plugins that provide scheduled tasks."""

    @abstractmethod
    def get_scheduled_tasks(self) -> List[TaskRegistration]:
        """
        Return scheduled tasks to register.

        Returns:
            List of TaskRegistration instances
        """
        pass

    def get_task_prefix(self) -> str:
        """
        Return prefix for task IDs.

        Used to namespace task IDs: {prefix}_{task_id}

        Returns:
            Task ID prefix (default: plugin_id)
        """
        return getattr(self, "plugin_id", "unknown")
