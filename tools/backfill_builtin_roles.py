#!/usr/bin/env python3
"""
Backfill Built-in Roles

This script creates built-in roles for all existing organizations that don't have them.
Run this after implementing the authorization system to ensure all orgs have their roles.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise
from config import settings
from models.organizations import Organization
from application.services.organizations.organization_service import OrganizationService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database connection."""
    await Tortoise.init(
        db_url=settings.database_url,
        modules={'models': [
            'models.user',
            'models.organizations',
            'models.authorization',
        ]}
    )


async def close_database():
    """Close database connection."""
    await Tortoise.close_connections()


async def backfill_organization_roles(org: Organization) -> int:
    """
    Backfill built-in roles for a single organization.
    
    Args:
        org: Organization to backfill
        
    Returns:
        Number of roles created
    """
    logger.info("Backfilling roles for organization '%s' (id=%s)...", org.name, org.id)
    
    org_service = OrganizationService()
    created_roles = await org_service.create_builtin_roles(org)
    
    return len(created_roles)


async def main():
    """Main entry point."""
    try:
        await init_database()
        
        logger.info("=" * 60)
        logger.info("Backfilling Built-in Roles for Existing Organizations")
        logger.info("=" * 60)
        logger.info("")
        
        # Get all organizations except System (id=-1)
        organizations = await Organization.filter(id__gt=0).all()
        
        if not organizations:
            logger.info("No organizations found (besides System org)")
            return 0
        
        logger.info("Found %s organizations to process", len(organizations))
        logger.info("")
        
        total_created = 0
        total_orgs_updated = 0
        
        for org in organizations:
            created_count = await backfill_organization_roles(org)
            if created_count > 0:
                total_orgs_updated += 1
                total_created += created_count
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("Backfill complete!")
        logger.info("  - Organizations processed: %s", len(organizations))
        logger.info("  - Organizations updated: %s", total_orgs_updated)
        logger.info("  - Total roles created: %s", total_created)
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error("Error during backfill: %s", str(e), exc_info=True)
        return 1
    finally:
        await close_database()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
