"""
Scheduled Task model for SahaBot2.

This module defines the database model for scheduled tasks that can execute
at specific intervals or times.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from enum import IntEnum
from tortoise import fields
from tortoise.models import Model

if TYPE_CHECKING:
    from .organizations import Organization


class TaskType(IntEnum):
    """Task type enum for scheduled tasks."""
    EXAMPLE_LOG = 0  # Example task that logs a message
    RACETIME_OPEN_ROOM = 1  # Open a race room on racetime.gg
    CLEANUP_TOURNAMENT_USAGE = 2  # Clean up old tournament usage tracking data
    ASYNC_TOURNAMENT_TIMEOUT_PENDING = 3  # Timeout pending async tournament races
    ASYNC_TOURNAMENT_TIMEOUT_IN_PROGRESS = 4  # Timeout in-progress async tournament races
    ASYNC_TOURNAMENT_SCORE_CALCULATION = 5  # Recalculate async tournament scores
    ASYNC_LIVE_RACE_OPEN = 6  # Open a RaceTime.gg room for a scheduled live race
    SPEEDGAMING_IMPORT = 7  # Import SpeedGaming episodes into matches
    CLEANUP_PLACEHOLDER_USERS = 8  # Clean up abandoned placeholder users
    CUSTOM = 99  # Custom task type


class ScheduleType(IntEnum):
    """Schedule type enum for how tasks are scheduled."""
    INTERVAL = 1  # Execute at a regular interval (e.g., every 5 minutes)
    CRON = 2  # Execute at specific times (cron-like)
    ONE_TIME = 3  # Execute once at a specific time


class ScheduledTask(Model):
    """
    Scheduled task model.

    Represents a task that can be executed at scheduled intervals or specific times.
    Tasks can be scoped to an organization (organization-specific) or global (organization=None).
    Built-in tasks are defined in code and loaded at startup, not stored in database.
    """
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='scheduled_tasks', null=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    task_type = fields.IntEnumField(TaskType)
    schedule_type = fields.IntEnumField(ScheduleType)

    # For INTERVAL type: interval in seconds
    interval_seconds = fields.IntField(null=True)

    # For CRON type: cron expression (e.g., "0 14 * * *" for daily at 2pm)
    cron_expression = fields.CharField(max_length=255, null=True)

    # For ONE_TIME type: specific datetime to execute
    scheduled_time = fields.DatetimeField(null=True)

    # Task configuration (JSON field for task-specific parameters)
    task_config = fields.JSONField(default=dict)

    # Task state
    is_active = fields.BooleanField(default=True)
    last_run_at = fields.DatetimeField(null=True)
    next_run_at = fields.DatetimeField(null=True)
    last_run_status = fields.CharField(max_length=50, null=True)  # 'success', 'failed', 'running'
    last_run_error = fields.TextField(null=True)

    # Metadata
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    created_by = fields.ForeignKeyField('models.User', related_name='created_tasks', null=True)

    class Meta:
        table = "scheduled_tasks"
        indexes = [
            ("organization_id", "is_active"),
            ("next_run_at", "is_active"),
        ]
