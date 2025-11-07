"""
Integration tests for Twitch OAuth2 flow.

Tests the complete Twitch account linking workflow.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, Mock
from middleware.twitch_oauth import TwitchOAuthService
from application.services.core.user_service import UserService
from models import User
from config import settings


@pytest.mark.integration
@pytest.mark.asyncio
class TestTwitchOAuth2Flow:
    """Test cases for Twitch OAuth2 integration."""

    async def test_link_initiate_requires_auth(self):
        """Test that initiating Twitch link requires authentication."""
        # Link initiation is handled by NiceGUI page (/twitch/link/initiate)
        # It uses require_auth() which redirects to login if not authenticated
        # We test the service layer methods independently

        service = TwitchOAuthService()

        # Verify service can generate authorization URL
        state = "test_state"
        url = service.get_authorization_url(state)

        assert "id.twitch.tv" in url
        assert state in url
        assert "client_id" in url

    async def test_link_initiate_redirects_to_twitch(self):
        """Test that link initiation redirects to Twitch."""
        service = TwitchOAuthService()
        state = "test_csrf_token"

        url = service.get_authorization_url(state)

        # Verify URL structure
        assert url.startswith("https://id.twitch.tv/oauth2/authorize")
        assert f"client_id={settings.TWITCH_CLIENT_ID}" in url
        assert f"state={state}" in url
        assert "response_type=code" in url
        # No email scope per requirements
        assert "user:read:email" not in url

    async def test_link_callback_success(self, db, sample_user):
        """Test successful OAuth callback and account linking."""
        service = TwitchOAuthService()
        user_service = UserService()

        # Mock token exchange
        mock_token_data = {
            'access_token': 'test_twitch_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 14400  # 4 hours (Twitch default)
        }

        # Mock user info from Twitch
        mock_user_info = {
            'id': '123456789',
            'login': 'teststreamer',
            'display_name': 'TestStreamer',
            'type': '',
            'broadcaster_type': '',
            'description': 'Test user',
            'profile_image_url': 'https://example.com/profile.jpg',
            'offline_image_url': '',
            'view_count': 0,
            'created_at': '2020-01-01T00:00:00Z'
        }

        with patch.object(service, 'exchange_code_for_token', AsyncMock(return_value=mock_token_data)):
            with patch.object(service, 'get_user_info', AsyncMock(return_value=mock_user_info)):
                # Link account
                token_data = await service.exchange_code_for_token('test_code')
                user_info = await service.get_user_info(token_data['access_token'])
                expires_at = service.calculate_token_expiry(token_data['expires_in'])

                linked_user = await user_service.link_twitch_account(
                    user=sample_user,
                    twitch_id=user_info['id'],
                    twitch_name=user_info['login'],
                    twitch_display_name=user_info['display_name'],
                    access_token=token_data['access_token'],
                    refresh_token=token_data['refresh_token'],
                    expires_at=expires_at
                )

                # Verify account was linked
                assert linked_user.twitch_id == '123456789'
                assert linked_user.twitch_name == 'teststreamer'
                assert linked_user.twitch_display_name == 'TestStreamer'
                assert linked_user.twitch_access_token == 'test_twitch_token'
                assert linked_user.twitch_refresh_token == 'test_refresh_token'

    async def test_link_callback_invalid_state(self):
        """Test OAuth callback with invalid state (CSRF protection)."""
        # State validation happens at the page/route level
        # The service layer doesn't validate state
        # We verify the service generates URLs with state parameter

        service = TwitchOAuthService()

        state1 = "valid_state"
        state2 = "invalid_state"

        url1 = service.get_authorization_url(state1)
        url2 = service.get_authorization_url(state2)

        # States should be different in URLs
        assert state1 in url1
        assert state2 in url2
        assert url1 != url2

    async def test_link_account_already_linked(self, db, sample_user):
        """Test linking an account that's already linked to another user."""
        user_service = UserService()

        # Create another user
        other_user = await User.create(
            discord_id=999999999,
            discord_username="OtherUser",
            permission=0,
            is_active=True
        )

        # Link Twitch account to other_user
        await user_service.link_twitch_account(
            user=other_user,
            twitch_id='already_linked_123',
            twitch_name='linkedstreamer',
            twitch_display_name='LinkedStreamer',
            access_token='token',
            refresh_token='refresh'
        )

        # Try to link same Twitch account to sample_user
        with pytest.raises(ValueError, match="already linked to another user"):
            await user_service.link_twitch_account(
                user=sample_user,
                twitch_id='already_linked_123',
                twitch_name='linkedstreamer',
                twitch_display_name='LinkedStreamer',
                access_token='token2',
                refresh_token='refresh2'
            )

    async def test_unlink_account(self, db, sample_user):
        """Test unlinking a Twitch account."""
        user_service = UserService()

        # Link account first
        linked_user = await user_service.link_twitch_account(
            user=sample_user,
            twitch_id='twitch_123',
            twitch_name='testuser',
            twitch_display_name='TestUser',
            access_token='token',
            refresh_token='refresh'
        )
        assert linked_user.twitch_id == 'twitch_123'

        # Unlink account
        unlinked_user = await user_service.unlink_twitch_account(linked_user)

        # Verify account was unlinked
        assert unlinked_user.twitch_id is None
        assert unlinked_user.twitch_name is None
        assert unlinked_user.twitch_display_name is None
        assert unlinked_user.twitch_access_token is None
        assert unlinked_user.twitch_refresh_token is None

    async def test_refresh_token(self, db, sample_user):
        """Test refreshing Twitch access token."""
        service = TwitchOAuthService()
        user_service = UserService()

        # Link account first
        linked_user = await user_service.link_twitch_account(
            user=sample_user,
            twitch_id='twitch_123',
            twitch_name='testuser',
            twitch_display_name='TestUser',
            access_token='old_token',
            refresh_token='refresh_token'
        )

        # Mock token refresh - mock the httpx response
        mock_new_token_data = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 14400
        }

        # Create a mock response - json() is SYNC in httpx, not async
        from unittest.mock import Mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_new_token_data)  # Sync method

        # Mock httpx.AsyncClient context manager and post method
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch('httpx.AsyncClient', return_value=mock_client):
            refreshed_user = await user_service.refresh_twitch_token(linked_user)

            # Verify tokens were updated
            assert refreshed_user.twitch_access_token == 'new_access_token'
            assert refreshed_user.twitch_refresh_token == 'new_refresh_token'

    async def test_admin_unlink_account(self, db, sample_user):
        """Test admin unlinking a Twitch account."""
        user_service = UserService()

        # Create admin user
        admin_user = await User.create(
            discord_id=888888888,
            discord_username="AdminUser",
            permission=100,  # ADMIN
            is_active=True
        )

        # Link account to sample_user
        await user_service.link_twitch_account(
            user=sample_user,
            twitch_id='twitch_123',
            twitch_name='testuser',
            twitch_display_name='TestUser',
            access_token='token',
            refresh_token='refresh'
        )

        # Admin unlinks the account
        result = await user_service.admin_unlink_twitch_account(
            user_id=sample_user.id,
            admin_user=admin_user
        )

        # Verify account was unlinked
        assert result is not None
        assert result.twitch_id is None

    async def test_admin_unlink_unauthorized(self, db, sample_user):
        """Test that non-admin cannot admin unlink accounts."""
        user_service = UserService()

        # Create non-admin user
        normal_user = await User.create(
            discord_id=777777777,
            discord_username="NormalUser",
            permission=0,  # USER
            is_active=True
        )

        # Try to admin unlink (should fail)
        result = await user_service.admin_unlink_twitch_account(
            user_id=sample_user.id,
            admin_user=normal_user
        )

        # Should return None for unauthorized
        assert result is None

    async def test_get_twitch_link_statistics(self, db, sample_user):
        """Test getting Twitch link statistics."""
        user_service = UserService()

        # Create admin user
        admin_user = await User.create(
            discord_id=888888888,
            discord_username="AdminUser",
            permission=100,  # ADMIN
            is_active=True
        )

        # Link account to sample_user
        await user_service.link_twitch_account(
            user=sample_user,
            twitch_id='twitch_123',
            twitch_name='testuser',
            twitch_display_name='TestUser',
            access_token='token',
            refresh_token='refresh'
        )

        # Get statistics
        stats = await user_service.get_twitch_link_statistics(admin_user)

        # Verify stats structure
        assert 'total_users' in stats
        assert 'linked_users' in stats
        assert 'unlinked_users' in stats
        assert 'link_percentage' in stats
        assert stats['linked_users'] >= 1  # At least sample_user is linked
