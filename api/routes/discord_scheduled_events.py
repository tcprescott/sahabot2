"""Discord scheduled event API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from api.schemas.discord_scheduled_event import (
    DiscordScheduledEventOut,
    DiscordScheduledEventListResponse,
    SyncEventsRequest,
    SyncEventsResponse,
)
from api.deps import get_current_user, enforce_rate_limit
from application.services.discord.discord_scheduled_event_service import (
    DiscordScheduledEventService,
)
from models import User, Permission

router = APIRouter(prefix="/discord-events", tags=["discord-events"])


async def _can_manage_discord_events(user: User, organization_id: int) -> bool:
    """
    Check if user can manage Discord scheduled events in an organization.

    Requires SUPERADMIN global permission OR ADMIN permission in the organization.
    """
    if not user:
        return False

    # SUPERADMINs can manage Discord events in any organization
    if user.has_permission(Permission.SUPERADMIN):
        return True

    # Check if user has ADMIN permission in the org
    from application.repositories.organization_repository import OrganizationRepository

    repo = OrganizationRepository()
    member = await repo.get_member(organization_id, user.id)

    if not member:
        return False

    # Check if member has admin permissions
    await member.fetch_related("permissions")
    permission_names = [p.permission_name for p in member.permissions]

    return "ADMIN" in permission_names


# ==================== DISCORD SCHEDULED EVENTS ====================


@router.get(
    "/organizations/{organization_id}",
    response_model=DiscordScheduledEventListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Discord Scheduled Events",
    description="List all Discord scheduled events for an organization. Requires MODERATOR or ADMIN permission.",
    responses={
        200: {"description": "Events retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_events(
    organization_id: int = Path(..., description="Organization ID"),
    tournament_id: int = Query(None, description="Filter by tournament ID"),
    current_user: User = Depends(get_current_user),
) -> DiscordScheduledEventListResponse:
    """
    List Discord scheduled events for an organization.

    Returns all Discord scheduled events for the specified organization.
    Optionally filter by tournament ID.

    Args:
        organization_id: ID of the organization
        tournament_id: Optional tournament ID filter
        current_user: Authenticated user making the request

    Returns:
        DiscordScheduledEventListResponse: List of events

    Raises:
        HTTPException: 403 if user lacks permission
    """
    # Check permissions
    if not await _can_manage_discord_events(current_user, organization_id):
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to manage Discord events"
        )

    service = DiscordScheduledEventService()

    if tournament_id:
        events = await service.repo.list_for_tournament(organization_id, tournament_id)
    else:
        events = await service.repo.list_for_org(organization_id)

    items = [DiscordScheduledEventOut.model_validate(event) for event in events]
    return DiscordScheduledEventListResponse(items=items, count=len(items))


@router.get(
    "/organizations/{organization_id}/matches/{match_id}",
    response_model=DiscordScheduledEventListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Events for Match",
    description="Get all Discord scheduled events for a specific match. Requires MODERATOR or ADMIN permission.",
    responses={
        200: {"description": "Events retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_match_events(
    organization_id: int = Path(..., description="Organization ID"),
    match_id: int = Path(..., description="Match ID"),
    current_user: User = Depends(get_current_user),
) -> DiscordScheduledEventListResponse:
    """
    Get all Discord scheduled events for a match.

    Returns all Discord scheduled events associated with the specified match.

    Args:
        organization_id: ID of the organization
        match_id: ID of the match
        current_user: Authenticated user making the request

    Returns:
        DiscordScheduledEventListResponse: List of events for the match

    Raises:
        HTTPException: 403 if user lacks permission
    """
    # Check permissions
    if not await _can_manage_discord_events(current_user, organization_id):
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to manage Discord events"
        )

    service = DiscordScheduledEventService()
    events = await service.repo.list_for_match(organization_id, match_id)

    items = [DiscordScheduledEventOut.model_validate(event) for event in events]
    return DiscordScheduledEventListResponse(items=items, count=len(items))


@router.post(
    "/organizations/{organization_id}/sync",
    response_model=SyncEventsResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Sync Discord Events",
    description="Synchronize Discord scheduled events for a tournament. Requires MODERATOR or ADMIN permission.",
    responses={
        200: {"description": "Sync completed successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def sync_events(
    data: SyncEventsRequest,
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> SyncEventsResponse:
    """
    Synchronize Discord scheduled events for a tournament.

    Creates, updates, or deletes Discord scheduled events to match the current
    tournament match schedule. This operation:
    - Creates events for newly scheduled matches
    - Updates events for matches with changed details
    - Deletes events for completed or deleted matches

    Args:
        organization_id: ID of the organization
        data: Sync request with tournament_id
        current_user: Authenticated user making the request

    Returns:
        SyncEventsResponse: Sync results with statistics

    Raises:
        HTTPException: 403 if user lacks permission
    """
    # Check permissions
    if not await _can_manage_discord_events(current_user, organization_id):
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to manage Discord events"
        )

    service = DiscordScheduledEventService()
    stats = await service.sync_tournament_events(
        user_id=current_user.id,
        organization_id=organization_id,
        tournament_id=data.tournament_id,
    )

    # Build message
    message_parts = []
    if stats["created"]:
        message_parts.append(f"Created {stats['created']} event(s)")
    if stats["updated"]:
        message_parts.append(f"Updated {stats['updated']} event(s)")
    if stats["deleted"]:
        message_parts.append(f"Deleted {stats['deleted']} event(s)")
    if stats["skipped"]:
        message_parts.append(f"Skipped {stats['skipped']} event(s)")

    if stats["errors"]:
        message_parts.append(f"Encountered {stats['errors']} error(s)")
        message = f"Sync completed with errors: {', '.join(message_parts)}"
        success = False
    elif not message_parts:
        message = "No changes needed - events are already synchronized"
        success = True
    else:
        message = f"Sync successful: {', '.join(message_parts)}"
        success = True

    return SyncEventsResponse(
        success=success,
        stats=stats,
        message=message,
    )


@router.delete(
    "/organizations/{organization_id}/matches/{match_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Events for Match",
    description="Delete all Discord scheduled events for a match. Requires MODERATOR or ADMIN permission.",
    responses={
        204: {"description": "Events deleted successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Match not found"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=204,
)
async def delete_match_events(
    organization_id: int = Path(..., description="Organization ID"),
    match_id: int = Path(..., description="Match ID"),
    current_user: User = Depends(get_current_user),
):
    """
    Delete all Discord scheduled events for a match.

    Removes all Discord scheduled events associated with the specified match
    from all configured Discord servers.

    Args:
        organization_id: ID of the organization
        match_id: ID of the match
        current_user: Authenticated user making the request

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if match not found
    """
    # Check permissions
    if not await _can_manage_discord_events(current_user, organization_id):
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to manage Discord events"
        )

    service = DiscordScheduledEventService()
    success = await service.delete_event_for_match(
        user_id=current_user.id,
        organization_id=organization_id,
        match_id=match_id,
    )

    if not success:
        raise HTTPException(
            status_code=404, detail="Match not found or events already deleted"
        )

    return None
