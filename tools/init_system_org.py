#!/usr/bin/env python3
"""
Initialize System Organization

This script creates the System organization (id=-1) with its built-in roles.
The System organization is used for platform-wide permission delegation.

Run this once during initial deployment or when setting up a new environment.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path so we can import from main codebase
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise

from config import settings
from models.organizations import Organization
from models.authorization import OrganizationRole
from application.services.organizations.organization_service import OrganizationService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

SYSTEM_ORG_ID = -1
SYSTEM_ORG_NAME = "System"


async def init_database():
    """Initialize database connection."""
    logger.info("Initializing database connection...")
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
    logger.info("Database connection initialized")


async def close_database():
    """Close database connection."""
    logger.info("Closing database connections...")
    await Tortoise.close_connections()
    logger.info("Database connections closed")


async def create_system_organization():
    """Create the System organization if it doesn't exist."""
    logger.info("Checking if System organization exists...")

    # Check if System org already exists
    existing = await Organization.filter(id=SYSTEM_ORG_ID).first()
    if existing:
        logger.info(
            "System organization already exists (id=%s, name=%s)",
            existing.id,
            existing.name,
        )
        return existing

    # Create System organization
    logger.info("Creating System organization with id=%s...", SYSTEM_ORG_ID)
    system_org = await Organization.create(
        id=SYSTEM_ORG_ID,
        name=SYSTEM_ORG_NAME,
        description="Platform-wide system organization for permission delegation",
        is_active=True,
    )
    logger.info(
        "System organization created: id=%s, name=%s", system_org.id, system_org.name
    )
    return system_org


async def create_builtin_roles(organization: Organization):
    """
    Create built-in roles for the given organization using OrganizationService.

    Args:
        organization: Organization to create roles for
    """
    logger.info(
        "Creating built-in roles for organization %s (id=%s)...",
        organization.name,
        organization.id,
    )

    # Use OrganizationService to create built-in roles
    org_service = OrganizationService()
    created_roles = await org_service.create_builtin_roles(organization)

    logger.info("Built-in roles creation complete: %s created", len(created_roles))


async def verify_system_setup():
    """Verify that System organization and roles are correctly set up."""
    logger.info("Verifying System organization setup...")

    # Verify organization exists
    system_org = await Organization.filter(id=SYSTEM_ORG_ID).first()
    if not system_org:
        logger.error("System organization not found!")
        return False

    logger.info(
        "✓ System organization exists (id=%s, name=%s)", system_org.id, system_org.name
    )

    # Verify built-in roles exist
    roles = await OrganizationRole.filter(
        organization=system_org, is_builtin=True
    ).all()
    role_names = [r.name for r in roles]

    expected_roles = {
        "User Manager",
        "Organization Manager",
        "Analytics Viewer",
        "Platform Moderator",
    }
    found_roles = set(role_names)

    missing_roles = expected_roles - found_roles
    if missing_roles:
        logger.error("Missing built-in roles: %s", missing_roles)
        return False

    logger.info("✓ All expected built-in roles found: %s", found_roles)

    # Show role details
    for role in roles:
        logger.info(
            "  - %s (id=%s, locked=%s): %s",
            role.name,
            role.id,
            role.is_locked,
            role.description,
        )

    logger.info("✓ System organization setup is valid")
    return True


async def main():
    """Main entry point."""
    try:
        # Initialize database
        await init_database()

        # Create System organization
        system_org = await create_system_organization()

        # Create built-in roles
        await create_builtin_roles(system_org)

        # Verify setup
        success = await verify_system_setup()

        if success:
            logger.info("=" * 60)
            logger.info("System organization initialization complete!")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("System organization initialization failed verification!")
            return 1

    except Exception as e:
        logger.error(
            "Error during System organization initialization: %s", str(e), exc_info=True
        )
        return 1

    finally:
        await close_database()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
