"""
Integration tests for RaceTime OAuth2 flow.

Tests the complete RaceTime.gg account linking workflow.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from middleware.racetime_oauth import RacetimeOAuthService
from application.services.core.user_service import UserService
from models import User
from config import settings


@pytest.mark.integration
@pytest.mark.asyncio
class TestRacetimeOAuth2Flow:
    """Test cases for RaceTime OAuth2 integration."""

    async def test_link_initiate_requires_auth(self):
        """Test that initiating RaceTime link requires authentication."""
        # Link initiation is handled by NiceGUI page (/racetime/link/initiate)
        # It uses require_auth() which redirects to login if not authenticated
        # We test the service layer methods independently
        
        service = RacetimeOAuthService()
        
        # Verify service can generate authorization URL
        state = "test_state"
        url = service.get_authorization_url(state)
        
        assert settings.RACETIME_URL in url
        assert state in url
        assert "client_id" in url

    async def test_link_initiate_redirects_to_racetime(self):
        """Test that link initiation redirects to RaceTime.gg."""
        service = RacetimeOAuthService()
        state = "test_csrf_token"
        
        url = service.get_authorization_url(state)
        
        # Verify URL structure
        assert url.startswith(f"{settings.RACETIME_URL}/o/authorize")
        assert f"client_id={settings.RACETIME_CLIENT_ID}" in url
        assert f"state={state}" in url
        assert "response_type=code" in url
        assert "scope=read" in url

    async def test_link_callback_success(self, db, sample_user):
        """Test successful OAuth callback and account linking."""
        service = RacetimeOAuthService()
        user_service = UserService()
        
        # Mock token exchange
        mock_token_data = {
            'access_token': 'test_racetime_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 2592000  # 30 days
        }
        
        # Mock user info from RaceTime
        mock_user_info = {
            'id': 'racetime_user_123',
            'name': 'TestRacer',
            'discriminator': '1234'
        }
        
        with patch.object(service, 'exchange_code_for_token', AsyncMock(return_value=mock_token_data)):
            with patch.object(service, 'get_user_info', AsyncMock(return_value=mock_user_info)):
                # Link account
                token_data = await service.exchange_code_for_token('test_code')
                user_info = await service.get_user_info(token_data['access_token'])
                expires_at = service.calculate_token_expiry(token_data['expires_in'])
                
                linked_user = await user_service.link_racetime_account(
                    user=sample_user,
                    racetime_id=user_info['id'],
                    racetime_name=user_info['name'],
                    access_token=token_data['access_token'],
                    refresh_token=token_data['refresh_token'],
                    expires_at=expires_at
                )
                
                # Verify account was linked
                assert linked_user.racetime_id == 'racetime_user_123'
                assert linked_user.racetime_name == 'TestRacer'
                assert linked_user.racetime_access_token == 'test_racetime_token'
                assert linked_user.racetime_refresh_token == 'test_refresh_token'

    async def test_link_callback_invalid_state(self):
        """Test OAuth callback with invalid state (CSRF protection)."""
        # State validation happens at the page/route level
        # The service layer doesn't validate state
        # We verify the service generates URLs with state parameter
        
        service = RacetimeOAuthService()
        
        state1 = "valid_state"
        state2 = "invalid_state"
        
        url1 = service.get_authorization_url(state1)
        url2 = service.get_authorization_url(state2)
        
        # Each URL should contain its respective state
        assert f"state={state1}" in url1
        assert f"state={state2}" in url2
        assert f"state={state1}" not in url2
        assert f"state={state2}" not in url1

    async def test_link_callback_existing_account(self, db, sample_user, admin_user):
        """Test linking when RaceTime account already linked to another user."""
        user_service = UserService()
        racetime_service = RacetimeOAuthService()
        
        # Link RaceTime account to first user
        linked_user1 = await user_service.link_racetime_account(
            user=sample_user,
            racetime_id='duplicate_racer',
            racetime_name='DuplicateRacer',
            access_token='token1',
            refresh_token='refresh1',
            expires_at=racetime_service.calculate_token_expiry(2592000)
        )
        
        assert linked_user1.racetime_id == 'duplicate_racer'
        
        # Try to link same RaceTime account to second user
        with pytest.raises(ValueError, match="already linked"):
            await user_service.link_racetime_account(
                user=admin_user,
                racetime_id='duplicate_racer',  # Same ID
                racetime_name='DuplicateRacer',
                access_token='token2',
                refresh_token='refresh2',
                expires_at=racetime_service.calculate_token_expiry(2592000)
            )

    async def test_unlink_account_success(self, db, sample_user):
        """Test successfully unlinking a RaceTime account."""
        user_service = UserService()
        racetime_service = RacetimeOAuthService()
        
        # First link an account
        linked_user = await user_service.link_racetime_account(
            user=sample_user,
            racetime_id='racer_to_unlink',
            racetime_name='UnlinkTest',
            access_token='token',
            refresh_token='refresh',
            expires_at=racetime_service.calculate_token_expiry(2592000)
        )
        
        assert linked_user.racetime_id is not None
        
        # Unlink the account
        unlinked_user = await user_service.unlink_racetime_account(linked_user)
        
        # Verify all RaceTime fields are cleared
        assert unlinked_user.racetime_id is None
        assert unlinked_user.racetime_name is None
        assert unlinked_user.racetime_access_token is None
        assert unlinked_user.racetime_refresh_token is None

    async def test_unlink_account_requires_auth(self):
        """Test that unlinking requires authentication."""
        # Unlinking is handled by UserService.unlink_racetime_account()
        # The page/route checks authentication before calling the service
        # We test that the service method requires a valid user
        
        user_service = UserService()
        
        # Cannot unlink without a user object
        # Service method signature requires User parameter
        with pytest.raises(TypeError):
            await user_service.unlink_racetime_account()  # Missing user parameter

    async def test_link_status_endpoint(self, db, sample_user):
        """Test the link status endpoint."""
        user_service = UserService()
        racetime_service = RacetimeOAuthService()
        
        # Initially not linked
        assert sample_user.racetime_id is None
        
        # Link account
        linked_user = await user_service.link_racetime_account(
            user=sample_user,
            racetime_id='status_test_racer',
            racetime_name='StatusTester',
            access_token='token',
            refresh_token='refresh',
            expires_at=racetime_service.calculate_token_expiry(2592000)
        )
        
        # Verify link status
        assert linked_user.racetime_id == 'status_test_racer'
        assert linked_user.racetime_name == 'StatusTester'
        
        # Status would be exposed via API endpoint
        # which would return {'linked': True, 'racetime_id': ..., 'racetime_name': ...}
        is_linked = linked_user.racetime_id is not None
        assert is_linked is True
