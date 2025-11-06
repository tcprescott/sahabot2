"""Tournament Match Settings API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path
from api.schemas.tournament import (
    TournamentMatchSettingsOut,
    TournamentMatchSettingsListResponse,
    TournamentMatchSettingsSubmitRequest,
    TournamentMatchSettingsValidateRequest,
    TournamentMatchSettingsValidateResponse,
)
from api.deps import get_current_user, enforce_rate_limit
from application.services.tournaments.tournament_match_settings_service import TournamentMatchSettingsService
from models import User

router = APIRouter(prefix="/tournaments/settings", tags=["tournament-settings"])


@router.get(
    "/matches/{match_id}",
    response_model=TournamentMatchSettingsListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Settings for Match",
    description="List all settings submissions for a match. Authorization enforced at service layer.",
    responses={
        200: {"description": "Settings retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_match_settings(
    match_id: int = Path(..., description="Match ID"),
    current_user: User = Depends(get_current_user)
) -> TournamentMatchSettingsListResponse:
    """
    List settings submissions for a match.

    Returns all settings submissions for the specified match.
    Authorization is enforced at the service layer (players or tournament managers).

    Args:
        match_id: ID of the match
        current_user: Authenticated user making the request

    Returns:
        TournamentMatchSettingsListResponse: List of settings submissions (empty if unauthorized)
    """
    service = TournamentMatchSettingsService()
    submissions = await service.list_submissions_for_match(current_user, match_id)
    items = [TournamentMatchSettingsOut.model_validate(s) for s in submissions]
    return TournamentMatchSettingsListResponse(items=items, count=len(items))


@router.get(
    "/matches/{match_id}/game/{game_number}",
    response_model=TournamentMatchSettingsOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Settings for Match Game",
    description="Get settings submission for a specific match and game number. Authorization enforced at service layer.",
    responses={
        200: {"description": "Settings retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Settings not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_match_game_settings(
    match_id: int = Path(..., description="Match ID"),
    game_number: int = Path(..., ge=1, le=10, description="Game number (1-10)"),
    current_user: User = Depends(get_current_user)
) -> TournamentMatchSettingsOut:
    """
    Get settings submission for a match game.

    Returns the settings submission for the specified match and game number.
    Authorization is enforced at the service layer.

    Args:
        match_id: ID of the match
        game_number: Game number in the match series
        current_user: Authenticated user making the request

    Returns:
        TournamentMatchSettingsOut: Settings submission

    Raises:
        HTTPException: 404 if settings not found or unauthorized
    """
    service = TournamentMatchSettingsService()
    submission = await service.get_submission(current_user, match_id, game_number)
    
    if not submission:
        raise HTTPException(status_code=404, detail="Settings not found or unauthorized")
    
    return TournamentMatchSettingsOut.model_validate(submission)


@router.post(
    "/matches/{match_id}",
    response_model=TournamentMatchSettingsOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Submit Settings for Match",
    description="Submit settings for a tournament match. Authorization enforced at service layer.",
    responses={
        201: {"description": "Settings submitted successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def submit_match_settings(
    data: TournamentMatchSettingsSubmitRequest,
    match_id: int = Path(..., description="Match ID"),
    current_user: User = Depends(get_current_user)
) -> TournamentMatchSettingsOut:
    """
    Submit settings for a tournament match.

    Creates or updates settings submission for the match.
    Authorization is enforced at the service layer (must be a player or tournament manager).

    Args:
        match_id: ID of the match
        data: Settings submission data
        current_user: Authenticated user making the request

    Returns:
        TournamentMatchSettingsOut: Created/updated settings submission

    Raises:
        HTTPException: 403 if user lacks permission, 422 if validation fails
    """
    service = TournamentMatchSettingsService()
    submission = await service.submit_settings(
        user=current_user,
        match_id=match_id,
        settings=data.settings,
        game_number=data.game_number,
        notes=data.notes
    )
    
    if not submission:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized to submit settings for this match or validation failed"
        )
    
    return TournamentMatchSettingsOut.model_validate(submission)


@router.delete(
    "/{submission_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Settings Submission",
    description="Delete a settings submission. Authorization enforced at service layer.",
    responses={
        204: {"description": "Settings deleted successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Settings not found"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=204,
)
async def delete_settings_submission(
    submission_id: int = Path(..., description="Settings submission ID"),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a settings submission.

    Authorization is enforced at the service layer (must be a player or tournament manager).

    Args:
        submission_id: ID of the settings submission
        current_user: Authenticated user making the request

    Raises:
        HTTPException: 404 if not found, 403 if unauthorized
    """
    service = TournamentMatchSettingsService()
    deleted = await service.delete_submission(current_user, submission_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Settings not found or unauthorized to delete"
        )


@router.post(
    "/validate",
    response_model=TournamentMatchSettingsValidateResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Validate Settings",
    description="Validate tournament match settings structure and content.",
    responses={
        200: {"description": "Validation result returned"},
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def validate_settings(
    data: TournamentMatchSettingsValidateRequest,
    current_user: User = Depends(get_current_user)
) -> TournamentMatchSettingsValidateResponse:
    """
    Validate tournament match settings.

    Validates settings structure and content against tournament rules.
    Does not require match player authorization - anyone can validate.

    Args:
        data: Settings validation request
        current_user: Authenticated user making the request

    Returns:
        TournamentMatchSettingsValidateResponse: Validation result
    """
    service = TournamentMatchSettingsService()
    is_valid, error_message = await service.validate_settings(
        data.settings,
        data.tournament_id
    )
    
    return TournamentMatchSettingsValidateResponse(
        is_valid=is_valid,
        error_message=error_message
    )
