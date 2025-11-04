"""Async Live Race-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from api.schemas.async_live_race import (
    AsyncLiveRaceOut,
    AsyncLiveRaceListResponse,
    AsyncLiveRaceCreateRequest,
    AsyncLiveRaceUpdateRequest,
    EligibleParticipantOut,
    EligibleParticipantsResponse,
)
from api.deps import get_current_user, enforce_rate_limit
from application.services.async_live_race_service import AsyncLiveRaceService
from models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/async-live-races", tags=["async-live-races"])


# ==================== ASYNC LIVE RACES ====================


@router.get(
    "/organizations/{organization_id}/tournaments/{tournament_id}",
    response_model=AsyncLiveRaceListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Live Races for Tournament",
    description="List all live races for a tournament. Authorization enforced at service layer.",
    responses={
        200: {"description": "Live races retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_live_races(
    organization_id: int = Path(..., description="Organization ID"),
    tournament_id: int = Path(..., description="Tournament ID"),
    status: str | None = Query(None, description="Filter by status (scheduled/pending/in_progress/finished/cancelled)"),
    current_user: User = Depends(get_current_user),
) -> AsyncLiveRaceListResponse:
    """
    List live races for a tournament.

    Returns all live races for the specified tournament, optionally filtered by status.
    Authorization is enforced at the service layer.

    Args:
        organization_id: ID of the organization
        tournament_id: ID of the tournament
        status: Optional status filter
        current_user: Authenticated user making the request

    Returns:
        AsyncLiveRaceListResponse: List of live races (empty if unauthorized)
    """
    service = AsyncLiveRaceService()
    races = await service.list_live_races(organization_id, tournament_id, status)

    # Fetch related data for response
    items = []
    for race in races:
        await race.fetch_related('pool', 'permalink')
        item_dict = {
            'id': race.id,
            'tournament_id': race.tournament_id,
            'pool_id': race.pool_id,
            'pool_name': race.pool.name if race.pool else None,
            'permalink_id': race.permalink_id,
            'permalink_url': race.permalink.url if race.permalink else None,
            'episode_id': race.episode_id,
            'scheduled_at': race.scheduled_at,
            'match_title': race.match_title,
            'racetime_slug': race.racetime_slug,
            'racetime_url': race.racetime_url,
            'racetime_goal': race.racetime_goal,
            'room_open_time': race.room_open_time,
            'race_room_profile_id': race.race_room_profile_id,
            'status': race.status,
            'participant_count': 0,  # Will be counted in future
            'created_at': race.created_at,
            'updated_at': race.updated_at,
        }
        items.append(AsyncLiveRaceOut.model_validate(item_dict))

    return AsyncLiveRaceListResponse(items=items, count=len(items))


@router.get(
    "/organizations/{organization_id}/scheduled",
    response_model=AsyncLiveRaceListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Scheduled Live Races",
    description="List upcoming scheduled live races for an organization. Authorization enforced at service layer.",
    responses={
        200: {"description": "Scheduled races retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_scheduled_races(
    organization_id: int = Path(..., description="Organization ID"),
    tournament_id: int | None = Query(None, description="Optional tournament filter"),
    current_user: User = Depends(get_current_user),
) -> AsyncLiveRaceListResponse:
    """
    List upcoming scheduled live races.

    Returns upcoming scheduled races for the organization, optionally filtered by tournament.
    Authorization is enforced at the service layer.

    Args:
        organization_id: ID of the organization
        tournament_id: Optional tournament ID filter
        current_user: Authenticated user making the request

    Returns:
        AsyncLiveRaceListResponse: List of scheduled races (empty if unauthorized)
    """
    service = AsyncLiveRaceService()
    races = await service.list_scheduled_races(organization_id, tournament_id)

    # Fetch related data for response
    items = []
    for race in races:
        await race.fetch_related('pool', 'permalink')
        item_dict = {
            'id': race.id,
            'tournament_id': race.tournament_id,
            'pool_id': race.pool_id,
            'pool_name': race.pool.name if race.pool else None,
            'permalink_id': race.permalink_id,
            'permalink_url': race.permalink.url if race.permalink else None,
            'episode_id': race.episode_id,
            'scheduled_at': race.scheduled_at,
            'match_title': race.match_title,
            'racetime_slug': race.racetime_slug,
            'racetime_url': race.racetime_url,
            'racetime_goal': race.racetime_goal,
            'room_open_time': race.room_open_time,
            'race_room_profile_id': race.race_room_profile_id,
            'status': race.status,
            'participant_count': 0,  # Will be counted in future
            'created_at': race.created_at,
            'updated_at': race.updated_at,
        }
        items.append(AsyncLiveRaceOut.model_validate(item_dict))

    return AsyncLiveRaceListResponse(items=items, count=len(items))


@router.get(
    "/{live_race_id}",
    response_model=AsyncLiveRaceOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Live Race",
    description="Get a specific live race by ID. Authorization enforced at service layer.",
    responses={
        200: {"description": "Live race retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Live race not found or access denied"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_live_race(
    live_race_id: int = Path(..., description="Live race ID"),
    organization_id: int = Query(..., description="Organization ID for scoping"),
    current_user: User = Depends(get_current_user),
) -> AsyncLiveRaceOut:
    """
    Get a specific live race.

    Returns details for a specific live race.
    Authorization is enforced at the service layer.

    Args:
        live_race_id: ID of the live race
        organization_id: Organization ID for scoping
        current_user: Authenticated user making the request

    Returns:
        AsyncLiveRaceOut: Live race details

    Raises:
        HTTPException: 404 if race not found or access denied
    """
    service = AsyncLiveRaceService()
    race = await service.get_live_race(organization_id, live_race_id)

    if not race:
        raise HTTPException(status_code=404, detail="Live race not found or access denied")

    # Fetch related data for response
    await race.fetch_related('pool', 'permalink')
    item_dict = {
        'id': race.id,
        'tournament_id': race.tournament_id,
        'pool_id': race.pool_id,
        'pool_name': race.pool.name if race.pool else None,
        'permalink_id': race.permalink_id,
        'permalink_url': race.permalink.url if race.permalink else None,
        'episode_id': race.episode_id,
        'scheduled_at': race.scheduled_at,
        'match_title': race.match_title,
        'racetime_slug': race.racetime_slug,
        'racetime_url': race.racetime_url,
        'racetime_goal': race.racetime_goal,
        'room_open_time': race.room_open_time,
        'race_room_profile_id': race.race_room_profile_id,
        'status': race.status,
        'participant_count': 0,  # Will be counted in future
        'created_at': race.created_at,
        'updated_at': race.updated_at,
    }

    return AsyncLiveRaceOut.model_validate(item_dict)


@router.post(
    "/organizations/{organization_id}/tournaments/{tournament_id}",
    response_model=AsyncLiveRaceOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Live Race",
    description="Create a new scheduled live race. Authorization enforced at service layer.",
    responses={
        201: {"description": "Live race created successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def create_live_race(
    data: AsyncLiveRaceCreateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> AsyncLiveRaceOut:
    """
    Create a new scheduled live race.

    Creates a new live race for the specified tournament.
    Requires ASYNC_TOURNAMENT_ADMIN or ADMIN permission.

    Args:
        data: Live race creation data
        organization_id: Organization ID
        current_user: Authenticated user making the request

    Returns:
        AsyncLiveRaceOut: Created live race

    Raises:
        HTTPException: 403 if insufficient permissions, 422 if invalid data
    """
    service = AsyncLiveRaceService()

    try:
        race = await service.create_live_race(
            current_user=current_user,
            organization_id=organization_id,
            tournament_id=data.tournament_id,
            pool_id=data.pool_id,
            scheduled_at=data.scheduled_at,
            match_title=data.match_title,
            permalink_id=data.permalink_id,
            episode_id=data.episode_id,
            race_room_profile_id=data.race_room_profile_id,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Fetch related data for response
    await race.fetch_related('pool', 'permalink')
    item_dict = {
        'id': race.id,
        'tournament_id': race.tournament_id,
        'pool_id': race.pool_id,
        'pool_name': race.pool.name if race.pool else None,
        'permalink_id': race.permalink_id,
        'permalink_url': race.permalink.url if race.permalink else None,
        'episode_id': race.episode_id,
        'scheduled_at': race.scheduled_at,
        'match_title': race.match_title,
        'racetime_slug': race.racetime_slug,
        'racetime_url': race.racetime_url,
        'racetime_goal': race.racetime_goal,
        'room_open_time': race.room_open_time,
        'race_room_profile_id': race.race_room_profile_id,
        'status': race.status,
        'participant_count': 0,
        'created_at': race.created_at,
        'updated_at': race.updated_at,
    }

    return AsyncLiveRaceOut.model_validate(item_dict)


@router.patch(
    "/{live_race_id}",
    response_model=AsyncLiveRaceOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Live Race",
    description="Update a live race. Authorization enforced at service layer.",
    responses={
        200: {"description": "Live race updated successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Live race not found"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def update_live_race(
    data: AsyncLiveRaceUpdateRequest,
    live_race_id: int = Path(..., description="Live race ID"),
    organization_id: int = Query(..., description="Organization ID for scoping"),
    current_user: User = Depends(get_current_user),
) -> AsyncLiveRaceOut:
    """
    Update a live race.

    Updates the specified live race.
    Requires ASYNC_TOURNAMENT_ADMIN or ADMIN permission.

    Args:
        data: Live race update data
        live_race_id: Live race ID
        organization_id: Organization ID for scoping
        current_user: Authenticated user making the request

    Returns:
        AsyncLiveRaceOut: Updated live race

    Raises:
        HTTPException: 403 if insufficient permissions, 404 if not found, 422 if invalid data
    """
    service = AsyncLiveRaceService()

    # Build updates dict from non-None fields
    updates = {k: v for k, v in data.model_dump().items() if v is not None}

    try:
        race = await service.update_live_race(
            current_user=current_user,
            organization_id=organization_id,
            live_race_id=live_race_id,
            **updates,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Fetch related data for response
    await race.fetch_related('pool', 'permalink')
    item_dict = {
        'id': race.id,
        'tournament_id': race.tournament_id,
        'pool_id': race.pool_id,
        'pool_name': race.pool.name if race.pool else None,
        'permalink_id': race.permalink_id,
        'permalink_url': race.permalink.url if race.permalink else None,
        'episode_id': race.episode_id,
        'scheduled_at': race.scheduled_at,
        'match_title': race.match_title,
        'racetime_slug': race.racetime_slug,
        'racetime_url': race.racetime_url,
        'racetime_goal': race.racetime_goal,
        'room_open_time': race.room_open_time,
        'race_room_profile_id': race.race_room_profile_id,
        'status': race.status,
        'participant_count': 0,
        'created_at': race.created_at,
        'updated_at': race.updated_at,
    }

    return AsyncLiveRaceOut.model_validate(item_dict)


@router.delete(
    "/{live_race_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Live Race",
    description="Delete a live race. Authorization enforced at service layer.",
    responses={
        204: {"description": "Live race deleted successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Live race not found"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=204,
)
async def delete_live_race(
    live_race_id: int = Path(..., description="Live race ID"),
    organization_id: int = Query(..., description="Organization ID for scoping"),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a live race.

    Deletes the specified live race (hard delete).
    Only allows deleting races that haven't started.
    Requires ASYNC_TOURNAMENT_ADMIN or ADMIN permission.

    Args:
        live_race_id: Live race ID
        organization_id: Organization ID for scoping
        current_user: Authenticated user making the request

    Raises:
        HTTPException: 403 if insufficient permissions, 404 if not found, 422 if invalid state
    """
    service = AsyncLiveRaceService()

    try:
        await service.delete_live_race(
            current_user=current_user,
            organization_id=organization_id,
            live_race_id=live_race_id,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/{live_race_id}/cancel",
    response_model=AsyncLiveRaceOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Cancel Live Race",
    description="Cancel a live race. Authorization enforced at service layer.",
    responses={
        200: {"description": "Live race cancelled successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Live race not found"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def cancel_live_race(
    live_race_id: int = Path(..., description="Live race ID"),
    organization_id: int = Query(..., description="Organization ID for scoping"),
    reason: str | None = Query(None, description="Optional cancellation reason"),
    current_user: User = Depends(get_current_user),
) -> AsyncLiveRaceOut:
    """
    Cancel a live race.

    Cancels the specified live race.
    Requires ASYNC_TOURNAMENT_ADMIN or ADMIN permission.

    Args:
        live_race_id: Live race ID
        organization_id: Organization ID for scoping
        reason: Optional cancellation reason
        current_user: Authenticated user making the request

    Returns:
        AsyncLiveRaceOut: Cancelled live race

    Raises:
        HTTPException: 403 if insufficient permissions, 404 if not found, 422 if invalid state
    """
    service = AsyncLiveRaceService()

    try:
        race = await service.cancel_live_race(
            current_user=current_user,
            organization_id=organization_id,
            live_race_id=live_race_id,
            reason=reason,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Fetch related data for response
    await race.fetch_related('pool', 'permalink')
    item_dict = {
        'id': race.id,
        'tournament_id': race.tournament_id,
        'pool_id': race.pool_id,
        'pool_name': race.pool.name if race.pool else None,
        'permalink_id': race.permalink_id,
        'permalink_url': race.permalink.url if race.permalink else None,
        'episode_id': race.episode_id,
        'scheduled_at': race.scheduled_at,
        'match_title': race.match_title,
        'racetime_slug': race.racetime_slug,
        'racetime_url': race.racetime_url,
        'racetime_goal': race.racetime_goal,
        'room_open_time': race.room_open_time,
        'race_room_profile_id': race.race_room_profile_id,
        'status': race.status,
        'participant_count': 0,
        'created_at': race.created_at,
        'updated_at': race.updated_at,
    }

    return AsyncLiveRaceOut.model_validate(item_dict)


@router.get(
    "/{live_race_id}/eligible",
    response_model=EligibleParticipantsResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Eligible Participants",
    description="Get list of eligible participants for a live race. Authorization enforced at service layer.",
    responses={
        200: {"description": "Eligible participants retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Live race not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_eligible_participants(
    live_race_id: int = Path(..., description="Live race ID"),
    organization_id: int = Query(..., description="Organization ID for scoping"),
    current_user: User = Depends(get_current_user),
) -> EligibleParticipantsResponse:
    """
    Get eligible participants for a live race.

    Returns a list of all participants with their eligibility status.

    Args:
        live_race_id: Live race ID
        organization_id: Organization ID for scoping
        current_user: Authenticated user making the request

    Returns:
        EligibleParticipantsResponse: List of participants with eligibility info

    Raises:
        HTTPException: 404 if race not found
    """
    service = AsyncLiveRaceService()

    try:
        eligibility_list = await service.get_eligible_participants(organization_id, live_race_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Convert to response format
    items = [
        EligibleParticipantOut(
            user_id=e.user.id,
            discord_username=e.user.discord_username,
            is_eligible=e.is_eligible,
            reason=e.reason,
        )
        for e in eligibility_list
    ]

    eligible_count = sum(1 for e in eligibility_list if e.is_eligible)

    return EligibleParticipantsResponse(
        items=items,
        count=len(items),
        eligible_count=eligible_count,
    )
