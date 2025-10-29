"""API dependencies for token-based authentication and authorization."""

from typing import Callable, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from application.services.authorization_service import AuthorizationService
from application.services.api_token_service import ApiTokenService
from application.services.rate_limit_service import RateLimitService
from config import settings
from models import User, Permission


_http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(_http_bearer)) -> User:
    """
    Dependency to retrieve the current authenticated user via Bearer token.
    """
    if not credentials or not credentials.scheme or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    token = credentials.credentials
    service = ApiTokenService()
    user = await service.verify_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


def require_permission(required: Permission) -> Callable[[User], User]:
    """Dependency factory to enforce a minimum permission level using AuthorizationService."""

    async def _enforce(user: User = Depends(get_current_user)) -> User:
        authz = AuthorizationService()
        if required == Permission.ADMIN and not authz.can_access_admin_panel(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        if required == Permission.MODERATOR and not authz.can_moderate(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        if required == Permission.SUPERADMIN and not user.has_permission(Permission.SUPERADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _enforce


async def enforce_rate_limit(user: User = Depends(get_current_user)) -> None:
    """Enforce per-user API rate limit.

    Uses user.api_rate_limit_per_minute if set; otherwise falls back to settings.
    Raises HTTP 429 with Retry-After header when exceeded.
    """
    per_minute = user.api_rate_limit_per_minute or settings.API_DEFAULT_RATE_LIMIT_PER_MINUTE
    window = settings.API_RATE_LIMIT_WINDOW_SECONDS
    limiter = RateLimitService()
    allowed, retry_after = await limiter.enforce(user.id, per_minute, window)
    if not allowed:
        headers = {"Retry-After": str(int(retry_after) or 1)}
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded", headers=headers)
