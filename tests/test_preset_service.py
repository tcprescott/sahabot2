"""
Tests for preset service.

This module tests the business logic for preset management.
"""

import pytest
from application.services.preset_service import PresetService
from models.user import User, Permission
from models.preset import PresetNamespace, Preset


@pytest.fixture
async def preset_namespace(db):
    """Create a test preset namespace."""
    namespace = await PresetNamespace.create(
        name="test_namespace",
        owner_discord_id=123456789,
        is_public=True,
        description="Test namespace"
    )
    return namespace


@pytest.fixture
async def private_namespace(db):
    """Create a private test preset namespace."""
    namespace = await PresetNamespace.create(
        name="private_namespace",
        owner_discord_id=987654321,
        is_public=False,
        description="Private test namespace"
    )
    return namespace


@pytest.fixture
async def test_preset(preset_namespace):
    """Create a test preset."""
    preset = await Preset.create(
        namespace=preset_namespace,
        preset_name="test_preset",
        randomizer="alttpr",
        content="goal_name: test\nsettings:\n  preset: standard",
        description="Test preset"
    )
    return preset


@pytest.mark.asyncio
class TestPresetService:
    """Test PresetService class."""

    async def test_get_namespace(self, db, preset_namespace):
        """Test getting a namespace by name."""
        service = PresetService()
        namespace = await service.get_namespace("test_namespace")

        assert namespace is not None
        assert namespace.name == "test_namespace"
        assert namespace.owner_discord_id == 123456789

    async def test_get_namespace_not_found(self, db):
        """Test getting a non-existent namespace."""
        service = PresetService()
        namespace = await service.get_namespace("nonexistent")

        assert namespace is None

    async def test_create_namespace(self, db, sample_user):
        """Test creating a new namespace."""
        service = PresetService()
        namespace = await service.create_namespace(
            "new_namespace",
            sample_user,
            is_public=True,
            description="New test namespace"
        )

        assert namespace is not None
        assert namespace.name == "new_namespace"
        assert namespace.owner_discord_id == sample_user.discord_id
        assert namespace.is_public is True

    async def test_get_or_create_namespace_existing(self, db, preset_namespace, sample_user):
        """Test get_or_create with existing namespace."""
        service = PresetService()
        namespace = await service.get_or_create_namespace("test_namespace", sample_user)

        assert namespace.id == preset_namespace.id

    async def test_get_or_create_namespace_new(self, db, sample_user):
        """Test get_or_create with new namespace."""
        service = PresetService()
        namespace = await service.get_or_create_namespace("brand_new", sample_user)

        assert namespace is not None
        assert namespace.name == "brand_new"

    async def test_is_namespace_owner(self, db, preset_namespace, sample_user):
        """Test namespace ownership check."""
        service = PresetService()

        # Create user with matching discord_id
        owner = await User.create(
            discord_id=123456789,
            discord_username="owner",
            discord_discriminator="0001",
            discord_avatar="avatar",
            discord_email="owner@example.com",
            permission=Permission.USER
        )

        assert service.is_namespace_owner(owner, preset_namespace) is True
        assert service.is_namespace_owner(sample_user, preset_namespace) is False

    async def test_list_presets_public_only(self, db, test_preset, sample_user):
        """Test listing public presets."""
        service = PresetService()

        # Create a private preset
        private_ns = await PresetNamespace.create(
            name="private",
            owner_discord_id=999999,
            is_public=False
        )
        await Preset.create(
            namespace=private_ns,
            preset_name="private_preset",
            randomizer="alttpr",
            content="test: data"
        )

        # List as non-owner (should only see public)
        presets = await service.list_presets(user=sample_user)

        assert len(presets) == 1
        assert presets[0].preset_name == "test_preset"

    async def test_create_preset(self, db, preset_namespace, sample_user):
        """Test creating a new preset."""
        service = PresetService()

        # Create user with matching discord_id
        owner = await User.create(
            discord_id=123456789,
            discord_username="owner",
            discord_discriminator="0001",
            discord_avatar="avatar",
            discord_email="owner@example.com",
            permission=Permission.USER
        )

        preset = await service.create_preset(
            "test_namespace",
            "new_preset",
            "smz3",
            "goal_name: test\nsettings:\n  mode: normal",
            owner,
            "New test preset"
        )

        assert preset is not None
        assert preset.preset_name == "new_preset"
        assert preset.randomizer == "smz3"

    async def test_create_preset_invalid_yaml(self, db, preset_namespace, sample_user):
        """Test creating preset with invalid YAML."""
        service = PresetService()

        # Create user with matching discord_id
        owner = await User.create(
            discord_id=123456789,
            discord_username="owner",
            discord_discriminator="0001",
            discord_avatar="avatar",
            discord_email="owner@example.com",
            permission=Permission.USER
        )

        with pytest.raises(ValueError, match="Invalid YAML"):
            await service.create_preset(
                "test_namespace",
                "bad_preset",
                "alttpr",
                "invalid: yaml: content: [unclosed",
                owner
            )

    async def test_update_preset(self, db, test_preset, sample_user):
        """Test updating a preset."""
        service = PresetService()

        # Create owner user
        owner = await User.create(
            discord_id=123456789,
            discord_username="owner",
            discord_discriminator="0001",
            discord_avatar="avatar",
            discord_email="owner@example.com",
            permission=Permission.USER
        )

        new_content = "goal_name: updated\nsettings:\n  preset: advanced"
        success = await service.update_preset(
            test_preset,
            content=new_content,
            description="Updated description",
            user=owner
        )

        assert success is True

        # Verify update
        updated = await service.get_preset("test_namespace", "test_preset", "alttpr")
        assert updated.content == new_content
        assert updated.description == "Updated description"

    async def test_delete_preset(self, db, test_preset):
        """Test deleting a preset."""
        service = PresetService()

        # Create owner user
        owner = await User.create(
            discord_id=123456789,
            discord_username="owner",
            discord_discriminator="0001",
            discord_avatar="avatar",
            discord_email="owner@example.com",
            permission=Permission.USER
        )

        success = await service.delete_preset(test_preset, owner)
        assert success is True

        # Verify deletion
        preset = await service.get_preset("test_namespace", "test_preset", "alttpr")
        assert preset is None

    async def test_get_preset_content_as_dict(self, db, test_preset):
        """Test parsing preset content as dict."""
        service = PresetService()

        content = await service.get_preset_content_as_dict(test_preset)

        assert isinstance(content, dict)
        assert content.get("goal_name") == "test"
        assert "settings" in content

    async def test_list_presets_for_randomizer(self, db, test_preset):
        """Test listing presets for a specific randomizer."""
        service = PresetService()

        # Add another preset for different randomizer
        await Preset.create(
            namespace=test_preset.namespace,
            preset_name="smz3_preset",
            randomizer="smz3",
            content="test: data"
        )

        # List ALTTPR presets
        presets = await service.list_presets_for_randomizer("alttpr", include_namespace_names=True)

        assert isinstance(presets, dict)
        assert "test_namespace" in presets
        assert "test_preset" in presets["test_namespace"]

    async def test_permission_check_unauthorized(self, db, test_preset, sample_user):
        """Test that unauthorized user cannot edit preset."""
        service = PresetService()

        success = await service.update_preset(
            test_preset,
            content="new content",
            user=sample_user
        )

        assert success is False
