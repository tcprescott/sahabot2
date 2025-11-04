"""RaceTime bot-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from api.schemas.racetime_bot import (
    RacetimeBotOut,
    RacetimeBotListResponse,
    RacetimeBotCreate,
    RacetimeBotUpdate,
)
from api.deps import get_current_user, enforce_rate_limit
from application.services.racetime_bot_service import RacetimeBotService
from models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/racetime-bots", tags=["racetime-bots"])


@router.get(
    "/",
    response_model=RacetimeBotListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List RaceTime Bots",
    description="List all RaceTime bot configurations. Requires ADMIN permission.",
)
async def list_bots(
    current_user: User = Depends(get_current_user),
) -> RacetimeBotListResponse:
    """
    List all RaceTime bots.

    Authorization is enforced at the service layer.

    Args:
        current_user: Authenticated user making the request

    Returns:
        RacetimeBotListResponse: List of bots (empty if unauthorized)
    """
    service = RacetimeBotService()
    bots = await service.get_all_bots(current_user)
    items = [RacetimeBotOut.model_validate(b) for b in bots]
    return RacetimeBotListResponse(items=items, count=len(items))


@router.get(
    "/{bot_id}",
    response_model=RacetimeBotOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get RaceTime Bot",
    description="Get a specific RaceTime bot by ID. Requires ADMIN permission.",
)
async def get_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
) -> RacetimeBotOut:
    """
    Get a RaceTime bot by ID.

    Authorization is enforced at the service layer.

    Args:
        bot_id: Bot ID
        current_user: Authenticated user making the request

    Returns:
        RacetimeBotOut: Bot details

    Raises:
        HTTPException: 404 if bot not found or unauthorized
    """
    service = RacetimeBotService()
    bot = await service.get_bot_by_id(bot_id, current_user)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found or access denied")
    return RacetimeBotOut.model_validate(bot)


@router.post(
    "/",
    response_model=RacetimeBotOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create RaceTime Bot",
    description="Create a new RaceTime bot configuration. Requires ADMIN permission.",
    status_code=201,
)
async def create_bot(
    bot_data: RacetimeBotCreate,
    current_user: User = Depends(get_current_user),
) -> RacetimeBotOut:
    """
    Create a new RaceTime bot.

    Authorization is enforced at the service layer.

    Args:
        bot_data: Bot creation data
        current_user: Authenticated user making the request

    Returns:
        RacetimeBotOut: Created bot

    Raises:
        HTTPException: 400 if validation fails, 403 if unauthorized
    """
    service = RacetimeBotService()
    try:
        bot = await service.create_bot(
            category=bot_data.category,
            client_id=bot_data.client_id,
            client_secret=bot_data.client_secret,
            name=bot_data.name,
            description=bot_data.description,
            is_active=bot_data.is_active,
            current_user=current_user,
        )
        if not bot:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return RacetimeBotOut.model_validate(bot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/{bot_id}",
    response_model=RacetimeBotOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update RaceTime Bot",
    description="Update an existing RaceTime bot. Requires ADMIN permission.",
)
async def update_bot(
    bot_id: int,
    bot_data: RacetimeBotUpdate,
    current_user: User = Depends(get_current_user),
) -> RacetimeBotOut:
    """
    Update a RaceTime bot.

    Authorization is enforced at the service layer.

    Args:
        bot_id: Bot ID
        bot_data: Bot update data
        current_user: Authenticated user making the request

    Returns:
        RacetimeBotOut: Updated bot

    Raises:
        HTTPException: 404 if bot not found, 400 if validation fails, 403 if unauthorized
    """
    service = RacetimeBotService()

    # Build updates dict from provided fields
    updates = bot_data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        bot = await service.update_bot(bot_id, current_user, **updates)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found or access denied")
        return RacetimeBotOut.model_validate(bot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{bot_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete RaceTime Bot",
    description="Delete a RaceTime bot. Requires SUPERADMIN permission.",
    status_code=204,
)
async def delete_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a RaceTime bot.

    Authorization is enforced at the service layer.

    Args:
        bot_id: Bot ID
        current_user: Authenticated user making the request

    Raises:
        HTTPException: 404 if bot not found or access denied
    """
    service = RacetimeBotService()
    success = await service.delete_bot(bot_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Bot not found or insufficient permissions")


@router.get(
    "/{bot_id}/organizations",
    response_model=list[int],
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Bot Organizations",
    description="Get organizations assigned to a RaceTime bot. Requires ADMIN permission.",
)
async def get_bot_organizations(
    bot_id: int,
    current_user: User = Depends(get_current_user),
) -> list[int]:
    """
    Get organizations assigned to a bot.

    Authorization is enforced at the service layer.

    Args:
        bot_id: Bot ID
        current_user: Authenticated user making the request

    Returns:
        list[int]: List of organization IDs
    """
    service = RacetimeBotService()
    orgs = await service.get_organizations_for_bot(bot_id, current_user)
    return [org.id for org in orgs]


@router.post(
    "/{bot_id}/organizations/{organization_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Assign Bot to Organization",
    description="Assign a RaceTime bot to an organization. Requires ADMIN permission.",
    status_code=204,
)
async def assign_bot_to_organization(
    bot_id: int,
    organization_id: int,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Assign a bot to an organization.

    Authorization is enforced at the service layer.

    Args:
        bot_id: Bot ID
        organization_id: Organization ID
        current_user: Authenticated user making the request

    Raises:
        HTTPException: 403 if unauthorized
    """
    service = RacetimeBotService()
    assignment = await service.assign_bot_to_organization(
        bot_id, organization_id, current_user
    )
    if not assignment:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.delete(
    "/{bot_id}/organizations/{organization_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Unassign Bot from Organization",
    description="Remove a RaceTime bot assignment from an organization. Requires ADMIN permission.",
    status_code=204,
)
async def unassign_bot_from_organization(
    bot_id: int,
    organization_id: int,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Unassign a bot from an organization.

    Authorization is enforced at the service layer.

    Args:
        bot_id: Bot ID
        organization_id: Organization ID
        current_user: Authenticated user making the request

    Raises:
        HTTPException: 403 if unauthorized, 404 if assignment not found
    """
    service = RacetimeBotService()
    success = await service.unassign_bot_from_organization(
        bot_id, organization_id, current_user
    )
    if not success:
        raise HTTPException(status_code=404, detail="Assignment not found or insufficient permissions")
