#!/usr/bin/env python3
"""
Quick database initialization test.

This script tests if the database can be initialized properly and models loaded.
"""

import asyncio
import sys


async def test_db_init():
    """Test database initialization."""
    print("Testing database initialization...")
    
    try:
        # Import database functions
        from database import init_db, close_db
        
        print("✓ Database module imported")
        
        # Initialize database
        await init_db()
        print("✓ Database initialized")
        
        # Now import models
        from models import User, Permission, AuditLog, ApiToken
        print("✓ Models imported")
        
        # Test a simple query
        user_count = await User.all().count()
        print(f"✓ Database query successful (found {user_count} users)")
        
        # Close database
        await close_db()
        print("✓ Database closed")
        
        print("\n✅ All database tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_db_init())
    sys.exit(0 if success else 1)
