"""
Tests for MOTD (Message of the Day) banner functionality.
"""

import pytest
from datetime import datetime, timezone
from application.services.core.settings_service import SettingsService


@pytest.mark.asyncio
class TestMOTDSettings:
    """Test MOTD settings management."""

    async def test_set_motd_text(self, db):
        """Test setting MOTD text."""
        service = SettingsService()

        # Set MOTD text
        motd_text = "Welcome to SahaBot2! Please check the latest updates."
        await service.set_global(
            key='motd_text',
            value=motd_text,
            description='Message of the Day banner text',
            is_public=True
        )

        # Retrieve and verify
        motd_setting = await service.get_global('motd_text')
        assert motd_setting is not None
        assert motd_setting['value'] == motd_text
        assert motd_setting['is_public'] is True

    async def test_set_motd_timestamp(self, db):
        """Test setting MOTD update timestamp."""
        service = SettingsService()

        # Set timestamp
        current_time = datetime.now(timezone.utc).isoformat()
        await service.set_global(
            key='motd_updated_at',
            value=current_time,
            description='Last time MOTD was updated',
            is_public=True
        )

        # Retrieve and verify
        timestamp_setting = await service.get_global('motd_updated_at')
        assert timestamp_setting is not None
        assert timestamp_setting['value'] == current_time

    async def test_update_motd_updates_timestamp(self, db):
        """Test that updating MOTD also updates the timestamp."""
        service = SettingsService()

        # Set initial MOTD
        initial_text = "Initial message"
        initial_time = datetime.now(timezone.utc).isoformat()
        await service.set_global(key='motd_text', value=initial_text, is_public=True)
        await service.set_global(key='motd_updated_at', value=initial_time, is_public=True)

        # Update MOTD
        updated_text = "Updated message"
        updated_time = datetime.now(timezone.utc).isoformat()
        await service.set_global(key='motd_text', value=updated_text, is_public=True)
        await service.set_global(key='motd_updated_at', value=updated_time, is_public=True)

        # Verify updates
        motd_setting = await service.get_global('motd_text')
        timestamp_setting = await service.get_global('motd_updated_at')

        assert motd_setting['value'] == updated_text
        assert timestamp_setting['value'] == updated_time
        assert timestamp_setting['value'] != initial_time

    async def test_empty_motd(self, db):
        """Test that empty MOTD text can be set to disable banner."""
        service = SettingsService()

        # Set empty MOTD
        await service.set_global(key='motd_text', value='', is_public=True)

        # Retrieve and verify
        motd_setting = await service.get_global('motd_text')
        assert motd_setting is not None
        assert motd_setting['value'] == ''

    async def test_motd_html_content(self, db):
        """Test that MOTD can contain HTML formatting."""
        service = SettingsService()

        # Set MOTD with HTML
        html_content = '<strong>Important:</strong> System maintenance scheduled for <em>tomorrow</em>.'
        await service.set_global(key='motd_text', value=html_content, is_public=True)

        # Retrieve and verify
        motd_setting = await service.get_global('motd_text')
        assert motd_setting is not None
        assert motd_setting['value'] == html_content

    async def test_delete_motd(self, db):
        """Test deleting MOTD setting."""
        service = SettingsService()

        # Set MOTD
        await service.set_global(key='motd_text', value='Test message', is_public=True)

        # Verify it exists
        motd_setting = await service.get_global('motd_text')
        assert motd_setting is not None

        # Delete MOTD
        await service.delete_global('motd_text')

        # Verify it's deleted
        motd_setting = await service.get_global('motd_text')
        assert motd_setting is None
