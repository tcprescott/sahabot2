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
