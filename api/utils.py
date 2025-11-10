"""Utility functions and decorators for API endpoints to reduce boilerplate."""

from typing import TypeVar, Generic, Callable, Any, Dict
from pydantic import BaseModel, Field
from functools import wraps
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ListResponse(BaseModel, Generic[T]):
    """Generic list response schema.

    This eliminates the need to create separate XxxListResponse classes
    for every entity type.

    Example:
        ```python
        @router.get("/", response_model=ListResponse[UserOut])
        async def list_users() -> ListResponse[UserOut]:
            users = await service.get_users()
            return create_list_response(users)
        ```
    """

    items: list[T] = Field(..., description="List of items")
    count: int = Field(..., description="Total number of items in the result")


def create_list_response(items: list[T]) -> ListResponse[T]:
    """Create a standardized list response.

    Args:
        items: List of items to return

    Returns:
        ListResponse with items and count
    """
    return ListResponse(items=items, count=len(items))


# Common response documentation patterns
COMMON_RESPONSES: Dict[int, Dict[str, str]] = {
    200: {"description": "Request successful"},
    201: {"description": "Resource created successfully"},
    204: {"description": "Resource deleted successfully"},
    400: {"description": "Bad request"},
    401: {"description": "Invalid or missing authentication token"},
    403: {"description": "Insufficient permissions"},
    404: {"description": "Resource not found"},
    422: {"description": "Validation error"},
    429: {"description": "Rate limit exceeded"},
}


def api_responses(*status_codes: int) -> Dict[int, Dict[str, str]]:
    """Generate common response documentation.

    Args:
        *status_codes: HTTP status codes to include in responses

    Returns:
        Dictionary of response documentation for OpenAPI

    Example:
        ```python
        @router.get("/", responses=api_responses(200, 401, 429))
        async def get_items():
            ...
        ```
    """
    return {code: COMMON_RESPONSES[code] for code in status_codes}


def handle_not_found(
    resource: Any | None, resource_name: str = "Resource"
) -> Any:
    """Raise HTTPException if resource is None, otherwise return resource.

    This eliminates repetitive None checks and HTTPException raising.

    Args:
        resource: The resource to check (typically from service layer)
        resource_name: Name of the resource for error message

    Returns:
        The resource if not None

    Raises:
        HTTPException: 404 if resource is None

    Example:
        ```python
        user = await service.get_user(user_id)
        return UserOut.model_validate(handle_not_found(user, "User"))
        ```
    """
    if resource is None:
        raise HTTPException(status_code=404, detail=f"{resource_name} not found")
    return resource


def handle_unauthorized(
    resource: Any | None,
    resource_name: str = "Resource",
    custom_message: str | None = None,
) -> Any:
    """Raise HTTPException if resource is None (indicating unauthorized), otherwise return resource.

    This handles the common pattern where service returns None for both
    "not found" and "insufficient permissions".

    Args:
        resource: The resource to check
        resource_name: Name of the resource for error message
        custom_message: Custom error message (optional)

    Returns:
        The resource if not None

    Raises:
        HTTPException: 403 if resource is None

    Example:
        ```python
        tournament = await service.create_tournament(...)
        return TournamentOut.model_validate(
            handle_unauthorized(tournament, "Tournament", "Insufficient permissions to create tournaments")
        )
        ```
    """
    if resource is None:
        message = (
            custom_message
            if custom_message
            else f"{resource_name} not found or insufficient permissions"
        )
        raise HTTPException(status_code=403, detail=message)
    return resource


def validate_model_list(items: list[Any], model: type[T]) -> list[T]:
    """Validate and convert list of ORM objects to Pydantic models.

    This eliminates the repetitive list comprehension pattern.

    Args:
        items: List of ORM objects
        model: Pydantic model class to validate against

    Returns:
        List of validated Pydantic models

    Example:
        ```python
        users = await service.get_users()
        items = validate_model_list(users, UserOut)
        return create_list_response(items)
        ```
    """
    return [model.model_validate(item) for item in items]


def endpoint_handler(func: Callable) -> Callable:
    """Decorator to add standard error handling to API endpoints.

    This catches common exceptions and converts them to appropriate HTTP responses.

    Args:
        func: The endpoint function to wrap

    Returns:
        Wrapped function with error handling

    Example:
        ```python
        @router.get("/")
        @endpoint_handler
        async def get_items():
            # Will automatically handle exceptions
            return await service.get_items()
        ```
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # Re-raise HTTPExceptions as-is
            raise
        except ValueError as e:
            logger.warning("Validation error in %s: %s", func.__name__, e)
            raise HTTPException(status_code=422, detail=str(e)) from e
        except PermissionError as e:
            logger.warning("Permission denied in %s: %s", func.__name__, e)
            raise HTTPException(status_code=403, detail=str(e)) from e
        except Exception as e:
            logger.error("Unexpected error in %s: %s", func.__name__, e, exc_info=True)
            raise HTTPException(
                status_code=500, detail="Internal server error"
            ) from e

    return wrapper
