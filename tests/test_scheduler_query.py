#!/usr/bin/env python3
"""Test script to check task scheduling."""
import asyncio
from datetime import datetime, timezone, timedelta
from database import init_db, close_db
from models.scheduled_task import ScheduledTask, TaskType, ScheduleType
from application.repositories.scheduled_task_repository import ScheduledTaskRepository


async def test():
    """Test task scheduling."""
    await init_db()

    # Check the existing task
    task = await ScheduledTask.get_or_none(id=1)
    if task:
        print(f"Task: {task.name}")
        print(f"Active: {task.is_active}")
        print(f"Next run: {task.next_run_at}")
        print(f"Now: {datetime.now(timezone.utc)}")

        if task.next_run_at:
            diff = task.next_run_at - datetime.now(timezone.utc)
            print(f"Time until next run: {diff}")
            print(f"Is overdue: {task.next_run_at <= datetime.now(timezone.utc)}")

    # Test the query
    repo = ScheduledTaskRepository()
    now = datetime.now(timezone.utc)
    due = await repo.list_tasks_due_to_run(now)
    print(f"\nTasks due to run: {len(due)}")

    await close_db()


if __name__ == "__main__":
    asyncio.run(test())
