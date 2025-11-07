# Built-in Tasks System

## Overview

SahaBot2 supports two types of scheduled tasks:

1. **Database Tasks**: Stored in the database, created and managed through the UI or API
2. **Built-in Tasks**: Defined in code, loaded automatically at startup

Built-in tasks provide a way to define system-level automation that should always run without requiring manual setup or database configuration.

## Key Concepts

### Built-in Tasks

Built-in tasks are:
- **Defined in code** (`application/services/builtin_tasks.py`)
- **Loaded at application startup** (no database entry required)
- **Global by default** (not scoped to any organization)
- **Read-only in the UI** (cannot be edited or deleted through the interface)
- **Always available** (no risk of accidental deletion)

### Global Tasks

Tasks (both built-in and database) can be global or organization-scoped:
- **Global tasks**: Run for the entire system (organization_id = None)
- **Organization tasks**: Run for a specific organization

## Creating Built-in Tasks

### 1. Define the Task

Edit `application/services/builtin_tasks.py` and add your task to the `BUILTIN_TASKS` dictionary:

```python
'my_task_id': BuiltInTask(
    task_id='my_task_id',                    # Unique identifier
    name='My Custom Task',                   # Display name
    description='What this task does',       # Description
    task_type=TaskType.CUSTOM,              # Task type enum
    schedule_type=ScheduleType.CRON,        # How it's scheduled
    is_global=True,                         # Global or org-scoped
    cron_expression='0 2 * * *',            # Schedule (e.g., daily at 2 AM)
    task_config={                           # Task-specific config
        'param1': 'value1',
        'param2': 42,
    },
    is_active=True,                         # Enable/disable
),
```

### 2. Create a Task Handler

Add a handler function in `application/services/task_handlers.py`:

```python
async def handle_my_task(task: ScheduledTask) -> None:
    """
    Handler for my custom task.
    
    Args:
        task: ScheduledTask to execute (may be built-in or database task)
    """
    logger.info("Running my task: %s", task.name)
    
    # Access configuration
    config = task.task_config or {}
    param1 = config.get('param1')
    
    # Your task logic here
    # ...
    
    logger.info("My task completed successfully")
```

### 3. Register the Handler

In `task_handlers.py`, register your handler in `register_task_handlers()`:

```python
def register_task_handlers() -> None:
    """Register all task handlers."""
    # ... existing handlers ...
    TaskSchedulerService.register_task_handler(TaskType.MY_TASK_TYPE, handle_my_task)
    logger.info("All task handlers registered")
```

### 4. Restart the Application

Built-in tasks are loaded at startup, so restart the app to activate your new task.

## Built-in Task Configuration

### BuiltInTask Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | str | Yes | Unique identifier (used internally) |
| `name` | str | Yes | Human-readable name |
| `description` | str | Yes | Task description |
| `task_type` | TaskType | Yes | Type of task (enum) |
| `schedule_type` | ScheduleType | Yes | Scheduling method |
| `is_global` | bool | No | If True, task is global (default: True) |
| `interval_seconds` | int | Conditional | Required for INTERVAL schedule |
| `cron_expression` | str | Conditional | Required for CRON schedule |
| `task_config` | dict | No | Task-specific configuration |
| `is_active` | bool | No | Enable/disable task (default: True) |

### Schedule Types

#### INTERVAL
Run at regular intervals:
```python
schedule_type=ScheduleType.INTERVAL,
interval_seconds=3600,  # Every hour
```

#### CRON
Run at specific times (cron expression):
```python
schedule_type=ScheduleType.CRON,
cron_expression='0 3 * * *',  # Daily at 3 AM UTC
```

Common cron expressions:
- `'0 * * * *'` - Every hour
- `'0 0 * * *'` - Daily at midnight
- `'0 2 * * *'` - Daily at 2 AM
- `'0 0 * * 0'` - Weekly on Sunday at midnight
- `'0 0 1 * *'` - Monthly on the 1st at midnight

#### ONE_TIME
Not typically used for built-in tasks (used for database tasks).

## Example: System Cleanup Task

Here's the built-in tournament usage cleanup task as an example:

```python
'cleanup_tournament_usage': BuiltInTask(
    task_id='cleanup_tournament_usage',
    name='Tournament Usage Cleanup',
    description='Automatically cleans up old tournament usage tracking data',
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
```

## Managing Built-in Tasks

### Viewing Built-in Tasks

Built-in tasks appear in the admin task list marked as `[Built-in]`.

Through the API:
```python
from application.services.task_scheduler_service import TaskSchedulerService

service = TaskSchedulerService()
all_tasks = await service.list_all_tasks_with_builtin(
    user=current_user,
    organization_id=None,  # Global tasks
    include_builtin=True
)

print(f"Database tasks: {len(all_tasks['database'])}")
print(f"Built-in tasks: {len(all_tasks['builtin'])}")
```

### Modifying Built-in Tasks

To modify a built-in task:
1. Edit `application/services/builtin_tasks.py`
2. Update the task definition
3. Restart the application

### Disabling Built-in Tasks

Built-in tasks can be disabled in two ways:

#### Option 1: Database Override (Recommended - Persists Across Restarts)

**Via Admin UI:**
1. Navigate to Admin → Scheduled Tasks
2. Find the built-in task in the "Built-in Tasks" section
3. Click the "Disable" button
4. The task will be disabled immediately and remain disabled after restarts

**Via Service:**
```python
from application.services.tasks.task_scheduler_service import TaskSchedulerService

service = TaskSchedulerService()

# Disable a built-in task (requires admin user)
await service.set_builtin_task_active(
    user=admin_user,
    task_id='cleanup_tournament_usage',
    is_active=False
)

# Re-enable it
await service.set_builtin_task_active(
    user=admin_user,
    task_id='cleanup_tournament_usage',
    is_active=True
)
```

Database overrides are stored in the `builtin_task_overrides` table and persist across application restarts. When an override exists, it takes precedence over the `is_active` value defined in code.

#### Option 2: Code Change (Temporary - Resets on Code Update)

To disable in code (not recommended for production):
```python
'my_task_id': BuiltInTask(
    # ... other parameters ...
    is_active=False,  # Disable the task
),
```

**Note:** Code-based disabling is reset whenever the code is updated or deployed. Use database overrides for persistent changes.

### Removing Built-in Tasks

To permanently remove a built-in task:
1. Remove it from the `BUILTIN_TASKS` dictionary in `application/services/builtin_tasks.py`
2. Restart the application

## Database Tasks vs Built-in Tasks

### When to Use Built-in Tasks

✅ **Use built-in tasks for:**
- System-level maintenance (cleanup, backups, etc.)
- Tasks that should always run
- Critical automation that shouldn't be accidentally deleted
- Tasks that don't need runtime configuration
- Tasks shared across all organizations

### When to Use Database Tasks

✅ **Use database tasks for:**
- Organization-specific automation
- Tasks created by admins/users
- Tasks that need frequent reconfiguration
- Temporary or experimental tasks
- Tasks with organization-specific schedules

### Feature Comparison

| Feature | Built-in Tasks | Database Tasks |
|---------|---------------|----------------|
| **Storage** | Code (in-memory) | Database |
| **Scope** | Global only* | Per-org or global |
| **Configuration** | Code changes + restart | UI/API (immediate) |
| **Management** | Read-only in UI | Full CRUD in UI |
| **Persistence** | Always loaded | Database-dependent |
| **Security** | Cannot be deleted | Can be deleted |
| **Visibility** | All admins | Per-organization |
| **Use Case** | System automation | User/org automation |

\* Built-in tasks can technically be org-scoped, but typically used for global tasks.

## Global Tasks

### Creating Global Database Tasks

Admins (ADMIN or SUPERADMIN permission) can create global database tasks:

```python
from application.services.task_scheduler_service import TaskSchedulerService
from models.scheduled_task import TaskType, ScheduleType

service = TaskSchedulerService()
task = await service.create_task(
    user=admin_user,
    organization_id=None,  # None = global
    name="Global Cleanup Task",
    task_type=TaskType.CUSTOM,
    schedule_type=ScheduleType.CRON,
    cron_expression="0 4 * * *",
    task_config={"param": "value"},
    is_active=True,
)
```

### Authorization

| Action | Organization Task | Global Task | Built-in Task Override |
|--------|------------------|-------------|------------------------|
| **Create** | Tournament manager | Superadmin only | N/A |
| **View** | Tournament manager | Superadmin only | Admin |
| **Update** | Tournament manager | Superadmin only | N/A |
| **Delete** | Tournament manager | Superadmin only | N/A |
| **Toggle Active** | N/A | N/A | Admin |
| **Execute** | Automatic | Automatic | Automatic (if active) |

## Built-in Task Overrides

### Overview

Built-in task overrides allow administrators to disable built-in tasks without modifying code. Overrides are stored in the `builtin_task_overrides` database table and persist across application restarts.

### How Overrides Work

1. **Default Behavior**: By default, a built-in task's active status is determined by its `is_active` value in `builtin_tasks.py`
2. **Override Created**: When an admin disables/enables a task via UI or API, an override is created in the database
3. **Override Applied**: The scheduler checks for overrides before running tasks
4. **Precedence**: Database override takes precedence over code-defined `is_active` value
5. **Cache**: Overrides are cached in memory for performance and reloaded at scheduler startup

### Database Schema

```sql
CREATE TABLE builtin_task_overrides (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Managing Overrides

**Via Service:**
```python
from application.services.tasks.task_scheduler_service import TaskSchedulerService

service = TaskSchedulerService()

# Set active status (creates or updates override)
await service.set_builtin_task_active(
    user=admin_user,
    task_id='cleanup_tournament_usage',
    is_active=False  # Disable the task
)

# Check effective active status
effective_status = TaskSchedulerService.get_effective_active_status(
    task_id='cleanup_tournament_usage',
    default_is_active=True  # From code definition
)
# Returns False if override exists with is_active=False
# Returns True if no override exists

# Reload overrides from database (e.g., after external changes)
await TaskSchedulerService.reload_builtin_task_overrides()
```

**Via Repository:**
```python
from application.repositories.builtin_task_override_repository import BuiltinTaskOverrideRepository

repo = BuiltinTaskOverrideRepository()

# Create override
override = await repo.create(task_id='my_task', is_active=False)

# Get override
override = await repo.get_by_task_id('my_task')

# Update or create
override = await repo.set_active('my_task', True)

# Get all as dict
overrides = await repo.get_overrides_dict()
# Returns: {'task_1': True, 'task_2': False, ...}

# Delete override (task reverts to code-defined is_active)
await repo.delete('my_task')
```

### Lifecycle

1. **Startup**: Scheduler loads all overrides from database into memory cache
2. **Runtime**: Scheduler checks cache for overrides when determining if task should run
3. **Toggle**: Admin toggles task via UI/API, override saved to database and updated in cache
4. **Restart**: Overrides persist in database and are reloaded into cache

### Use Cases

- **Temporarily disable problematic task** without deploying code changes
- **Enable/disable tasks per environment** (dev vs prod) without code changes
- **Quick response to incidents** - disable task immediately without waiting for deployment
- **Testing** - disable tasks during system maintenance or testing
- **Gradual rollout** - disable new tasks by default in code, enable via override after verification

## Task Execution

### Execution Flow

1. **Scheduler loop** runs every 10 seconds
2. **Load overrides** (at startup - cached in memory)
3. **Checks database tasks** due to run
4. **Checks built-in tasks** due to run
   - Applies database overrides to determine effective `is_active` status
   - Only executes tasks where effective status is `True`
5. **Executes tasks** in background (async)
6. **Updates state** (database tasks only)
7. **Logs results** for monitoring

### Built-in Task Execution

For built-in tasks:
- **Active status** determined by database override if exists, otherwise code-defined `is_active`
- Last run time tracked in memory (`_builtin_tasks_last_run`)
- No database updates for execution state (since not stored in database)
- Next run calculated from schedule definition
- Execution state lost on application restart (tasks will run as if never executed)
- **Overrides persist** across restarts (stored in database)

### Pseudo-Task Object

Built-in tasks are wrapped in a `PseudoTask` object when executed to provide a compatible interface with database tasks:

```python
class PseudoTask:
    id = "builtin:task_id"
    name = "Task Name"
    description = "Description"
    task_type = TaskType.CUSTOM
    schedule_type = ScheduleType.CRON
    task_config = {...}
    organization_id = None
    is_builtin = True
```

Task handlers receive this object and can check `is_builtin` attribute if needed.

## Monitoring

### Logs

Built-in task execution is logged:

```
INFO: Executing built-in task: Tournament Usage Cleanup
INFO: Starting tournament usage cleanup task: Tournament Usage Cleanup
INFO: Cleaned up 23 entries older than 90 days
INFO: Cleaned up 12 excess entries (keeping 10 per user)
INFO: Built-in task cleanup_tournament_usage executed successfully
```

### Health Checks

To verify built-in tasks are loaded:

```python
from application.services.builtin_tasks import get_all_builtin_tasks

tasks = get_all_builtin_tasks()
for task in tasks:
    print(f"{task.task_id}: {task.name} ({'active' if task.is_active else 'inactive'})")
```

## Best Practices

1. **Use descriptive task_id**: Choose clear, unique identifiers (e.g., `cleanup_old_logs`, not `task1`)

2. **Document configuration**: Add comments explaining `task_config` parameters

3. **Set appropriate schedules**: Avoid running resource-intensive tasks during peak hours

4. **Handle errors gracefully**: Built-in task failures are logged but don't affect other tasks

5. **Test before deploying**: Test task handlers independently before adding to built-in tasks

6. **Monitor execution**: Check logs regularly to ensure tasks run as expected

7. **Use global tasks sparingly**: Only for truly system-wide automation

8. **Prefer database tasks for user-facing features**: Gives users control without code changes

## Migration from Database Tasks

To convert an existing database task to built-in:

1. **Define the built-in task** in `builtin_tasks.py` with the same configuration
2. **Test the built-in task** in a development environment
3. **Deploy the code** with the new built-in task
4. **Disable or delete** the database task
5. **Verify** the built-in task is running

## Troubleshooting

### Built-in Task Not Running

**Check:**
- Is `is_active=True`?
- Is the task scheduler started?
- Are task handlers registered?
- Check application logs for errors

**Debug:**
```python
from application.services.builtin_tasks import get_builtin_task

task = get_builtin_task('my_task_id')
if task:
    print(f"Task found: {task.name}")
    print(f"Active: {task.is_active}")
    print(f"Schedule: {task.cron_expression or task.interval_seconds}")
else:
    print("Task not found!")
```

### Task Runs Too Often/Rarely

**Fix schedule:**
- For INTERVAL: Check `interval_seconds` value
- For CRON: Verify cron expression using [crontab.guru](https://crontab.guru/)

### Task Configuration Not Updating

**Remember:** Built-in tasks require application restart to pick up changes.

1. Edit `builtin_tasks.py`
2. Save changes
3. **Restart the application** ← Don't forget this!

## API Reference

See `application/services/builtin_tasks.py` for:
- `BuiltInTask` class
- `get_builtin_task(task_id)` - Get single task
- `get_all_builtin_tasks()` - Get all tasks
- `get_active_builtin_tasks()` - Get active tasks only
