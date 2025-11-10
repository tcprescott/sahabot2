"""
Unit tests for User model.

Tests the User model methods and properties.
"""

import pytest
from models.user import User, Permission


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserModel:
    """Test cases for the User model."""

    async def test_create_user(self, db, discord_user_payload):
        """Test creating a user."""
        user = await User.create(
            discord_id=int(discord_user_payload["id"]),
            discord_username=discord_user_payload["username"],
            discord_discriminator=discord_user_payload["discriminator"],
            discord_avatar=discord_user_payload["avatar"],
            permission=Permission.USER,
            is_active=True,
        )

        # Verify user was created with correct fields
        assert user.id is not None
        assert user.discord_id == int(discord_user_payload["id"])
        assert user.discord_username == discord_user_payload["username"]
        assert user.permission == Permission.USER
        assert user.is_active is True
        assert user.created_at is not None

    async def test_has_permission(self, sample_user):
        """Test has_permission method."""
        # USER should not have ADMIN permission
        assert not sample_user.has_permission(Permission.ADMIN)

        # USER should have USER permission
        assert sample_user.has_permission(Permission.USER)

        # Set user to ADMIN
        sample_user.permission = Permission.ADMIN
        await sample_user.save()

        # ADMIN should have USER and MODERATOR permissions
        assert sample_user.has_permission(Permission.USER)
        assert sample_user.has_permission(Permission.MODERATOR)
        assert sample_user.has_permission(Permission.ADMIN)

        # ADMIN should not have SUPERADMIN permission
        assert not sample_user.has_permission(Permission.SUPERADMIN)

    async def test_is_admin(self, sample_user, admin_user):
        """Test is_admin method."""
        # Regular user should not be admin
        assert not sample_user.is_admin()

        # Admin user should be admin
        assert admin_user.is_admin()

        # SUPERADMIN should also be admin
        sample_user.permission = Permission.SUPERADMIN
        await sample_user.save()
        assert sample_user.is_admin()

    async def test_is_moderator(self, sample_user):
        """Test is_moderator method."""
        # USER should not be moderator
        assert not sample_user.is_moderator()

        # Set to MODERATOR
        sample_user.permission = Permission.MODERATOR
        await sample_user.save()
        assert sample_user.is_moderator()

        # ADMIN should also be moderator
        sample_user.permission = Permission.ADMIN
        await sample_user.save()
        assert sample_user.is_moderator()

    async def test_user_permissions_hierarchy(self, db):
        """Test permission hierarchy logic."""
        # Create users with different permission levels
        user = await User.create(
            discord_id=111111111111111111,
            discord_username="user",
            permission=Permission.USER,
        )

        moderator = await User.create(
            discord_id=222222222222222222,
            discord_username="moderator",
            permission=Permission.MODERATOR,
        )

        admin = await User.create(
            discord_id=333333333333333333,
            discord_username="admin",
            permission=Permission.ADMIN,
        )

        superadmin = await User.create(
            discord_id=444444444444444444,
            discord_username="superadmin",
            permission=Permission.SUPERADMIN,
        )

        # Verify hierarchy
        assert (
            Permission.USER
            < Permission.MODERATOR
            < Permission.ADMIN
            < Permission.SUPERADMIN
        )

        # Verify each level has appropriate permissions
        assert user.has_permission(Permission.USER)
        assert not user.has_permission(Permission.MODERATOR)

        assert moderator.has_permission(Permission.USER)
        assert moderator.has_permission(Permission.MODERATOR)
        assert not moderator.has_permission(Permission.ADMIN)

        assert admin.has_permission(Permission.USER)
        assert admin.has_permission(Permission.MODERATOR)
        assert admin.has_permission(Permission.ADMIN)
        assert not admin.has_permission(Permission.SUPERADMIN)

        assert superadmin.has_permission(Permission.USER)
        assert superadmin.has_permission(Permission.MODERATOR)
        assert superadmin.has_permission(Permission.ADMIN)
        assert superadmin.has_permission(Permission.SUPERADMIN)

    async def test_inactive_user_permissions(self, sample_user):
        """Test that inactive users don't have permissions."""
        # Active user has permissions
        assert sample_user.has_permission(Permission.USER)

        # Deactivate user
        sample_user.is_active = False
        await sample_user.save()

        # Inactive user should not have any permissions
        assert not sample_user.has_permission(Permission.USER)
        assert not sample_user.is_admin()
        assert not sample_user.is_moderator()

    async def test_get_display_name(self, sample_user):
        """Test get_display_name method."""
        # Should use discord_username when display_name not set
        assert sample_user.get_display_name() == sample_user.discord_username

        # Should use display_name when set
        sample_user.display_name = "Custom Name"
        await sample_user.save()
        assert sample_user.get_display_name() == "Custom Name"

    async def test_get_full_display_name(self, sample_user):
        """Test get_full_display_name with pronouns."""
        # Without pronouns
        assert sample_user.get_full_display_name() == sample_user.discord_username

        # With pronouns but not enabled
        sample_user.pronouns = "they/them"
        sample_user.show_pronouns = False
        await sample_user.save()
        assert sample_user.get_full_display_name() == sample_user.discord_username

        # With pronouns enabled
        sample_user.show_pronouns = True
        await sample_user.save()
        full_name = sample_user.get_full_display_name()
        assert "they/them" in full_name
        assert sample_user.discord_username in full_name

    async def test_user_str_representation(self, sample_user):
        """Test string representation of user."""
        user_str = str(sample_user)
        assert sample_user.discord_username in user_str
        assert str(sample_user.discord_id) in user_str
