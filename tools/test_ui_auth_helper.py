#!/usr/bin/env python3
"""
Test script for UI Authorization Helper.

Tests the UIAuthorizationHelper service and verifies permissions
are correctly evaluated for different roles.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_db, close_db
from models import User, Organization, OrganizationMember, OrganizationRole, OrganizationMemberRole
from application.services.ui_authorization_helper import UIAuthorizationHelper


async def test_ui_auth_helper():
    """Test UI Authorization Helper."""
    print("=" * 80)
    print("UI AUTHORIZATION HELPER TEST")
    print("=" * 80)
    
    # Initialize database
    await init_db()
    
    try:
        # Get test users and organization
        print("\n1. Loading test data...")
        
        # Get first regular organization (skip System org with id=-1)
        org = await Organization.filter(id__gt=0).first()
        if not org:
            print("❌ No organizations found. Run tools/backfill_builtin_roles.py first.")
            return
        
        print(f"   Organization: {org.name} (ID: {org.id})")
        
        # Get users (should exist from previous tests)
        admin_user = await User.filter(discord_username="TestAdmin").first()
        manager_user = await User.filter(discord_username="TestTournamentManager").first()
        member_user = await User.filter(discord_username="TestRegularMember").first()
        
        if not all([admin_user, manager_user, member_user]):
            print("❌ Test users not found. Run tools/test_tournament_service_auth.py first.")
            return
        
        print(f"   Admin User: {admin_user.discord_username}")
        print(f"   Manager User: {manager_user.discord_username}")
        print(f"   Member User: {member_user.discord_username}")
        
        # Initialize helper
        helper = UIAuthorizationHelper()
        
        print("\n2. Testing Organization Admin permissions...")
        admin_perms = await helper.get_organization_permissions(admin_user, org.id)
        print(f"   is_organization_member: {admin_perms.is_organization_member}")
        print(f"   is_organization_admin: {admin_perms.is_organization_admin}")
        print(f"   can_manage_tournaments: {admin_perms.can_manage_tournaments}")
        print(f"   can_manage_async_tournaments: {admin_perms.can_manage_async_tournaments}")
        print(f"   can_review_async_races: {admin_perms.can_review_async_races}")
        print(f"   can_manage_members: {admin_perms.can_manage_members}")
        print(f"   can_manage_organization: {admin_perms.can_manage_organization}")
        print(f"   can_manage_scheduled_tasks: {admin_perms.can_manage_scheduled_tasks}")
        print(f"   can_manage_race_room_profiles: {admin_perms.can_manage_race_room_profiles}")
        print(f"   can_manage_live_races: {admin_perms.can_manage_live_races}")
        
        # Verify admin has all permissions
        assert admin_perms.is_organization_member, "Admin should be org member"
        assert admin_perms.is_organization_admin, "Admin should be org admin"
        assert admin_perms.can_manage_tournaments, "Admin should manage tournaments"
        assert admin_perms.can_manage_members, "Admin should manage members"
        assert admin_perms.can_manage_organization, "Admin should manage org"
        print("   ✅ Admin has all permissions")
        
        print("\n3. Testing Tournament Manager permissions...")
        manager_perms = await helper.get_organization_permissions(manager_user, org.id)
        print(f"   is_organization_member: {manager_perms.is_organization_member}")
        print(f"   is_organization_admin: {manager_perms.is_organization_admin}")
        print(f"   can_manage_tournaments: {manager_perms.can_manage_tournaments}")
        print(f"   can_manage_async_tournaments: {manager_perms.can_manage_async_tournaments}")
        print(f"   can_manage_members: {manager_perms.can_manage_members}")
        print(f"   can_manage_organization: {manager_perms.can_manage_organization}")
        
        # Verify manager has tournament permissions but not admin permissions
        assert manager_perms.is_organization_member, "Manager should be org member"
        assert not manager_perms.is_organization_admin, "Manager should NOT be org admin"
        assert manager_perms.can_manage_tournaments, "Manager should manage tournaments"
        assert not manager_perms.can_manage_members, "Manager should NOT manage members"
        assert not manager_perms.can_manage_organization, "Manager should NOT manage org"
        print("   ✅ Manager has correct permissions")
        
        print("\n4. Testing Regular Member permissions...")
        member_perms = await helper.get_organization_permissions(member_user, org.id)
        print(f"   is_organization_member: {member_perms.is_organization_member}")
        print(f"   is_organization_admin: {member_perms.is_organization_admin}")
        print(f"   can_manage_tournaments: {member_perms.can_manage_tournaments}")
        print(f"   can_manage_members: {member_perms.can_manage_members}")
        print(f"   can_view_tournaments: {member_perms.can_view_tournaments}")
        print(f"   can_view_organization_settings: {member_perms.can_view_organization_settings}")
        
        # Verify member has view-only permissions
        assert member_perms.is_organization_member, "Member should be org member"
        assert not member_perms.is_organization_admin, "Member should NOT be org admin"
        assert not member_perms.can_manage_tournaments, "Member should NOT manage tournaments"
        assert not member_perms.can_manage_members, "Member should NOT manage members"
        assert member_perms.can_view_tournaments, "Member should view tournaments"
        assert member_perms.can_view_organization_settings, "Member should view org settings"
        print("   ✅ Member has correct permissions")
        
        print("\n5. Testing individual permission check methods...")
        
        # Test can_manage_tournaments
        admin_can_manage = await helper.can_manage_tournaments(admin_user, org.id)
        manager_can_manage = await helper.can_manage_tournaments(manager_user, org.id)
        member_can_manage = await helper.can_manage_tournaments(member_user, org.id)
        
        print(f"   Admin can_manage_tournaments: {admin_can_manage}")
        print(f"   Manager can_manage_tournaments: {manager_can_manage}")
        print(f"   Member can_manage_tournaments: {member_can_manage}")
        
        assert admin_can_manage, "Admin should manage tournaments"
        assert manager_can_manage, "Manager should manage tournaments"
        assert not member_can_manage, "Member should NOT manage tournaments"
        print("   ✅ Individual checks work correctly")
        
        print("\n6. Testing batch permissions check...")
        
        # Create a second org for batch test (if needed)
        org2 = await Organization.filter(name="Test Org 2").first()
        if not org2:
            org2 = await Organization.create(name="Test Org 2")
            # Add admin to org2 as a member
            member2 = await OrganizationMember.create(
                organization_id=org2.id,
                user_id=admin_user.id
            )
            # Assign Organization Admin role
            admin_role = await OrganizationRole.filter(
                organization_id=org2.id,
                name="Organization Admin",
                is_builtin=True
            ).first()
            if admin_role:
                await OrganizationMemberRole.create(
                    member_id=member2.id,
                    role_id=admin_role.id
                )
        
        batch_perms = await helper.get_multiple_organization_permissions(
            admin_user,
            [org.id, org2.id]
        )
        
        print(f"   Org {org.id} permissions: {batch_perms[org.id].is_organization_member}")
        print(f"   Org {org2.id} permissions: {batch_perms[org2.id].is_organization_member}")
        
        assert org.id in batch_perms, "Should have permissions for org 1"
        assert org2.id in batch_perms, "Should have permissions for org 2"
        print("   ✅ Batch permissions work correctly")
        
        print("\n7. Testing non-member permissions...")
        
        # Use the existing non-member user
        non_member = await User.filter(discord_username="TestNonMember").first()
        if not non_member:
            non_member = await User.create(
                discord_id=999999,
                discord_username="TestNonMember",
                discord_email="nonmember@test.com"
            )
        
        non_member_perms = await helper.get_organization_permissions(non_member, org.id)
        print(f"   is_organization_member: {non_member_perms.is_organization_member}")
        print(f"   can_manage_tournaments: {non_member_perms.can_manage_tournaments}")
        print(f"   can_view_tournaments: {non_member_perms.can_view_tournaments}")
        
        # Verify non-member has no permissions
        assert not non_member_perms.is_organization_member, "Non-member should NOT be org member"
        assert not non_member_perms.can_manage_tournaments, "Non-member should NOT manage tournaments"
        assert not non_member_perms.can_view_tournaments, "Non-member should NOT view tournaments"
        print("   ✅ Non-member has no permissions")
        
        print("\n" + "=" * 80)
        print("✅ ALL UI AUTHORIZATION HELPER TESTS PASSED")
        print("=" * 80)
        
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(test_ui_auth_helper())
