"""
Tests for mystery preset authentication behavior.

This module tests that:
1. Public presets can be accessed without authentication
2. Private presets require authentication and ownership
"""

import pytest
from application.services.randomizer.alttpr_mystery_service import ALTTPRMysteryService
from models.randomizer_preset import RandomizerPreset
from models.user import User, Permission


class TestMysteryPresetAuthentication:
    """Test suite for mystery preset authentication."""

    @pytest.fixture
    async def owner_user(self, db):
        """Create a user who owns presets."""
        return await User.create(
            discord_id=111111111,
            discord_username="owner",
            discord_discriminator="0001",
            discord_avatar="avatar1",
            discord_email="owner@example.com",
            permission=Permission.USER,
            is_active=True
        )

    @pytest.fixture
    async def other_user(self, db):
        """Create another user."""
        return await User.create(
            discord_id=222222222,
            discord_username="other",
            discord_discriminator="0002",
            discord_avatar="avatar2",
            discord_email="other@example.com",
            permission=Permission.USER,
            is_active=True
        )

    @pytest.fixture
    async def public_preset(self, db, owner_user):
        """Create a public mystery preset."""
        return await RandomizerPreset.create(
            user_id=owner_user.id,
            randomizer='alttpr',
            name='public_mystery',
            description='A public mystery preset',
            settings={
                'preset_type': 'mystery',
                'weights': {
                    'open': 10,
                    'standard': 5
                }
            },
            is_public=True
        )

    @pytest.fixture
    async def private_preset(self, db, owner_user):
        """Create a private mystery preset."""
        return await RandomizerPreset.create(
            user_id=owner_user.id,
            randomizer='alttpr',
            name='private_mystery',
            description='A private mystery preset',
            settings={
                'preset_type': 'mystery',
                'weights': {
                    'inverted': 7,
                    'retro': 3
                }
            },
            is_public=False
        )

    @pytest.mark.asyncio
    async def test_public_preset_no_auth(self, db, public_preset):
        """Test that public presets can be accessed without authentication."""
        service = ALTTPRMysteryService()
        
        # Mock the alttpr_service.generate to avoid actual API calls
        from unittest.mock import AsyncMock, MagicMock
        mock_result = MagicMock()
        mock_result.url = "https://alttpr.com/test"
        mock_result.hash_id = "TESTHASH"
        service.alttpr_service.generate = AsyncMock(return_value=mock_result)
        
        # Should succeed without user_id for public preset
        result, description = await service.generate_from_preset_name(
            mystery_preset_name='public_mystery',
            user_id=None,  # No authentication
            tournament=True,
            spoilers='off'
        )
        
        assert result is not None
        assert 'preset' in description

    @pytest.mark.asyncio
    async def test_public_preset_with_auth(self, db, public_preset, other_user):
        """Test that public presets can be accessed with authentication by any user."""
        service = ALTTPRMysteryService()
        
        # Mock the alttpr_service.generate
        from unittest.mock import AsyncMock, MagicMock
        mock_result = MagicMock()
        mock_result.url = "https://alttpr.com/test"
        mock_result.hash_id = "TESTHASH"
        service.alttpr_service.generate = AsyncMock(return_value=mock_result)
        
        # Should succeed with user_id (even though it's not the owner)
        result, description = await service.generate_from_preset_name(
            mystery_preset_name='public_mystery',
            user_id=other_user.id,
            tournament=True,
            spoilers='off'
        )
        
        assert result is not None
        assert 'preset' in description

    @pytest.mark.asyncio
    async def test_private_preset_no_auth(self, db, private_preset):
        """Test that private presets cannot be accessed without authentication."""
        service = ALTTPRMysteryService()
        
        # Should raise PermissionError for private preset without auth
        with pytest.raises(PermissionError, match="Authentication required"):
            await service.generate_from_preset_name(
                mystery_preset_name='private_mystery',
                user_id=None,  # No authentication
                tournament=True,
                spoilers='off'
            )

    @pytest.mark.asyncio
    async def test_private_preset_wrong_user(self, db, private_preset, other_user):
        """Test that private presets cannot be accessed by non-owners."""
        service = ALTTPRMysteryService()
        
        # Should raise PermissionError for private preset with wrong user
        with pytest.raises(PermissionError, match="Not authorized"):
            await service.generate_from_preset_name(
                mystery_preset_name='private_mystery',
                user_id=other_user.id,  # Different user
                tournament=True,
                spoilers='off'
            )

    @pytest.mark.asyncio
    async def test_private_preset_owner(self, db, private_preset, owner_user):
        """Test that private presets can be accessed by their owner."""
        service = ALTTPRMysteryService()
        
        # Mock the alttpr_service.generate
        from unittest.mock import AsyncMock, MagicMock
        mock_result = MagicMock()
        mock_result.url = "https://alttpr.com/test"
        mock_result.hash_id = "TESTHASH"
        service.alttpr_service.generate = AsyncMock(return_value=mock_result)
        
        # Should succeed with owner's user_id
        result, description = await service.generate_from_preset_name(
            mystery_preset_name='private_mystery',
            user_id=owner_user.id,  # Owner
            tournament=True,
            spoilers='off'
        )
        
        assert result is not None
        assert 'preset' in description

    @pytest.mark.asyncio
    async def test_nonexistent_preset(self, db):
        """Test that accessing a nonexistent preset raises ValueError."""
        service = ALTTPRMysteryService()
        
        with pytest.raises(ValueError, match="not found"):
            await service.generate_from_preset_name(
                mystery_preset_name='nonexistent',
                user_id=None,
                tournament=True,
                spoilers='off'
            )
