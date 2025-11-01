"""API token-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path
from api.schemas.token import (
    ApiTokenOut,
    ApiTokenListResponse,
    ApiTokenCreateRequest,
    ApiTokenCreateResponse,
)
from api.deps import get_current_user, enforce_rate_limit
from application.services.api_token_service import ApiTokenService
from models import User

router = APIRouter(prefix="/tokens", tags=["tokens"])


@router.get(
    "/",
    response_model=ApiTokenListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List API Tokens",
    description="List all API tokens for the current user.",
    responses={
        200: {"description": "Tokens retrieved successfully"},
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_tokens(
    current_user: User = Depends(get_current_user)
) -> ApiTokenListResponse:
    """
    List user's API tokens.

    Returns all API tokens created by the authenticated user.
    Token values are not included in the response.

    Args:
        current_user: Authenticated user making the request

    Returns:
        ApiTokenListResponse: List of tokens and total count
    """
    service = ApiTokenService()
    tokens = await service.list_user_tokens(current_user.id)
    items = [ApiTokenOut.model_validate(token) for token in tokens]
    return ApiTokenListResponse(items=items, count=len(items))


@router.post(
    "/",
    response_model=ApiTokenCreateResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create API Token",
    description="Create a new API token for the current user.",
    responses={
        201: {"description": "Token created successfully"},
        401: {"description": "Invalid or missing authentication token"},
        422: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def create_token(
    data: ApiTokenCreateRequest,
    current_user: User = Depends(get_current_user)
) -> ApiTokenCreateResponse:
    """
    Create a new API token.

    Creates an API token for the authenticated user. The plaintext token
    value is only returned in this response and cannot be retrieved later.

    Args:
        data: Token creation data
        current_user: Authenticated user making the request

    Returns:
        ApiTokenCreateResponse: Token value and metadata
    """
    service = ApiTokenService()
    result = await service.create_token(
        user_id=current_user.id,
        name=data.name or "API Token",
        expires_at=data.expires_at
    )

    return ApiTokenCreateResponse(
        token=result["token"],
        token_info=ApiTokenOut.model_validate(result["token_obj"])
    )


@router.delete(
    "/{token_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Revoke API Token",
    description="Revoke an API token. Only the token owner can revoke their tokens.",
    responses={
        204: {"description": "Token revoked successfully"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Token not found or not owned by user"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=204,
)
async def revoke_token(
    token_id: int = Path(..., description="Token ID to revoke"),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Revoke an API token.

    Revokes the specified API token. Users can only revoke their own tokens.

    Args:
        token_id: ID of the token to revoke
        current_user: Authenticated user making the request

    Raises:
        HTTPException: 404 if token not found or not owned by user
    """
    service = ApiTokenService()
    
    # Verify token belongs to user
    tokens = await service.list_user_tokens(current_user.id)
    if not any(t.id == token_id for t in tokens):
        raise HTTPException(status_code=404, detail="Token not found")

    await service.revoke_token(token_id)
