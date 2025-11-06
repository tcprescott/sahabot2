"""API endpoints for settings (global and organization-scoped)."""

from fastapi import APIRouter, Depends, HTTPException, Path
from api.schemas.setting import (
    SettingOut,
    SettingListResponse,
    GlobalSettingCreateRequest,
    GlobalSettingUpdateRequest,
    OrganizationSettingCreateRequest,
    OrganizationSettingUpdateRequest,
)
from api.deps import get_current_user, enforce_rate_limit
from application.services.core.settings_service import SettingsService
from models import User, Permission

router = APIRouter(prefix="/settings", tags=["settings"])


# ========== Global Settings ==========

@router.get(
    "/global",
    response_model=SettingListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Global Settings",
    description="List all global settings. Requires SUPERADMIN permission.",
)
async def list_global_settings(
    current_user: User = Depends(get_current_user)
) -> SettingListResponse:
    """
    List all global settings.

    Only SUPERADMIN users can view global settings.

    Args:
        current_user: Authenticated user

    Returns:
        SettingListResponse: List of global settings

    Raises:
        HTTPException: 403 if not authorized
    """
    if not current_user.has_permission(Permission.SUPERADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = SettingsService()
    settings = await service.list_global()
    items = [
        SettingOut(
            key=s.key,
            value=s.value,
            description=s.description,
            is_public=s.is_public
        )
        for s in settings
    ]
    return SettingListResponse(items=items, count=len(items))


@router.post(
    "/global",
    response_model=SettingOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Global Setting",
    description="Create a new global setting. Requires SUPERADMIN permission.",
    status_code=201,
)
async def create_global_setting(
    data: GlobalSettingCreateRequest,
    current_user: User = Depends(get_current_user)
) -> SettingOut:
    """
    Create a new global setting.

    Args:
        data: Setting creation data
        current_user: Authenticated user

    Returns:
        SettingOut: Created setting

    Raises:
        HTTPException: 403 if not authorized
    """
    if not current_user.has_permission(Permission.SUPERADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = SettingsService()
    await service.set_global(
        key=data.key,
        value=data.value,
        description=data.description,
        is_public=data.is_public
    )
    setting = await service.get_global(data.key)
    if not setting:
        raise HTTPException(status_code=500, detail="Failed to create setting")
    return SettingOut(**setting)


@router.get(
    "/global/{key}",
    response_model=SettingOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Global Setting",
    description="Get a specific global setting. Requires SUPERADMIN permission.",
)
async def get_global_setting(
    key: str = Path(..., description="Setting key"),
    current_user: User = Depends(get_current_user)
) -> SettingOut:
    """
    Get global setting.

    Args:
        key: Setting key
        current_user: Authenticated user

    Returns:
        SettingOut: Setting details

    Raises:
        HTTPException: 403 if not authorized, 404 if not found
    """
    if not current_user.has_permission(Permission.SUPERADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = SettingsService()
    setting = await service.get_global(key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return SettingOut(**setting)


@router.patch(
    "/global/{key}",
    response_model=SettingOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Global Setting",
    description="Update a global setting. Requires SUPERADMIN permission.",
)
async def update_global_setting(
    data: GlobalSettingUpdateRequest,
    key: str = Path(..., description="Setting key"),
    current_user: User = Depends(get_current_user)
) -> SettingOut:
    """
    Update global setting.

    Args:
        data: Update data
        key: Setting key
        current_user: Authenticated user

    Returns:
        SettingOut: Updated setting

    Raises:
        HTTPException: 403 if not authorized, 404 if not found
    """
    if not current_user.has_permission(Permission.SUPERADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = SettingsService()
    # Check if setting exists
    existing = await service.get_global(key)
    if not existing:
        raise HTTPException(status_code=404, detail="Setting not found")

    # Update
    await service.set_global(
        key=key,
        value=data.value,
        description=data.description if data.description is not None else existing.get('description'),
        is_public=data.is_public if data.is_public is not None else existing.get('is_public', False)
    )
    setting = await service.get_global(key)
    if not setting:
        raise HTTPException(status_code=500, detail="Failed to update setting")
    return SettingOut(**setting)


@router.delete(
    "/global/{key}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Global Setting",
    description="Delete a global setting. Requires SUPERADMIN permission.",
    status_code=204,
)
async def delete_global_setting(
    key: str = Path(..., description="Setting key"),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete global setting.

    Args:
        key: Setting key
        current_user: Authenticated user

    Raises:
        HTTPException: 403 if not authorized
    """
    if not current_user.has_permission(Permission.SUPERADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = SettingsService()
    await service.delete_global(key)


# ========== Organization Settings ==========

@router.get(
    "/organizations/{organization_id}",
    response_model=SettingListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Organization Settings",
    description="List all settings for an organization.",
)
async def list_organization_settings(
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> SettingListResponse:
    """
    List organization settings.

    User must be a member with admin permissions for the organization.

    Args:
        organization_id: Organization ID
        current_user: Authenticated user

    Returns:
        SettingListResponse: List of organization settings

    Raises:
        HTTPException: 403 if not authorized
    """
    # Check authorization via organization service
    from application.services.organizations.organization_service import OrganizationService
    org_service = OrganizationService()
    can_admin = await org_service.user_can_admin_org(current_user, organization_id)
    if not can_admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = SettingsService()
    settings = await service.list_org(organization_id)
    items = [
        SettingOut(
            key=s.key,
            value=s.value,
            description=s.description
        )
        for s in settings
    ]
    return SettingListResponse(items=items, count=len(items))


@router.post(
    "/organizations/{organization_id}",
    response_model=SettingOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Organization Setting",
    description="Create a new organization setting.",
    status_code=201,
)
async def create_organization_setting(
    data: OrganizationSettingCreateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user)
) -> SettingOut:
    """
    Create organization setting.

    Args:
        data: Setting creation data
        organization_id: Organization ID
        current_user: Authenticated user

    Returns:
        SettingOut: Created setting

    Raises:
        HTTPException: 403 if not authorized
    """
    from application.services.organizations.organization_service import OrganizationService
    org_service = OrganizationService()
    can_admin = await org_service.user_can_admin_org(current_user, organization_id)
    if not can_admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = SettingsService()
    await service.set_org(
        organization_id=organization_id,
        key=data.key,
        value=data.value,
        description=data.description
    )
    setting = await service.get_org(organization_id, data.key)
    if not setting:
        raise HTTPException(status_code=500, detail="Failed to create setting")
    return SettingOut(**setting)


@router.get(
    "/organizations/{organization_id}/{key}",
    response_model=SettingOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Organization Setting",
    description="Get a specific organization setting.",
)
async def get_organization_setting(
    organization_id: int = Path(..., description="Organization ID"),
    key: str = Path(..., description="Setting key"),
    current_user: User = Depends(get_current_user)
) -> SettingOut:
    """
    Get organization setting.

    Args:
        organization_id: Organization ID
        key: Setting key
        current_user: Authenticated user

    Returns:
        SettingOut: Setting details

    Raises:
        HTTPException: 403 if not authorized, 404 if not found
    """
    from application.services.organizations.organization_service import OrganizationService
    org_service = OrganizationService()
    can_admin = await org_service.user_can_admin_org(current_user, organization_id)
    if not can_admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = SettingsService()
    setting = await service.get_org(organization_id, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return SettingOut(**setting)


@router.patch(
    "/organizations/{organization_id}/{key}",
    response_model=SettingOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Organization Setting",
    description="Update an organization setting.",
)
async def update_organization_setting(
    data: OrganizationSettingUpdateRequest,
    organization_id: int = Path(..., description="Organization ID"),
    key: str = Path(..., description="Setting key"),
    current_user: User = Depends(get_current_user)
) -> SettingOut:
    """
    Update organization setting.

    Args:
        data: Update data
        organization_id: Organization ID
        key: Setting key
        current_user: Authenticated user

    Returns:
        SettingOut: Updated setting

    Raises:
        HTTPException: 403 if not authorized, 404 if not found
    """
    from application.services.organizations.organization_service import OrganizationService
    org_service = OrganizationService()
    can_admin = await org_service.user_can_admin_org(current_user, organization_id)
    if not can_admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = SettingsService()
    existing = await service.get_org(organization_id, key)
    if not existing:
        raise HTTPException(status_code=404, detail="Setting not found")

    await service.set_org(
        organization_id=organization_id,
        key=key,
        value=data.value,
        description=data.description if data.description is not None else existing.get('description')
    )
    setting = await service.get_org(organization_id, key)
    if not setting:
        raise HTTPException(status_code=500, detail="Failed to update setting")
    return SettingOut(**setting)


@router.delete(
    "/organizations/{organization_id}/{key}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Organization Setting",
    description="Delete an organization setting.",
    status_code=204,
)
async def delete_organization_setting(
    organization_id: int = Path(..., description="Organization ID"),
    key: str = Path(..., description="Setting key"),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete organization setting.

    Args:
        organization_id: Organization ID
        key: Setting key
        current_user: Authenticated user

    Raises:
        HTTPException: 403 if not authorized
    """
    from application.services.organizations.organization_service import OrganizationService
    org_service = OrganizationService()
    can_admin = await org_service.user_can_admin_org(current_user, organization_id)
    if not can_admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = SettingsService()
    await service.delete_org(organization_id, key)
