import pytest

from application.services.security.api_token_service import ApiTokenService


@pytest.mark.asyncio
async def test_generate_and_verify_token_returns_user(sample_user):
    service = ApiTokenService()
    token, _api_token = await service.generate_token(sample_user, name="test")
    assert token and isinstance(token, str)
    user = await service.verify_token(token)
    assert user is not None
    assert user.id == sample_user.id


@pytest.mark.asyncio
async def test_verify_invalid_token_returns_none():
    service = ApiTokenService()
    user = await service.verify_token("not-a-real-token")
    assert user is None
