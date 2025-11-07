# Admin Guide: Managing Scheduled Tasks

## Overview

SahaBot2 has a task scheduler that runs automated tasks in the background. As an admin, you can monitor and manage both built-in system tasks and custom database tasks.

## Accessing the Scheduled Tasks Page

1. Log in to SahaBot2 as an admin user
2. Navigate to **Admin** → **Scheduled Tasks**
3. The page shows two sections:
   - **Built-in Tasks**: System tasks defined in code
   - **Global Database Tasks**: User-created global tasks

## Built-in Tasks

Built-in tasks are system-level automation tasks that are defined in the application code. Examples include:

- **Tournament Usage Cleanup**: Removes old tournament usage tracking data
- **Async Tournament Timeout**: Manages timeout logic for async tournament races
- **Score Calculation**: Recalculates tournament scores periodically
- **SpeedGaming Import**: Imports upcoming SpeedGaming episodes
- **Placeholder User Cleanup**: Removes abandoned placeholder users

### Viewing Built-in Task Status

The Built-in Tasks table shows:
- **Name**: Task name
- **Type**: Task type category
- **Schedule**: How often the task runs (e.g., "Every 1h", "Daily at 3 AM")
- **Active**: Whether the task is currently enabled
- **Last Run**: When the task last executed
- **Status**: Success, Failed, or Not Run
- **Next Run**: When the task will run next
- **Actions**: Available operations

### Disabling/Enabling Built-in Tasks

You can temporarily disable a built-in task without modifying code:

1. Find the task in the **Built-in Tasks** section
2. Click the **Disable** button (or **Enable** if already disabled)
3. Confirm the action in the notification
4. The task will immediately stop running

**Key Points:**
- Disabled tasks persist across server restarts
- Changes are stored in the database, not in code
- Only admin users can enable/disable built-in tasks
- Tasks can be re-enabled at any time

### Running a Built-in Task Manually

To execute a task immediately (for testing or urgent needs):

1. Ensure the task is **Active** (enabled)
2. Click the **Run Now** button
3. The task will execute in the background
4. Check the **Last Run** and **Status** columns to verify execution

**Note:** Only active tasks can be run manually.

### Viewing Task Details

To see detailed information about a task:

1. Click the **Details** button for any task
2. A dialog will show:
   - Task ID and description
   - Complete schedule configuration
   - Execution history (last run time, status, errors)
   - Next scheduled run time
   - Any error messages from failed executions

## Global Database Tasks

Global database tasks are user-created tasks that run across the entire system (not scoped to a specific organization).

**Note:** Creating global tasks requires SUPERADMIN permission. Managing built-in tasks only requires ADMIN permission.

## Understanding Task Status

### Active Status Indicators

- **Green Play Icon** (Active): Task is enabled and will run on schedule
- **Gray Pause Icon** (Inactive): Task is disabled and will not run

### Execution Status Indicators

- **Green Check** (Success): Last execution completed successfully
- **Red Error** (Failed): Last execution encountered an error
- **Gray Clock** (Not Run): Task has never executed yet

### Last Run / Next Run

- **Last Run**: Shows relative time (e.g., "2 hours ago", "Yesterday")
- **Next Run**: Shows when the task will run next (e.g., "in 3 hours", "Tomorrow")

## Task Scheduler Status

At the top of the page, you'll see:
- **Task Scheduler: Running** (green) - Scheduler is active and processing tasks
- **Task Scheduler: Stopped** (red) - Scheduler is not running (contact support)

## Common Administrative Tasks

### Temporarily Disable a Problematic Task

If a task is causing issues:

1. Locate the task in the list
2. Click **Disable** to stop it immediately
3. Investigate the issue using the **Details** dialog
4. Fix the underlying problem
5. Click **Enable** to resume the task

### Check Why a Task Failed

1. Find the failed task (red error icon in Status column)
2. Click **Details** to open the task dialog
3. Scroll to the **Last Error** section
4. Review the error message
5. Take corrective action based on the error

### Verify Task Execution

After enabling or running a task:

1. Click **Refresh** to update the view
2. Check **Last Run** to verify execution time
3. Check **Status** to verify success/failure
4. Review **Next Run** to confirm next execution time

## Built-in Task Override Persistence

When you disable/enable a built-in task:

1. **Immediate Effect**: Task stops/starts running immediately
2. **Persistent**: Setting survives application restarts
3. **Database Storage**: Override stored in `builtin_task_overrides` table
4. **Code Independent**: Changes don't require code deployment
5. **Reversible**: Can always re-enable later

## Use Cases

### During Deployment or Maintenance

Disable tasks temporarily to prevent interference:

1. Disable tasks that might conflict with deployment
2. Perform deployment or maintenance
3. Re-enable tasks when complete

### Environment-Specific Configuration

Different environments may need different task configurations:

- **Production**: All critical tasks enabled
- **Staging**: Some tasks disabled for testing
- **Development**: Most tasks disabled to reduce noise

Enable/disable tasks as needed per environment without code changes.

### Troubleshooting Performance Issues

If a task is causing performance problems:

1. Disable the task immediately
2. Investigate the issue
3. Fix the underlying problem (may require code changes)
4. Re-enable after fix is deployed

## Best Practices

1. **Monitor Regularly**: Check the scheduled tasks page weekly for failures
2. **Investigate Failures**: Don't ignore failed tasks - check the error details
3. **Test Before Enabling**: When enabling a previously disabled task, monitor the first few runs
4. **Document Changes**: Keep a log of why you disabled/enabled tasks
5. **Coordinate with Team**: Communicate task changes to other admins

## Troubleshooting

### Task Not Running

**Check:**
- Is the task Active (enabled)?
- Is the Task Scheduler running?
- Does Next Run show a valid future time?
- Are there errors in the Last Error field?

**Solutions:**
- Enable the task if disabled
- Contact support if scheduler is stopped
- Check application logs for errors

### Task Always Failing

**Check:**
- Review error message in Details dialog
- Check if issue is configuration or code-related
- Verify dependencies (e.g., external services are available)

**Solutions:**
- Disable task if causing problems
- Contact development team for code fixes
- Adjust configuration if needed

### Can't Enable/Disable Task

**Check:**
- Are you logged in as an admin user?
- Do you have ADMIN permission level?

**Solutions:**
- Ensure you're logged in with admin account
- Contact SUPERADMIN if you need permission upgrade

## Related Documentation

- [Built-in Tasks System](../../systems/BUILTIN_TASKS.md) - Technical documentation
- [Task Scheduler System](../../systems/TASK_SCHEDULER.md) - Architecture and design
- [Adding New Task Types](../../ADDING_FEATURES.md) - For developers

## Support

If you encounter issues or have questions:

1. Check the task error details for specific error messages
2. Review application logs for more context
3. Contact the development team with:
   - Task name and ID
   - Error message from Details dialog
   - What you were trying to do
   - When the issue started
