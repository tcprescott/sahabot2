"""
Scheduled Task Dialog for creating and editing scheduled tasks.
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional, Callable
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from models import User
from models.scheduled_task import ScheduledTask, TaskType, ScheduleType
from application.services.task_scheduler_service import TaskSchedulerService

logger = logging.getLogger(__name__)


class ScheduledTaskDialog(BaseDialog):
    """Dialog for creating or editing a scheduled task."""

    def __init__(
        self,
        user: User,
        organization_id: int,
        task: Optional[ScheduledTask] = None,
        on_save: Optional[Callable] = None
    ):
        super().__init__()
        self.user = user
        self.organization_id = organization_id
        self.task = task
        self.on_save = on_save
        self.service = TaskSchedulerService()

        # Form fields
        self.name_input = None
        self.description_input = None
        self.task_type_select = None
        self.schedule_type_select = None
        self.interval_input = None
        self.cron_input = None
        self.scheduled_time_input = None
        self.config_message_input = None
        self.is_active_switch = None
        
        # Containers for conditional fields
        self.interval_container = None
        self.cron_container = None
        self.onetime_container = None
        self.config_container = None
        self.interval_multiplier = 60  # Default to minutes

    async def show(self):
        """Display the dialog."""
        title = f'Edit Task: {self.task.name}' if self.task else 'Create New Task'
        self.create_dialog(title=title, icon='schedule')
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        with self.create_form_grid(columns=1):
            # Basic information
            self.name_input = ui.input(
                label='Task Name',
                placeholder='Enter task name',
                value=self.task.name if self.task else ''
            ).classes('w-full').props('outlined')

            self.description_input = ui.textarea(
                label='Description (optional)',
                placeholder='Enter task description',
                value=self.task.description if self.task else ''
            ).classes('w-full').props('outlined')

            # Task type
            task_type_options = {
                TaskType.EXAMPLE_LOG.value: 'Example Log Task',
                TaskType.CUSTOM.value: 'Custom Task',
            }
            self.task_type_select = ui.select(
                options=task_type_options,
                label='Task Type',
                value=self.task.task_type.value if self.task else TaskType.EXAMPLE_LOG.value,
                on_change=self._on_task_type_change
            ).classes('w-full').props('outlined')

            # Schedule type
            schedule_type_options = {
                ScheduleType.INTERVAL.value: 'Interval (Every X seconds/minutes/hours)',
                ScheduleType.CRON.value: 'Cron Expression',
                ScheduleType.ONE_TIME.value: 'One-Time (Specific date/time)',
            }
            self.schedule_type_select = ui.select(
                options=schedule_type_options,
                label='Schedule Type',
                value=self.task.schedule_type.value if self.task else ScheduleType.INTERVAL.value,
                on_change=self._on_schedule_type_change
            ).classes('w-full').props('outlined')

            # Interval fields (conditional)
            self.interval_container = ui.element('div').classes('w-full')
            with self.interval_container:
                with ui.row().classes('w-full gap-2'):
                    self.interval_input = ui.number(
                        label='Interval',
                        value=self.task.interval_seconds // 60 if self.task and self.task.interval_seconds else 5,
                        min=1,
                        step=1
                    ).classes('flex-1').props('outlined')
                    
                    ui.select(
                        options={
                            1: 'Seconds',
                            60: 'Minutes',
                            3600: 'Hours',
                        },
                        label='Unit',
                        value=60,
                        on_change=lambda e: self._update_interval_multiplier(e.value)
                    ).classes('w-32').props('outlined')
                self.interval_multiplier = 60

            # Cron fields (conditional)
            self.cron_container = ui.element('div').classes('w-full hidden')
            with self.cron_container:
                self.cron_input = ui.input(
                    label='Cron Expression',
                    placeholder='* * * * *',
                    value=self.task.cron_expression if self.task and self.task.cron_expression else ''
                ).classes('w-full').props('outlined')
                ui.label('Format: minute hour day month weekday').classes('text-xs text-secondary')
                ui.label('Example: "0 9 * * *" = Every day at 9:00 AM UTC').classes('text-xs text-secondary')

            # One-time fields (conditional)
            self.onetime_container = ui.element('div').classes('w-full hidden')
            with self.onetime_container:
                # Default to 1 hour from now
                default_time = datetime.now(timezone.utc).replace(second=0, microsecond=0)
                if self.task and self.task.scheduled_time:
                    default_time = self.task.scheduled_time
                
                self.scheduled_time_input = ui.input(
                    label='Scheduled Time (UTC)',
                    value=default_time.strftime('%Y-%m-%dT%H:%M')
                ).classes('w-full').props('outlined type=datetime-local')

            ui.separator()

            # Task configuration (conditional based on task type)
            self.config_container = ui.element('div').classes('w-full')
            with self.config_container:
                ui.label('Task Configuration').classes('font-bold')
                self.config_message_input = ui.input(
                    label='Custom Message',
                    placeholder='Enter a custom message for the log',
                    value=self.task.task_config.get('message', '') if self.task and self.task.task_config else ''
                ).classes('w-full').props('outlined')

            # Active status
            self.is_active_switch = ui.switch(
                'Active',
                value=self.task.is_active if self.task else True
            )

        ui.separator()

        # Action buttons
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button(
                'Save' if self.task else 'Create',
                on_click=self._save
            ).classes('btn').props('color=positive')

        # Initialize visibility
        self._on_schedule_type_change()

    def _on_task_type_change(self):
        """Handle task type change."""
        # Show/hide configuration fields based on task type
        task_type = self.task_type_select.value
        if task_type == TaskType.EXAMPLE_LOG.value:
            self.config_container.set_visibility(True)
        else:
            self.config_container.set_visibility(False)

    def _on_schedule_type_change(self):
        """Handle schedule type change."""
        schedule_type = self.schedule_type_select.value
        
        # Show/hide relevant fields
        self.interval_container.set_visibility(schedule_type == ScheduleType.INTERVAL.value)
        self.cron_container.set_visibility(schedule_type == ScheduleType.CRON.value)
        self.onetime_container.set_visibility(schedule_type == ScheduleType.ONE_TIME.value)

    def _update_interval_multiplier(self, multiplier: int):
        """Update the interval multiplier."""
        self.interval_multiplier = multiplier

    async def _save(self):
        """Save the task."""
        # Validate required fields
        if not self.name_input.value:
            ui.notify('Task name is required', type='negative')
            return

        schedule_type = ScheduleType(self.schedule_type_select.value)
        task_type = TaskType(self.task_type_select.value)
        
        # Validate schedule-specific fields
        interval_seconds = None
        cron_expression = None
        scheduled_time = None

        if schedule_type == ScheduleType.INTERVAL:
            if not self.interval_input.value or self.interval_input.value < 1:
                ui.notify('Valid interval is required', type='negative')
                return
            interval_seconds = int(self.interval_input.value * self.interval_multiplier)

        elif schedule_type == ScheduleType.CRON:
            if not self.cron_input.value:
                ui.notify('Cron expression is required', type='negative')
                return
            cron_expression = self.cron_input.value

        elif schedule_type == ScheduleType.ONE_TIME:
            if not self.scheduled_time_input.value:
                ui.notify('Scheduled time is required', type='negative')
                return
            # Parse datetime
            try:
                scheduled_time = datetime.fromisoformat(self.scheduled_time_input.value).replace(tzinfo=timezone.utc)
            except ValueError:
                ui.notify('Invalid datetime format', type='negative')
                return

        # Build task config
        task_config = {}
        if task_type == TaskType.EXAMPLE_LOG and self.config_message_input.value:
            task_config['message'] = self.config_message_input.value

        try:
            if self.task:
                # Update existing task
                updated_task = await self.service.update_task(
                    user=self.user,
                    organization_id=self.organization_id,
                    task_id=self.task.id,
                    name=self.name_input.value,
                    description=self.description_input.value or None,
                    task_type=task_type,
                    schedule_type=schedule_type,
                    interval_seconds=interval_seconds,
                    cron_expression=cron_expression,
                    scheduled_time=scheduled_time,
                    task_config=task_config if task_config else None,
                    is_active=self.is_active_switch.value,
                )
                if updated_task:
                    ui.notify('Task updated successfully', type='positive')
                else:
                    ui.notify('Failed to update task', type='negative')
                    return
            else:
                # Create new task
                new_task = await self.service.create_task(
                    user=self.user,
                    organization_id=self.organization_id,
                    name=self.name_input.value,
                    description=self.description_input.value or None,
                    task_type=task_type,
                    schedule_type=schedule_type,
                    interval_seconds=interval_seconds,
                    cron_expression=cron_expression,
                    scheduled_time=scheduled_time,
                    task_config=task_config if task_config else None,
                    is_active=self.is_active_switch.value,
                )
                if new_task:
                    ui.notify('Task created successfully', type='positive')
                else:
                    ui.notify('Failed to create task', type='negative')
                    return

            # Call callback and close
            if self.on_save:
                await self.on_save()
            await self.close()

        except Exception as e:
            logger.error("Error saving task: %s", e, exc_info=True)
            ui.notify(f'Error saving task: {str(e)}', type='negative')
