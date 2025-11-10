"""
API routes for race room profiles.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from api.deps import get_current_user, enforce_rate_limit
from api.schemas.race_room_profile import (
    RaceRoomProfileCreate,
    RaceRoomProfileUpdate,
    RaceRoomProfileResponse,
    RaceRoomProfileListResponse,
)
from application.services.racetime.race_room_profile_service import (
    RaceRoomProfileService,
)
from models import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/organizations/{organization_id}/race-room-profiles",
    tags=["race-room-profiles"],
)


@router.get(
    "/",
    dependencies=[Depends(enforce_rate_limit)],
    response_model=RaceRoomProfileListResponse,
    summary="List Race Room Profiles",
)
async def list_profiles(
    organization_id: int, current_user: User = Depends(get_current_user)
) -> RaceRoomProfileListResponse:
    """
    List all race room profiles for an organization.

    Authorization is enforced at the service layer.
    """
    service = RaceRoomProfileService()
    profiles = await service.list_profiles(current_user, organization_id)

    return RaceRoomProfileListResponse(
        items=[RaceRoomProfileResponse.model_validate(p) for p in profiles],
        count=len(profiles),
    )


@router.get(
    "/{profile_id}",
    dependencies=[Depends(enforce_rate_limit)],
    response_model=RaceRoomProfileResponse,
    summary="Get Race Room Profile",
)
async def get_profile(
    organization_id: int,
    profile_id: int,
    current_user: User = Depends(get_current_user),
) -> RaceRoomProfileResponse:
    """
    Get a specific race room profile.

    Authorization is enforced at the service layer.
    """
    service = RaceRoomProfileService()
    profile = await service.get_profile(current_user, organization_id, profile_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return RaceRoomProfileResponse.model_validate(profile)


@router.post(
    "/",
    dependencies=[Depends(enforce_rate_limit)],
    response_model=RaceRoomProfileResponse,
    summary="Create Race Room Profile",
    status_code=201,
)
async def create_profile(
    organization_id: int,
    profile_data: RaceRoomProfileCreate,
    current_user: User = Depends(get_current_user),
) -> RaceRoomProfileResponse:
    """
    Create a new race room profile.

    Requires TOURNAMENT_MANAGER permission.
    Authorization is enforced at the service layer.
    """
    service = RaceRoomProfileService()
    profile = await service.create_profile(
        current_user=current_user,
        organization_id=organization_id,
        name=profile_data.name,
        description=profile_data.description or "",
        start_delay=profile_data.start_delay,
        time_limit=profile_data.time_limit,
        streaming_required=profile_data.streaming_required,
        auto_start=profile_data.auto_start,
        allow_comments=profile_data.allow_comments,
        hide_comments=profile_data.hide_comments,
        allow_prerace_chat=profile_data.allow_prerace_chat,
        allow_midrace_chat=profile_data.allow_midrace_chat,
        allow_non_entrant_chat=profile_data.allow_non_entrant_chat,
        is_default=profile_data.is_default,
    )

    if not profile:
        raise HTTPException(status_code=403, detail="Permission denied")

    return RaceRoomProfileResponse.model_validate(profile)


@router.put(
    "/{profile_id}",
    dependencies=[Depends(enforce_rate_limit)],
    response_model=RaceRoomProfileResponse,
    summary="Update Race Room Profile",
)
async def update_profile(
    organization_id: int,
    profile_id: int,
    profile_data: RaceRoomProfileUpdate,
    current_user: User = Depends(get_current_user),
) -> RaceRoomProfileResponse:
    """
    Update a race room profile.

    Requires TOURNAMENT_MANAGER permission.
    Authorization is enforced at the service layer.
    """
    service = RaceRoomProfileService()

    # Build updates dict from provided fields
    updates = {}
    for field, value in profile_data.model_dump(exclude_unset=True).items():
        updates[field] = value

    profile = await service.update_profile(
        current_user=current_user,
        organization_id=organization_id,
        profile_id=profile_id,
        **updates
    )

    if not profile:
        raise HTTPException(
            status_code=404, detail="Profile not found or permission denied"
        )

    return RaceRoomProfileResponse.model_validate(profile)


@router.delete(
    "/{profile_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Race Room Profile",
    status_code=204,
)
async def delete_profile(
    organization_id: int,
    profile_id: int,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a race room profile.

    Requires TOURNAMENT_MANAGER permission.
    Authorization is enforced at the service layer.
    """
    service = RaceRoomProfileService()
    success = await service.delete_profile(current_user, organization_id, profile_id)

    if not success:
        raise HTTPException(
            status_code=404, detail="Profile not found or permission denied"
        )


@router.post(
    "/{profile_id}/set-default",
    dependencies=[Depends(enforce_rate_limit)],
    response_model=RaceRoomProfileResponse,
    summary="Set Default Profile",
)
async def set_default_profile(
    organization_id: int,
    profile_id: int,
    current_user: User = Depends(get_current_user),
) -> RaceRoomProfileResponse:
    """
    Set a race room profile as the default for the organization.

    Requires TOURNAMENT_MANAGER permission.
    Authorization is enforced at the service layer.
    """
    service = RaceRoomProfileService()
    success = await service.set_default_profile(
        current_user, organization_id, profile_id
    )

    if not success:
        raise HTTPException(
            status_code=404, detail="Profile not found or permission denied"
        )

    # Fetch and return the updated profile
    profile = await service.get_profile(current_user, organization_id, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return RaceRoomProfileResponse.model_validate(profile)
