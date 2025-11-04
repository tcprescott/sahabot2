#!/usr/bin/env python3
"""Test script to simulate scheduler execution."""
import asyncio
import logging
from datetime import datetime, timezone
from database import init_db, close_db
from application.services.task_scheduler_service import TaskSchedulerService
from application.services.task_handlers import register_task_handlers
from application.services.builtin_tasks import get_active_builtin_tasks

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_scheduler():
    """Test if scheduler logic works."""
    await init_db()
    
    print("\n" + "="*80)
    print("TESTING SCHEDULER LOGIC")
    print("="*80 + "\n")
    
    # Register handlers
    print("Registering task handlers...")
    register_task_handlers()
    
    # Check handlers
    handlers = TaskSchedulerService._task_handlers
    print(f"Registered handlers: {len(handlers)}")
    for task_type, handler in handlers.items():
        print(f"  {task_type.name}: {handler.__name__}")
    print()
    
    # Get built-in tasks
    builtin_tasks = get_active_builtin_tasks()
    print(f"Active built-in tasks: {len(builtin_tasks)}")
    
    # Check if they should run
    now = datetime.now(timezone.utc)
    for task in builtin_tasks:
        should_run = TaskSchedulerService._should_run_builtin_task(task, now)
        print(f"  {task.name}: should_run={should_run}")
        
        # Get the last run info
        last_run = TaskSchedulerService._builtin_tasks_last_run.get(task.task_id)
        status = TaskSchedulerService._builtin_tasks_status.get(task.task_id, {})
        print(f"    Last run: {last_run}")
        print(f"    Status: {status}")
        print()
    
    print("\n" + "="*80)
    print("SIMULATING ONE SCHEDULER CYCLE")
    print("="*80 + "\n")
    
    # Simulate one scheduler cycle
    for task in builtin_tasks:
        if TaskSchedulerService._should_run_builtin_task(task, now):
            print(f"Would execute: {task.name}")
            try:
                # Try to execute
                await TaskSchedulerService._execute_builtin_task(task, now)
                print(f"  ✅ Executed successfully")
            except Exception as e:
                print(f"  ❌ Error: {e}")
            print()
    
    # Check status after
    print("\n" + "="*80)
    print("STATUS AFTER EXECUTION")
    print("="*80 + "\n")
    
    builtin_status = TaskSchedulerService.get_builtin_tasks_with_status(active_only=True)
    for task_info in builtin_status:
        print(f"{task_info['name']}:")
        print(f"  Last run: {task_info['last_run_at']}")
        print(f"  Last status: {task_info['last_status']}")
        print(f"  Next run: {task_info['next_run_at']}")
        if task_info['last_error']:
            print(f"  Error: {task_info['last_error']}")
        print()
    
    await close_db()

if __name__ == "__main__":
    asyncio.run(test_scheduler())
