"""
Repository layer for ScheduledTask data access.

Handles all database operations for scheduled tasks.
"""
from __future__ import annotations
from typing import Optional, List
from datetime import datetime
import logging

from models.scheduled_task import ScheduledTask, TaskType, ScheduleType

logger = logging.getLogger(__name__)


class ScheduledTaskRepository:
    """Repository for scheduled task data access."""

    async def create(
        self,
        organization_id: int,
        name: str,
        task_type: TaskType,
        schedule_type: ScheduleType,
        description: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        cron_expression: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
        task_config: Optional[dict] = None,
        is_active: bool = True,
        created_by_id: Optional[int] = None,
    ) -> ScheduledTask:
        """
        Create a new scheduled task.

        Args:
            organization_id: Organization ID that owns this task
            name: Task name
            task_type: Type of task (TaskType enum)
            schedule_type: How the task is scheduled (ScheduleType enum)
            description: Optional task description
            interval_seconds: For INTERVAL type, the interval in seconds
            cron_expression: For CRON type, the cron expression
            scheduled_time: For ONE_TIME type, the specific time to run
            task_config: Task-specific configuration as JSON
            is_active: Whether the task is active
            created_by_id: User ID who created the task

        Returns:
            Created ScheduledTask instance
        """
        task = await ScheduledTask.create(
            organization_id=organization_id,
            name=name,
            description=description,
            task_type=task_type,
            schedule_type=schedule_type,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            scheduled_time=scheduled_time,
            task_config=task_config or {},
            is_active=is_active,
            created_by_id=created_by_id,
        )
        logger.info("Created scheduled task %s for organization %s", task.id, organization_id)
        return task

    async def get_by_id(self, task_id: int) -> Optional[ScheduledTask]:
        """
        Get a scheduled task by ID.

        Args:
            task_id: Task ID

        Returns:
            ScheduledTask instance or None if not found
        """
        return await ScheduledTask.filter(id=task_id).first()

    async def list_by_org(self, organization_id: int, active_only: bool = False) -> List[ScheduledTask]:
        """
        List all scheduled tasks for an organization.

        Args:
            organization_id: Organization ID
            active_only: If True, only return active tasks

        Returns:
            List of ScheduledTask instances
        """
        query = ScheduledTask.filter(organization_id=organization_id)
        if active_only:
            query = query.filter(is_active=True)
        return await query.order_by('-created_at')

    async def list_active_tasks(self) -> List[ScheduledTask]:
        """
        List all active scheduled tasks across all organizations.

        Returns:
            List of active ScheduledTask instances
        """
        return await ScheduledTask.filter(is_active=True).order_by('next_run_at')

    async def list_tasks_due_to_run(self, before_time: datetime) -> List[ScheduledTask]:
        """
        List tasks that are due to run before the specified time.

        Args:
            before_time: Time threshold

        Returns:
            List of ScheduledTask instances that should run
        """
        return await ScheduledTask.filter(
            is_active=True,
            next_run_at__lte=before_time,
        ).order_by('next_run_at')

    async def update(
        self,
        task_id: int,
        **kwargs
    ) -> Optional[ScheduledTask]:
        """
        Update a scheduled task.

        Args:
            task_id: Task ID
            **kwargs: Fields to update

        Returns:
            Updated ScheduledTask instance or None if not found
        """
        task = await self.get_by_id(task_id)
        if not task:
            return None

        await task.update_from_dict(kwargs)
        await task.save()
        logger.info("Updated scheduled task %s", task_id)
        return task

    async def delete(self, task_id: int) -> bool:
        """
        Delete a scheduled task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted, False if not found
        """
        task = await self.get_by_id(task_id)
        if not task:
            return False

        await task.delete()
        logger.info("Deleted scheduled task %s", task_id)
        return True

    async def update_run_status(
        self,
        task_id: int,
        status: str,
        last_run_at: datetime,
        next_run_at: Optional[datetime] = None,
        error: Optional[str] = None,
    ) -> Optional[ScheduledTask]:
        """
        Update the run status of a task.

        Args:
            task_id: Task ID
            status: Run status ('success', 'failed', 'running')
            last_run_at: When the task last ran
            next_run_at: When the task should run next (optional)
            error: Error message if failed (optional)

        Returns:
            Updated ScheduledTask instance or None if not found
        """
        task = await self.get_by_id(task_id)
        if not task:
            return None

        task.last_run_status = status
        task.last_run_at = last_run_at
        if next_run_at is not None:
            task.next_run_at = next_run_at
        if error is not None:
            task.last_run_error = error
        else:
            task.last_run_error = None

        await task.save()
        return task
