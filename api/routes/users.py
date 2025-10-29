"""User-related API endpoints."""

from fastapi import APIRouter, Depends, Query
from api.schemas.user import UserOut, UserListResponse
from api.deps import get_current_user, require_permission, enforce_rate_limit
from application.services.user_service import UserService
from models import User, Permission


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut, dependencies=[Depends(enforce_rate_limit)])
async def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    """Get the current authenticated user."""
    return UserOut.model_validate(current_user)


@router.get("/", response_model=UserListResponse, dependencies=[Depends(enforce_rate_limit), Depends(require_permission(Permission.ADMIN))])
async def list_users(include_inactive: bool = Query(False)) -> UserListResponse:
    """List users (admin only)."""
    service = UserService()
    users = await service.get_all_users(include_inactive=include_inactive)
    items = [UserOut.model_validate(u) for u in users]
    return UserListResponse(items=items, count=len(items))


@router.get("/search", response_model=UserListResponse, dependencies=[Depends(enforce_rate_limit), Depends(require_permission(Permission.MODERATOR))])
async def search_users(q: str = Query(..., min_length=2, max_length=100)) -> UserListResponse:
    """Search users by username (moderator+)."""
    service = UserService()
    users = await service.search_users(q)
    items = [UserOut.model_validate(u) for u in users]
    return UserListResponse(items=items, count=len(items))
