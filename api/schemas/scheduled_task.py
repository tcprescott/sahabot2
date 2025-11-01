"""
API schemas for scheduled tasks.

Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from models.scheduled_task import TaskType, ScheduleType


class ScheduledTaskBase(BaseModel):
    """Base schema for scheduled task."""
    name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    task_type: TaskType = Field(..., description="Type of task")
    schedule_type: ScheduleType = Field(..., description="How the task is scheduled")
    interval_seconds: Optional[int] = Field(None, description="For INTERVAL type: interval in seconds")
    cron_expression: Optional[str] = Field(None, description="For CRON type: cron expression")
    scheduled_time: Optional[datetime] = Field(None, description="For ONE_TIME type: specific time to run")
    task_config: dict = Field(default_factory=dict, description="Task-specific configuration")
    is_active: bool = Field(True, description="Whether the task is active")


class ScheduledTaskCreateRequest(ScheduledTaskBase):
    """Schema for creating a scheduled task."""
    pass


class ScheduledTaskUpdateRequest(BaseModel):
    """Schema for updating a scheduled task."""
    name: Optional[str] = Field(None, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    interval_seconds: Optional[int] = Field(None, description="For INTERVAL type: interval in seconds")
    cron_expression: Optional[str] = Field(None, description="For CRON type: cron expression")
    scheduled_time: Optional[datetime] = Field(None, description="For ONE_TIME type: specific time to run")
    task_config: Optional[dict] = Field(None, description="Task-specific configuration")
    is_active: Optional[bool] = Field(None, description="Whether the task is active")


class ScheduledTaskOut(BaseModel):
    """Schema for scheduled task response."""
    id: int
    organization_id: int
    name: str
    description: Optional[str]
    task_type: TaskType
    schedule_type: ScheduleType
    interval_seconds: Optional[int]
    cron_expression: Optional[str]
    scheduled_time: Optional[datetime]
    task_config: dict
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    last_run_status: Optional[str]
    last_run_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int]

    class Config:
        from_attributes = True


class ScheduledTaskListResponse(BaseModel):
    """Schema for list of scheduled tasks."""
    items: List[ScheduledTaskOut]
    count: int
