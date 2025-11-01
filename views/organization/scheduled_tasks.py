"""
Scheduled Tasks View for Organization Admin.

Displays and manages scheduled tasks for an organization.
"""

from __future__ import annotations
from nicegui import ui
from models import User, Organization
from models.scheduled_task import TaskType, ScheduleType
from components.card import Card
from application.services.task_scheduler_service import TaskSchedulerService
from datetime import datetime


class OrganizationScheduledTasksView:
    """View for managing scheduled tasks in an organization."""

    def __init__(self, org: Organization, user: User) -> None:
        self.org = org
        self.user = user
        self.service = TaskSchedulerService()

    async def render(self) -> None:
        """Render the scheduled tasks view."""
        with Card.create(title=f'Scheduled Tasks - {self.org.name}'):
            with ui.row().classes('w-full justify-between items-center mb-4'):
                ui.label('Manage automated tasks for this organization').classes('text-secondary')
                # TODO: Re-enable when create dialog is implemented
                # ui.button(
                #     'Create Task',
                #     icon='add',
                #     on_click=self._show_create_dialog
                # ).classes('btn').props('color=positive')
                ui.label('Use API to create tasks (UI coming soon)').classes('text-sm text-secondary')

            # Container for task list
            self.tasks_container = ui.element('div').classes('w-full')

            await self._refresh_tasks()

    async def _refresh_tasks(self) -> None:
        """Refresh the task list."""
        self.tasks_container.clear()

        with self.tasks_container:
            tasks = await self.service.list_tasks(self.user, self.org.id)

            if not tasks:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('schedule').classes('text-secondary icon-large')
                    ui.label('No scheduled tasks yet').classes('text-secondary')
                    ui.label('Create your first automated task to get started').classes('text-secondary text-sm')
            else:
                # Display tasks in a responsive layout
                with ui.element('div').classes('flex flex-col gap-4'):
                    for task in tasks:
                        await self._render_task_card(task)

    async def _render_task_card(self, task) -> None:
        """Render a single task card."""
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-body'):
                with ui.row().classes('w-full justify-between items-start'):
                    # Task info
                    with ui.column().classes('gap-2 flex-grow'):
                        with ui.row().classes('items-center gap-2'):
                            ui.label(task.name).classes('text-lg font-bold')
                            # Status badge
                            if task.is_active:
                                ui.badge('Active', color='positive')
                            else:
                                ui.badge('Inactive', color='negative')

                        if task.description:
                            ui.label(task.description).classes('text-sm text-secondary')

                        # Task details
                        with ui.element('div').classes('text-sm mt-2'):
                            ui.label(f'Type: {self._format_task_type(task.task_type)}')
                            ui.label(f'Schedule: {self._format_schedule(task)}')

                            if task.last_run_at:
                                ui.label(f'Last run: {self._format_datetime(task.last_run_at)} ({task.last_run_status or "unknown"})')
                            else:
                                ui.label('Last run: Never')

                            if task.next_run_at:
                                ui.label(f'Next run: {self._format_datetime(task.next_run_at)}')

                    # Actions
                    with ui.column().classes('gap-2'):
                        # TODO: Re-enable when edit dialog is implemented
                        # ui.button(
                        #     icon='edit',
                        #     on_click=lambda t=task: self._show_edit_dialog(t)
                        # ).props('flat color=primary').tooltip('Edit Task')

                        if task.is_active:
                            ui.button(
                                icon='pause',
                                on_click=lambda t=task: self._toggle_task(t)
                            ).props('flat color=warning').tooltip('Pause Task')
                        else:
                            ui.button(
                                icon='play_arrow',
                                on_click=lambda t=task: self._toggle_task(t)
                            ).props('flat color=positive').tooltip('Activate Task')

                        ui.button(
                            icon='delete',
                            on_click=lambda t=task: self._delete_task(t)
                        ).props('flat color=negative').tooltip('Delete Task')

    def _format_task_type(self, task_type: TaskType) -> str:
        """Format task type for display."""
        if task_type == TaskType.RACETIME_OPEN_ROOM:
            return 'Open Racetime Room'
        elif task_type == TaskType.CUSTOM:
            return 'Custom'
        return str(task_type)

    def _format_schedule(self, task) -> str:
        """Format schedule for display."""
        if task.schedule_type == ScheduleType.INTERVAL:
            minutes = task.interval_seconds // 60
            hours = minutes // 60
            if hours > 0:
                return f'Every {hours} hour(s)'
            else:
                return f'Every {minutes} minute(s)'
        elif task.schedule_type == ScheduleType.CRON:
            return f'Cron: {task.cron_expression}'
        elif task.schedule_type == ScheduleType.ONE_TIME:
            return f'One-time: {self._format_datetime(task.scheduled_time)}'
        return 'Unknown'

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for display."""
        return dt.strftime('%Y-%m-%d %H:%M UTC')

    async def _show_create_dialog(self) -> None:
        """Show dialog to create a new task."""
        ui.notify('Task creation dialog coming soon!', type='info')
        # TODO: Implement create dialog

    async def _show_edit_dialog(self, task) -> None:
        """Show dialog to edit a task."""
        ui.notify(f'Edit dialog for task {task.name} coming soon!', type='info')
        # TODO: Implement edit dialog

    async def _toggle_task(self, task) -> None:
        """Toggle task active status."""
        new_status = not task.is_active
        updated_task = await self.service.update_task(
            self.user,
            self.org.id,
            task.id,
            is_active=new_status
        )

        if updated_task:
            status_text = 'activated' if new_status else 'paused'
            ui.notify(f'Task {status_text} successfully', type='positive')
            await self._refresh_tasks()
        else:
            ui.notify('Failed to update task', type='negative')

    async def _delete_task(self, task) -> None:
        """Delete a task."""
        # Show confirmation dialog
        with ui.dialog() as dialog, ui.card():
            ui.label(f'Delete task "{task.name}"?').classes('text-lg')
            ui.label('This action cannot be undone.').classes('text-secondary')

            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancel', on_click=dialog.close).classes('btn')
                ui.button(
                    'Delete',
                    on_click=lambda: self._confirm_delete(task, dialog)
                ).classes('btn').props('color=negative')

        dialog.open()

    async def _confirm_delete(self, task, dialog) -> None:
        """Confirm and execute task deletion."""
        success = await self.service.delete_task(self.user, self.org.id, task.id)

        if success:
            ui.notify('Task deleted successfully', type='positive')
            await self._refresh_tasks()
        else:
            ui.notify('Failed to delete task', type='negative')

        dialog.close()
