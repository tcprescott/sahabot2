# Task Scheduler System

The task scheduler system provides automated task execution at scheduled intervals or specific times. This document describes the architecture, usage, and extension points.

## Overview

The task scheduler allows organizations to automate recurring tasks such as:
- Opening race rooms on racetime.gg at scheduled times
- Running custom automation tasks
- Periodic maintenance operations

Tasks are organization-scoped, ensuring multi-tenant isolation, and can be scheduled in three ways:
1. **Interval-based**: Execute every N seconds/minutes/hours
2. **Cron-based**: Execute at specific times using cron expressions
3. **One-time**: Execute once at a specific datetime

## Architecture

### Components

1. **Model** (`models/scheduled_task.py`)
   - `ScheduledTask`: Database model for tasks
   - `TaskType`: Enum for task types (RACETIME_OPEN_ROOM, CUSTOM)
   - `ScheduleType`: Enum for schedule types (INTERVAL, CRON, ONE_TIME)

2. **Repository** (`application/repositories/scheduled_task_repository.py`)
   - Data access layer for scheduled tasks
   - CRUD operations
   - Query methods for finding tasks due to run

3. **Service** (`application/services/task_scheduler_service.py`)
   - Business logic for task management
   - Authorization checks (organization-scoped)
   - Background scheduler implementation
   - Task execution orchestration

4. **Task Handlers** (`application/services/task_handlers.py`)
   - Pluggable handlers for different task types
   - Registration system for extending task types

5. **API Routes** (`api/routes/scheduled_tasks.py`)
   - RESTful endpoints for task management
   - OpenAPI/Swagger documentation

6. **UI View** (`views/organization/scheduled_tasks.py`)
   - Organization admin page integration
   - Task list and management interface

## Database Schema

```sql
CREATE TABLE scheduled_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    organization_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type SMALLINT NOT NULL,
    schedule_type SMALLINT NOT NULL,
    interval_seconds INT NULL,
    cron_expression VARCHAR(255) NULL,
    scheduled_time DATETIME NULL,
    task_config JSON NOT NULL,
    is_active BOOL DEFAULT TRUE,
    last_run_at DATETIME NULL,
    next_run_at DATETIME NULL,
    last_run_status VARCHAR(50) NULL,
    last_run_error TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by_id INT NULL,
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES user(id) ON DELETE SET NULL,
    INDEX idx_org_active (organization_id, is_active),
    INDEX idx_next_run_active (next_run_at, is_active)
);
```

## Usage

### Creating a Scheduled Task (API)

**Interval-based task (every 5 minutes):**
```bash
POST /api/scheduled-tasks/organizations/{organization_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "Open Race Room Every 5 Minutes",
  "description": "Opens an ALTTPR race room every 5 minutes",
  "task_type": 1,
  "schedule_type": 1,
  "interval_seconds": 300,
  "task_config": {
    "category": "alttpr",
    "goal": "Beat the game",
    "info": "Automated race room"
  },
  "is_active": true
}
```

**Cron-based task (daily at 2 PM UTC):**
```bash
POST /api/scheduled-tasks/organizations/{organization_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "Daily Race at 2 PM",
  "description": "Opens a race room daily at 2 PM UTC",
  "task_type": 1,
  "schedule_type": 2,
  "cron_expression": "0 14 * * *",
  "task_config": {
    "category": "alttpr",
    "goal": "Beat the game"
  },
  "is_active": true
}
```

**One-time task:**
```bash
POST /api/scheduled-tasks/organizations/{organization_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "Special Event Race",
  "description": "One-time race for special event",
  "task_type": 1,
  "schedule_type": 3,
  "scheduled_time": "2025-11-15T20:00:00Z",
  "task_config": {
    "category": "alttpr",
    "goal": "Special Event Seed"
  },
  "is_active": true
}
```

### Creating a Task (UI)

1. Navigate to Admin → Organizations → {Your Organization}
2. Click "Scheduled Tasks" in the sidebar
3. Click "Create Task"
4. Fill in the task details
5. Click "Save"

### Managing Tasks

**List tasks:**
```bash
GET /api/scheduled-tasks/organizations/{organization_id}
Authorization: Bearer {token}
```

**Get a specific task:**
```bash
GET /api/scheduled-tasks/organizations/{organization_id}/tasks/{task_id}
Authorization: Bearer {token}
```

**Update a task:**
```bash
PATCH /api/scheduled-tasks/organizations/{organization_id}/tasks/{task_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "is_active": false,
  "interval_seconds": 600
}
```

**Delete a task:**
```bash
DELETE /api/scheduled-tasks/organizations/{organization_id}/tasks/{task_id}
Authorization: Bearer {token}
```

## Extending the Scheduler

### Adding a New Task Type

1. **Define the task type enum:**

```python
# In models/scheduled_task.py
class TaskType(IntEnum):
    RACETIME_OPEN_ROOM = 1
    CUSTOM = 99
    MY_NEW_TASK = 100  # Add your task type
```

2. **Create a task handler:**

```python
# In application/services/task_handlers.py
async def handle_my_new_task(task: ScheduledTask) -> None:
    """
    Handler for my new task type.
    
    Args:
        task: ScheduledTask to execute
    """
    logger.info("Executing my new task: %s", task.name)
    
    # Extract configuration
    config = task.task_config or {}
    
    # Your task logic here
    # ...
    
    logger.info("My new task completed successfully")
```

3. **Register the handler:**

```python
# In application/services/task_handlers.py
def register_task_handlers() -> None:
    """Register all task handlers."""
    TaskSchedulerService.register_task_handler(TaskType.RACETIME_OPEN_ROOM, handle_racetime_open_room)
    TaskSchedulerService.register_task_handler(TaskType.CUSTOM, handle_custom_task)
    TaskSchedulerService.register_task_handler(TaskType.MY_NEW_TASK, handle_my_new_task)
    logger.info("All task handlers registered")
```

## How the Scheduler Works

### Lifecycle

1. **Startup** (`main.py`):
   - Task handlers are registered via `register_task_handlers()`
   - Scheduler starts via `TaskSchedulerService.start_scheduler()`
   - Background task runner begins polling for due tasks

2. **Runtime**:
   - Scheduler polls every 10 seconds for tasks where `next_run_at <= current_time` and `is_active = true`
   - For each due task:
     - Task status set to 'running'
     - Appropriate handler executed based on `task_type`
     - On success: status set to 'success', next_run_at calculated
     - On failure: status set to 'failed', error logged
   - One-time tasks are deactivated after successful execution

3. **Shutdown** (`main.py`):
   - Scheduler stops via `TaskSchedulerService.stop_scheduler()`
   - Background task runner gracefully terminates

### Next Run Time Calculation

- **INTERVAL**: `current_time + interval_seconds`
- **CRON**: Next matching time based on cron expression (using croniter)
- **ONE_TIME**: Only runs once; no next_run_at after execution

## Authorization

All task operations require organization membership and tournament management permissions:
- Users must be members of the organization
- Users must have tournament management permissions (same as tournament creation)
- SUPERADMIN and ADMIN can manage all tasks

## Rate Limiting

API endpoints are rate-limited per-user (default: 60 requests per minute).

## Error Handling

- Invalid cron expressions are rejected at creation time
- Missing required schedule parameters (e.g., interval_seconds for INTERVAL type) return validation errors
- Task execution errors are logged in `last_run_error` and do not stop the scheduler
- Unauthorized operations return empty results (service layer) or 403 errors (API)

## Monitoring

Task execution status is tracked in the database:
- `last_run_at`: When the task last executed
- `last_run_status`: 'success', 'failed', or 'running'
- `last_run_error`: Error message if execution failed
- `next_run_at`: When the task will run next

View task status in the UI or query via API.

## Performance Considerations

- The scheduler polls every 10 seconds (configurable in `TaskSchedulerService._run_scheduler`)
- Tasks are executed in background asyncio tasks (non-blocking)
- Database queries are indexed on `(organization_id, is_active)` and `(next_run_at, is_active)`
- For high-frequency tasks, consider using interval-based schedules instead of cron

## Security

- All tasks are organization-scoped (multi-tenant isolation)
- Authorization checked at service layer for all operations
- Task execution is sandboxed per handler
- No user input directly executed; all configuration via structured JSON

## Troubleshooting

**Task not running:**
- Check `is_active` is `true`
- Verify `next_run_at` is set and in the past
- Check logs for execution errors
- Ensure task handler is registered for the task type

**Scheduler not starting:**
- Check application startup logs
- Verify `TaskSchedulerService.start_scheduler()` is called in `main.py`
- Check for exceptions during task handler registration

**Tasks running twice:**
- Ensure only one application instance is running
- Check for clock drift if using distributed systems
- Review `next_run_at` calculation logic

## Future Enhancements

Potential improvements for future versions:
- Task execution history table (audit trail)
- Task retry logic with exponential backoff
- Task dependencies (run task B after task A)
- Task execution timeout limits
- Webhook/notification on task failure
- Task execution dry-run mode
- Bulk task operations
- Task import/export
- Enhanced UI with task creation dialogs
- Real-time task status updates (WebSocket)

## API Reference

See `/docs` (Swagger UI) or `/redoc` for complete API documentation.

## Examples

### Open a Race Room Every Hour

```python
from models.scheduled_task import TaskType, ScheduleType
from application.services.task_scheduler_service import TaskSchedulerService

service = TaskSchedulerService()
task = await service.create_task(
    user=current_user,
    organization_id=1,
    name="Hourly Race Room",
    task_type=TaskType.RACETIME_OPEN_ROOM,
    schedule_type=ScheduleType.INTERVAL,
    interval_seconds=3600,  # 1 hour
    task_config={
        "category": "alttpr",
        "goal": "Beat the game",
        "info": "Hourly race - Good luck!"
    },
    is_active=True,
)
```

### Schedule a Race for a Specific Time

```python
from datetime import datetime, timedelta, timezone

# Schedule a race for tomorrow at 8 PM UTC
tomorrow_8pm = datetime.now(timezone.utc).replace(hour=20, minute=0, second=0, microsecond=0) + timedelta(days=1)

task = await service.create_task(
    user=current_user,
    organization_id=1,
    name="Tomorrow's Special Race",
    task_type=TaskType.RACETIME_OPEN_ROOM,
    schedule_type=ScheduleType.ONE_TIME,
    scheduled_time=tomorrow_8pm,
    task_config={
        "category": "alttpr",
        "goal": "Special Event Seed",
    },
    is_active=True,
)
```

### Weekly Race (Every Sunday at 3 PM)

```python
task = await service.create_task(
    user=current_user,
    organization_id=1,
    name="Weekly Sunday Race",
    task_type=TaskType.RACETIME_OPEN_ROOM,
    schedule_type=ScheduleType.CRON,
    cron_expression="0 15 * * 0",  # Every Sunday at 3 PM (15:00)
    task_config={
        "category": "alttpr",
        "goal": "Beat the game",
    },
    is_active=True,
)
```
