"""Unit tests for schema utility classes and functions."""

import pytest
from datetime import datetime
from pydantic import BaseModel, Field
from api.schema_utils import (
    BaseOutSchema,
    BaseListResponse,
    make_list_response,
    TimestampMixin,
    OrganizationScopedMixin,
)


class SampleOut(BaseOutSchema):
    """Sample output schema for testing."""

    id: int
    name: str


class SampleORMModel:
    """Mock ORM model."""

    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name


class TestBaseOutSchema:
    """Test BaseOutSchema base class."""

    def test_from_attributes_enabled(self):
        """Test that from_attributes is automatically enabled."""
        # BaseOutSchema should have from_attributes=True via model_config
        assert SampleOut.model_config.get("from_attributes") is True

    def test_can_validate_from_orm(self):
        """Test that BaseOutSchema can validate ORM objects."""
        orm_obj = SampleORMModel(id=1, name="Test")
        result = SampleOut.model_validate(orm_obj)

        assert result.id == 1
        assert result.name == "Test"

    def test_can_validate_from_dict(self):
        """Test that BaseOutSchema can validate dictionaries."""
        data = {"id": 2, "name": "Test2"}
        result = SampleOut.model_validate(data)

        assert result.id == 2
        assert result.name == "Test2"


class TestBaseListResponse:
    """Test BaseListResponse generic class."""

    def test_create_list_response(self):
        """Test creating a list response with typed items."""
        items = [
            SampleOut(id=1, name="Item 1"),
            SampleOut(id=2, name="Item 2"),
        ]
        response = BaseListResponse[SampleOut](items=items, count=2)

        assert response.count == 2
        assert len(response.items) == 2
        assert response.items[0].name == "Item 1"

    def test_empty_list_response(self):
        """Test creating an empty list response."""
        response = BaseListResponse[SampleOut](items=[], count=0)

        assert response.count == 0
        assert len(response.items) == 0

    def test_json_serialization(self):
        """Test that list response can be serialized to JSON."""
        items = [SampleOut(id=1, name="Test")]
        response = BaseListResponse[SampleOut](items=items, count=1)

        # Should serialize without errors
        json_data = response.model_dump()
        assert json_data["count"] == 1
        assert len(json_data["items"]) == 1


class TestMakeListResponse:
    """Test make_list_response factory function."""

    def test_creates_typed_list_response(self):
        """Test that factory creates a properly typed list response."""
        ListResponse = make_list_response(SampleOut)

        items = [SampleOut(id=1, name="Test")]
        response = ListResponse(items=items, count=1)

        assert isinstance(response, BaseListResponse)
        assert response.count == 1
        assert len(response.items) == 1

    def test_generated_class_has_correct_name(self):
        """Test that generated class has a descriptive name."""
        ListResponse = make_list_response(SampleOut)

        assert ListResponse.__name__ == "SampleOutListResponse"

    def test_can_be_used_as_response_model(self):
        """Test that generated class can be used as FastAPI response_model."""
        UserListResponse = make_list_response(SampleOut)

        # Should have the expected structure for OpenAPI
        schema = UserListResponse.model_json_schema()
        assert "properties" in schema
        assert "items" in schema["properties"]
        assert "count" in schema["properties"]


class TestTimestampMixin:
    """Test TimestampMixin."""

    def test_adds_timestamp_fields(self):
        """Test that mixin adds created_at and updated_at fields."""

        class WithTimestamps(BaseOutSchema, TimestampMixin):
            id: int
            name: str

        # Check that fields exist
        fields = WithTimestamps.model_fields
        assert "created_at" in fields
        assert "updated_at" in fields
        assert "id" in fields
        assert "name" in fields

    def test_can_create_instance_with_timestamps(self):
        """Test creating an instance with timestamp fields."""

        class WithTimestamps(BaseOutSchema, TimestampMixin):
            id: int
            name: str

        now = datetime.now()
        instance = WithTimestamps(
            id=1,
            name="Test",
            created_at=now,
            updated_at=now,
        )

        assert instance.id == 1
        assert instance.name == "Test"
        assert instance.created_at == now
        assert instance.updated_at == now


class TestOrganizationScopedMixin:
    """Test OrganizationScopedMixin."""

    def test_adds_organization_id_field(self):
        """Test that mixin adds organization_id field."""

        class OrgScoped(BaseOutSchema, OrganizationScopedMixin):
            id: int
            name: str

        fields = OrgScoped.model_fields
        assert "organization_id" in fields
        assert "id" in fields
        assert "name" in fields

    def test_can_create_instance_with_org_id(self):
        """Test creating an instance with organization_id."""

        class OrgScoped(BaseOutSchema, OrganizationScopedMixin):
            id: int
            name: str

        instance = OrgScoped(
            id=1,
            name="Test",
            organization_id=42,
        )

        assert instance.id == 1
        assert instance.name == "Test"
        assert instance.organization_id == 42


class TestMixinCombination:
    """Test combining multiple mixins."""

    def test_can_combine_all_mixins(self):
        """Test that all mixins can be combined."""

        class FullModel(
            BaseOutSchema,
            OrganizationScopedMixin,
            TimestampMixin,
        ):
            id: int
            name: str

        fields = FullModel.model_fields
        assert "id" in fields
        assert "name" in fields
        assert "organization_id" in fields
        assert "created_at" in fields
        assert "updated_at" in fields

    def test_combined_instance_creation(self):
        """Test creating instance with all mixin fields."""

        class FullModel(
            BaseOutSchema,
            OrganizationScopedMixin,
            TimestampMixin,
        ):
            id: int
            name: str

        now = datetime.now()
        instance = FullModel(
            id=1,
            name="Test",
            organization_id=42,
            created_at=now,
            updated_at=now,
        )

        assert instance.id == 1
        assert instance.name == "Test"
        assert instance.organization_id == 42
        assert instance.created_at == now
        assert instance.updated_at == now

    def test_combined_from_orm(self):
        """Test that combined mixins work with ORM objects."""

        class FullModel(
            BaseOutSchema,
            OrganizationScopedMixin,
            TimestampMixin,
        ):
            id: int
            name: str

        class ORMModel:
            def __init__(self):
                self.id = 1
                self.name = "Test"
                self.organization_id = 42
                self.created_at = datetime.now()
                self.updated_at = datetime.now()

        orm_obj = ORMModel()
        instance = FullModel.model_validate(orm_obj)

        assert instance.id == 1
        assert instance.name == "Test"
        assert instance.organization_id == 42
