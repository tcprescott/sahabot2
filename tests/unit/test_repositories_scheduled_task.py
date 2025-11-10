"""
Unit tests for ScheduledTaskRepository.

Tests the data access layer for scheduled tasks.
"""

import pytest
from datetime import datetime, timedelta, timezone
from models.scheduled_task import ScheduledTask, TaskType, ScheduleType
from application.repositories.scheduled_task_repository import ScheduledTaskRepository


@pytest.mark.unit
@pytest.mark.asyncio
class TestScheduledTaskRepository:
    """Test cases for ScheduledTaskRepository."""

    async def test_create_interval_task(self, db, sample_organization):
        """Test creating an interval-based scheduled task."""
        repo = ScheduledTaskRepository()

        task = await repo.create(
            organization_id=sample_organization.id,
            name="Test Interval Task",
            task_type=TaskType.RACETIME_OPEN_ROOM,
            schedule_type=ScheduleType.INTERVAL,
            description="A test interval task",
            interval_seconds=300,  # 5 minutes
            task_config={"category": "alttpr", "goal": "Beat the game"},
            is_active=True,
        )

        assert task.id is not None
        assert task.name == "Test Interval Task"
        assert task.task_type == TaskType.RACETIME_OPEN_ROOM
        assert task.schedule_type == ScheduleType.INTERVAL
        assert task.interval_seconds == 300
        assert task.is_active is True

    async def test_create_cron_task(self, db, sample_organization):
        """Test creating a cron-based scheduled task."""
        repo = ScheduledTaskRepository()

        task = await repo.create(
            organization_id=sample_organization.id,
            name="Test Cron Task",
            task_type=TaskType.CUSTOM,
            schedule_type=ScheduleType.CRON,
            cron_expression="0 14 * * *",  # Daily at 2pm
            task_config={},
            is_active=True,
        )

        assert task.id is not None
        assert task.cron_expression == "0 14 * * *"
        assert task.schedule_type == ScheduleType.CRON

    async def test_create_onetime_task(self, db, sample_organization):
        """Test creating a one-time scheduled task."""
        repo = ScheduledTaskRepository()
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)

        task = await repo.create(
            organization_id=sample_organization.id,
            name="Test One-Time Task",
            task_type=TaskType.RACETIME_OPEN_ROOM,
            schedule_type=ScheduleType.ONE_TIME,
            scheduled_time=future_time,
            task_config={"category": "alttpr"},
            is_active=True,
        )

        assert task.id is not None
        assert task.schedule_type == ScheduleType.ONE_TIME
        assert task.scheduled_time == future_time

    async def test_get_by_id(self, db, sample_organization):
        """Test retrieving a task by ID."""
        repo = ScheduledTaskRepository()

        created_task = await repo.create(
            organization_id=sample_organization.id,
            name="Test Task",
            task_type=TaskType.CUSTOM,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=60,
        )

        retrieved_task = await repo.get_by_id(created_task.id)

        assert retrieved_task is not None
        assert retrieved_task.id == created_task.id
        assert retrieved_task.name == "Test Task"

    async def test_get_by_id_not_found(self, db, sample_organization):
        """Test retrieving a non-existent task."""
        repo = ScheduledTaskRepository()

        task = await repo.get_by_id(99999)

        assert task is None

    async def test_list_by_org(self, db, sample_organization):
        """Test listing tasks by organization."""
        repo = ScheduledTaskRepository()

        # Create second organization for testing
        from models.organizations import Organization

        org2 = await Organization.create(name="Test Org 2", slug="test-org-2")

        # Create tasks for different orgs
        await repo.create(
            organization_id=sample_organization.id,
            name="Org 1 Task 1",
            task_type=TaskType.CUSTOM,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=60,
        )
        await repo.create(
            organization_id=sample_organization.id,
            name="Org 1 Task 2",
            task_type=TaskType.CUSTOM,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=120,
        )
        await repo.create(
            organization_id=org2.id,
            name="Org 2 Task 1",
            task_type=TaskType.CUSTOM,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=180,
        )

        org1_tasks = await repo.list_by_org(organization_id=sample_organization.id)
        org2_tasks = await repo.list_by_org(organization_id=org2.id)

        assert len(org1_tasks) == 2
        assert len(org2_tasks) == 1

    async def test_list_active_tasks(self, db, sample_organization):
        """Test listing only active tasks."""
        repo = ScheduledTaskRepository()

        await repo.create(
            organization_id=sample_organization.id,
            name="Active Task",
            task_type=TaskType.CUSTOM,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=60,
            is_active=True,
        )
        await repo.create(
            organization_id=sample_organization.id,
            name="Inactive Task",
            task_type=TaskType.CUSTOM,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=60,
            is_active=False,
        )

        active_tasks = await repo.list_by_org(
            organization_id=sample_organization.id, active_only=True
        )

        assert len(active_tasks) == 1
        assert active_tasks[0].name == "Active Task"

    async def test_update_task(self, db, sample_organization):
        """Test updating a task."""
        repo = ScheduledTaskRepository()

        task = await repo.create(
            organization_id=sample_organization.id,
            name="Original Name",
            task_type=TaskType.CUSTOM,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=60,
        )

        updated_task = await repo.update(
            task_id=task.id,
            name="Updated Name",
            interval_seconds=120,
        )

        assert updated_task is not None
        assert updated_task.name == "Updated Name"
        assert updated_task.interval_seconds == 120

    async def test_delete_task(self, db, sample_organization):
        """Test deleting a task."""
        repo = ScheduledTaskRepository()

        task = await repo.create(
            organization_id=sample_organization.id,
            name="Task to Delete",
            task_type=TaskType.CUSTOM,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=60,
        )

        success = await repo.delete(task.id)
        assert success is True

        deleted_task = await repo.get_by_id(task.id)
        assert deleted_task is None

    async def test_update_run_status(self, db, sample_organization):
        """Test updating task run status."""
        repo = ScheduledTaskRepository()

        task = await repo.create(
            organization_id=sample_organization.id,
            name="Test Task",
            task_type=TaskType.CUSTOM,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=60,
        )

        now = datetime.now(timezone.utc)
        next_run = now + timedelta(seconds=60)

        updated_task = await repo.update_run_status(
            task_id=task.id,
            status="success",
            last_run_at=now,
            next_run_at=next_run,
        )

        assert updated_task is not None
        assert updated_task.last_run_status == "success"
        assert updated_task.last_run_at is not None
        assert updated_task.next_run_at == next_run

    async def test_list_tasks_due_to_run(self, db, sample_organization):
        """Test listing tasks due to run."""
        repo = ScheduledTaskRepository()
        now = datetime.now(timezone.utc)

        # Task due to run now
        task1 = await repo.create(
            organization_id=sample_organization.id,
            name="Due Now",
            task_type=TaskType.CUSTOM,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=60,
        )
        await repo.update(task1.id, next_run_at=now - timedelta(seconds=10))

        # Task due to run in the future
        task2 = await repo.create(
            organization_id=sample_organization.id,
            name="Due Later",
            task_type=TaskType.CUSTOM,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=60,
        )
        await repo.update(task2.id, next_run_at=now + timedelta(hours=1))

        due_tasks = await repo.list_tasks_due_to_run(now)

        assert len(due_tasks) == 1
        assert due_tasks[0].name == "Due Now"
