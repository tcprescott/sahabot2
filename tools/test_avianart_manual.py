#!/usr/bin/env python3
"""
Manual test script for Avianart randomizer.

This script demonstrates the Avianart service and command handler.
Run with: poetry run python tools/test_avianart_manual.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from application.services.randomizer.avianart_service import AvianartService
from application.services.randomizer.randomizer_service import RandomizerService


async def test_avianart_service():
    """Test Avianart service directly."""
    print("\n" + "=" * 70)
    print("Testing Avianart Service")
    print("=" * 70)
    
    service = AvianartService()
    
    print("\nService created successfully")
    print(f"Base URL: {service.BASE_URL}")
    print(f"Poll interval: {service.POLL_INTERVAL_SECONDS} seconds")
    print(f"Max attempts: {service.MAX_POLL_ATTEMPTS}")
    
    # Note: We can't actually call the API without a valid preset
    # This is just a demonstration of the service structure
    print("\n✓ AvianartService initialized")
    

async def test_randomizer_factory():
    """Test that Avianart is registered in RandomizerService."""
    print("\n" + "=" * 70)
    print("Testing RandomizerService Factory")
    print("=" * 70)
    
    service = RandomizerService()
    
    # List all randomizers
    randomizers = service.list_randomizers()
    print(f"\nAvailable randomizers ({len(randomizers)}):")
    for r in randomizers:
        print(f"  - {r}")
    
    # Check Avianart is registered
    if 'avianart' in randomizers:
        print("\n✓ Avianart is registered in RandomizerService")
    else:
        print("\n✗ ERROR: Avianart is NOT registered!")
        return False
    
    # Get Avianart service
    try:
        avianart = service.get_randomizer('avianart')
        print(f"✓ Successfully retrieved Avianart service: {type(avianart).__name__}")
    except Exception as e:
        print(f"✗ ERROR: Failed to get Avianart service: {e}")
        return False
    
    return True


async def test_command_handler():
    """Test that !avianart command is registered."""
    print("\n" + "=" * 70)
    print("Testing !avianart Command Handler")
    print("=" * 70)
    
    from racetime.command_handlers import BUILTIN_HANDLERS, get_all_handlers
    
    # Check if handle_avianart is in built-in handlers
    if 'handle_avianart' in BUILTIN_HANDLERS:
        print("\n✓ handle_avianart is registered in BUILTIN_HANDLERS")
    else:
        print("\n✗ ERROR: handle_avianart is NOT in BUILTIN_HANDLERS!")
        return False
    
    # Get all handlers
    all_handlers = get_all_handlers()
    if 'handle_avianart' in all_handlers:
        print("✓ handle_avianart is available in get_all_handlers()")
    else:
        print("✗ ERROR: handle_avianart is NOT in get_all_handlers()!")
        return False
    
    # Show handler signature
    handler = all_handlers['handle_avianart']
    print(f"\nHandler function: {handler.__name__}")
    print(f"Module: {handler.__module__}")
    print(f"Docstring: {handler.__doc__.split(chr(10))[0] if handler.__doc__ else 'None'}")
    
    return True


async def show_usage_example():
    """Show example usage."""
    print("\n" + "=" * 70)
    print("Usage Examples")
    print("=" * 70)
    
    print("\n1. Using the service directly:")
    print("   ```python")
    print("   from application.services.randomizer import AvianartService")
    print("   ")
    print("   service = AvianartService()")
    print("   result = await service.generate(preset='open', race=True)")
    print("   print(f'Seed URL: {result.url}')")
    print("   print(f'File Select Code: {result.metadata['file_select_code']}')")
    print("   ```")
    
    print("\n2. Using the RandomizerService factory:")
    print("   ```python")
    print("   from application.services.randomizer import RandomizerService")
    print("   ")
    print("   service = RandomizerService().get_randomizer('avianart')")
    print("   result = await service.generate(preset='open', race=True)")
    print("   ```")
    
    print("\n3. Using the RaceTime.gg command:")
    print("   In a RaceTime.gg race room chat:")
    print("   !avianart <preset_name>")
    print("   ")
    print("   Example:")
    print("   !avianart open")
    print("   ")
    print("   Response:")
    print("   Avianart seed generated! https://avianart.games/perm/ABC123 |")
    print("   Code: Bow/Bombs/Hookshot/Mushroom/Lamp | Version: 1.0.0")


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("Avianart Integration Test")
    print("=" * 70)
    print("\nThis test verifies that the Avianart randomizer is properly")
    print("integrated into SahaBot2 without making actual API calls.")
    
    results = []
    
    # Run tests
    await test_avianart_service()
    results.append(await test_randomizer_factory())
    results.append(await test_command_handler())
    await show_usage_example()
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    if all(results):
        print("\n✓ All tests passed!")
        print("\nThe Avianart randomizer is properly integrated.")
        print("Ready to use with real Avianart presets!")
    else:
        print("\n✗ Some tests failed!")
        return 1
    
    print("\n" + "=" * 70)
    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
