"""User-related API endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from api.schemas.user import UserOut, UserListResponse
from api.deps import get_current_user, enforce_rate_limit
from application.services.core.user_service import UserService
from middleware.auth import DiscordAuthService
from models import User, Permission


router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Current User",
    description="Get the profile information for the currently authenticated user.",
    responses={
        200: {
            "description": "User profile retrieved successfully",
        },
        401: {
            "description": "Invalid or missing authentication token",
        },
        429: {
            "description": "Rate limit exceeded",
        },
    },
)
async def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    """
    Get current authenticated user profile.
    
    Returns the full profile information for the user associated with the
    provided Bearer token.
    
    Args:
        current_user: Injected current user from Bearer token
        
    Returns:
        UserOut: User profile data
    """
    return UserOut.model_validate(current_user)


@router.get(
    "/",
    response_model=UserListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List All Users",
    description="List all users in the system. Requires ADMIN permission.",
    responses={
        200: {
            "description": "Users retrieved successfully",
        },
        401: {
            "description": "Invalid or missing authentication token",
        },
        403: {
            "description": "Insufficient permissions (requires ADMIN)",
        },
        429: {
            "description": "Rate limit exceeded",
        },
    },
)
async def list_users(
    current_user: User = Depends(get_current_user),
    include_inactive: bool = Query(
        False,
        description="Include inactive/disabled users in the results"
    )
) -> UserListResponse:
    """
    List all users (admin only).
    
    Retrieve a list of all users in the system. By default, only active users
    are returned. Set include_inactive=true to include disabled users.
    
    Authorization is enforced at the service layer.
    
    Args:
        current_user: Authenticated user making the request
        include_inactive: Whether to include inactive users
        
    Returns:
        UserListResponse: List of users and total count (empty if unauthorized)
    """
    service = UserService()
    users = await service.get_all_users(current_user, include_inactive=include_inactive)
    items = [UserOut.model_validate(u) for u in users]
    return UserListResponse(items=items, count=len(items))


@router.get(
    "/search",
    response_model=UserListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Search Users",
    description="Search for users by username. Requires MODERATOR permission.",
    responses={
        200: {
            "description": "Search results retrieved successfully",
        },
        401: {
            "description": "Invalid or missing authentication token",
        },
        403: {
            "description": "Insufficient permissions (requires MODERATOR)",
        },
        422: {
            "description": "Invalid search query (must be 2-100 characters)",
        },
        429: {
            "description": "Rate limit exceeded",
        },
    },
)
async def search_users(
    current_user: User = Depends(get_current_user),
    q: str = Query(
        ...,
        min_length=2,
        max_length=100,
        description="Search query for username (minimum 2 characters)"
    )
) -> UserListResponse:
    """
    Search users by username (moderator+).
    
    Search for users whose Discord username contains the search query.
    Case-insensitive partial match search.
    
    Authorization is enforced at the service layer.
    
    Args:
        current_user: Authenticated user making the request
        q: Search query string (2-100 characters)
        
    Returns:
        UserListResponse: Matching users and total count (empty if unauthorized)
    """
    service = UserService()
    users = await service.search_users(current_user, q)
    items = [UserOut.model_validate(u) for u in users]
    return UserListResponse(items=items, count=len(items))


@router.post(
    "/admin/impersonate/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Start Impersonating User",
    description="Start impersonating another user. Requires SUPERADMIN permission.",
    responses={
        200: {
            "description": "Impersonation started successfully",
        },
        401: {
            "description": "Invalid or missing authentication token",
        },
        403: {
            "description": "Insufficient permissions (requires SUPERADMIN)",
        },
        404: {
            "description": "Target user not found",
        },
        429: {
            "description": "Rate limit exceeded",
        },
    },
)
async def start_impersonation(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user)
) -> UserOut:
    """
    Start impersonating another user (SUPERADMIN only).
    
    Only SUPERADMIN users can impersonate others.
    Cannot impersonate yourself.
    All impersonation actions are audit logged with IP address.
    
    Args:
        user_id: ID of user to impersonate
        request: FastAPI request (for IP address)
        current_user: Currently authenticated user
        
    Returns:
        UserOut: The user being impersonated
        
    Raises:
        HTTPException: 403 if unauthorized, 404 if user not found
    """
    # Get IP address
    ip_address = request.client.host if request.client else None
    
    # Start impersonation via service (handles permissions and audit)
    service = UserService()
    target_user = await service.start_impersonation(
        admin_user=current_user,
        target_user_id=user_id,
        ip_address=ip_address
    )
    
    if not target_user:
        # Check if it's a permission issue or user not found
        if not current_user.has_permission(Permission.SUPERADMIN):
            raise HTTPException(
                status_code=403,
                detail="Only SUPERADMIN users can impersonate others"
            )
        elif current_user.id == user_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot impersonate yourself"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
    
    # Set impersonation in session
    await DiscordAuthService.start_impersonation(target_user)
    
    return UserOut.model_validate(target_user)


@router.post(
    "/admin/stop-impersonation",
    response_model=UserOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Stop Impersonating User",
    description="Stop impersonating and return to original user.",
    responses={
        200: {
            "description": "Impersonation stopped successfully",
        },
        401: {
            "description": "Invalid or missing authentication token",
        },
        400: {
            "description": "Not currently impersonating",
        },
        429: {
            "description": "Rate limit exceeded",
        },
    },
)
async def stop_impersonation(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> UserOut:
    """
    Stop impersonating and return to original user.
    
    Can only be called when impersonation is active.
    All impersonation actions are audit logged with IP address.
    
    Args:
        request: FastAPI request (for IP address)
        current_user: Currently authenticated user (impersonated user)
        
    Returns:
        UserOut: The original user
        
    Raises:
        HTTPException: 400 if not currently impersonating
    """
    # Check if impersonation is active
    if not DiscordAuthService.is_impersonating():
        raise HTTPException(
            status_code=400,
            detail="Not currently impersonating"
        )
    
    # Get original user and impersonated user
    original_user = await DiscordAuthService.get_original_user()
    impersonated_user = current_user  # This is the impersonated user
    
    # Get IP address
    ip_address = request.client.host if request.client else None
    
    # Stop impersonation via service (audit logging)
    service = UserService()
    await service.stop_impersonation(
        original_user=original_user,
        impersonated_user=impersonated_user,
        ip_address=ip_address
    )
    
    # Clear impersonation from session
    await DiscordAuthService.stop_impersonation()
    
    return UserOut.model_validate(original_user)

