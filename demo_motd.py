#!/usr/bin/env python
"""
Demo script to show MOTD banner functionality.

This script demonstrates how the MOTD banner works:
1. Set an MOTD message
2. Show how it's stored
3. Show how the timestamp works
4. Explain the dismissal logic
"""

import asyncio
from datetime import datetime, timezone


async def demo_motd():
    """Demonstrate MOTD functionality."""
    from application.services.core.settings_service import SettingsService
    from tortoise import Tortoise
    from migrations.tortoise_config import get_tortoise_config

    # Initialize database
    config = get_tortoise_config()
    await Tortoise.init(config=config)
    await Tortoise.generate_schemas()

    service = SettingsService()

    print("=" * 60)
    print("MOTD (Message of the Day) Banner Demo")
    print("=" * 60)
    print()

    # 1. Set initial MOTD
    print("1. Setting initial MOTD message...")
    initial_motd = "Welcome to SahaBot2! Check out our new features."
    initial_time = datetime.now(timezone.utc).isoformat()

    await service.set_global(
        key="motd_text",
        value=initial_motd,
        description="Message of the Day banner text",
        is_public=True,
    )
    await service.set_global(
        key="motd_updated_at",
        value=initial_time,
        description="Last time MOTD was updated",
        is_public=True,
    )
    print(f"   ✓ MOTD set: {initial_motd}")
    print(f"   ✓ Timestamp: {initial_time}")
    print()

    # 2. Retrieve MOTD
    print("2. Retrieving MOTD from database...")
    motd = await service.get_global("motd_text")
    timestamp = await service.get_global("motd_updated_at")
    print(f"   ✓ MOTD: {motd['value']}")
    print(f"   ✓ Timestamp: {timestamp['value']}")
    print()

    # 3. Explain dismissal logic
    print("3. Dismissal Logic (handled in browser):")
    print("   - When user clicks dismiss, current timestamp stored in localStorage")
    print("   - Banner hidden via JavaScript")
    print("   - If admin updates MOTD, new timestamp > dismissed timestamp")
    print("   - Banner reappears for all users")
    print()

    # 4. Update MOTD
    print("4. Updating MOTD (simulating admin edit)...")
    await asyncio.sleep(1)  # Small delay to ensure different timestamp
    updated_motd = "🎉 <strong>New Tournament Starting!</strong> Sign up now in the Organizations tab."
    updated_time = datetime.now(timezone.utc).isoformat()

    await service.set_global(key="motd_text", value=updated_motd, is_public=True)
    await service.set_global(key="motd_updated_at", value=updated_time, is_public=True)

    print(f"   ✓ Updated MOTD: {updated_motd}")
    print(f"   ✓ New timestamp: {updated_time}")
    print()

    # 5. Explain re-display
    print("5. Banner Re-display:")
    print(f"   - Original timestamp: {initial_time}")
    print(f"   - Updated timestamp: {updated_time}")
    print(f"   - If user dismissed at original time, banner will reappear")
    print(f"   - JavaScript compares: {updated_time} > {initial_time} = True")
    print()

    # 6. Clear MOTD
    print("6. Disabling banner (setting empty MOTD)...")
    await service.set_global(key="motd_text", value="", is_public=True)
    empty_motd = await service.get_global("motd_text")
    print(f"   ✓ MOTD now: '{empty_motd['value']}' (empty = banner hidden)")
    print()

    print("=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print()
    print("How to use in production:")
    print("1. Admin goes to Admin Panel → Settings")
    print("2. Clicks 'Edit MOTD' button")
    print("3. Enters message (HTML supported)")
    print("4. Clicks Save")
    print("5. Banner appears on all pages")
    print("6. Users can dismiss it")
    print("7. If admin updates MOTD, it reappears for everyone")
    print()

    # Cleanup
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(demo_motd())
