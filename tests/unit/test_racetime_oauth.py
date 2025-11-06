"""
Unit tests for RaceTime OAuth service and account linking.

Tests the RaceTime.gg OAuth2 flow and account linking functionality.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from application.services.core.user_service import UserService
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

        # URL should contain the base URL from settings (might be localhost in test env)
        assert "/o/authorize" in auth_url
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

        # Calculate expiry
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Link account
        result = await service.link_racetime_account(
            user=mock_user,
            racetime_id='racetime_123',
            racetime_name='TestRacer',
            access_token='token_abc',
            refresh_token='refresh_xyz',
            expires_at=expires_at
        )

        assert mock_user.racetime_id == 'racetime_123'
        assert mock_user.racetime_name == 'TestRacer'
        assert mock_user.racetime_access_token == 'token_abc'
        assert mock_user.racetime_refresh_token == 'refresh_xyz'
        assert mock_user.racetime_token_expires_at == expires_at
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
        mock_user.racetime_refresh_token = 'refresh_xyz'
        mock_user.racetime_token_expires_at = datetime.now(timezone.utc)
        mock_user.save = AsyncMock()

        service = UserService()

        # Unlink account
        result = await service.unlink_racetime_account(mock_user)

        assert mock_user.racetime_id is None
        assert mock_user.racetime_name is None
        assert mock_user.racetime_access_token is None
        assert mock_user.racetime_refresh_token is None
        assert mock_user.racetime_token_expires_at is None
        mock_user.save.assert_called_once()

    @patch('httpx.AsyncClient')
    async def test_refresh_access_token_success(self, mock_client_class):
        """Test successful token refresh."""
        # Mock the HTTP client response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3600
        }

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = RacetimeOAuthService()
        result = await service.refresh_access_token("old_refresh_token")

        assert result['access_token'] == 'new_access_token'
        assert result['refresh_token'] == 'new_refresh_token'
        assert result['expires_in'] == 3600

    def test_calculate_token_expiry(self):
        """Test token expiry calculation."""
        service = RacetimeOAuthService()
        
        # Calculate expiry for 3600 seconds (1 hour)
        before = datetime.now(timezone.utc)
        expires_at = service.calculate_token_expiry(3600)
        after = datetime.now(timezone.utc)

        # Should be approximately 1 hour from now
        assert expires_at > before + timedelta(seconds=3590)
        assert expires_at < after + timedelta(seconds=3610)

    async def test_refresh_racetime_token(self):
        """Test refreshing user's RaceTime token."""
        # Create mock user with expired token
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.racetime_id = 'racetime_123'
        mock_user.racetime_refresh_token = 'old_refresh_token'
        mock_user.save = AsyncMock()

        # Mock the repository
        mock_repo = MagicMock()

        # Mock RacetimeOAuthService
        with patch('middleware.racetime_oauth.RacetimeOAuthService') as mock_oauth_class:
            mock_oauth = MagicMock()
            mock_oauth.refresh_access_token = AsyncMock(return_value={
                'access_token': 'new_access_token',
                'refresh_token': 'new_refresh_token',
                'expires_in': 3600
            })
            mock_oauth.calculate_token_expiry = MagicMock(return_value=datetime.now(timezone.utc) + timedelta(hours=1))
            mock_oauth_class.return_value = mock_oauth

            service = UserService()
            service.user_repository = mock_repo

            # Refresh token
            result = await service.refresh_racetime_token(mock_user)

            assert mock_user.racetime_access_token == 'new_access_token'
            assert mock_user.racetime_refresh_token == 'new_refresh_token'
            assert mock_user.racetime_token_expires_at is not None
            mock_user.save.assert_called_once()

    async def test_refresh_racetime_token_no_refresh_token(self):
        """Test refreshing token when user has no refresh token."""
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.racetime_id = None
        mock_user.racetime_refresh_token = None

        service = UserService()

        with pytest.raises(ValueError, match="no linked RaceTime account or refresh token"):
            await service.refresh_racetime_token(mock_user)


@pytest.mark.unit
@pytest.mark.asyncio
class TestAdminRacetimeFeatures:
    """Test cases for admin RaceTime account management."""

    @patch('application.services.audit_service.AuditService')
    @patch('application.services.user_service.AuthorizationService')
    async def test_get_all_racetime_accounts_unauthorized(self, mock_auth_service_class, mock_audit_class):
        """Test that unauthorized users get empty list."""
        # Mock authorization service - return False for permission check
        mock_auth = MagicMock()
        mock_auth.can_access_admin_panel.return_value = False
        mock_auth_service_class.return_value = mock_auth
        
        # Mock audit service
        mock_audit = MagicMock()
        mock_audit.log_action = AsyncMock()
        mock_audit_class.return_value = mock_audit
        
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.permission = Permission.USER

        service = UserService()
        result = await service.get_all_racetime_accounts(admin_user=mock_user)

        assert result == []

    @patch('application.services.audit_service.AuditService')
    @patch('application.services.user_service.AuthorizationService')
    async def test_get_all_racetime_accounts_authorized(self, mock_auth_service_class, mock_audit_class):
        """Test that admin users can get all accounts."""
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.permission = Permission.ADMIN

        # Mock authorization service
        mock_auth = MagicMock()
        mock_auth.can_access_admin_panel.return_value = True
        mock_auth_service_class.return_value = mock_auth

        # Mock audit service
        mock_audit = MagicMock()
        mock_audit.log_action = AsyncMock()
        mock_audit_class.return_value = mock_audit

        service = UserService()
        service.user_repository = MagicMock()
        service.user_repository.get_users_with_racetime = AsyncMock(return_value=[])

        result = await service.get_all_racetime_accounts(
            admin_user=mock_user,
            limit=10,
            offset=0
        )

        assert isinstance(result, list)
        service.user_repository.get_users_with_racetime.assert_called_once_with(
            include_inactive=False,
            limit=10,
            offset=0
        )

    @patch('application.services.audit_service.AuditService')
    @patch('application.services.user_service.AuthorizationService')
    async def test_search_racetime_accounts_unauthorized(self, mock_auth_service_class, mock_audit_class):
        """Test that unauthorized users cannot search racetime accounts."""
        # Mock authorization service - return False for permission check
        mock_auth = MagicMock()
        mock_auth.can_access_admin_panel.return_value = False
        mock_auth_service_class.return_value = mock_auth
        
        # Mock audit service
        mock_audit = MagicMock()
        mock_audit.log_action = AsyncMock()
        mock_audit_class.return_value = mock_audit
        
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.permission = Permission.USER

        service = UserService()
        result = await service.search_racetime_accounts(
            admin_user=mock_user,
            query="test"
        )

        assert result == []

    @patch('application.services.audit_service.AuditService')
    @patch('application.services.user_service.AuthorizationService')
    async def test_get_racetime_link_statistics_authorized(self, mock_auth_service_class, mock_audit_class):
        """Test that admin users can get statistics."""
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.permission = Permission.ADMIN

        # Mock authorization service
        mock_auth = MagicMock()
        mock_auth.can_access_admin_panel.return_value = True
        mock_auth_service_class.return_value = mock_auth

        # Mock audit service
        mock_audit = MagicMock()
        mock_audit.log_action = AsyncMock()
        mock_audit_class.return_value = mock_audit

        service = UserService()
        service.user_repository = MagicMock()
        service.user_repository.count_active_users = AsyncMock(return_value=100)
        service.user_repository.count_racetime_linked_users = AsyncMock(return_value=42)

        result = await service.get_racetime_link_statistics(admin_user=mock_user)

        assert result['total_users'] == 100
        assert result['linked_users'] == 42
        assert result['unlinked_users'] == 58
        assert result['link_percentage'] == 42.0

    @patch('application.services.audit_service.AuditService')
    @patch('application.services.user_service.AuthorizationService')
    async def test_admin_unlink_racetime_account_success(self, mock_auth_service_class, mock_audit_class):
        """Test successful admin unlink."""
        mock_admin = MagicMock(spec=User)
        mock_admin.id = 1
        mock_admin.permission = Permission.ADMIN

        mock_target_user = MagicMock(spec=User)
        mock_target_user.id = 2
        mock_target_user.racetime_id = "test123"
        mock_target_user.racetime_name = "TestUser"
        mock_target_user.racetime_access_token = "token"
        mock_target_user.racetime_refresh_token = "refresh"
        mock_target_user.racetime_token_expires_at = datetime.now(timezone.utc)
        mock_target_user.save = AsyncMock()

        # Mock authorization service
        mock_auth = MagicMock()
        mock_auth.can_access_admin_panel.return_value = True
        mock_auth_service_class.return_value = mock_auth

        # Mock audit service
        mock_audit = MagicMock()
        mock_audit.log_action = AsyncMock()
        mock_audit_class.return_value = mock_audit

        service = UserService()
        service.user_repository = MagicMock()
        service.user_repository.get_by_id = AsyncMock(return_value=mock_target_user)

        result = await service.admin_unlink_racetime_account(
            user_id=2,
            admin_user=mock_admin
        )

        assert result is not None
        assert result.racetime_id is None
        assert result.racetime_name is None
        mock_target_user.save.assert_called_once()

    @patch('application.services.audit_service.AuditService')
    @patch('application.services.user_service.AuthorizationService')
    async def test_admin_unlink_racetime_account_unauthorized(self, mock_auth_service_class, mock_audit_class):
        """Test that unauthorized users cannot admin unlink."""
        # Mock authorization service - return False for permission check
        mock_auth = MagicMock()
        mock_auth.can_access_admin_panel.return_value = False
        mock_auth_service_class.return_value = mock_auth
        
        # Mock audit service
        mock_audit = MagicMock()
        mock_audit.log_action = AsyncMock()
        mock_audit_class.return_value = mock_audit
        
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.permission = Permission.USER

        service = UserService()
        result = await service.admin_unlink_racetime_account(
            user_id=2,
            admin_user=mock_user
        )

        assert result is None

