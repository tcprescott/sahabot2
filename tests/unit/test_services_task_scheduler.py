"""
Unit tests for TaskSchedulerService.

Tests the business logic for scheduled tasks.
"""

import pytest
from datetime import datetime, timedelta, timezone
from models.scheduled_task import TaskType, ScheduleType
from application.services.tasks.task_scheduler_service import TaskSchedulerService


@pytest.mark.unit
class TestTaskSchedulerService:
    """Test cases for TaskSchedulerService."""

    def test_calculate_next_run_interval(self):
        """Test calculating next run time for interval tasks."""
        service = TaskSchedulerService()
        now = datetime.now(timezone.utc)

        next_run = service._calculate_next_run(
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=300,
            from_time=now,
        )

        assert next_run is not None
        assert next_run > now
        assert (next_run - now).total_seconds() == 300

    def test_calculate_next_run_cron(self):
        """Test calculating next run time for cron tasks."""
        service = TaskSchedulerService()
        now = datetime.now(timezone.utc)

        # Daily at 14:00 (2 PM)
        next_run = service._calculate_next_run(
            schedule_type=ScheduleType.CRON,
            cron_expression="0 14 * * *",
            from_time=now,
        )

        assert next_run is not None
        assert next_run > now

    def test_calculate_next_run_onetime_future(self):
        """Test calculating next run time for one-time tasks (future)."""
        service = TaskSchedulerService()
        now = datetime.now(timezone.utc)
        future_time = now + timedelta(hours=1)

        next_run = service._calculate_next_run(
            schedule_type=ScheduleType.ONE_TIME,
            scheduled_time=future_time,
            from_time=now,
        )

        assert next_run == future_time

    def test_calculate_next_run_onetime_past(self):
        """Test calculating next run time for one-time tasks (past)."""
        service = TaskSchedulerService()
        now = datetime.now(timezone.utc)
        past_time = now - timedelta(hours=1)

        next_run = service._calculate_next_run(
            schedule_type=ScheduleType.ONE_TIME,
            scheduled_time=past_time,
            from_time=now,
        )

        assert next_run is None

    @pytest.mark.asyncio
    async def test_register_task_handler(self):
        """Test registering a task handler."""

        async def dummy_handler(task):
            pass

        TaskSchedulerService.register_task_handler(TaskType.CUSTOM, dummy_handler)

        assert TaskType.CUSTOM in TaskSchedulerService._task_handlers
        assert TaskSchedulerService._task_handlers[TaskType.CUSTOM] == dummy_handler

    @pytest.mark.asyncio
    async def test_create_task_interval(self, db, admin_user, sample_organization):
        """Test creating an interval-based task."""
        service = TaskSchedulerService()

        # Mock the org service check
        from unittest.mock import AsyncMock, patch

        with patch.object(service.org_service, 'user_can_manage_tournaments', new=AsyncMock(return_value=True)):
            task = await service.create_task(
                user=admin_user,
                organization_id=sample_organization.id,
                name="Test Task",
                task_type=TaskType.CUSTOM,
                schedule_type=ScheduleType.INTERVAL,
                interval_seconds=300,
                task_config={"test": "data"},
            )

        assert task is not None
        assert task.name == "Test Task"
        assert task.interval_seconds == 300

    @pytest.mark.asyncio
    async def test_create_task_unauthorized(self, db, sample_user):
        """Test creating a task without authorization."""
        service = TaskSchedulerService()

        # Mock the org service check to return False
        from unittest.mock import AsyncMock, patch

        with patch.object(service.org_service, 'user_can_manage_tournaments', new=AsyncMock(return_value=False)):
            task = await service.create_task(
                user=sample_user,
                organization_id=1,
                name="Test Task",
                task_type=TaskType.CUSTOM,
                schedule_type=ScheduleType.INTERVAL,
                interval_seconds=300,
            )

        assert task is None

    @pytest.mark.asyncio
    async def test_create_task_missing_interval(self, db, sample_user):
        """Test creating an interval task without interval_seconds."""
        service = TaskSchedulerService()

        from unittest.mock import AsyncMock, patch

        with patch.object(service.org_service, 'user_can_manage_tournaments', new=AsyncMock(return_value=True)):
            task = await service.create_task(
                user=sample_user,
                organization_id=1,
                name="Test Task",
                task_type=TaskType.CUSTOM,
                schedule_type=ScheduleType.INTERVAL,
                # Missing interval_seconds
            )

        assert task is None

    @pytest.mark.asyncio
    async def test_create_task_invalid_cron(self, db, sample_user):
        """Test creating a cron task with invalid expression."""
        service = TaskSchedulerService()

        from unittest.mock import AsyncMock, patch

        with patch.object(service.org_service, 'user_can_manage_tournaments', new=AsyncMock(return_value=True)):
            task = await service.create_task(
                user=sample_user,
                organization_id=1,
                name="Test Task",
                task_type=TaskType.CUSTOM,
                schedule_type=ScheduleType.CRON,
                cron_expression="invalid cron",
            )

        assert task is None
