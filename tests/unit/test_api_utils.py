"""Unit tests for API utility functions."""

import pytest
from fastapi import HTTPException
from pydantic import BaseModel, Field
from api.utils import (
    ListResponse,
    create_list_response,
    api_responses,
    handle_not_found,
    handle_unauthorized,
    validate_model_list,
)


class SampleModel(BaseModel):
    """Test model for validation."""

    id: int = Field(..., description="ID")
    name: str = Field(..., description="Name")

    class Config:
        from_attributes = True


class SampleItem:
    """Mock ORM model."""

    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name


class TestListResponse:
    """Test ListResponse generic class."""

    def test_create_list_response(self):
        """Test creating a list response."""
        items = [SampleModel(id=1, name="Item 1"), SampleModel(id=2, name="Item 2")]
        response = create_list_response(items)

        assert isinstance(response, ListResponse)
        assert response.count == 2
        assert len(response.items) == 2
        assert response.items[0].name == "Item 1"

    def test_create_empty_list_response(self):
        """Test creating an empty list response."""
        response = create_list_response([])

        assert response.count == 0
        assert len(response.items) == 0


class TestApiResponses:
    """Test api_responses helper."""

    def test_single_response(self):
        """Test generating a single response."""
        responses = api_responses(200)

        assert 200 in responses
        assert responses[200]["description"] == "Request successful"

    def test_multiple_responses(self):
        """Test generating multiple responses."""
        responses = api_responses(200, 401, 404, 429)

        assert len(responses) == 4
        assert 200 in responses
        assert 401 in responses
        assert 404 in responses
        assert 429 in responses

    def test_common_crud_responses(self):
        """Test generating typical CRUD operation responses."""
        # GET
        get_responses = api_responses(200, 401, 404, 429)
        assert 200 in get_responses

        # POST
        post_responses = api_responses(201, 401, 403, 422, 429)
        assert 201 in post_responses

        # DELETE
        delete_responses = api_responses(204, 401, 403, 404, 429)
        assert 204 in delete_responses


class TestHandleNotFound:
    """Test handle_not_found helper."""

    def test_returns_resource_when_not_none(self):
        """Test that resource is returned when not None."""
        resource = {"id": 1, "name": "Test"}
        result = handle_not_found(resource, "Test Resource")

        assert result == resource

    def test_raises_404_when_none(self):
        """Test that HTTPException is raised when resource is None."""
        with pytest.raises(HTTPException) as exc_info:
            handle_not_found(None, "Test Resource")

        assert exc_info.value.status_code == 404
        assert "Test Resource not found" in exc_info.value.detail

    def test_custom_resource_name(self):
        """Test that custom resource name is used in error message."""
        with pytest.raises(HTTPException) as exc_info:
            handle_not_found(None, "User")

        assert "User not found" in exc_info.value.detail


class TestHandleUnauthorized:
    """Test handle_unauthorized helper."""

    def test_returns_resource_when_not_none(self):
        """Test that resource is returned when not None."""
        resource = {"id": 1, "name": "Test"}
        result = handle_unauthorized(resource, "Test Resource")

        assert result == resource

    def test_raises_403_when_none(self):
        """Test that HTTPException is raised when resource is None."""
        with pytest.raises(HTTPException) as exc_info:
            handle_unauthorized(None, "Tournament")

        assert exc_info.value.status_code == 403
        assert "not found or insufficient permissions" in exc_info.value.detail

    def test_custom_error_message(self):
        """Test that custom error message is used."""
        custom_msg = "Only admins can create tournaments"

        with pytest.raises(HTTPException) as exc_info:
            handle_unauthorized(None, "Tournament", custom_msg)

        assert exc_info.value.status_code == 403
        assert custom_msg in exc_info.value.detail


class TestValidateModelList:
    """Test validate_model_list helper."""

    def test_validates_list_of_orm_objects(self):
        """Test validating a list of ORM objects."""
        items = [SampleItem(id=1, name="Item 1"), SampleItem(id=2, name="Item 2")]
        result = validate_model_list(items, SampleModel)

        assert len(result) == 2
        assert all(isinstance(item, SampleModel) for item in result)
        assert result[0].name == "Item 1"
        assert result[1].name == "Item 2"

    def test_validates_empty_list(self):
        """Test validating an empty list."""
        result = validate_model_list([], SampleModel)

        assert len(result) == 0

    def test_validates_single_item(self):
        """Test validating a list with single item."""
        items = [SampleItem(id=1, name="Single")]
        result = validate_model_list(items, SampleModel)

        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].name == "Single"
