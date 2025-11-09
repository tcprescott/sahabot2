"""Test match status advancement functionality."""
import pytest
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_advance_match_status(db):
    """Test advancing match status through all stages."""
    from models import User, Organization
    from models.user import Permission
    from models.match_schedule import Match, Tournament
    from application.services.tournaments.tournament_service import TournamentService
    
    # Create test data
    admin_user = await User.create(
        discord_id=999888777666555444,
        discord_username="StatusAdmin",
        permission=Permission.ADMIN
    )
    
    org = await Organization.create(name="Status Test Org")
    
    tournament = await Tournament.create(
        organization=org,
        name="Status Test Tournament",
        is_active=True
    )
    
    match = await Match.create(
        tournament=tournament,
        scheduled_at=datetime.now(timezone.utc),
        title="Status Test Match"
    )
    
    service = TournamentService()
    
    # Test each status advancement
    # 1. Checked In
    updated = await service.advance_match_status(
        user=admin_user,
        organization_id=org.id,
        match_id=match.id,
        status='checked_in'
    )
    assert updated is not None
    assert updated.checked_in_at is not None
    print(f"✓ checked_in_at: {updated.checked_in_at}")
    
    # 2. Started
    updated = await service.advance_match_status(
        user=admin_user,
        organization_id=org.id,
        match_id=match.id,
        status='started'
    )
    assert updated is not None
    assert updated.started_at is not None
    print(f"✓ started_at: {updated.started_at}")
    
    # 3. Finished
    updated = await service.advance_match_status(
        user=admin_user,
        organization_id=org.id,
        match_id=match.id,
        status='finished'
    )
    assert updated is not None
    assert updated.finished_at is not None
    print(f"✓ finished_at: {updated.finished_at}")
    
    # 4. Recorded
    updated = await service.advance_match_status(
        user=admin_user,
        organization_id=org.id,
        match_id=match.id,
        status='recorded'
    )
    assert updated is not None
    assert updated.confirmed_at is not None
    print(f"✓ confirmed_at (recorded): {updated.confirmed_at}")
    
    print("\n✅ All status advancements work correctly!")


@pytest.mark.asyncio
async def test_revert_match_status(db):
    """Test reverting match status."""
    from models import User, Organization
    from models.user import Permission
    from models.match_schedule import Match, Tournament
    from application.services.tournaments.tournament_service import TournamentService
    
    # Create test data
    admin_user = await User.create(
        discord_id=999888777666555445,
        discord_username="RevertAdmin",
        permission=Permission.ADMIN
    )
    
    org = await Organization.create(name="Revert Test Org")
    
    tournament = await Tournament.create(
        organization=org,
        name="Revert Test Tournament",
        is_active=True
    )
    
    match = await Match.create(
        tournament=tournament,
        scheduled_at=datetime.now(timezone.utc),
        title="Revert Test Match",
        racetime_room_slug=None  # No RaceTime room
    )
    
    service = TournamentService()
    
    # First advance to finished
    await service.advance_match_status(
        user=admin_user,
        organization_id=org.id,
        match_id=match.id,
        status='checked_in'
    )
    await service.advance_match_status(
        user=admin_user,
        organization_id=org.id,
        match_id=match.id,
        status='started'
    )
    await service.advance_match_status(
        user=admin_user,
        organization_id=org.id,
        match_id=match.id,
        status='finished'
    )
    
    # Verify finished
    match = await Match.get(id=match.id)
    assert match.finished_at is not None
    print(f"✓ Match finished at: {match.finished_at}")
    
    # Now revert from finished
    updated = await service.revert_match_status(
        user=admin_user,
        organization_id=org.id,
        match_id=match.id,
        status='finished'
    )
    assert updated is not None
    assert updated.finished_at is None
    assert updated.started_at is not None  # Should still be started
    print(f"✓ Reverted from finished, finished_at is now None")
    
    # Revert from started
    updated = await service.revert_match_status(
        user=admin_user,
        organization_id=org.id,
        match_id=match.id,
        status='started'
    )
    assert updated is not None
    assert updated.started_at is None
    assert updated.checked_in_at is not None  # Should still be checked in
    print(f"✓ Reverted from started, started_at is now None")
    
    # Revert from checked_in
    updated = await service.revert_match_status(
        user=admin_user,
        organization_id=org.id,
        match_id=match.id,
        status='checked_in'
    )
    assert updated is not None
    assert updated.checked_in_at is None
    print(f"✓ Reverted from checked_in, checked_in_at is now None")
    
    print("\n✅ All status reverts work correctly!")


@pytest.mark.asyncio
async def test_revert_with_racetime_room_fails(db):
    """Test that reverting fails when match has a RaceTime room."""
    from models import User, Organization
    from models.user import Permission
    from models.match_schedule import Match, Tournament
    from application.services.tournaments.tournament_service import TournamentService
    
    # Create test data
    admin_user = await User.create(
        discord_id=999888777666555446,
        discord_username="RoomTestAdmin",
        permission=Permission.ADMIN
    )
    
    org = await Organization.create(name="Room Test Org")
    
    tournament = await Tournament.create(
        organization=org,
        name="Room Test Tournament",
        is_active=True
    )
    
    match = await Match.create(
        tournament=tournament,
        scheduled_at=datetime.now(timezone.utc),
        title="Room Test Match",
        racetime_room_slug="alttpr/cool-doge-1234"  # Has RaceTime room
    )
    
    service = TournamentService()
    
    # Try to advance - should fail with ValueError
    try:
        await service.advance_match_status(
            user=admin_user,
            organization_id=org.id,
            match_id=match.id,
            status='checked_in'
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "RaceTime room" in str(e)
        print(f"✓ Correctly prevented advance: {e}")
    
    # Try to revert - should also fail with ValueError
    try:
        await service.revert_match_status(
            user=admin_user,
            organization_id=org.id,
            match_id=match.id,
            status='checked_in'
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "RaceTime room" in str(e)
        print(f"✓ Correctly prevented revert: {e}")
    
    print("\n✅ Both advance and revert correctly blocked for matches with RaceTime room!")
