"""Organization-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path
from api.schemas.organization import (
    OrganizationOut,
    OrganizationListResponse,
    OrganizationCreateRequest,
    OrganizationUpdateRequest,
    OrganizationPermissionOut,
    OrganizationPermissionListResponse,
    OrganizationPermissionCreateRequest,
    OrganizationMemberOut,
    OrganizationMemberListResponse,
    OrganizationMemberPermissionsUpdateRequest,
)
from api.deps import get_current_user, enforce_rate_limit
from application.services.organization_service import OrganizationService
from models import User

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get(
    "/",
    response_model=OrganizationListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Organizations",
    description="List all organizations. Any authenticated user can view organizations.",
    responses={
        200: {"description": "Organizations retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_organizations(
    current_user: User = Depends(get_current_user)  # noqa: ARG001 - authentication required
) -> OrganizationListResponse:
    """
    List all organizations.

    Returns a list of all organizations in the system. Any authenticated
    user can view the list of organizations.

    Args:
        current_user: Authenticated user making the request

    Returns:
        OrganizationListResponse: List of organizations and total count
    """
    service = OrganizationService()
    organizations = await service.list_organizations()
    items = [OrganizationOut.model_validate(org) for org in organizations]
    return OrganizationListResponse(items=items, count=len(items))


@router.get(
    "/{organization_id}",
    response_model=OrganizationOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Organization",
    description="Get details of a specific organization.",
    responses={
        200: {"description": "Organization retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Organization not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_organization(
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)  # noqa: ARG001 - authentication required
) -> OrganizationOut:
    """
    Get organization details.

    Retrieve detailed information about a specific organization.

    Args:
        organization_id: ID of the organization to retrieve
        current_user: Authenticated user making the request

    Returns:
        OrganizationOut: Organization details

    Raises:
        HTTPException: 404 if organization not found
    """
    service = OrganizationService()
    organization = await service.get_organization(organization_id)

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    return OrganizationOut.model_validate(organization)


@router.post(
    "/",
    response_model=OrganizationOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Organization",
    description="Create a new organization. Requires SUPERADMIN permission.",
    responses={
        201: {"description": "Organization created successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions (requires SUPERADMIN)"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def create_organization(
    data: OrganizationCreateRequest,
    current_user: User = Depends(get_current_user)
) -> OrganizationOut:
    """
    Create a new organization (superadmin only).

    Creates a new organization with the specified details. Only superadmin
    users can create organizations.

    Args:
        data: Organization creation data
        current_user: Authenticated user making the request

    Returns:
        OrganizationOut: Newly created organization

    Raises:
        HTTPException: 403 if user lacks SUPERADMIN permission
    """
    service = OrganizationService()
    organization = await service.create_organization(
        current_user=current_user,
        name=data.name,
        description=data.description,
        is_active=data.is_active
    )

    if not organization:
        raise HTTPException(
            status_code=403,
            detail="Only superadmin users can create organizations"
        )

    return OrganizationOut.model_validate(organization)


@router.patch(
    "/{organization_id}",
    response_model=OrganizationOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Organization",
    description="Update an organization. Requires SUPERADMIN permission.",
    responses={
        200: {"description": "Organization updated successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions (requires SUPERADMIN)"},
        404: {"description": "Organization not found"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def update_organization(
    data: OrganizationUpdateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> OrganizationOut:
    """
    Update an organization (superadmin only).

    Updates organization details. Only superadmin users can update organizations.

    Args:
        organization_id: ID of the organization to update
        data: Organization update data
        current_user: Authenticated user making the request

    Returns:
        OrganizationOut: Updated organization

    Raises:
        HTTPException: 403 if user lacks SUPERADMIN permission
        HTTPException: 404 if organization not found
    """
    service = OrganizationService()

    # Get current organization to use for defaults
    current_org = await service.get_organization(organization_id)
    if not current_org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Use current values as defaults for fields not provided
    organization = await service.update_organization(
        current_user=current_user,
        organization_id=organization_id,
        name=data.name if data.name is not None else current_org.name,
        description=data.description if data.description is not None else current_org.description,
        is_active=data.is_active if data.is_active is not None else current_org.is_active
    )

    if not organization:
        raise HTTPException(
            status_code=403,
            detail="Only superadmin users can update organizations"
        )

    return OrganizationOut.model_validate(organization)


# ==================== MEMBERS ====================


@router.get(
    "/{organization_id}/members",
    response_model=OrganizationMemberListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Organization Members",
    description="List all members of an organization.",
    responses={
        200: {"description": "Members retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Organization not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_organization_members(
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)  # noqa: ARG001 - authentication required
) -> OrganizationMemberListResponse:
    """
    List organization members.

    Retrieve all members of an organization along with their permissions.

    Args:
        organization_id: ID of the organization
        current_user: Authenticated user making the request

    Returns:
        OrganizationMemberListResponse: List of members and their permissions
    """
    service = OrganizationService()
    members = await service.list_members(organization_id)

    # Convert to output schema with permission names
    items = []
    for member in members:
        # Fetch permissions for this member
        permission_names = await service.list_member_permissions(
            organization_id,
            member.user_id
        )

        items.append(
            OrganizationMemberOut(
                id=member.id,
                organization_id=organization_id,
                user_id=member.user_id,
                permissions=permission_names,
                joined_at=member.joined_at,
                updated_at=member.updated_at,
            )
        )

    return OrganizationMemberListResponse(items=items, count=len(items))


@router.put(
    "/{organization_id}/members/{user_id}/permissions",
    response_model=OrganizationMemberOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Member Permissions",
    description="Set permissions for an organization member. Requires organization admin permission.",
    responses={
        200: {"description": "Member permissions updated successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions (requires organization admin)"},
        404: {"description": "Organization or member not found"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def update_member_permissions(
    data: OrganizationMemberPermissionsUpdateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    user_id: int = Path(..., description="User ID of the member"),
    current_user: User = Depends(get_current_user)
) -> OrganizationMemberOut:
    """
    Update member permissions.

    Set the permissions for an organization member. This replaces all
    existing permissions with the provided list. Requires organization
    admin permission or SUPERADMIN.

    Args:
        organization_id: ID of the organization
        user_id: ID of the user whose permissions to update
        data: List of permission names to assign
        current_user: Authenticated user making the request

    Returns:
        OrganizationMemberOut: Updated member with new permissions

    Raises:
        HTTPException: 403 if user lacks permission to manage members
        HTTPException: 404 if organization or member not found
    """
    service = OrganizationService()

    # Verify member exists
    member = await service.get_member(organization_id, user_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in organization")

    # Update permissions (authorization enforced in service)
    success = await service.set_permissions_for_member(
        current_user=current_user,
        organization_id=organization_id,
        user_id=user_id,
        permission_names=data.permission_names
    )

    if not success:
        raise HTTPException(
            status_code=403,
            detail="Only organization admins can manage member permissions"
        )

    # Fetch updated permissions
    updated_permissions = await service.list_member_permissions(organization_id, user_id)

    return OrganizationMemberOut(
        id=member.id,
        organization_id=organization_id,
        user_id=user_id,
        permissions=updated_permissions,
        joined_at=member.joined_at,
        updated_at=member.updated_at,
    )


# ==================== PERMISSIONS ====================


@router.get(
    "/{organization_id}/permissions",
    response_model=OrganizationPermissionListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Organization Permissions",
    description="List all available permissions for an organization.",
    responses={
        200: {"description": "Permissions retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Organization not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_organization_permissions(
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)  # noqa: ARG001 - authentication required
) -> OrganizationPermissionListResponse:
    """
    List organization permissions.

    Retrieve all available permissions defined for an organization.

    Args:
        organization_id: ID of the organization
        current_user: Authenticated user making the request

    Returns:
        OrganizationPermissionListResponse: List of permissions
    """
    service = OrganizationService()
    permissions = await service.list_permissions(organization_id)

    items = [OrganizationPermissionOut.model_validate(perm) for perm in permissions]
    return OrganizationPermissionListResponse(items=items, count=len(items))


@router.post(
    "/{organization_id}/permissions",
    response_model=OrganizationPermissionOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Organization Permission",
    description="Create a new permission for an organization. Requires organization admin permission.",
    responses={
        201: {"description": "Permission created successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions (requires organization admin)"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def create_organization_permission(
    data: OrganizationPermissionCreateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> OrganizationPermissionOut:
    """
    Create organization permission.

    Create a new permission type for an organization. Requires organization
    admin permission or SUPERADMIN.

    Args:
        organization_id: ID of the organization
        data: Permission creation data
        current_user: Authenticated user making the request

    Returns:
        OrganizationPermissionOut: Newly created permission

    Raises:
        HTTPException: 403 if user lacks permission to manage permissions
    """
    service = OrganizationService()

    # Authorization enforced in service
    permission = await service.create_permission(
        current_user=current_user,
        organization_id=organization_id,
        permission_name=data.permission_name,
        description=data.description
    )

    if not permission:
        raise HTTPException(
            status_code=403,
            detail="Only organization admins can create permissions"
        )

    return OrganizationPermissionOut.model_validate(permission)


@router.delete(
    "/{organization_id}/permissions/{permission_name}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Organization Permission",
    description="Delete a permission from an organization. Requires organization admin permission.",
    responses={
        204: {"description": "Permission deleted successfully"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions (requires organization admin)"},
        404: {"description": "Permission not found"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=204,
)
async def delete_organization_permission(
    organization_id: int = Path(..., description="Organization ID"),
    permission_name: str = Path(..., description="Permission name to delete"),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete organization permission.

    Delete a permission from an organization. This will remove the permission
    from all members. Requires organization admin permission or SUPERADMIN.

    Args:
        organization_id: ID of the organization
        permission_name: Name of the permission to delete
        current_user: Authenticated user making the request

    Raises:
        HTTPException: 403 if user lacks permission to manage permissions
        HTTPException: 404 if permission not found
    """
    service = OrganizationService()

    # Authorization enforced in service
    deleted_count = await service.delete_permission(
        current_user=current_user,
        organization_id=organization_id,
        permission_name=permission_name
    )

    if deleted_count == 0:
        # Could be unauthorized or not found - treat as not found for API consistency
        raise HTTPException(status_code=404, detail="Permission not found or insufficient permissions")
