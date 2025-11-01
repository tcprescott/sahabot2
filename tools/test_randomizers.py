#!/usr/bin/env python3
"""
Test script for randomizer services.

This script demonstrates how to use the various randomizer services.
Run this to verify the randomizer services are working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import directly from randomizer package to avoid model dependencies
from application.services.randomizer.randomizer_service import RandomizerService


async def test_aosr():
    """Test AOSR randomizer."""
    print("\n=== Testing AOSR ===")
    service = RandomizerService().get_randomizer('aosr')
    result = await service.generate(enemyRando='on', startingRoom='random')
    print(f"URL: {result.url}")
    print(f"Hash: {result.hash_id}")
    print(f"Settings: {result.settings}")


async def test_z1r():
    """Test Z1R randomizer."""
    print("\n=== Testing Z1R ===")
    service = RandomizerService().get_randomizer('z1r')
    result = await service.generate(flags='test-flags')
    print(f"URL: {result.url}")
    print(f"Hash: {result.hash_id}")
    print(f"Metadata: {result.metadata}")


async def test_ffr():
    """Test FFR randomizer."""
    print("\n=== Testing FFR ===")
    service = RandomizerService().get_randomizer('ffr')
    result = await service.generate(flags='test')
    print(f"URL: {result.url}")
    print(f"Hash: {result.hash_id}")


async def test_smb3r():
    """Test SMB3R randomizer."""
    print("\n=== Testing SMB3R ===")
    service = RandomizerService().get_randomizer('smb3r')
    result = await service.generate()
    print(f"URL: {result.url}")
    print(f"Hash: {result.hash_id}")


async def test_factory():
    """Test RandomizerService factory."""
    print("\n=== Testing Factory ===")
    service = RandomizerService()
    available = service.list_randomizers()
    print(f"Available randomizers: {', '.join(available)}")


async def main():
    """Run all tests."""
    print("Testing Randomizer Services")
    print("=" * 50)

    await test_factory()
    await test_aosr()
    await test_z1r()
    await test_ffr()
    await test_smb3r()

    print("\n" + "=" * 50)
    print("All tests completed!")
    print("\nNote: Tests for ALTTPR, SM, SMZ3, OOTR, CTJets, and Bingosync")
    print("require actual API calls and are not included in this basic test.")


if __name__ == '__main__':
    asyncio.run(main())
