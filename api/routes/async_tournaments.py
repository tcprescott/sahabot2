"""Async Tournament-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from api.schemas.async_tournament import (
    AsyncTournamentOut,
    AsyncTournamentListResponse,
    AsyncTournamentCreateRequest,
    AsyncTournamentUpdateRequest,
)
from api.deps import get_current_user, enforce_rate_limit
from application.services.async_tournament_service import AsyncTournamentService
from models import User

router = APIRouter(prefix="/async-tournaments", tags=["async-tournaments"])


# ==================== ASYNC TOURNAMENTS ====================


@router.get(
    "/organizations/{organization_id}",
    response_model=AsyncTournamentListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Async Tournaments",
    description="List all async tournaments for an organization. Authorization enforced at service layer.",
    responses={
        200: {"description": "Async tournaments retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_async_tournaments(
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> AsyncTournamentListResponse:
    """
    List organization async tournaments.

    Returns all async tournaments for the specified organization.
    Authorization is enforced at the service layer.

    Args:
        organization_id: ID of the organization
        current_user: Authenticated user making the request

    Returns:
        AsyncTournamentListResponse: List of async tournaments (empty if unauthorized)
    """
    service = AsyncTournamentService()
    tournaments = await service.list_org_tournaments(current_user, organization_id)
    items = [AsyncTournamentOut.model_validate(tournament) for tournament in tournaments]
    return AsyncTournamentListResponse(items=items, count=len(items))


@router.post(
    "/organizations/{organization_id}",
    response_model=AsyncTournamentOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Async Tournament",
    description="Create a new async tournament. Authorization enforced at service layer.",
    responses={
        201: {"description": "Async tournament created successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def create_async_tournament(
    data: AsyncTournamentCreateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> AsyncTournamentOut:
    """
    Create an async tournament.

    Creates a new async tournament in the organization.
    Authorization is enforced at the service layer.

    Args:
        organization_id: ID of the organization
        data: Async tournament creation data
        current_user: Authenticated user making the request

    Returns:
        AsyncTournamentOut: Created async tournament

    Raises:
        HTTPException: 403 if user lacks permission
    """
    service = AsyncTournamentService()
    tournament = await service.create_tournament(
        user=current_user,
        organization_id=organization_id,
        name=data.name,
        description=data.description,
        is_active=data.is_active,
        discord_channel_id=data.discord_channel_id,
        runs_per_pool=data.runs_per_pool,
    )

    if not tournament:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to create async tournament"
        )

    return AsyncTournamentOut.model_validate(tournament)


@router.get(
    "/{tournament_id}",
    response_model=AsyncTournamentOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Async Tournament",
    description="Get a specific async tournament by ID. Authorization enforced at service layer.",
    responses={
        200: {"description": "Async tournament retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Tournament not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_async_tournament(
    tournament_id: int = Path(..., description="Tournament ID"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> AsyncTournamentOut:
    """
    Get an async tournament by ID.

    Authorization is enforced at the service layer.

    Args:
        tournament_id: ID of the tournament
        organization_id: ID of the organization
        current_user: Authenticated user making the request

    Returns:
        AsyncTournamentOut: The async tournament

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if tournament not found
    """
    service = AsyncTournamentService()
    tournament = await service.get_tournament(current_user, organization_id, tournament_id)

    if not tournament:
        raise HTTPException(
            status_code=404,
            detail="Async tournament not found or you lack permission to view it"
        )

    return AsyncTournamentOut.model_validate(tournament)


@router.patch(
    "/{tournament_id}",
    response_model=AsyncTournamentOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Async Tournament",
    description="Update an async tournament. Authorization enforced at service layer.",
    responses={
        200: {"description": "Async tournament updated successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Tournament not found"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def update_async_tournament(
    data: AsyncTournamentUpdateRequest,
    tournament_id: int = Path(..., description="Tournament ID"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> AsyncTournamentOut:
    """
    Update an async tournament.

    Only provided fields will be updated.
    Authorization is enforced at the service layer.

    Args:
        tournament_id: ID of the tournament to update
        organization_id: ID of the organization
        data: Tournament update data
        current_user: Authenticated user making the request

    Returns:
        AsyncTournamentOut: Updated async tournament

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if tournament not found
    """
    service = AsyncTournamentService()
    
    # Build update fields from request
    update_fields = {}
    if data.name is not None:
        update_fields['name'] = data.name
    if data.description is not None:
        update_fields['description'] = data.description
    if data.is_active is not None:
        update_fields['is_active'] = data.is_active
    if data.discord_channel_id is not None:
        update_fields['discord_channel_id'] = data.discord_channel_id
    if data.runs_per_pool is not None:
        update_fields['runs_per_pool'] = data.runs_per_pool

    tournament = await service.update_tournament(
        user=current_user,
        organization_id=organization_id,
        tournament_id=tournament_id,
        **update_fields
    )

    if not tournament:
        raise HTTPException(
            status_code=404,
            detail="Async tournament not found or insufficient permissions"
        )

    return AsyncTournamentOut.model_validate(tournament)


@router.delete(
    "/{tournament_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Async Tournament",
    description="Delete an async tournament. Authorization enforced at service layer.",
    responses={
        204: {"description": "Async tournament deleted successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Tournament not found"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=204,
)
async def delete_async_tournament(
    tournament_id: int = Path(..., description="Tournament ID"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete an async tournament.

    This will also delete all associated pools, permalinks, and race data.
    Authorization is enforced at the service layer.

    Args:
        tournament_id: ID of the tournament to delete
        organization_id: ID of the organization
        current_user: Authenticated user making the request

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if tournament not found
    """
    service = AsyncTournamentService()
    success = await service.delete_tournament(
        user=current_user,
        organization_id=organization_id,
        tournament_id=tournament_id
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Async tournament not found or insufficient permissions"
        )
