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


@pytest.mark.asyncio
async def test_sync_racetime_room_status(db):
    """Test manually syncing match status from RaceTime room."""
    from models import User, Organization
    from models.user import Permission
    from models.match_schedule import Match, Tournament
    from application.services.tournaments.tournament_service import TournamentService
    from unittest.mock import AsyncMock, patch
    
    # Create test data
    admin_user = await User.create(
        discord_id=999888777666555447,
        discord_username="SyncTestAdmin",
        permission=Permission.ADMIN
    )
    
    org = await Organization.create(name="Sync Test Org")
    
    tournament = await Tournament.create(
        organization=org,
        name="Sync Test Tournament",
        is_active=True
    )
    
    match = await Match.create(
        tournament=tournament,
        scheduled_at=datetime.now(timezone.utc),
        title="Sync Test Match",
        racetime_room_slug="alttpr/test-room-sync"  # Has RaceTime room
    )
    
    service = TournamentService()
    
    # Mock the aiohttp session to return race data
    mock_race_data = {
        'status': {'value': 'in_progress'}
    }
    
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_race_data)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_get = AsyncMock()
    mock_get.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.get = lambda url: mock_get
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Sync status from RaceTime
        result = await service.sync_racetime_room_status(
            user=admin_user,
            organization_id=org.id,
            match_id=match.id
        )
    
    assert result is not None
    assert result.checked_in_at is not None
    assert result.started_at is not None
    print(f"✓ Match synced: checked_in_at={result.checked_in_at}, started_at={result.started_at}")
    
    print("\n✅ RaceTime room status sync works correctly!")


@pytest.mark.asyncio
async def test_sync_racetime_cancelled_unlinks_room(db):
    """Test that syncing a cancelled race unlinks the RaceTime room."""
    from models import User, Organization
    from models.user import Permission
    from models.match_schedule import Match, Tournament
    from application.services.tournaments.tournament_service import TournamentService
    from unittest.mock import AsyncMock, patch
    
    # Create test data
    admin_user = await User.create(
        discord_id=999888777666555448,
        discord_username="CancelTestAdmin",
        permission=Permission.ADMIN
    )
    
    org = await Organization.create(name="Cancel Test Org")
    
    tournament = await Tournament.create(
        organization=org,
        name="Cancel Test Tournament",
        is_active=True
    )
    
    match = await Match.create(
        tournament=tournament,
        scheduled_at=datetime.now(timezone.utc),
        title="Cancel Test Match",
        racetime_room_slug="alttpr/cancelled-race"  # Has RaceTime room
    )
    
    service = TournamentService()
    
    # Mock the aiohttp session to return cancelled race data
    mock_race_data = {
        'status': {'value': 'cancelled'}
    }
    
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_race_data)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_get = AsyncMock()
    mock_get.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.get = lambda url: mock_get
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Sync status from RaceTime - race is cancelled
        result = await service.sync_racetime_room_status(
            user=admin_user,
            organization_id=org.id,
            match_id=match.id
        )
    
    assert result is not None
    assert result.racetime_room_slug is None
    print(f"✓ RaceTime room unlinked: racetime_room_slug={result.racetime_room_slug}")
    
    print("\n✅ Cancelled race correctly unlinks RaceTime room!")
