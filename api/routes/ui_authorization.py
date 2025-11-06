"""UI Authorization API routes.

Provides frontend UI with permission information for conditional rendering.
"""

import logging
from typing import List, Dict
from fastapi import APIRouter, Depends

from api.deps import get_current_user, enforce_rate_limit
from models import User
from application.services.authorization.ui_authorization_helper import UIAuthorizationHelper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ui-auth", tags=["ui-authorization"])


@router.get(
    "/organizations/{organization_id}/permissions",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get UI Permissions for Organization"
)
async def get_organization_permissions(
    organization_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get all UI permissions for the current user in an organization.
    
    Returns a comprehensive set of permission flags for conditional UI rendering.
    
    **Example Response:**
    ```json
    {
        "can_manage_tournaments": true,
        "can_create_tournaments": true,
        "can_review_async_races": false,
        "can_manage_members": true,
        "is_organization_member": true,
        "is_organization_admin": true,
        ...
    }
    ```
    """
    helper = UIAuthorizationHelper()
    permissions = await helper.get_organization_permissions(current_user, organization_id)
    return permissions.to_dict()


@router.post(
    "/organizations/permissions/batch",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get UI Permissions for Multiple Organizations"
)
async def get_multiple_organization_permissions(
    organization_ids: List[int],
    current_user: User = Depends(get_current_user)
) -> Dict[int, Dict]:
    """
    Get UI permissions for multiple organizations at once.
    
    Useful for dashboard views that show multiple organizations.
    
    **Request Body:**
    ```json
    [1, 2, 3, 4]
    ```
    
    **Example Response:**
    ```json
    {
        "1": {
            "can_manage_tournaments": true,
            "is_organization_member": true,
            ...
        },
        "2": {
            "can_manage_tournaments": false,
            "is_organization_member": true,
            ...
        }
    }
    ```
    """
    helper = UIAuthorizationHelper()
    permissions_dict = await helper.get_multiple_organization_permissions(
        current_user,
        organization_ids
    )
    # Convert UIPermissions objects to dicts
    return {
        org_id: perms.to_dict()
        for org_id, perms in permissions_dict.items()
    }


@router.get(
    "/organizations/{organization_id}/can-manage-tournaments",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Check Tournament Management Permission"
)
async def can_manage_tournaments(
    organization_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    """
    Check if user can manage tournaments in the organization.
    
    **Example Response:**
    ```json
    {
        "allowed": true
    }
    ```
    """
    helper = UIAuthorizationHelper()
    allowed = await helper.can_manage_tournaments(current_user, organization_id)
    return {"allowed": allowed}


@router.get(
    "/organizations/{organization_id}/can-manage-async-tournaments",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Check Async Tournament Management Permission"
)
async def can_manage_async_tournaments(
    organization_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    """
    Check if user can manage async tournaments in the organization.
    
    **Example Response:**
    ```json
    {
        "allowed": true
    }
    ```
    """
    helper = UIAuthorizationHelper()
    allowed = await helper.can_manage_async_tournaments(current_user, organization_id)
    return {"allowed": allowed}


@router.get(
    "/organizations/{organization_id}/can-review-async-races",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Check Async Race Review Permission"
)
async def can_review_async_races(
    organization_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    """
    Check if user can review async race submissions in the organization.
    
    **Example Response:**
    ```json
    {
        "allowed": false
    }
    ```
    """
    helper = UIAuthorizationHelper()
    allowed = await helper.can_review_async_races(current_user, organization_id)
    return {"allowed": allowed}


@router.get(
    "/organizations/{organization_id}/can-manage-members",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Check Member Management Permission"
)
async def can_manage_members(
    organization_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    """
    Check if user can manage organization members.
    
    **Example Response:**
    ```json
    {
        "allowed": true
    }
    ```
    """
    helper = UIAuthorizationHelper()
    allowed = await helper.can_manage_members(current_user, organization_id)
    return {"allowed": allowed}


@router.get(
    "/organizations/{organization_id}/can-manage-organization",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Check Organization Management Permission"
)
async def can_manage_organization(
    organization_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    """
    Check if user can manage organization settings.
    
    **Example Response:**
    ```json
    {
        "allowed": true
    }
    ```
    """
    helper = UIAuthorizationHelper()
    allowed = await helper.can_manage_organization(current_user, organization_id)
    return {"allowed": allowed}


@router.get(
    "/organizations/{organization_id}/can-manage-scheduled-tasks",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Check Scheduled Task Management Permission"
)
async def can_manage_scheduled_tasks(
    organization_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    """
    Check if user can manage scheduled tasks.
    
    **Example Response:**
    ```json
    {
        "allowed": false
    }
    ```
    """
    helper = UIAuthorizationHelper()
    allowed = await helper.can_manage_scheduled_tasks(current_user, organization_id)
    return {"allowed": allowed}


@router.get(
    "/organizations/{organization_id}/can-manage-race-room-profiles",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Check Race Room Profile Management Permission"
)
async def can_manage_race_room_profiles(
    organization_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    """
    Check if user can manage race room profiles.
    
    **Example Response:**
    ```json
    {
        "allowed": true
    }
    ```
    """
    helper = UIAuthorizationHelper()
    allowed = await helper.can_manage_race_room_profiles(current_user, organization_id)
    return {"allowed": allowed}


@router.get(
    "/organizations/{organization_id}/can-manage-live-races",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Check Live Race Management Permission"
)
async def can_manage_live_races(
    organization_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    """
    Check if user can manage live races.
    
    **Example Response:**
    ```json
    {
        "allowed": true
    }
    ```
    """
    helper = UIAuthorizationHelper()
    allowed = await helper.can_manage_live_races(current_user, organization_id)
    return {"allowed": allowed}
