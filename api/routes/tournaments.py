"""Tournament-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from api.schemas.tournament import (
    TournamentOut,
    TournamentListResponse,
    TournamentCreateRequest,
    TournamentUpdateRequest,
    MatchOut,
    MatchListResponse,
    MatchCreateRequest,
    MatchUpdateRequest,
    MatchAdvanceStatusRequest,
    TournamentPlayerOut,
    TournamentPlayerListResponse,
    CrewOut,
    CrewApprovalRequest,
)
from api.deps import get_current_user, enforce_rate_limit
from application.services.tournaments.tournament_service import TournamentService
from models import User

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


# ==================== TOURNAMENTS ====================


@router.get(
    "/organizations/{organization_id}",
    response_model=TournamentListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Tournaments",
    description="List all tournaments for an organization. Authorization enforced at service layer.",
    responses={
        200: {"description": "Tournaments retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_tournaments(
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> TournamentListResponse:
    """
    List organization tournaments.

    Returns all tournaments for the specified organization.
    Authorization is enforced at the service layer.

    Args:
        organization_id: ID of the organization
        current_user: Authenticated user making the request

    Returns:
        TournamentListResponse: List of tournaments (empty if unauthorized)
    """
    service = TournamentService()
    tournaments = await service.list_org_tournaments(current_user, organization_id)
    items = [TournamentOut.model_validate(tournament) for tournament in tournaments]
    return TournamentListResponse(items=items, count=len(items))


@router.post(
    "/organizations/{organization_id}",
    response_model=TournamentOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Tournament",
    description="Create a new tournament. Authorization enforced at service layer.",
    responses={
        201: {"description": "Tournament created successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def create_tournament(
    data: TournamentCreateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> TournamentOut:
    """
    Create a tournament.

    Creates a new tournament in the organization.
    Authorization is enforced at the service layer.

    Args:
        organization_id: ID of the organization
        data: Tournament creation data
        current_user: Authenticated user making the request

    Returns:
        TournamentOut: Created tournament

    Raises:
        HTTPException: 403 if user lacks permission
    """
    service = TournamentService()
    tournament = await service.create_tournament(
        user=current_user,
        organization_id=organization_id,
        name=data.name,
        description=data.description,
        is_active=data.is_active,
        tracker_enabled=data.tracker_enabled
    )

    if not tournament:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to create tournaments"
        )

    return TournamentOut.model_validate(tournament)


@router.patch(
    "/{tournament_id}",
    response_model=TournamentOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Tournament",
    description="Update a tournament. Authorization enforced at service layer.",
    responses={
        200: {"description": "Tournament updated successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Tournament not found"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def update_tournament(
    data: TournamentUpdateRequest,
    tournament_id: int = Path(..., description="Tournament ID"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> TournamentOut:
    """
    Update a tournament.

    Updates an existing tournament.
    Authorization is enforced at the service layer.

    Args:
        tournament_id: ID of the tournament to update
        organization_id: Organization ID (for authorization)
        data: Tournament update data
        current_user: Authenticated user making the request

    Returns:
        TournamentOut: Updated tournament

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if tournament not found
    """
    service = TournamentService()
    tournament = await service.update_tournament(
        user=current_user,
        organization_id=organization_id,
        tournament_id=tournament_id,
        name=data.name,
        description=data.description,
        is_active=data.is_active,
        tracker_enabled=data.tracker_enabled
    )

    if not tournament:
        raise HTTPException(
            status_code=403,
            detail="Tournament not found or insufficient permissions"
        )

    return TournamentOut.model_validate(tournament)


@router.delete(
    "/{tournament_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Tournament",
    description="Delete a tournament. Authorization enforced at service layer.",
    responses={
        204: {"description": "Tournament deleted successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Tournament not found"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=204,
)
async def delete_tournament(
    tournament_id: int = Path(..., description="Tournament ID"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a tournament.

    Deletes a tournament permanently.
    Authorization is enforced at the service layer.

    Args:
        tournament_id: ID of the tournament to delete
        organization_id: Organization ID (for authorization)
        current_user: Authenticated user making the request

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if tournament not found
    """
    service = TournamentService()
    success = await service.delete_tournament(
        user=current_user,
        organization_id=organization_id,
        tournament_id=tournament_id
    )

    if not success:
        raise HTTPException(
            status_code=403,
            detail="Tournament not found or insufficient permissions"
        )


# ==================== TOURNAMENT PLAYERS ====================


@router.get(
    "/{tournament_id}/players",
    response_model=TournamentPlayerListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Tournament Players",
    description="List all players registered for a tournament.",
    responses={
        200: {"description": "Players retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_tournament_players(
    tournament_id: int = Path(..., description="Tournament ID"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)  # noqa: ARG001 - authentication required
) -> TournamentPlayerListResponse:
    """
    List tournament players.

    Returns all players registered for the tournament.

    Args:
        tournament_id: ID of the tournament
        organization_id: Organization ID
        current_user: Authenticated user making the request

    Returns:
        TournamentPlayerListResponse: List of registered players
    """
    service = TournamentService()
    players = await service.list_tournament_players(organization_id, tournament_id)
    items = [TournamentPlayerOut.model_validate(player) for player in players]
    return TournamentPlayerListResponse(items=items, count=len(items))


@router.post(
    "/{tournament_id}/players/{user_id}",
    response_model=TournamentPlayerOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Register Player",
    description="Register a player for a tournament.",
    responses={
        201: {"description": "Player registered successfully"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Tournament not found"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def register_player(
    tournament_id: int = Path(..., description="Tournament ID"),
    user_id: int = Path(..., description="User ID to register"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)  # noqa: ARG001 - authentication required
) -> TournamentPlayerOut:
    """
    Register a player for tournament.

    Registers a user for the specified tournament.

    Args:
        tournament_id: ID of the tournament
        user_id: ID of the user to register
        organization_id: Organization ID
        current_user: Authenticated user making the request

    Returns:
        TournamentPlayerOut: Registration record

    Raises:
        HTTPException: 404 if tournament not found
    """
    service = TournamentService()
    registration = await service.register_user_for_tournament(
        organization_id,
        tournament_id,
        user_id
    )

    if not registration:
        raise HTTPException(status_code=404, detail="Tournament not found")

    return TournamentPlayerOut.model_validate(registration)


@router.delete(
    "/{tournament_id}/players/{user_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Unregister Player",
    description="Unregister a player from a tournament.",
    responses={
        204: {"description": "Player unregistered successfully"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Tournament or player not found"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=204,
)
async def unregister_player(
    tournament_id: int = Path(..., description="Tournament ID"),
    user_id: int = Path(..., description="User ID to unregister"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)  # noqa: ARG001 - authentication required
) -> None:
    """
    Unregister a player from tournament.

    Removes a user's registration from the specified tournament.

    Args:
        tournament_id: ID of the tournament
        user_id: ID of the user to unregister
        organization_id: Organization ID
        current_user: Authenticated user making the request

    Raises:
        HTTPException: 404 if tournament or player not found
    """
    service = TournamentService()
    success = await service.unregister_user_from_tournament(
        organization_id,
        tournament_id,
        user_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Tournament or player not found")


# ==================== MATCHES ====================


@router.get(
    "/organizations/{organization_id}/matches",
    response_model=MatchListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Matches",
    description="List all matches for an organization.",
    responses={
        200: {"description": "Matches retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_matches(
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)  # noqa: ARG001 - authentication required
) -> MatchListResponse:
    """
    List organization matches.

    Returns all matches for the specified organization.

    Args:
        organization_id: ID of the organization
        current_user: Authenticated user making the request

    Returns:
        MatchListResponse: List of matches
    """
    service = TournamentService()
    matches = await service.list_org_matches(organization_id)
    items = [MatchOut.model_validate(match) for match in matches]
    return MatchListResponse(items=items, count=len(items))


@router.post(
    "/matches",
    response_model=MatchOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Match",
    description="Create a new match.",
    responses={
        201: {"description": "Match created successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def create_match(
    data: MatchCreateRequest,
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> MatchOut:
    """
    Create a match.

    Creates a new match in a tournament.

    Args:
        data: Match creation data
        organization_id: Organization ID
        current_user: Authenticated user making the request

    Returns:
        MatchOut: Created match

    Raises:
        HTTPException: 403 if user lacks permission
    """
    service = TournamentService()
    match = await service.create_match(
        user=current_user,
        organization_id=organization_id,
        tournament_id=data.tournament_id,
        player_ids=data.player_ids,
        scheduled_at=data.scheduled_at,
        title=data.title,
        comment=data.comment
    )

    if not match:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions or invalid tournament"
        )

    return MatchOut.model_validate(match)


@router.patch(
    "/matches/{match_id}",
    response_model=MatchOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Match",
    description="Update a match.",
    responses={
        200: {"description": "Match updated successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Match not found"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def update_match(
    data: MatchUpdateRequest,
    match_id: int = Path(..., description="Match ID"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> MatchOut:
    """
    Update a match.

    Updates an existing match.

    Args:
        match_id: ID of the match to update
        organization_id: Organization ID
        data: Match update data
        current_user: Authenticated user making the request

    Returns:
        MatchOut: Updated match

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if match not found
    """
    service = TournamentService()
    match = await service.update_match(
        user=current_user,
        organization_id=organization_id,
        match_id=match_id,
        title=data.title,
        scheduled_at=data.scheduled_at,
        stream_channel_id=data.stream_channel_id,
        comment=data.comment
    )

    if not match:
        raise HTTPException(
            status_code=403,
            detail="Match not found or insufficient permissions"
        )

    return MatchOut.model_validate(match)


@router.post(
    "/matches/{match_id}/advance-status",
    response_model=MatchOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Advance Match Status",
    description="Advance a match to the next status. Requires TOURNAMENT_MANAGER or MODERATOR permission.",
    responses={
        200: {"description": "Match status advanced successfully"},
        400: {"description": "Invalid status value"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Match not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def advance_match_status(
    data: MatchAdvanceStatusRequest,
    match_id: int = Path(..., description="Match ID"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> MatchOut:
    """
    Advance match status.

    Advances a match to the specified status by recording the appropriate timestamp.
    Valid statuses: 'checked_in', 'started', 'finished', 'recorded'.

    Args:
        match_id: ID of the match to update
        organization_id: Organization ID
        data: Status advancement request
        current_user: Authenticated user making the request

    Returns:
        MatchOut: Updated match

    Raises:
        HTTPException: 400 if status is invalid
        HTTPException: 403 if user lacks permission or tournament is read-only
        HTTPException: 404 if match not found
    """
    service = TournamentService()

    try:
        match = await service.advance_match_status(
            user=current_user,
            organization_id=organization_id,
            match_id=match_id,
            status=data.status
        )

        if not match:
            raise HTTPException(
                status_code=403,
                detail="Match not found or insufficient permissions"
            )

        return MatchOut.model_validate(match)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ==================== CREW MANAGEMENT ====================


@router.post(
    "/crew/approve",
    response_model=CrewOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Approve Crew Signup",
    description="Approve a crew signup for a match. Requires ADMIN, TOURNAMENT_MANAGER, or MODERATOR permission.",
    responses={
        200: {"description": "Crew signup approved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Crew signup not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def approve_crew(
    data: CrewApprovalRequest,
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> CrewOut:
    """
    Approve a crew signup.

    Requires ADMIN, TOURNAMENT_MANAGER, or MODERATOR permission in the organization.

    Args:
        data: Crew approval request data
        organization_id: Organization ID
        current_user: Authenticated user making the request

    Returns:
        CrewOut: Approved crew signup

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if crew signup not found
    """
    service = TournamentService()
    crew = await service.approve_crew(
        user=current_user,
        organization_id=organization_id,
        crew_id=data.crew_id
    )

    if not crew:
        raise HTTPException(
            status_code=403,
            detail="Crew signup not found or insufficient permissions"
        )

    return CrewOut.model_validate(crew)


@router.post(
    "/crew/unapprove",
    response_model=CrewOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Unapprove Crew Signup",
    description="Remove approval from a crew signup. Requires ADMIN, TOURNAMENT_MANAGER, or MODERATOR permission.",
    responses={
        200: {"description": "Crew signup unapproved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Crew signup not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def unapprove_crew(
    data: CrewApprovalRequest,
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> CrewOut:
    """
    Remove approval from a crew signup.

    Requires ADMIN, TOURNAMENT_MANAGER, or MODERATOR permission in the organization.

    Args:
        data: Crew approval request data
        organization_id: Organization ID
        current_user: Authenticated user making the request

    Returns:
        CrewOut: Unapproved crew signup

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if crew signup not found
    """
    service = TournamentService()
    crew = await service.unapprove_crew(
        user=current_user,
        organization_id=organization_id,
        crew_id=data.crew_id
    )

    if not crew:
        raise HTTPException(
            status_code=403,
            detail="Crew signup not found or insufficient permissions"
        )

    return CrewOut.model_validate(crew)
