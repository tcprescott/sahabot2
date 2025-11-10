"""Async Qualifier-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from api.schemas.async_qualifier import (
    AsyncQualifierOut,
    AsyncQualifierListResponse,
    AsyncQualifierCreateRequest,
    AsyncQualifierCreateResponse,
    AsyncQualifierUpdateRequest,
    AsyncQualifierRaceReviewOut,
    AsyncQualifierRaceReviewListResponse,
    AsyncQualifierRaceReviewUpdateRequest,
    AsyncQualifierRaceUpdateRequest,
    UserBasicInfo,
)
from api.deps import get_current_user, enforce_rate_limit
from application.services.tournaments.async_qualifier_service import (
    AsyncQualifierService,
)
from models import User

router = APIRouter(prefix="/async-qualifiers", tags=["async-qualifiers"])


# ==================== ASYNC QUALIFIERS ====================


@router.get(
    "/organizations/{organization_id}",
    response_model=AsyncQualifierListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Async Qualifiers",
    description="List all async qualifiers for an organization. Authorization enforced at service layer.",
    responses={
        200: {"description": "Async qualifiers retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_async_qualifiers(
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> AsyncQualifierListResponse:
    """
    List organization async qualifiers.

    Returns all async qualifiers for the specified organization.
    Authorization is enforced at the service layer.

    Args:
        organization_id: ID of the organization
        current_user: Authenticated user making the request

    Returns:
        AsyncQualifierListResponse: List of async qualifiers (empty if unauthorized)
    """
    service = AsyncQualifierService()
    tournaments = await service.list_org_qualifiers(current_user, organization_id)
    items = [
        AsyncQualifierOut.model_validate(tournament) for tournament in tournaments
    ]
    return AsyncQualifierListResponse(items=items, count=len(items))


@router.post(
    "/organizations/{organization_id}",
    response_model=AsyncQualifierOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Async Qualifier",
    description="Create a new async qualifier. Authorization enforced at service layer.",
    responses={
        201: {"description": "Async qualifier created successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def create_async_qualifier(
    data: AsyncQualifierCreateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> AsyncQualifierCreateResponse:
    """
    Create an async qualifier.

    Creates a new async qualifier in the organization.
    Authorization is enforced at the service layer.

    Args:
        organization_id: ID of the organization
        data: Async tournament creation data
        current_user: Authenticated user making the request

    Returns:
        AsyncQualifierCreateResponse: Created async qualifier with any warnings

    Raises:
        HTTPException: 403 if user lacks permission
    """
    service = AsyncQualifierService()
    tournament, warnings = await service.create_qualifier(
        user=current_user,
        organization_id=organization_id,
        name=data.name,
        description=data.description,
        is_active=data.is_active,
        discord_channel_id=data.discord_channel_id,
        runs_per_pool=data.runs_per_pool,
        require_racetime_for_async_runs=data.require_racetime_for_async_runs,
    )

    if not tournament:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to create async qualifier",
        )

    return AsyncQualifierCreateResponse(
        tournament=AsyncQualifierOut.model_validate(tournament), warnings=warnings
    )


@router.get(
    "/{tournament_id}",
    response_model=AsyncQualifierOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Async Qualifier",
    description="Get a specific async qualifier by ID. Authorization enforced at service layer.",
    responses={
        200: {"description": "Async qualifier retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Tournament not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_async_qualifier(
    tournament_id: int = Path(..., description="Tournament ID"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> AsyncQualifierOut:
    """
    Get an async qualifier by ID.

    Authorization is enforced at the service layer.

    Args:
        tournament_id: ID of the tournament
        organization_id: ID of the organization
        current_user: Authenticated user making the request

    Returns:
        AsyncQualifierOut: The async qualifier

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if tournament not found
    """
    service = AsyncQualifierService()
    tournament = await service.get_qualifier(
        current_user, organization_id, tournament_id
    )

    if not tournament:
        raise HTTPException(
            status_code=404,
            detail="Async qualifier not found or you lack permission to view it",
        )

    return AsyncQualifierOut.model_validate(tournament)


@router.patch(
    "/{tournament_id}",
    response_model=AsyncQualifierCreateResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Async Qualifier",
    description="Update an async qualifier. Authorization enforced at service layer.",
    responses={
        200: {"description": "Async qualifier updated successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Tournament not found"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def update_async_qualifier(
    data: AsyncQualifierUpdateRequest,
    tournament_id: int = Path(..., description="Tournament ID"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> AsyncQualifierCreateResponse:
    """
    Update an async qualifier.

    Only provided fields will be updated.
    Authorization is enforced at the service layer.

    Args:
        tournament_id: ID of the tournament to update
        organization_id: ID of the organization
        data: Tournament update data
        current_user: Authenticated user making the request

    Returns:
        AsyncQualifierCreateResponse: Updated async qualifier with any warnings

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if tournament not found
    """
    service = AsyncQualifierService()

    # Build update fields from request
    update_fields = {}
    if data.name is not None:
        update_fields["name"] = data.name
    if data.description is not None:
        update_fields["description"] = data.description
    if data.is_active is not None:
        update_fields["is_active"] = data.is_active
    if data.discord_channel_id is not None:
        update_fields["discord_channel_id"] = data.discord_channel_id
    if data.runs_per_pool is not None:
        update_fields["runs_per_pool"] = data.runs_per_pool

    tournament, warnings = await service.update_qualifier(
        user=current_user,
        organization_id=organization_id,
        tournament_id=tournament_id,
        **update_fields
    )

    if not tournament:
        raise HTTPException(
            status_code=404,
            detail="Async qualifier not found or insufficient permissions",
        )

    return AsyncQualifierCreateResponse(
        tournament=AsyncQualifierOut.model_validate(tournament), warnings=warnings
    )


@router.delete(
    "/{tournament_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Async Qualifier",
    description="Delete an async qualifier. Authorization enforced at service layer.",
    responses={
        204: {"description": "Async qualifier deleted successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Tournament not found"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=204,
)
async def delete_async_qualifier(
    tournament_id: int = Path(..., description="Tournament ID"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete an async qualifier.

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
    service = AsyncQualifierService()
    success = await service.delete_qualifier(
        user=current_user, organization_id=organization_id, tournament_id=tournament_id
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Async qualifier not found or insufficient permissions",
        )


# ==================== RACE REVIEW ====================


@router.get(
    "/{tournament_id}/review-queue",
    response_model=AsyncQualifierRaceReviewListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Review Queue",
    description="Get races awaiting review. Requires ASYNC_REVIEWER or ADMIN permission.",
    responses={
        200: {"description": "Review queue retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_review_queue(
    tournament_id: int = Path(..., description="Tournament ID"),
    organization_id: int = Query(..., description="Organization ID"),
    status: str = Query("finished", description="Race status filter"),
    review_status: str = Query(
        "pending", description="Review status filter (pending, accepted, rejected, all)"
    ),
    reviewed_by_id: int = Query(
        -1, description="Reviewer ID filter (-1 for unreviewed, 0 for all)"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        50, ge=1, le=100, description="Maximum number of records to return"
    ),
    current_user: User = Depends(get_current_user),
) -> AsyncQualifierRaceReviewListResponse:
    """
    Get review queue for a tournament.

    Only users with ASYNC_REVIEWER or ADMIN permissions can access the review queue.
    These users can see all runs regardless of hide_results setting.

    Args:
        tournament_id: Tournament ID
        organization_id: Organization ID
        status: Race status filter (default: 'finished')
        review_status: Review status filter (default: 'pending', use 'all' for no filter)
        reviewed_by_id: Reviewer filter (-1 for unreviewed, 0 for all, or specific user ID)
        skip: Pagination offset
        limit: Pagination limit
        current_user: Authenticated user

    Returns:
        List of races in review queue

    Raises:
        HTTPException: 403 if user lacks permission
    """
    service = AsyncQualifierService()

    # Convert 'all' filters to None
    status_filter = None if status == "all" else status
    review_status_filter = None if review_status == "all" else review_status
    reviewer_filter = None if reviewed_by_id == 0 else reviewed_by_id

    races = await service.get_review_queue(
        user=current_user,
        organization_id=organization_id,
        tournament_id=tournament_id,
        status=status_filter,
        review_status=review_status_filter,
        reviewed_by_id=reviewer_filter,
        skip=skip,
        limit=limit,
    )

    # Convert to response schema
    items = []
    for race in races:
        # Build response object
        user_info = UserBasicInfo(
            id=race.user.id, discord_username=race.user.discord_username
        )

        reviewed_by_info = None
        if race.reviewed_by:
            reviewed_by_info = UserBasicInfo(
                id=race.reviewed_by.id,
                discord_username=race.reviewed_by.discord_username,
            )

        item = AsyncQualifierRaceReviewOut(
            id=race.id,
            tournament_id=race.tournament_id,
            user=user_info,
            permalink_id=race.permalink_id,
            permalink_url=race.permalink.url if race.permalink else None,
            pool_name=(
                race.permalink.pool.name
                if race.permalink and race.permalink.pool
                else None
            ),
            status=race.status,
            start_time=race.start_time,
            end_time=race.end_time,
            elapsed_time_formatted=race.elapsed_time_formatted,
            runner_vod_url=race.runner_vod_url,
            runner_notes=race.runner_notes,
            score=race.score,
            review_status=race.review_status,
            reviewed_by=reviewed_by_info,
            reviewed_at=race.reviewed_at,
            reviewer_notes=race.reviewer_notes,
            review_requested_by_user=race.review_requested_by_user,
            review_request_reason=race.review_request_reason,
            thread_open_time=race.thread_open_time,
            created_at=race.created_at,
        )
        items.append(item)

    return AsyncQualifierRaceReviewListResponse(items=items, count=len(items))


@router.get(
    "/races/{race_id}/review",
    response_model=AsyncQualifierRaceReviewOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Race for Review",
    description="Get detailed race information for review. Requires ASYNC_REVIEWER or ADMIN permission.",
    responses={
        200: {"description": "Race retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Race not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_race_for_review(
    race_id: int = Path(..., description="Race ID"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> AsyncQualifierRaceReviewOut:
    """
    Get race for review with full details.

    Only users with ASYNC_REVIEWER or ADMIN permissions can review races.

    Args:
        race_id: Race ID
        organization_id: Organization ID
        current_user: Authenticated user

    Returns:
        Race details

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if race not found
    """
    service = AsyncQualifierService()
    race = await service.get_race_for_review(
        user=current_user,
        organization_id=organization_id,
        race_id=race_id,
    )

    if not race:
        raise HTTPException(
            status_code=404, detail="Race not found or insufficient permissions"
        )

    # Build response object
    user_info = UserBasicInfo(
        id=race.user.id, discord_username=race.user.discord_username
    )

    reviewed_by_info = None
    if race.reviewed_by:
        reviewed_by_info = UserBasicInfo(
            id=race.reviewed_by.id, discord_username=race.reviewed_by.discord_username
        )

    return AsyncQualifierRaceReviewOut(
        id=race.id,
        tournament_id=race.tournament_id,
        user=user_info,
        permalink_id=race.permalink_id,
        permalink_url=race.permalink.url if race.permalink else None,
        pool_name=(
            race.permalink.pool.name if race.permalink and race.permalink.pool else None
        ),
        status=race.status,
        start_time=race.start_time,
        end_time=race.end_time,
        elapsed_time_formatted=race.elapsed_time_formatted,
        runner_vod_url=race.runner_vod_url,
        runner_notes=race.runner_notes,
        score=race.score,
        review_status=race.review_status,
        reviewed_by=reviewed_by_info,
        reviewed_at=race.reviewed_at,
        reviewer_notes=race.reviewer_notes,
        review_requested_by_user=race.review_requested_by_user,
        review_request_reason=race.review_request_reason,
        thread_open_time=race.thread_open_time,
        created_at=race.created_at,
    )


@router.patch(
    "/races/{race_id}/review",
    response_model=AsyncQualifierRaceReviewOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Race Review",
    description="Update review status and details for a race. Requires ASYNC_REVIEWER or ADMIN permission.",
    responses={
        200: {"description": "Review updated successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {
            "description": "Insufficient permissions or attempting to review own race"
        },
        404: {"description": "Race not found"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def update_race_review(
    data: AsyncQualifierRaceReviewUpdateRequest,
    race_id: int = Path(..., description="Race ID"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> AsyncQualifierRaceReviewOut:
    """
    Update review status and details for a race.

    Only users with ASYNC_REVIEWER or ADMIN permissions can review races.
    Users cannot review their own races.

    Args:
        race_id: Race ID
        organization_id: Organization ID
        data: Review update data
        current_user: Authenticated user

    Returns:
        Updated race

    Raises:
        HTTPException: 403 if user lacks permission or reviewing own race
        HTTPException: 404 if race not found
    """
    service = AsyncQualifierService()
    race = await service.update_race_review(
        user=current_user,
        organization_id=organization_id,
        race_id=race_id,
        review_status=data.review_status,
        reviewer_notes=data.reviewer_notes,
        elapsed_time_seconds=data.elapsed_time_seconds,
    )

    if not race:
        raise HTTPException(
            status_code=404,
            detail="Race not found, insufficient permissions, or cannot review own race",
        )

    # Build response object
    user_info = UserBasicInfo(
        id=race.user.id, discord_username=race.user.discord_username
    )

    reviewed_by_info = None
    if race.reviewed_by:
        reviewed_by_info = UserBasicInfo(
            id=race.reviewed_by.id, discord_username=race.reviewed_by.discord_username
        )

    return AsyncQualifierRaceReviewOut(
        id=race.id,
        tournament_id=race.tournament_id,
        user=user_info,
        permalink_id=race.permalink_id,
        permalink_url=race.permalink.url if race.permalink else None,
        pool_name=(
            race.permalink.pool.name if race.permalink and race.permalink.pool else None
        ),
        status=race.status,
        start_time=race.start_time,
        end_time=race.end_time,
        elapsed_time_formatted=race.elapsed_time_formatted,
        runner_vod_url=race.runner_vod_url,
        runner_notes=race.runner_notes,
        score=race.score,
        review_status=race.review_status,
        reviewed_by=reviewed_by_info,
        reviewed_at=race.reviewed_at,
        reviewer_notes=race.reviewer_notes,
        review_requested_by_user=race.review_requested_by_user,
        review_request_reason=race.review_request_reason,
        thread_open_time=race.thread_open_time,
        created_at=race.created_at,
    )


# ==================== RACE SUBMISSION ====================


@router.patch(
    "/races/{race_id}/submission",
    response_model=AsyncQualifierRaceReviewOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Race Submission",
    description="Update VoD URL, notes, and review flag for own race. Only race participant can update.",
    responses={
        200: {"description": "Race submission updated successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions or not race participant"},
        404: {"description": "Race not found"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def update_race_submission(
    data: AsyncQualifierRaceUpdateRequest,
    race_id: int = Path(..., description="Race ID"),
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> AsyncQualifierRaceReviewOut:
    """
    Update race submission with VoD URL, notes, and optional review flag.

    Only the race participant can update their own submission.
    When flagging for review, a reason must be provided.

    Args:
        race_id: Race ID
        organization_id: Organization ID
        data: Submission update data
        current_user: Authenticated user

    Returns:
        Updated race

    Raises:
        HTTPException: 403 if user is not the race participant
        HTTPException: 404 if race not found
        HTTPException: 422 if flagging for review without reason
    """
    service = AsyncQualifierService()

    race = await service.update_race_submission(
        user=current_user,
        organization_id=organization_id,
        race_id=race_id,
        runner_vod_url=data.runner_vod_url,
        runner_notes=data.runner_notes,
        review_requested_by_user=data.review_requested_by_user,
        review_request_reason=data.review_request_reason,
    )

    if not race:
        raise HTTPException(
            status_code=404, detail="Race not found or insufficient permissions"
        )

    # Build response object
    user_info = UserBasicInfo(
        id=race.user.id, discord_username=race.user.discord_username
    )

    reviewed_by_info = None
    if race.reviewed_by:
        reviewed_by_info = UserBasicInfo(
            id=race.reviewed_by.id, discord_username=race.reviewed_by.discord_username
        )

    return AsyncQualifierRaceReviewOut(
        id=race.id,
        tournament_id=race.tournament_id,
        user=user_info,
        permalink_id=race.permalink_id,
        permalink_url=race.permalink.url if race.permalink else None,
        pool_name=(
            race.permalink.pool.name if race.permalink and race.permalink.pool else None
        ),
        status=race.status,
        start_time=race.start_time,
        end_time=race.end_time,
        elapsed_time_formatted=race.elapsed_time_formatted,
        runner_vod_url=race.runner_vod_url,
        runner_notes=race.runner_notes,
        score=race.score,
        review_status=race.review_status,
        reviewed_by=reviewed_by_info,
        reviewed_at=race.reviewed_at,
        reviewer_notes=race.reviewer_notes,
        review_requested_by_user=race.review_requested_by_user,
        review_request_reason=race.review_request_reason,
        thread_open_time=race.thread_open_time,
        created_at=race.created_at,
    )
