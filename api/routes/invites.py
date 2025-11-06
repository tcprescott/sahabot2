"""Organization invite-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path
from api.schemas.invite import (
    OrganizationInviteOut,
    OrganizationInviteListResponse,
    OrganizationInviteCreateRequest,
    OrganizationInviteUpdateRequest,
    OrganizationInviteUseResponse,
)
from api.deps import get_current_user, enforce_rate_limit
from application.services.organizations.organization_invite_service import OrganizationInviteService
from models import User

router = APIRouter(prefix="/invites", tags=["invites"])


@router.get(
    "/organizations/{organization_id}",
    response_model=OrganizationInviteListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Organization Invites",
    description="List all invites for an organization. Authorization enforced at service layer.",
    responses={
        200: {"description": "Invites retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_organization_invites(
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> OrganizationInviteListResponse:
    """
    List organization invites.

    Returns all invites for the specified organization.
    Authorization is enforced at the service layer.

    Args:
        organization_id: ID of the organization
        current_user: Authenticated user making the request

    Returns:
        OrganizationInviteListResponse: List of invites (empty if unauthorized)
    """
    service = OrganizationInviteService()
    invites = await service.list_org_invites(current_user, organization_id)
    items = [OrganizationInviteOut.model_validate(invite) for invite in invites]
    return OrganizationInviteListResponse(items=items, count=len(items))


@router.post(
    "/organizations/{organization_id}",
    response_model=OrganizationInviteOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Organization Invite",
    description="Create a new invite for an organization. Authorization enforced at service layer.",
    responses={
        201: {"description": "Invite created successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def create_organization_invite(
    data: OrganizationInviteCreateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> OrganizationInviteOut:
    """
    Create organization invite.

    Creates a new invite link for the organization.
    Authorization is enforced at the service layer.

    Args:
        organization_id: ID of the organization
        data: Invite creation data
        current_user: Authenticated user making the request

    Returns:
        OrganizationInviteOut: Created invite

    Raises:
        HTTPException: 403 if user lacks permission
    """
    service = OrganizationInviteService()
    invite = await service.create_invite(
        user=current_user,
        organization_id=organization_id,
        slug=data.slug,
        max_uses=data.max_uses,
        expires_at=data.expires_at
    )

    if not invite:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to create invites"
        )

    return OrganizationInviteOut.model_validate(invite)


@router.patch(
    "/{invite_id}",
    response_model=OrganizationInviteOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Organization Invite",
    description="Update an organization invite. Authorization enforced at service layer.",
    responses={
        200: {"description": "Invite updated successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Invite not found"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def update_organization_invite(
    data: OrganizationInviteUpdateRequest,
    invite_id: int = Path(..., description="Invite ID"),
    current_user: User = Depends(get_current_user)
) -> OrganizationInviteOut:
    """
    Update organization invite.

    Updates an existing organization invite.
    Authorization is enforced at the service layer.

    Args:
        invite_id: ID of the invite to update
        data: Invite update data
        current_user: Authenticated user making the request

    Returns:
        OrganizationInviteOut: Updated invite

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if invite not found
    """
    service = OrganizationInviteService()
    
    # Get invite by ID across all organizations user has access to
    # Service will validate access during update
    # For now, we'll try to update and let service handle authorization
    # This is a simplified approach - ideally we'd have a get_by_id method
    
    # Try each organization the user has access to
    from application.services.organizations.organization_service import OrganizationService
    org_service = OrganizationService()
    user_orgs = await org_service.list_user_memberships(current_user.id)
    
    current_invite = None
    for membership in user_orgs:
        invites = await service.list_org_invites(current_user, membership.organization_id)
        current_invite = next((inv for inv in invites if inv.id == invite_id), None)
        if current_invite:
            break
    
    if not current_invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    invite = await service.update_invite(
        user=current_user,
        organization_id=current_invite.organization_id,
        invite_id=invite_id,
        is_active=data.is_active,
        max_uses=data.max_uses,
        expires_at=data.expires_at
    )

    if not invite:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to update invite"
        )

    return OrganizationInviteOut.model_validate(invite)


@router.delete(
    "/{invite_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Organization Invite",
    description="Delete an organization invite. Authorization enforced at service layer.",
    responses={
        204: {"description": "Invite deleted successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Invite not found"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=204,
)
async def delete_organization_invite(
    invite_id: int = Path(..., description="Invite ID"),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete organization invite.

    Deletes an organization invite permanently.
    Authorization is enforced at the service layer.

    Args:
        invite_id: ID of the invite to delete
        current_user: Authenticated user making the request

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if invite not found
    """
    service = OrganizationInviteService()
    
    # Get invite by ID across all organizations user has access to
    from application.services.organizations.organization_service import OrganizationService
    org_service = OrganizationService()
    user_orgs = await org_service.list_user_memberships(current_user.id)
    
    current_invite = None
    for membership in user_orgs:
        invites = await service.list_org_invites(current_user, membership.organization_id)
        current_invite = next((inv for inv in invites if inv.id == invite_id), None)
        if current_invite:
            break
    
    if not current_invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    success = await service.delete_invite(
        user=current_user,
        organization_id=current_invite.organization_id,
        invite_id=invite_id
    )

    if not success:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to delete invite"
        )


@router.get(
    "/by-slug/{slug}",
    response_model=OrganizationInviteOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Invite by Slug",
    description="Get invite details by slug/code.",
    responses={
        200: {"description": "Invite retrieved successfully"},
        404: {"description": "Invite not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_invite_by_slug(
    slug: str = Path(..., description="Invite slug/code"),
    current_user: User = Depends(get_current_user)  # noqa: ARG001 - authentication required
) -> OrganizationInviteOut:
    """
    Get invite by slug.

    Retrieve invite details using the slug/code.

    Args:
        slug: Invite slug/code
        current_user: Authenticated user making the request

    Returns:
        OrganizationInviteOut: Invite details

    Raises:
        HTTPException: 404 if invite not found
    """
    service = OrganizationInviteService()
    invite = await service.get_invite_by_slug(slug)

    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    return OrganizationInviteOut.model_validate(invite)


@router.post(
    "/use/{slug}",
    response_model=OrganizationInviteUseResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Use Invite",
    description="Use an invite to join an organization.",
    responses={
        200: {"description": "Invite used successfully"},
        400: {"description": "Invite cannot be used (expired, max uses reached, etc.)"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Invite not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def use_invite(
    slug: str = Path(..., description="Invite slug/code"),
    current_user: User = Depends(get_current_user)
) -> OrganizationInviteUseResponse:
    """
    Use invite to join organization.

    Uses the invite to join the associated organization.

    Args:
        slug: Invite slug/code
        current_user: Authenticated user making the request

    Returns:
        OrganizationInviteUseResponse: Result of invite usage

    Raises:
        HTTPException: 404 if invite not found
        HTTPException: 400 if invite cannot be used
    """
    service = OrganizationInviteService()
    success, message = await service.use_invite(slug, current_user.id)

    if not success:
        if "not found" in message.lower():
            raise HTTPException(status_code=404, detail=message)
        raise HTTPException(status_code=400, detail=message)

    # Get invite to return organization_id
    invite = await service.get_invite_by_slug(slug)

    return OrganizationInviteUseResponse(
        success=True,
        message=message,
        organization_id=invite.organization_id if invite else None
    )
