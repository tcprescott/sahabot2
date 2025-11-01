"""
Task Scheduler Service for SahaBot2.

Manages scheduled tasks execution and provides business logic for task scheduling.
"""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Callable, Dict, Any
from croniter import croniter

from models import User
from models.scheduled_task import ScheduledTask, TaskType, ScheduleType
from application.repositories.scheduled_task_repository import ScheduledTaskRepository
from application.services.organization_service import OrganizationService

logger = logging.getLogger(__name__)


class TaskSchedulerService:
    """
    Service for managing scheduled tasks.

    Handles task scheduling, execution, and lifecycle management.
    """

    # Singleton for background task runner
    _runner_task: Optional[asyncio.Task] = None
    _is_running: bool = False
    _task_handlers: Dict[TaskType, Callable] = {}

    def __init__(self) -> None:
        self.repo = ScheduledTaskRepository()
        self.org_service = OrganizationService()

    @classmethod
    def register_task_handler(cls, task_type: TaskType, handler: Callable) -> None:
        """
        Register a handler function for a specific task type.

        Args:
            task_type: The type of task this handler processes
            handler: Async function that takes (task: ScheduledTask) and executes it
        """
        cls._task_handlers[task_type] = handler
        logger.info("Registered task handler for task type: %s", task_type.name)

    async def create_task(
        self,
        user: Optional[User],
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
    ) -> Optional[ScheduledTask]:
        """
        Create a new scheduled task.

        Args:
            user: User creating the task
            organization_id: Organization ID
            name: Task name
            task_type: Type of task
            schedule_type: How the task is scheduled
            description: Optional description
            interval_seconds: For INTERVAL type
            cron_expression: For CRON type
            scheduled_time: For ONE_TIME type
            task_config: Task-specific configuration
            is_active: Whether task is active

        Returns:
            Created ScheduledTask or None if unauthorized
        """
        # Check authorization
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning(
                "Unauthorized create_task by user %s for org %s",
                getattr(user, 'id', None),
                organization_id
            )
            return None

        # Validate schedule parameters
        if schedule_type == ScheduleType.INTERVAL and not interval_seconds:
            logger.error("interval_seconds required for INTERVAL schedule type")
            return None
        if schedule_type == ScheduleType.CRON and not cron_expression:
            logger.error("cron_expression required for CRON schedule type")
            return None
        if schedule_type == ScheduleType.ONE_TIME and not scheduled_time:
            logger.error("scheduled_time required for ONE_TIME schedule type")
            return None

        # Validate cron expression if provided
        if cron_expression:
            try:
                croniter(cron_expression)
            except Exception as e:
                logger.error("Invalid cron expression: %s", e)
                return None

        # Calculate next run time
        next_run_at = self._calculate_next_run(
            schedule_type=schedule_type,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            scheduled_time=scheduled_time,
        )

        # Create task
        task = await self.repo.create(
            organization_id=organization_id,
            name=name,
            task_type=task_type,
            schedule_type=schedule_type,
            description=description,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            scheduled_time=scheduled_time,
            task_config=task_config,
            is_active=is_active,
            created_by_id=user.id if user else None,
        )

        # Set next run time
        if next_run_at:
            await self.repo.update(task.id, next_run_at=next_run_at)

        return task

    async def list_tasks(
        self,
        user: Optional[User],
        organization_id: int,
        active_only: bool = False
    ) -> List[ScheduledTask]:
        """
        List scheduled tasks for an organization.

        Args:
            user: User requesting the list
            organization_id: Organization ID
            active_only: If True, only return active tasks

        Returns:
            List of ScheduledTask instances
        """
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning(
                "Unauthorized list_tasks by user %s for org %s",
                getattr(user, 'id', None),
                organization_id
            )
            return []

        return await self.repo.list_by_org(organization_id, active_only=active_only)

    async def get_task(
        self,
        user: Optional[User],
        organization_id: int,
        task_id: int
    ) -> Optional[ScheduledTask]:
        """
        Get a specific scheduled task.

        Args:
            user: User requesting the task
            organization_id: Organization ID
            task_id: Task ID

        Returns:
            ScheduledTask instance or None
        """
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning(
                "Unauthorized get_task by user %s for org %s",
                getattr(user, 'id', None),
                organization_id
            )
            return None

        task = await self.repo.get_by_id(task_id)
        if task and task.organization_id != organization_id:
            logger.warning("Task %s does not belong to org %s", task_id, organization_id)
            return None

        return task

    async def update_task(
        self,
        user: Optional[User],
        organization_id: int,
        task_id: int,
        **kwargs
    ) -> Optional[ScheduledTask]:
        """
        Update a scheduled task.

        Args:
            user: User updating the task
            organization_id: Organization ID
            task_id: Task ID
            **kwargs: Fields to update

        Returns:
            Updated ScheduledTask or None
        """
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning(
                "Unauthorized update_task by user %s for org %s",
                getattr(user, 'id', None),
                organization_id
            )
            return None

        task = await self.repo.get_by_id(task_id)
        if not task or task.organization_id != organization_id:
            return None

        # Recalculate next run time if schedule changed
        if any(k in kwargs for k in ['interval_seconds', 'cron_expression', 'scheduled_time', 'schedule_type']):
            schedule_type = kwargs.get('schedule_type', task.schedule_type)
            interval_seconds = kwargs.get('interval_seconds', task.interval_seconds)
            cron_expression = kwargs.get('cron_expression', task.cron_expression)
            scheduled_time = kwargs.get('scheduled_time', task.scheduled_time)

            next_run_at = self._calculate_next_run(
                schedule_type=schedule_type,
                interval_seconds=interval_seconds,
                cron_expression=cron_expression,
                scheduled_time=scheduled_time,
            )
            if next_run_at:
                kwargs['next_run_at'] = next_run_at

        return await self.repo.update(task_id, **kwargs)

    async def delete_task(
        self,
        user: Optional[User],
        organization_id: int,
        task_id: int
    ) -> bool:
        """
        Delete a scheduled task.

        Args:
            user: User deleting the task
            organization_id: Organization ID
            task_id: Task ID

        Returns:
            True if deleted, False otherwise
        """
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning(
                "Unauthorized delete_task by user %s for org %s",
                getattr(user, 'id', None),
                organization_id
            )
            return False

        task = await self.repo.get_by_id(task_id)
        if not task or task.organization_id != organization_id:
            return False

        return await self.repo.delete(task_id)

    @classmethod
    async def start_scheduler(cls) -> None:
        """
        Start the background task scheduler.

        Should be called during application startup.
        """
        if cls._is_running:
            logger.warning("Task scheduler already running")
            return

        cls._is_running = True
        cls._runner_task = asyncio.create_task(cls._run_scheduler())
        logger.info("Task scheduler started")

    @classmethod
    async def stop_scheduler(cls) -> None:
        """
        Stop the background task scheduler.

        Should be called during application shutdown.
        """
        if not cls._is_running:
            logger.warning("Task scheduler not running")
            return

        cls._is_running = False
        if cls._runner_task:
            cls._runner_task.cancel()
            try:
                await cls._runner_task
            except asyncio.CancelledError:
                pass
        logger.info("Task scheduler stopped")

    @classmethod
    async def _run_scheduler(cls) -> None:
        """Background task that runs scheduled tasks."""
        logger.info("Task scheduler loop started")
        repo = ScheduledTaskRepository()

        while cls._is_running:
            try:
                # Get tasks due to run
                now = datetime.utcnow()
                tasks = await repo.list_tasks_due_to_run(now)

                for task in tasks:
                    # Execute task in background
                    asyncio.create_task(cls._execute_task(task))

                # Sleep for a short interval before checking again
                await asyncio.sleep(10)  # Check every 10 seconds

            except asyncio.CancelledError:
                logger.info("Task scheduler cancelled")
                break
            except Exception as e:
                logger.error("Error in task scheduler loop: %s", e, exc_info=True)
                await asyncio.sleep(10)

        logger.info("Task scheduler loop stopped")

    @classmethod
    async def _execute_task(cls, task: ScheduledTask) -> None:
        """
        Execute a scheduled task.

        Args:
            task: ScheduledTask to execute
        """
        logger.info("Executing task %s: %s", task.id, task.name)
        repo = ScheduledTaskRepository()

        # Update status to running
        await repo.update_run_status(
            task_id=task.id,
            status='running',
            last_run_at=datetime.utcnow(),
        )

        try:
            # Get handler for this task type
            handler = cls._task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {task.task_type}")

            # Execute the handler
            await handler(task)

            # Calculate next run time
            next_run_at = cls._calculate_next_run(
                schedule_type=task.schedule_type,
                interval_seconds=task.interval_seconds,
                cron_expression=task.cron_expression,
                scheduled_time=task.scheduled_time,
                from_time=datetime.utcnow(),
            )

            # Update status to success
            await repo.update_run_status(
                task_id=task.id,
                status='success',
                last_run_at=datetime.utcnow(),
                next_run_at=next_run_at,
            )

            # Deactivate one-time tasks after execution
            if task.schedule_type == ScheduleType.ONE_TIME:
                await repo.update(task.id, is_active=False)

            logger.info("Task %s executed successfully", task.id)

        except Exception as e:
            logger.error("Error executing task %s: %s", task.id, e, exc_info=True)
            await repo.update_run_status(
                task_id=task.id,
                status='failed',
                last_run_at=datetime.utcnow(),
                error=str(e),
            )

    @staticmethod
    def _calculate_next_run(
        schedule_type: ScheduleType,
        interval_seconds: Optional[int] = None,
        cron_expression: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
        from_time: Optional[datetime] = None,
    ) -> Optional[datetime]:
        """
        Calculate the next run time for a task.

        Args:
            schedule_type: Type of schedule
            interval_seconds: For INTERVAL type
            cron_expression: For CRON type
            scheduled_time: For ONE_TIME type
            from_time: Calculate from this time (default: now)

        Returns:
            Next run datetime or None
        """
        if from_time is None:
            from_time = datetime.utcnow()

        if schedule_type == ScheduleType.INTERVAL and interval_seconds:
            return from_time + timedelta(seconds=interval_seconds)

        elif schedule_type == ScheduleType.CRON and cron_expression:
            try:
                cron = croniter(cron_expression, from_time)
                return cron.get_next(datetime)
            except Exception as e:
                logger.error("Error calculating next cron run: %s", e)
                return None

        elif schedule_type == ScheduleType.ONE_TIME and scheduled_time:
            # For one-time tasks, only return scheduled_time if it's in the future
            if scheduled_time > from_time:
                return scheduled_time
            return None

        return None
