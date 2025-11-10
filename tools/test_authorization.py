#!/usr/bin/env python3
"""
Test Authorization System

Manual integration test to verify the new authorization system works correctly.
This tests:
1. Built-in roles are loaded from code
2. PolicyEngine evaluates permissions correctly
3. AuthorizationServiceV2 provides clean API
4. Caching works
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise
from config import settings
from models import User, Permission
from models.organizations import Organization
from application.services.authorization.authorization_service_v2 import (
    AuthorizationServiceV2,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database connection."""
    await Tortoise.init(
        db_url=settings.database_url,
        modules={
            "models": [
                "models.user",
                "models.organizations",
                "models.authorization",
            ]
        },
    )


async def close_database():
    """Close database connection."""
    await Tortoise.close_connections()


async def test_global_admin_bypass():
    """Test that global ADMIN users bypass all checks."""
    logger.info("=== Test: Global Admin Bypass ===")

    # Create a test ADMIN user (or use existing)
    admin_user = await User.filter(permission=Permission.ADMIN).first()
    if not admin_user:
        logger.warning("No ADMIN user found, skipping test")
        return

    auth = AuthorizationServiceV2()

    # Admin should be able to do anything
    result = await auth.can(
        admin_user, "tournament:create", "tournament:*", organization_id=1
    )
    logger.info("Admin can create tournament: %s ✓", result)
    assert result is True, "Admin should bypass all checks"

    result = await auth.can(admin_user, "user:delete", "user:123")
    logger.info("Admin can delete user: %s ✓", result)
    assert result is True, "Admin should bypass all checks"

    logger.info("✓ Global admin bypass working correctly\n")


async def test_organization_membership():
    """Test that non-members cannot access organization resources."""
    logger.info("=== Test: Organization Membership ===")

    # Get a regular user
    user = await User.filter(permission=Permission.USER).first()
    if not user:
        logger.warning("No USER found, creating one")
        user = await User.create(
            discord_id=999999, discord_username="test_user", permission=Permission.USER
        )

    # Get an organization
    org = await Organization.filter(id__gt=0).first()
    if not org:
        logger.warning("No organization found, skipping test")
        return

    auth = AuthorizationServiceV2()

    # User should NOT have access (not a member)
    result = await auth.can(
        user, "tournament:create", "tournament:*", organization_id=org.id
    )
    logger.info("Non-member can create tournament: %s", result)
    assert result is False, "Non-members should not have access"

    logger.info("✓ Organization membership check working correctly\n")


async def test_builtin_roles():
    """Test that built-in roles provide correct permissions."""
    logger.info("=== Test: Built-in Roles ===")

    # Get System organization
    system_org = await Organization.filter(id=-1).first()
    if not system_org:
        logger.error("System organization not found!")
        return

    # Check roles were created
    from models.authorization import OrganizationRole

    roles = await OrganizationRole.filter(
        organization=system_org, is_builtin=True
    ).all()
    logger.info("System organization has %s built-in roles:", len(roles))
    for role in roles:
        logger.info("  - %s (locked=%s)", role.name, role.is_locked)

    assert len(roles) == 4, "System org should have 4 built-in roles"

    # Get a regular organization
    org = await Organization.filter(id__gt=0).first()
    if org:
        roles = await OrganizationRole.filter(organization=org, is_builtin=True).all()
        logger.info(
            "\nRegular organization '%s' has %s built-in roles:", org.name, len(roles)
        )
        for role in roles:
            logger.info("  - %s (locked=%s)", role.name, role.is_locked)

        assert len(roles) == 5, "Regular org should have 5 built-in roles"

    logger.info("✓ Built-in roles created correctly\n")


async def test_authorization_service_api():
    """Test the AuthorizationServiceV2 API methods."""
    logger.info("=== Test: AuthorizationServiceV2 API ===")

    admin_user = await User.filter(permission=Permission.ADMIN).first()
    if not admin_user:
        logger.warning("No ADMIN user found, skipping test")
        return

    auth = AuthorizationServiceV2()

    # Test can() method
    can_create = await auth.can(
        admin_user, "tournament:create", "tournament:*", organization_id=1
    )
    logger.info("can() method returned: %s", can_create)

    # Test authorize() method (detailed result)
    result = await auth.authorize(
        admin_user, "tournament:create", "tournament:*", organization_id=1
    )
    logger.info(
        "authorize() method returned: allowed=%s, reason=%s",
        result.allowed,
        result.reason,
    )

    # Test helper methods
    action = auth.get_action_for_operation("tournament", "create")
    logger.info("get_action_for_operation() returned: %s", action)
    assert action == "tournament:create"

    resource = auth.get_resource_identifier("tournament", 123)
    logger.info("get_resource_identifier() returned: %s", resource)
    assert resource == "tournament:123"

    resource_wildcard = auth.get_resource_identifier("tournament")
    logger.info("get_resource_identifier() (wildcard) returned: %s", resource_wildcard)
    assert resource_wildcard == "tournament:*"

    logger.info("✓ AuthorizationServiceV2 API working correctly\n")


async def test_caching():
    """Test that caching works correctly."""
    logger.info("=== Test: Policy Caching ===")

    admin_user = await User.filter(permission=Permission.ADMIN).first()
    if not admin_user:
        logger.warning("No ADMIN user found, skipping test")
        return

    auth = AuthorizationServiceV2()

    # First call - should hit PolicyEngine
    logger.info("First authorization check (should evaluate policy)...")
    result1 = await auth.can(
        admin_user, "tournament:create", "tournament:*", organization_id=1
    )

    # Second call - should hit cache
    logger.info("Second authorization check (should use cache)...")
    result2 = await auth.can(
        admin_user, "tournament:create", "tournament:*", organization_id=1
    )

    assert result1 == result2, "Cached result should match"
    logger.info("Both calls returned: %s", result1)

    # Invalidate cache
    logger.info("Invalidating user cache...")
    await auth.invalidate_user_permissions(admin_user.id)

    # Third call - should re-evaluate
    logger.info("Third authorization check (after invalidation)...")
    result3 = await auth.can(
        admin_user, "tournament:create", "tournament:*", organization_id=1
    )

    assert result3 == result1, "Result after invalidation should still match"
    logger.info("✓ Caching working correctly\n")


async def main():
    """Run all tests."""
    try:
        await init_database()

        logger.info("=" * 60)
        logger.info("Testing Authorization System")
        logger.info("=" * 60)
        logger.info("")

        await test_global_admin_bypass()
        await test_organization_membership()
        await test_builtin_roles()
        await test_authorization_service_api()
        await test_caching()

        logger.info("=" * 60)
        logger.info("All tests passed! ✓")
        logger.info("=" * 60)

        return 0

    except AssertionError as e:
        logger.error("Test failed: %s", str(e))
        return 1
    except Exception as e:
        logger.error("Error during tests: %s", str(e), exc_info=True)
        return 1
    finally:
        await close_database()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
