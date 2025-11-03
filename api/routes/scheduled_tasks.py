"""Scheduled task-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path
from api.schemas.scheduled_task import (
    ScheduledTaskOut,
    ScheduledTaskListResponse,
    ScheduledTaskCreateRequest,
    ScheduledTaskUpdateRequest,
)
from api.deps import get_current_user, enforce_rate_limit
from application.services.task_scheduler_service import TaskSchedulerService
from models import User

router = APIRouter(prefix="/scheduled-tasks", tags=["scheduled-tasks"])


@router.get(
    "/organizations/{organization_id}",
    response_model=ScheduledTaskListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Scheduled Tasks",
    description="List all scheduled tasks for an organization. Authorization enforced at service layer.",
    responses={
        200: {"description": "Scheduled tasks retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_scheduled_tasks(
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> ScheduledTaskListResponse:
    """
    List organization scheduled tasks.

    Returns all scheduled tasks for the specified organization.
    Authorization is enforced at the service layer.

    Args:
        organization_id: ID of the organization
        current_user: Authenticated user making the request

    Returns:
        ScheduledTaskListResponse: List of scheduled tasks (empty if unauthorized)
    """
    service = TaskSchedulerService()
    tasks = await service.list_tasks(current_user, organization_id)
    items = [ScheduledTaskOut.model_validate(task) for task in tasks]
    return ScheduledTaskListResponse(items=items, count=len(items))


@router.post(
    "/organizations/{organization_id}",
    response_model=ScheduledTaskOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Scheduled Task",
    description="Create a new scheduled task. Authorization enforced at service layer.",
    responses={
        201: {"description": "Scheduled task created successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def create_scheduled_task(
    data: ScheduledTaskCreateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> ScheduledTaskOut:
    """
    Create a new scheduled task.

    Creates a scheduled task with the specified configuration.
    Authorization is enforced at the service layer.

    Args:
        data: Scheduled task data
        organization_id: ID of the organization
        current_user: Authenticated user making the request

    Returns:
        ScheduledTaskOut: Created scheduled task

    Raises:
        HTTPException: If unauthorized or creation fails
    """
    service = TaskSchedulerService()
    task = await service.create_task(
        user=current_user,
        organization_id=organization_id,
        name=data.name,
        task_type=data.task_type,
        schedule_type=data.schedule_type,
        description=data.description,
        interval_seconds=data.interval_seconds,
        cron_expression=data.cron_expression,
        scheduled_time=data.scheduled_time,
        task_config=data.task_config,
        is_active=data.is_active,
    )

    if not task:
        raise HTTPException(status_code=403, detail="Insufficient permissions to create scheduled task")

    return ScheduledTaskOut.model_validate(task)


@router.get(
    "/organizations/{organization_id}/tasks/{task_id}",
    response_model=ScheduledTaskOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Scheduled Task",
    description="Get a specific scheduled task. Authorization enforced at service layer.",
    responses={
        200: {"description": "Scheduled task retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Scheduled task not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_scheduled_task(
    organization_id: int = Path(..., description="Organization ID"),
    task_id: int = Path(..., description="Scheduled task ID"),
    current_user: User = Depends(get_current_user)
) -> ScheduledTaskOut:
    """
    Get a specific scheduled task.

    Retrieves a scheduled task by ID.
    Authorization is enforced at the service layer.

    Args:
        organization_id: ID of the organization
        task_id: ID of the scheduled task
        current_user: Authenticated user making the request

    Returns:
        ScheduledTaskOut: Scheduled task details

    Raises:
        HTTPException: If task not found or unauthorized
    """
    service = TaskSchedulerService()
    task = await service.get_task(current_user, organization_id, task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")

    return ScheduledTaskOut.model_validate(task)


@router.patch(
    "/organizations/{organization_id}/tasks/{task_id}",
    response_model=ScheduledTaskOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Scheduled Task",
    description="Update a scheduled task. Authorization enforced at service layer.",
    responses={
        200: {"description": "Scheduled task updated successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Scheduled task not found"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def update_scheduled_task(
    data: ScheduledTaskUpdateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    task_id: int = Path(..., description="Scheduled task ID"),
    current_user: User = Depends(get_current_user)
) -> ScheduledTaskOut:
    """
    Update a scheduled task.

    Updates the specified scheduled task with the provided data.
    Authorization is enforced at the service layer.

    Args:
        data: Updated task data
        organization_id: ID of the organization
        task_id: ID of the scheduled task
        current_user: Authenticated user making the request

    Returns:
        ScheduledTaskOut: Updated scheduled task

    Raises:
        HTTPException: If task not found or unauthorized
    """
    service = TaskSchedulerService()

    # Build update dict excluding None values
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    task = await service.update_task(current_user, organization_id, task_id, **update_data)

    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found or insufficient permissions")

    return ScheduledTaskOut.model_validate(task)


@router.delete(
    "/organizations/{organization_id}/tasks/{task_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Scheduled Task",
    description="Delete a scheduled task. Authorization enforced at service layer.",
    responses={
        204: {"description": "Scheduled task deleted successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Scheduled task not found"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=204,
)
async def delete_scheduled_task(
    organization_id: int = Path(..., description="Organization ID"),
    task_id: int = Path(..., description="Scheduled task ID"),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a scheduled task.

    Deletes the specified scheduled task.
    Authorization is enforced at the service layer.

    Args:
        organization_id: ID of the organization
        task_id: ID of the scheduled task
        current_user: Authenticated user making the request

    Raises:
        HTTPException: If task not found or unauthorized
    """
    service = TaskSchedulerService()
    success = await service.delete_task(current_user, organization_id, task_id)

    if not success:
        raise HTTPException(status_code=404, detail="Scheduled task not found or insufficient permissions")
