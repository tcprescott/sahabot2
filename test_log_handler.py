"""
Test script for the in-memory log handler.

This script tests the log handler functionality without requiring
the full application to be running.
"""

import logging
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from application.utils.log_handler import init_log_handler, get_log_handler


def test_log_handler():
    """Test the in-memory log handler."""
    print("Testing in-memory log handler...")
    print()

    # Initialize the handler
    handler = init_log_handler(max_records=10)
    print(f"✓ Handler initialized with max_records=10")

    # Create a test logger
    logger = logging.getLogger("test.logger")
    logger.setLevel(logging.DEBUG)

    # Test different log levels
    print("\n1. Testing different log levels:")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Get records
    records = handler.get_records()
    print(f"   ✓ Captured {len(records)} log records")

    # Test filtering by level
    print("\n2. Testing level filtering:")
    error_records = handler.get_records(level='ERROR')
    print(f"   ✓ Found {len(error_records)} ERROR records")
    for r in error_records:
        print(f"     - {r.level}: {r.message}")

    # Test search filtering
    print("\n3. Testing search filtering:")
    search_records = handler.get_records(search='warning')
    print(f"   ✓ Found {len(search_records)} records matching 'warning'")
    for r in search_records:
        print(f"     - {r.level}: {r.message}")

    # Test exception logging
    print("\n4. Testing exception logging:")
    try:
        raise ValueError("Test exception")
    except Exception:
        logger.exception("An error occurred")

    exc_records = handler.get_records()
    exc_record = [r for r in exc_records if r.exc_info]
    print(f"   ✓ Found {len(exc_record)} records with exception info")
    if exc_record:
        print(f"     - Exception: {exc_record[0].exc_info[:50]}...")

    # Test circular buffer (max_records=10)
    print("\n5. Testing circular buffer (max=10):")
    for i in range(15):
        logger.info(f"Message {i}")
    
    all_records = handler.get_records()
    print(f"   ✓ Buffer has {len(all_records)} records (should be 10)")
    print(f"     - First message: {all_records[0].message}")
    print(f"     - Last message: {all_records[-1].message}")

    # Test clear
    print("\n6. Testing clear:")
    handler.clear()
    cleared_records = handler.get_records()
    print(f"   ✓ After clear: {len(cleared_records)} records (should be 0)")

    # Test to_dict
    print("\n7. Testing record serialization:")
    logger.info("Test serialization")
    records = handler.get_records()
    if records:
        record_dict = records[-1].to_dict()
        print(f"   ✓ Record serialized to dict with keys: {list(record_dict.keys())}")

    print("\n✅ All tests passed!")


if __name__ == '__main__':
    test_log_handler()
