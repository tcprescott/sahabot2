#!/usr/bin/env python3
"""
Diagnostic script to check scheduled task system status.

Usage: poetry run python check_scheduler.py
"""
import asyncio
import logging
from datetime import datetime, timezone

from database import init_db, close_db
from application.services.tasks.task_scheduler_service import TaskSchedulerService
from application.repositories.scheduled_task_repository import ScheduledTaskRepository
from application.services.tasks.builtin_tasks import get_all_builtin_tasks, get_active_builtin_tasks
from application.services.tasks.task_handlers import register_task_handlers
from models.scheduled_task import ScheduledTask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def check_scheduler():
    """Check scheduler status and list tasks."""
    print("\n" + "="*80)
    print("SCHEDULER STATUS CHECK")
    print("="*80 + "\n")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Register task handlers (simulating app startup)
    register_task_handlers()
    logger.info("Task handlers registered")
    
    try:
        # Check if scheduler is running
        is_running = TaskSchedulerService.is_running()
        print(f"Scheduler Running: {is_running}")
        print()
        
        # Get repository
        repo = ScheduledTaskRepository()
        
        # Get all database tasks
        all_tasks = await ScheduledTask.all()
        print(f"Total Database Tasks: {len(all_tasks)}")
        
        # Get active database tasks
        active_tasks = await repo.list_active_tasks()
        print(f"Active Database Tasks: {len(active_tasks)}")
        print()
        
        # Get tasks due to run
        now = datetime.now(timezone.utc)
        due_tasks = await repo.list_tasks_due_to_run(now)
        print(f"Tasks Due to Run (as of {now}): {len(due_tasks)}")
        print()
        
        # List all database tasks with details
        if all_tasks:
            print("\n" + "-"*80)
            print("DATABASE TASKS:")
            print("-"*80)
            for task in all_tasks:
                print(f"\nTask ID: {task.id}")
                print(f"  Name: {task.name}")
                print(f"  Type: {task.task_type.name}")
                print(f"  Schedule: {task.schedule_type.name}")
                if task.interval_seconds:
                    print(f"  Interval: {task.interval_seconds}s")
                if task.cron_expression:
                    print(f"  Cron: {task.cron_expression}")
                if task.scheduled_time:
                    print(f"  Scheduled Time: {task.scheduled_time}")
                print(f"  Organization ID: {task.organization_id}")
                print(f"  Active: {task.is_active}")
                print(f"  Last Run: {task.last_run_at or 'Never'}")
                print(f"  Next Run: {task.next_run_at or 'Not set'}")
                print(f"  Last Status: {task.last_run_status or 'N/A'}")
                if task.last_run_error:
                    print(f"  Last Error: {task.last_run_error}")
                print(f"  Created: {task.created_at}")
        else:
            print("\nNo database tasks found.")
        
        # Get built-in tasks
        all_builtin = get_all_builtin_tasks()
        active_builtin = get_active_builtin_tasks()
        
        print("\n" + "-"*80)
        print("BUILT-IN TASKS:")
        print("-"*80)
        print(f"Total Built-in Tasks: {len(all_builtin)}")
        print(f"Active Built-in Tasks: {len(active_builtin)}")
        
        if all_builtin:
            builtin_status = TaskSchedulerService.get_builtin_tasks_with_status()
            for task_info in builtin_status:
                print(f"\nTask ID: {task_info['task_id']}")
                print(f"  Name: {task_info['name']}")
                print(f"  Type: {task_info['task_type'].name}")
                print(f"  Schedule: {task_info['schedule_type'].name}")
                if task_info['interval_seconds']:
                    print(f"  Interval: {task_info['interval_seconds']}s")
                if task_info['cron_expression']:
                    print(f"  Cron: {task_info['cron_expression']}")
                print(f"  Active: {task_info['is_active']}")
                print(f"  Last Run: {task_info['last_run_at'] or 'Never'}")
                print(f"  Next Run: {task_info['next_run_at'] or 'Not calculated'}")
                print(f"  Last Status: {task_info['last_status'] or 'N/A'}")
                if task_info['last_error']:
                    print(f"  Last Error: {task_info['last_error']}")
        
        # Check registered handlers
        print("\n" + "-"*80)
        print("REGISTERED TASK HANDLERS:")
        print("-"*80)
        handlers = TaskSchedulerService._task_handlers
        if handlers:
            for task_type, handler in handlers.items():
                print(f"  {task_type.name}: {handler.__name__}")
        else:
            print("  No handlers registered!")
            print("  WARNING: This will prevent tasks from executing.")
        
        print("\n" + "="*80)
        print("DIAGNOSIS:")
        print("="*80)
        
        issues = []
        
        if not handlers:
            issues.append("❌ No task handlers registered - tasks cannot execute")
        
        if not is_running:
            issues.append("❌ Scheduler is not running - tasks will not be checked")
        
        if active_tasks or active_builtin:
            if is_running and handlers:
                print("✅ Scheduler is running and handlers are registered")
                print(f"✅ {len(active_tasks)} active database task(s)")
                print(f"✅ {len(active_builtin)} active built-in task(s)")
            else:
                issues.append(f"⚠️  {len(active_tasks) + len(active_builtin)} active tasks, but scheduler may not execute them")
        else:
            print("ℹ️  No active tasks to run")
        
        if due_tasks and is_running and handlers:
            print(f"⚠️  {len(due_tasks)} task(s) are overdue and should run soon")
        
        if issues:
            print("\nISSUES FOUND:")
            for issue in issues:
                print(f"  {issue}")
        
        print()
        
    finally:
        await close_db()
        logger.info("Database closed")


if __name__ == "__main__":
    asyncio.run(check_scheduler())
