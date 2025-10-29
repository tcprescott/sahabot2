import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from api.deps import get_current_user, require_permission
from application.services.api_token_service import ApiTokenService
from models.user import Permission


@pytest.mark.asyncio
async def test_get_current_user_with_valid_token(sample_user):
    # Generate token for sample user
    token, _ = await ApiTokenService().generate_token(sample_user, name="test")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = await get_current_user(creds)
    assert user.id == sample_user.id


@pytest.mark.asyncio
async def test_get_current_user_with_invalid_token_raises():
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="nope")
    with pytest.raises(HTTPException) as ei:
        await get_current_user(creds)
    assert ei.value.status_code == 401


@pytest.mark.asyncio
async def test_require_permission_admin_allows_admin(admin_user):
    dep = require_permission(Permission.ADMIN)
    # Call the inner dependency directly with admin user
    user = await dep(admin_user)  # type: ignore[arg-type]
    assert user.id == admin_user.id
