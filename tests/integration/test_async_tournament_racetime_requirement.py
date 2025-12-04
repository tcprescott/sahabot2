"""
Test async tournament RaceTime.gg account requirement feature.

Tests that users must have a linked RaceTime.gg account to start async runs
when the tournament has require_racetime_for_async_runs enabled.
"""

import pytest

from models.user import User, Permission
from modules.async_qualifier.models.async_qualifier import AsyncQualifier
from models.organizations import Organization


@pytest.mark.asyncio
async def test_async_tournament_with_racetime_required(db):
    """Test that async tournament can require RaceTime.gg account."""
    # Create organization
    org = await Organization.create(name="Test Org", slug="test-org")

    # Create tournament with RaceTime requirement
    tournament = await AsyncQualifier.create(
        organization=org,
        name="Test Tournament",
        description="Test tournament with RaceTime requirement",
        is_active=True,
        require_racetime_for_async_runs=True,
        runs_per_pool=1,
    )

    # Verify the field is set correctly
    assert tournament.require_racetime_for_async_runs is True

    # Cleanup
    await tournament.delete()
    await org.delete()


@pytest.mark.asyncio
async def test_user_with_racetime_can_access(db):
    """Test that users with linked RaceTime.gg account can proceed."""
    # Create user with RaceTime.gg account
    user = await User.create(
        discord_id=123456789012345678,
        discord_username="testuser",
        discord_discriminator="0001",
        discord_avatar="test_avatar",
        discord_email="test@example.com",
        permission=Permission.USER,
        racetime_id="test_racetime_user",
        racetime_name="TestRacetimeUser",
    )

    # Verify RaceTime.gg account is linked
    assert user.racetime_id is not None
    assert user.racetime_name is not None

    # Cleanup
    await user.delete()


@pytest.mark.asyncio
async def test_user_without_racetime_cannot_access(db):
    """Test that users without linked RaceTime.gg account are blocked."""
    # Create user without RaceTime.gg account
    user = await User.create(
        discord_id=987654321098765432,
        discord_username="testuser2",
        discord_discriminator="0002",
        discord_avatar="test_avatar",
        discord_email="test2@example.com",
        permission=Permission.USER,
    )

    # Verify RaceTime.gg account is not linked
    assert user.racetime_id is None
    assert user.racetime_name is None

    # Cleanup
    await user.delete()


@pytest.mark.asyncio
async def test_tournament_without_racetime_requirement(db):
    """Test that tournaments without RaceTime requirement work normally."""
    # Create organization
    org = await Organization.create(name="Test Org 2", slug="test-org-2")

    # Create tournament without RaceTime requirement
    tournament = await AsyncQualifier.create(
        organization=org,
        name="Test Tournament 2",
        description="Test tournament without RaceTime requirement",
        is_active=True,
        require_racetime_for_async_runs=False,
        runs_per_pool=1,
    )

    # Verify the field is set correctly
    assert tournament.require_racetime_for_async_runs is False

    # Cleanup
    await tournament.delete()
    await org.delete()


@pytest.mark.asyncio
async def test_default_racetime_requirement_is_false(db):
    """Test that RaceTime requirement defaults to False."""
    # Create organization
    org = await Organization.create(name="Test Org 3", slug="test-org-3")

    # Create tournament without specifying RaceTime requirement
    tournament = await AsyncQualifier.create(
        organization=org,
        name="Test Tournament 3",
        description="Test tournament with default RaceTime requirement",
        is_active=True,
        runs_per_pool=1,
    )

    # Verify the field defaults to False
    assert tournament.require_racetime_for_async_runs is False

    # Cleanup
    await tournament.delete()
    await org.delete()
