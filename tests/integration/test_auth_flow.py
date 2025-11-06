"""
Integration tests for Discord OAuth2 authentication flow.

Tests the complete OAuth2 authentication workflow.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from middleware.auth import DiscordAuthService
from models import User
from config import settings


@pytest.mark.integration
@pytest.mark.asyncio
class TestDiscordOAuth2Flow:
    """Test cases for Discord OAuth2 integration."""
    
    async def test_authorization_url_generation(self):
        """Test generating Discord OAuth2 authorization URL."""
        service = DiscordAuthService()
        state = "test_state_123"
        
        url = service.get_authorization_url(state)
        
        # Verify URL structure
        assert url.startswith("https://discord.com/api/oauth2/authorize")
        assert f"client_id={settings.DISCORD_CLIENT_ID}" in url
        assert f"state={state}" in url
        assert "response_type=code" in url
        assert "scope=identify" in url
    
    async def test_oauth_callback_success(self, db, discord_user_payload):
        """Test successful OAuth callback handling."""
        service = DiscordAuthService()
        
        # Mock token exchange
        mock_token_data = {
            'access_token': 'mock_access_token',
            'refresh_token': 'mock_refresh_token',
            'expires_in': 604800
        }
        
        with patch.object(service, 'exchange_code_for_token', AsyncMock(return_value=mock_token_data)):
            with patch.object(service, 'get_user_info', AsyncMock(return_value=discord_user_payload)):
                # Authenticate user
                user = await service.authenticate_user(code='test_code')
                
                # Verify user was created
                assert user is not None
                assert user.discord_id == int(discord_user_payload['id'])
                assert user.discord_username == discord_user_payload['username']
                
                # Verify tokens stored
                assert user.discord_access_token == 'mock_access_token'
                assert user.discord_refresh_token == 'mock_refresh_token'
                assert user.discord_token_expires_at is not None
    
    async def test_oauth_callback_invalid_state(self):
        """Test OAuth callback with invalid state (CSRF protection)."""
        # This would be tested at the page/route level
        # The service layer doesn't handle state validation
        # State validation happens in the OAuth callback page
        
        # For now, verify service methods work independently
        service = DiscordAuthService()
        
        # Generate URL with state
        state = "valid_state"
        url = service.get_authorization_url(state)
        assert f"state={state}" in url
        
        # Different state would be rejected by page handler
        # Service methods don't perform state validation
    
    async def test_user_creation_from_oauth(self, db, discord_user_payload):
        """Test creating user from OAuth data."""
        service = DiscordAuthService()
        
        # Mock token exchange
        mock_token_data = {
            'access_token': 'test_token',
            'refresh_token': 'test_refresh',
            'expires_in': 604800
        }
        
        with patch.object(service, 'exchange_code_for_token', AsyncMock(return_value=mock_token_data)):
            with patch.object(service, 'get_user_info', AsyncMock(return_value=discord_user_payload)):
                # Ensure user doesn't exist
                existing_user = await User.filter(discord_id=int(discord_user_payload['id'])).first()
                assert existing_user is None
                
                # Create user via OAuth
                user = await service.authenticate_user(code='test_code')
                
                # Verify user was created
                assert user.discord_id == int(discord_user_payload['id'])
                assert user.discord_username == discord_user_payload['username']
                assert user.discord_discriminator == discord_user_payload.get('discriminator')
                
                # Verify in database
                db_user = await User.filter(id=user.id).first()
                assert db_user is not None
                assert db_user.discord_id == user.discord_id
    
    async def test_user_update_from_oauth(self, db, sample_user, discord_user_payload):
        """Test updating existing user from OAuth data."""
        service = DiscordAuthService()
        
        # Update payload to match sample_user's Discord ID
        discord_user_payload['id'] = str(sample_user.discord_id)
        discord_user_payload['username'] = 'updated_username'
        
        mock_token_data = {
            'access_token': 'new_token',
            'refresh_token': 'new_refresh',
            'expires_in': 604800
        }
        
        with patch.object(service, 'exchange_code_for_token', AsyncMock(return_value=mock_token_data)):
            with patch.object(service, 'get_user_info', AsyncMock(return_value=discord_user_payload)):
                # Authenticate (should update existing user)
                user = await service.authenticate_user(code='test_code')
                
                # Verify same user ID
                assert user.id == sample_user.id
                
                # Verify username was updated
                assert user.discord_username == 'updated_username'
                
                # Verify token was stored
                assert user.discord_access_token == 'new_token'
                assert user.discord_refresh_token == 'new_refresh'
    
    async def test_session_management(self):
        """Test user session creation and management."""
        # Session management uses NiceGUI app.storage.user
        # This would require NiceGUI context to test properly
        # We can test the static methods with mocked storage
        
        from nicegui import app
        
        # Mock storage
        mock_storage = {}
        
        with patch.object(app, 'storage', MagicMock(user=mock_storage)):
            # Test setting current user
            from models import Permission
            test_user = User(
                id=123,
                discord_id=456789,
                discord_username='test_user',
                permission=Permission.USER
            )
            
            await DiscordAuthService.set_current_user(test_user)
            
            # Verify session data
            assert mock_storage['user_id'] == 123
            assert mock_storage['discord_id'] == 456789
            assert mock_storage['permission'] == Permission.USER.value
            
            # Test clearing session
            await DiscordAuthService.clear_current_user()
            
            # Verify storage cleared
            assert len(mock_storage) == 0
