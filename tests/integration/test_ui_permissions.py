"""
Integration tests for UI permission checking.

Tests UIAuthorizationHelper and Permission enum checks across different
user types and organization roles.
"""

import pytest
from models import User, Permission, Organization, OrganizationMember, OrganizationMemberRole
from application.services.ui_authorization_helper import UIAuthorizationHelper
from application.repositories.organization_repository import OrganizationRepository
from application.repositories.user_repository import UserRepository


@pytest.mark.integration
@pytest.mark.asyncio
class TestUIPermissions:
    """Integration tests for UI permission system."""

    @pytest.fixture
    async def organization(self):
        """Create a test organization."""
        org = await Organization.create(
            name="Test Organization",
            slug="test-org"
        )
        yield org
        await org.delete()

    @pytest.fixture
    async def superadmin_user(self):
        """Create a SUPERADMIN user."""
        user = await User.create(
            discord_id=1000001,
            discord_username="superadmin_user",
            permission=Permission.SUPERADMIN
        )
        yield user
        await user.delete()

    @pytest.fixture
    async def admin_user(self):
        """Create an ADMIN user."""
        user = await User.create(
            discord_id=1000002,
            discord_username="admin_user",
            permission=Permission.ADMIN
        )
        yield user
        await user.delete()

    @pytest.fixture
    async def moderator_user(self):
        """Create a MODERATOR user."""
        user = await User.create(
            discord_id=1000003,
            discord_username="moderator_user",
            permission=Permission.MODERATOR
        )
        yield user
        await user.delete()

    @pytest.fixture
    async def regular_user(self):
        """Create a regular USER."""
        user = await User.create(
            discord_id=1000004,
            discord_username="regular_user",
            permission=Permission.USER
        )
        yield user
        await user.delete()

    @pytest.fixture
    async def org_admin_user(self, organization):
        """Create a user with ADMIN role in organization."""
        user = await User.create(
            discord_id=1000005,
            discord_username="org_admin_user",
            permission=Permission.USER
        )
        
        # Add to organization
        member = await OrganizationMember.create(
            organization=organization,
            user=user
        )
        
        # Grant ADMIN permission
        await OrganizationMemberRole.create(
            member=member,
            permission_name='ADMIN'
        )
        
        yield user
        await member.delete()
        await user.delete()

    @pytest.fixture
    async def org_tournament_manager(self, organization):
        """Create a user with TOURNAMENT_MANAGER role in organization."""
        user = await User.create(
            discord_id=1000006,
            discord_username="tournament_manager",
            permission=Permission.USER
        )
        
        # Add to organization
        member = await OrganizationMember.create(
            organization=organization,
            user=user
        )
        
        # Grant TOURNAMENT_MANAGER permission
        await OrganizationMemberRole.create(
            member=member,
            permission_name='TOURNAMENT_MANAGER'
        )
        
        yield user
        await member.delete()
        await user.delete()

    @pytest.fixture
    async def org_member_user(self, organization):
        """Create a user who is just a member (no special roles)."""
        user = await User.create(
            discord_id=1000007,
            discord_username="org_member_user",
            permission=Permission.USER
        )
        
        # Add to organization with no special roles
        member = await OrganizationMember.create(
            organization=organization,
            user=user
        )
        
        yield user
        await member.delete()
        await user.delete()

    @pytest.fixture
    def ui_auth(self):
        """Create UIAuthorizationHelper instance."""
        return UIAuthorizationHelper()

    # ==================== Global Permission Tests ====================

    async def test_superadmin_has_all_global_permissions(self, superadmin_user):
        """SUPERADMIN should have all global permissions."""
        assert superadmin_user.has_permission(Permission.SUPERADMIN)
        assert superadmin_user.has_permission(Permission.ADMIN)
        assert superadmin_user.has_permission(Permission.MODERATOR)
        assert superadmin_user.has_permission(Permission.USER)

    async def test_admin_has_admin_and_below(self, admin_user):
        """ADMIN should have admin and below permissions."""
        assert not admin_user.has_permission(Permission.SUPERADMIN)
        assert admin_user.has_permission(Permission.ADMIN)
        assert admin_user.has_permission(Permission.MODERATOR)
        assert admin_user.has_permission(Permission.USER)

    async def test_moderator_has_moderator_and_below(self, moderator_user):
        """MODERATOR should have moderator and below permissions."""
        assert not moderator_user.has_permission(Permission.SUPERADMIN)
        assert not moderator_user.has_permission(Permission.ADMIN)
        assert moderator_user.has_permission(Permission.MODERATOR)
        assert moderator_user.has_permission(Permission.USER)

    async def test_regular_user_has_only_user_permission(self, regular_user):
        """Regular USER should only have user permission."""
        assert not regular_user.has_permission(Permission.SUPERADMIN)
        assert not regular_user.has_permission(Permission.ADMIN)
        assert not regular_user.has_permission(Permission.MODERATOR)
        assert regular_user.has_permission(Permission.USER)

    # ==================== Organization Management Tests ====================

    async def test_superadmin_can_manage_any_organization(
        self, ui_auth, superadmin_user, organization
    ):
        """SUPERADMIN can manage any organization."""
        can_manage = await ui_auth.can_manage_organization(
            superadmin_user,
            organization.id
        )
        assert can_manage is True

    async def test_org_admin_can_manage_their_organization(
        self, ui_auth, org_admin_user, organization
    ):
        """Organization admin can manage their organization."""
        can_manage = await ui_auth.can_manage_organization(
            org_admin_user,
            organization.id
        )
        assert can_manage is True

    async def test_regular_member_cannot_manage_organization(
        self, ui_auth, org_member_user, organization
    ):
        """Regular member cannot manage organization."""
        can_manage = await ui_auth.can_manage_organization(
            org_member_user,
            organization.id
        )
        assert can_manage is False

    async def test_non_member_cannot_manage_organization(
        self, ui_auth, regular_user, organization
    ):
        """Non-member cannot manage organization."""
        can_manage = await ui_auth.can_manage_organization(
            regular_user,
            organization.id
        )
        assert can_manage is False

    # ==================== Member Management Tests ====================

    async def test_superadmin_can_manage_members_in_any_org(
        self, ui_auth, superadmin_user, organization
    ):
        """SUPERADMIN can manage members in any organization."""
        can_manage = await ui_auth.can_manage_members(
            superadmin_user,
            organization.id
        )
        assert can_manage is True

    async def test_org_admin_can_manage_members(
        self, ui_auth, org_admin_user, organization
    ):
        """Organization admin can manage members."""
        can_manage = await ui_auth.can_manage_members(
            org_admin_user,
            organization.id
        )
        assert can_manage is True

    async def test_regular_member_cannot_manage_members(
        self, ui_auth, org_member_user, organization
    ):
        """Regular member cannot manage members."""
        can_manage = await ui_auth.can_manage_members(
            org_member_user,
            organization.id
        )
        assert can_manage is False

    # ==================== Tournament Management Tests ====================

    async def test_superadmin_can_manage_tournaments_in_any_org(
        self, ui_auth, superadmin_user, organization
    ):
        """SUPERADMIN can manage tournaments in any organization."""
        can_manage = await ui_auth.can_manage_tournaments(
            superadmin_user,
            organization.id
        )
        assert can_manage is True

    async def test_org_admin_can_manage_tournaments(
        self, ui_auth, org_admin_user, organization
    ):
        """Organization admin can manage tournaments."""
        can_manage = await ui_auth.can_manage_tournaments(
            org_admin_user,
            organization.id
        )
        assert can_manage is True

    async def test_tournament_manager_can_manage_tournaments(
        self, ui_auth, org_tournament_manager, organization
    ):
        """Tournament manager can manage tournaments."""
        can_manage = await ui_auth.can_manage_tournaments(
            org_tournament_manager,
            organization.id
        )
        assert can_manage is True

    async def test_regular_member_cannot_manage_tournaments(
        self, ui_auth, org_member_user, organization
    ):
        """Regular member cannot manage tournaments."""
        can_manage = await ui_auth.can_manage_tournaments(
            org_member_user,
            organization.id
        )
        assert can_manage is False

    async def test_non_member_cannot_manage_tournaments(
        self, ui_auth, regular_user, organization
    ):
        """Non-member cannot manage tournaments."""
        can_manage = await ui_auth.can_manage_tournaments(
            regular_user,
            organization.id
        )
        assert can_manage is False

    # ==================== Async Tournament Management Tests ====================

    async def test_superadmin_can_manage_async_tournaments(
        self, ui_auth, superadmin_user, organization
    ):
        """SUPERADMIN can manage async tournaments in any organization."""
        can_manage = await ui_auth.can_manage_async_tournaments(
            superadmin_user,
            organization.id
        )
        assert can_manage is True

    async def test_org_admin_can_manage_async_tournaments(
        self, ui_auth, org_admin_user, organization
    ):
        """Organization admin can manage async tournaments."""
        can_manage = await ui_auth.can_manage_async_tournaments(
            org_admin_user,
            organization.id
        )
        assert can_manage is True

    async def test_tournament_manager_can_manage_async_tournaments(
        self, ui_auth, org_tournament_manager, organization
    ):
        """Tournament manager can manage async tournaments."""
        can_manage = await ui_auth.can_manage_async_tournaments(
            org_tournament_manager,
            organization.id
        )
        assert can_manage is True

    # ==================== Race Review Tests ====================

    async def test_superadmin_can_review_async_races(
        self, ui_auth, superadmin_user, organization
    ):
        """SUPERADMIN can review async races in any organization."""
        can_review = await ui_auth.can_review_async_races(
            superadmin_user,
            organization.id
        )
        assert can_review is True

    async def test_org_admin_can_review_async_races(
        self, ui_auth, org_admin_user, organization
    ):
        """Organization admin can review async races."""
        can_review = await ui_auth.can_review_async_races(
            org_admin_user,
            organization.id
        )
        assert can_review is True

    # ==================== Scheduled Tasks Tests ====================

    async def test_superadmin_can_manage_scheduled_tasks(
        self, ui_auth, superadmin_user, organization
    ):
        """SUPERADMIN can manage scheduled tasks in any organization."""
        can_manage = await ui_auth.can_manage_scheduled_tasks(
            superadmin_user,
            organization.id
        )
        assert can_manage is True

    async def test_org_admin_can_manage_scheduled_tasks(
        self, ui_auth, org_admin_user, organization
    ):
        """Organization admin can manage scheduled tasks."""
        can_manage = await ui_auth.can_manage_scheduled_tasks(
            org_admin_user,
            organization.id
        )
        assert can_manage is True

    async def test_regular_member_cannot_manage_scheduled_tasks(
        self, ui_auth, org_member_user, organization
    ):
        """Regular member cannot manage scheduled tasks."""
        can_manage = await ui_auth.can_manage_scheduled_tasks(
            org_member_user,
            organization.id
        )
        assert can_manage is False

    # ==================== RaceTime Profile Tests ====================

    async def test_superadmin_can_manage_race_room_profiles(
        self, ui_auth, superadmin_user, organization
    ):
        """SUPERADMIN can manage race room profiles in any organization."""
        can_manage = await ui_auth.can_manage_race_room_profiles(
            superadmin_user,
            organization.id
        )
        assert can_manage is True

    async def test_org_admin_can_manage_race_room_profiles(
        self, ui_auth, org_admin_user, organization
    ):
        """Organization admin can manage race room profiles."""
        can_manage = await ui_auth.can_manage_race_room_profiles(
            org_admin_user,
            organization.id
        )
        assert can_manage is True

    # ==================== Live Race Tests ====================

    async def test_superadmin_can_manage_live_races(
        self, ui_auth, superadmin_user, organization
    ):
        """SUPERADMIN can manage live races in any organization."""
        can_manage = await ui_auth.can_manage_live_races(
            superadmin_user,
            organization.id
        )
        assert can_manage is True

    async def test_org_admin_can_manage_live_races(
        self, ui_auth, org_admin_user, organization
    ):
        """Organization admin can manage live races."""
        can_manage = await ui_auth.can_manage_live_races(
            org_admin_user,
            organization.id
        )
        assert can_manage is True

    # ==================== Graceful Degradation Tests ====================

    async def test_null_user_returns_false(self, ui_auth, organization):
        """Null user should return False for all permission checks."""
        can_manage_org = await ui_auth.can_manage_organization(None, organization.id)
        can_manage_members = await ui_auth.can_manage_members(None, organization.id)
        can_manage_tournaments = await ui_auth.can_manage_tournaments(None, organization.id)
        
        assert can_manage_org is False
        assert can_manage_members is False
        assert can_manage_tournaments is False

    async def test_invalid_organization_returns_false(self, ui_auth, regular_user):
        """Invalid organization ID should return False."""
        invalid_org_id = 999999
        
        can_manage = await ui_auth.can_manage_organization(regular_user, invalid_org_id)
        assert can_manage is False

    # ==================== Permission Hierarchy Tests ====================

    async def test_permission_hierarchy_ordering(self):
        """Test that permission hierarchy is correctly ordered."""
        # SUPERADMIN > ADMIN > MODERATOR > USER
        assert Permission.SUPERADMIN > Permission.ADMIN
        assert Permission.ADMIN > Permission.MODERATOR
        assert Permission.MODERATOR > Permission.USER
        
        # Test transitivity
        assert Permission.SUPERADMIN > Permission.USER

    async def test_has_permission_respects_hierarchy(self, admin_user):
        """has_permission() should respect permission hierarchy."""
        # Admin has admin and below
        assert admin_user.has_permission(Permission.ADMIN)
        assert admin_user.has_permission(Permission.MODERATOR)
        assert admin_user.has_permission(Permission.USER)
        
        # But not higher
        assert not admin_user.has_permission(Permission.SUPERADMIN)

    # ==================== Multiple Organization Tests ====================

    async def test_user_permissions_scoped_to_organization(
        self, ui_auth, org_admin_user, organization
    ):
        """User with admin in one org shouldn't have admin in another."""
        # Create second organization
        org2 = await Organization.create(
            name="Other Organization",
            slug="other-org"
        )
        
        try:
            # User is admin in organization
            can_manage_org1 = await ui_auth.can_manage_organization(
                org_admin_user,
                organization.id
            )
            assert can_manage_org1 is True
            
            # But not in org2 (not a member)
            can_manage_org2 = await ui_auth.can_manage_organization(
                org_admin_user,
                org2.id
            )
            assert can_manage_org2 is False
        finally:
            await org2.delete()

    # ==================== Combined Permission Tests ====================

    async def test_global_admin_overrides_org_permissions(
        self, ui_auth, admin_user, organization
    ):
        """Global ADMIN should have permissions even without org membership."""
        # Admin user is not a member of organization
        can_manage = await ui_auth.can_manage_organization(
            admin_user,
            organization.id
        )
        # Global admin has access regardless
        assert can_manage is True

    async def test_regular_user_needs_org_role(
        self, ui_auth, regular_user, org_member_user, organization
    ):
        """Regular users need org role for permissions, unlike global admins."""
        # Regular user (not member) - no access
        can_manage_non_member = await ui_auth.can_manage_tournaments(
            regular_user,
            organization.id
        )
        assert can_manage_non_member is False
        
        # Regular user (member but no role) - no access
        can_manage_member = await ui_auth.can_manage_tournaments(
            org_member_user,
            organization.id
        )
        assert can_manage_member is False
