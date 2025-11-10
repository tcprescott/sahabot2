"""Utility classes and functions for reducing schema boilerplate.

This module provides base classes and helpers for Pydantic schemas to reduce
repetitive configuration and patterns across API schemas.
"""

from typing import TypeVar, Generic, Type
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T", bound=BaseModel)


class BaseOutSchema(BaseModel):
    """Base class for output schemas.

    Automatically configures from_attributes for ORM compatibility.
    Eliminates the need to add `Config: from_attributes = True` to every Out schema.

    Example:
        ```python
        class UserOut(BaseOutSchema):
            id: int
            name: str
            # No need for Config class!
        ```
    """

    model_config = ConfigDict(from_attributes=True)


class BaseListResponse(BaseModel, Generic[T]):
    """Generic base class for list response schemas.

    Provides the standard list + count structure. Can be used directly or
    extended for backward compatibility.

    Example:
        ```python
        # Direct use with generic type
        @router.get("/", response_model=BaseListResponse[UserOut])
        async def list_users() -> BaseListResponse[UserOut]:
            users = await service.get_users()
            return BaseListResponse(items=users, count=len(users))

        # Or extend for backward compatibility
        class UserListResponse(BaseListResponse[UserOut]):
            pass
        ```
    """

    items: list[T] = Field(..., description="List of items")
    count: int = Field(..., description="Total number of items in the result")


def make_list_response(item_class: Type[T]) -> Type[BaseListResponse[T]]:
    """Create a list response class for a given item type.

    This factory function creates a properly typed list response class.
    Useful when you need a named class for OpenAPI documentation.

    Args:
        item_class: The Pydantic model class for items in the list

    Returns:
        A new list response class typed for the given item class

    Example:
        ```python
        from api.schemas.user import UserOut

        # Create a typed list response
        UserListResponse = make_list_response(UserOut)

        @router.get("/", response_model=UserListResponse)
        async def list_users() -> UserListResponse:
            ...
        ```
    """

    class ListResponse(BaseListResponse[item_class]):  # type: ignore
        """List response for the given item type."""

        pass

    # Set a meaningful name for OpenAPI docs
    ListResponse.__name__ = f"{item_class.__name__}ListResponse"
    return ListResponse  # type: ignore


def create_update_schema(create_schema: Type[BaseModel]) -> Type[BaseModel]:
    """Generate an update schema from a create schema.

    Creates an update schema where all fields are optional. This eliminates
    the need to duplicate field definitions between Create and Update schemas.

    Args:
        create_schema: The create schema to base the update schema on

    Returns:
        A new update schema class with all fields made optional

    Example:
        ```python
        class TournamentCreateRequest(BaseModel):
            name: str = Field(..., description="Tournament name")
            description: str | None = Field(None, description="Description")
            is_active: bool = Field(True, description="Active status")

        # Generate update schema automatically
        TournamentUpdateRequest = create_update_schema(TournamentCreateRequest)

        # All fields are now Optional[...] in TournamentUpdateRequest
        ```

    Note:
        This is a runtime generation approach. For better IDE support,
        you may still want to explicitly define update schemas in many cases.
        This helper is most useful for simple CRUD operations.
    """
    from typing import Optional, get_type_hints, get_origin
    from pydantic import create_model

    # Get field definitions from the create schema
    fields = {}
    for field_name, field_info in create_schema.model_fields.items():
        # Make field optional
        field_type = field_info.annotation
        if get_origin(field_type) is not Optional:
            field_type = Optional[field_type]  # type: ignore

        # Copy field metadata
        fields[field_name] = (field_type, Field(default=None, **field_info.metadata[0].metadata))  # type: ignore

    # Create the new model
    update_model = create_model(
        f"{create_schema.__name__.replace('Create', 'Update')}",
        **fields,  # type: ignore
        __base__=BaseModel,
    )

    return update_model


class TimestampMixin(BaseModel):
    """Mixin for models with created_at and updated_at timestamps.

    Reduces repetition of timestamp fields across output schemas.

    Example:
        ```python
        class UserOut(BaseOutSchema, TimestampMixin):
            id: int
            name: str
            # created_at and updated_at are automatically included
        ```
    """

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class OrganizationScopedMixin(BaseModel):
    """Mixin for models that belong to an organization.

    Reduces repetition of organization_id field across schemas.

    Example:
        ```python
        class TournamentOut(BaseOutSchema, OrganizationScopedMixin, TimestampMixin):
            id: int
            name: str
            # organization_id, created_at, updated_at are automatically included
        ```
    """

    organization_id: int = Field(..., description="Organization ID")
