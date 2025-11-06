#!/usr/bin/env python3
"""
Integration test for TournamentService with new authorization system.

Tests:
- Admin role can create/update/delete tournaments
- Tournament Manager role can create/update/delete tournaments
- Regular member without roles cannot manage tournaments
- Non-members cannot access tournaments

Run with: poetry run python tools/test_tournament_service_auth.py
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise

from config import settings
from models import User, Permission
from models.organizations import Organization, OrganizationMember
from models.authorization import OrganizationRole, OrganizationMemberRole
from application.services.tournaments.tournament_service import TournamentService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def init_db():
    """Initialize database connection."""
    from config import settings
    from migrations.tortoise_config import get_model_modules
    
    await Tortoise.init(
        db_url=settings.database_url,
        modules={'models': get_model_modules()},
        use_tz=True,
        timezone='UTC'
    )


async def close_db():
    """Close database connection."""
    await Tortoise.close_connections()


async def get_or_create_test_org():
    """Get or create a test organization."""
    # Just use the first existing organization for testing
    org = await Organization.filter(id__gt=0).first()  # Skip System org (id=-1)
    if not org:
        raise RuntimeError("No organizations found in database - please create one first")
    
    logger.info("Using existing test organization: %s (id=%s)", org.name, org.id)
    return org


async def create_test_users(org: Organization):
    """Create test users with different roles."""
    users = {}
    
    # 1. Admin role user (via built-in Admin role)
    admin_user = await User.filter(discord_id=111111111).first()
    if not admin_user:
        admin_user = await User.create(
            discord_id=111111111,
            discord_username="TestAdmin",
            discord_email="admin@example.com",
            permission=Permission.USER
        )
        # Add to org
        await OrganizationMember.create(user=admin_user, organization=org)
        # Assign Admin built-in role
        admin_role = await OrganizationRole.filter(
            organization=org,
            name="Admin",
            is_builtin=True
        ).first()
        if admin_role:
            await OrganizationMemberRole.create(
                member=await OrganizationMember.filter(user=admin_user, organization=org).first(),
                role=admin_role
            )
            logger.info("Created admin user with Admin role")
    users['admin'] = admin_user
    
    # 2. Tournament Manager role user
    manager_user = await User.filter(discord_id=222222222).first()
    if not manager_user:
        manager_user = await User.create(
            discord_id=222222222,
            discord_username="TestTournamentManager",
            discord_email="manager@example.com",
            permission=Permission.USER
        )
        # Add to org
        await OrganizationMember.create(user=manager_user, organization=org)
        # Assign Tournament Manager built-in role
        manager_role = await OrganizationRole.filter(
            organization=org,
            name="Tournament Manager",
            is_builtin=True
        ).first()
        if manager_role:
            await OrganizationMemberRole.create(
                member=await OrganizationMember.filter(user=manager_user, organization=org).first(),
                role=manager_role
            )
            logger.info("Created tournament manager user with Tournament Manager role")
    users['manager'] = manager_user
    
    # 3. Regular member (no roles)
    member_user = await User.filter(discord_id=333333333).first()
    if not member_user:
        member_user = await User.create(
            discord_id=333333333,
            discord_username="TestRegularMember",
            discord_email="member@example.com",
            permission=Permission.USER
        )
        # Add to org but no roles
        await OrganizationMember.create(user=member_user, organization=org)
        logger.info("Created regular member user (no roles)")
    users['member'] = member_user
    
    # 4. Non-member
    nonmember_user = await User.filter(discord_id=444444444).first()
    if not nonmember_user:
        nonmember_user = await User.create(
            discord_id=444444444,
            discord_username="TestNonMember",
            discord_email="nonmember@example.com",
            permission=Permission.USER
        )
        logger.info("Created non-member user")
    users['nonmember'] = nonmember_user
    
    return users


async def test_create_tournament(service: TournamentService, org: Organization, users: dict):
    """Test tournament creation with different user roles."""
    logger.info("\n=== Testing Tournament Creation ===")
    
    # Admin should be able to create
    logger.info("Testing admin user can create tournament...")
    tournament = await service.create_tournament(
        user=users['admin'],
        organization_id=org.id,
        name="Test Tournament Admin",
        description="Created by admin",
        is_active=True
    )
    if tournament:
        logger.info("✓ Admin successfully created tournament (id=%s)", tournament.id)
        users['admin_tournament'] = tournament
    else:
        logger.error("✗ Admin failed to create tournament")
    
    # Tournament Manager should be able to create
    logger.info("Testing tournament manager can create tournament...")
    tournament = await service.create_tournament(
        user=users['manager'],
        organization_id=org.id,
        name="Test Tournament Manager",
        description="Created by tournament manager",
        is_active=True
    )
    if tournament:
        logger.info("✓ Tournament Manager successfully created tournament (id=%s)", tournament.id)
        users['manager_tournament'] = tournament
    else:
        logger.error("✗ Tournament Manager failed to create tournament")
    
    # Regular member should NOT be able to create
    logger.info("Testing regular member CANNOT create tournament...")
    tournament = await service.create_tournament(
        user=users['member'],
        organization_id=org.id,
        name="Test Tournament Member",
        description="Should fail",
        is_active=True
    )
    if tournament is None:
        logger.info("✓ Regular member correctly denied")
    else:
        logger.error("✗ Regular member incorrectly allowed (id=%s)", tournament.id)
    
    # Non-member should NOT be able to create
    logger.info("Testing non-member CANNOT create tournament...")
    tournament = await service.create_tournament(
        user=users['nonmember'],
        organization_id=org.id,
        name="Test Tournament NonMember",
        description="Should fail",
        is_active=True
    )
    if tournament is None:
        logger.info("✓ Non-member correctly denied")
    else:
        logger.error("✗ Non-member incorrectly allowed (id=%s)", tournament.id)


async def test_update_tournament(service: TournamentService, org: Organization, users: dict):
    """Test tournament update with different user roles."""
    logger.info("\n=== Testing Tournament Update ===")
    
    if 'admin_tournament' not in users:
        logger.warning("Skipping update tests - no tournaments created")
        return
    
    tournament = users['admin_tournament']
    
    # Admin should be able to update
    logger.info("Testing admin user can update tournament...")
    updated = await service.update_tournament(
        user=users['admin'],
        organization_id=org.id,
        tournament_id=tournament.id,
        description="Updated by admin"
    )
    if updated:
        logger.info("✓ Admin successfully updated tournament")
    else:
        logger.error("✗ Admin failed to update tournament")
    
    # Tournament Manager should be able to update
    logger.info("Testing tournament manager can update tournament...")
    updated = await service.update_tournament(
        user=users['manager'],
        organization_id=org.id,
        tournament_id=tournament.id,
        description="Updated by manager"
    )
    if updated:
        logger.info("✓ Tournament Manager successfully updated tournament")
    else:
        logger.error("✗ Tournament Manager failed to update tournament")
    
    # Regular member should NOT be able to update
    logger.info("Testing regular member CANNOT update tournament...")
    updated = await service.update_tournament(
        user=users['member'],
        organization_id=org.id,
        tournament_id=tournament.id,
        description="Should fail"
    )
    if updated is None:
        logger.info("✓ Regular member correctly denied")
    else:
        logger.error("✗ Regular member incorrectly allowed")


async def test_list_tournaments(service: TournamentService, org: Organization, users: dict):
    """Test tournament listing with different user roles."""
    logger.info("\n=== Testing Tournament Listing ===")
    
    # Admin should be able to list
    logger.info("Testing admin user can list tournaments...")
    tournaments = await service.list_org_tournaments(users['admin'], org.id)
    logger.info("✓ Admin listed %s tournaments", len(tournaments))
    
    # Tournament Manager should be able to list
    logger.info("Testing tournament manager can list tournaments...")
    tournaments = await service.list_org_tournaments(users['manager'], org.id)
    logger.info("✓ Tournament Manager listed %s tournaments", len(tournaments))
    
    # Regular member should NOT be able to list (unless we change policy)
    logger.info("Testing regular member CANNOT list tournaments...")
    tournaments = await service.list_org_tournaments(users['member'], org.id)
    if len(tournaments) == 0:
        logger.info("✓ Regular member correctly denied (empty list)")
    else:
        logger.warning("Regular member listed %s tournaments (might be expected based on policy)", len(tournaments))
    
    # Non-member should NOT be able to list
    logger.info("Testing non-member CANNOT list tournaments...")
    tournaments = await service.list_org_tournaments(users['nonmember'], org.id)
    if len(tournaments) == 0:
        logger.info("✓ Non-member correctly denied (empty list)")
    else:
        logger.error("✗ Non-member incorrectly allowed to list %s tournaments", len(tournaments))


async def test_delete_tournament(service: TournamentService, org: Organization, users: dict):
    """Test tournament deletion with different user roles."""
    logger.info("\n=== Testing Tournament Deletion ===")
    
    if 'manager_tournament' not in users:
        logger.warning("Skipping delete tests - no tournaments created by manager")
        return
    
    tournament = users['manager_tournament']
    
    # Regular member should NOT be able to delete
    logger.info("Testing regular member CANNOT delete tournament...")
    deleted = await service.delete_tournament(users['member'], org.id, tournament.id)
    if not deleted:
        logger.info("✓ Regular member correctly denied")
    else:
        logger.error("✗ Regular member incorrectly allowed to delete")
    
    # Admin should be able to delete
    logger.info("Testing admin user can delete tournament...")
    deleted = await service.delete_tournament(users['admin'], org.id, tournament.id)
    if deleted:
        logger.info("✓ Admin successfully deleted tournament")
    else:
        logger.error("✗ Admin failed to delete tournament")


async def main():
    """Run all tests."""
    await init_db()
    
    try:
        logger.info("Starting TournamentService authorization integration tests...")
        
        # Setup
        org = await get_or_create_test_org()
        users = await create_test_users(org)
        service = TournamentService()
        
        # Run tests
        await test_create_tournament(service, org, users)
        await test_update_tournament(service, org, users)
        await test_list_tournaments(service, org, users)
        await test_delete_tournament(service, org, users)
        
        logger.info("\n=== All Tests Complete ===")
        
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
