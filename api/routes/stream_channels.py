"""API endpoints for stream channels."""

from fastapi import APIRouter, Depends, HTTPException, Path
from api.schemas.stream_channel import (
    StreamChannelOut,
    StreamChannelListResponse,
    StreamChannelCreateRequest,
    StreamChannelUpdateRequest,
)
from api.deps import get_current_user, enforce_rate_limit
from modules.tournament.services.stream_channel_service import StreamChannelService
from models import User

router = APIRouter(prefix="/stream-channels", tags=["stream-channels"])


@router.get(
    "/organizations/{organization_id}",
    response_model=StreamChannelListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Stream Channels",
    description="List all stream channels for an organization.",
)
async def list_stream_channels(
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> StreamChannelListResponse:
    """
    List stream channels for an organization.

    User must be able to admin the organization to view channels.

    Args:
        organization_id: Organization ID
        current_user: Authenticated user

    Returns:
        StreamChannelListResponse: List of stream channels

    Raises:
        HTTPException: 403 if not authorized
    """
    service = StreamChannelService()
    channels = await service.list_org_channels(current_user, organization_id)

    # Empty list means either no channels or not authorized
    # Service already logged unauthorized access
    items = [StreamChannelOut.model_validate(ch) for ch in channels]
    return StreamChannelListResponse(items=items, count=len(items))


@router.post(
    "/organizations/{organization_id}",
    response_model=StreamChannelOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Stream Channel",
    description="Create a new stream channel for an organization.",
    status_code=201,
)
async def create_stream_channel(
    data: StreamChannelCreateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
) -> StreamChannelOut:
    """
    Create a new stream channel.

    Args:
        data: Channel creation data
        organization_id: Organization ID
        current_user: Authenticated user

    Returns:
        StreamChannelOut: Created channel

    Raises:
        HTTPException: 403 if not authorized, 400 if creation fails
    """
    service = StreamChannelService()
    channel = await service.create_channel(
        user=current_user,
        organization_id=organization_id,
        name=data.name,
        stream_url=data.stream_url,
        is_active=data.is_active,
    )

    if not channel:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to create channels in this organization",
        )

    return StreamChannelOut.model_validate(channel)


@router.get(
    "/organizations/{organization_id}/{channel_id}",
    response_model=StreamChannelOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Stream Channel",
    description="Get details of a specific stream channel.",
)
async def get_stream_channel(
    organization_id: int = Path(..., description="Organization ID"),
    channel_id: int = Path(..., description="Channel ID"),
    current_user: User = Depends(get_current_user),
) -> StreamChannelOut:
    """
    Get stream channel details.

    Args:
        organization_id: Organization ID
        channel_id: Channel ID
        current_user: Authenticated user

    Returns:
        StreamChannelOut: Channel details

    Raises:
        HTTPException: 403 if not authorized, 404 if not found
    """
    service = StreamChannelService()
    # List channels (includes auth check)
    channels = await service.list_org_channels(current_user, organization_id)

    # Find the specific channel
    channel = next((ch for ch in channels if ch.id == channel_id), None)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    return StreamChannelOut.model_validate(channel)


@router.patch(
    "/organizations/{organization_id}/{channel_id}",
    response_model=StreamChannelOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Stream Channel",
    description="Update a stream channel.",
)
async def update_stream_channel(
    data: StreamChannelUpdateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    channel_id: int = Path(..., description="Channel ID"),
    current_user: User = Depends(get_current_user),
) -> StreamChannelOut:
    """
    Update stream channel.

    Args:
        data: Update data
        organization_id: Organization ID
        channel_id: Channel ID
        current_user: Authenticated user

    Returns:
        StreamChannelOut: Updated channel

    Raises:
        HTTPException: 403 if not authorized, 404 if not found
    """
    service = StreamChannelService()
    channel = await service.update_channel(
        user=current_user,
        organization_id=organization_id,
        channel_id=channel_id,
        name=data.name,
        stream_url=data.stream_url,
        is_active=data.is_active,
    )

    if not channel:
        raise HTTPException(
            status_code=404, detail="Channel not found or not authorized"
        )

    return StreamChannelOut.model_validate(channel)


@router.delete(
    "/organizations/{organization_id}/{channel_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Stream Channel",
    description="Delete a stream channel.",
    status_code=204,
)
async def delete_stream_channel(
    organization_id: int = Path(..., description="Organization ID"),
    channel_id: int = Path(..., description="Channel ID"),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete stream channel.

    Args:
        organization_id: Organization ID
        channel_id: Channel ID
        current_user: Authenticated user

    Raises:
        HTTPException: 403 if not authorized, 404 if not found
    """
    service = StreamChannelService()
    success = await service.delete_channel(
        user=current_user, organization_id=organization_id, channel_id=channel_id
    )

    if not success:
        raise HTTPException(
            status_code=404, detail="Channel not found or not authorized"
        )
