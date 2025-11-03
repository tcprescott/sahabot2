"""
Unit tests for RaceTime OAuth service and account linking.

Tests the RaceTime.gg OAuth2 flow and account linking functionality.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from application.services.user_service import UserService
from middleware.racetime_oauth import RacetimeOAuthService
from models import User, Permission


@pytest.mark.unit
@pytest.mark.asyncio
class TestRacetimeOAuthService:
    """Test cases for RacetimeOAuthService."""

    def test_get_authorization_url(self):
        """Test generating RaceTime OAuth2 authorization URL."""
        service = RacetimeOAuthService()
        state = "test_state_token"

        auth_url = service.get_authorization_url(state)

        assert "https://racetime.gg/o/authorize" in auth_url
        assert f"state={state}" in auth_url
        assert "response_type=code" in auth_url
        assert "scope=read" in auth_url

    @patch('httpx.AsyncClient')
    async def test_exchange_code_for_token_success(self, mock_client_class):
        """Test successful code-to-token exchange."""
        # Mock the HTTP client response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = RacetimeOAuthService()
        result = await service.exchange_code_for_token("test_code")

        assert result['access_token'] == 'test_access_token'
        mock_client.post.assert_called_once()

    @patch('httpx.AsyncClient')
    async def test_exchange_code_for_token_failure(self, mock_client_class):
        """Test failed code-to-token exchange."""
        # Mock the HTTP client response with error
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid code"
        mock_response.request = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = RacetimeOAuthService()

        with pytest.raises(Exception):
            await service.exchange_code_for_token("invalid_code")

    @patch('httpx.AsyncClient')
    async def test_get_user_info_success(self, mock_client_class):
        """Test successful user info retrieval."""
        # Mock the HTTP client response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'racetime_user_123',
            'name': 'TestRacer',
            'url': 'https://racetime.gg/user/TestRacer'
        }

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = RacetimeOAuthService()
        result = await service.get_user_info("test_token")

        assert result['id'] == 'racetime_user_123'
        assert result['name'] == 'TestRacer'


@pytest.mark.unit
@pytest.mark.asyncio
class TestRacetimeAccountLinking:
    """Test cases for RaceTime account linking in UserService."""

    async def test_link_racetime_account_success(self):
        """Test successfully linking a RaceTime account."""
        # Create mock user
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.discord_id = 123456789
        mock_user.racetime_id = None
        mock_user.save = AsyncMock()

        # Mock repository
        mock_repo = MagicMock()
        mock_repo.get_by_racetime_id = AsyncMock(return_value=None)

        service = UserService()
        service.user_repository = mock_repo

        # Link account
        result = await service.link_racetime_account(
            user=mock_user,
            racetime_id='racetime_123',
            racetime_name='TestRacer',
            access_token='token_abc'
        )

        assert mock_user.racetime_id == 'racetime_123'
        assert mock_user.racetime_name == 'TestRacer'
        assert mock_user.racetime_access_token == 'token_abc'
        mock_user.save.assert_called_once()

    async def test_link_racetime_account_already_linked(self):
        """Test linking a RaceTime account that's already linked to another user."""
        # Create mock users
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.discord_id = 123456789

        mock_existing_user = MagicMock(spec=User)
        mock_existing_user.id = 2
        mock_existing_user.racetime_id = 'racetime_123'

        # Mock repository
        mock_repo = MagicMock()
        mock_repo.get_by_racetime_id = AsyncMock(return_value=mock_existing_user)

        service = UserService()
        service.user_repository = mock_repo

        # Attempt to link account (should fail)
        with pytest.raises(ValueError, match="already linked to another user"):
            await service.link_racetime_account(
                user=mock_user,
                racetime_id='racetime_123',
                racetime_name='TestRacer',
                access_token='token_abc'
            )

    async def test_unlink_racetime_account(self):
        """Test unlinking a RaceTime account."""
        # Create mock user with linked account
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.racetime_id = 'racetime_123'
        mock_user.racetime_name = 'TestRacer'
        mock_user.racetime_access_token = 'token_abc'
        mock_user.save = AsyncMock()

        service = UserService()

        # Unlink account
        result = await service.unlink_racetime_account(mock_user)

        assert mock_user.racetime_id is None
        assert mock_user.racetime_name is None
        assert mock_user.racetime_access_token is None
        mock_user.save.assert_called_once()
