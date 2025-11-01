"""User-related API endpoints."""

from fastapi import APIRouter, Depends, Query
from api.schemas.user import UserOut, UserListResponse
from api.deps import get_current_user, enforce_rate_limit
from application.services.user_service import UserService
from models import User


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
