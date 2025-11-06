"""
Admin Scheduled Tasks view: monitor status of all scheduled tasks.

Renders within the Admin page dynamic content area.
Shows both database tasks and built-in tasks.
"""

from __future__ import annotations
from typing import Any
from nicegui import ui
from components.data_table import ResponsiveTable, TableColumn
from components.card import Card
from components.datetime_label import DateTimeLabel
from application.services.tasks.task_scheduler_service import TaskSchedulerService
from models.scheduled_task import TaskType, ScheduleType


class ScheduledTasksView:
    """Admin view for monitoring all scheduled tasks."""

    def __init__(self, user: Any) -> None:
        self.user = user
        self.service = TaskSchedulerService()
        self.container = None

    async def _refresh(self) -> None:
        """Refresh the view by re-rendering content in place."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    def _render_task_type(self, task_info: dict) -> None:
        """Render task type badge."""
        task_type = task_info['task_type']
        type_name = TaskType(task_type).name if isinstance(task_type, int) else task_type.name
        
        # Color code by task type category
        if 'ASYNC_TOURNAMENT' in type_name:
            color = 'primary'
        elif 'CLEANUP' in type_name:
            color = 'warning'
        elif 'RACETIME' in type_name:
            color = 'info'
        else:
            color = 'secondary'
        
        ui.badge(type_name.replace('_', ' ').title()).props(f'color={color}')

    def _render_schedule(self, task_info: dict) -> None:
        """Render schedule information."""
        schedule_type = task_info['schedule_type']
        
        if schedule_type == ScheduleType.INTERVAL:
            seconds = task_info['interval_seconds']
            if seconds >= 3600:
                hours = seconds // 3600
                label = f"Every {hours}h"
            elif seconds >= 60:
                minutes = seconds // 60
                label = f"Every {minutes}m"
            else:
                label = f"Every {seconds}s"
            ui.label(label).classes('text-sm')
        elif schedule_type == ScheduleType.CRON:
            ui.label(task_info['cron_expression']).classes('text-sm font-mono')
        else:
            ui.label('One-time').classes('text-sm')

    def _render_status(self, task_info: dict) -> None:
        """Render task status indicator."""
        last_status = task_info['last_status']
        
        if last_status == 'success':
            with ui.row().classes('items-center gap-1'):
                ui.icon('check_circle').classes('text-positive')
                ui.label('Success').classes('text-positive text-sm')
        elif last_status == 'failed':
            with ui.row().classes('items-center gap-1'):
                ui.icon('error').classes('text-negative')
                ui.label('Failed').classes('text-negative text-sm')
        elif last_status is None:
            with ui.row().classes('items-center gap-1'):
                ui.icon('schedule').classes('text-secondary')
                ui.label('Not Run').classes('text-secondary text-sm')
        else:
            ui.label(last_status).classes('text-sm')

    def _render_last_run(self, task_info: dict) -> None:
        """Render last run time."""
        last_run_at = task_info['last_run_at']
        
        if last_run_at:
            DateTimeLabel.create(last_run_at, format_type='relative')
        else:
            ui.label('Never').classes('text-secondary text-sm')

    def _render_next_run(self, task_info: dict) -> None:
        """Render next scheduled run time."""
        next_run_at = task_info['next_run_at']
        
        if next_run_at:
            DateTimeLabel.create(next_run_at, format_type='relative')
        else:
            ui.label('—').classes('text-secondary text-sm')

    def _render_active_status(self, task_info: dict) -> None:
        """Render active/inactive status."""
        is_active = task_info['is_active']
        
        if is_active:
            with ui.row().classes('items-center gap-1'):
                ui.icon('play_circle').classes('text-positive')
                ui.label('Active').classes('text-positive text-sm')
        else:
            with ui.row().classes('items-center gap-1'):
                ui.icon('pause_circle').classes('text-secondary')
                ui.label('Inactive').classes('text-secondary text-sm')

    async def _view_task_details(self, task_info: dict) -> None:
        """Show detailed information about a task."""
        with ui.dialog() as dialog:
            with ui.element('div').classes('card dialog-card'):
                # Header
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('info').classes('icon-medium')
                            ui.label(task_info['name']).classes('text-xl text-bold')
                        ui.button(icon='close', on_click=dialog.close).props('flat round dense')
                
                # Body
                with ui.element('div').classes('card-body'):
                    # Task ID and Description
                    with ui.column().classes('gap-2 mb-4'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('label', size='sm')
                            ui.label(f"Task ID: {task_info['task_id']}").classes('text-sm font-mono')
                        
                        if task_info['description']:
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('description', size='sm')
                                ui.label(task_info['description']).classes('text-sm')
                    
                    ui.separator()
                    
                    # Schedule Information
                    ui.label('Schedule Configuration').classes('font-bold mt-4 mb-2')
                    with ui.column().classes('gap-2'):
                        with ui.row().classes('items-center gap-2'):
                            ui.label('Type:').classes('text-sm font-bold')
                            self._render_task_type(task_info)
                        
                        with ui.row().classes('items-center gap-2'):
                            ui.label('Schedule:').classes('text-sm font-bold')
                            self._render_schedule(task_info)
                        
                        with ui.row().classes('items-center gap-2'):
                            ui.label('Status:').classes('text-sm font-bold')
                            self._render_active_status(task_info)
                    
                    ui.separator()
                    
                    # Execution Status
                    ui.label('Execution Status').classes('font-bold mt-4 mb-2')
                    with ui.column().classes('gap-2'):
                        with ui.row().classes('items-center gap-2'):
                            ui.label('Last Run:').classes('text-sm font-bold')
                            self._render_last_run(task_info)
                        
                        with ui.row().classes('items-center gap-2'):
                            ui.label('Last Status:').classes('text-sm font-bold')
                            self._render_status(task_info)
                        
                        with ui.row().classes('items-center gap-2'):
                            ui.label('Next Run:').classes('text-sm font-bold')
                            self._render_next_run(task_info)
                    
                    # Error information if failed
                    if task_info['last_error']:
                        ui.separator()
                        ui.label('Last Error').classes('font-bold mt-4 mb-2')
                        with ui.row().classes('items-center gap-2 p-3 rounded bg-negative text-white'):
                            ui.icon('error')
                            ui.label(task_info['last_error']).classes('text-sm')
                    
                    # Action buttons
                    with ui.row().classes('justify-end gap-2 mt-4'):
                        ui.button('Refresh', on_click=lambda: (dialog.close(), self._refresh())).classes('btn')
                        ui.button('Close', on_click=dialog.close).classes('btn')
        
        dialog.open()

    async def _execute_builtin_task_now(self, task_info: dict) -> None:
        """Execute a built-in task immediately."""
        task_id = task_info['task_id']
        task_name = task_info['name']

        success = await TaskSchedulerService.execute_builtin_task_now(self.user, task_id)

        if success:
            ui.notify(f'Built-in task "{task_name}" execution triggered', type='positive')
            # Refresh after a short delay to allow task to update status
            await self._refresh()
        else:
            ui.notify('Failed to execute task - check permissions or task status', type='negative')

    async def _execute_db_task_now(self, task) -> None:
        """Execute a database task immediately (admin global tasks only)."""
        # Global tasks have organization_id = None
        success = await self.service.execute_task_now(
            self.user,
            task.organization_id,  # Will be None for global tasks
            task.id
        )

        if success:
            ui.notify(f'Task "{task.name}" execution triggered', type='positive')
            await self._refresh()
        else:
            ui.notify('Failed to execute task', type='negative')

    async def _view_db_task_details(self, task) -> None:
        """Show detailed information about a database task."""
        with ui.dialog() as dialog:
            with ui.element('div').classes('card dialog-card'):
                # Header
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('info').classes('icon-medium')
                            ui.label(task.name).classes('text-xl text-bold')
                        ui.button(icon='close', on_click=dialog.close).props('flat round dense')
                
                # Body
                with ui.element('div').classes('card-body'):
                    # Task ID and Description
                    with ui.column().classes('gap-2 mb-4'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('label', size='sm')
                            ui.label(f"Task ID: {task.id}").classes('text-sm font-mono')
                        
                        if task.description:
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('description', size='sm')
                                ui.label(task.description).classes('text-sm')
                        
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('storage', size='sm')
                            ui.label('Source: Database (Global)').classes('text-sm badge')
                    
                    ui.separator()
                    
                    # Schedule Information
                    ui.label('Schedule Configuration').classes('font-bold mt-4 mb-2')
                    with ui.column().classes('gap-2'):
                        with ui.row().classes('items-center gap-2'):
                            ui.label('Type:').classes('text-sm font-bold')
                            task_info = {'task_type': task.task_type}
                            self._render_task_type(task_info)
                        
                        with ui.row().classes('items-center gap-2'):
                            ui.label('Schedule:').classes('text-sm font-bold')
                            schedule_info = {
                                'schedule_type': task.schedule_type,
                                'interval_seconds': task.interval_seconds,
                                'cron_expression': task.cron_expression,
                            }
                            self._render_schedule(schedule_info)
                        
                        with ui.row().classes('items-center gap-2'):
                            ui.label('Status:').classes('text-sm font-bold')
                            active_info = {'is_active': task.is_active}
                            self._render_active_status(active_info)
                    
                    ui.separator()
                    
                    # Execution Status
                    ui.label('Execution Status').classes('font-bold mt-4 mb-2')
                    with ui.column().classes('gap-2'):
                        with ui.row().classes('items-center gap-2'):
                            ui.label('Last Run:').classes('text-sm font-bold')
                            if task.last_run_at:
                                DateTimeLabel.create(task.last_run_at, format_type='relative')
                            else:
                                ui.label('Never').classes('text-secondary text-sm')
                        
                        with ui.row().classes('items-center gap-2'):
                            ui.label('Last Status:').classes('text-sm font-bold')
                            status_info = {'last_status': task.last_run_status}
                            self._render_status(status_info)
                        
                        with ui.row().classes('items-center gap-2'):
                            ui.label('Next Run:').classes('text-sm font-bold')
                            if task.next_run_at:
                                DateTimeLabel.create(task.next_run_at, format_type='relative')
                            else:
                                ui.label('—').classes('text-secondary text-sm')
                    
                    # Error information if failed
                    if task.last_run_error:
                        ui.separator()
                        ui.label('Last Error').classes('font-bold mt-4 mb-2')
                        with ui.row().classes('items-center gap-2 p-3 rounded bg-negative text-white'):
                            ui.icon('error')
                            ui.label(task.last_run_error).classes('text-sm')
                    
                    # Task configuration
                    if task.task_config:
                        ui.separator()
                        ui.label('Task Configuration').classes('font-bold mt-4 mb-2')
                        import json
                        config_str = json.dumps(task.task_config, indent=2)
                        ui.code(config_str).classes('text-sm')
                    
                    # Created info
                    if task.created_at or task.created_by_id:
                        ui.separator()
                        ui.label('Metadata').classes('font-bold mt-4 mb-2')
                        with ui.column().classes('gap-2'):
                            if task.created_at:
                                with ui.row().classes('items-center gap-2'):
                                    ui.label('Created:').classes('text-sm font-bold')
                                    DateTimeLabel.create(task.created_at, format_type='datetime')
                            if task.created_by_id:
                                with ui.row().classes('items-center gap-2'):
                                    ui.label('Created By:').classes('text-sm font-bold')
                                    ui.label(f'User ID {task.created_by_id}').classes('text-sm')
                    
                    # Action buttons
                    with ui.row().classes('justify-end gap-2 mt-4'):
                        ui.button('Refresh', on_click=lambda: (dialog.close(), self._refresh())).classes('btn')
                        ui.button('Close', on_click=dialog.close).classes('btn')
        
        dialog.open()

    def _render_actions(self, task_info: dict) -> None:
        """Render action buttons for built-in tasks."""
        with ui.element('div').classes('flex gap-2'):
            # Only show Run Now for active tasks
            if task_info.get('is_active', False):
                ui.button(
                    'Run Now',
                    icon='play_circle',
                    on_click=lambda t=task_info: self._execute_builtin_task_now(t)
                ).classes('btn').props('color=primary size=sm')
            ui.button(
                'Details',
                icon='info',
                on_click=lambda t=task_info: self._view_task_details(t)
            ).classes('btn').props('size=sm')

    async def _render_content(self) -> None:
        """Render the scheduled tasks monitoring interface."""
        # Get built-in tasks with status
        builtin_tasks = self.service.get_builtin_tasks_with_status(active_only=False)
        
        # Get database tasks (global tasks only - organization tasks are managed elsewhere)
        db_tasks = await self.service.repo.list_global_tasks(active_only=False)

        # Scheduler status header
        with ui.element('div').classes('card mb-4'):
            with ui.element('div').classes('card-header'):
                with ui.row().classes('w-full justify-between items-center'):
                    with ui.column():
                        ui.label('Scheduled Tasks Monitor').classes('text-xl font-bold')
                        is_running = TaskSchedulerService.is_running()
                        ui.label(f'Task Scheduler: {"Running" if is_running else "Stopped"}').classes(
                            'text-sm text-positive' if is_running else 'text-sm text-negative'
                        )
                    ui.button('Refresh', icon='refresh', on_click=self._refresh).classes('btn')

        # Built-in Tasks Card
        with Card.create(title='Built-in Tasks'):
            ui.label('System tasks defined in code and loaded at startup.').classes('text-sm text-secondary mb-4')
            
            # Statistics
            active_count = sum(1 for t in builtin_tasks if t['is_active'])
            success_count = sum(1 for t in builtin_tasks if t['last_status'] == 'success')
            failed_count = sum(1 for t in builtin_tasks if t['last_status'] == 'failed')
            
            with ui.row().classes('gap-4 mb-4'):
                with ui.element('div').classes('flex items-center gap-2'):
                    ui.icon('task').classes('text-primary')
                    ui.label(f'{len(builtin_tasks)} Total').classes('text-sm')
                
                with ui.element('div').classes('flex items-center gap-2'):
                    ui.icon('play_circle').classes('text-positive')
                    ui.label(f'{active_count} Active').classes('text-sm')
                
                with ui.element('div').classes('flex items-center gap-2'):
                    ui.icon('check_circle').classes('text-positive')
                    ui.label(f'{success_count} Successful').classes('text-sm')
                
                if failed_count > 0:
                    with ui.element('div').classes('flex items-center gap-2'):
                        ui.icon('error').classes('text-negative')
                        ui.label(f'{failed_count} Failed').classes('text-sm')

            ui.separator()

            columns = [
                TableColumn('Name', key='name'),
                TableColumn('Type', cell_render=self._render_task_type),
                TableColumn('Schedule', cell_render=self._render_schedule),
                TableColumn('Active', cell_render=self._render_active_status),
                TableColumn('Last Run', cell_render=self._render_last_run),
                TableColumn('Status', cell_render=self._render_status),
                TableColumn('Next Run', cell_render=self._render_next_run),
                TableColumn('Actions', cell_render=self._render_actions),
            ]
            table = ResponsiveTable(columns, builtin_tasks)
            await table.render()

        # Database Tasks Card
        with Card.create(title='Global Database Tasks'):
            ui.label('User-created global tasks stored in the database.').classes('text-sm text-secondary mb-4')
            
            if db_tasks:
                # Statistics for database tasks
                db_active_count = sum(1 for t in db_tasks if t.is_active)
                db_success_count = sum(1 for t in db_tasks if t.last_run_status == 'success')
                db_failed_count = sum(1 for t in db_tasks if t.last_run_status == 'failed')
                
                with ui.row().classes('gap-4 mb-4'):
                    with ui.element('div').classes('flex items-center gap-2'):
                        ui.icon('task').classes('text-primary')
                        ui.label(f'{len(db_tasks)} Total').classes('text-sm')
                    
                    with ui.element('div').classes('flex items-center gap-2'):
                        ui.icon('play_circle').classes('text-positive')
                        ui.label(f'{db_active_count} Active').classes('text-sm')
                    
                    with ui.element('div').classes('flex items-center gap-2'):
                        ui.icon('check_circle').classes('text-positive')
                        ui.label(f'{db_success_count} Successful').classes('text-sm')
                    
                    if db_failed_count > 0:
                        with ui.element('div').classes('flex items-center gap-2'):
                            ui.icon('error').classes('text-negative')
                            ui.label(f'{db_failed_count} Failed').classes('text-sm')

                ui.separator()

                def render_db_task_type(task):
                    task_info = {'task_type': task.task_type}
                    self._render_task_type(task_info)

                def render_db_schedule(task):
                    task_info = {
                        'schedule_type': task.schedule_type,
                        'interval_seconds': task.interval_seconds,
                        'cron_expression': task.cron_expression,
                    }
                    self._render_schedule(task_info)

                def render_db_active(task):
                    task_info = {'is_active': task.is_active}
                    self._render_active_status(task_info)

                def render_db_last_run(task):
                    if task.last_run_at:
                        DateTimeLabel.create(task.last_run_at, format_type='relative')
                    else:
                        ui.label('Never').classes('text-secondary text-sm')

                def render_db_status(task):
                    task_info = {'last_status': task.last_run_status}
                    self._render_status(task_info)

                def render_db_next_run(task):
                    if task.next_run_at:
                        DateTimeLabel.create(task.next_run_at, format_type='relative')
                    else:
                        ui.label('—').classes('text-secondary text-sm')

                def render_db_actions(task):
                    with ui.element('div').classes('flex gap-2'):
                        ui.button(
                            'Run Now',
                            icon='play_circle',
                            on_click=lambda t=task: self._execute_db_task_now(t)
                        ).classes('btn').props('color=primary size=sm')
                        ui.button(
                            'Details',
                            icon='info',
                            on_click=lambda t=task: self._view_db_task_details(t)
                        ).classes('btn').props('size=sm')

                db_columns = [
                    TableColumn('Name', key='name'),
                    TableColumn('Type', cell_render=render_db_task_type),
                    TableColumn('Schedule', cell_render=render_db_schedule),
                    TableColumn('Active', cell_render=render_db_active),
                    TableColumn('Last Run', cell_render=render_db_last_run),
                    TableColumn('Status', cell_render=render_db_status),
                    TableColumn('Next Run', cell_render=render_db_next_run),
                    TableColumn('Actions', cell_render=render_db_actions),
                ]
                db_table = ResponsiveTable(db_columns, db_tasks)
                await db_table.render()
            else:
                with ui.row().classes('items-center gap-2 p-4 bg-secondary/10 rounded'):
                    ui.icon('info').classes('text-secondary')
                    ui.label('No global database tasks created yet.').classes('text-secondary')

    async def render(self) -> None:
        """Render the built-in tasks monitoring UI."""
        self.container = ui.column().classes('full-width')
        with self.container:
            await self._render_content()
